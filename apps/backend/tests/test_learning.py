"""Synthetic public-contract learning flows and adversarial ownership/transaction regressions."""

import asyncio
import hashlib
import json
import secrets
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import httpx2
import pytest
from pydantic import ValidationError
from sqlalchemy import func, select, text, update
from sqlalchemy.exc import IntegrityError
from test_course_packages import mutate, payload, zipped
from test_identity import bearer, proof, verified

from norskallstars_backend.app import create_app
from norskallstars_backend.course_packages.archive import BoundaryError
from norskallstars_backend.course_packages.models import CourseRelease
from norskallstars_backend.course_packages.service import import_package, publish_release
from norskallstars_backend.learning.cli import read_policy
from norskallstars_backend.learning.evaluation import LocalEvaluator
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
from norskallstars_backend.learning.policy import ActivityRule, LearningPolicy, validate_policy
from norskallstars_backend.learning.service import LearningError, select_learning_release
from norskallstars_backend.storage import LocalObjectStorage

PREFIX = "/api/v1/learning"


def documents(files):
    return {
        name: json.loads(raw)
        for name, raw in files.items()
        if name.endswith(".json") and name != "manifest.json"
    }


def synthetic_policy(docs):
    # These are explicit test-only policies, never default production thresholds/intervals.
    lessons = {d["lesson_id"]: d for name, d in docs.items() if name.startswith("lessons/")}
    activities = {d["activity_id"]: d for name, d in docs.items() if name.startswith("activities/")}
    activity_rules = {}
    for aid, activity in activities.items():
        activity_rules[aid] = {
            "comparison": "exact",
            "accepted_responses": None,
            "normalization": [
                {"flag": flag, "operation": flag} for flag in activity.get("normalization", {})
            ],
            "display_prompt": "Synthetic structured task"
            if isinstance(activity["prompt"], dict)
            else None,
            "display_choices": ["Synthetic left", "Synthetic right"]
            if any(isinstance(c, dict) for c in activity.get("choices", []))
            else None,
        }
        if activity["evaluation"]["type"] == "deterministic" and not activity.get(
            "accepted_answers"
        ):
            activity_rules[aid]["accepted_responses"] = [["synthetic-one", "synthetic-two"]]
    rules = {}
    for lid, lesson in lessons.items():
        scored = all(
            activities[aid]["evaluation"]["type"] == "deterministic"
            for aid in lesson["activity_refs"]
        )
        rules[lid] = {
            "required_activities": lesson["activity_refs"],
            "require_evaluation": scored,
            "completion_score": "1" if scored else None,
            "mastery_score": "1" if scored else None,
            "review": {
                "intervals_seconds": [60, 120, 240],
                "success_score": "1",
                "on_failure": "reset",
            }
            if scored
            else None,
        }
    assessment = [
        aid
        for aid, a in activities.items()
        if a.get("accepted_answers") and a["evaluation"]["type"] == "deterministic"
    ]
    order = [
        lid
        for cid in docs["course.json"]["chapters"]
        for lid in docs[f"chapters/{cid}.json"]["lesson_refs"]
    ]
    return LearningPolicy.model_validate(
        {
            "policy_version": "synthetic-policy-1",
            "lessons": rules,
            "activities": activity_rules,
            "concepts": {},
            "package_policy_inputs": {
                path + "#" + field: hashlib.sha256(
                    json.dumps(
                        component[field], sort_keys=True, separators=(",", ":"), ensure_ascii=False
                    ).encode()
                ).hexdigest()
                for path, component in docs.items()
                if path.startswith(("lessons/", "chapters/"))
                for field in ("completion", "review")
                if component[field] is not None
            },
            "placement": {
                "assessment_version": "synthetic-assessment-1",
                "activity_ids": assessment,
                "recommendations": [
                    {"minimum_score": "0", "lesson_id": order[0]},
                    {"minimum_score": "1", "lesson_id": order[-1]},
                ],
            },
        }
    )


def eligible(files):
    mutate(
        files,
        "course.json",
        lambda d: d["metadata"].update(
            fixture=False,
            synthetic_test_only=True,
            source_status="approved",
            human_g2="passed",
            illustrations="all_approved",
            release_approval="simulated-test",
        ),
    )
    mutate(files, "manifest.json", lambda d: d.update(release_eligible=True, build_kind="release"))
    return files


@pytest.fixture
async def runtime(database, integration_settings, tmp_path):
    async with database.transaction() as db:
        await db.execute(
            text("TRUNCATE identity_accounts, identity_rate_buckets, course_releases CASCADE")
        )
    # Unchanged approved fixture remains release-ineligible. Eligible derivatives exist only
    # in memory/the isolated test DB to exercise the genuine publication boundary.
    files = payload()
    mutate(
        files,
        "lessons/fixture.lesson.signal.json",
        lambda d: d["blocks"][0].update(
            reference_text="Synthetic explicit translation",
            internal_extra="private-internal-sentinel",
        ),
    )
    policy = synthetic_policy(documents(files))
    storage_root = tmp_path / "objects"
    storage_root.mkdir()
    storage = LocalObjectStorage(storage_root, 32 << 20)
    rid = await import_package(
        database,
        storage,
        zipped(eligible(files)),
        actor="synthetic-operator",
        approval="synthetic-only",
    )
    await publish_release(
        database, rid, actor="synthetic-operator", approval="synthetic-only", storage=storage
    )
    await select_learning_release(
        database, rid, policy, actor="synthetic-operator", approval="synthetic-only"
    )
    app = create_app(integration_settings, database)
    password = secrets.token_urlsafe(24)
    async with httpx2.AsyncClient(
        transport=httpx2.ASGITransport(app=app),
        base_url="http://testserver",
        headers={"X-NorskAllstars-Client": "android"},
    ) as client:
        session = await verified(app.state.identity, client, password)
        client.headers.update(bearer(session))
        enrollment = (
            await client.post(
                PREFIX + "/enrollments",
                json={"course_id": files and documents(files)["course.json"]["course_id"]},
            )
        ).json()
        yield app.state.learning, client, enrollment, policy, files, storage, session, password
    async with database.transaction() as db:
        await db.execute(
            text("TRUNCATE identity_accounts, identity_rate_buckets, course_releases CASCADE")
        )


async def start(client, enrollment, lid=None, kind="canonical", operation_id=None):
    result = await client.post(
        PREFIX + f"/enrollments/{enrollment['id']}/attempts",
        json={
            "operation_id": str(operation_id or uuid4()),
            "lesson_id": lid or enrollment["progress"][0]["lesson_id"],
            "kind": kind,
        },
    )
    assert result.status_code == 200, result.text
    return result.json()


def submission(policy, docs, lid, correct=True):
    result = []
    for aid in docs[f"lessons/{lid}.json"]["activity_refs"]:
        activity = docs[f"activities/{aid}.json"]
        rule = policy.activities[aid]
        accepted = rule.accepted_responses or activity.get("accepted_answers")
        result.append(
            {
                "activity_id": aid,
                "response": accepted[0]
                if correct and accepted
                else "synthetic incorrect"
                if accepted
                else "potentially personal synthetic response",
                "acknowledged": True,
                "self_assessment": True
                if activity["evaluation"]["type"] == "self_assessment"
                else None,
            }
        )
    return {"acknowledged": True, "responses": result}


async def finish(client, attempt, policy, files, correct=True):
    return await client.post(
        PREFIX + f"/attempts/{attempt['id']}/submit",
        json=submission(policy, documents(files), attempt["lesson_id"], correct),
    )


def test_explicit_policy_required_and_contract_fixture_unchanged():
    docs = documents(payload())
    policy = synthetic_policy(docs)
    validate_policy(policy, docs)
    assert json.loads(payload()["manifest.json"])["release_eligible"] is False
    for field in ("lessons", "activities", "concepts", "placement", "policy_version"):
        candidate = policy.document()
        del candidate[field]
        with pytest.raises(ValidationError):
            LearningPolicy.model_validate(candidate)
    assert policy.digest() == LearningPolicy.model_validate(policy.document()).digest()


@pytest.mark.parametrize(
    "case",
    [
        "missing_lesson",
        "unknown_activity",
        "unknown_normalizer",
        "normalizer_type",
        "completion_extension",
        "review_extension",
        "ambiguous_prompt",
        "ambiguous_choices",
        "missing_answers",
        "assessment_non_deterministic",
        "assessment_reference",
        "bands",
        "prerequisite",
        "duplicate_required",
    ],
)
def test_policy_fail_closed(case):
    docs = documents(payload())
    value = synthetic_policy(docs).document()
    first = "fixture.lesson.signal"
    if case == "missing_lesson":
        del value["lessons"][first]
    elif case == "unknown_activity":
        value["activities"]["unknown.activity"] = deepcopy(next(iter(value["activities"].values())))
    elif case == "unknown_normalizer":
        value["activities"]["fixture.activity.choose"]["normalization"] = []
    elif case == "normalizer_type":
        docs["activities/fixture.activity.choose.json"]["normalization"]["trim"] = "true"
    elif case == "completion_extension":
        docs[f"lessons/{first}.json"]["completion"] = {"threshold": "invented"}
    elif case == "review_extension":
        docs["chapters/fixture.chapter.garden.json"]["review"] = {"lesson_ref": first}
    elif case == "ambiguous_prompt":
        value["activities"]["fixture.activity.match"]["display_prompt"] = None
    elif case == "ambiguous_choices":
        value["activities"]["fixture.activity.match"]["display_choices"] = None
    elif case == "missing_answers":
        value["activities"]["fixture.activity.match"]["accepted_responses"] = None
    elif case == "assessment_non_deterministic":
        value["placement"]["activity_ids"] = ["fixture.activity.describe"]
    elif case == "assessment_reference":
        value["placement"]["activity_ids"] = ["unknown.activity"]
    elif case == "bands":
        value["placement"]["recommendations"][0]["minimum_score"] = "0.5"
    elif case == "prerequisite":
        docs[f"lessons/{first}.json"]["prerequisites"] = ["fixture.lesson.pattern"]
    elif case == "duplicate_required":
        value["lessons"][first]["required_activities"] *= 2
    with pytest.raises((ValueError, ValidationError)):
        validate_policy(LearningPolicy.model_validate(value), docs)


@pytest.mark.parametrize("value", ["-0.01", "1.01", "NaN", "Infinity", "0.1234567891"])
def test_invalid_thresholds(value):
    policy = synthetic_policy(documents(payload())).document()
    policy["lessons"]["fixture.lesson.signal"]["mastery_score"] = value
    with pytest.raises(ValidationError):
        LearningPolicy.model_validate(policy)


def test_normalization_is_explicit_and_type_strict():
    docs = documents(payload())
    policy = synthetic_policy(docs)
    activity = docs["activities/fixture.activity.choose.json"]
    rule = policy.activities[activity["activity_id"]]
    evaluator = LocalEvaluator()
    result = evaluator.evaluate(activity, rule, " WATER ", None)
    assert result.correct and result.normalized == "water"
    activity["normalization"] = {"trim": False, "case_fold": False}
    assert not evaluator.evaluate(activity, rule, " WATER ", None).correct
    activity["accepted_answers"] = [False]
    assert evaluator.evaluate(activity, rule, False, None).correct
    result = evaluator.evaluate(activity, rule, 0, None)
    assert result.correct is False and result.score == 0
    with pytest.raises(ValueError):
        evaluator.evaluate(activity, rule, "water", True)


@pytest.mark.parametrize(
    "mode,status,assessment,score",
    [
        ("rubric", "pending", None, None),
        ("external_future", "pending", None, None),
        ("none", "not_applicable", None, None),
        ("self_assessment", "self_assessed", False, Decimal(0)),
        ("self_assessment", "self_assessed", True, Decimal(1)),
    ],
)
def test_evaluation_modes_distinguish_unknown_not_applicable_and_false(
    mode, status, assessment, score
):
    rule = ActivityRule(
        comparison="exact",
        accepted_responses=None,
        normalization=[],
        display_prompt=None,
        display_choices=None,
    )
    result = LocalEvaluator().evaluate(
        {"evaluation": {"type": mode}}, rule, "synthetic", assessment
    )
    assert result.status == status and result.score == score
    assert result.correct is (assessment if mode == "self_assessment" else None)


def test_structured_exact_unordered_and_unicode_rules():
    rule = ActivityRule(
        comparison="unordered",
        accepted_responses=[["x", "y", "y"]],
        normalization=[],
        display_prompt=None,
        display_choices=None,
    )
    activity = {"evaluation": {"type": "deterministic"}}
    evaluator = LocalEvaluator()
    assert evaluator.evaluate(activity, rule, ["y", "x", "y"], None).correct
    assert not evaluator.evaluate(activity, rule, ["x", "y"], None).correct
    rule.comparison = "exact"
    assert not evaluator.evaluate(activity, rule, ["y", "x", "y"], None).correct
    rule.accepted_responses = ["å"]
    assert not evaluator.evaluate(activity, rule, "a\u030a", None).correct
    value = rule.model_dump()
    value["normalization"] = [{"flag": "explicit_nfc", "operation": "unicode_nfc"}]
    rule = ActivityRule.model_validate(value)
    activity["normalization"] = {"explicit_nfc": True}
    assert evaluator.evaluate(activity, rule, "a\u030a", None).correct


def test_operator_policy_parser_bounds_duplicates_and_secret_free_errors(tmp_path):
    path = tmp_path / "policy.json"
    for raw in [b'{"lessons":{},"lessons":{}}', b'{"x":NaN}', b"x" * ((2 << 20) + 1)]:
        path.write_bytes(raw)
        with pytest.raises(BoundaryError):
            read_policy(path)


@pytest.mark.integration
async def test_end_to_end_canonical_mastery_progress_repeat_review(runtime):
    service, client, enrollment, policy, files, *_ = runtime
    eid = enrollment["id"]
    first, second = enrollment["progress"]
    assert first["mastery"]["status"] == "unknown" and first["mastery"]["value"] is None
    assert first["available"] and not second["available"]
    result = await client.get(PREFIX + f"/enrollments/{eid}/lessons/{second['lesson_id']}")
    assert result.status_code == 409
    attempt = await start(client, enrollment)
    result = await finish(client, attempt, policy, files, False)
    assert result.status_code == 200 and not result.json()["completion_credit"]
    state = (await client.get(PREFIX + f"/enrollments/{eid}")).json()
    assert state["progress"][0]["mastery"]["status"] == "assessed"
    assert state["progress"][0]["mastery"]["value"] is False
    assert Decimal(state["progress"][0]["mastery"]["score"]) == 0
    assert not state["progress"][1]["available"]
    attempt = await start(client, enrollment)
    completed = await finish(client, attempt, policy, files)
    assert completed.status_code == 200 and completed.json()["completion_credit"]
    state = (await client.get(PREFIX + f"/enrollments/{eid}")).json()
    timestamp = state["progress"][0]["completed_at"]
    assert state["progress"][1]["available"] and state["progress"][0]["review_due_at"]
    async with service.database.transaction() as db:
        from norskallstars_backend.identity.service import now

        await db.execute(update(LessonProgress).values(review_due_at=now() - timedelta(seconds=1)))
    assert len((await client.get(PREFIX + f"/enrollments/{eid}/review")).json()) == 1
    for correct in (False, True, True):
        repeat = await start(client, enrollment, kind="practice")
        result = await finish(client, repeat, policy, files, correct)
        assert result.status_code == 200 and not result.json()["completion_credit"]
        state = (await client.get(PREFIX + f"/enrollments/{eid}")).json()
        assert (
            state["progress"][0]["completed_at"] == timestamp and state["progress"][1]["available"]
        )
    async with service.database.transaction() as db:
        assert (
            await db.scalar(
                select(func.count())
                .select_from(LearningEvent)
                .where(LearningEvent.kind == "lesson_completed")
            )
            == 1
        )
        progress = await db.get(LessonProgress, (UUID(eid), first["lesson_id"]))
        assert progress.review_step == 2
    second_attempt = await start(client, enrollment, lid=second["lesson_id"])
    second_result = await finish(client, second_attempt, policy, files)
    assert second_result.status_code == 200 and second_result.json()["completion_credit"]
    assert any(
        e["status"] == "pending" and e["score"] is None for e in second_result.json()["evaluations"]
    )


@pytest.mark.integration
async def test_content_projection_and_explicit_translation(runtime, caplog):
    _, client, enrollment, *_ = runtime
    eid = enrollment["id"]
    lid = enrollment["progress"][0]["lesson_id"]
    response = await client.get(PREFIX + f"/enrollments/{eid}/lessons/{lid}")
    assert response.status_code == 200
    for private in (
        "accepted_answers",
        "reference_text",
        "internal_extra",
        "private-internal-sentinel",
        "object_key",
        "checksum",
        "speaker_notes",
        "normalization",
        "metadata",
    ):
        assert private not in response.text
    op = {"operation_id": str(uuid4()), "lesson_id": lid, "block_id": "fixture.block.story"}
    first = await client.post(PREFIX + f"/enrollments/{eid}/translations", json=op)
    assert (
        first.status_code == 200
        and first.json()["reference_text"] == "Synthetic explicit translation"
    )
    assert (
        await client.post(PREFIX + f"/enrollments/{eid}/translations", json=op)
    ).json() == first.json()
    op["block_id"] = "fixture.block.picture"
    assert (
        await client.post(PREFIX + f"/enrollments/{eid}/translations", json=op)
    ).status_code == 404
    assert "Synthetic explicit translation" not in caplog.text


@pytest.mark.integration
async def test_placement_is_advisory_and_never_grants_completion(runtime):
    service, client, enrollment, policy, files, *_ = runtime
    eid = enrollment["id"]
    assessment = (await client.get(PREFIX + f"/enrollments/{eid}/placement")).json()
    assert "accepted_answers" not in json.dumps(assessment)
    first_id = enrollment["progress"][0]["lesson_id"]
    data = submission(policy, documents(files), first_id)
    data["operation_id"] = str(uuid4())
    response = await client.post(PREFIX + f"/enrollments/{eid}/placement", json=data)
    assert response.status_code == 200
    placement = response.json()
    target = enrollment["progress"][-1]["lesson_id"]
    assert placement["recommended_lesson_id"] == target and Decimal(placement["score"]) == 1
    assert (
        await client.post(PREFIX + f"/enrollments/{eid}/placement", json=data)
    ).json() == placement
    accepted = await client.post(
        PREFIX + f"/enrollments/{eid}/placement/{placement['id']}/accept", json={}
    )
    assert accepted.status_code == 200 and all(
        p["completed_at"] is None for p in accepted.json()["progress"]
    )
    assert (
        await client.post(
            PREFIX + f"/enrollments/{eid}/attempts",
            json={"operation_id": str(uuid4()), "lesson_id": target, "kind": "canonical"},
        )
    ).status_code == 409
    attempt = await start(client, enrollment, lid=target, kind="practice")
    assert not (await finish(client, attempt, policy, files)).json()["completion_credit"]
    state = (await client.get(PREFIX + f"/enrollments/{eid}")).json()
    assert all(p["completed_at"] is None for p in state["progress"])
    assert state["progress"][0]["available"]
    assert (await client.get(PREFIX + f"/enrollments/{eid}/lessons/{first_id}")).status_code == 200
    async with service.database.transaction() as db:
        assert (
            await db.scalar(
                select(func.count())
                .select_from(LearningEvent)
                .where(LearningEvent.kind == "lesson_completed")
            )
            == 0
        )


@pytest.mark.integration
async def test_idempotent_concurrent_enrollment_attempt_submission(runtime):
    service, client, enrollment, policy, files, *_ = runtime
    results = await asyncio.gather(
        *[
            client.post(
                PREFIX + "/enrollments", json={"course_id": enrollment["course"]["course_id"]}
            )
            for _ in range(2)
        ]
    )
    assert all(r.status_code == 200 and r.json()["id"] == enrollment["id"] for r in results)
    operation = uuid4()
    first, second = await asyncio.gather(
        *[start(client, enrollment, operation_id=operation) for _ in range(2)]
    )
    assert first["id"] == second["id"]
    results = await asyncio.gather(*[finish(client, first, policy, files) for _ in range(2)])
    assert all(r.status_code == 200 for r in results) and results[0].json() == results[1].json()
    conflict = await finish(client, first, policy, files, False)
    assert conflict.status_code == 409
    async with service.database.transaction() as db:
        assert await db.scalar(select(func.count()).select_from(Attempt)) == 1
        assert (
            await db.scalar(
                select(func.count())
                .select_from(LearningEvent)
                .where(LearningEvent.kind == "lesson_completed")
            )
            == 1
        )


@pytest.mark.integration
async def test_cross_account_reads_writes_cursors_and_placement_are_isolated(runtime):
    service, client, enrollment, policy, files, _, session, password = runtime
    attempt = await start(client, enrollment)
    data = submission(policy, documents(files), attempt["lesson_id"])
    data["operation_id"] = str(uuid4())
    placement = (
        await client.post(PREFIX + f"/enrollments/{enrollment['id']}/placement", json=data)
    ).json()
    other = await verified(service.identity, client, password, "other-synthetic@example.com")
    client.headers.update(bearer(other))
    eid = enrollment["id"]
    for suffix in ("", "/review", "/placement", "/lessons/" + attempt["lesson_id"]):
        assert (await client.get(PREFIX + f"/enrollments/{eid}" + suffix)).status_code == 404
    for suffix, body in [
        ("history", {}),
        (
            "attempts",
            {"operation_id": str(uuid4()), "lesson_id": attempt["lesson_id"], "kind": "canonical"},
        ),
        (
            "translations",
            {
                "operation_id": str(uuid4()),
                "lesson_id": attempt["lesson_id"],
                "block_id": "fixture.block.story",
            },
        ),
        ("placement", data),
        (f"placement/{placement['id']}/accept", {}),
    ]:
        assert (
            await client.post(PREFIX + f"/enrollments/{eid}/{suffix}", json=body)
        ).status_code == 404
    assert (await finish(client, attempt, policy, files)).status_code == 404
    own = (
        await client.post(
            PREFIX + "/enrollments", json={"course_id": enrollment["course"]["course_id"]}
        )
    ).json()
    assert (
        await client.post(
            PREFIX + f"/enrollments/{own['id']}/history", json={"before": attempt["id"]}
        )
    ).status_code == 404
    assert (
        await client.post(
            PREFIX + f"/enrollments/{own['id']}/placement/{placement['id']}/accept", json={}
        )
    ).status_code == 404
    client.headers.update(bearer(session))
    async with service.database.transaction() as db:
        assert (await db.get(Attempt, UUID(attempt["id"]))).submitted_at is None


@pytest.mark.integration
async def test_foreign_attempt_is_not_locked_before_ownership(runtime):
    service, client, enrollment, policy, files, _, _, password = runtime
    attempt = await start(client, enrollment)
    other = await verified(service.identity, client, password, "other-lock@example.com")
    client.headers.update(bearer(other))
    async with service.database.transaction() as db:
        await db.get(Attempt, UUID(attempt["id"]), with_for_update=True)
        response = await asyncio.wait_for(finish(client, attempt, policy, files), 2)
        assert response.status_code == 404


@pytest.mark.integration
async def test_revoked_sessions_and_account_deletion_erase_all_learning(runtime):
    service, client, enrollment, policy, files, _, session, password = runtime
    attempt = await start(client, enrollment)
    assert (await finish(client, attempt, policy, files)).status_code == 200
    assessment_data = submission(policy, documents(files), attempt["lesson_id"])
    assessment_data["operation_id"] = str(uuid4())
    assert (
        await client.post(
            PREFIX + f"/enrollments/{enrollment['id']}/placement", json=assessment_data
        )
    ).status_code == 200
    second_response = await client.post(
        "/api/v1/identity/sign-in",
        json={
            "email": "synthetic@example.com",
            "password": password,
            "device_label": "Second synthetic device",
        },
    )
    assert second_response.status_code == 200
    second = second_response.json()
    client.headers.update(bearer(second))
    assert (
        await client.delete("/api/v1/identity/sessions/" + session["session_id"])
    ).status_code == 200
    client.headers.update(bearer(session))
    assert (await client.get(PREFIX + f"/enrollments/{enrollment['id']}")).status_code == 401
    client.headers.update(bearer(second))
    fresh = await proof(client, second, password, "delete")
    assert (
        await client.request(
            "DELETE", "/api/v1/identity/me", json={"reauthentication_token": fresh}
        )
    ).status_code == 200
    async with service.database.transaction() as db:
        for model in (Enrollment, Attempt, LearningEvent, LessonProgress, PlacementResult):
            assert await db.scalar(select(func.count()).select_from(model)) == 0
        # Shared content/policy provenance is not user data and is preserved.
        assert await db.scalar(select(func.count()).select_from(RuleSet)) == 1
        assert await db.scalar(select(func.count()).select_from(CourseRelease)) == 1
    assert (await client.get(PREFIX + "/enrollments")).status_code == 401


@pytest.mark.integration
async def test_deletion_submission_race_has_no_recreated_learning_state(runtime):
    service, client, enrollment, policy, files, _, session, password = runtime
    attempt = await start(client, enrollment)
    fresh = await proof(client, session, password, "delete")
    submit, deleted = await asyncio.gather(
        finish(client, attempt, policy, files),
        client.request("DELETE", "/api/v1/identity/me", json={"reauthentication_token": fresh}),
    )
    assert deleted.status_code == 200 and submit.status_code in (200, 401)
    async with service.database.transaction() as db:
        for model in (Enrollment, Attempt, LessonProgress, LearningEvent):
            assert await db.scalar(select(func.count()).select_from(model)) == 0


@pytest.mark.integration
async def test_failed_submission_rolls_back_evidence_progress_and_events(runtime, monkeypatch):
    service, client, enrollment, policy, files, *_ = runtime
    attempt = await start(client, enrollment)
    original = service.event

    def fail_after_changes(db, enrollment, operation, kind, lid, block_id=None):
        original(db, enrollment, operation, kind, lid, block_id)
        if kind == "attempt_evaluated":
            raise RuntimeError("sensitive-answer-do-not-disclose")

    monkeypatch.setattr(service, "event", fail_after_changes)
    response = await finish(client, attempt, policy, files)
    assert response.status_code == 500 and "sensitive-answer" not in response.text
    async with service.database.transaction() as db:
        stored = await db.get(Attempt, UUID(attempt["id"]))
        assert (
            stored.submitted_at is None and stored.results is None and stored.request_digest is None
        )
        progress = await db.get(LessonProgress, (UUID(enrollment["id"]), attempt["lesson_id"]))
        assert (
            progress.completed_at is None
            and progress.score is None
            and progress.review_due_at is None
        )
        assert await db.scalar(select(func.count()).select_from(LearningEvent)) == 1
    monkeypatch.setattr(service, "event", original)
    assert (await finish(client, attempt, policy, files)).json()["completion_credit"]


@pytest.mark.integration
async def test_release_selection_is_explicit_and_existing_progress_stays_pinned(runtime):
    service, client, enrollment, policy, files, storage, session, password = runtime
    original_release = enrollment["course"]["release_id"]
    attempt = await start(client, enrollment)
    assert (await finish(client, attempt, policy, files)).json()["completion_credit"]
    newer = deepcopy(files)
    mutate(newer, "course.json", lambda d: d.update(version="2.0.0"))
    mutate(
        newer, "manifest.json", lambda d: d.update(course_version="2.0.0", content_version="2.0.0")
    )
    rid = await import_package(
        service.database, storage, zipped(newer), actor="test", approval="synthetic"
    )
    await publish_release(
        service.database, rid, actor="test", approval="synthetic", storage=storage
    )
    await select_learning_release(service.database, rid, policy, actor="test", approval="synthetic")
    catalog = (await client.get(PREFIX + "/courses")).json()
    assert catalog[0]["release_id"] == str(rid)
    existing = (
        await client.post(
            PREFIX + "/enrollments", json={"course_id": enrollment["course"]["course_id"]}
        )
    ).json()
    assert (
        existing["id"] == enrollment["id"] and existing["course"]["release_id"] == original_release
    )
    assert existing["progress"][0]["completed_at"]
    second_attempt = await start(client, enrollment, lid=enrollment["progress"][1]["lesson_id"])
    assert (await finish(client, second_attempt, policy, files)).status_code == 200
    other = await verified(service.identity, client, password, "new-version@example.com")
    client.headers.update(bearer(other))
    fresh = (
        await client.post(
            PREFIX + "/enrollments", json={"course_id": enrollment["course"]["course_id"]}
        )
    ).json()
    assert fresh["course"]["release_id"] == str(rid) and all(
        p["completed_at"] is None for p in fresh["progress"]
    )
    client.headers.update(bearer(session))


@pytest.mark.integration
async def test_policy_identity_conflict_staged_fixture_and_transactional_selection(runtime):
    service, _, enrollment, policy, _, storage, *_ = runtime
    rid = UUID(enrollment["course"]["release_id"])
    original = await select_learning_release(
        service.database, rid, policy, actor="test", approval="synthetic"
    )
    assert original == await select_learning_release(
        service.database, rid, policy, actor="test", approval="synthetic"
    )
    changed = policy.document()
    changed["lessons"]["fixture.lesson.signal"]["mastery_score"] = "0.5"
    with pytest.raises(
        LearningError, check=lambda error: error.code == "policy_version_conflict"
    ) as error:
        await select_learning_release(
            service.database,
            rid,
            LearningPolicy.model_validate(changed),
            actor="test",
            approval="synthetic",
        )
    assert error.value.code == "policy_version_conflict"
    staged = payload()
    mutate(staged, "course.json", lambda d: d.update(version="3.0.0"))
    mutate(
        staged, "manifest.json", lambda d: d.update(course_version="3.0.0", content_version="3.0.0")
    )
    staged_id = await import_package(
        service.database, storage, zipped(staged), actor="test", approval="synthetic"
    )
    with pytest.raises(LearningError):
        await select_learning_release(
            service.database, staged_id, policy, actor="test", approval="synthetic"
        )
    async with service.database.transaction() as db:
        assert await db.scalar(select(func.count()).select_from(RuleSet)) == 1
        assert await db.scalar(select(func.count()).select_from(PolicyAudit)) == 1
        assert (await db.get(CourseSelection, enrollment["course"]["course_id"])).release_id == rid


@pytest.mark.integration
async def test_database_enforces_policy_release_and_mastery_invariants(runtime):
    service, _, enrollment, *_ = runtime
    with pytest.raises(IntegrityError):
        async with service.database.transaction() as db:
            db.add(
                LessonProgress(
                    enrollment_id=UUID(enrollment["id"]),
                    lesson_id="bad.lesson",
                    mastery_status="not_applicable",
                    mastered=False,
                    score=Decimal(0),
                    review_step=0,
                    updated_at=datetime.now(UTC),
                )
            )
    with pytest.raises(IntegrityError):
        async with service.database.transaction() as db:
            await db.execute(update(Enrollment).values(course_id="wrong.course"))
    async with service.database.transaction() as db:
        assert (await db.get(Enrollment, UUID(enrollment["id"]))).course_id == enrollment["course"][
            "course_id"
        ]


@pytest.mark.integration
async def test_history_pagination_and_potentially_sensitive_answer_logging(runtime, caplog):
    _, client, enrollment, policy, files, *_ = runtime
    ids = []
    for _ in range(3):
        attempt = await start(client, enrollment)
        ids.append(attempt["id"])
        assert (await finish(client, attempt, policy, files)).status_code == 200
    path = PREFIX + f"/enrollments/{enrollment['id']}/history"
    first = (await client.post(path, json={"limit": 2})).json()
    second = (await client.post(path, json={"limit": 2, "before": first["next_before"]})).json()
    returned = [a["id"] for a in first["attempts"] + second["attempts"]]
    assert set(returned) == set(ids) and len(returned) == 3 and second["next_before"] is None
    assert "accepted_answers" not in json.dumps(first)
    assert "potentially personal synthetic response" not in caplog.text


@pytest.mark.integration
@pytest.mark.parametrize(
    "case",
    [
        "missing_auth",
        "cookie",
        "origin",
        "query",
        "duplicate",
        "nan",
        "overflow",
        "nul",
        "deep",
        "oversize",
        "account_id",
        "role",
        "client_score",
        "self_grade",
        "duplicate_activity",
    ],
)
async def test_http_learning_input_authorization_and_resource_guards(runtime, case):
    _, client, enrollment, policy, files, *_ = runtime
    attempt = await start(client, enrollment)
    path = PREFIX + f"/attempts/{attempt['id']}/submit"
    body = submission(policy, documents(files), attempt["lesson_id"])
    headers = {"Content-Type": "application/json"}
    if case == "missing_auth":
        client.headers.pop("Authorization")
    elif case == "cookie":
        headers["Cookie"] = "sid=untrusted"
    elif case == "origin":
        headers["Origin"] = "https://untrusted.invalid"
    elif case == "query":
        path += "?user_id=untrusted"
    elif case == "account_id":
        body["account_id"] = str(uuid4())
    elif case == "role":
        body["role"] = "admin"
    elif case == "client_score":
        body["responses"][0]["score"] = 1
    elif case == "self_grade":
        body["responses"][0]["self_assessment"] = True
    elif case == "duplicate_activity":
        body["responses"] *= 2
    raw = json.dumps(body)
    if case == "duplicate":
        raw = '{"acknowledged":true,"acknowledged":false,"responses":[]}'
    elif case == "nan":
        raw = '{"acknowledged":true,"responses":[],"extra":NaN}'
    elif case == "overflow":
        raw = '{"acknowledged":true,"responses":[],"extra":1e999}'
    elif case == "nul":
        body["responses"][0]["response"] = "invalid\x00response"
        raw = json.dumps(body)
    elif case == "deep":
        raw = '{"x":' * 12 + "0" + "}" * 12
    elif case == "oversize":
        raw = "x" * 32769
    response = await client.post(path, content=raw, headers=headers)
    assert response.status_code in (400, 401, 403, 413, 422), response.text
    assert "untrusted" not in response.text and "input" not in response.json()["error"]


@pytest.mark.integration
async def test_account_abuse_limit_persists_and_has_no_raw_identifiers(runtime):
    service, _, enrollment, *_ = runtime
    async with service.database.transaction() as db:
        row = await db.get(Enrollment, UUID(enrollment["id"]))
        from norskallstars_backend.identity.models import DeviceSession
        from norskallstars_backend.identity.service import Principal

        sid = await db.scalar(
            select(DeviceSession.id).where(DeviceSession.account_id == row.account_id)
        )
        principal = Principal(row.account_id, sid)
    for _ in range(120):
        await service.identity.rate_limit_account("synthetic-limit", principal)
    from norskallstars_backend.identity.service import IdentityError

    with pytest.raises(IdentityError) as error:
        await service.identity.rate_limit_account("synthetic-limit", principal)
    assert error.value.status == 429


def test_learning_openapi_has_explicit_identity_and_no_privileged_surface():
    from norskallstars_backend.identity.openapi import schema_bytes

    generated = schema_bytes("/api/v1/learning/")
    committed = Path(__file__).resolve().parents[3] / "contracts/api/learning-v1.openapi.json"
    assert committed.read_bytes() == generated
    schema = json.loads(generated)
    assert len(schema["paths"]) == 13
    for path, methods in schema["paths"].items():
        assert (
            "publish" not in path
            and "import" not in path
            and "admin" not in path
            and "media" not in path
        )
        for method, operation in methods.items():
            assert operation["security"] == [{"HTTPBearer": []}]
            if method == "post":
                assert any(
                    p["name"] == "X-NorskAllstars-Client" and p["required"]
                    for p in operation["parameters"]
                )
    assert "HTTPValidationError" not in schema["components"]["schemas"]
    assert "account_id" not in schema["components"]["schemas"]["SubmitInput"]["properties"]


@pytest.mark.integration
async def test_generic_new_course_three_lessons_and_optional_activity(runtime):
    service, client, _, _, _, storage, *_ = runtime
    files = eligible(payload())
    new_id = "synthetic.course.unrelated"
    mutate(files, "course.json", lambda d: d.update(course_id=new_id))
    mutate(files, "manifest.json", lambda d: d.update(course_id=new_id))
    lesson = json.loads(files["lessons/fixture.lesson.pattern.json"])
    lesson.update(
        lesson_id="synthetic.lesson.extra", order=3, prerequisites=["fixture.lesson.pattern"]
    )
    for index, block in enumerate(lesson["blocks"]):
        block["block_id"] = f"synthetic.block.extra.{index}"
    path = "lessons/synthetic.lesson.extra.json"
    files[path] = json.dumps(lesson).encode()
    mutate(
        files,
        "chapters/fixture.chapter.garden.json",
        lambda d: d["lesson_refs"].append(lesson["lesson_id"]),
    )
    mutate(
        files,
        "manifest.json",
        lambda d: (
            d["components"].append(path),
            d["checksums"].update({path: hashlib.sha256(files[path]).hexdigest()}),
        ),
    )
    policy = synthetic_policy(documents(files))
    policy.lessons["fixture.lesson.pattern"].required_activities = ["fixture.activity.match"]
    rid = await import_package(
        service.database, storage, zipped(files), actor="test", approval="synthetic"
    )
    await publish_release(
        service.database, rid, actor="test", approval="synthetic", storage=storage
    )
    await select_learning_release(service.database, rid, policy, actor="test", approval="synthetic")
    enrollment = (await client.post(PREFIX + "/enrollments", json={"course_id": new_id})).json()
    assert len(enrollment["progress"]) == 3
    first = await start(client, enrollment)
    assert (await finish(client, first, policy, files)).json()["completion_credit"]
    second = await start(client, enrollment, lid="fixture.lesson.pattern")
    data = submission(policy, documents(files), second["lesson_id"])
    data["responses"] = [
        r for r in data["responses"] if r["activity_id"] == "fixture.activity.match"
    ]
    response = await client.post(PREFIX + f"/attempts/{second['id']}/submit", json=data)
    assert response.status_code == 200 and response.json()["completion_credit"]
    state = (await client.get(PREFIX + f"/enrollments/{enrollment['id']}")).json()
    assert state["progress"][2]["available"]


@pytest.mark.integration
async def test_concept_mastery_comes_from_explicit_versioned_evidence(runtime):
    service, client, _, _, _, storage, *_ = runtime
    files = eligible(payload())
    mutate(
        files,
        "course.json",
        lambda d: d.update(
            course_id="synthetic.concepts",
            concepts=[
                {"concept_id": "synthetic.concept", "kind": "grammar", "label": "Synthetic concept"}
            ],
        ),
    )
    mutate(files, "manifest.json", lambda d: d.update(course_id="synthetic.concepts"))
    policy = synthetic_policy(documents(files))
    value = policy.document()
    value["concepts"] = {
        "synthetic.concept": {"required_lessons": ["fixture.lesson.signal"], "mastery_score": "1"}
    }
    policy = LearningPolicy.model_validate(value)
    rid = await import_package(
        service.database, storage, zipped(files), actor="test", approval="synthetic"
    )
    await publish_release(
        service.database, rid, actor="test", approval="synthetic", storage=storage
    )
    await select_learning_release(service.database, rid, policy, actor="test", approval="synthetic")
    enrollment = (
        await client.post(PREFIX + "/enrollments", json={"course_id": "synthetic.concepts"})
    ).json()
    assert enrollment["concepts"]["synthetic.concept"]["status"] == "unknown"
    attempt = await start(client, enrollment)
    assert (await finish(client, attempt, policy, files)).status_code == 200
    state = (await client.get(PREFIX + f"/enrollments/{enrollment['id']}")).json()
    assert state["concepts"]["synthetic.concept"]["value"] is True


def test_required_future_grading_and_unacknowledged_extensions_fail_closed():
    docs = documents(payload())
    value = synthetic_policy(docs).document()
    value["lessons"]["fixture.lesson.pattern"]["require_evaluation"] = True
    with pytest.raises(ValueError):
        validate_policy(LearningPolicy.model_validate(value), docs)
    value = synthetic_policy(docs).document()
    value["package_policy_inputs"] = {}
    with pytest.raises(ValueError):
        validate_policy(LearningPolicy.model_validate(value), docs)
