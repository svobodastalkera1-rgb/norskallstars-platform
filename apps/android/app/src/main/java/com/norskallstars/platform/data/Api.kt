package com.norskallstars.platform.data

import java.io.IOException
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicLong
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody

enum class TransportFailure { TIMEOUT, EOF, CONNECT, SOCKET, TLS, NETWORK }

class ApiFailure(val status: Int = 0, val transport: TransportFailure? = null) : IOException(
    "Request unavailable" + (transport?.let { " (${it.name})" } ?: ""))

interface TokenStore {
    fun read(): IdentitySessionTokens?
    fun write(tokens: IdentitySessionTokens)
    fun clear()
}

class MemoryTokenStore : TokenStore {
    private var tokens: IdentitySessionTokens? = null
    override fun read() = tokens
    override fun write(tokens: IdentitySessionTokens) { this.tokens = tokens }
    override fun clear() { tokens = null }
}

/** One fixed origin; mutating calls never replay. Read recovery uses one fresh connection. */
class Api(
    val origin: String,
    private val store: TokenStore,
    development: Boolean = false,
    private val client: OkHttpClient = OkHttpClient.Builder()
        .followRedirects(false).followSslRedirects(false).retryOnConnectionFailure(false)
        .connectTimeout(10, TimeUnit.SECONDS).readTimeout(15, TimeUnit.SECONDS)
        .callTimeout(20, TimeUnit.SECONDS).build(),
) {
    val json = Json { ignoreUnknownKeys = true; encodeDefaults = true; explicitNulls = true }
    private val epoch = AtomicLong(0)
    private val revision = MutableStateFlow(0L)
    val sessionRevision = revision.asStateFlow()
    private val rotation = Mutex()
    @Volatile private var tokens: IdentitySessionTokens? = store.read()

    init {
        val uri = java.net.URI(origin)
        require(uri.rawUserInfo == null && uri.rawQuery == null && uri.rawFragment == null)
        require(uri.rawPath.isNullOrEmpty() && uri.host != null)
        require(uri.scheme == "https" ||
            (development && uri.scheme == "http" && uri.host in setOf("10.0.2.2", "127.0.0.1", "localhost")))
    }

    fun authenticated() = tokens != null

    @Synchronized fun setTokens(value: IdentitySessionTokens) {
        store.write(value)
        tokens = value
        revision.value = epoch.incrementAndGet()
    }

    @Synchronized fun clear() {
        tokens = null
        try { store.clear() } finally { revision.value = epoch.incrementAndGet() }
    }

    private data class Reply(val status: Int, val bytes: ByteArray, val type: String?)

    private suspend fun send(path: String, method: String, body: String?, token: String?, maximum: Int,
        fresh: Boolean = false): Reply =
        withContext(Dispatchers.IO) {
            require(path.matches(Regex("/api/v1/(identity|learning|media)/[A-Za-z0-9%._/-]+")))
            require(!path.contains("..") && !path.contains("//"))
            require(path.split('/').all { segment ->
                val decoded = java.net.URLDecoder.decode(segment, "UTF-8")
                decoded != ".." && decoded != "." && !decoded.contains('/') && !decoded.contains('\\')
            })
            val request = Request.Builder().url(origin + path)
                .header("X-NorskAllstars-Client", "android")
                .header("Cache-Control", "no-store")
            if (token != null) request.header("Authorization", "Bearer $token")
            val payload = body ?: if (method == "POST" || method == "PATCH") "{}" else null
            require(payload == null || payload.toByteArray().size <= 524288)
            request.method(method, payload?.toRequestBody("application/json".toMediaType()))
            try {
                val connection = if (fresh) client.newBuilder()
                    .connectionPool(okhttp3.ConnectionPool(0, 1, TimeUnit.SECONDS)).build() else client
                connection.newCall(request.build()).execute().use { response ->
                    val source = response.body
                    if (source.contentLength() > maximum) throw ApiFailure(413)
                    val bytes = readBounded(source.byteStream(), maximum)
                    Reply(response.code, bytes, source.contentType()?.let { "${it.type}/${it.subtype}" })
                }
            } catch (e: CancellationException) {
                throw e
            } catch (e: ApiFailure) {
                throw e
            } catch (e: IOException) {
                val kind = when {
                    e is javax.net.ssl.SSLException -> TransportFailure.TLS
                    e.cause is java.io.EOFException -> TransportFailure.EOF
                    else -> when (e) {
                    is java.io.InterruptedIOException -> TransportFailure.TIMEOUT
                    is java.io.EOFException -> TransportFailure.EOF
                    is java.net.ConnectException -> TransportFailure.CONNECT
                    is java.net.SocketException -> TransportFailure.SOCKET
                    else -> TransportFailure.NETWORK
                    }
                }
                // Keep only a bounded category, never exception text/URLs/payloads.
                throw ApiFailure(transport = kind)
            }
        }

    private suspend fun refresh(observed: String, generation: Long) = rotation.withLock {
        if (epoch.get() != generation) throw ApiFailure(401)
        val current = tokens ?: throw ApiFailure(401)
        if (current.access_token != observed) return@withLock
        try {
            // A crash or lost response must never reuse a rotating refresh credential.
            synchronized(this) {
                if (epoch.get() != generation) throw ApiFailure(401)
                store.clear()
            }
            val response = send("/api/v1/identity/sessions/refresh", "POST",
                json.encodeToString(IdentityRefresh(current.refresh_token)), null, 1048576)
            if (response.status != 200) throw ApiFailure(401)
            val next = json.decodeFromString<IdentitySessionTokens>(response.bytes.decodeToString())
            synchronized(this) {
                if (epoch.get() != generation) throw ApiFailure(401)
                store.write(next)
                tokens = next
            }
        } catch (e: Exception) {
            synchronized(this) { if (epoch.get() == generation) clear() }
            if (e is CancellationException) throw e
            throw ApiFailure(401)
        }
    }

    private suspend fun reply(path: String, method: String, body: String?, protected: Boolean, maximum: Int): Reply {
        val generation = epoch.get()
        val access = if (protected) tokens?.access_token ?: throw ApiFailure(401) else null
        suspend fun readOrSend(token: String?): Reply {
            try { return send(path, method, body, token, maximum) }
            catch (failure: ApiFailure) {
                if (method != "GET" || failure.transport !in setOf(
                    TransportFailure.EOF, TransportFailure.CONNECT, TransportFailure.SOCKET)) throw failure
                if (generation != epoch.get()) throw ApiFailure(401)
                return send(path, method, body, token, maximum, fresh = true)
            }
        }
        var result = readOrSend(access)
        if (protected && generation != epoch.get()) throw ApiFailure(401)
        if (result.status == 401 && protected && access != null) {
            refresh(access, generation)
            result = readOrSend(tokens?.access_token)
        }
        if (protected && generation != epoch.get()) throw ApiFailure(401)
        if (result.status !in 200..299) {
            if (result.status == 401 && protected) clear()
            throw ApiFailure(result.status)
        }
        return result
    }

    suspend fun request(path: String, method: String = "GET", body: String? = null, protected: Boolean = true): String =
        reply(path, method, body, protected, 1048576).bytes.decodeToString()

    suspend inline fun <reified T> get(path: String): T = json.decodeFromString(request(path))

    suspend inline fun <reified T, reified B> post(path: String, body: B, protected: Boolean = true): T =
        json.decodeFromString(request(path, "POST", json.encodeToString(body), protected))

    suspend fun asset(path: String): Pair<String, ByteArray> {
        val result = reply(path, "GET", null, true, 10485760)
        val type = result.type
        if (type !in setOf("image/png", "image/jpeg", "image/webp", "audio/mpeg", "audio/wav", "audio/ogg"))
            throw ApiFailure(415)
        return Pair(type ?: throw ApiFailure(415), result.bytes)
    }
}

fun part(value: String): String = java.net.URLEncoder.encode(value, "UTF-8").replace("+", "%20")

fun readBounded(stream: java.io.InputStream, maximum: Int): ByteArray {
    val output = java.io.ByteArrayOutputStream()
    val buffer = ByteArray(8192)
    while (true) {
        val count = stream.read(buffer, 0, minOf(buffer.size, maximum + 1 - output.size()))
        if (count < 0) return output.toByteArray()
        output.write(buffer, 0, count)
        if (output.size() > maximum) throw ApiFailure(413)
    }
}
