"""Explicit consent is independent of learning credit and evaluator claims."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StrictBool

from norskallstars_backend.learning.dto import LearningDTO
from norskallstars_backend.learning.policy import Id


class OfferInput(LearningDTO):
    attempt_id: UUID
    activity_id: Id
    consent: StrictBool
    policy_version: Literal["voice-1"]


class OfferView(LearningDTO):
    id: UUID
    selected: bool
    expires_at: datetime
    retention_until: datetime
    purpose: Literal["speaking_response_processing"] = "speaking_response_processing"
    policy_version: Literal["voice-1"] = "voice-1"


class UploadInput(LearningDTO):
    audio_base64: Annotated[str, Field(min_length=1, max_length=350000)]
    mime_type: Literal["audio/webm", "audio/ogg", "audio/mp4", "audio/wav"]


class RecordingView(LearningDTO):
    id: UUID
    consented_at: datetime
    retention_until: datetime
    uploaded: bool
    purpose: Literal["speaking_response_processing"] = "speaking_response_processing"
    policy_version: Literal["voice-1"] = "voice-1"
