"""Create only synthetic browser-test data in a guarded isolated test database."""

import asyncio
import json
import os
import secrets
from pathlib import Path

import httpx2
from sqlalchemy import text
from test_course_packages import payload, zipped
from test_identity import verified
from test_learning import documents, eligible, synthetic_policy

from norskallstars_backend.app import create_app
from norskallstars_backend.config import Environment, load_settings
from norskallstars_backend.course_packages.service import import_package, publish_release
from norskallstars_backend.database import Database
from norskallstars_backend.learning.policy import Presentation, ResponseOption, validate_policy
from norskallstars_backend.learning.service import select_learning_release
from norskallstars_backend.storage import create_storage


def browser_policy(docs):
    """Explicit binding for the approved synthetic fixture, never runtime inference."""
    policy = synthetic_policy(docs)
    policy.policy_version = "synthetic-browser-policy-2"
    policy.activities["fixture.activity.match"].presentation = Presentation(
        kind="matching",
        fields=["yellow square", "blue circle"],
        options=[
            ResponseOption(label="water", value="synthetic-one"),
            ResponseOption(label="shade", value="synthetic-two"),
        ],
    )
    validate_policy(policy, docs)
    return policy


async def main(client_name="browser"):
    if client_name not in ("browser", "android"):
        raise RuntimeError("Unknown synthetic client")
    settings = load_settings()
    expected = (
        "norskallstars_web_test" if client_name == "browser" else "norskallstars_android_test"
    )
    if settings.env != Environment.TEST or settings.database_name != expected:
        raise RuntimeError("Client seed requires its dedicated synthetic test database")
    database = Database(settings)
    try:
        async with database.transaction() as db:
            await db.execute(
                text(
                    "TRUNCATE identity_accounts, identity_rate_buckets, "
                    "course_releases, storage_deletions CASCADE"
                )
            )
        storage = create_storage(settings)
        if storage is None:
            raise RuntimeError("Explicit synthetic local storage required")
        files = payload()
        docs = documents(files)
        policy = browser_policy(docs)
        first_chapter = docs["course.json"]["chapters"][0]
        first_lesson = docs[f"chapters/{first_chapter}.json"]["lesson_refs"][0]
        lesson = docs[f"lessons/{first_lesson}.json"]
        activity = docs[f"activities/{lesson['activity_refs'][0]}.json"]
        scenario = {
            "lesson_title": lesson["title"],
            "correct_choice": activity["accepted_answers"][0],
            "alternative_choice": next(
                choice
                for choice in activity["choices"]
                if choice not in activity["accepted_answers"]
            ),
        }
        rid = await import_package(
            database,
            storage,
            zipped(eligible(files)),
            actor="synthetic-browser",
            approval="synthetic-only",
        )
        await publish_release(
            database, rid, actor="synthetic-browser", approval="synthetic-only", storage=storage
        )
        await select_learning_release(
            database, rid, policy, actor="synthetic-browser", approval="synthetic-only"
        )
        app = create_app(settings, database)
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app),
            base_url="http://testserver",
            headers={"X-NorskAllstars-Client": "web"},
        ) as client:
            accounts = {}
            for browser in (
                ("chromium", "firefox", "webkit") if client_name == "browser" else ("android",)
            ):
                for flow in ("learning", "accessibility"):
                    email = f"synthetic-{browser}-{flow}@example.com"
                    password = secrets.token_urlsafe(24)
                    await verified(app.state.identity, client, password, email)
                    accounts[f"{browser}:{flow}"] = {"email": email, "password": password}
        folder = "web-e2e" if client_name == "browser" else "android-e2e"
        destination = Path(__file__).resolve().parents[3] / f".cache/{folder}/login.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(destination, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            json.dump({"accounts": accounts, "scenario": scenario}, stream)
        print("Synthetic client data ready; credentials remain in ignored local staging")
    finally:
        await database.close()


if __name__ == "__main__":
    asyncio.run(main())
