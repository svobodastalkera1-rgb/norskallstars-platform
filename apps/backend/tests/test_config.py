import secrets

import pytest
from pydantic import ValidationError

from norskallstars_backend.config import Environment, Settings, load_settings


def values(settings):
    return settings.model_dump()


def test_required_credentials_have_no_defaults(monkeypatch):
    for name in ["HOST", "NAME", "USER", "PASSWORD"]:
        monkeypatch.delenv("NORSKALLSTARS_DATABASE_" + name, raising=False)
    with pytest.raises(ValidationError):
        Settings()


def test_environment_and_secret_redaction(settings):
    data = values(settings)
    data["env"] = "dev"
    parsed = Settings(**data)
    assert parsed.env == Environment.LOCAL
    assert parsed.database_password.get_secret_value() not in repr(parsed)
    assert parsed.database_password.get_secret_value() not in repr(parsed.database_url)
    assert parsed.database_password.get_secret_value() not in str(parsed.database_url)


@pytest.mark.parametrize(
    "change",
    [
        {"database_password": "placeholder"},
        {"database_port": 0},
        {"allowed_hosts": ["*"]},
        {"cors_origins": ["*"]},
        {"cors_origins": ["https://user:password@localhost"]},
        {"storage_backend": "local", "storage_root": "relative"},
    ],
)
def test_invalid_configuration(settings, change):
    with pytest.raises(ValidationError):
        Settings(**(values(settings) | change))


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_deployed_configuration_requires_explicit_tls_and_hosts(settings, environment, tmp_path):
    data = values(settings) | {"env": environment}
    with pytest.raises(ValidationError):
        Settings(**data)
    ca = tmp_path / "public-ca.crt"
    ca.write_text("Test configuration path, not a real certificate")
    data |= {
        "database_sslmode": "verify-full",
        "database_sslrootcert": ca,
        "allowed_hosts": ["api.example.invalid"],
    }
    assert Settings(**data).database_sslmode == "verify-full"
    for change in [
        {"log_level": "DEBUG"},
        {"database_user": "postgres"},
        {"storage_backend": "local", "storage_root": tmp_path},
        {"cors_origins": ["http://example.invalid"]},
        {"database_sslrootcert": tmp_path / "missing.crt"},
    ]:
        with pytest.raises(ValidationError):
            Settings(**(data | change))


def test_startup_validation_does_not_expose_inputs(monkeypatch):
    sentinel = secrets.token_urlsafe(32)
    monkeypatch.setenv("NORSKALLSTARS_DATABASE_PORT", sentinel)
    with pytest.raises(RuntimeError) as error:
        load_settings()
    assert sentinel not in str(error.value)


def test_dsn_special_characters_are_not_interpolated(settings):
    password = secrets.token_urlsafe(32) + "@:%/"
    parsed = Settings(**(values(settings) | {"database_password": password}))
    assert parsed.database_url.password == password
