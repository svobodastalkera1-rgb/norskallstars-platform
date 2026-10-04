"""Encrypted transactional outbox, bounded leases and authenticated TLS SMTP."""

import asyncio
import logging
import smtplib
import ssl
from datetime import timedelta
from email.message import EmailMessage
from typing import Literal, Protocol
from uuid import UUID, uuid4

from sqlalchemy import delete, select, update

from norskallstars_backend.config import Environment
from norskallstars_backend.identity.models import (
    DeviceSession,
    MailOutbox,
    OneTimeCredential,
    RateBucket,
)
from norskallstars_backend.identity.security import Email, Input, Token
from norskallstars_backend.identity.service import Identity, now
from norskallstars_backend.logging import exception_fields
from norskallstars_backend.storage import LocalObjectStorage


class MailPayload(Input):
    email: Email
    purpose: Literal["verify", "reset"]
    token: Token


class MailTransport(Protocol):
    async def send(self, message: EmailMessage, message_id: UUID) -> None: ...


class SMTPTransport:
    def __init__(self, identity: Identity) -> None:
        self.settings = identity.settings

    async def send(self, message: EmailMessage, message_id: UUID) -> None:
        def deliver() -> None:
            cfg = self.settings
            if not cfg.smtp_host or not cfg.smtp_username or not cfg.smtp_password:
                raise RuntimeError("Invalid mail transport")
            # Implicit TLS only, using system CA verification. No plaintext fallback.
            with smtplib.SMTP_SSL(
                cfg.smtp_host, cfg.smtp_port, timeout=5, context=ssl.create_default_context()
            ) as smtp:
                smtp.login(
                    cfg.smtp_username.get_secret_value(), cfg.smtp_password.get_secret_value()
                )
                smtp.send_message(message)

        await asyncio.to_thread(deliver)


class LocalMailTransport:
    def __init__(self, identity: Identity, storage: LocalObjectStorage) -> None:
        if identity.settings.env not in (Environment.LOCAL, Environment.TEST):
            raise RuntimeError("Private local mailbox is development-only")
        self.storage = storage

    async def send(self, message: EmailMessage, message_id: UUID) -> None:
        # Private local mailbox, not media storage or an HTTP asset route.
        await self.storage.put(f"mail/{message_id.hex}.eml", message.as_bytes())


class MailWorker:
    def __init__(self, identity: Identity, transport: MailTransport) -> None:
        self.identity, self.transport = identity, transport

    async def drain(self, limit: int = 20) -> dict[str, int]:
        if not 1 <= limit <= 100:
            raise ValueError("Invalid mail batch limit")
        delivered = failed = 0
        # Claim one item at a time so every lease bounds exactly one network operation.
        for _ in range(limit):
            timestamp, lease = now(), uuid4()
            async with self.identity.database.transaction() as db:
                item = await db.scalar(
                    select(MailOutbox)
                    .where(
                        MailOutbox.delivered_at.is_(None),
                        MailOutbox.expires_at > timestamp,
                        MailOutbox.next_attempt_at <= timestamp,
                        MailOutbox.attempts < 5,
                        (MailOutbox.lease_until.is_(None) | (MailOutbox.lease_until <= timestamp)),
                    )
                    .order_by(MailOutbox.created_at)
                    .with_for_update(skip_locked=True)
                    .limit(1)
                )
                if item is None:
                    break
                item.lease_id, item.lease_until = lease, timestamp + timedelta(seconds=30)
                item.attempts += 1
                item_id, payload, attempts = item.id, item.encrypted_payload, item.attempts
            # Re-check committed existence before the external side effect. An in-flight SMTP
            # delivery cannot be unsent after concurrent deletion; its token is then invalid.
            async with self.identity.database.transaction() as db:
                current = await db.get(MailOutbox, item_id)
                valid = (
                    current is not None
                    and current.lease_id == lease
                    and current.expires_at > now()
                    and current.lease_until is not None
                    and current.lease_until > now()
                )
            if not valid:
                continue
            success = False
            try:
                data = MailPayload.model_validate_json(self.identity.cipher.decrypt(payload))
                message = self.message(data, item_id)
                await self.transport.send(message, item_id)
                success = True
            except Exception as exc:
                logging.getLogger("norskallstars.mail").warning(
                    "dependency_unavailable", extra=exception_fields(exc)
                )
                # No plaintext mail, token, destination or SMTP error in logs/CLI output.
                failed += 1
            else:
                delivered += 1
            async with self.identity.database.transaction() as db:
                await db.execute(
                    update(MailOutbox)
                    .where(MailOutbox.id == item_id, MailOutbox.lease_id == lease)
                    .values(
                        delivered_at=now() if success else None,
                        lease_id=None,
                        lease_until=None,
                        next_attempt_at=now() + timedelta(seconds=min(60 * 2**attempts, 3600)),
                    )
                )
        return {"delivered": delivered, "failed": failed}

    def message(self, data: MailPayload, message_id: UUID) -> EmailMessage:
        message = EmailMessage()
        message["From"] = self.identity.settings.mail_sender or "noreply@example.com"
        message["To"] = data.email
        message["Message-ID"] = f"<{message_id.hex}@norskallstars.invalid>"
        message["Subject"] = (
            "NorskAllstars: verify your email"
            if data.purpose == "verify"
            else "NorskAllstars: reset your password"
        )
        # Fragment keeps the secret out of HTTP URLs/logs/referrers. Clients submit it as JSON.
        link = (
            f"{self.identity.settings.identity_public_origin}/account/{data.purpose}#token="
            + data.token.get_secret_value()
        )
        message.set_content(
            f"Use this single-use link to {data.purpose} your account:\n{link}\n"
            "If you did not request this, ignore this message.\n"
        )
        return message


async def cleanup(identity: Identity) -> dict[str, int]:
    # Identity credential/mail retention only; never deletes course objects or release state.
    removed: dict[str, int] = {}
    cutoff = now()
    async with identity.database.transaction() as db:
        for name, model, predicate in (
            ("mail", MailOutbox, MailOutbox.expires_at <= cutoff),
            ("credentials", OneTimeCredential, OneTimeCredential.expires_at <= cutoff),
            ("rate_buckets", RateBucket, RateBucket.expires_at <= cutoff),
            (
                "sessions",
                DeviceSession,
                (DeviceSession.expires_at <= cutoff)
                | (DeviceSession.revoked_at <= cutoff - timedelta(days=1)),
            ),
        ):
            result = await db.execute(
                delete(model).where(predicate).returning(model.__table__.c[0])
            )
            removed[name] = len(result.all())
    return removed
