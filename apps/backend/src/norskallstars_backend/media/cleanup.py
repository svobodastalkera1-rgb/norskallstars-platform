"""Private bounded cleanup: expiry and inventory reconciliation, never public HTTP."""

import argparse
import asyncio
import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, or_, select

from norskallstars_backend.config import load_settings
from norskallstars_backend.course_packages.models import ReleaseAsset
from norskallstars_backend.database import Database
from norskallstars_backend.media.models import Recording, StorageDeletion
from norskallstars_backend.storage import InventoryStorage, create_storage
from norskallstars_backend.storage_coordination import storage_lock


async def reconcile(
    database: Database, storage: InventoryStorage, grace_seconds: int, *, limit: int = 100
) -> int:
    if not 300 <= grace_seconds <= 86400 or not 1 <= limit <= 100:
        raise ValueError("Explicit bounded cleanup budgets required")
    removed = 0
    now = datetime.now(UTC)
    # Expire mappings in a committed transaction before any external deletion.
    async with database.transaction() as db:
        await db.execute(
            delete(Recording).where(
                or_(
                    Recording.expires_at <= now,
                    (Recording.object_key.is_(None)) & (Recording.offer_expires_at <= now),
                )
            )
        )
        # Nonpersonal hashed-object deletion audit has a bounded operational retention.
        await db.execute(
            delete(StorageDeletion).where(StorageDeletion.created_at < now - timedelta(days=365))
        )
    async with database.transaction() as db:
        await storage_lock(db, exclusive=True)
        reference_list = list(await db.scalars(select(ReleaseAsset.object_key).limit(100001)))
        reference_list += list(
            await db.scalars(
                select(Recording.object_key).where(Recording.object_key.is_not(None)).limit(100001)
            )
        )
        if len(reference_list) > 100000:
            raise ValueError("Storage reference inventory exceeds resource budget")
        references = set(reference_list)
        attempted = 0
        for obj in await storage.inventory():
            if attempted >= limit:
                break
            if obj.key in references or now.timestamp() - obj.modified_at < grace_seconds:
                continue
            # Final reference re-check while all participating writers are excluded.
            course = await db.scalar(
                select(ReleaseAsset.object_key).where(ReleaseAsset.object_key == obj.key).limit(1)
            )
            recording = await db.scalar(
                select(Recording.id).where(Recording.object_key == obj.key).limit(1)
            )
            if course is not None or recording is not None:
                continue
            attempted += 1
            digest = hashlib.sha256(obj.key.encode()).hexdigest()
            # Persist intent independently BEFORE the nontransactional side effect.
            # A crash can leave an intent; an object deletion can never lose all audit evidence.
            async with database.transaction() as audit:
                event = StorageDeletion(key_digest=digest, outcome="intent", created_at=now)
                audit.add(event)
                await audit.flush()
                event_id = event.id
            try:
                await storage.delete(obj.key)
            except Exception:
                outcome = "retry"
            else:
                outcome = "deleted"
                removed += 1
            async with database.transaction() as audit:
                entry = await audit.get(StorageDeletion, event_id)
                if entry is not None:
                    entry.outcome = outcome
    return removed


async def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    settings = load_settings()
    storage = create_storage(settings)
    if storage is None:
        raise RuntimeError("Object storage must be explicitly configured")
    database = Database(settings)
    try:
        count = await reconcile(database, storage, settings.storage_gc_grace_seconds)
        print(f"Storage cleanup completed: {count} objects removed")
    finally:
        await database.close()


if __name__ == "__main__":
    asyncio.run(main())
