"""Account-owned media access, one-time sampling and coordinated private retention."""

import base64
import binascii
import calendar
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select

from norskallstars_backend.identity.service import IdentityError, Principal
from norskallstars_backend.learning.models import Attempt, Enrollment
from norskallstars_backend.learning.service import Learning, LearningError
from norskallstars_backend.media.dto import OfferInput, OfferView, RecordingView, UploadInput
from norskallstars_backend.media.models import Recording
from norskallstars_backend.storage import ObjectStorage
from norskallstars_backend.storage_coordination import storage_lock

MAX_AUDIO_BYTES = 262144


def year_after(now: datetime) -> datetime:
    return now.replace(
        year=now.year + 1, day=min(now.day, calendar.monthrange(now.year + 1, now.month)[1])
    )


def audio_bytes(data: UploadInput) -> bytes:
    try:
        raw = base64.b64decode(data.audio_base64, validate=True)
    except (ValueError, binascii.Error):
        raise IdentityError(422, "invalid_audio") from None
    if not 16 <= len(raw) <= MAX_AUDIO_BYTES:
        raise IdentityError(413, "invalid_audio")
    valid = {
        "audio/webm": raw.startswith(b"\x1a\x45\xdf\xa3") and b"webm" in raw[:256],
        "audio/ogg": raw.startswith(b"OggS"),
        "audio/mp4": raw[4:8] == b"ftyp",
        "audio/wav": raw[:4] == b"RIFF" and raw[8:12] == b"WAVE",
    }
    if not valid[data.mime_type]:
        raise IdentityError(422, "invalid_audio")
    # Stored opaque, never fed to a decoder/process in this phase. A future processor
    # needs its own sandbox/parser validation; magic alone does not prove media safety.
    return raw


class Media:
    def __init__(self, learning: Learning, storage: ObjectStorage | None) -> None:
        self.learning, self.storage = learning, storage
        self.identity = learning.identity
        self.database = learning.database

    def required_storage(self) -> ObjectStorage:
        if self.storage is None:
            raise IdentityError(503, "media_unavailable")
        return self.storage

    async def recordings(self, actor: Principal) -> list[RecordingView]:
        async with self.database.transaction() as db:
            await self.identity.locked_principal(db, actor)
            rows = await db.scalars(
                select(Recording)
                .where(Recording.account_id == actor.account_id, Recording.sampled.is_(True))
                .order_by(Recording.consented_at.desc(), Recording.id)
                .limit(100)
            )
            return [
                RecordingView(
                    id=row.id,
                    consented_at=row.consented_at,
                    retention_until=row.expires_at,
                    uploaded=row.object_key is not None,
                )
                for row in rows
            ]

    async def asset(
        self, actor: Principal, enrollment_id: UUID, lid: str, aid: str
    ) -> tuple[bytes, str]:
        from norskallstars_backend.course_packages.models import ReleaseAsset

        storage = self.required_storage()
        async with self.database.transaction() as db:
            enrollment = await self.learning.owned(db, actor, enrollment_id)
            content, _, _ = await self.learning.context(db, enrollment)
            lesson = self.learning.lesson_document(content, lid)
            if (
                not self.learning.available(
                    content, await self.learning.progress(db, enrollment), lid
                )
                and enrollment.recommended_lesson_id != lid
            ):
                raise LearningError(403, "lesson_locked")
            refs = {b.get("asset_ref") for b in lesson["blocks"]}
            for activity_id in lesson["activity_refs"]:
                refs.update(
                    content.documents[f"activities/{activity_id}.json"].get("stimulus_refs", [])
                )
            if aid not in refs:
                raise LearningError()
            asset = await db.get(ReleaseAsset, (enrollment.release_id, aid))
            if asset is None:
                raise LearningError()
            raw = await storage.get(asset.object_key)
            if len(raw) > 10485760 or hashlib.sha256(raw).hexdigest() != asset.checksum:
                raise IdentityError(503, "media_unavailable")
            mime = asset.metadata_json["mime_type"]
            if mime not in {
                "image/png",
                "image/jpeg",
                "image/webp",
                "audio/mpeg",
                "audio/wav",
                "audio/ogg",
            }:
                raise IdentityError(503, "media_unavailable")
            return raw, mime

    async def offer(self, actor: Principal, data: OfferInput) -> OfferView:
        budget_key = self.identity.digest("voice-budget", str(actor.account_id))
        await self.identity.rate_limit("voice-offer", budget_key, budget_key)
        if not data.consent:
            raise IdentityError(422, "consent_required")
        async with self.database.transaction() as db:
            await self.identity.locked_principal(db, actor)
            attempt = await db.scalar(
                select(Attempt)
                .join(Enrollment)
                .where(
                    Attempt.id == data.attempt_id,
                    Enrollment.account_id == actor.account_id,
                )
                .with_for_update(of=Attempt)
            )
            if attempt is None:
                raise LearningError()
            enrollment = await db.get(Enrollment, attempt.enrollment_id)
            if enrollment is None:
                raise LearningError()
            content, _, _ = await self.learning.context(db, enrollment)
            lesson = self.learning.lesson_document(content, attempt.lesson_id)
            if data.activity_id not in lesson["activity_refs"]:
                raise LearningError()
            activity = content.documents[f"activities/{data.activity_id}.json"]
            if activity["response_mode"] != "speech":
                raise IdentityError(422, "invalid_activity")
            record = await db.scalar(
                select(Recording).where(
                    Recording.attempt_id == attempt.id,
                    Recording.activity_id == data.activity_id,
                )
            )
            if record is None:
                if attempt.submitted_at:
                    raise IdentityError(409, "attempt_submitted")
                count = await db.scalar(
                    select(func.count())
                    .select_from(Recording)
                    .where(
                        Recording.account_id == actor.account_id,
                    )
                )
                if (count or 0) >= 100:
                    raise IdentityError(429, "recording_limit")
                now = datetime.now(UTC)
                selected = self.storage is not None and secrets.randbelow(1000000) < int(
                    self.identity.settings.voice_sample_rate * 1000000
                )
                record = Recording(
                    account_id=actor.account_id,
                    attempt_id=attempt.id,
                    activity_id=data.activity_id,
                    sampled=selected,
                    policy_version=data.policy_version,
                    consented_at=now,
                    offer_expires_at=now + timedelta(hours=1),
                    expires_at=year_after(now),
                )
                db.add(record)
                await db.flush()
            return OfferView(
                id=record.id,
                selected=record.sampled,
                expires_at=record.offer_expires_at,
                retention_until=record.expires_at,
            )

    async def upload(self, actor: Principal, rid: UUID, data: UploadInput) -> None:
        storage = self.required_storage()
        raw = audio_bytes(data)
        checksum = hashlib.sha256(raw).hexdigest()
        async with self.database.transaction() as db:
            await self.identity.locked_principal(db, actor)
            await storage_lock(db)
            record = await db.scalar(
                select(Recording)
                .where(
                    Recording.id == rid,
                    Recording.account_id == actor.account_id,
                )
                .with_for_update()
            )
            if record is None:
                raise LearningError()
            if record.expires_at <= datetime.now(UTC):
                raise IdentityError(409, "recording_unavailable")
            if record.object_key:
                if record.checksum != checksum or record.mime_type != data.mime_type:
                    raise IdentityError(409, "recording_conflict")
                return
            if not record.sampled or record.offer_expires_at <= datetime.now(UTC):
                raise IdentityError(409, "recording_unavailable")
            key = "recordings/" + record.id.hex + "/" + checksum
            await storage.put(key, raw)
            if hashlib.sha256(await storage.get(key)).hexdigest() != checksum:
                raise IdentityError(503, "media_unavailable")
            record.object_key, record.checksum, record.mime_type = key, checksum, data.mime_type

    async def erase(self, actor: Principal, rid: UUID) -> None:
        async with self.database.transaction() as db:
            await self.identity.locked_principal(db, actor)
            record = await db.scalar(
                select(Recording)
                .where(
                    Recording.id == rid,
                    Recording.account_id == actor.account_id,
                )
                .with_for_update()
            )
            if record is None:
                raise LearningError()
            # Access/reference removal commits atomically; worker erases the private object.
            await db.delete(record)
