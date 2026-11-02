package com.norskallstars.platform.data

import android.content.Context
import android.media.MediaPlayer
import android.media.MediaRecorder
import android.os.Build
import java.io.File
import java.util.UUID
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

/** Private ephemeral interaction files, not a course cache/offline store. */
class NativeMedia(private val context: Context) {
    private val directory = File(context.cacheDir, "ephemeral-media").apply { mkdirs() }
    private val players = mutableSetOf<MediaPlayer>()
    private val clips = mutableSetOf<Clip>()
    private val playback = MutableStateFlow<File?>(null)
    val playingFile = playback.asStateFlow()
    init { directory.listFiles()?.forEach { it.delete() } }
    fun file(bytes: ByteArray? = null): File = File(directory, UUID.randomUUID().toString()).apply {
        createNewFile()
        if (bytes != null) writeBytes(bytes)
    }
    fun clip(onStopped: (Boolean) -> Unit): Clip = Clip(context, file(), onStopped).also { clips.add(it) }
    fun erase(clip: Clip) { if (playback.value == clip.file) stopPlayback(); clip.close() }
    fun dispose(clip: Clip) { erase(clip); clips.remove(clip) }
    fun record(clip: Clip) { require(clip in clips); pause(); clip.start() }
    fun play(file: File, onError: () -> Unit) {
        stopPlayback()
        val player = MediaPlayer()
        players.add(player)
        playback.value = file
        player.setOnCompletionListener { if (players.remove(it)) { playback.value = null; it.release() } }
        player.setOnErrorListener { value, _, _ ->
            if (players.remove(value)) { playback.value = null; value.release(); onError() }; true
        }
        try {
            player.setDataSource(file.path)
            player.setOnPreparedListener {
                if (it in players) try { it.start() }
                catch (_: IllegalStateException) { players.remove(it); playback.value = null; it.release(); onError() }
            }
            player.prepareAsync()
        } catch (_: Exception) { players.remove(player); playback.value = null; player.release(); onError() }
    }
    fun stopPlayback() {
        val stopped = players.toList()
        players.clear()
        playback.value = null
        stopped.forEach { it.release() }
    }
    fun pause() { clips.toList().forEach { it.stop() }; stopPlayback() }
    fun clear() {
        stopPlayback()
        clips.toList().forEach { it.close() }; clips.clear()
        directory.listFiles()?.forEach { it.delete() }
    }
}

class Clip(private val context: Context, val file: File, private val onStopped: (Boolean) -> Unit) {
    private var recorder: MediaRecorder? = null
    var ready: Boolean = false
        private set
    @Suppress("DEPRECATION") // Context constructor starts at API 31; retain API 26 support.
    fun start() {
        stop()
        ready = false
        try {
            val value = if (Build.VERSION.SDK_INT >= 31) MediaRecorder(context) else MediaRecorder()
            recorder = value
            value.setAudioSource(MediaRecorder.AudioSource.MIC)
            value.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
            value.setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
            value.setAudioEncodingBitRate(24000)
            value.setAudioSamplingRate(16000)
            value.setAudioChannels(1)
            value.setMaxDuration(60000)
            value.setMaxFileSize(262144)
            value.setOutputFile(file.path)
            value.setOnInfoListener { _, _, _ -> stop() }
            value.setOnErrorListener { _, _, _ -> close(); onStopped(false) }
            value.prepare()
            value.start()
        } catch (e: Exception) { close(); throw e }
    }
    fun stop() {
        val value = recorder ?: return
        recorder = null
        try {
            value.stop()
            ready = file.length() in 1..262144
        } catch (_: Exception) { ready = false }
        finally { value.release() }
        if (!ready) file.delete()
        onStopped(ready)
    }
    fun close() { stop(); ready = false; file.delete() }
}
