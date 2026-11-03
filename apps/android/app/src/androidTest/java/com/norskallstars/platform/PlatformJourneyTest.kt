package com.norskallstars.platform

import androidx.compose.ui.test.*
import androidx.compose.ui.graphics.asAndroidBitmap
import android.graphics.Bitmap
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import com.norskallstars.platform.data.*
import java.io.File
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.*
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test

/** Real backend, isolated approved synthetic scenario; no private test artifacts. */
class PlatformJourneyTest {
    @get:Rule val rule = createAndroidComposeRule<MainActivity>()
    private val api get() = (rule.activity.application as NorskAllstarsApplication).api
    private fun <T> probe(stage: String, work: suspend () -> T): T = runBlocking {
        try { work() }
        catch (failure: ApiFailure) {
            throw AssertionError("Native probe failed: $stage; status=${failure.status}; transport=${failure.transport}", failure)
        }
    }
    private fun waitFor(text: String) {
        rule.waitUntil(30000) {
            if (rule.onAllNodesWithText(text).fetchSemanticsNodes().isNotEmpty()) true
            else runCatching {
                rule.onNodeWithTag("screen-list").performScrollToNode(hasText(text))
                rule.onAllNodesWithText(text).fetchSemanticsNodes().isNotEmpty()
            }.getOrDefault(false)
        }
    }
    private fun click(text: String) {
        rule.onNodeWithTag("screen-list").performScrollToNode(hasText(text) and hasClickAction())
        // A committed response can arrive before the follow-up projection finishes.
        // Never turn a click on a disabled loading-state button into a false failure.
        rule.waitUntil(30000) {
            runCatching { rule.onNode(hasText(text) and hasClickAction()).assertIsEnabled() }.isSuccess
        }
        rule.onNode(hasText(text) and hasClickAction()).assertIsDisplayed().performClick()
    }
    private fun input(label: String, text: String) {
        rule.onNodeWithTag("screen-list").performScrollToNode(hasText(label) and hasSetTextAction())
        rule.onNode(hasText(label) and hasSetTextAction()).performTextInput(text)
        if (label == "Email" || label == "Password")
            rule.onNode(hasText(label) and hasSetTextAction()).performImeAction()
    }
    private fun acknowledge(id: String) {
        rule.onNodeWithTag("screen-list").performScrollToNode(hasTestTag("$id/ack"))
        rule.onNodeWithTag("$id/ack").performClick()
    }
    // Opt-in local evidence of this guarded synthetic journey only. CI does not
    // supply the argument or publish screenshots; the secure window stays enabled.
    private fun review(name: String) {
        if (InstrumentationRegistry.getArguments().getString("experienceReview") != "synthetic-only") return
        rule.waitForIdle()
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        File(context.cacheDir, "synthetic-review-$name.png").outputStream().use {
            rule.onRoot().captureToImage().asAndroidBitmap().compress(Bitmap.CompressFormat.PNG, 100, it)
        }
    }
    private fun finishAttempt() {
        // Await the real result screen, not a tight stream of server probes.
        // Failure to submit must fail this UI gate, never become a rate-limit storm.
        waitFor("Continue"); click("Continue")
        waitFor("Norwegian, one step at a time.")
    }

    @Test fun accountPinnedLearningPlacementReplayAndErasure() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val inputFile = File(context.filesDir, "synthetic-test-input.json")
        val document = Json.parseToJsonElement(inputFile.readText()).jsonObject
        inputFile.delete()
        val account = document.getValue("account").jsonObject
        val email = account.getValue("email").jsonPrimitive.content
        val password = account.getValue("password").jsonPrimitive.content
        val scenario = document.getValue("scenario").jsonObject
        rule.onNodeWithText("English").performClick()
        input("Email", email); input("Password", password); click("Send")
        waitFor("Norsk, ett steg om gangen.")
        rule.activityRule.scenario.recreate()
        waitFor("Norsk, ett steg om gangen.")
        rule.waitUntil(30000) { runCatching { rule.onNodeWithText("English").assertIsEnabled() }.isSuccess }
        rule.onNodeWithText("English").performClick()
        waitFor("Norwegian, one step at a time.")
        click("Start")
        waitFor("Find a starting point")
        val enrollment = probe("enrollment") { api.get<List<LearningEnrollmentSummary>>("/api/v1/learning/enrollments").single() }
        val pinned = enrollment.course.release_id
        click("Find a starting point")
        waitFor("Optional. A recommendation grants no completion or mastery.")
        val assessment = probe("assessment") { api.get<LearningAssessmentView>("/api/v1/learning/enrollments/${part(enrollment.id)}/placement") }
        click(scenario.getValue("correct_choice").jsonPrimitive.content)
        assessment.activities.forEach { acknowledge(it.activity_id) }
        click("Submit answers")
        waitFor("Accept recommendation")
        click("Accept recommendation")
        waitFor("Norwegian, one step at a time.")
        val advisory = probe("advisory result") { api.get<LearningEnrollmentView>("/api/v1/learning/enrollments/${part(enrollment.id)}") }
        assertTrue(advisory.progress.none { it.completion == "completed" })
        review("journey")
        click("Continue")
        waitFor(scenario.getValue("lesson_title").jsonPrimitive.content)
        val initialLesson = probe("initial lesson") { api.get<LearningLessonView>("/api/v1/learning/enrollments/${part(enrollment.id)}/lessons/${part(advisory.progress.first { it.available }.lesson_id)}") }
        val image = initialLesson.blocks.first { it.type == "image" && it.alt_text != null }
        val description = checkNotNull(image.alt_text)
        rule.waitUntil(30000) {
            if (rule.onAllNodesWithContentDescription(description).fetchSemanticsNodes().isNotEmpty()) true
            else runCatching {
                rule.onNodeWithTag("screen-list").performScrollToNode(hasContentDescription(description))
                rule.onAllNodesWithContentDescription(description).fetchSemanticsNodes().isNotEmpty()
            }.getOrDefault(false)
        }
        assertTrue(initialLesson.blocks.any { it.transcript != null })
        assertTrue(initialLesson.activities.any { it.stimuli.orEmpty().isNotEmpty() })
        review("reading")
        click("Inspect image")
        rule.onNodeWithText("Enlarge").assertIsDisplayed().performClick()
        // Native Back dismisses inspection, preserving the lesson and its state.
        InstrumentationRegistry.getInstrumentation().sendKeyDownUpSync(android.view.KeyEvent.KEYCODE_BACK)
        val inspectionModel = androidx.lifecycle.ViewModelProvider(rule.activity)[com.norskallstars.platform.ui.PlatformModel::class.java]
        assertEquals(com.norskallstars.platform.ui.Page.LESSON, inspectionModel.state.value.page)
        waitFor(scenario.getValue("lesson_title").jsonPrimitive.content)
        click("Start")
        waitFor("Submit answers")
        review("exercise")
        click(scenario.getValue("correct_choice").jsonPrimitive.content)
        val first = probe("canonical progress") { api.get<LearningEnrollmentView>("/api/v1/learning/enrollments/${part(enrollment.id)}") }
        val lessonId = first.progress.first { it.available && it.completion != "completed" }.lesson_id
        val lesson = probe("canonical lesson") { api.get<LearningLessonView>("/api/v1/learning/enrollments/${part(enrollment.id)}/lessons/${part(lessonId)}") }
        lesson.activities.forEach { acknowledge(it.activity_id) }
        click("Submit answers")
        waitFor("Continue")
        review("completion")
        finishAttempt()
        val canonical = probe("canonical completion") { api.get<LearningEnrollmentView>("/api/v1/learning/enrollments/${part(enrollment.id)}") }
        assertEquals(1, canonical.progress.count { it.completion == "completed" })
        // Replay the completed unit with the wrong choice; canonical credit survives.
        click("Practise again")
        waitFor("Practice does not change previous completion.")
        click("Start"); waitFor("Submit answers")
        click(scenario.getValue("alternative_choice").jsonPrimitive.content)
        lesson.activities.forEach { acknowledge(it.activity_id) }
        click("Submit answers")
        finishAttempt()
        assertEquals(2, probe("replay count") { api.get<Map<String, Int>>("/api/v1/learning/dashboard") }["submitted_attempts"])
        click("Continue"); click("Start"); waitFor("Submit answers")
        click("yellow square · water"); click("blue circle · shade")
        input("Answer", "An invented square signals water.")
        val afterFirst = probe("next progress") { api.get<LearningEnrollmentView>("/api/v1/learning/enrollments/${part(enrollment.id)}") }
        val next = afterFirst.progress.first { it.available && it.completion != "completed" }
        val second = probe("next lesson") { api.get<LearningLessonView>("/api/v1/learning/enrollments/${part(enrollment.id)}/lessons/${part(next.lesson_id)}") }
        second.activities.forEach { acknowledge(it.activity_id) }
        click("Submit answers")
        finishAttempt()
        assertEquals(3, probe("final count") { api.get<Map<String, Int>>("/api/v1/learning/dashboard") }["submitted_attempts"])
        val completed = probe("pinned completion") { api.get<LearningEnrollmentView>("/api/v1/learning/enrollments/${part(enrollment.id)}") }
        assertEquals(pinned, completed.course.release_id)
        assertEquals(2, completed.progress.count { it.completion == "completed" })
        assertTrue(completed.progress.any { it.completion != "completed" && it.available })
        click("Continue")
        waitFor(scenario.getValue("reading_title").jsonPrimitive.content)
        rule.onAllNodesWithText("Submit answers").assertCountEquals(0)
        rule.onAllNodesWithText("Start").assertCountEquals(0)
        click("Back")
        val afterReading = probe("reading does not grant credit") { api.get<LearningEnrollmentView>("/api/v1/learning/enrollments/${part(enrollment.id)}") }
        assertEquals(2, afterReading.progress.count { it.completion == "completed" })
        val history = probe("history") { api.post<LearningHistoryView, LearningHistoryInput>(
            "/api/v1/learning/enrollments/${part(enrollment.id)}/history", LearningHistoryInput(null, 25)) }
        assertTrue(history.attempts.any { it.evaluations?.any { evaluation -> evaluation.status == "pending" } == true })
        click("Attempts and history"); waitFor("Attempts and history")
        click("Back"); waitFor("Norwegian, one step at a time.")
        rule.waitUntil(30000) {
            runCatching { rule.onNodeWithText("Account", substring = false).assertIsEnabled() }.isSuccess
        }
        rule.onNodeWithText("Account", substring = false).assertIsDisplayed().performClick()
        waitFor("Confirm your identity")
        input("Password", password)
        click("I want to delete my account and data")
        click("Delete my account")
        rule.waitForIdle()
        val model = androidx.lifecycle.ViewModelProvider(rule.activity)[com.norskallstars.platform.ui.PlatformModel::class.java]
        assertTrue("Delete action did not reach the application model",
            model.state.value.busy || model.state.value.account == null || model.state.value.message != null)
        waitFor("Sign in")
        assertFalse(api.authenticated())
        assertFalse(File(context.noBackupFilesDir, "native-session").exists())
        assertTrue(File(context.cacheDir, "ephemeral-media").listFiles().orEmpty().isEmpty())
    }
}
