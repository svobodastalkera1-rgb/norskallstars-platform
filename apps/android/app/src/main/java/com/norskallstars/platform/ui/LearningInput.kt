package com.norskallstars.platform.ui

import com.norskallstars.platform.data.LearningActivityView
import com.norskallstars.platform.data.LearningResponseInput
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull

/** Presentation only. Evaluation, completion and mastery stay on the server. */
fun presentationKind(activity: LearningActivityView): String? {
    activity.presentation?.let {
        return it.kind.takeIf { kind -> kind in setOf("text", "speech", "single_choice", "multiple_choice", "ordering", "matching", "acknowledgement") }
    }
    return when (activity.response_mode) {
        "text", "reflection" -> "text"
        "speech" -> "speech"
        "choice" -> if (activity.type == "multiple_choice") "multiple_choice" else "single_choice"
        "action" -> "acknowledgement"
        else -> null
    }
}

fun answer(activity: String, response: JsonElement = JsonNull, acknowledged: Boolean = false, self: Boolean? = null) =
    LearningResponseInput(acknowledged, activity, response, self)

/** Monotonic UI evidence gate; server still decides/counts heartbeat intervals. */
class Engagement {
    var foreground = false
    private var interaction: Long? = null
    fun interact(now: Long) { interaction = now }
    fun eligible(now: Long): Boolean = foreground && interaction?.let { now >= it && now - it <= 30000 } == true
}
