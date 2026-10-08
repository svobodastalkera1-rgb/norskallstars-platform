"""Cross-domain storage mutation/GC serialization, held until reference commit."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

STORAGE_LOCK = 791032145002


async def storage_lock(db: AsyncSession, *, exclusive: bool = False) -> None:
    function = "pg_advisory_xact_lock" if exclusive else "pg_advisory_xact_lock_shared"
    await db.execute(text(f"SELECT {function}(:key)"), {"key": STORAGE_LOCK})
