"""Identity data and single-use credentials; never persist plaintext bearer tokens."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, LargeBinary, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from norskallstars_backend.database import Base


class Account(Base):
    __tablename__ = "identity_accounts"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(256))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    interface_language: Mapped[str] = mapped_column(String(35), default="nb")


class GoogleIdentity(Base):
    __tablename__ = "identity_google"
    subject: Mapped[str] = mapped_column(String(255), primary_key=True)
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("identity_accounts.id", ondelete="CASCADE"), unique=True
    )


class DeviceSession(Base):
    __tablename__ = "identity_sessions"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("identity_accounts.id", ondelete="CASCADE"), index=True
    )
    device_label: Mapped[str] = mapped_column(String(80))
    access_hash: Mapped[str] = mapped_column(String(64), unique=True)
    access_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RefreshCredential(Base):
    __tablename__ = "identity_refresh_credentials"
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("identity_sessions.id", ondelete="CASCADE"), index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OneTimeCredential(Base):
    __tablename__ = "identity_one_time_credentials"
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    purpose: Mapped[str] = mapped_column(String(20))
    account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("identity_accounts.id", ondelete="CASCADE"), index=True
    )
    session_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("identity_sessions.id", ondelete="CASCADE")
    )
    client_id: Mapped[str | None] = mapped_column(String(255))
    nonce_hash: Mapped[str | None] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class MailOutbox(Base):
    __tablename__ = "identity_mail_outbox"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("identity_accounts.id", ondelete="CASCADE"), index=True
    )
    # Recipient, action and token are encrypted together, not exposed in queue/log metadata.
    encrypted_payload: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lease_id: Mapped[UUID | None] = mapped_column(Uuid)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (Index("ix_identity_mail_due", "next_attempt_at", "expires_at"),)


class RateBucket(Base):
    __tablename__ = "identity_rate_buckets"
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    count: Mapped[int] = mapped_column(Integer)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
