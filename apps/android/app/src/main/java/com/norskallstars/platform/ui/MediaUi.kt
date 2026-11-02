package com.norskallstars.platform.ui

import android.Manifest
import android.graphics.BitmapFactory
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.norskallstars.platform.data.*
import java.io.File
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch

@Composable
fun Asset(api: Api, media: NativeMedia, enrollment: String, lesson: String, asset: String, alt: String) {
    val t = LocalStrings.current
    var loaded by remember { mutableStateOf<Pair<String, ByteArray>?>(null) }
    var file by remember { mutableStateOf<File?>(null) }
    var failed by remember { mutableStateOf(false) }
    val playing by media.playingFile.collectAsStateWithLifecycle()
    LaunchedEffect(enrollment, lesson, asset) {
        try {
            val data = api.asset("/api/v1/media/enrollments/${part(enrollment)}/lessons/${part(lesson)}/assets/${part(asset)}")
            loaded = data
            if (data.first.startsWith("audio/")) file = media.file(data.second)
        } catch (e: Exception) { if (e is CancellationException) throw e; failed = true }
    }
    DisposableEffect(Unit) { onDispose {
        if (media.playingFile.value == file && file != null) media.stopPlayback()
        file?.delete()
    } }
    val data = loaded
    when {
        failed -> Text(t(Msg.mediaError))
        data == null -> Text(t(Msg.loading))
        data.first.startsWith("image/") -> {
            val bitmap = remember(data) {
                val options = BitmapFactory.Options().apply { inJustDecodeBounds = true }
                BitmapFactory.decodeByteArray(data.second, 0, data.second.size, options)
                if (options.outWidth <= 0 || options.outHeight <= 0 ||
                    options.outWidth.toLong() * options.outHeight > 16000000) null
                else {
                    options.inJustDecodeBounds = false
                    options.inSampleSize = maxOf(1, maxOf(options.outWidth, options.outHeight) / 1024)
                    BitmapFactory.decodeByteArray(data.second, 0, data.second.size, options)?.asImageBitmap()
                }
            }
            if (bitmap == null) Text(t(Msg.mediaError))
            else Image(bitmap, contentDescription = alt.ifBlank { t(Msg.courseImage) }, modifier = Modifier.fillMaxWidth().heightIn(max = 320.dp))
        }
        else -> Action(t(if (playing == file && file != null) Msg.stopAudio else Msg.playAudio), file != null) {
            if (playing == file) media.stopPlayback() else file?.let { media.play(it) { failed = true } }
        }
    }
}

@Composable
fun Recorder(api: Api, media: NativeMedia, attempt: String?, activity: String, enabled: Boolean, onRecorded: (Boolean) -> Unit) {
    val t = LocalStrings.current
    val latest by rememberUpdatedState(onRecorded)
    val available by rememberUpdatedState(enabled)
    val lifecycle = LocalLifecycleOwner.current.lifecycle
    var ready by remember { mutableStateOf(false) }
    var running by remember { mutableStateOf(false) }
    var consent by remember { mutableStateOf(false) }
    var busy by remember { mutableStateOf(false) }
    var uploaded by remember { mutableStateOf(false) }
    var offer by remember { mutableStateOf<String?>(null) }
    var message by remember { mutableStateOf<Msg?>(null) }
    var active by remember { mutableStateOf(true) }
    var permissionPending by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val submission = remember(api, attempt, activity) { VoiceSubmission(api) }
    val playing by media.playingFile.collectAsStateWithLifecycle()
    val clip = remember { media.clip { ready = it; running = false; latest(it) } }
    DisposableEffect(clip) { onDispose { active = false; media.dispose(clip) } }
    val permission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        permissionPending = false
        if (granted && active && available && lifecycle.currentState.isAtLeast(Lifecycle.State.RESUMED)) {
            try { media.record(clip); ready = false; latest(false); running = true; message = null }
            catch (_: Exception) { message = Msg.audioError }
        } else message = Msg.audioError
    }
    Action(t(if (running) Msg.stop else Msg.record), enabled && !busy && !permissionPending && offer == null) {
        if (running) clip.stop() else {
            permissionPending = true
            permission.launch(Manifest.permission.RECORD_AUDIO)
        }
    }
    if (running) Text(t(Msg.recording))
    if (ready) {
        Action(t(if (playing == clip.file) Msg.stopAudio else Msg.playRecording), enabled && !busy) {
            if (playing == clip.file) media.stopPlayback() else media.play(clip.file) { message = Msg.audioError }
        }
        Check(t(Msg.consent), consent, enabled && !busy && !uploaded) { consent = it }
        if (attempt != null && !uploaded) Action(t(Msg.upload), enabled && consent && !busy) {
            busy = true
            scope.launch {
                try {
                    if (submission.submit(attempt, activity, consent) {
                        check(clip.file.length() in 1..262144)
                        clip.file.readBytes()
                    }) {
                        uploaded = true
                        message = Msg.voiceSaved
                    } else message = Msg.localOnly
                } catch (e: Exception) { if (e is CancellationException) throw e; message = Msg.error }
                finally { offer = submission.offer; busy = false }
            }
        }
        Action(t(if (offer == null) Msg.remove else Msg.withdraw), enabled && !busy) {
            busy = true
            scope.launch {
                try {
                    submission.withdraw()
                    media.erase(clip); ready = false; latest(false); offer = null; uploaded = false; consent = false
                    message = Msg.localOnly
                } catch (e: Exception) { if (e is CancellationException) throw e; message = Msg.error }
                finally { busy = false }
            }
        }
    }
    Text(t(message ?: Msg.localOnly))
}
