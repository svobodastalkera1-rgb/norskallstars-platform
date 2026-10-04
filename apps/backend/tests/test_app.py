import asyncio
import io
import json
import logging
import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel

from norskallstars_backend.app import create_app
from norskallstars_backend.config import Settings
from norskallstars_backend.database import Database
from norskallstars_backend.logging import JsonFormatter


def client_app(settings):
    database = Database(settings)
    database.ready = AsyncMock(return_value=True)
    database.close = AsyncMock(wraps=database.close)
    return create_app(settings, database), database


def test_startup_liveness_and_shutdown(settings):
    app, database = client_app(settings)
    with TestClient(app) as client:
        response = client.get("/health/live")
        assert response.status_code == 200 and response.json() == {"status": "alive"}
        assert uuid.UUID(response.headers["x-request-id"])
        assert response.headers["cache-control"] == "no-store"
        database.ready.assert_not_awaited()
    database.close.assert_awaited_once()


def test_readiness_status_and_sanitized_failure(settings):
    app, database = client_app(settings)
    with TestClient(app) as client:
        assert client.get("/health/ready").json() == {"status": "ready"}
        database.ready.side_effect = RuntimeError("private-database-connection-detail")
        response = client.get("/health/ready")
        assert response.status_code == 503 and response.json() == {"status": "not_ready"}
        assert "private-database" not in response.text
        assert client.get("/health/live").status_code == 200


def test_readiness_timeout_is_bounded(settings):
    settings = Settings(**(settings.model_dump() | {"readiness_timeout": 0.1}))
    app, database = client_app(settings)

    async def stalled():
        await asyncio.sleep(1)
        return True

    database.ready.side_effect = stalled
    with TestClient(app) as client:
        assert client.get("/health/ready").status_code == 503


@pytest.mark.parametrize("identifier", [str(uuid.uuid4()), "invalid\tvalue", "x" * 300])
def test_correlation_ids_and_safe_logging(settings, identifier):
    app, _ = client_app(settings)
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logging.getLogger().addHandler(handler)
    with TestClient(app) as client:
        response = client.get(
            "/health/live?token=private-query",
            headers={"X-Request-ID": identifier, "Authorization": "Bearer private-header"},
        )
    actual = response.headers["x-request-id"]
    assert str(uuid.UUID(actual)) == actual
    entries = [json.loads(line) for line in stream.getvalue().splitlines()]
    completed = next(entry for entry in entries if entry["event"] == "request_completed")
    assert completed["request_id"] == actual and completed["status"] == 200
    assert "private-query" not in stream.getvalue() and "private-header" not in stream.getvalue()
    if len(identifier) == 36:
        assert actual == identifier


def test_errors_and_validation_do_not_echo_payloads(settings):
    app, _ = client_app(settings)
    sentinel = "confidential-runtime-value"
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logging.getLogger().addHandler(handler)

    @app.get("/_test/error")
    async def explode():
        raise RuntimeError(sentinel)

    @app.get("/_test/http-error")
    async def http_error():
        raise HTTPException(status_code=409, detail=sentinel)

    class Payload(BaseModel):
        number: int

    @app.post("/_test/validate")
    async def validate(payload: Payload):
        return {"number": payload.number}

    with TestClient(app) as client:
        for path, expected in [("/_test/error", 500), ("/_test/http-error", 409)]:
            response = client.get(path)
            assert response.status_code == expected and sentinel not in response.text
            assert response.json()["error"]["request_id"] == response.headers["x-request-id"]
        response = client.post("/_test/validate", json={"number": sentinel})
        assert response.status_code == 422 and sentinel not in response.text
    output = stream.getvalue()
    assert sentinel not in output
    assert '"exception_type": "RuntimeError"' in output and '"frames":' in output


def test_library_exception_and_message_are_not_serialized():
    sentinel = "sensitive-driver-value"
    record = logging.LogRecord(
        "third_party",
        logging.ERROR,
        __file__,
        1,
        "error: %s",
        (sentinel,),
        (RuntimeError, RuntimeError(sentinel), None),
    )
    assert sentinel not in JsonFormatter().format(record)


def test_host_cors_and_body_bounds(settings):
    app, _ = client_app(settings)

    @app.post("/_test/body")
    async def consume(request: Request):
        await request.body()
        return {"ok": True}

    with TestClient(app) as client:
        assert (
            client.get("/health/live", headers={"Host": "evil.example.invalid"}).status_code == 400
        )
        assert (
            "access-control-allow-origin"
            not in client.get(
                "/health/live", headers={"Origin": "https://evil.example.invalid"}
            ).headers
        )
        assert (
            client.post("/_test/body", content=b"x" * (settings.max_request_bytes + 1)).status_code
            == 413
        )
        response = client.post(
            "/_test/body", content=iter([b"x" * settings.max_request_bytes, b"x"])
        )
        assert response.status_code == 413


def test_request_timeout(settings):
    settings = Settings(**(settings.model_dump() | {"request_timeout": 1}))
    app, _ = client_app(settings)

    @app.get("/_test/slow")
    async def slow():
        await asyncio.sleep(2)

    with TestClient(app) as client:
        assert client.get("/_test/slow").status_code == 504


def test_production_has_no_debug_docs_and_sets_security_headers(settings, tmp_path):
    ca = tmp_path / "test-ca.crt"
    ca.write_text("Configuration placeholder")
    production = Settings(
        **(
            settings.model_dump()
            | {
                "env": "production",
                "database_sslmode": "verify-full",
                "database_sslrootcert": ca,
                "allowed_hosts": ["api.example.invalid"],
                "identity_public_origin": "https://app.example.invalid",
                "google_client_ids": ["synthetic.apps.googleusercontent.com"],
                "mail_transport": "smtp",
                "smtp_host": "smtp.example.invalid",
                "smtp_username": "synthetic",
                "smtp_password": settings.database_password,
                "mail_sender": "noreply@example.com",
            }
        )
    )
    app, _ = client_app(production)
    with TestClient(app, base_url="https://api.example.invalid") as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["strict-transport-security"] == "max-age=31536000"
