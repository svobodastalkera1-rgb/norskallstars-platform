"""learning"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_learning"
down_revision = "0003_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        op.f("uq_course_releases_id"), "course_releases", ["id", "course_id"]
    )
    op.create_table(
        "learning_rule_sets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("release_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("digest", sa.String(length=64), nullable=False),
        sa.Column("document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["release_id"],
            ["course_releases.id"],
            name=op.f("fk_learning_rule_sets_release_id_course_releases"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_learning_rule_sets")),
        sa.UniqueConstraint("id", "release_id", name=op.f("uq_learning_rule_sets_id")),
        sa.UniqueConstraint("release_id", "version", name=op.f("uq_learning_rule_sets_release_id")),
    )
    op.create_table(
        "learning_course_selections",
        sa.Column("course_id", sa.String(length=128), nullable=False),
        sa.Column("release_id", sa.Uuid(), nullable=False),
        sa.Column("policy_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["policy_id", "release_id"],
            ["learning_rule_sets.id", "learning_rule_sets.release_id"],
            name=op.f("fk_learning_course_selections_policy_id_learning_rule_sets"),
        ),
        sa.ForeignKeyConstraint(
            ["release_id", "course_id"],
            ["course_releases.id", "course_releases.course_id"],
            name=op.f("fk_learning_course_selections_release_id_course_releases"),
        ),
        sa.PrimaryKeyConstraint("course_id", name=op.f("pk_learning_course_selections")),
    )
    op.create_table(
        "learning_enrollments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.String(length=128), nullable=False),
        sa.Column("release_id", sa.Uuid(), nullable=False),
        sa.Column("policy_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recommended_lesson_id", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["identity_accounts.id"],
            name=op.f("fk_learning_enrollments_account_id_identity_accounts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["policy_id", "release_id"],
            ["learning_rule_sets.id", "learning_rule_sets.release_id"],
            name=op.f("fk_learning_enrollments_policy_id_learning_rule_sets"),
        ),
        sa.ForeignKeyConstraint(
            ["release_id", "course_id"],
            ["course_releases.id", "course_releases.course_id"],
            name=op.f("fk_learning_enrollments_release_id_course_releases"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_learning_enrollments")),
        sa.UniqueConstraint(
            "account_id", "course_id", name=op.f("uq_learning_enrollments_account_id")
        ),
    )
    op.create_index(
        op.f("ix_learning_enrollments_account_id"),
        "learning_enrollments",
        ["account_id"],
        unique=False,
    )
    op.create_table(
        "learning_policy_audit",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("policy_id", sa.Uuid(), nullable=False),
        sa.Column("actor", sa.String(length=128), nullable=False),
        sa.Column("approval", sa.String(length=240), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["policy_id"],
            ["learning_rule_sets.id"],
            name=op.f("fk_learning_policy_audit_policy_id_learning_rule_sets"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_learning_policy_audit")),
    )
    op.create_table(
        "learning_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("enrollment_id", sa.Uuid(), nullable=False),
        sa.Column("operation_id", sa.Uuid(), nullable=False),
        sa.Column("lesson_id", sa.String(length=128), nullable=False),
        sa.Column("lesson_version", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("request_digest", sa.String(length=64), nullable=True),
        sa.Column("results", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.CheckConstraint(
            "kind IN ('canonical', 'practice')", name=op.f("ck_learning_attempts_attempt_kind")
        ),
        sa.CheckConstraint(
            "(submitted_at IS NULL AND results IS NULL AND request_digest IS NULL) OR "
            "(submitted_at IS NOT NULL AND results IS NOT NULL AND request_digest IS NOT NULL)",
            name=op.f("ck_learning_attempts_attempt_submission"),
        ),
        sa.ForeignKeyConstraint(
            ["enrollment_id"],
            ["learning_enrollments.id"],
            name=op.f("fk_learning_attempts_enrollment_id_learning_enrollments"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_learning_attempts")),
        sa.UniqueConstraint(
            "enrollment_id", "operation_id", name=op.f("uq_learning_attempts_enrollment_id")
        ),
    )
    op.create_index(
        op.f("ix_learning_attempts_enrollment_id"),
        "learning_attempts",
        ["enrollment_id"],
        unique=False,
    )
    op.create_table(
        "learning_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("enrollment_id", sa.Uuid(), nullable=False),
        sa.Column("operation_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("lesson_id", sa.String(length=128), nullable=False),
        sa.Column("block_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "kind IN ('attempt_started', 'attempt_evaluated', 'lesson_completed', "
            "'translation_requested', 'placement_accepted')",
            name=op.f("ck_learning_events_event_kind"),
        ),
        sa.ForeignKeyConstraint(
            ["enrollment_id"],
            ["learning_enrollments.id"],
            name=op.f("fk_learning_events_enrollment_id_learning_enrollments"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_learning_events")),
        sa.UniqueConstraint(
            "enrollment_id", "operation_id", "kind", name=op.f("uq_learning_events_enrollment_id")
        ),
    )
    op.create_index(
        op.f("ix_learning_events_enrollment_id"), "learning_events", ["enrollment_id"], unique=False
    )
    op.create_table(
        "learning_lesson_progress",
        sa.Column("enrollment_id", sa.Uuid(), nullable=False),
        sa.Column("lesson_id", sa.String(length=128), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mastery_status", sa.String(length=24), nullable=False),
        sa.Column("mastered", sa.Boolean(), nullable=True),
        sa.Column("score", sa.Numeric(precision=30, scale=28), nullable=True),
        sa.Column("review_step", sa.Integer(), nullable=False),
        sa.Column("review_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(mastery_status = 'assessed' AND mastered IS NOT NULL AND score IS NOT NULL) OR "
            "(mastery_status <> 'assessed' AND mastered IS NULL)",
            name=op.f("ck_learning_lesson_progress_mastery_value"),
        ),
        sa.CheckConstraint(
            "mastery_status IN ('unknown', 'not_applicable', 'assessed')",
            name=op.f("ck_learning_lesson_progress_mastery_status"),
        ),
        sa.CheckConstraint(
            "review_step >= 0", name=op.f("ck_learning_lesson_progress_review_step")
        ),
        sa.CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 1)",
            name=op.f("ck_learning_lesson_progress_progress_score"),
        ),
        sa.ForeignKeyConstraint(
            ["enrollment_id"],
            ["learning_enrollments.id"],
            name=op.f("fk_learning_lesson_progress_enrollment_id_learning_enrollments"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "enrollment_id", "lesson_id", name=op.f("pk_learning_lesson_progress")
        ),
    )
    op.create_index(
        op.f("ix_learning_lesson_progress_review_due_at"),
        "learning_lesson_progress",
        ["review_due_at"],
        unique=False,
    )
    op.create_table(
        "learning_placements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("enrollment_id", sa.Uuid(), nullable=False),
        sa.Column("operation_id", sa.Uuid(), nullable=False),
        sa.Column("request_digest", sa.String(length=64), nullable=False),
        sa.Column("assessment_version", sa.String(length=64), nullable=False),
        sa.Column("score", sa.Numeric(precision=30, scale=28), nullable=False),
        sa.Column("recommended_lesson_id", sa.String(length=128), nullable=False),
        sa.Column("results", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "score >= 0 AND score <= 1", name=op.f("ck_learning_placements_placement_score")
        ),
        sa.ForeignKeyConstraint(
            ["enrollment_id"],
            ["learning_enrollments.id"],
            name=op.f("fk_learning_placements_enrollment_id_learning_enrollments"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_learning_placements")),
        sa.UniqueConstraint(
            "enrollment_id", "operation_id", name=op.f("uq_learning_placements_enrollment_id")
        ),
    )
    op.create_index(
        op.f("ix_learning_placements_enrollment_id"),
        "learning_placements",
        ["enrollment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_learning_placements_enrollment_id"), table_name="learning_placements")
    op.drop_table("learning_placements")
    op.drop_index(
        op.f("ix_learning_lesson_progress_review_due_at"), table_name="learning_lesson_progress"
    )
    op.drop_table("learning_lesson_progress")
    op.drop_index(op.f("ix_learning_events_enrollment_id"), table_name="learning_events")
    op.drop_table("learning_events")
    op.drop_index(op.f("ix_learning_attempts_enrollment_id"), table_name="learning_attempts")
    op.drop_table("learning_attempts")
    op.drop_table("learning_policy_audit")
    op.drop_index(op.f("ix_learning_enrollments_account_id"), table_name="learning_enrollments")
    op.drop_table("learning_enrollments")
    op.drop_table("learning_course_selections")
    op.drop_table("learning_rule_sets")
    op.drop_constraint(op.f("uq_course_releases_id"), "course_releases", type_="unique")
