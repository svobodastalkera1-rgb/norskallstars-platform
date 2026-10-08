"""Synthetic media and race/retention tests; no microphone or real user/corpus data."""

import asyncio
import base64
import hashlib
import os
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx2
import pytest
from pydantic import ValidationError
from sqlalchemy import func, select, text
from test_course_packages import mutate, payload, zipped
from test_identity import bearer, proof, verified
from test_learning import documents, eligible, start, synthetic_policy

from norskallstars_backend.app import create_app
from norskallstars_backend.course_packages.service import import_package, publish_release
from norskallstars_backend.identity.service import IdentityError
from norskallstars_backend.learning.service import select_learning_release
from norskallstars_backend.media.cleanup import reconcile
from norskallstars_backend.media.dto import UploadInput
from norskallstars_backend.media.models import Recording, StorageDeletion
from norskallstars_backend.media.service import audio_bytes, year_after
from norskallstars_backend.storage import InventoriedLocalStorage
from norskallstars_backend.storage_coordination import storage_lock


@pytest.fixture
async def media_runtime(database, integration_settings, tmp_path, monkeypatch):
    async with database.transaction() as db:
        await db.execute(
            text(
                "TRUNCATE identity_accounts, identity_rate_buckets, "
                "course_releases, storage_deletions CASCADE"
            )
        )
    files = payload()
    aid = "fixture.activity.describe"
    mutate(
        files,
        f"activities/{aid}.json",
        lambda d: d.update(
            type="speaking", response_mode="speech", evaluation={"type": "self_assessment"}
        ),
    )
    docs = documents(files)
    lid = next(
        d["lesson_id"]
        for path, d in docs.items()
        if path.startswith("lessons/") and aid in d["activity_refs"]
    )
    asset = docs["course.json"]["assets"][0]
    mutate(
        files,
        f"lessons/{lid}.json",
        lambda d: d["blocks"].append(
            {
                "block_id": "synthetic.media",
                "type": "image",
                "order": len(d["blocks"]) + 1,
                "asset_ref": asset["asset_id"],
                "alt_text": "Synthetic asset",
            }
        ),
    )
    policy = synthetic_policy(documents(files))
    root = tmp_path / "objects"
    root.mkdir()
    storage = InventoriedLocalStorage(root, 32 << 20)
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
    app = create_app(
        integration_settings.model_copy(
            update={"storage_backend": "local", "storage_root": root, "voice_sample_rate": 0.25}
        ),
        database,
    )
    monkeypatch.setattr("norskallstars_backend.media.service.secrets.randbelow", lambda bound: 0)
    password = secrets.token_urlsafe(24)
    async with httpx2.AsyncClient(
        transport=httpx2.ASGITransport(app=app),
        base_url="http://testserver",
        headers={"X-NorskAllstars-Client": "web"},
    ) as client:
        session = await verified(app.state.identity, client, password)
        client.headers.update(bearer(session))
        enrollment = (
            await client.post(
                "/api/v1/learning/enrollments", json={"course_id": docs["course.json"]["course_id"]}
            )
        ).json()
        # Speaking lesson can be practiced under an explicit advisory recommendation in tests.
        from norskallstars_backend.learning.models import Enrollment

        async with database.transaction() as db:
            record = await db.get(Enrollment, enrollment["id"])
            record.recommended_lesson_id = lid
        attempt = await start(client, enrollment, lid, "practice")
        yield app, client, enrollment, attempt, aid, asset, storage, session, password
    async with database.transaction() as db:
        await db.execute(
            text(
                "TRUNCATE identity_accounts, identity_rate_buckets, "
                "course_releases, storage_deletions CASCADE"
            )
        )


def upload_data():
    return {
        "audio_base64": base64.b64encode(b"OggS" + b"synthetic-audio" * 4).decode(),
        "mime_type": "audio/ogg",
    }


async def offered(runtime):
    _, client, _, attempt, aid, *_ = runtime
    response = await client.post(
        "/api/v1/media/recording-offers",
        json={
            "attempt_id": attempt["id"],
            "activity_id": aid,
            "consent": True,
            "policy_version": "voice-1",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_calendar_retention_and_audio_limits():
    assert year_after(datetime(2024, 2, 29, tzinfo=UTC)) == datetime(2025, 2, 28, tzinfo=UTC)
    assert audio_bytes(UploadInput(**upload_data())).startswith(b"OggS")
    for data in (
        {"audio_base64": "bad", "mime_type": "audio/ogg"},
        {"audio_base64": base64.b64encode(b"<script>" * 10).decode(), "mime_type": "audio/ogg"},
    ):
        with pytest.raises(IdentityError):
            audio_bytes(UploadInput(**data))
    with pytest.raises(ValidationError):
        UploadInput(audio_base64="x", mime_type="text/html")


@pytest.mark.integration
async def test_sampling_consent_idempotence_and_private_owner(media_runtime):
    app, client, _, attempt, aid, *_ = media_runtime
    bad = await client.post(
        "/api/v1/media/recording-offers",
        json={
            "attempt_id": attempt["id"],
            "activity_id": aid,
            "consent": False,
            "policy_version": "voice-1",
        },
    )
    assert bad.status_code == 422
    record = await offered(media_runtime)
    assert record == await offered(media_runtime)
    assert record["selected"]
    path = "/api/v1/media/recordings/" + record["id"]
    assert (await client.post(path, json=upload_data())).status_code == 200
    assert (await client.post(path, json=upload_data())).status_code == 200
    changed = upload_data()
    changed["audio_base64"] = base64.b64encode(b"OggS" + b"other" * 12).decode()
    assert (await client.post(path, json=changed)).status_code == 409
    client.headers.pop("Authorization")
    assert (await client.post(path, json=upload_data())).status_code == 401
    other = await verified(
        app.state.identity, client, secrets.token_urlsafe(24), "other@example.com"
    )
    client.headers.update(bearer(other))
    assert (await client.post(path, json=upload_data())).status_code == 404
    assert (await client.delete(path)).status_code == 404


@pytest.mark.integration
async def test_account_erasure_and_orphan_gc(media_runtime):
    app, client, _, _, _, _, storage, session, password = media_runtime
    record = await offered(media_runtime)
    assert (
        await client.post("/api/v1/media/recordings/" + record["id"], json=upload_data())
    ).status_code == 200
    fresh = await proof(client, session, password, "delete")
    assert (
        await client.request(
            "DELETE", "/api/v1/identity/me", json={"reauthentication_token": fresh}
        )
    ).status_code == 200
    async with app.state.database.transaction() as db:
        assert await db.scalar(select(func.count()).select_from(Recording)) == 0
    for obj in await storage.inventory():
        os.utime(storage.root / obj.key, (datetime.now(UTC).timestamp() - 7200,) * 2)
    assert await reconcile(app.state.database, storage, 3600) == 1
    assert await reconcile(app.state.database, storage, 3600) == 0
    assert all(not obj.key.startswith("recordings/") for obj in await storage.inventory())
    async with app.state.database.transaction() as db:
        assert await db.scalar(select(func.count()).select_from(StorageDeletion)) == 1


@pytest.mark.integration
async def test_gc_grace_active_writer_and_retry(media_runtime, monkeypatch):
    app, _, _, _, _, _, storage, *_ = media_runtime
    key = "recordings/" + uuid4().hex + "/orphan"
    await storage.put(key, b"synthetic")
    assert await reconcile(app.state.database, storage, 3600) == 0
    os.utime(storage.root / key, (datetime.now(UTC).timestamp() - 7200,) * 2)
    async with app.state.database.transaction() as db:
        await storage_lock(db)
        job = asyncio.create_task(reconcile(app.state.database, storage, 3600))
        await asyncio.sleep(0.1)
        assert not job.done()
    assert await job == 1
    await storage.put(key, b"synthetic")
    os.utime(storage.root / key, (datetime.now(UTC).timestamp() - 7200,) * 2)
    original = storage.delete

    async def failure(key):
        raise OSError("synthetic failure")

    monkeypatch.setattr(storage, "delete", failure)
    assert await reconcile(app.state.database, storage, 3600) == 0
    monkeypatch.setattr(storage, "delete", original)
    assert await reconcile(app.state.database, storage, 3600) == 1


@pytest.mark.integration
async def test_offer_expiry_and_foreign_attempt(media_runtime):
    app, client, _, _, _, _, _, _, _ = media_runtime
    record = await offered(media_runtime)
    async with app.state.database.transaction() as db:
        row = await db.get(Recording, record["id"])
        row.offer_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    assert (
        await client.post("/api/v1/media/recordings/" + record["id"], json=upload_data())
    ).status_code == 409
    assert (
        await client.post(
            "/api/v1/media/recording-offers",
            json={
                "attempt_id": str(uuid4()),
                "activity_id": "synthetic.missing",
                "consent": True,
                "policy_version": "voice-1",
            },
        )
    ).status_code == 404


@pytest.mark.integration
async def test_asset_release_scope_integrity_and_cross_account(media_runtime):
    app, client, enrollment, attempt, _, asset, storage, *_ = media_runtime
    path = (
        f"/api/v1/media/enrollments/{enrollment['id']}/lessons/"
        f"{attempt['lesson_id']}/assets/{asset['asset_id']}"
    )
    response = await client.get(path)
    assert response.status_code == 200
    assert hashlib.sha256(response.content).hexdigest() == asset["checksum"]
    assert response.headers["cache-control"] == "no-store"
    assert (await client.get(path.rsplit("/", 1)[0] + "/synthetic.missing")).status_code == 404
    other = await verified(
        app.state.identity, client, secrets.token_urlsafe(24), "asset-other@example.com"
    )
    client.headers.update(bearer(other))
    assert (await client.get(path)).status_code == 404
    client.headers.pop("Authorization")
    assert (await client.get(path)).status_code == 401


@pytest.mark.integration
async def test_zero_sampling_and_storage_failure_rollback(media_runtime, monkeypatch):
    app, client, _, _, _, _, storage, *_ = media_runtime
    original = app.state.identity.settings.voice_sample_rate
    app.state.identity.settings.voice_sample_rate = 0
    record = await offered(media_runtime)
    assert not record["selected"]
    assert (
        await client.post("/api/v1/media/recordings/" + record["id"], json=upload_data())
    ).status_code == 409
    app.state.identity.settings.voice_sample_rate = original
    # Explicit test override removes the unselected offer; normal retries cannot reroll sampling.
    async with app.state.database.transaction() as db:
        row = await db.get(Recording, record["id"])
        await db.delete(row)
    record = await offered(media_runtime)
    original_put = app.state.media.storage.put

    async def failed_put(key, data):
        await original_put(key, data)
        raise OSError("synthetic storage failure")

    monkeypatch.setattr(app.state.media.storage, "put", failed_put)
    response = await client.post("/api/v1/media/recordings/" + record["id"], json=upload_data())
    assert response.status_code == 500
    assert "synthetic storage failure" not in response.text
    async with app.state.database.transaction() as db:
        row = await db.get(Recording, record["id"])
        assert row.object_key is None


@pytest.mark.integration
async def test_recording_expiry_withdrawal_and_account_delete_race(media_runtime):
    app, client, _, _, _, _, storage, session, password = media_runtime
    record = await offered(media_runtime)
    assert (
        await client.post("/api/v1/media/recordings/" + record["id"], json=upload_data())
    ).status_code == 200
    async with app.state.database.transaction() as db:
        row = await db.get(Recording, record["id"])
        row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await reconcile(app.state.database, storage, 3600)
    assert (await client.delete("/api/v1/media/recordings/" + record["id"])).status_code == 404
    record = await offered(media_runtime)
    fresh = await proof(client, session, password, "delete")
    uploaded, erased = await asyncio.gather(
        client.post("/api/v1/media/recordings/" + record["id"], json=upload_data()),
        client.request("DELETE", "/api/v1/identity/me", json={"reauthentication_token": fresh}),
    )
    assert erased.status_code == 200
    assert uploaded.status_code in (200, 401)
    async with app.state.database.transaction() as db:
        assert await db.scalar(select(func.count()).select_from(Recording)) == 0


def test_static_web_security_and_api_fallback(settings, tmp_path):
    from fastapi.testclient import TestClient

    (tmp_path / "index.html").write_text('<html lang="nb">Synthetic client</html>')
    app = create_app(settings.model_copy(update={"web_root": tmp_path}))
    with TestClient(app) as client:
        response = client.get("/account/reset")
        assert response.status_code == 200
        assert "frame-ancestors" in response.headers["content-security-policy"]
        assert "microphone=(self)" in response.headers["permissions-policy"]
        assert client.get("/api/v1/missing").status_code == 404
        assert client.get("/.env").status_code == 404


@pytest.mark.integration
async def test_engagement_idempotence_bounds_and_dashboard_ownership(media_runtime):
    app, client, _, attempt, _, _, _, session, _ = media_runtime
    path = "/api/v1/learning/attempts/" + attempt["id"] + "/engagement"
    first = await client.post(path, json={"sequence": 1})
    assert first.status_code == 200
    assert first.json()["active_seconds"] == 0
    assert (await client.post(path, json={"sequence": 1})).json() == first.json()
    assert (await client.post(path, json={"sequence": 3})).status_code == 409
    from norskallstars_backend.learning.models import Attempt

    async with app.state.database.transaction() as db:
        row = await db.get(Attempt, attempt["id"])
        row.last_engaged_at = datetime.now(UTC) - timedelta(seconds=10)
    second = await client.post(path, json={"sequence": 2})
    assert 10 <= second.json()["active_seconds"] <= 11
    assert (await client.post(path, json={"sequence": 2})).json() == second.json()
    assert (await client.get("/api/v1/learning/dashboard")).json()["submitted_attempts"] == 0
    other = await verified(
        app.state.identity, client, secrets.token_urlsafe(24), "timer-other@example.com"
    )
    client.headers.update(bearer(other))
    assert (await client.post(path, json={"sequence": 3})).status_code == 404
    assert (await client.get("/api/v1/learning/dashboard")).json()["correct_answers"] == 0
    client.headers.update(bearer(session))


def test_presentation_binding_preserves_legacy_policy_identity():
    from norskallstars_backend.learning.policy import LearningPolicy

    policy = synthetic_policy(documents(payload()))
    serialized = policy.document()
    assert all("presentation" not in rule for rule in serialized["activities"].values())
    assert LearningPolicy.model_validate(serialized).digest() == policy.digest()


@pytest.mark.integration
async def test_dashboard_counts_only_submitted_active_time_and_excludes_gaps(
    media_runtime, monkeypatch
):
    app, client, enrollment, attempt, *_ = media_runtime
    timestamp = datetime.now(UTC)
    monkeypatch.setattr("norskallstars_backend.learning.service.now", lambda: timestamp)
    path = "/api/v1/learning/attempts/" + attempt["id"] + "/engagement"
    assert (await client.post(path, json={"sequence": 1})).json()["active_seconds"] == 0
    # Real server-time intervals, not client duration assertions; fractions round down.
    for sequence in range(2, 8):
        timestamp += timedelta(seconds=10.25)
        assert (await client.post(path, json={"sequence": sequence})).json()["active_seconds"] == (
            sequence - 1
        ) * 10
    before = (await client.get("/api/v1/learning/dashboard")).json()
    assert before["active_learning_seconds"] == before["timed_attempts"] == 0
    timestamp += timedelta(seconds=60)
    after_gap = await client.post(path, json={"sequence": 8})
    assert after_gap.json()["active_seconds"] == 60
    assert (await client.post(path, json={"sequence": 8})).json() == after_gap.json()
    lesson = (
        await client.get(
            f"/api/v1/learning/enrollments/{enrollment['id']}/lessons/{attempt['lesson_id']}"
        )
    ).json()
    result = await client.post(
        f"/api/v1/learning/attempts/{attempt['id']}/submit",
        json={
            "acknowledged": True,
            "responses": [
                {
                    "activity_id": activity["activity_id"],
                    "response": ["synthetic-one", "synthetic-two"]
                    if activity["response_mode"] == "matching"
                    else {"recorded": False},
                    "acknowledged": True,
                    "self_assessment": True
                    if activity["evaluation_type"] == "self_assessment"
                    else None,
                }
                for activity in lesson["activities"]
            ],
        },
    )
    assert result.status_code == 200, result.text
    summary = (await client.get("/api/v1/learning/dashboard")).json()
    assert summary["active_learning_seconds"] == 60
    assert summary["timed_attempts"] == summary["submitted_attempts"] == 1
    timestamp += timedelta(seconds=10)
    assert (await client.post(path, json={"sequence": 9})).status_code == 409
    assert (await client.get("/api/v1/learning/dashboard")).json() == summary


def test_browser_smoke_policy_explicitly_binds_matching_without_changing_contract():
    from browser_seed import browser_policy

    from norskallstars_backend.learning.evaluation import LocalEvaluator

    files = payload()
    docs = documents(files)
    policy = browser_policy(docs)
    aid = "fixture.activity.match"
    rule = policy.activities[aid]
    assert rule.presentation.kind == "matching"
    assert rule.presentation.fields == ["yellow square", "blue circle"]
    response = [option.value for option in rule.presentation.options]
    result = LocalEvaluator().evaluate(docs[f"activities/{aid}.json"], rule, response, None)
    assert result.correct is True
    assert files == payload()


def test_s3_boundary_explicit_config_and_bounded_calls(settings):
    from botocore.stub import Stubber

    from norskallstars_backend.storage import S3ObjectStorage

    configured = settings.model_copy(
        update={
            "storage_backend": "s3",
            "s3_endpoint": "https://storage.example.invalid",
            "s3_bucket": "synthetic-private",
            "s3_region": "test-region",
            "s3_access_key": settings.database_password,
            "s3_secret_key": settings.database_password,
        }
    )
    storage = S3ObjectStorage(configured)
    with Stubber(storage.client) as stub:
        stub.add_response("get_bucket_versioning", {}, {"Bucket": "synthetic-private"})
        stub.add_response(
            "put_object",
            {},
            {
                "Bucket": "synthetic-private",
                "Key": "recordings/synthetic/data",
                "Body": b"synthetic",
                "ServerSideEncryption": "AES256",
            },
        )
        asyncio.run(storage.put("recordings/synthetic/data", b"synthetic"))
    with pytest.raises(ValueError):
        asyncio.run(storage.put("../invalid", b"synthetic"))
    assert storage.client.meta.endpoint_url.startswith("https://")


def test_presentation_rejects_invalid_or_contradictory_bindings():
    from norskallstars_backend.learning.policy import Presentation, validate_policy

    for invalid in (
        {"kind": "matching", "options": [], "fields": ["Synthetic field"]},
        {"kind": "single_choice", "options": [{"label": "Synthetic", "value": None}]},
        {"kind": "speech", "options": [{"label": "Synthetic", "value": "unexpected"}]},
        {
            "kind": "single_choice",
            "options": [
                {"label": "Synthetic A", "value": "duplicate"},
                {"label": "Synthetic B", "value": "duplicate"},
            ],
        },
    ):
        with pytest.raises(ValueError):
            Presentation.model_validate(invalid)
    docs = documents(payload())
    policy = synthetic_policy(docs)
    choice = next(
        aid
        for aid, rule in docs.items()
        if aid.startswith("activities/") and rule["response_mode"] == "choice"
    )
    aid = docs[choice]["activity_id"]
    policy.activities[aid].presentation = Presentation(kind="speech", options=[])
    with pytest.raises(ValueError, match="contradicts"):
        validate_policy(policy, docs)


def test_engagement_migration_offline_downgrade_uses_exact_constraint_name():
    import importlib.util
    import io
    from pathlib import Path

    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    path = Path(__file__).resolve().parents[1] / "migrations/versions/0006_learning_engagement.py"
    spec = importlib.util.spec_from_file_location("synthetic_migration", path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    output = io.StringIO()
    from norskallstars_backend.database import Base

    context = MigrationContext.configure(
        dialect_name="postgresql",
        opts={"as_sql": True, "output_buffer": output, "target_metadata": Base.metadata},
    )
    with Operations.context(context):
        migration.downgrade()
    sql = output.getvalue()
    assert "DROP CONSTRAINT ck_learning_attempts_engagement_seconds;" in sql
    assert "ck_learning_attempts_ck_" not in sql


@pytest.mark.integration
async def test_owned_recording_inventory_survives_browser_reload(media_runtime):
    app, client, *_ = media_runtime
    record = await offered(media_runtime)
    listing = await client.get("/api/v1/media/recordings")
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()] == [record["id"]]
    assert all(
        not ({"object_key", "checksum", "account_id"} & set(item)) for item in listing.json()
    )
    other = await verified(
        app.state.identity, client, secrets.token_urlsafe(24), "record-list-other@example.com"
    )
    client.headers.update(bearer(other))
    assert (await client.get("/api/v1/media/recordings")).json() == []
    assert (await client.delete("/api/v1/media/recordings/" + record["id"])).status_code == 404


def test_s3_versioning_cannot_silently_defeat_erasure(settings):
    from botocore.stub import Stubber

    from norskallstars_backend.storage import S3ObjectStorage

    configured = settings.model_copy(
        update={
            "s3_endpoint": "https://storage.example.invalid",
            "s3_bucket": "synthetic-private",
            "s3_region": "test-region",
            "s3_access_key": settings.database_password,
            "s3_secret_key": settings.database_password,
        }
    )
    storage = S3ObjectStorage(configured)
    for state in ("Enabled", "Suspended"):
        with Stubber(storage.client) as stub:
            stub.add_response(
                "get_bucket_versioning", {"Status": state}, {"Bucket": "synthetic-private"}
            )
            with pytest.raises(ValueError, match="unversioned"):
                storage._ensure_unversioned()


def test_media_configuration_rejects_insecure_or_missing_values(settings):
    from norskallstars_backend.config import Settings

    good = settings.model_dump()
    good.update(
        storage_backend="s3",
        s3_endpoint="https://storage.example.invalid",
        s3_bucket="synthetic-private",
        s3_region="test-region",
        s3_access_key=settings.database_password,
        s3_secret_key=settings.database_password,
    )
    for changed in (
        {"s3_endpoint": "http://storage.example.invalid"},
        {"s3_endpoint": "https://user:password@storage.example.invalid"},
        {"s3_access_key": ""},
        {"s3_secret_key": ""},
        {"s3_region": None},
        {"voice_sample_rate": 1},
        {"storage_gc_grace_seconds": 0},
    ):
        with pytest.raises(ValidationError):
            Settings.model_validate({**good, **changed})
