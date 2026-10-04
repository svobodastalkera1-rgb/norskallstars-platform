"""Privileged operator boundary; no public import/publication HTTP routes."""

import asyncio
import hashlib
import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from norskallstars_backend.course_packages.archive import BoundaryError
from norskallstars_backend.course_packages.models import CourseRelease, ReleaseAsset, ReleaseEvent
from norskallstars_backend.course_packages.validation import contract_root, validate_archive
from norskallstars_backend.database import Database
from norskallstars_backend.storage import ObjectStorage


def actor_valid(actor: str, approval: str) -> None:
    if not actor or len(actor) > 128 or not approval or len(approval) > 240:
        raise BoundaryError("audit_identity")
    if any(ord(c) < 32 for c in actor + approval):
        raise BoundaryError("audit_identity")


async def import_package(
    database: Database, storage: ObjectStorage, archive: bytes, *, actor: str, approval: str
) -> uuid.UUID:
    actor_valid(actor, approval)
    package = await asyncio.to_thread(validate_archive, archive)
    manifest = package.manifest
    course_id, version = manifest["course_id"], manifest["course_version"]
    # Serialize same identity before DB/object changes. No overwrite on conflict.
    lock = int.from_bytes(
        hashlib.sha256((course_id + "\0" + version).encode()).digest()[:8], signed=True
    )
    async with database.transaction() as session:
        await session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock})
        existing = await session.scalar(
            select(CourseRelease).where(
                CourseRelease.course_id == course_id, CourseRelease.course_version == version
            )
        )
        if existing:
            if existing.package_digest != package.digest:
                raise BoundaryError("version_conflict")
            return existing.id
        schema_hash = hashlib.sha256()
        for p in sorted((contract_root() / "specification/platform-contract/v1").glob("*.json")):
            schema_hash.update(p.name.encode() + b"\0" + p.read_bytes())
        release = CourseRelease(
            course_id=course_id,
            course_version=version,
            schema_version=manifest["schema_version"],
            content_version=manifest["content_version"],
            package_digest=package.digest,
            archive_digest=hashlib.sha256(archive).hexdigest(),
            contract_digest=schema_hash.hexdigest(),
            release_eligible=manifest["release_eligible"],
            manifest=manifest,
            documents=package.documents,
        )
        session.add(release)
        await session.flush()
        for asset in package.documents["course.json"].get("assets", []):
            # Isolated per-release namespace: a failed attempt cannot affect accepted assets.
            key = "releases/" + release.id.hex + "/" + asset["checksum"]
            await storage.put(key, package.files[asset["path"]])
            if hashlib.sha256(await storage.get(key)).hexdigest() != asset["checksum"]:
                raise BoundaryError("storage_integrity")
            session.add(
                ReleaseAsset(
                    release_id=release.id,
                    asset_id=asset["asset_id"],
                    object_key=key,
                    checksum=asset["checksum"],
                    metadata_json=asset,
                )
            )
        session.add(
            ReleaseEvent(release_id=release.id, action="import", actor=actor, approval=approval)
        )
        # DB rollback is automatic on validation/storage/flush/commit/cancellation failures.
        # Unreferenced private objects may remain; no publication references are committed.
        return release.id


async def publish_release(
    database: Database, release_id: uuid.UUID, *, actor: str, approval: str, storage: ObjectStorage
) -> None:
    actor_valid(actor, approval)
    async with database.transaction() as session:
        await _publish(session, release_id, actor, approval, storage)


async def _publish(
    session: AsyncSession, release_id: uuid.UUID, actor: str, approval: str, storage: ObjectStorage
) -> None:
    release = await session.scalar(
        select(CourseRelease).where(CourseRelease.id == release_id).with_for_update()
    )
    if not release or not release.release_eligible:
        raise BoundaryError("release_ineligible")
    if release.documents["course.json"].get("metadata", {}).get("fixture"):
        raise BoundaryError("release_ineligible")
    if release.state == "published":
        return
    assets = (
        await session.scalars(select(ReleaseAsset).where(ReleaseAsset.release_id == release_id))
    ).all()
    for asset in assets:
        if hashlib.sha256(await storage.get(asset.object_key)).hexdigest() != asset.checksum:
            raise BoundaryError("storage_integrity")
    release.state = "published"
    session.add(
        ReleaseEvent(release_id=release_id, action="publish", actor=actor, approval=approval)
    )
