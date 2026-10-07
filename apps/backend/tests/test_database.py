from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from norskallstars_backend.app import create_app
from norskallstars_backend.database import SCHEMA_REVISION, Base, Database

pytestmark = pytest.mark.integration
CONFIG = str(Path(__file__).resolve().parents[1] / "alembic.ini")


async def test_real_postgresql_and_session_commit_rollback(database):
    assert await database.ready()
    assert set(Base.metadata.tables) == {
        "media_recordings",
        "storage_deletions",
        "course_releases",
        "release_assets",
        "release_events",
        "identity_accounts",
        "identity_google",
        "identity_sessions",
        "identity_refresh_credentials",
        "identity_one_time_credentials",
        "identity_mail_outbox",
        "identity_rate_buckets",
        "learning_rule_sets",
        "learning_course_selections",
        "learning_policy_audit",
        "learning_enrollments",
        "learning_attempts",
        "learning_lesson_progress",
        "learning_events",
        "learning_placements",
    }
    async with database.transaction() as session:
        # Temporary table exists only on this isolated test session/connection.
        await session.execute(text("CREATE TEMP TABLE phase1_probe (value INTEGER) ON COMMIT DROP"))
        await session.execute(text("INSERT INTO phase1_probe VALUES (1)"))
        assert (await session.execute(text("SELECT value FROM phase1_probe"))).scalar_one() == 1
    with pytest.raises(RuntimeError):
        async with database.transaction() as session:
            await session.execute(text("CREATE TABLE phase1_rollback_probe (value INTEGER)"))
            raise RuntimeError("rollback")
    async with database.transaction() as session:
        assert (
            await session.execute(text("SELECT to_regclass('phase1_rollback_probe')"))
        ).scalar_one() is None
    assert await database.ready()


def test_migration_upgrade_downgrade_and_drift(integration_settings):
    config = Config(CONFIG)
    command.upgrade(config, "head")
    command.upgrade(config, "head")
    command.check(config)
    command.downgrade(config, "base")
    with TestClient(create_app(integration_settings)) as client:
        assert client.get("/health/ready").status_code == 503
        assert client.get("/health/live").status_code == 200
    command.upgrade(config, "head")
    with TestClient(create_app(integration_settings)) as client:
        assert client.get("/health/ready").status_code == 200


async def test_unknown_migration_revision_is_not_ready(database):
    async with database.transaction() as session:
        await session.execute(text("UPDATE alembic_version SET version_num = 'unknown_revision'"))
    try:
        assert not await database.ready()
    finally:
        async with database.transaction() as session:
            await session.execute(
                text("UPDATE alembic_version SET version_num = :revision"),
                {"revision": SCHEMA_REVISION},
            )


async def test_database_outage_does_not_claim_readiness(integration_settings):
    changed = integration_settings.model_copy(update={"database_port": 1})
    db = Database(changed)
    try:
        with pytest.raises(OperationalError):
            await db.ready()
    finally:
        await db.close()
