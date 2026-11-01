package com.norskallstars.platform

import android.Manifest
import android.content.pm.PackageManager
import android.os.ParcelFileDescriptor
import androidx.test.platform.app.InstrumentationRegistry
import com.norskallstars.platform.data.*
import java.io.File
import org.junit.Assert.*
import org.junit.Test

class NativeSecurityTest {
    @Test fun vaultEncryptsAndTamperingFailsClosed() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val vault = TokenVault(context)
        val tokens = IdentitySessionTokens("synthetic-access-marker", 900, "synthetic-refresh-marker", "synthetic-session")
        vault.write(tokens)
        val file = File(context.noBackupFilesDir, "native-session")
        assertFalse(file.readBytes().decodeToString().contains("synthetic-refresh-marker"))
        assertEquals(tokens, vault.read())
        val bytes = file.readBytes(); bytes[bytes.lastIndex] = (bytes.last().toInt() xor 1).toByte(); file.writeBytes(bytes)
        assertNull(vault.read()); assertFalse(file.exists())
    }

    @Test fun microphoneIsBoundedPrivateAndStoppedWithLifecycle() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val context = instrumentation.targetContext
        // UiAutomation.grantRuntimePermission requires API 28. Shell permission
        // provisioning supports the same isolated test on our API 26 floor.
        ParcelFileDescriptor.AutoCloseInputStream(instrumentation.uiAutomation.executeShellCommand(
            "pm grant ${context.packageName} ${Manifest.permission.RECORD_AUDIO}"
        )).use { it.readBytes() }
        assertEquals(PackageManager.PERMISSION_GRANTED, context.checkSelfPermission(Manifest.permission.RECORD_AUDIO))
        val media = NativeMedia(context)
        var recorded = false
        val clip = media.clip { recorded = it }
        instrumentation.runOnMainSync { media.record(clip) }
        android.os.SystemClock.sleep(1500)
        instrumentation.runOnMainSync { media.pause() }
        assertTrue(recorded)
        assertTrue(clip.file.length() in 1..262144)
        assertTrue(clip.file.canonicalPath.startsWith(context.cacheDir.canonicalPath))
        instrumentation.runOnMainSync {
            media.play(clip.file) { fail("Private synthetic playback failed") }
            media.erase(clip)
        }
        assertNull(media.playingFile.value)
        assertFalse(clip.file.exists())
        instrumentation.waitForIdleSync()
        media.clear(); assertFalse(clip.file.exists())
        // Revoking a runtime permission kills the instrumented app process.
        // The isolated device/app is cleaned by the harness after instrumentation.
    }
}
