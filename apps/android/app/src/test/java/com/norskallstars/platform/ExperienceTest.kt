package com.norskallstars.platform

import com.norskallstars.platform.data.*
import com.norskallstars.platform.ui.experienceSequence
import kotlinx.serialization.json.Json
import org.junit.Assert.*
import org.junit.Test

class ExperienceTest {
    private fun lesson(reference: String = "synthetic.task"): LearningLessonView = Json.decodeFromString("""
        {"lesson_id":"synthetic.lesson","version":"1.0.0","title":"Synthetic",
         "activities":[{"activity_id":"synthetic.task","type":"single_choice","response_mode":"choice","evaluation_type":"deterministic","prompt":"Synthetic","choices":[],"rubric":null}],
         "blocks":[{"block_id":"after","type":"text","order":3,"text":"Synthetic after","language":"en","asset_ref":null,"activity_ref":null,"alt_text":null,"translation_available":false},
         {"block_id":"task","type":"activity","order":2,"text":null,"language":null,"asset_ref":null,"activity_ref":"$reference","alt_text":null,"translation_available":false},
         {"block_id":"before","type":"text","order":1,"text":"Synthetic before","language":"en","asset_ref":null,"activity_ref":null,"alt_text":null,"translation_available":false}]}
    """)
    @Test fun authoredOrderInterleavesWithoutDuplicatingAnActivity() {
        val source = lesson()
        val result = experienceSequence(source.copy(blocks = source.blocks + source.blocks[1].copy(block_id = "repeated", order = 4)))
        assertEquals(listOf("before", "task", "after", "repeated"), result.map { it.block?.block_id })
        assertEquals(1, result.count { it.activity != null })
    }
    @Test fun unreferencedActivityRetainsDeclaredOrder() {
        assertEquals("synthetic.task", experienceSequence(lesson().copy(blocks = emptyList())).single().activity?.activity_id)
    }
    @Test(expected = IllegalArgumentException::class) fun unknownReferenceFailsClosed() { experienceSequence(lesson("foreign.task")) }
    @Test(expected = IllegalArgumentException::class) fun duplicateActivityFailsClosed() {
        val source = lesson(); experienceSequence(source.copy(activities = source.activities + source.activities))
    }
    @Test fun readingRemainsContentWithoutNewCompletionState() {
        val source = lesson(); val reading = source.copy(activities = emptyList(), blocks = source.blocks.filter { it.activity_ref == null })
        assertTrue(experienceSequence(reading).all { it.activity == null })
    }
}
