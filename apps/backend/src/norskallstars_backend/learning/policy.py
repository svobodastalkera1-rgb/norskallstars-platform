"""Versioned PLATFORM rules: not an extension or reinterpretation of Course Package v1."""

import hashlib
import json
from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, StrictBool, model_validator

Id = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{1,127}$")]
Score = Annotated[Decimal, Field(ge=0, le=1, allow_inf_nan=False, decimal_places=9)]


class Rule(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class Normalizer(Rule):
    # Explicit binding to a package flag, no inferred names or linguistic defaults.
    flag: Annotated[str, Field(min_length=1, max_length=64)]
    operation: Literal["trim", "case_fold", "unicode_nfc"]


class ActivityRule(Rule):
    comparison: Literal["exact", "unordered"]
    # null means use Contract scalar accepted_answers. Structured answers need explicit rules.
    accepted_responses: Annotated[list[JsonValue], Field(min_length=1, max_length=200)] | None
    normalization: Annotated[list[Normalizer], Field(max_length=8)]
    display_prompt: Annotated[str, Field(min_length=1, max_length=16384)] | None
    display_choices: Annotated[list[str], Field(max_length=200)] | None


class ReviewRule(Rule):
    intervals_seconds: Annotated[
        list[Annotated[int, Field(strict=True, ge=60, le=31536000)]],
        Field(min_length=1, max_length=32),
    ]
    success_score: Score
    on_failure: Literal["reset", "retain"]


class LessonRule(Rule):
    required_activities: Annotated[list[Id], Field(max_length=200)]
    require_evaluation: StrictBool
    completion_score: Score | None
    mastery_score: Score | None
    review: ReviewRule | None

    @model_validator(mode="after")
    def unique_required(self) -> "LessonRule":
        if len(set(self.required_activities)) != len(self.required_activities):
            raise ValueError("Duplicate required activity")
        if (
            self.completion_score is not None or self.mastery_score is not None
        ) and not self.required_activities:
            raise ValueError("A score requires activity evidence")
        return self


class ConceptRule(Rule):
    required_lessons: Annotated[list[Id], Field(min_length=1, max_length=2000)]
    mastery_score: Score


class PlacementBand(Rule):
    minimum_score: Score
    lesson_id: Id


class PlacementRule(Rule):
    assessment_version: Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")]
    activity_ids: Annotated[list[Id], Field(min_length=1, max_length=200)]
    recommendations: Annotated[list[PlacementBand], Field(min_length=1, max_length=2000)]


class LearningPolicy(Rule):
    policy_version: Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")]
    # No pedagogical defaults, including no score, review interval or inferred assessment.
    lessons: Annotated[dict[Id, LessonRule], Field(min_length=1, max_length=2000)]
    activities: Annotated[dict[Id, ActivityRule], Field(max_length=2000)]
    concepts: Annotated[dict[Id, ConceptRule], Field(max_length=2000)]
    placement: PlacementRule | None
    # Byte-bound acknowledgment: opaque upstream extensions are NOT grading/scheduling rules.
    package_policy_inputs: dict[str, str]

    def document(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    def digest(self) -> str:
        return hashlib.sha256(
            json.dumps(
                self.document(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode()
        ).hexdigest()


def validate_policy(policy: LearningPolicy, documents: dict[str, Any]) -> None:
    """Require full explicit coverage; reject unsupported semantics before selection."""
    if len(json.dumps(documents, ensure_ascii=False).encode()) > 8 * 1024 * 1024:
        raise ValueError("Learning snapshot exceeds runtime resource budget")
    lessons = {v["lesson_id"]: v for k, v in documents.items() if k.startswith("lessons/")}
    activities = {v["activity_id"]: v for k, v in documents.items() if k.startswith("activities/")}
    if set(policy.lessons) != set(lessons) or set(policy.activities) != set(activities):
        raise ValueError("Policy coverage mismatch")
    chapters = {v["chapter_id"]: v for k, v in documents.items() if k.startswith("chapters/")}
    chapter_order = documents["course.json"]["chapters"]
    lesson_order = [lid for cid in chapter_order for lid in chapters[cid]["lesson_refs"]]
    for position, cid in enumerate(chapter_order):
        if not set(chapters[cid]["prerequisites"]) <= set(chapter_order[:position]):
            raise ValueError("Chapter prerequisite conflicts with linear path")
    for position, lid in enumerate(lesson_order):
        if not set(lessons[lid]["prerequisites"]) <= set(lesson_order[:position]):
            raise ValueError("Lesson prerequisite conflicts with linear path")
    for lid, rule in policy.lessons.items():
        if not set(rule.required_activities) <= set(lessons[lid]["activity_refs"]):
            raise ValueError("Required activity outside lesson")
        if len(lessons[lid]["activity_refs"]) > 200:
            raise ValueError("Lesson exceeds bounded activity submission limit")
        needs_score = (
            rule.require_evaluation
            or rule.completion_score is not None
            or rule.mastery_score is not None
            or rule.review is not None
        )
        if needs_score and any(
            activities[aid]["evaluation"]["type"] not in ("deterministic", "self_assessment")
            for aid in rule.required_activities
        ):
            raise ValueError("Future evaluators cannot be a required learning gate")
    extensions = {}
    for path, component in documents.items():
        if path.startswith(("lessons/", "chapters/")):
            for field in ("completion", "review"):
                if component[field] is not None:
                    extensions[path + "#" + field] = hashlib.sha256(
                        json.dumps(
                            component[field],
                            sort_keys=True,
                            separators=(",", ":"),
                            ensure_ascii=False,
                        ).encode()
                    ).hexdigest()
    if policy.package_policy_inputs != extensions:
        raise ValueError("Opaque package policies need exact explicit acknowledgment")
    for aid, activity_rule in policy.activities.items():
        activity = activities[aid]
        flags = activity.get("normalization", {})
        bindings = [b.flag for b in activity_rule.normalization]
        if len(set(bindings)) != len(bindings) or set(bindings) != set(flags):
            raise ValueError("Every normalization flag needs an explicit binding")
        if any(type(value) is not bool for value in flags.values()):
            raise ValueError("Unsupported normalization flag")
        if activity["evaluation"]["type"] == "deterministic":
            accepted = (
                activity_rule.accepted_responses
                if activity_rule.accepted_responses is not None
                else activity.get("accepted_answers")
            )
            if not accepted or any(answer is None for answer in accepted):
                raise ValueError("Deterministic activity has no explicit answer rules")
            if activity_rule.comparison == "unordered" and any(
                not isinstance(answer, list) for answer in accepted
            ):
                raise ValueError("Unordered comparison requires lists")
        # Arbitrary prompt/choice objects must not disclose hidden answer/internal fields.
        if not isinstance(activity["prompt"], str) and activity_rule.display_prompt is None:
            raise ValueError("Object prompts need a reviewed public presentation")
        if (
            any(not isinstance(choice, str) for choice in activity.get("choices", []))
            and activity_rule.display_choices is None
        ):
            raise ValueError("Object choices need a reviewed public presentation")
    known_concepts = {c["concept_id"] for c in documents["course.json"].get("concepts", [])}
    if not set(policy.concepts) <= known_concepts:
        raise ValueError("Unknown concept")
    for concept in policy.concepts.values():
        if len(set(concept.required_lessons)) != len(concept.required_lessons) or not set(
            concept.required_lessons
        ) <= set(lessons):
            raise ValueError("Invalid concept evidence")
    if policy.placement:
        placement = policy.placement
        if len(set(placement.activity_ids)) != len(placement.activity_ids) or not set(
            placement.activity_ids
        ) <= set(activities):
            raise ValueError("Invalid assessment references")
        if any(
            activities[aid]["evaluation"]["type"] != "deterministic"
            for aid in placement.activity_ids
        ):
            raise ValueError("Placement needs deterministic evidence")
        scores = [b.minimum_score for b in placement.recommendations]
        if (
            scores != sorted(set(scores))
            or scores[0] != 0
            or any(b.lesson_id not in lessons for b in placement.recommendations)
        ):
            raise ValueError("Assessment needs ordered, complete recommendation bands")
