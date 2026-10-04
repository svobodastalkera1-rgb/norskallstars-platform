"""Shared transactional identity, ownership checks and revocable opaque sessions."""

import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import delete, func, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from norskallstars_backend.config import Settings
from norskallstars_backend.database import Database
from norskallstars_backend.identity.google import GoogleClaims, GoogleVerifier
from norskallstars_backend.identity.models import (
    Account,
    DeviceSession,
    GoogleIdentity,
    MailOutbox,
    OneTimeCredential,
    RateBucket,
    RefreshCredential,
)
from norskallstars_backend.identity.security import digest, hash_password, token, verify_password

ACCESS_TTL = timedelta(minutes=15)
SESSION_TTL = timedelta(days=30)
REFRESH_TTL = timedelta(days=7)


def now() -> datetime:
    return datetime.now(UTC)


class IdentityError(Exception):
    def __init__(self, status: int = 401, code: str = "authentication_failed") -> None:
        self.status, self.code = status, code


@dataclass(frozen=True)
class Principal:
    account_id: UUID
    session_id: UUID


@dataclass(frozen=True)
class SessionTokens:
    access_token: str
    refresh_token: str
    session_id: UUID
    expires_in: int = 900
    token_type: str = "Bearer"  # noqa: S105 -- public authentication scheme, not a secret


class Identity:
    def __init__(self, settings: Settings, database: Database, google: GoogleVerifier) -> None:
        self.settings, self.database, self.google = settings, database, google
        self.cipher = Fernet(settings.identity_mail_key.get_secret_value().encode())

    def digest(self, purpose: str, value: str) -> str:
        return digest(self.settings.identity_pepper, purpose, value)

    async def rate_limit(self, operation: str, remote: str, email: str = "") -> None:
        # HMAC buckets contain no raw IP/email. Count rejections too; never roll them back.
        timestamp = now()
        epoch = int(timestamp.timestamp())
        limits = [
            ("global", 60, 300),
            (
                "ip:" + remote,
                60 if operation == "http" else 600,
                120 if operation == "http" else 60,
            ),
        ]
        if email:
            limits.append(("email:" + email, 600, 6))
        denied = False
        async with self.database.transaction() as db:
            for key, seconds, limit in limits:
                end = datetime.fromtimestamp((epoch // seconds + 1) * seconds, UTC)
                key_hash = self.digest("rate", f"{operation}:{key}:{epoch // seconds}")
                statement = insert(RateBucket).values(digest=key_hash, count=1, expires_at=end)
                increment = statement.on_conflict_do_update(
                    index_elements=[RateBucket.digest], set_={"count": RateBucket.count + 1}
                ).returning(RateBucket.count)
                count = (await db.execute(increment)).scalar_one()
                denied |= count > limit
        if denied:
            raise IdentityError(429, "rate_limited")

    async def email_lock(self, db: AsyncSession, email: str) -> None:
        # Serialize registration/federation against one canonical email, across instances.
        key = int(self.digest("email-lock", email)[:16], 16)
        key = key if key < 2**63 else key - 2**64
        await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})

    async def issue_mail(self, db: AsyncSession, account: Account, purpose: str) -> None:
        timestamp = now()
        expires = timestamp + (
            timedelta(hours=24) if purpose == "verify" else timedelta(minutes=30)
        )
        await db.execute(
            delete(OneTimeCredential).where(
                OneTimeCredential.account_id == account.id, OneTimeCredential.purpose == purpose
            )
        )
        # Superseded unsent mail cannot deliver invalid tokens later.
        await db.execute(delete(MailOutbox).where(MailOutbox.account_id == account.id))
        raw = token()
        db.add(
            OneTimeCredential(
                digest=self.digest(purpose, raw),
                purpose=purpose,
                account_id=account.id,
                expires_at=expires,
            )
        )
        payload = json.dumps({"email": account.email, "purpose": purpose, "token": raw}).encode()
        db.add(
            MailOutbox(
                account_id=account.id,
                encrypted_payload=self.cipher.encrypt(payload),
                created_at=timestamp,
                expires_at=expires,
                next_attempt_at=timestamp,
            )
        )

    async def register(self, email: str, password: SecretStr) -> None:
        # Equal expensive work for existing/new addresses; response never discloses existence.
        encoded = await hash_password(password)
        async with self.database.transaction() as db:
            await self.email_lock(db, email)
            account = await db.scalar(
                select(Account).where(Account.email == email).with_for_update()
            )
            if account is None:
                account = Account(email=email, password_hash=encoded, created_at=now())
                db.add(account)
                await db.flush()
                await self.issue_mail(db, account, "verify")
            # Existing unverified accounts are not overwritten/linked using a public signup.

    async def email_request(self, email: str, purpose: str) -> None:
        async with self.database.transaction() as db:
            account = await db.scalar(
                select(Account).where(Account.email == email).with_for_update()
            )
            if account and (
                (purpose == "verify" and not account.verified_at)
                or (purpose == "reset" and account.verified_at)
            ):
                await self.issue_mail(db, account, purpose)

    async def account_for_token(
        self, db: AsyncSession, purpose: str, raw: str
    ) -> tuple[Account, OneTimeCredential]:
        key = self.digest(purpose, raw)
        candidate = await db.scalar(
            select(OneTimeCredential).where(
                OneTimeCredential.digest == key, OneTimeCredential.purpose == purpose
            )
        )
        if candidate is None or candidate.account_id is None:
            raise IdentityError(400, "invalid_token")
        # All account writes lock account first, then session/token. Re-read after lock.
        account = await db.get(Account, candidate.account_id, with_for_update=True)
        credential = await db.get(
            OneTimeCredential, key, with_for_update=True, populate_existing=True
        )
        if account is None or credential is None or credential.expires_at <= now():
            raise IdentityError(400, "invalid_token")
        return account, credential

    async def verify_email(self, raw: str) -> None:
        async with self.database.transaction() as db:
            account, credential = await self.account_for_token(db, "verify", raw)
            account.verified_at = now()
            await db.delete(credential)
            await db.execute(delete(MailOutbox).where(MailOutbox.account_id == account.id))

    async def reset_password(self, raw: str, password: SecretStr) -> None:
        encoded = await hash_password(password)
        async with self.database.transaction() as db:
            account, credential = await self.account_for_token(db, "reset", raw)
            if not account.verified_at:
                raise IdentityError(400, "invalid_token")
            account.password_hash = encoded
            await db.delete(credential)
            await self.revoke_all(db, account.id)
            await db.execute(
                delete(OneTimeCredential).where(OneTimeCredential.account_id == account.id)
            )
            await db.execute(delete(MailOutbox).where(MailOutbox.account_id == account.id))

    async def new_session(self, db: AsyncSession, account: Account, device: str) -> SessionTokens:
        timestamp = now()
        active = (
            await db.scalars(
                select(DeviceSession)
                .where(
                    DeviceSession.account_id == account.id,
                    DeviceSession.revoked_at.is_(None),
                    DeviceSession.expires_at > timestamp,
                )
                .order_by(DeviceSession.created_at)
            )
        ).all()
        # Keep a bounded device list; oldest active session is revoked on the eleventh sign-in.
        for old in active[:-9]:
            old.revoked_at = timestamp
        access, refresh = token(), token()
        session = DeviceSession(
            account_id=account.id,
            device_label=device,
            access_hash=self.digest("access", access),
            access_expires_at=timestamp + ACCESS_TTL,
            expires_at=timestamp + SESSION_TTL,
            created_at=timestamp,
            last_used_at=timestamp,
        )
        db.add(session)
        await db.flush()
        db.add(
            RefreshCredential(
                digest=self.digest("refresh", refresh),
                session_id=session.id,
                expires_at=timestamp + REFRESH_TTL,
            )
        )
        return SessionTokens(access, refresh, session.id)

    async def sign_in(self, email: str, password: SecretStr, device: str) -> SessionTokens:
        async with self.database.transaction() as db:
            account = await db.scalar(
                select(Account).where(Account.email == email).with_for_update()
            )
            valid = await verify_password(password, account.password_hash if account else None)
            if not valid or account is None or not account.verified_at:
                raise IdentityError()
            return await self.new_session(db, account, device)

    async def locked_principal(
        self, db: AsyncSession, principal: Principal
    ) -> tuple[Account, DeviceSession]:
        account = await db.get(Account, principal.account_id, with_for_update=True)
        session = await db.scalar(
            select(DeviceSession)
            .where(
                DeviceSession.id == principal.session_id,
                DeviceSession.account_id == principal.account_id,
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if account is None or session is None or session.account_id != principal.account_id:
            raise IdentityError()
        if session.revoked_at or session.expires_at <= now() or session.access_expires_at <= now():
            raise IdentityError()
        return account, session

    async def authenticate(self, raw: str) -> Principal:
        async with self.database.transaction() as db:
            session = await db.scalar(
                select(DeviceSession).where(
                    DeviceSession.access_hash == self.digest("access", raw),
                    DeviceSession.revoked_at.is_(None),
                    DeviceSession.expires_at > now(),
                    DeviceSession.access_expires_at > now(),
                )
            )
            if session is None:
                raise IdentityError()
            return Principal(session.account_id, session.id)

    async def refresh(self, raw: str) -> SessionTokens:
        result: SessionTokens | None = None
        key = self.digest("refresh", raw)
        async with self.database.transaction() as db:
            candidate = await db.get(RefreshCredential, key)
            if candidate is None:
                raise IdentityError()
            initial = await db.get(DeviceSession, candidate.session_id)
            if initial is None:
                raise IdentityError()
            await db.get(Account, initial.account_id, with_for_update=True)
            session = await db.get(
                DeviceSession, initial.id, with_for_update=True, populate_existing=True
            )
            credential = await db.get(
                RefreshCredential, key, with_for_update=True, populate_existing=True
            )
            if session is None or credential is None or session.revoked_at:
                raise IdentityError()
            rotations = await db.scalar(
                select(func.count())
                .select_from(RefreshCredential)
                .where(RefreshCredential.session_id == session.id)
            )
            if (
                credential.used_at
                or credential.expires_at <= now()
                or session.expires_at <= now()
                or (rotations or 0) >= 256
            ):
                session.revoked_at = now()
                # Commit revocation before returning an error, preserving replay defense.
            else:
                timestamp = now()
                credential.used_at = timestamp
                access, refresh = token(), token()
                session.access_hash = self.digest("access", access)
                session.access_expires_at = min(timestamp + ACCESS_TTL, session.expires_at)
                session.last_used_at = timestamp
                db.add(
                    RefreshCredential(
                        digest=self.digest("refresh", refresh),
                        session_id=session.id,
                        expires_at=min(timestamp + REFRESH_TTL, session.expires_at),
                    )
                )
                result = SessionTokens(
                    access,
                    refresh,
                    session.id,
                    int((session.access_expires_at - timestamp).total_seconds()),
                )
        if result is None:
            raise IdentityError()
        return result

    async def me(self, principal: Principal) -> dict[str, object]:
        async with self.database.transaction() as db:
            account, _ = await self.locked_principal(db, principal)
            google = await db.scalar(
                select(GoogleIdentity).where(GoogleIdentity.account_id == account.id)
            )
            return {
                "id": str(account.id),
                "email": account.email,
                "email_verified": account.verified_at is not None,
                "interface_language": account.interface_language,
                "sign_in_methods": (["password"] if account.password_hash else [])
                + (["google"] if google else []),
            }

    async def preferences(self, principal: Principal, language: str) -> None:
        async with self.database.transaction() as db:
            account, _ = await self.locked_principal(db, principal)
            account.interface_language = language.lower()

    async def sessions(self, principal: Principal) -> list[dict[str, object]]:
        async with self.database.transaction() as db:
            await self.locked_principal(db, principal)
            sessions = (
                await db.scalars(
                    select(DeviceSession)
                    .where(
                        DeviceSession.account_id == principal.account_id,
                        DeviceSession.revoked_at.is_(None),
                        DeviceSession.expires_at > now(),
                    )
                    .order_by(DeviceSession.created_at)
                )
            ).all()
            return [
                {
                    "id": str(s.id),
                    "device_label": s.device_label,
                    "created_at": s.created_at.isoformat(),
                    "last_used_at": s.last_used_at.isoformat(),
                    "expires_at": s.expires_at.isoformat(),
                    "current": s.id == principal.session_id,
                }
                for s in sessions
            ]

    async def revoke_all(self, db: AsyncSession, account_id: UUID) -> None:
        await db.execute(
            update(DeviceSession)
            .where(DeviceSession.account_id == account_id, DeviceSession.revoked_at.is_(None))
            .values(revoked_at=now())
        )
        await db.execute(
            delete(OneTimeCredential).where(
                OneTimeCredential.account_id == account_id,
                OneTimeCredential.session_id.is_not(None),
            )
        )

    async def revoke(self, principal: Principal, session_id: UUID | None) -> None:
        async with self.database.transaction() as db:
            await self.locked_principal(db, principal)
            if session_id is None:
                await self.revoke_all(db, principal.account_id)
            else:
                session = await db.scalar(
                    select(DeviceSession)
                    .where(
                        DeviceSession.id == session_id,
                        DeviceSession.account_id == principal.account_id,
                    )
                    .with_for_update()
                )
                if session is None or session.account_id != principal.account_id:
                    raise IdentityError(404, "not_found")
                session.revoked_at = now()

    async def challenge(self, client_id: str) -> dict[str, str]:
        if client_id not in self.settings.google_client_ids:
            raise IdentityError(400, "invalid_request")
        raw, nonce = token(), token()
        async with self.database.transaction() as db:
            db.add(
                OneTimeCredential(
                    digest=self.digest("google", raw),
                    purpose="google",
                    client_id=client_id,
                    nonce_hash=self.digest("nonce", nonce),
                    expires_at=now() + timedelta(minutes=5),
                )
            )
        return {"challenge": raw, "nonce": nonce}

    async def google_claims(self, challenge: str, encoded: str) -> GoogleClaims:
        async with self.database.transaction() as db:
            credential = await db.get(OneTimeCredential, self.digest("google", challenge))
            if (
                credential is None
                or credential.purpose != "google"
                or credential.expires_at <= now()
                or credential.client_id is None
            ):
                raise IdentityError()
            client_id = credential.client_id
        claims = await self.google.verify(encoded, client_id)
        if not hmac.compare_digest(self.digest("nonce", claims.nonce), credential.nonce_hash or ""):
            raise IdentityError()
        return claims

    async def consume_challenge(self, db: AsyncSession, raw: str) -> None:
        credential = await db.get(
            OneTimeCredential, self.digest("google", raw), with_for_update=True
        )
        if credential is None or credential.purpose != "google" or credential.expires_at <= now():
            raise IdentityError()
        await db.delete(credential)

    async def google_sign_in(
        self, challenge: str, encoded: str, device: str
    ) -> SessionTokens | None:
        claims = await self.google_claims(challenge, encoded)
        async with self.database.transaction() as db:
            await self.email_lock(db, claims.email)
            # Serialize first-use of a provider subject even when its email changes concurrently.
            await self.email_lock(db, "google-sub:" + claims.subject)
            provider = await db.get(GoogleIdentity, claims.subject)
            if provider:
                account = await db.get(Account, provider.account_id, with_for_update=True)
            else:
                existing = await db.scalar(select(Account).where(Account.email == claims.email))
                if existing:
                    # Email equality is not proof of permission to link accounts.
                    raise IdentityError()
                account = Account(
                    email=claims.email,
                    created_at=now(),
                    verified_at=now() if claims.authoritative_email else None,
                )
                db.add(account)
                await db.flush()
                db.add(GoogleIdentity(subject=claims.subject, account_id=account.id))
            if account is None:
                raise IdentityError()
            await self.consume_challenge(db, challenge)
            if not account.verified_at:
                # Google is not authoritative for non-Gmail/non-Workspace third-party email.
                await self.issue_mail(db, account, "verify")
                return None
            return await self.new_session(db, account, device)

    async def reauthenticate(
        self,
        principal: Principal,
        purpose: str,
        password: SecretStr | None,
        google_proof: tuple[str, str] | None,
    ) -> str:
        if (password is None) == (google_proof is None):
            raise IdentityError(400, "invalid_request")
        claims = await self.google_claims(*google_proof) if google_proof else None
        async with self.database.transaction() as db:
            account, _ = await self.locked_principal(db, principal)
            if password is not None:
                if not await verify_password(password, account.password_hash):
                    raise IdentityError()
            else:
                provider = await db.get(GoogleIdentity, claims.subject if claims else "")
                if provider is None or provider.account_id != account.id or google_proof is None:
                    raise IdentityError()
                await self.consume_challenge(db, google_proof[0])
            raw = token()
            db.add(
                OneTimeCredential(
                    digest=self.digest("reauth", raw),
                    purpose=purpose,
                    account_id=account.id,
                    session_id=principal.session_id,
                    expires_at=now() + timedelta(minutes=5),
                )
            )
            return raw

    async def consume_reauth(
        self, db: AsyncSession, principal: Principal, raw: str, purpose: str
    ) -> None:
        credential = await db.scalar(
            select(OneTimeCredential)
            .where(
                OneTimeCredential.digest == self.digest("reauth", raw),
                OneTimeCredential.account_id == principal.account_id,
                OneTimeCredential.session_id == principal.session_id,
                OneTimeCredential.purpose == purpose,
            )
            .with_for_update()
        )
        if (
            credential is None
            or credential.purpose != purpose
            or credential.expires_at <= now()
            or credential.account_id != principal.account_id
            or credential.session_id != principal.session_id
        ):
            raise IdentityError()
        await db.delete(credential)
        await db.flush()

    async def change_password(self, principal: Principal, raw: str, password: SecretStr) -> None:
        encoded = await hash_password(password)
        async with self.database.transaction() as db:
            account, _ = await self.locked_principal(db, principal)
            await self.consume_reauth(db, principal, raw, "password")
            account.password_hash = encoded
            await self.revoke_all(db, account.id)
            await db.execute(
                delete(OneTimeCredential).where(OneTimeCredential.account_id == account.id)
            )
            await db.execute(delete(MailOutbox).where(MailOutbox.account_id == account.id))

    async def link_google(
        self, principal: Principal, raw: str, challenge: str, encoded: str
    ) -> None:
        claims = await self.google_claims(challenge, encoded)
        async with self.database.transaction() as db:
            await self.email_lock(db, "google-sub:" + claims.subject)
            account, _ = await self.locked_principal(db, principal)
            await self.consume_reauth(db, principal, raw, "link")
            existing = await db.get(GoogleIdentity, claims.subject)
            linked = await db.scalar(
                select(GoogleIdentity).where(GoogleIdentity.account_id == account.id)
            )
            if (existing and existing.account_id != account.id) or (
                linked and linked.subject != claims.subject
            ):
                raise IdentityError(409, "identity_conflict")
            await self.consume_challenge(db, challenge)
            if not existing:
                db.add(GoogleIdentity(subject=claims.subject, account_id=account.id))

    async def delete_account(self, principal: Principal, raw: str) -> None:
        async with self.database.transaction() as db:
            account, _ = await self.locked_principal(db, principal)
            await self.consume_reauth(db, principal, raw, "delete")
            # All identity-owned data cascades; future domains must add explicit erasure hooks.
            await db.delete(account)
