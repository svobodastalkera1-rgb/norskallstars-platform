"""Immutable versioned curriculum payload, asset mapping and publication audit."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from norskallstars_backend.database import Base


class CourseRelease(Base):
    __tablename__ = "course_releases"
    __table_args__ = (
        UniqueConstraint("course_id", "course_version"),
        UniqueConstraint("package_digest"),
        CheckConstraint("state IN ('staged', 'published')", name="release_state"),
        CheckConstraint("state <> 'published' OR release_eligible", name="release_eligibility"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    course_id: Mapped[str] = mapped_column(String(128))
    course_version: Mapped[str] = mapped_column(String(64))
    schema_version: Mapped[str] = mapped_column(String(64))
    content_version: Mapped[str] = mapped_column(String(16384))
    package_digest: Mapped[str] = mapped_column(String(64))
    archive_digest: Mapped[str] = mapped_column(String(64))
    importer_version: Mapped[str] = mapped_column(String(16), default="1.0.0")
    contract_digest: Mapped[str] = mapped_column(String(64))
    release_eligible: Mapped[bool] = mapped_column(Boolean)
    state: Mapped[str] = mapped_column(String(16), default="staged")
    manifest: Mapped[dict[str, Any]] = mapped_column(JSONB)
    documents: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReleaseAsset(Base):
    __tablename__ = "release_assets"
    release_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("course_releases.id"), primary_key=True
    )
    asset_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    object_key: Mapped[str] = mapped_column(String(240))
    checksum: Mapped[str] = mapped_column(String(64))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB)


class ReleaseEvent(Base):
    __tablename__ = "release_events"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    release_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("course_releases.id"))
    action: Mapped[str] = mapped_column(String(16))
    actor: Mapped[str] = mapped_column(String(128))
    approval: Mapped[str] = mapped_column(String(240))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
