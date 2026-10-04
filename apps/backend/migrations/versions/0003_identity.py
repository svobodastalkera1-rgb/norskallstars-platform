"""identity"""

import sqlalchemy as sa
from alembic import op

revision = "0003_identity"
down_revision = "0002_course_releases"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "identity_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=256), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("interface_language", sa.String(length=35), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_identity_accounts")),
        sa.UniqueConstraint("email", name=op.f("uq_identity_accounts_email")),
    )
    op.create_table(
        "identity_rate_buckets",
        sa.Column("digest", sa.String(length=64), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("digest", name=op.f("pk_identity_rate_buckets")),
    )
    op.create_index(
        op.f("ix_identity_rate_buckets_expires_at"),
        "identity_rate_buckets",
        ["expires_at"],
        unique=False,
    )
    op.create_table(
        "identity_google",
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["identity_accounts.id"],
            name=op.f("fk_identity_google_account_id_identity_accounts"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("subject", name=op.f("pk_identity_google")),
        sa.UniqueConstraint("account_id", name=op.f("uq_identity_google_account_id")),
    )
    op.create_table(
        "identity_mail_outbox",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("encrypted_payload", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lease_id", sa.Uuid(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["identity_accounts.id"],
            name=op.f("fk_identity_mail_outbox_account_id_identity_accounts"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_identity_mail_outbox")),
    )
    op.create_index(
        "ix_identity_mail_due",
        "identity_mail_outbox",
        ["next_attempt_at", "expires_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_identity_mail_outbox_account_id"),
        "identity_mail_outbox",
        ["account_id"],
        unique=False,
    )
    op.create_table(
        "identity_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("device_label", sa.String(length=80), nullable=False),
        sa.Column("access_hash", sa.String(length=64), nullable=False),
        sa.Column("access_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["identity_accounts.id"],
            name=op.f("fk_identity_sessions_account_id_identity_accounts"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_identity_sessions")),
        sa.UniqueConstraint("access_hash", name=op.f("uq_identity_sessions_access_hash")),
    )
    op.create_index(
        op.f("ix_identity_sessions_account_id"), "identity_sessions", ["account_id"], unique=False
    )
    op.create_table(
        "identity_one_time_credentials",
        sa.Column("digest", sa.String(length=64), nullable=False),
        sa.Column("purpose", sa.String(length=20), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=True),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column("client_id", sa.String(length=255), nullable=True),
        sa.Column("nonce_hash", sa.String(length=64), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["identity_accounts.id"],
            name=op.f("fk_identity_one_time_credentials_account_id_identity_accounts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["identity_sessions.id"],
            name=op.f("fk_identity_one_time_credentials_session_id_identity_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("digest", name=op.f("pk_identity_one_time_credentials")),
    )
    op.create_index(
        op.f("ix_identity_one_time_credentials_account_id"),
        "identity_one_time_credentials",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_identity_one_time_credentials_expires_at"),
        "identity_one_time_credentials",
        ["expires_at"],
        unique=False,
    )
    op.create_table(
        "identity_refresh_credentials",
        sa.Column("digest", sa.String(length=64), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["identity_sessions.id"],
            name=op.f("fk_identity_refresh_credentials_session_id_identity_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("digest", name=op.f("pk_identity_refresh_credentials")),
    )
    op.create_index(
        op.f("ix_identity_refresh_credentials_session_id"),
        "identity_refresh_credentials",
        ["session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_identity_refresh_credentials_session_id"),
        table_name="identity_refresh_credentials",
    )
    op.drop_table("identity_refresh_credentials")
    op.drop_index(
        op.f("ix_identity_one_time_credentials_expires_at"),
        table_name="identity_one_time_credentials",
    )
    op.drop_index(
        op.f("ix_identity_one_time_credentials_account_id"),
        table_name="identity_one_time_credentials",
    )
    op.drop_table("identity_one_time_credentials")
    op.drop_index(op.f("ix_identity_sessions_account_id"), table_name="identity_sessions")
    op.drop_table("identity_sessions")
    op.drop_index(op.f("ix_identity_mail_outbox_account_id"), table_name="identity_mail_outbox")
    op.drop_index("ix_identity_mail_due", table_name="identity_mail_outbox")
    op.drop_table("identity_mail_outbox")
    op.drop_table("identity_google")
    op.drop_index(op.f("ix_identity_rate_buckets_expires_at"), table_name="identity_rate_buckets")
    op.drop_table("identity_rate_buckets")
    op.drop_table("identity_accounts")
