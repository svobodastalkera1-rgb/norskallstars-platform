"""Private recording provenance and pseudonymous operational storage deletion audit."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from norskallstars_backend.database import Base


class Recording(Base):
    __tablename__ = "media_recordings"
    __table_args__ = (
        UniqueConstraint("attempt_id", "activity_id"),
        CheckConstraint("object_key IS NULL OR sampled", name="recording_sample"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("identity_accounts.id", ondelete="CASCADE"))
    attempt_id: Mapped[UUID] = mapped_column(ForeignKey("learning_attempts.id", ondelete="CASCADE"))
    activity_id: Mapped[str] = mapped_column(String(128))
    sampled: Mapped[bool] = mapped_column(Boolean)
    policy_version: Mapped[str] = mapped_column(String(32))
    consented_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    offer_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    object_key: Mapped[str | None] = mapped_column(String(240))
    checksum: Mapped[str | None] = mapped_column(String(64))
    mime_type: Mapped[str | None] = mapped_column(String(64))


class StorageDeletion(Base):
    __tablename__ = "storage_deletions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    key_digest: Mapped[str] = mapped_column(String(64))
    outcome: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
