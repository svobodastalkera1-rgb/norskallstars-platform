"""Transactional account-owned learning; no storage delivery or privileged HTTP operations."""

import hashlib
import json
from datetime import timedelta
from decimal import Decimal
from typing import Any, Literal, cast
from uuid import UUID

from sqlalchemy import func, select, text, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from norskallstars_backend.course_packages.catalog import (
    PublishedContent,
    published_content,
    published_summary,
)
from norskallstars_backend.course_packages.service import actor_valid
from norskallstars_backend.database import Database
from norskallstars_backend.identity.service import Identity, Principal, now
from norskallstars_backend.learning import dto
from norskallstars_backend.learning.evaluation import (
    DeterministicPlacement,
    Evaluator,
    LocalEvaluator,
    PlacementStrategy,
)
from norskallstars_backend.learning.models import (
    Attempt,
    CourseSelection,
    Enrollment,
    LearningEvent,
    LessonProgress,
    PlacementResult,
    PolicyAudit,
    RuleSet,
)
from norskallstars_backend.learning.policy import LearningPolicy, validate_policy


class LearningError(Exception):
    def __init__(self, status: int = 404, code: str = "not_found") -> None:
        self.status, self.code = status, code


def request_digest(data: dto.LearningDTO) -> str:
    return hashlib.sha256(
        json.dumps(
            data.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def ordered_lessons(content: PublishedContent) -> list[dict[str, Any]]:
    docs = content.documents
    return [
        docs[f"lessons/{lid}.json"]
        for cid in docs["course.json"]["chapters"]
        for lid in docs[f"chapters/{cid}.json"]["lesson_refs"]
    ]


def course_view(content: PublishedContent) -> dto.CourseView:
    course = content.documents["course.json"]
    return dto.CourseView(
        course_id=content.course_id,
        release_id=content.id,
        course_version=content.version,
        language=course["language"],
        title=course["title"],
    )


async def select_learning_release(
    database: Database, release_id: UUID, policy: LearningPolicy, *, actor: str, approval: str
) -> UUID:
    """Trusted operator/OS/DB privileges only. Policy selection NEVER publishes a release."""
    actor_valid(actor, approval)
    async with database.transaction() as db:
        content = await published_content(db, release_id)
        if content is None:
            raise LearningError(409, "release_unavailable")
        try:
            validate_policy(policy, content.documents)
        except ValueError:
            raise LearningError(409, "unsupported_learning_policy") from None
        key = int.from_bytes(
            hashlib.sha256(("learning-selection:" + content.course_id).encode()).digest()[:8],
            signed=True,
        )
        await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
        existing = await db.scalar(
            select(RuleSet).where(
                RuleSet.release_id == release_id, RuleSet.version == policy.policy_version
            )
        )
        if existing is None:
            existing = RuleSet(
                release_id=release_id,
                version=policy.policy_version,
                digest=policy.digest(),
                document=policy.document(),
                created_at=now(),
            )
            db.add(existing)
            await db.flush()
        elif existing.digest != policy.digest():
            raise LearningError(409, "policy_version_conflict")
        selection = await db.get(CourseSelection, content.course_id, with_for_update=True)
        if selection is None:
            db.add(
                CourseSelection(
                    course_id=content.course_id, release_id=release_id, policy_id=existing.id
                )
            )
        elif selection.release_id == release_id and selection.policy_id == existing.id:
            return existing.id
        else:
            selection.release_id, selection.policy_id = release_id, existing.id
        db.add(PolicyAudit(policy_id=existing.id, actor=actor, approval=approval, created_at=now()))
        return existing.id


class Learning:
    def __init__(
        self,
        database: Database,
        identity: Identity,
        evaluator: Evaluator | None = None,
        placement: PlacementStrategy | None = None,
    ) -> None:
        self.database, self.identity = database, identity
        self.evaluator = evaluator or LocalEvaluator()
        self.placement = placement or DeterministicPlacement()

    async def owned(
        self, db: AsyncSession, principal: Principal, enrollment_id: UUID
    ) -> Enrollment:
        await self.identity.locked_principal(db, principal)
        enrollment = await db.scalar(
            select(Enrollment)
            .where(Enrollment.id == enrollment_id, Enrollment.account_id == principal.account_id)
            .with_for_update()
        )
        if enrollment is None:
            raise LearningError()
        return enrollment

    async def context(
        self, db: AsyncSession, enrollment: Enrollment
    ) -> tuple[PublishedContent, RuleSet, LearningPolicy]:
        content = await published_content(db, enrollment.release_id)
        rules = await db.get(RuleSet, enrollment.policy_id)
        if content is None or rules is None:
            raise LearningError(409, "release_unavailable")
        return content, rules, LearningPolicy.model_validate(rules.document)

    async def catalog(self, principal: Principal) -> list[dto.CourseView]:
        async with self.database.transaction() as db:
            await self.identity.locked_principal(db, principal)
            selections = (
                await db.scalars(
                    select(CourseSelection).order_by(CourseSelection.course_id).limit(101)
                )
            ).all()
            if len(selections) > 100:
                raise LearningError(503, "catalog_limit")
            result = []
            for selection in selections:
                summary = await published_summary(db, selection.release_id)
                if summary:
                    result.append(
                        dto.CourseView(
                            course_id=summary.course_id,
                            release_id=summary.id,
                            course_version=summary.version,
                            language=summary.language,
                            title=summary.title,
                        )
                    )
            return result

    async def enroll(self, principal: Principal, course_id: str) -> dto.EnrollmentView:
        async with self.database.transaction() as db:
            await self.identity.locked_principal(db, principal)
            existing = await db.scalar(
                select(Enrollment)
                .where(
                    Enrollment.account_id == principal.account_id, Enrollment.course_id == course_id
                )
                .with_for_update()
            )
            if existing is None:
                selection = await db.get(CourseSelection, course_id, with_for_update=True)
                if selection is None or await published_content(db, selection.release_id) is None:
                    raise LearningError()
                count = await db.scalar(
                    select(func.count())
                    .select_from(Enrollment)
                    .where(Enrollment.account_id == principal.account_id)
                )
                if (count or 0) >= 100:
                    raise LearningError(409, "enrollment_limit")
                existing = Enrollment(
                    account_id=principal.account_id,
                    course_id=course_id,
                    release_id=selection.release_id,
                    policy_id=selection.policy_id,
                    created_at=now(),
                )
                db.add(existing)
                await db.flush()
            return await self.enrollment_view(db, existing)

    async def enrollments(self, principal: Principal) -> list[dto.EnrollmentSummary]:
        async with self.database.transaction() as db:
            await self.identity.locked_principal(db, principal)
            records = (
                await db.scalars(
                    select(Enrollment)
                    .where(Enrollment.account_id == principal.account_id)
                    .order_by(Enrollment.created_at)
                    .limit(101)
                )
            ).all()
            if len(records) > 100:
                raise LearningError(503, "enrollment_limit")
            result = []
            for enrollment in records:
                summary = await published_summary(db, enrollment.release_id)
                rules = await db.get(RuleSet, enrollment.policy_id)
                if summary is None or rules is None:
                    raise LearningError(409, "release_unavailable")
                result.append(
                    dto.EnrollmentSummary(
                        id=enrollment.id,
                        course=dto.CourseView(
                            course_id=summary.course_id,
                            release_id=summary.id,
                            course_version=summary.version,
                            language=summary.language,
                            title=summary.title,
                        ),
                        policy_version=rules.version,
                        policy_digest=rules.digest,
                        created_at=enrollment.created_at,
                    )
                )
            return result

    async def progress(self, db: AsyncSession, enrollment: Enrollment) -> dict[str, LessonProgress]:
        return {
            p.lesson_id: p
            for p in (
                await db.scalars(
                    select(LessonProgress).where(LessonProgress.enrollment_id == enrollment.id)
                )
            ).all()
        }

    def available(
        self, content: PublishedContent, progress: dict[str, LessonProgress], lid: str
    ) -> bool:
        completed = {key for key, p in progress.items() if p.completed_at is not None}
        for lesson in ordered_lessons(content):
            if lesson["lesson_id"] == lid:
                return set(lesson["prerequisites"]) <= completed
            if lesson["lesson_id"] not in completed:
                return False
        return False

    async def enrollment_view(self, db: AsyncSession, enrollment: Enrollment) -> dto.EnrollmentView:
        content, rules, policy = await self.context(db, enrollment)
        progress = await self.progress(db, enrollment)
        views = []
        for lesson in ordered_lessons(content):
            lid = lesson["lesson_id"]
            state = progress.get(lid)
            views.append(
                dto.ProgressView(
                    lesson_id=lid,
                    completion="completed"
                    if state and state.completed_at
                    else "in_progress"
                    if state
                    else "not_started",
                    completed_at=state.completed_at if state else None,
                    mastery=dto.MasteryView(
                        status=cast(
                            Literal["unknown", "not_applicable", "assessed"],
                            state.mastery_status
                            if state
                            else "not_applicable"
                            if policy.lessons[lid].mastery_score is None
                            else "unknown",
                        ),
                        value=state.mastered if state else None,
                        score=state.score if state else None,
                    ),
                    available=self.available(content, progress, lid),
                    review_due_at=state.review_due_at if state else None,
                )
            )
        concepts: dict[str, dto.MasteryView] = {}
        for cid, rule in policy.concepts.items():
            scores = [
                progress[lid].score if lid in progress else None for lid in rule.required_lessons
            ]
            score = (
                None
                if any(s is None for s in scores)
                else sum((s for s in scores if s is not None), Decimal(0)) / len(scores)
            )
            concepts[cid] = dto.MasteryView(
                status="unknown" if score is None else "assessed",
                value=None if score is None else score >= rule.mastery_score,
                score=score,
            )
        chapters = [
            dto.ChapterView(
                chapter_id=cid,
                title=content.documents[f"chapters/{cid}.json"]["title"],
                lessons=[
                    dto.LessonSummary(
                        lesson_id=lesson["lesson_id"],
                        version=lesson["version"],
                        title=lesson["title"],
                    )
                    for lesson in ordered_lessons(content)
                    if lesson["chapter_id"] == cid
                ],
            )
            for cid in content.documents["course.json"]["chapters"]
        ]
        return dto.EnrollmentView(
            id=enrollment.id,
            course=course_view(content),
            policy_version=rules.version,
            policy_digest=rules.digest,
            created_at=enrollment.created_at,
            recommended_lesson_id=enrollment.recommended_lesson_id,
            chapters=chapters,
            progress=views,
            concepts=concepts,
            placement_available=policy.placement is not None,
        )

    async def view(self, principal: Principal, enrollment_id: UUID) -> dto.EnrollmentView:
        async with self.database.transaction() as db:
            return await self.enrollment_view(db, await self.owned(db, principal, enrollment_id))

    def lesson_document(self, content: PublishedContent, lid: str) -> dict[str, Any]:
        lesson = content.documents.get(f"lessons/{lid}.json")
        if not isinstance(lesson, dict):
            raise LearningError()
        return lesson

    def activity_view(
        self, content: PublishedContent, policy: LearningPolicy, aid: str
    ) -> dto.ActivityView:
        activity = content.documents[f"activities/{aid}.json"]
        rule = policy.activities[aid]
        return dto.ActivityView(
            activity_id=aid,
            presentation=rule.presentation,
            type=activity["type"],
            response_mode=activity["response_mode"],
            evaluation_type=activity["evaluation"]["type"],
            prompt=rule.display_prompt if rule.display_prompt is not None else activity["prompt"],
            choices=rule.display_choices
            if rule.display_choices is not None
            else activity.get("choices", []),
            rubric=activity["evaluation"].get("rubric"),
        )

    async def lesson(self, principal: Principal, enrollment_id: UUID, lid: str) -> dto.LessonView:
        async with self.database.transaction() as db:
            enrollment = await self.owned(db, principal, enrollment_id)
            content, _, policy = await self.context(db, enrollment)
            lesson = self.lesson_document(content, lid)
            if (
                not self.available(content, await self.progress(db, enrollment), lid)
                and enrollment.recommended_lesson_id != lid
            ):
                raise LearningError(409, "lesson_locked")
            blocks = [
                dto.BlockView(
                    block_id=b["block_id"],
                    type=b["type"],
                    order=b["order"],
                    text=b.get("text"),
                    language=b.get("language"),
                    asset_ref=b.get("asset_ref"),
                    activity_ref=b.get("activity_ref"),
                    alt_text=b.get("alt_text"),
                    translation_available=isinstance(b.get("reference_text"), str),
                )
                for b in lesson["blocks"]
            ]
            return dto.LessonView(
                lesson_id=lid,
                version=lesson["version"],
                title=lesson["title"],
                blocks=blocks,
                activities=[
                    self.activity_view(content, policy, aid) for aid in lesson["activity_refs"]
                ],
            )

    def event(
        self,
        db: AsyncSession,
        enrollment: Enrollment,
        operation_id: UUID,
        kind: str,
        lid: str,
        block_id: str | None = None,
    ) -> None:
        db.add(
            LearningEvent(
                enrollment_id=enrollment.id,
                operation_id=operation_id,
                kind=kind,
                lesson_id=lid,
                block_id=block_id,
                created_at=now(),
            )
        )

    async def start(
        self, principal: Principal, enrollment_id: UUID, data: dto.StartInput
    ) -> dto.AttemptView:
        async with self.database.transaction() as db:
            enrollment = await self.owned(db, principal, enrollment_id)
            content, rules, policy = await self.context(db, enrollment)
            lesson = self.lesson_document(content, data.lesson_id)
            existing = await db.scalar(
                select(Attempt).where(
                    Attempt.enrollment_id == enrollment.id,
                    Attempt.operation_id == data.operation_id,
                )
            )
            if existing:
                if existing.lesson_id != data.lesson_id or existing.kind != data.kind:
                    raise LearningError(409, "operation_conflict")
                return self.attempt_view(existing, rules)
            progress = await self.progress(db, enrollment)
            completed = (
                data.lesson_id in progress and progress[data.lesson_id].completed_at is not None
            )
            if data.kind == "canonical" and not self.available(content, progress, data.lesson_id):
                raise LearningError(409, "lesson_locked")
            if (
                data.kind == "practice"
                and not completed
                and enrollment.recommended_lesson_id != data.lesson_id
            ):
                raise LearningError(409, "lesson_locked")
            open_count = await db.scalar(
                select(func.count())
                .select_from(Attempt)
                .where(Attempt.enrollment_id == enrollment.id, Attempt.submitted_at.is_(None))
            )
            if (open_count or 0) >= 20:
                raise LearningError(409, "attempt_limit")
            attempt = Attempt(
                enrollment_id=enrollment.id,
                operation_id=data.operation_id,
                lesson_id=data.lesson_id,
                lesson_version=lesson["version"],
                kind=data.kind,
                started_at=now(),
            )
            db.add(attempt)
            if data.lesson_id not in progress:
                db.add(
                    LessonProgress(
                        enrollment_id=enrollment.id,
                        lesson_id=data.lesson_id,
                        mastery_status="not_applicable"
                        if policy.lessons[data.lesson_id].mastery_score is None
                        else "unknown",
                        review_step=0,
                        updated_at=now(),
                    )
                )
            self.event(db, enrollment, data.operation_id, "attempt_started", data.lesson_id)
            await db.flush()
            return self.attempt_view(attempt, rules)

    def attempt_view(self, attempt: Attempt, rules: RuleSet) -> dto.AttemptView:
        return dto.AttemptView(
            id=attempt.id,
            lesson_id=attempt.lesson_id,
            lesson_version=attempt.lesson_version,
            kind=cast(Literal["canonical", "practice"], attempt.kind),
            active_seconds=attempt.active_seconds,
            started_at=attempt.started_at,
            submitted_at=attempt.submitted_at,
            evaluations=attempt.results["evaluations"] if attempt.results else None,
            completion_credit=attempt.results["completion_credit"] if attempt.results else None,
            policy_version=rules.version,
            policy_digest=rules.digest,
        )

    def evaluations(
        self,
        content: PublishedContent,
        policy: LearningPolicy,
        data: dto.SubmitInput,
        expected: set[str],
        required: set[str] | None = None,
    ) -> list[dto.EvaluationView]:
        provided = {r.activity_id for r in data.responses}
        if (
            not data.acknowledged
            or not provided <= expected
            or not (expected if required is None else required) <= provided
            or any(not r.acknowledged for r in data.responses)
        ):
            raise LearningError(422, "invalid_learning_response")
        result = []
        for response in data.responses:
            try:
                evaluation = self.evaluator.evaluate(
                    content.documents[f"activities/{response.activity_id}.json"],
                    policy.activities[response.activity_id],
                    response.response,
                    response.self_assessment,
                )
            except ValueError:
                raise LearningError(422, "invalid_learning_response") from None
            result.append(
                dto.EvaluationView(
                    activity_id=response.activity_id,
                    response=response.response,
                    normalized=evaluation.normalized,
                    status=evaluation.status,
                    score=evaluation.score,
                    correct=evaluation.correct,
                    evaluator=evaluation.evaluator,
                    evaluator_version=evaluation.version,
                )
            )
        return result

    async def submit(
        self, principal: Principal, attempt_id: UUID, data: dto.SubmitInput
    ) -> dto.AttemptView:
        async with self.database.transaction() as db:
            await self.identity.locked_principal(db, principal)
            attempt = await db.scalar(
                select(Attempt)
                .join(Enrollment)
                .where(Attempt.id == attempt_id, Enrollment.account_id == principal.account_id)
                .with_for_update(of=Attempt)
            )
            if attempt is None:
                raise LearningError()
            enrollment = await self.owned(db, principal, attempt.enrollment_id)
            content, rules, policy = await self.context(db, enrollment)
            digest = request_digest(data)
            if attempt.submitted_at:
                if attempt.request_digest != digest:
                    raise LearningError(409, "operation_conflict")
                return self.attempt_view(attempt, rules)
            lesson = self.lesson_document(content, attempt.lesson_id)
            rule = policy.lessons[attempt.lesson_id]
            evaluated = self.evaluations(
                content, policy, data, set(lesson["activity_refs"]), set(rule.required_activities)
            )
            required = [e for e in evaluated if e.activity_id in rule.required_activities]
            scores = [e.score for e in required]
            score = (
                None
                if not scores or any(s is None for s in scores)
                else sum((s for s in scores if s is not None), Decimal(0)) / len(scores)
            )
            state = await db.get(
                LessonProgress, (enrollment.id, attempt.lesson_id), with_for_update=True
            )
            if state is None:
                raise LearningError(409, "invalid_attempt_state")
            state.score, state.updated_at = score, now()
            state.mastery_status = (
                "not_applicable"
                if rule.mastery_score is None
                else "unknown"
                if score is None
                else "assessed"
            )
            state.mastered = (
                None if rule.mastery_score is None or score is None else score >= rule.mastery_score
            )
            meets_evaluation = not rule.require_evaluation or all(
                e.score is not None for e in required
            )
            meets_completion = rule.completion_score is None or (
                score is not None and score >= rule.completion_score
            )
            meets_mastery = rule.mastery_score is None or state.mastered is True
            credit = False
            was_completed = state.completed_at is not None
            if (
                attempt.kind == "canonical"
                and self.available(content, await self.progress(db, enrollment), attempt.lesson_id)
                and meets_evaluation
                and meets_completion
                and meets_mastery
            ):
                if not was_completed:
                    state.completed_at, credit = now(), True
                    self.event(
                        db, enrollment, attempt.operation_id, "lesson_completed", attempt.lesson_id
                    )
            if state.completed_at and rule.review:
                if not was_completed:
                    state.review_step = 0
                    state.review_due_at = now() + timedelta(
                        seconds=rule.review.intervals_seconds[0]
                    )
                elif score is not None:
                    state.review_step = (
                        min(state.review_step + 1, len(rule.review.intervals_seconds) - 1)
                        if score >= rule.review.success_score
                        else 0
                        if rule.review.on_failure == "reset"
                        else state.review_step
                    )
                    state.review_due_at = now() + timedelta(
                        seconds=rule.review.intervals_seconds[state.review_step]
                    )
            attempt.submitted_at, attempt.request_digest = now(), digest
            attempt.results = {
                "evaluations": [e.model_dump(mode="json") for e in evaluated],
                "completion_credit": credit,
            }
            self.event(db, enrollment, attempt.operation_id, "attempt_evaluated", attempt.lesson_id)
            await db.flush()
            return self.attempt_view(attempt, rules)

    async def history(
        self, principal: Principal, enrollment_id: UUID, data: dto.HistoryInput
    ) -> dto.HistoryView:
        async with self.database.transaction() as db:
            enrollment = await self.owned(db, principal, enrollment_id)
            _, rules, _ = await self.context(db, enrollment)
            query = select(Attempt).where(Attempt.enrollment_id == enrollment.id)
            if data.before:
                cursor = await db.scalar(
                    select(Attempt).where(
                        Attempt.id == data.before, Attempt.enrollment_id == enrollment.id
                    )
                )
                if cursor is None:
                    raise LearningError()
                query = query.where(
                    tuple_(Attempt.started_at, Attempt.id) < tuple_(cursor.started_at, cursor.id)
                )
            records = (
                await db.scalars(
                    query.order_by(Attempt.started_at.desc(), Attempt.id.desc()).limit(
                        data.limit + 1
                    )
                )
            ).all()
            return dto.HistoryView(
                attempts=[self.attempt_view(a, rules) for a in records[: data.limit]],
                next_before=records[data.limit - 1].id if len(records) > data.limit else None,
            )

    async def review(self, principal: Principal, enrollment_id: UUID) -> list[dto.ReviewView]:
        async with self.database.transaction() as db:
            enrollment = await self.owned(db, principal, enrollment_id)
            await self.context(db, enrollment)
            rows = (
                await db.scalars(
                    select(LessonProgress)
                    .where(
                        LessonProgress.enrollment_id == enrollment.id,
                        LessonProgress.completed_at.is_not(None),
                        LessonProgress.review_due_at <= now(),
                    )
                    .order_by(LessonProgress.review_due_at, LessonProgress.lesson_id)
                )
            ).all()
            return [
                dto.ReviewView(lesson_id=p.lesson_id, due_at=p.review_due_at)
                for p in rows
                if p.review_due_at
            ]

    async def assessment(self, principal: Principal, enrollment_id: UUID) -> dict[str, Any]:
        async with self.database.transaction() as db:
            enrollment = await self.owned(db, principal, enrollment_id)
            content, rules, policy = await self.context(db, enrollment)
            if policy.placement is None:
                raise LearningError()
            return {
                "assessment_version": policy.placement.assessment_version,
                "policy_version": rules.version,
                "policy_digest": rules.digest,
                "activities": [
                    self.activity_view(content, policy, aid)
                    for aid in policy.placement.activity_ids
                ],
            }

    async def place(
        self, principal: Principal, enrollment_id: UUID, data: dto.PlacementInput
    ) -> dto.PlacementView:
        async with self.database.transaction() as db:
            enrollment = await self.owned(db, principal, enrollment_id)
            content, rules, policy = await self.context(db, enrollment)
            if policy.placement is None:
                raise LearningError()
            existing = await db.scalar(
                select(PlacementResult).where(
                    PlacementResult.enrollment_id == enrollment.id,
                    PlacementResult.operation_id == data.operation_id,
                )
            )
            digest = request_digest(data)
            if existing:
                if existing.request_digest != digest:
                    raise LearningError(409, "operation_conflict")
                return self.placement_view(existing, rules)
            evaluated = self.evaluations(content, policy, data, set(policy.placement.activity_ids))
            score = sum((e.score for e in evaluated if e.score is not None), Decimal(0)) / len(
                evaluated
            )
            result = PlacementResult(
                enrollment_id=enrollment.id,
                operation_id=data.operation_id,
                request_digest=digest,
                assessment_version=policy.placement.assessment_version,
                score=score,
                recommended_lesson_id=self.placement.recommend(policy.placement, score),
                results={"evaluations": [e.model_dump(mode="json") for e in evaluated]},
                created_at=now(),
            )
            db.add(result)
            await db.flush()
            await db.refresh(result, attribute_names=["score"])
            return self.placement_view(result, rules)

    def placement_view(self, result: PlacementResult, rules: RuleSet) -> dto.PlacementView:
        return dto.PlacementView(
            id=result.id,
            score=result.score,
            recommended_lesson_id=result.recommended_lesson_id,
            assessment_version=result.assessment_version,
            policy_version=rules.version,
            policy_digest=rules.digest,
            created_at=result.created_at,
        )

    async def accept_placement(
        self, principal: Principal, enrollment_id: UUID, placement_id: UUID
    ) -> dto.EnrollmentView:
        async with self.database.transaction() as db:
            enrollment = await self.owned(db, principal, enrollment_id)
            result = await db.scalar(
                select(PlacementResult).where(
                    PlacementResult.id == placement_id,
                    PlacementResult.enrollment_id == enrollment.id,
                )
            )
            if result is None:
                raise LearningError()
            if enrollment.recommended_lesson_id != result.recommended_lesson_id:
                enrollment.recommended_lesson_id = result.recommended_lesson_id
                previous = await db.scalar(
                    select(LearningEvent).where(
                        LearningEvent.enrollment_id == enrollment.id,
                        LearningEvent.operation_id == result.id,
                        LearningEvent.kind == "placement_accepted",
                    )
                )
                if previous is None:
                    self.event(
                        db,
                        enrollment,
                        result.id,
                        "placement_accepted",
                        result.recommended_lesson_id,
                    )
            return await self.enrollment_view(db, enrollment)

    async def translate(
        self, principal: Principal, enrollment_id: UUID, data: dto.TranslationInput
    ) -> dto.TranslationView:
        async with self.database.transaction() as db:
            enrollment = await self.owned(db, principal, enrollment_id)
            content, _, _ = await self.context(db, enrollment)
            lesson = self.lesson_document(content, data.lesson_id)
            if (
                not self.available(content, await self.progress(db, enrollment), data.lesson_id)
                and enrollment.recommended_lesson_id != data.lesson_id
            ):
                raise LearningError(409, "lesson_locked")
            block = next((b for b in lesson["blocks"] if b["block_id"] == data.block_id), None)
            if block is None or not isinstance(block.get("reference_text"), str):
                raise LearningError()
            event = await db.scalar(
                select(LearningEvent).where(
                    LearningEvent.enrollment_id == enrollment.id,
                    LearningEvent.operation_id == data.operation_id,
                    LearningEvent.kind == "translation_requested",
                )
            )
            if event:
                if event.lesson_id != data.lesson_id or event.block_id != data.block_id:
                    raise LearningError(409, "operation_conflict")
            else:
                self.event(
                    db,
                    enrollment,
                    data.operation_id,
                    "translation_requested",
                    data.lesson_id,
                    data.block_id,
                )
            return dto.TranslationView(reference_text=block["reference_text"])

    async def engage(self, principal: Principal, attempt_id: UUID, sequence: int) -> dict[str, int]:
        async with self.database.transaction() as db:
            await self.identity.locked_principal(db, principal)
            attempt = await db.scalar(
                select(Attempt)
                .join(Enrollment)
                .where(
                    Attempt.id == attempt_id,
                    Enrollment.account_id == principal.account_id,
                )
                .with_for_update(of=Attempt)
            )
            if attempt is None:
                raise LearningError()
            previous = attempt.engagement_sequence or 0
            if sequence <= previous:
                return {"active_seconds": attempt.active_seconds or 0, "sequence": previous}
            if sequence != previous + 1 or attempt.submitted_at:
                raise LearningError(409, "engagement_conflict")
            timestamp = now()
            elapsed = (
                (timestamp - attempt.last_engaged_at).total_seconds()
                if attempt.last_engaged_at
                else 0
            )
            # Only adjacent bounded heartbeats count. Gaps/idle time are not learning evidence.
            attempt.active_seconds = (attempt.active_seconds or 0) + (
                int(elapsed) if 0 <= elapsed <= 20 else 0
            )
            attempt.last_engaged_at, attempt.engagement_sequence = timestamp, sequence
            return {"active_seconds": attempt.active_seconds, "sequence": sequence}
