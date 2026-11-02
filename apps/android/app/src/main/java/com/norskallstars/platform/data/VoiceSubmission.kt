package com.norskallstars.platform.data

import java.util.Base64

/** Consent and server sampling happen before reading/uploading local audio. */
class VoiceSubmission(private val api: Api) {
    var offer: String? = null
        private set
    suspend fun submit(attempt: String, activity: String, consent: Boolean, bytes: () -> ByteArray): Boolean {
        require(consent)
        val selectedId = offer ?: run {
            val selected = api.post<MediaOfferView, MediaOfferInput>("/api/v1/media/recording-offers",
                MediaOfferInput(activity, attempt, true, "voice-1"))
            if (!selected.selected) return false
            selected.id.also { offer = it }
        }
        val audio = bytes()
        require(audio.size in 1..262144)
        api.post<MediaAccepted, MediaUploadInput>("/api/v1/media/recordings/${part(selectedId)}",
            MediaUploadInput(Base64.getEncoder().encodeToString(audio), "audio/mp4"))
        return true
    }
    suspend fun withdraw() {
        offer?.let {
            try { api.request("/api/v1/media/recordings/${part(it)}", "DELETE") }
            catch (e: ApiFailure) { if (e.status != 404) throw e }
        }
        offer = null
    }
}
