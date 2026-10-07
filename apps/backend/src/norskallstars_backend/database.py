"""Owned async pool/transactions and migration-aware readiness, without product tables."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from norskallstars_backend.config import Settings

SCHEMA_REVISION = "0004_learning"


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class Database:
    def __init__(self, settings: Settings) -> None:
        args: dict[str, object] = {
            "connect_timeout": settings.database_connect_timeout,
            "sslmode": settings.database_sslmode,
            "options": "-c statement_timeout=5000",
        }
        if settings.database_sslrootcert:
            args["sslrootcert"] = str(settings.database_sslrootcert)
        self.engine = create_async_engine(
            settings.database_url,
            connect_args=args,
            pool_pre_ping=True,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_connect_timeout,
            echo=False,
            hide_parameters=True,
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncSession]:
        # Commit only on success; rollback and close on exceptions/cancellation.
        async with self.sessions.begin() as session:
            yield session

    async def ready(self) -> bool:
        async with self.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            revisions = (
                (await connection.execute(text("SELECT version_num FROM alembic_version")))
                .scalars()
                .all()
            )
            return revisions == [SCHEMA_REVISION]

    async def close(self) -> None:
        await self.engine.dispose()
