"""Bounded engagement evidence for private dashboard time; never learning credit."""

import sqlalchemy as sa
from alembic import op

revision = "0006_learning_engagement"
down_revision = "0005_media"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("learning_attempts", sa.Column("active_seconds", sa.Integer(), nullable=True))
    op.add_column(
        "learning_attempts", sa.Column("engagement_sequence", sa.Integer(), nullable=True)
    )
    op.add_column(
        "learning_attempts", sa.Column("last_engaged_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_check_constraint(
        "engagement_seconds", "learning_attempts", "active_seconds IS NULL OR active_seconds >= 0"
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_learning_attempts_engagement_seconds"), "learning_attempts", type_="check"
    )
    op.drop_column("learning_attempts", "last_engaged_at")
    op.drop_column("learning_attempts", "engagement_sequence")
    op.drop_column("learning_attempts", "active_seconds")
