package com.norskallstars.platform.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.norskallstars.platform.data.*
import java.util.UUID
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.decodeFromJsonElement

enum class Page { AUTH, HOME, LESSON, PLACEMENT, HISTORY, SETTINGS }

data class UiState(
    val page: Page = Page.AUTH,
    val account: IdentityAccountView? = null,
    val locale: String = "nb",
    val busy: Boolean = false,
    val message: String? = null,
    val courses: List<LearningCourseView> = emptyList(),
    val enrollments: List<LearningEnrollmentView> = emptyList(),
    val dashboard: Map<String, Int> = emptyMap(),
    val enrollment: LearningEnrollmentView? = null,
    val lesson: LearningLessonView? = null,
    val practice: Boolean = false,
    val attempt: LearningAttemptView? = null,
    val assessment: LearningAssessmentView? = null,
    val placement: LearningPlacementView? = null,
    val answers: Map<String, LearningResponseInput> = emptyMap(),
    val translations: Map<String, String> = emptyMap(),
    val history: LearningHistoryView? = null,
    val sessions: List<IdentitySessionView> = emptyList(),
    val recordings: List<MediaRecordingView> = emptyList(),
) {
    override fun toString() = "UiState(redacted)"
}

class PlatformModel(val api: Api, private val clearMedia: () -> Unit) : ViewModel() {
    private val current = MutableStateFlow(UiState())
    val state = current.asStateFlow()
    val engagement = Engagement()
    private var operation = UUID.randomUUID().toString()
    private val translationOperations = mutableMapOf<String, String>()
    private var sequence = 1

    init {
        viewModelScope.launch {
            api.sessionRevision.collect {
                if (!api.authenticated()) {
                    clearMedia()
                    current.value = UiState(locale = current.value.locale)
                }
            }
        }
        if (api.authenticated()) execute { signedIn() }
        viewModelScope.launch {
            while (true) {
                delay(10000)
                val attempt = current.value.attempt
                if (attempt != null && attempt.submitted_at == null && engagement.eligible(android.os.SystemClock.elapsedRealtime())) {
                    try {
                        api.post<Map<String, Int>, LearningEngagementInput>(
                            "/api/v1/learning/attempts/${part(attempt.id)}/engagement", LearningEngagementInput(sequence))
                        if (current.value.attempt?.id == attempt.id) sequence++
                    } catch (e: Exception) { if (e is CancellationException) throw e }
                }
            }
        }
    }

    private fun execute(work: suspend () -> Unit) {
        if (current.value.busy) return
        current.update { it.copy(busy = true, message = null) }
        viewModelScope.launch {
            try { work() }
            catch (e: Exception) {
                if (e is CancellationException) throw e
                current.update { it.copy(message = if (e is ApiFailure && e.status == 401) "expired" else "securityError") }
            } finally { current.update { it.copy(busy = false) } }
        }
    }

    private suspend fun signedIn() {
        val account = api.get<IdentityAccountView>("/api/v1/identity/me")
        current.update { it.copy(account = account, locale = account.interface_language, page = Page.HOME) }
        loadHome()
    }

    private suspend fun loadHome() {
        val courses = api.get<List<LearningCourseView>>("/api/v1/learning/courses")
        val summaries = api.get<List<LearningEnrollmentSummary>>("/api/v1/learning/enrollments")
        val details = summaries.take(100).map { api.get<LearningEnrollmentView>("/api/v1/learning/enrollments/${part(it.id)}") }
        val stats = api.get<Map<String, Int>>("/api/v1/learning/dashboard")
        current.update { it.copy(courses = courses, enrollments = details, dashboard = stats,
            enrollment = details.find { enrollment -> enrollment.id == it.enrollment?.id } ?: it.enrollment) }
    }

    fun authenticate(mode: String, email: String, password: String, token: String) = execute {
        val body = when (mode) {
            "signIn" -> api.json.encodeToString(IdentitySignIn("Android", email, password))
            "register" -> api.json.encodeToString(IdentityRegistration(email, password))
            "verify" -> api.json.encodeToString(IdentityTokenRequest(token))
            "reset" -> api.json.encodeToString(IdentityPasswordReset(password, token))
            else -> api.json.encodeToString(IdentityEmailRequest(email))
        }
        val suffix = when (mode) {
            "signIn" -> "/sign-in"; "register" -> "/register"; "verify" -> "/verification/confirm"
            "reset" -> "/password/reset"; "requestVerification" -> "/verification/request"; else -> "/password/recovery"
        }
        val result = api.request("/api/v1/identity$suffix", "POST", body, false)
        if (mode == "signIn") {
            api.setTokens(api.json.decodeFromString<IdentitySessionTokens>(result))
            signedIn()
        } else current.update { it.copy(message = "sent") }
    }

    fun googleSignIn(proof: suspend () -> IdentityGoogleProof) = execute {
        val google = proof()
        val result = api.post<JsonObject, IdentityGoogleSignIn>("/api/v1/identity/google/sign-in",
            IdentityGoogleSignIn(google.challenge, "Android", google.id_token), false)
        if ("access_token" in result) {
            api.setTokens(api.json.decodeFromJsonElement<IdentitySessionTokens>(result))
            signedIn()
        } else current.update { it.copy(message = "sent") }
    }

    fun home() {
        if (current.value.busy) return
        clearMedia()
        current.update { it.copy(page = Page.HOME, lesson = null, attempt = null, assessment = null,
            placement = null, answers = emptyMap(), translations = emptyMap(), history = null, message = null) }
        execute { loadHome() }
    }

    fun refreshHome() = execute { loadHome() }
    fun enroll(course: String) = execute {
        api.post<LearningEnrollmentView, LearningEnrollInput>("/api/v1/learning/enrollments", LearningEnrollInput(course))
        loadHome()
    }
    fun lesson(enrollment: LearningEnrollmentView, id: String, practice: Boolean) = execute {
        val lesson = api.get<LearningLessonView>("/api/v1/learning/enrollments/${part(enrollment.id)}/lessons/${part(id)}")
        operation = UUID.randomUUID().toString()
        translationOperations.clear()
        sequence = 1
        clearMedia()
        current.update { it.copy(page = Page.LESSON, enrollment = enrollment, lesson = lesson,
            practice = practice, attempt = null, answers = emptyMap(), translations = emptyMap()) }
    }
    fun start() = execute {
        val s = current.value
        val attempt = api.post<LearningAttemptView, LearningStartInput>(
            "/api/v1/learning/enrollments/${part(s.enrollment!!.id)}/attempts",
            LearningStartInput(if (s.practice) "practice" else "canonical", s.lesson!!.lesson_id, operation))
        current.update { it.copy(attempt = attempt) }
    }
    fun answer(value: LearningResponseInput) {
        current.update {
            if (it.account == null || it.page !in setOf(Page.LESSON, Page.PLACEMENT)) it
            else it.copy(answers = it.answers + (value.activity_id to value))
        }
    }
    fun submit() = execute {
        val s = current.value
        val attempt = api.post<LearningAttemptView, LearningSubmitInput>(
            "/api/v1/learning/attempts/${part(s.attempt!!.id)}/submit", LearningSubmitInput(true, s.answers.values.toList()))
        current.update { it.copy(attempt = attempt) }
        loadHome()
    }
    fun translate(block: String) = execute {
        val s = current.value
        val op = translationOperations.getOrPut(block) { UUID.randomUUID().toString() }
        val result = api.post<LearningTranslationView, LearningTranslationInput>(
            "/api/v1/learning/enrollments/${part(s.enrollment!!.id)}/translations",
            LearningTranslationInput(block, s.lesson!!.lesson_id, op))
        current.update { it.copy(translations = it.translations + (block to result.reference_text)) }
    }
    fun placement(enrollment: LearningEnrollmentView) = execute {
        val result = api.get<LearningAssessmentView>("/api/v1/learning/enrollments/${part(enrollment.id)}/placement")
        operation = UUID.randomUUID().toString()
        current.update { it.copy(page = Page.PLACEMENT, enrollment = enrollment, assessment = result,
            placement = null, answers = emptyMap()) }
    }
    fun submitPlacement() = execute {
        val s = current.value
        val result = api.post<LearningPlacementView, LearningPlacementInput>(
            "/api/v1/learning/enrollments/${part(s.enrollment!!.id)}/placement",
            LearningPlacementInput(true, operation, s.answers.values.toList()))
        current.update { it.copy(placement = result) }
    }
    fun acceptPlacement() = execute {
        val s = current.value
        api.request("/api/v1/learning/enrollments/${part(s.enrollment!!.id)}/placement/${part(s.placement!!.id)}/accept", "POST")
        loadHome()
        current.update { it.copy(page = Page.HOME, assessment = null, placement = null, answers = emptyMap()) }
    }
    fun history(enrollment: LearningEnrollmentView, more: Boolean = false) = execute {
        val before = if (more) current.value.history?.next_before else null
        val result = api.post<LearningHistoryView, LearningHistoryInput>(
            "/api/v1/learning/enrollments/${part(enrollment.id)}/history", LearningHistoryInput(before, 25))
        current.update { it.copy(page = Page.HISTORY, enrollment = enrollment,
            history = if (more) result.copy(attempts = it.history!!.attempts + result.attempts) else result) }
    }
    fun language(value: String) {
        if (current.value.account == null) current.update { it.copy(locale = value) }
        else execute {
            api.request("/api/v1/identity/me/preferences", "PATCH", api.json.encodeToString(IdentityPreferences(value)))
            current.update { it.copy(locale = value) }
        }
    }
    fun settings() = execute {
        clearMedia()
        val sessions = api.get<List<IdentitySessionView>>("/api/v1/identity/sessions")
        val recordings = api.get<List<MediaRecordingView>>("/api/v1/media/recordings")
        current.update { it.copy(page = Page.SETTINGS, lesson = null, attempt = null, answers = emptyMap(),
            translations = emptyMap(), sessions = sessions, recordings = recordings) }
    }
    fun revoke(id: String, own: Boolean) = execute {
        api.request("/api/v1/identity/sessions/${part(id)}", "DELETE")
        if (own) api.clear() else current.update { it.copy(sessions = it.sessions.filterNot { session -> session.id == id }) }
    }
    fun revokeAll() = execute {
        api.request("/api/v1/identity/sessions/revoke-all", "POST")
        api.clear()
    }
    fun logout() = execute {
        try {
            val own = api.get<List<IdentitySessionView>>("/api/v1/identity/sessions").find { it.current }
            if (own != null) api.request("/api/v1/identity/sessions/${part(own.id)}", "DELETE")
        } finally { api.clear() }
    }
    fun sensitive(purpose: String, password: String, newPassword: String = "",
        google: (suspend () -> IdentityGoogleProof)? = null) = execute {
        val fresh = api.post<IdentityReauthenticationView, IdentityReauthentication>(
            "/api/v1/identity/reauthenticate", IdentityReauthentication(
                google = if (password.isEmpty()) google?.invoke() else null, password = password.ifEmpty { null }, purpose = purpose))
        when (purpose) {
            "delete" -> {
                api.request("/api/v1/identity/me", "DELETE", api.json.encodeToString(IdentityAuthorizedChange(fresh.reauthentication_token)))
                api.clear()
            }
            "password" -> {
                api.post<IdentityAccepted, IdentityPasswordChange>("/api/v1/identity/password/change",
                    IdentityPasswordChange(newPassword, fresh.reauthentication_token))
                api.clear()
            }
            "link" -> {
                val proof = checkNotNull(google).invoke()
                api.post<IdentityAccepted, IdentityGoogleLink>("/api/v1/identity/me/google",
                    IdentityGoogleLink(proof.challenge, proof.id_token, fresh.reauthentication_token))
                val account = api.get<IdentityAccountView>("/api/v1/identity/me")
                current.update { it.copy(account = account, message = "saved") }
            }
        }
    }
    fun withdraw(id: String) = execute {
        api.request("/api/v1/media/recordings/${part(id)}", "DELETE")
        current.update { it.copy(recordings = it.recordings.filterNot { recording -> recording.id == id }, message = "saved") }
    }
    override fun onCleared() { clearMedia() }
}
