import secrets

import pytest

from norskallstars_backend.config import Environment, Settings, load_settings
from norskallstars_backend.database import Database


@pytest.fixture
def settings():
    return Settings(
        env="test",
        database_host="127.0.0.1",
        database_name="unit_test",
        database_user="test_user",
        database_password=secrets.token_urlsafe(36),
    )


@pytest.fixture
def integration_settings():
    settings = load_settings()
    if settings.env != Environment.TEST or not settings.database_name.endswith("_test"):
        pytest.fail("Integration tests require an isolated *_test database and test environment")
    return settings


@pytest.fixture
async def database(integration_settings):
    db = Database(integration_settings)
    try:
        yield db
    finally:
        await db.close()
