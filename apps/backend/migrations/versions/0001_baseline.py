"""Initialize Alembic revision tracking without any product tables."""

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alembic manages alembic_version. Phase 1 has no product schema.
    pass


def downgrade() -> None:
    pass
