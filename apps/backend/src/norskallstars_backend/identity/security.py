"""Bounded password work, purpose-separated credential hashing and strict JSON inputs."""

import asyncio
import hashlib
import hmac
import secrets
import unicodedata
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from threading import BoundedSemaphore
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, SecretStr

HASHER = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=1)
PASSWORD_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="password")
PASSWORD_SLOTS = BoundedSemaphore(20)


class PasswordCapacityError(Exception):
    pass


async def password_job[T](function: Callable[[], T]) -> T:
    # Cancellation must not release capacity while native Argon2 work still runs.
    # Two workers bound memory; twenty slots bound pending work, including abandoned requests.
    if not PASSWORD_SLOTS.acquire(blocking=False):
        raise PasswordCapacityError

    def bounded() -> T:
        try:
            return function()
        finally:
            PASSWORD_SLOTS.release()

    try:
        future = PASSWORD_EXECUTOR.submit(bounded)
    except Exception:
        PASSWORD_SLOTS.release()
        raise
    return await asyncio.shield(asyncio.wrap_future(future))


DUMMY_HASH = HASHER.hash(secrets.token_urlsafe(32))
# Initial public blocklist; no breached-password lookup sends user passwords off-platform.
BLOCKED_PASSWORDS = frozenset(
    {
        "passwordpassword",
        "123456789012345",
        "qwertyuiopasdfgh",
        "norskallstars123",
        "letmeinletmein123",
    }
)


def normalize_email(value: object) -> str:
    if not isinstance(value, str) or len(value) > 254:
        raise ValueError("Invalid email")
    try:
        return str(validate_email(value, check_deliverability=False).normalized).casefold()
    except EmailNotValidError:
        raise ValueError("Invalid email") from None


def normalize_password(value: object) -> SecretStr:
    if isinstance(value, SecretStr):
        value = value.get_secret_value()
    if not isinstance(value, str):
        raise ValueError("Invalid password")
    value = unicodedata.normalize("NFC", value)
    if not 15 <= len(value) <= 128 or value.casefold() in BLOCKED_PASSWORDS:
        raise ValueError("Password does not meet policy")
    if any(unicodedata.category(char).startswith("C") for char in value):
        raise ValueError("Invalid password")
    return SecretStr(value)


Email = Annotated[str, BeforeValidator(normalize_email)]
NewPassword = Annotated[SecretStr, BeforeValidator(normalize_password)]
Token = Annotated[SecretStr, Field(min_length=32, max_length=512)]
DeviceLabel = Annotated[str, Field(min_length=1, max_length=80, pattern=r"^[^\x00-\x1f\x7f]+$")]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class Registration(Input):
    email: Email
    password: NewPassword


class EmailRequest(Input):
    email: Email


class TokenRequest(Input):
    token: Token


class PasswordReset(TokenRequest):
    password: NewPassword


class SignIn(Input):
    email: Email
    password: SecretStr = Field(min_length=1, max_length=128)
    device_label: DeviceLabel


class Refresh(Input):
    refresh_token: Token


class GoogleChallenge(Input):
    client_id: str = Field(min_length=1, max_length=255)


class GoogleProof(Input):
    challenge: Token
    id_token: SecretStr = Field(min_length=1, max_length=16384)


class GoogleSignIn(GoogleProof):
    device_label: DeviceLabel


class Reauthentication(Input):
    purpose: str = Field(pattern=r"^(password|delete|link)$")
    password: SecretStr | None = Field(default=None, min_length=1, max_length=128)
    google: GoogleProof | None = None


class AuthorizedChange(Input):
    reauthentication_token: Token


class PasswordChange(AuthorizedChange):
    password: NewPassword


class GoogleLink(GoogleProof, AuthorizedChange):
    pass


class Preferences(Input):
    # BCP47 shape only: a preference is not a promise that UI translations exist.
    interface_language: str = Field(
        min_length=2, max_length=35, pattern=r"^[A-Za-z]{2,8}(-[A-Za-z0-9]{1,8})*$"
    )


def token() -> str:
    return secrets.token_urlsafe(32)


def digest(pepper: SecretStr, purpose: str, value: str) -> str:
    return hmac.new(
        pepper.get_secret_value().encode(), (purpose + "\0" + value).encode(), hashlib.sha256
    ).hexdigest()


async def hash_password(password: SecretStr) -> str:
    return await password_job(lambda: HASHER.hash(password.get_secret_value()))


async def verify_password(password: SecretStr, encoded: str | None) -> bool:
    def verify() -> bool:
        try:
            HASHER.verify(
                encoded or DUMMY_HASH, unicodedata.normalize("NFC", password.get_secret_value())
            )
            return encoded is not None
        except (VerificationError, InvalidHashError):
            return False

    return await password_job(verify)
