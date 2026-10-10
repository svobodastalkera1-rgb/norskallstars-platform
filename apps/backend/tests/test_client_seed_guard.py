"""Client smoke tooling cannot select ordinary runtime/account databases."""

from types import SimpleNamespace

import browser_seed
import pytest

from norskallstars_backend.config import Environment


@pytest.mark.asyncio
async def test_client_seed_refuses_arbitrary_selector():
    with pytest.raises(RuntimeError, match="Unknown synthetic client"):
        await browser_seed.main("ordinary-runtime")


@pytest.mark.asyncio
@pytest.mark.parametrize("client", ["browser", "android"])
async def test_client_seed_refuses_nonisolated_database(monkeypatch, client):
    monkeypatch.setattr(
        browser_seed,
        "load_settings",
        lambda: SimpleNamespace(env=Environment.TEST, database_name="norskallstars_test"),
    )
    with pytest.raises(RuntimeError, match="dedicated synthetic test database"):
        await browser_seed.main(client)
