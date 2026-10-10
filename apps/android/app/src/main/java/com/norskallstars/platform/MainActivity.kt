package com.norskallstars.platform

import android.app.Application
import android.os.Bundle
import android.os.SystemClock
import android.view.MotionEvent
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.enableEdgeToEdge
import androidx.activity.compose.setContent
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.norskallstars.platform.data.Api
import com.norskallstars.platform.data.NativeMedia
import com.norskallstars.platform.data.TokenVault
import com.norskallstars.platform.ui.PlatformApp
import com.norskallstars.platform.ui.PlatformModel

class NorskAllstarsApplication : Application() {
    val media by lazy { NativeMedia(this) }
    val api by lazy { Api(BuildConfig.API_ORIGIN, TokenVault(this), BuildConfig.DEBUG) }
}

class MainActivity : ComponentActivity() {
    private lateinit var model: PlatformModel
    private val graph get() = application as NorskAllstarsApplication
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        model = ViewModelProvider(this, object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                require(modelClass == PlatformModel::class.java)
                return PlatformModel(graph.api, graph.media::clear) as T
            }
        })[PlatformModel::class.java]
        setContent { PlatformApp(model, graph.media) }
    }
    override fun onStart() { super.onStart(); model.engagement.foreground = true }
    override fun onStop() { model.engagement.foreground = false; graph.media.pause(); super.onStop() }
    override fun dispatchTouchEvent(event: MotionEvent): Boolean {
        if (::model.isInitialized && event.action == MotionEvent.ACTION_DOWN) model.engagement.interact(SystemClock.elapsedRealtime())
        return super.dispatchTouchEvent(event)
    }
}
