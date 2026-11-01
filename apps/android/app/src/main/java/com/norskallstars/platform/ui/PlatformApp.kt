package com.norskallstars.platform.ui

import android.content.res.Configuration
import androidx.activity.compose.BackHandler
import androidx.activity.compose.LocalActivity
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.input.key.onPreviewKeyEvent
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.norskallstars.platform.BuildConfig
import com.norskallstars.platform.data.*
import java.util.Locale
import kotlinx.serialization.json.*

@Composable
fun Action(label: String, enabled: Boolean = true, onClick: () -> Unit) {
    Button(onClick = onClick, enabled = enabled, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text(label) }
}

@Composable
fun Check(label: String, checked: Boolean, enabled: Boolean, modifier: Modifier = Modifier, onChange: (Boolean) -> Unit) {
    Row(modifier.fillMaxWidth().heightIn(min = 48.dp).toggleable(checked, enabled = enabled, role = Role.Checkbox, onValueChange = onChange),
        verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
        Checkbox(checked, null, enabled = enabled)
        Text(label, Modifier.weight(1f))
    }
}

@Composable
fun Radio(label: String, selected: Boolean, enabled: Boolean, onClick: () -> Unit) {
    Row(Modifier.fillMaxWidth().heightIn(min = 48.dp).selectable(selected, enabled = enabled, role = Role.RadioButton, onClick = onClick),
        verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
        RadioButton(selected, null, enabled = enabled)
        Text(label, Modifier.weight(1f))
    }
}

@Composable
fun Field(label: String, value: String, maximum: Int = 12000, secret: Boolean = false, enabled: Boolean = true, onChange: (String) -> Unit) {
    OutlinedTextField(value, { if (it.length <= maximum) onChange(it) }, label = { Text(label) },
        enabled = enabled,
        modifier = Modifier.fillMaxWidth(), singleLine = secret || maximum <= 512,
        visualTransformation = if (secret) PasswordVisualTransformation() else VisualTransformation.None,
        keyboardOptions = KeyboardOptions(keyboardType = if (secret) KeyboardType.Password else KeyboardType.Text,
            imeAction = if (secret || maximum <= 512) ImeAction.Done else ImeAction.Default))
}

@Composable
fun Title(value: String) { Text(value, style = MaterialTheme.typography.headlineSmall, modifier = Modifier.semantics { heading() }) }

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun PlatformApp(model: PlatformModel, media: NativeMedia) {
    val state by model.state.collectAsStateWithLifecycle()
    val context = LocalContext.current
    val configuration = LocalConfiguration.current
    val localized = remember(state.locale, context, configuration) {
        context.createConfigurationContext(Configuration(configuration).apply {
            setLocale(Locale.forLanguageTag(if (state.locale == "en") "en" else "nb"))
        })
    }
    val t: (Msg) -> String = { localized.getString(it.resource) }
    BackHandler(state.account != null && state.page != Page.HOME && !state.busy) { model.home() }
    MaterialTheme(colorScheme = lightColorScheme(primary = Color(0xFF155A4E), secondary = Color(0xFF405F59),
        background = Color(0xFFF4F7F4), surface = Color(0xFFF4F7F4))) {
        CompositionLocalProvider(LocalStrings provides t) {
            Scaffold { padding ->
                Column(Modifier.fillMaxSize().onPreviewKeyEvent {
                    model.engagement.interact(android.os.SystemClock.elapsedRealtime()); false
                }.padding(padding).consumeWindowInsets(padding).imePadding().padding(horizontal = 20.dp)) {
                    Text("NorskAllstars", style = MaterialTheme.typography.headlineMedium, modifier = Modifier.padding(vertical = 12.dp))
                    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        TextButton({ model.language("nb") }, enabled = !state.busy) { Text("Bokmål") }
                        TextButton({ model.language("en") }, enabled = !state.busy) { Text("English") }
                    }
                    if (state.account != null) FlowRow {
                        TextButton(model::home, enabled = !state.busy) { Text(t(Msg.home)) }
                        TextButton(model::settings, enabled = !state.busy) { Text(t(Msg.settings)) }
                        TextButton(model::logout, enabled = !state.busy) { Text(t(Msg.logout)) }
                    }
                    if (state.busy) LinearProgressIndicator(Modifier.fillMaxWidth())
                    state.message?.let { key ->
                        Text(t(Msg.entries.find { it.name == key } ?: Msg.error), modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite })
                    }
                    Box(Modifier.weight(1f)) {
                        when (state.page) {
                            Page.AUTH -> AuthUi(model, state)
                            Page.HOME -> HomeUi(model, state)
                            Page.LESSON -> LessonUi(model, media, state)
                            Page.PLACEMENT -> PlacementUi(model, media, state)
                            Page.HISTORY -> HistoryUi(model, state)
                            Page.SETTINGS -> SettingsUi(model, state)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun AuthUi(model: PlatformModel, state: UiState) {
    val t = LocalStrings.current
    var mode by remember { mutableStateOf(Msg.signIn) }
    var email by remember(mode) { mutableStateOf("") }
    var password by remember(mode) { mutableStateOf("") }
    var token by remember(mode) { mutableStateOf("") }
    val activity = checkNotNull(LocalActivity.current)
    val provider = remember(activity) { GoogleIdentity(activity, BuildConfig.GOOGLE_CLIENT_ID) }
    val modes = listOf(Msg.signIn, Msg.register, Msg.recovery, Msg.verify, Msg.reset, Msg.requestVerification)
    LazyColumn(modifier = Modifier.testTag("screen-list"), verticalArrangement = Arrangement.spacedBy(12.dp), contentPadding = PaddingValues(bottom = 24.dp)) {
        item { Title(t(mode)) }
        item { Text(t(Msg.intro)) }
        if (mode in listOf(Msg.signIn, Msg.register, Msg.recovery, Msg.requestVerification))
            item { Field(t(Msg.email), email, 254) { email = it } }
        if (mode in listOf(Msg.verify, Msg.reset)) item { Field("Token", token, 512, true) { token = it } }
        if (mode in listOf(Msg.signIn, Msg.register, Msg.reset)) item { Field(t(Msg.password), password, 128, true) { password = it } }
        item {
            Action(t(Msg.send), !state.busy &&
                (mode !in listOf(Msg.signIn, Msg.register, Msg.recovery, Msg.requestVerification) || email.isNotBlank()) &&
                (mode !in listOf(Msg.verify, Msg.reset) || token.length in 32..512) &&
                (mode !in listOf(Msg.register, Msg.reset) || password.length in 15..128) &&
                (mode != Msg.signIn || password.isNotEmpty())) {
                model.authenticate(mode.name, email, password, token)
                password = ""; token = ""
            }
        }
        if (mode == Msg.signIn) item {
            if (BuildConfig.GOOGLE_CLIENT_ID.isEmpty()) Text(t(Msg.googleUnavailable))
            else Action(t(Msg.google), !state.busy) { model.googleSignIn { provider.proof(model.api) } }
        }
        items(modes.filterNot { it == mode }) { next ->
            TextButton({ mode = next }, enabled = !state.busy) { Text(t(next)) }
        }
        item { Text(t(Msg.memory)) }
    }
}

@Composable
private fun HomeUi(model: PlatformModel, state: UiState) {
    val t = LocalStrings.current
    LazyColumn(modifier = Modifier.testTag("screen-list"), verticalArrangement = Arrangement.spacedBy(12.dp), contentPadding = PaddingValues(bottom = 24.dp)) {
        item { Title(t(Msg.welcome)); Text(t(Msg.intro)) }
        item {
            val stats = state.dashboard
            Text("${t(Msg.attempts)}: ${stats["submitted_attempts"] ?: 0}")
            Text("${t(Msg.accuracy)}: " + if ((stats["scored_answers"] ?: 0) == 0) t(Msg.noScores)
                else "${stats["correct_answers"]}/${stats["scored_answers"]}")
            Text("${t(Msg.time)}: " + if ((stats["timed_attempts"] ?: 0) == 0) "—"
                else "${(stats["active_learning_seconds"] ?: 0) / 60} min")
            Text(t(Msg.timeNote))
            Action(t(Msg.courses), !state.busy, model::refreshHome)
        }
        if (state.courses.isEmpty() && state.enrollments.isEmpty()) item { Text(t(Msg.empty)) }
        items(state.courses.filter { c -> state.enrollments.none { it.course.course_id == c.course_id } }, key = { it.release_id }) { course ->
            Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp)) {
                Title(course.title); Text("${course.language} · v${course.course_version}")
                Action(t(Msg.start), !state.busy) { model.enroll(course.course_id) }
            } }
        }
        state.enrollments.forEach { enrollment ->
            item(key = enrollment.id) {
                Title(enrollment.course.title)
                Text("v${enrollment.course.course_version} · ${t(Msg.progress)}: " +
                    "${enrollment.progress.count { it.completion == "completed" }}/${enrollment.progress.size}")
                enrollment.progress.find { it.available && it.completion != "completed" }?.let { next ->
                    Action(t(Msg.continueLearning), !state.busy) { model.lesson(enrollment, next.lesson_id, false) }
                }
                enrollment.recommended_lesson_id?.let { recommended ->
                    Action(t(Msg.recommendation), !state.busy) { model.lesson(enrollment, recommended, true) }
                }
                if (enrollment.placement_available) Action(t(Msg.placement), !state.busy) { model.placement(enrollment) }
                Action(t(Msg.history), !state.busy) { model.history(enrollment) }
            }
            enrollment.chapters.forEach { chapter ->
                item(key = "${enrollment.id}/${chapter.chapter_id}") { Title(chapter.title) }
                items(chapter.lessons, key = { "${enrollment.id}/${it.lesson_id}" }) { lesson ->
                    val progress = enrollment.progress.find { it.lesson_id == lesson.lesson_id }
                    if (progress != null) Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp)) {
                        Text(lesson.title, style = MaterialTheme.typography.titleMedium)
                        Text(t(when (progress.completion) { "completed" -> Msg.completed; "in_progress" -> Msg.inProgress; else -> Msg.notStarted }))
                        Text("${t(Msg.mastery)}: " + when {
                            progress.mastery.status == "not_applicable" -> t(Msg.notApplicable)
                            progress.mastery.value == null -> t(Msg.unknown)
                            progress.mastery.value -> t(Msg.yes)
                            else -> t(Msg.no)
                        })
                        if (progress.review_due_at?.let { java.time.Instant.parse(it).isBefore(java.time.Instant.now()) } == true) Text(t(Msg.review))
                        Action(t(if (!progress.available) Msg.locked else if (progress.completion == "completed") Msg.review else Msg.start),
                            progress.available && !state.busy) { model.lesson(enrollment, lesson.lesson_id, progress.completion == "completed") }
                    } }
                }
            }
        }
        item { Text(t(Msg.future)) }
    }
}

@Composable
private fun LessonUi(model: PlatformModel, media: NativeMedia, state: UiState) {
    val t = LocalStrings.current
    val lesson = state.lesson ?: return
    val enrollment = state.enrollment ?: return
    LazyColumn(modifier = Modifier.testTag("screen-list"), verticalArrangement = Arrangement.spacedBy(16.dp), contentPadding = PaddingValues(bottom = 24.dp)) {
        item { Action(t(Msg.back), !state.busy, model::home); Title(lesson.title); if (state.practice) Text(t(Msg.replayNote)) }
        items(lesson.blocks.sortedBy { it.order }, key = { it.block_id }) { block ->
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                block.text?.let { Text(it) }
                block.asset_ref?.let { Asset(model.api, media, enrollment.id, lesson.lesson_id, it, block.alt_text ?: "") }
                if (block.translation_available) {
                    Action(t(Msg.translation), !state.busy) { model.translate(block.block_id) }
                    state.translations[block.block_id]?.let { Text(it) }
                }
            }
        }
        if (state.attempt == null) item { Action(t(Msg.start), !state.busy, model::start) }
        else if (state.attempt.submitted_at == null) {
            items(lesson.activities, key = { it.activity_id }) { activity ->
                ActivityUi(activity, state.answers[activity.activity_id], !state.busy, model.api, media, state.attempt.id, model::answer)
            }
            item { Action(t(Msg.submit), !state.busy && lesson.activities.all { state.answers[it.activity_id]?.acknowledged == true }, model::submit) }
        } else {
            item { Results(state.attempt.evaluations.orEmpty()); Action(t(Msg.continueLearning), !state.busy, model::home) }
        }
    }
}

@Composable
private fun PlacementUi(model: PlatformModel, media: NativeMedia, state: UiState) {
    val t = LocalStrings.current
    LazyColumn(modifier = Modifier.testTag("screen-list"), verticalArrangement = Arrangement.spacedBy(16.dp), contentPadding = PaddingValues(bottom = 24.dp)) {
        item { Action(t(Msg.back), !state.busy, model::home); Title(t(Msg.placement)); Text(t(Msg.optional)) }
        if (state.placement == null) {
            items(state.assessment?.activities.orEmpty(), key = { it.activity_id }) { activity ->
                ActivityUi(activity, state.answers[activity.activity_id], !state.busy, model.api, media, null, model::answer)
            }
            item { Action(t(Msg.submit), !state.busy && state.assessment?.activities?.all { state.answers[it.activity_id]?.acknowledged == true } == true, model::submitPlacement) }
        } else item {
            Title(t(Msg.recommendation))
            Text(state.enrollment?.chapters?.flatMap { it.lessons }?.find { it.lesson_id == state.placement.recommended_lesson_id }?.title ?: t(Msg.unknown))
            Text("${t(Msg.score)}: ${state.placement.score}")
            Action(t(Msg.accept), !state.busy, model::acceptPlacement)
            Action(t(Msg.beginning), !state.busy, model::home)
        }
    }
}

@Composable
private fun HistoryUi(model: PlatformModel, state: UiState) {
    val t = LocalStrings.current
    LazyColumn(modifier = Modifier.testTag("screen-list"), verticalArrangement = Arrangement.spacedBy(16.dp), contentPadding = PaddingValues(bottom = 24.dp)) {
        item { Action(t(Msg.back), !state.busy, model::home); Title(t(Msg.history)) }
        items(state.history?.attempts.orEmpty(), key = { it.id }) { attempt ->
            Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp)) {
                Text(state.enrollment?.chapters?.flatMap { it.lessons }?.find { it.lesson_id == attempt.lesson_id }?.title ?: attempt.lesson_id)
                Text("${attempt.started_at} · ${attempt.kind} · ${attempt.policy_version}")
                Text(t(if (attempt.submitted_at == null) Msg.inProgress else Msg.completed))
                Results(attempt.evaluations.orEmpty(), responses = true)
            } }
        }
        if (state.history?.next_before != null) item { Action(t(Msg.more), !state.busy) { model.history(state.enrollment!!, true) } }
    }
}

@Composable
fun Results(evaluations: List<LearningEvaluationView>, responses: Boolean = false) {
    val t = LocalStrings.current
    evaluations.forEach { value ->
        Text("${value.activity_id}: " + when {
            value.status == "pending" -> t(Msg.pending)
            value.status == "not_applicable" -> t(Msg.notApplicable)
            value.correct == null -> t(Msg.unknown)
            value.correct -> t(Msg.correct)
            else -> t(Msg.incorrect)
        } + (value.score?.let { " · $it" } ?: ""))
        if (responses) Text("${t(Msg.response)}: ${value.response}")
    }
}

@Composable
private fun SettingsUi(model: PlatformModel, state: UiState) {
    val t = LocalStrings.current
    val account = state.account ?: return
    var password by remember { mutableStateOf("") }
    var newPassword by remember { mutableStateOf("") }
    var confirmDelete by remember { mutableStateOf(false) }
    val activity = checkNotNull(LocalActivity.current)
    val provider = remember(activity) { GoogleIdentity(activity, BuildConfig.GOOGLE_CLIENT_ID) }
    val google: (suspend () -> IdentityGoogleProof)? = if (BuildConfig.GOOGLE_CLIENT_ID.isEmpty()) null else ({ provider.proof(model.api) })
    val hasPassword = "password" in account.sign_in_methods
    LazyColumn(modifier = Modifier.testTag("screen-list"), verticalArrangement = Arrangement.spacedBy(12.dp), contentPadding = PaddingValues(bottom = 24.dp)) {
        item { Title(t(Msg.settings)); Text(account.email); Text(t(Msg.access)) }
        item {
            Title(t(Msg.freshProof))
            if (hasPassword) Field(t(Msg.password), password, 128, true) { password = it }
            else if (google == null) Text(t(Msg.googleUnavailable))
            Title(t(Msg.changePassword))
            Field(t(Msg.newPassword), newPassword, 128, true) { newPassword = it }
            Action(t(Msg.changePassword), !state.busy && newPassword.length in 15..128 && (if (hasPassword) password.isNotEmpty() else google != null)) {
                model.sensitive("password", password, newPassword, google); password = ""; newPassword = ""
            }
            if (hasPassword && "google" !in account.sign_in_methods && google != null) {
                Action(t(Msg.connectGoogle), !state.busy && password.isNotEmpty()) {
                    model.sensitive("link", password, google = google); password = ""
                }
            }
        }
        item { Title(t(Msg.sessions)) }
        items(state.sessions, key = { it.id }) { session ->
            Text("${session.device_label} · ${session.last_used_at}")
            Action(t(Msg.revoke), !state.busy) { model.revoke(session.id, session.current) }
        }
        item { Action(t(Msg.revokeAll), !state.busy, model::revokeAll); Title(t(Msg.voiceRecords)) }
        if (state.recordings.isEmpty()) item { Text(t(Msg.noRecordings)) }
        items(state.recordings, key = { it.id }) { recording ->
            Text("${t(Msg.retentionUntil)}: ${recording.retention_until}")
            Action(t(Msg.withdraw), !state.busy) { model.withdraw(recording.id) }
        }
        item {
            Title(t(Msg.deleteAccount)); Text(t(Msg.deleteNotice))
            Check(t(Msg.confirmDelete), confirmDelete, !state.busy) { confirmDelete = it }
            Action(t(Msg.deleteAccount), confirmDelete && !state.busy && (if (hasPassword) password.isNotEmpty() else google != null)) {
                model.sensitive("delete", password, google = google); password = ""; newPassword = ""; confirmDelete = false
            }
        }
    }
}
