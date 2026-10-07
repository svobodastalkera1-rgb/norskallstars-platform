"""Policy provenance and account-owned, release-pinned learning records."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from norskallstars_backend.database import Base


class RuleSet(Base):
    __tablename__ = "learning_rule_sets"
    __table_args__ = (
        UniqueConstraint("release_id", "version"),
        UniqueConstraint("id", "release_id"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    release_id: Mapped[UUID] = mapped_column(ForeignKey("course_releases.id"))
    version: Mapped[str] = mapped_column(String(64))
    digest: Mapped[str] = mapped_column(String(64))
    document: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CourseSelection(Base):
    __tablename__ = "learning_course_selections"
    __table_args__ = (
        ForeignKeyConstraint(
            ["release_id", "course_id"], ["course_releases.id", "course_releases.course_id"]
        ),
        ForeignKeyConstraint(
            ["policy_id", "release_id"], ["learning_rule_sets.id", "learning_rule_sets.release_id"]
        ),
    )
    course_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    release_id: Mapped[UUID] = mapped_column()
    policy_id: Mapped[UUID] = mapped_column()


class PolicyAudit(Base):
    __tablename__ = "learning_policy_audit"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    policy_id: Mapped[UUID] = mapped_column(ForeignKey("learning_rule_sets.id"))
    actor: Mapped[str] = mapped_column(String(128))
    approval: Mapped[str] = mapped_column(String(240))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Enrollment(Base):
    __tablename__ = "learning_enrollments"
    __table_args__ = (
        UniqueConstraint("account_id", "course_id"),
        ForeignKeyConstraint(
            ["release_id", "course_id"], ["course_releases.id", "course_releases.course_id"]
        ),
        ForeignKeyConstraint(
            ["policy_id", "release_id"], ["learning_rule_sets.id", "learning_rule_sets.release_id"]
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("identity_accounts.id", ondelete="CASCADE"), index=True
    )
    course_id: Mapped[str] = mapped_column(String(128))
    release_id: Mapped[UUID] = mapped_column()
    policy_id: Mapped[UUID] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    recommended_lesson_id: Mapped[str | None] = mapped_column(String(128))


class Attempt(Base):
    __tablename__ = "learning_attempts"
    __table_args__ = (
        UniqueConstraint("enrollment_id", "operation_id"),
        CheckConstraint("active_seconds IS NULL OR active_seconds >= 0", name="engagement_seconds"),
        CheckConstraint("kind IN ('canonical', 'practice')", name="attempt_kind"),
        CheckConstraint(
            "(submitted_at IS NULL AND results IS NULL AND request_digest IS NULL) OR "
            "(submitted_at IS NOT NULL AND results IS NOT NULL AND request_digest IS NOT NULL)",
            name="attempt_submission",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    enrollment_id: Mapped[UUID] = mapped_column(
        ForeignKey("learning_enrollments.id", ondelete="CASCADE"), index=True
    )
    active_seconds: Mapped[int | None] = mapped_column(Integer)
    engagement_sequence: Mapped[int | None] = mapped_column(Integer)
    last_engaged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    operation_id: Mapped[UUID] = mapped_column()
    lesson_id: Mapped[str] = mapped_column(String(128))
    lesson_version: Mapped[str] = mapped_column(String(64))
    kind: Mapped[str] = mapped_column(String(16))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    request_digest: Mapped[str | None] = mapped_column(String(64))
    results: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class LessonProgress(Base):
    __tablename__ = "learning_lesson_progress"
    __table_args__ = (
        CheckConstraint(
            "mastery_status IN ('unknown', 'not_applicable', 'assessed')", name="mastery_status"
        ),
        CheckConstraint(
            "(mastery_status = 'assessed' AND mastered IS NOT NULL AND score IS NOT NULL) OR "
            "(mastery_status <> 'assessed' AND mastered IS NULL)",
            name="mastery_value",
        ),
        CheckConstraint("score IS NULL OR (score >= 0 AND score <= 1)", name="progress_score"),
        CheckConstraint("review_step >= 0", name="review_step"),
    )
    enrollment_id: Mapped[UUID] = mapped_column(
        ForeignKey("learning_enrollments.id", ondelete="CASCADE"), primary_key=True
    )
    lesson_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    mastery_status: Mapped[str] = mapped_column(String(24))
    mastered: Mapped[bool | None] = mapped_column(Boolean)
    score: Mapped[Decimal | None] = mapped_column(Numeric(30, 28))
    review_step: Mapped[int] = mapped_column(Integer)
    review_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class LearningEvent(Base):
    __tablename__ = "learning_events"
    __table_args__ = (
        UniqueConstraint("enrollment_id", "operation_id", "kind"),
        CheckConstraint(
            "kind IN ('attempt_started', 'attempt_evaluated', 'lesson_completed', "
            "'translation_requested', 'placement_accepted')",
            name="event_kind",
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    enrollment_id: Mapped[UUID] = mapped_column(
        ForeignKey("learning_enrollments.id", ondelete="CASCADE"), index=True
    )
    operation_id: Mapped[UUID] = mapped_column()
    kind: Mapped[str] = mapped_column(String(32))
    lesson_id: Mapped[str] = mapped_column(String(128))
    block_id: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PlacementResult(Base):
    __tablename__ = "learning_placements"
    __table_args__ = (
        UniqueConstraint("enrollment_id", "operation_id"),
        CheckConstraint("score >= 0 AND score <= 1", name="placement_score"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    enrollment_id: Mapped[UUID] = mapped_column(
        ForeignKey("learning_enrollments.id", ondelete="CASCADE"), index=True
    )
    operation_id: Mapped[UUID] = mapped_column()
    request_digest: Mapped[str] = mapped_column(String(64))
    assessment_version: Mapped[str] = mapped_column(String(64))
    score: Mapped[Decimal] = mapped_column(Numeric(30, 28))
    recommended_lesson_id: Mapped[str] = mapped_column(String(128))
    results: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
