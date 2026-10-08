"""Consent-scoped recordings and storage deletion audit; no change to account erasure."""

import sqlalchemy as sa
from alembic import op

revision = "0005_media"
down_revision = "0004_learning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "media_recordings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "account_id",
            sa.Uuid(),
            sa.ForeignKey("identity_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "attempt_id",
            sa.Uuid(),
            sa.ForeignKey("learning_attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("activity_id", sa.String(128), nullable=False),
        sa.Column("sampled", sa.Boolean(), nullable=False),
        sa.Column("policy_version", sa.String(32), nullable=False),
        sa.Column("consented_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("offer_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("object_key", sa.String(240)),
        sa.Column("checksum", sa.String(64)),
        sa.Column("mime_type", sa.String(64)),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", "activity_id"),
        sa.CheckConstraint("object_key IS NULL OR sampled", name="recording_sample"),
    )
    op.create_table(
        "storage_deletions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("key_digest", sa.String(64), nullable=False),
        sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("storage_deletions")
    op.drop_table("media_recordings")
