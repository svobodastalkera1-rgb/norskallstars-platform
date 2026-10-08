"""Migration CLI with the same settings/driver as the runtime; never log a DSN."""

import asyncio
import logging

from alembic import context
from sqlalchemy.engine import Connection

from norskallstars_backend.config import load_settings
from norskallstars_backend.course_packages.models import CourseRelease
from norskallstars_backend.database import Database
from norskallstars_backend.identity.models import Account  # noqa: F401 -- register metadata
from norskallstars_backend.learning.models import Enrollment  # noqa: F401 -- register metadata
from norskallstars_backend.logging import configure_logging, exception_fields
from norskallstars_backend.media.models import Recording  # noqa: F401 -- register metadata


def run(connection: Connection) -> None:
    context.configure(
        connection=connection, target_metadata=CourseRelease.metadata, compare_type=True
    )
    with context.begin_transaction():
        context.run_migrations()


async def online() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)
    database = Database(settings)
    try:
        async with database.engine.connect() as connection:
            await connection.run_sync(run)
    except Exception as exc:
        logging.getLogger("norskallstars.migrations").error(
            "unexpected_error", extra=exception_fields(exc)
        )
        raise RuntimeError("Migration failed; check database access and revision") from None
    finally:
        await database.close()


if context.is_offline_mode():
    context.configure(
        dialect_name="postgresql", target_metadata=CourseRelease.metadata, literal_binds=True
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    asyncio.run(online())
