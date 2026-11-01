package com.norskallstars.platform.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import com.norskallstars.platform.data.*
import kotlinx.serialization.json.*

@Composable
fun ActivityUi(activity: LearningActivityView, value: LearningResponseInput?, enabled: Boolean,
    api: Api, media: NativeMedia, attempt: String?, onChange: (LearningResponseInput) -> Unit) {
    val t = LocalStrings.current
    val response = value ?: answer(activity.activity_id)
    val kind = presentationKind(activity)
    val options = activity.presentation?.options ?: activity.choices.map { LearningResponseOption(it, JsonPrimitive(it)) }
    val list = (response.response as? JsonArray)?.toList().orEmpty()
    fun change(next: JsonElement) { onChange(response.copy(response = next)) }
    Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Title(activity.prompt)
        activity.rubric?.forEach { Text(it) }
        when (kind) {
            "text" -> Field(t(Msg.response), (response.response as? JsonPrimitive)?.contentOrNull ?: "", enabled = enabled) { change(JsonPrimitive(it)) }
            "single_choice" -> options.forEach { option ->
                Radio(option.label, response.response == option.value, enabled) { change(option.value) }
            }
            "multiple_choice" -> options.forEach { option ->
                Check(option.label, option.value in list, enabled) { checked ->
                    change(JsonArray(if (checked) list + option.value else list.filterNot { it == option.value }))
                }
            }
            "ordering" -> {
                if (list.isEmpty()) Action(t(Msg.start), enabled) { change(JsonArray(options.map { it.value })) }
                list.forEachIndexed { index, element ->
                    Text(options.find { it.value == element }?.label ?: (index + 1).toString())
                    if (index > 0) Action("${t(Msg.up)} ${index + 1}", enabled) {
                        val next = list.toMutableList(); next[index] = next[index - 1]; next[index - 1] = element
                        change(JsonArray(next))
                    }
                    if (index < list.lastIndex) Action("${t(Msg.down)} ${index + 1}", enabled) {
                        val next = list.toMutableList(); next[index] = next[index + 1]; next[index + 1] = element
                        change(JsonArray(next))
                    }
                }
            }
            "matching" -> activity.presentation?.fields.orEmpty().forEachIndexed { index, field ->
                Text(field, style = MaterialTheme.typography.titleMedium)
                options.forEach { option ->
                    Radio("$field · ${option.label}", list.getOrNull(index) == option.value, enabled) {
                        val next = MutableList<JsonElement>(activity.presentation?.fields.orEmpty().size) { list.getOrNull(it) ?: JsonNull }
                        next[index] = option.value; change(JsonArray(next))
                    }
                }
            }
            "speech" -> Recorder(api, media, attempt, activity.activity_id, enabled) { recorded ->
                change(buildJsonObject { put("recorded", recorded) })
            }
            "acknowledgement" -> Unit
            else -> Text(t(Msg.error))
        }
        if (activity.evaluation_type == "self_assessment") {
            Check(t(Msg.selfAssessment), response.self_assessment == true, enabled) {
                onChange(response.copy(self_assessment = if (it) true else null))
            }
            Check(t(Msg.selfNo), response.self_assessment == false, enabled) {
                onChange(response.copy(self_assessment = if (it) false else null))
            }
        }
        Check(t(Msg.acknowledged), response.acknowledged, enabled && kind != null,
            Modifier.testTag("${activity.activity_id}/ack")) {
            onChange(response.copy(acknowledged = it))
        }
    } }
}
