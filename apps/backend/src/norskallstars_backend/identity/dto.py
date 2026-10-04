"""Public response contracts exclude persistence credentials and provider subject identifiers."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Output(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Accepted(Output):
    status: Literal["accepted"]


class VerificationRequired(Output):
    status: Literal["verification_required"]


class AccountView(Output):
    id: UUID
    email: str
    email_verified: bool
    interface_language: str
    sign_in_methods: list[Literal["password", "google"]]


class SessionView(Output):
    id: UUID
    device_label: str
    created_at: datetime
    last_used_at: datetime
    expires_at: datetime
    current: bool


class GoogleChallengeView(Output):
    challenge: str = Field(min_length=32, max_length=512)
    nonce: str = Field(min_length=32, max_length=512)


class ReauthenticationView(Output):
    reauthentication_token: str = Field(min_length=32, max_length=512)
    expires_in: int


class ErrorDetail(Output):
    code: str
    request_id: UUID


class ErrorResponse(Output):
    error: ErrorDetail
