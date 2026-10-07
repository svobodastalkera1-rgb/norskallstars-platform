"""Bounded learner inputs and explicit projections; never return raw package/ORM data."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, JsonValue, StrictBool, model_validator

from norskallstars_backend.learning.policy import Id


class LearningDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class EnrollInput(LearningDTO):
    course_id: Id


class StartInput(LearningDTO):
    operation_id: UUID
    lesson_id: Id
    kind: Literal["canonical", "practice"]


class ResponseInput(LearningDTO):
    activity_id: Id
    response: JsonValue
    acknowledged: StrictBool
    self_assessment: StrictBool | None = None


class SubmitInput(LearningDTO):
    acknowledged: StrictBool
    responses: Annotated[list[ResponseInput], Field(max_length=200)]

    @model_validator(mode="after")
    def unique_responses(self) -> "SubmitInput":
        if len({r.activity_id for r in self.responses}) != len(self.responses):
            raise ValueError("Duplicate activity")
        return self


class PlacementInput(SubmitInput):
    operation_id: UUID


class HistoryInput(LearningDTO):
    before: UUID | None = None
    limit: Annotated[int, Field(strict=True, ge=1, le=100)] = 25


class TranslationInput(LearningDTO):
    operation_id: UUID
    lesson_id: Id
    block_id: Id


class MasteryView(LearningDTO):
    status: Literal["unknown", "not_applicable", "assessed"]
    value: bool | None
    score: Decimal | None


class ProgressView(LearningDTO):
    lesson_id: str
    completion: Literal["not_started", "in_progress", "completed"]
    completed_at: datetime | None
    mastery: MasteryView
    available: bool
    review_due_at: datetime | None


class LessonSummary(LearningDTO):
    lesson_id: str
    version: str
    title: str


class ChapterView(LearningDTO):
    chapter_id: str
    title: str
    lessons: list[LessonSummary]


class CourseView(LearningDTO):
    course_id: str
    release_id: UUID
    course_version: str
    language: str
    title: str


class EnrollmentSummary(LearningDTO):
    id: UUID
    course: CourseView
    policy_version: str
    policy_digest: str
    created_at: datetime


class EnrollmentView(LearningDTO):
    id: UUID
    course: CourseView
    policy_version: str
    policy_digest: str
    created_at: datetime
    recommended_lesson_id: str | None
    chapters: list[ChapterView]
    progress: list[ProgressView]
    concepts: dict[str, MasteryView]
    placement_available: bool


class ActivityView(LearningDTO):
    activity_id: str
    type: str
    response_mode: str
    evaluation_type: str
    prompt: str
    choices: list[str]
    rubric: list[str] | None


class BlockView(LearningDTO):
    block_id: str
    type: str
    order: int
    text: str | None
    language: str | None
    asset_ref: str | None
    activity_ref: str | None
    alt_text: str | None
    translation_available: bool


class LessonView(LearningDTO):
    lesson_id: str
    version: str
    title: str
    blocks: list[BlockView]
    activities: list[ActivityView]


class EvaluationView(LearningDTO):
    activity_id: str
    response: JsonValue
    normalized: JsonValue
    status: Literal["scored", "self_assessed", "pending", "not_applicable"]
    score: Decimal | None
    correct: bool | None
    evaluator: str
    evaluator_version: str


class AttemptView(LearningDTO):
    id: UUID
    lesson_id: str
    lesson_version: str
    kind: Literal["canonical", "practice"]
    started_at: datetime
    submitted_at: datetime | None
    evaluations: list[EvaluationView] | None
    completion_credit: bool | None
    policy_version: str
    policy_digest: str


class HistoryView(LearningDTO):
    attempts: list[AttemptView]
    next_before: UUID | None


class ReviewView(LearningDTO):
    lesson_id: str
    due_at: datetime


class PlacementView(LearningDTO):
    id: UUID
    score: Decimal
    recommended_lesson_id: str
    assessment_version: str
    policy_version: str
    policy_digest: str
    created_at: datetime


class TranslationView(LearningDTO):
    reference_text: str


class AssessmentView(LearningDTO):
    assessment_version: str
    policy_version: str
    policy_digest: str
    activities: list[ActivityView]
