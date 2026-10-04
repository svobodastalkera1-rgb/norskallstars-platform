"""Immutable package releases, storage references and transition audit."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_course_releases"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "course_releases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.String(128), nullable=False),
        sa.Column("course_version", sa.String(64), nullable=False),
        sa.Column("schema_version", sa.String(64), nullable=False),
        sa.Column("content_version", sa.String(16384), nullable=False),
        sa.Column("package_digest", sa.String(64), nullable=False),
        sa.Column("archive_digest", sa.String(64), nullable=False),
        sa.Column("importer_version", sa.String(16), nullable=False),
        sa.Column("contract_digest", sa.String(64), nullable=False),
        sa.Column("release_eligible", sa.Boolean(), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("manifest", postgresql.JSONB(), nullable=False),
        sa.Column("documents", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "course_version"),
        sa.UniqueConstraint("package_digest"),
        sa.CheckConstraint(
            "state IN ('staged', 'published')", name=op.f("ck_course_releases_release_state")
        ),
        sa.CheckConstraint(
            "state <> 'published' OR release_eligible",
            name=op.f("ck_course_releases_release_eligibility"),
        ),
    )
    op.create_table(
        "release_assets",
        sa.Column("release_id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.String(128), nullable=False),
        sa.Column("object_key", sa.String(240), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(["release_id"], ["course_releases.id"]),
        sa.PrimaryKeyConstraint("release_id", "asset_id"),
    )
    op.create_table(
        "release_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("release_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("approval", sa.String(240), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["release_id"], ["course_releases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("release_events")
    op.drop_table("release_assets")
    op.drop_table("course_releases")
