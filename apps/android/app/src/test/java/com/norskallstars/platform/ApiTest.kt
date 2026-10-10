package com.norskallstars.platform

import com.norskallstars.platform.data.*
import com.norskallstars.platform.ui.*
import java.io.ByteArrayInputStream
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.*
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.*
import mockwebserver3.Dispatcher
import mockwebserver3.MockResponse
import mockwebserver3.MockWebServer
import mockwebserver3.RecordedRequest
import org.junit.Assert.*
import org.junit.Test
import okhttp3.ResponseBody.Companion.toResponseBody

class ApiTest {
    @Test fun readRecoveryStopsAfterAccountRevocation() = runBlocking {
        lateinit var api: Api
        val calls = AtomicInteger()
        val client = okhttp3.OkHttpClient.Builder().addInterceptor {
            calls.incrementAndGet(); api.clear()
            throw java.net.SocketException("synthetic-sensitive-marker")
        }.build()
        api = Api("http://127.0.0.1", MemoryTokenStore(), true, client)
        api.setTokens(tokens())
        rejected(401) { api.request("/api/v1/identity/me") }
        assertEquals(1, calls.get())
        assertFalse(api.authenticated())
    }

    @Test fun safeReadRecoveryIsBoundedAndMutatingRequestsNeverReplay() = runBlocking {
        val calls = AtomicInteger()
        val client = okhttp3.OkHttpClient.Builder().addInterceptor { chain ->
            if (calls.incrementAndGet() == 1) throw java.net.SocketException("synthetic-sensitive-marker")
            okhttp3.Response.Builder().request(chain.request()).protocol(okhttp3.Protocol.HTTP_1_1)
                .code(200).message("OK").body("{}".toResponseBody()).build()
        }.build()
        val api = Api("http://127.0.0.1", MemoryTokenStore(), true, client)
        api.setTokens(tokens())
        assertEquals("{}", api.request("/api/v1/identity/me"))
        assertEquals(2, calls.get())
        calls.set(0)
        rejected { api.request("/api/v1/identity/reauthenticate", "POST", "{}") }
        assertEquals(1, calls.get())
    }

    @Test fun tlsFailureWithNestedEofIsNeverRetried() = runBlocking {
        val calls = AtomicInteger()
        val client = okhttp3.OkHttpClient.Builder().addInterceptor {
            calls.incrementAndGet()
            throw javax.net.ssl.SSLException("synthetic-sensitive-marker").apply {
                initCause(java.io.EOFException("synthetic-sensitive-marker"))
            }
        }.build()
        val api = Api("http://127.0.0.1", MemoryTokenStore(), true, client)
        api.setTokens(tokens())
        try { api.request("/api/v1/identity/me"); fail("Broken TLS accepted") }
        catch (failure: ApiFailure) {
            assertEquals(TransportFailure.TLS, failure.transport)
            assertNull(failure.cause)
        }
        assertEquals(1, calls.get())
    }

    @Test fun transportDiagnosticsNeverRetainExceptionDetails() = runBlocking {
        val client = okhttp3.OkHttpClient.Builder().addInterceptor {
            throw java.io.EOFException("synthetic-sensitive-marker")
        }.build()
        val api = Api("http://127.0.0.1", MemoryTokenStore(), true, client)
        api.setTokens(tokens())
        try { api.request("/api/v1/identity/me"); fail("Broken transport accepted") }
        catch (failure: ApiFailure) {
            assertEquals(TransportFailure.EOF, failure.transport)
            assertFalse(failure.toString().contains("synthetic-sensitive-marker"))
            assertNull(failure.cause)
        }
    }

    private fun tokens(suffix: String = "one") = IdentitySessionTokens("access-$suffix", 900, "refresh-$suffix", "session-$suffix")
    private suspend fun rejected(status: Int? = null, work: suspend () -> Unit) {
        try { work(); fail("Operation should fail closed") }
        catch (e: ApiFailure) { if (status != null) assertEquals(status, e.status) }
    }
    private fun response(status: Int = 200, body: String = "{}") = MockResponse.Builder().code(status).body(body).build()

    @Test fun fixedOriginAndTraversalFailClosed() = runBlocking {
        for (origin in listOf("http://remote.example", "https://example.com/path", "https://user:pass@example.com", "https://example.com?token=x")) {
            assertThrows(IllegalArgumentException::class.java) { Api(origin, MemoryTokenStore()) }
        }
        MockWebServer().use { server ->
            server.start()
            val api = Api(server.url("/").toString().removeSuffix("/"), MemoryTokenStore(), true)
            for (path in listOf("https://elsewhere.example/api/v1/me", "/api/v1/identity/../me", "/api/v1/identity/%2e%2e/me", "/api/v1/identity/a%2fb", "/api/v1/identity/me?token=x", "/api/v1/identity/me#x")) {
                try { api.request(path, protected = false); fail("Unsafe path accepted") }
                catch (_: IllegalArgumentException) { /* intended fail-closed boundary */ }
            }
            assertEquals(0, server.requestCount)
        }
    }

    @Test fun bearerAndClientHeadersWithoutCookies() = runBlocking {
        MockWebServer().use { server ->
            server.start(); server.enqueue(response())
            val api = Api(server.url("/").toString().removeSuffix("/"), MemoryTokenStore(), true)
            api.setTokens(tokens())
            api.request("/api/v1/identity/me")
            val request = server.takeRequest()
            assertEquals("Bearer access-one", request.headers["Authorization"])
            assertEquals("android", request.headers["X-NorskAllstars-Client"])
            assertNull(request.headers["Cookie"])
            assertEquals("/api/v1/identity/me", request.url.encodedPath)
        }
    }

    @Test fun concurrentUnauthorizedRequestsRotateOnceAndConsumeDurably() = runBlocking {
        MockWebServer().use { server ->
            val store = MemoryTokenStore()
            val refreshes = AtomicInteger()
            server.dispatcher = object : Dispatcher() {
                override fun dispatch(request: RecordedRequest): MockResponse {
                    if (request.url.encodedPath.endsWith("refresh")) {
                        assertNull(store.read())
                        refreshes.incrementAndGet()
                        return response(body = Json.encodeToString(tokens("two")))
                    }
                    return response(if (request.headers["Authorization"] == "Bearer access-one") 401 else 200)
                }
            }
            server.start()
            val api = Api(server.url("/").toString().removeSuffix("/"), store, true)
            api.setTokens(tokens())
            coroutineScope { List(5) { async { api.request("/api/v1/identity/me") } }.awaitAll() }
            assertEquals(1, refreshes.get())
            assertEquals("refresh-two", store.read()?.refresh_token)
        }
    }

    @Test fun delayedRefreshCannotOverwriteOrClearAReplacementAccount() = runBlocking {
        MockWebServer().use { server ->
            val refreshEntered = java.util.concurrent.CountDownLatch(1)
            val releaseRefresh = java.util.concurrent.CountDownLatch(1)
            server.dispatcher = object : Dispatcher() {
                override fun dispatch(request: RecordedRequest): MockResponse {
                    if (!request.url.encodedPath.endsWith("refresh")) return response(401)
                    refreshEntered.countDown()
                    check(releaseRefresh.await(5, java.util.concurrent.TimeUnit.SECONDS))
                    return response(body = Json.encodeToString(tokens("rotated-old-account")))
                }
            }
            server.start()
            val store = MemoryTokenStore()
            val api = Api(server.url("/").toString().removeSuffix("/"), store, true)
            api.setTokens(tokens())
            val pending = async { rejected(401) { api.request("/api/v1/identity/me") } }
            withContext(Dispatchers.IO) {
                assertTrue(refreshEntered.await(5, java.util.concurrent.TimeUnit.SECONDS))
            }
            api.setTokens(tokens("replacement-account"))
            releaseRefresh.countDown()
            pending.await()
            assertEquals(tokens("replacement-account"), store.read())
            assertTrue(api.authenticated())
        }
    }

    @Test fun rejectedRefreshClearsMemoryAndPersistence() = runBlocking {
        MockWebServer().use { server ->
            server.start(); server.enqueue(response(401)); server.enqueue(response(401))
            val store = MemoryTokenStore()
            val api = Api(server.url("/").toString().removeSuffix("/"), store, true)
            api.setTokens(tokens())
            rejected(401) { api.request("/api/v1/identity/me") }
            assertFalse(api.authenticated()); assertNull(store.read())
            rejected(401) { api.request("/api/v1/identity/me") }
            assertEquals(2, server.requestCount)
        }
    }

    @Test fun logoutDropsInFlightOldAccountResponse() = runBlocking {
        MockWebServer().use { server ->
            server.start()
            server.enqueue(MockResponse.Builder().body("{\"private\":true}").bodyDelay(300, java.util.concurrent.TimeUnit.MILLISECONDS).build())
            val api = Api(server.url("/").toString().removeSuffix("/"), MemoryTokenStore(), true)
            api.setTokens(tokens())
            val request = async { rejected(401) { api.request("/api/v1/identity/me") } }
            withContext(Dispatchers.IO) { server.takeRequest() }
            api.clear(); api.setTokens(tokens("different-account"))
            request.await()
            assertTrue(api.authenticated())
        }
    }

    @Test fun redirectsNeverReceiveCredentials() = runBlocking {
        MockWebServer().use { server ->
            server.start()
            server.enqueue(MockResponse.Builder().code(302).addHeader("Location", "https://untrusted.invalid/").build())
            val api = Api(server.url("/").toString().removeSuffix("/"), MemoryTokenStore(), true)
            api.setTokens(tokens())
            rejected(302) { api.request("/api/v1/identity/me") }
            assertEquals(1, server.requestCount)
        }
    }

    @Test fun exceptionNeverEchoesSensitiveErrorBody() = runBlocking {
        MockWebServer().use { server ->
            server.start(); server.enqueue(response(500, "synthetic-sensitive-marker"))
            val api = Api(server.url("/").toString().removeSuffix("/"), MemoryTokenStore(), true)
            try { api.request("/api/v1/identity/register", "POST", "{}", false); fail() }
            catch (e: ApiFailure) { assertFalse(e.toString().contains("synthetic-sensitive-marker")) }
        }
    }

    @Test fun mediaMimeAndReplySizeAreBounded() = runBlocking {
        MockWebServer().use { server ->
            server.start()
            server.enqueue(MockResponse.Builder().addHeader("Content-Type", "text/html").body("synthetic").build())
            val api = Api(server.url("/").toString().removeSuffix("/"), MemoryTokenStore(), true)
            api.setTokens(tokens())
            rejected(415) { api.asset("/api/v1/media/enrollments/synthetic") }
            server.enqueue(MockResponse.Builder().addHeader("Content-Type", "application/json").body("x".repeat(1048577)).build())
            rejected(413) { api.request("/api/v1/identity/me") }
            assertThrows(ApiFailure::class.java) { readBounded(ByteArrayInputStream(ByteArray(1025)), 1024) }
            assertEquals(1024, readBounded(ByteArrayInputStream(ByteArray(1024)), 1024).size)
        }
    }

    @Test fun inputPresentationFailsClosedAndDoesNotGrade() {
        val basic = LearningActivityView("synthetic", emptyList(), "deterministic", null,
            "Synthetic prompt", "text", null, "short_answer")
        assertEquals("text", presentationKind(basic))
        assertNull(presentationKind(basic.copy(response_mode = "pairs", type = "matching")))
        assertNull(presentationKind(basic.copy(presentation = LearningPresentation(null, "unsupported-future-kind", emptyList()))))
        assertEquals("matching", presentationKind(basic.copy(presentation = LearningPresentation(listOf("synthetic-field"), "matching",
            listOf(LearningResponseOption("Synthetic option", JsonPrimitive("public-value")))))))
        assertEquals(JsonNull, answer("synthetic").response)
        assertNull(answer("synthetic").self_assessment)
        assertFalse(answer("synthetic").acknowledged)
    }

    @Test fun engagementExcludesBackgroundAndIdleTime() {
        val gate = Engagement()
        gate.foreground = true
        assertFalse(gate.eligible(0))
        gate.interact(1000)
        assertTrue(gate.eligible(31000))
        assertFalse(gate.eligible(31001))
        gate.foreground = false
        assertFalse(gate.eligible(1001))
        gate.foreground = true
        assertFalse(gate.eligible(999))
    }

    @Test fun generatedSensitiveDtoStringRepresentationsAreRedacted() {
        assertFalse(tokens().toString().contains("access-one"))
        assertFalse(IdentitySignIn("Android", "synthetic@example.com", "synthetic-password").toString().contains("synthetic-password"))
    }

    @Test fun voiceNeverUploadsOrReadsAudioWithoutConsentAndSelection() = runBlocking {
        MockWebServer().use { server ->
            server.start()
            val api = Api(server.url("/").toString().removeSuffix("/"), MemoryTokenStore(), true)
            api.setTokens(tokens())
            val submission = VoiceSubmission(api)
            try { submission.submit("synthetic-attempt", "synthetic-activity", false) { error("Must not read audio") }; fail() }
            catch (_: IllegalArgumentException) { /* consent is independent of learning */ }
            assertEquals(0, server.requestCount)
            server.enqueue(response(body = """{"expires_at":"synthetic-time","id":"synthetic-offer","retention_until":"synthetic-time","selected":false}"""))
            assertFalse(submission.submit("synthetic-attempt", "synthetic-activity", true) { error("Unselected audio must remain local") })
            assertEquals(1, server.requestCount)
            assertNull(submission.offer)
        }
    }

    @Test fun ambiguousVoiceRetryUsesTheSameSelectedOffer() = runBlocking {
        MockWebServer().use { server ->
            server.start()
            val api = Api(server.url("/").toString().removeSuffix("/"), MemoryTokenStore(), true)
            api.setTokens(tokens())
            val submission = VoiceSubmission(api)
            server.enqueue(response(body = """{"expires_at":"synthetic-time","id":"synthetic-offer","retention_until":"synthetic-time","selected":true}"""))
            server.enqueue(response(503))
            rejected(503) { submission.submit("synthetic-attempt", "synthetic-activity", true) { ByteArray(24) } }
            server.enqueue(response(body = """{"status":"accepted"}"""))
            assertTrue(submission.submit("synthetic-attempt", "synthetic-activity", true) { ByteArray(24) })
            assertEquals(3, server.requestCount)
            assertEquals("/api/v1/media/recording-offers", server.takeRequest().url.encodedPath)
            repeat(2) { assertEquals("/api/v1/media/recordings/synthetic-offer", server.takeRequest().url.encodedPath) }
        }
    }

    @Test fun ambiguousVoiceUploadRetainsWithdrawalAndSizeIsBounded() = runBlocking {
        MockWebServer().use { server ->
            server.start()
            val api = Api(server.url("/").toString().removeSuffix("/"), MemoryTokenStore(), true)
            api.setTokens(tokens())
            val submission = VoiceSubmission(api)
            server.enqueue(response(body = """{"expires_at":"synthetic-time","id":"synthetic-offer","retention_until":"synthetic-time","selected":true}"""))
            server.enqueue(response(503))
            rejected(503) { submission.submit("synthetic-attempt", "synthetic-activity", true) { ByteArray(24) } }
            assertEquals("synthetic-offer", submission.offer)
            server.enqueue(response())
            submission.withdraw(); assertNull(submission.offer)
            server.enqueue(response(body = """{"expires_at":"synthetic-time","id":"synthetic-offer","retention_until":"synthetic-time","selected":true}"""))
            try { submission.submit("synthetic-attempt", "synthetic-activity", true) { ByteArray(262145) }; fail() }
            catch (_: IllegalArgumentException) { /* no oversized upload */ }
            assertEquals(4, server.requestCount)
        }
    }
}
