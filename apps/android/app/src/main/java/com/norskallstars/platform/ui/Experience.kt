package com.norskallstars.platform.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.unit.dp
import com.norskallstars.platform.data.*

/** Presentation only: server DTOs, never Course Package parsing or credit rules. */
data class ExperienceItem(val block: LearningBlockView?, val activity: LearningActivityView?)

fun experienceSequence(lesson: LearningLessonView): List<ExperienceItem> {
    val activities = lesson.activities.associateBy { it.activity_id }
    require(activities.size == lesson.activities.size)
    val seen = mutableSetOf<String>()
    val result = lesson.blocks.sortedBy { it.order }.map { block ->
        val reference = block.activity_ref
        val activity = if (reference == null) null else {
            require(activities.containsKey(reference))
            if (seen.add(reference)) activities[reference] else null
        }
        ExperienceItem(block, activity)
    }.toMutableList()
    lesson.activities.filter { it.activity_id !in seen }.forEach { result += ExperienceItem(null, it) }
    return result
}

val LocalExperience = staticCompositionLocalOf { false }
val NorthIron = Color(0xFF101E24)
val NorthPaper = Color(0xFFEEE9DC)
val NorthInk = Color(0xFF1B302F)
val NorthFire = Color(0xFFEDC185)
val NorthColors = darkColorScheme(
    primary = NorthFire, onPrimary = NorthIron,
    secondary = Color(0xFFB9CFCE), onSecondary = NorthIron,
    background = NorthIron, onBackground = Color(0xFFEEF1E9),
    surface = Color(0xFF172D32), onSurface = Color(0xFFEEF1E9),
    surfaceVariant = Color(0xFF283F42), onSurfaceVariant = Color(0xFFD5E0DB),
    surfaceContainerLowest = Color(0xFF0B171D), surfaceContainerLow = Color(0xFF12252B),
    surfaceContainer = Color(0xFF172D32), surfaceContainerHigh = Color(0xFF21383C),
    surfaceContainerHighest = Color(0xFF283F42), surfaceDim = NorthIron,
    surfaceBright = Color(0xFF30484B), surfaceTint = NorthFire,
    primaryContainer = Color(0xFF3E4432), onPrimaryContainer = Color(0xFFFFF1D2),
    secondaryContainer = Color(0xFF304B4B), onSecondaryContainer = Color(0xFFE6ECE6),
    tertiary = Color(0xFFD5B183), onTertiary = Color(0xFF31281C),
    tertiaryContainer = Color(0xFF443B2C), onTertiaryContainer = Color(0xFFF4E4C7),
    inverseSurface = NorthPaper, inverseOnSurface = NorthInk, inversePrimary = Color(0xFF6A4F2A),
    errorContainer = Color(0xFF48272C), onErrorContainer = Color(0xFFFFDED5),
    error = Color(0xFFFFB7A9), onError = Color(0xFF42252A), outline = Color(0xFF9DB2B3),
)
val NorthShapes = Shapes(
    extraSmall = RoundedCornerShape(2.dp), small = RoundedCornerShape(2.dp),
    medium = RoundedCornerShape(2.dp), large = RoundedCornerShape(2.dp), extraLarge = RoundedCornerShape(2.dp),
)

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun ExperienceProgress(progress: List<LearningProgressView>) {
    val t = LocalStrings.current
    val done = progress.count { it.completion == "completed" }
    Column(Modifier.fillMaxWidth().padding(vertical = 12.dp)) {
        FlowRow(Modifier.clearAndSetSemantics { contentDescription = "${t(Msg.progress)}: $done/${progress.size}" },
            horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            progress.forEach { state ->
                Text(if (state.completion == "completed") "▲" else "△",
                    color = if (state.completion == "completed") NorthFire else MaterialTheme.colorScheme.secondary)
            }
        }
        Text("$done / ${progress.size} · ${t(Msg.completed)}", style = MaterialTheme.typography.labelLarge)
    }
}
