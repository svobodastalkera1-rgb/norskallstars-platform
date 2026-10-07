"""Explicit typed environment settings; never load a working-directory .env implicitly."""

from enum import StrEnum
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Environment(StrEnum):
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NORSKALLSTARS_", env_file=None, extra="forbid", hide_input_in_errors=True
    )
    env: Environment
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    database_host: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,252}$")
    database_port: int = Field(default=5432, ge=1, le=65535)
    database_name: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_]{0,62}$")
    database_user: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_]{0,62}$")
    database_password: SecretStr
    database_sslmode: Literal["disable", "verify-full"] = "disable"
    database_sslrootcert: Path | None = None
    database_connect_timeout: int = Field(default=3, ge=1, le=10)
    database_pool_size: int = Field(default=5, ge=1, le=20)
    database_max_overflow: int = Field(default=5, ge=0, le=20)
    readiness_timeout: float = Field(default=4, ge=0.1, le=10)
    request_timeout: float = Field(default=30, ge=1, le=120)
    max_request_bytes: int = Field(default=1_048_576, ge=1024, le=10_485_760)
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "testserver"]
    cors_origins: list[str] = []
    storage_backend: Literal["disabled", "local"] = "disabled"
    storage_root: Path | None = None
    storage_max_bytes: int = Field(default=10_485_760, ge=1, le=104_857_600)

    identity_pepper: SecretStr
    identity_mail_key: SecretStr
    identity_public_origin: str = "http://localhost:3000"
    google_client_ids: list[str] = []
    mail_transport: Literal["outbox", "smtp"] = "outbox"
    smtp_host: str | None = Field(default=None, pattern=r"^[A-Za-z0-9][A-Za-z0-9.-]{0,252}$")
    smtp_port: int = Field(default=465, ge=1, le=65535)
    smtp_username: SecretStr | None = None
    smtp_password: SecretStr | None = None
    mail_sender: str | None = None

    @field_validator("identity_pepper")
    @classmethod
    def identity_key_strength(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("Identity pepper must contain at least 32 characters")
        return value

    @field_validator("identity_mail_key")
    @classmethod
    def valid_mail_key(cls, value: SecretStr) -> SecretStr:
        from cryptography.fernet import Fernet

        try:
            Fernet(value.get_secret_value().encode())
        except (ValueError, TypeError):
            raise ValueError("An explicit Fernet key is required") from None
        return value

    @field_validator("env", mode="before")
    @classmethod
    def environment_alias(cls, value: object) -> object:
        return "local" if value == "dev" else value

    @field_validator("database_password")
    @classmethod
    def password_strength(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 24:
            raise ValueError("Database password must contain at least 24 characters")
        return value

    @model_validator(mode="after")
    def validate_boundaries(self) -> Self:
        if not self.allowed_hosts or any(
            "*" in host or "/" in host or "\n" in host or "\r" in host
            for host in self.allowed_hosts
        ):
            raise ValueError("Explicit allowed hosts are required; wildcards are forbidden")
        for origin in [*self.cors_origins, self.identity_public_origin]:
            from urllib.parse import urlsplit

            parsed = urlsplit(origin)
            if (
                parsed.scheme not in ("http", "https")
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.path
                or parsed.query
                or parsed.fragment
                or "*" in origin
            ):
                raise ValueError("CORS origins must be explicit HTTP(S) origins")
        if len(self.google_client_ids) > 8 or len(set(self.google_client_ids)) != len(
            self.google_client_ids
        ):
            raise ValueError("Explicit unique Google audiences are required")
        if any(
            not client.endswith(".apps.googleusercontent.com")
            or len(client) > 255
            or not client.replace("-", "").replace(".", "").isalnum()
            for client in self.google_client_ids
        ):
            raise ValueError("Invalid Google client identifier")
        if self.mail_transport == "smtp":
            from email_validator import EmailNotValidError, validate_email

            if not all((self.smtp_host, self.smtp_username, self.smtp_password, self.mail_sender)):
                raise ValueError("Authenticated TLS SMTP configuration is required")
            try:
                validate_email(self.mail_sender or "", check_deliverability=False)
            except EmailNotValidError:
                raise ValueError("Invalid mail sender") from None
            if not self.smtp_username or not self.smtp_username.get_secret_value().strip():
                raise ValueError("SMTP username is required")
            if not self.smtp_password or not self.smtp_password.get_secret_value():
                raise ValueError("SMTP password is required")
        if self.storage_backend == "local" and (
            self.storage_root is None or not self.storage_root.is_absolute()
        ):
            raise ValueError("Local storage requires an explicit absolute root")
        if self.env in (Environment.STAGING, Environment.PRODUCTION):
            if self.database_sslmode != "verify-full":
                raise ValueError("Staging/production require verified PostgreSQL TLS")
            if self.database_sslrootcert is None or not self.database_sslrootcert.is_file():
                raise ValueError("Staging/production require a mounted PostgreSQL CA file")
            if self.database_user.lower() == "postgres":
                raise ValueError(
                    "Staging/production must not use the default database administrator"
                )
            if self.log_level == "DEBUG" or self.storage_backend == "local":
                raise ValueError("Debug logging and local asset storage are development-only")
            if any(host in ("localhost", "127.0.0.1", "testserver") for host in self.allowed_hosts):
                raise ValueError("Staging/production require explicit service hosts")
            if self.mail_transport != "smtp" or not self.google_client_ids:
                raise ValueError("Staging/production require SMTP and explicit Google audiences")
            if not self.identity_public_origin.startswith("https://"):
                raise ValueError("Staging/production identity links require HTTPS")
            if any(not origin.startswith("https://") for origin in self.cors_origins):
                raise ValueError("Staging/production CORS requires HTTPS")
        return self

    @property
    def database_url(self) -> URL:
        # URL.create escapes credentials. Do not serialize this URL to logs/config files.
        return URL.create(
            "postgresql+psycopg",
            username=self.database_user,
            password=self.database_password.get_secret_value(),
            host=self.database_host,
            port=self.database_port,
            database=self.database_name,
        )


def load_settings() -> Settings:
    from pydantic import ValidationError

    try:
        return Settings()  # type: ignore[call-arg]  # required fields come from environment
    except ValidationError:
        # Uvicorn/CLI startup must not print raw environment values or validation inputs.
        raise RuntimeError("Invalid backend configuration; check documented settings") from None
