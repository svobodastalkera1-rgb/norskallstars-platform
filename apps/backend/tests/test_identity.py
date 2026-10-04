"""Synthetic shared-account HTTP/DB flows, adversarial inputs and transaction regressions."""

import asyncio
import io
import json
import logging
import secrets
import time
from datetime import timedelta
from email import policy
from email.parser import BytesParser
from uuid import UUID, uuid4

import httpx2
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import PyJWK
from pydantic import SecretStr, ValidationError
from sqlalchemy import func, select, text, update

from norskallstars_backend.app import create_app
from norskallstars_backend.config import Settings
from norskallstars_backend.identity.google import GoogleVerificationError, GoogleVerifier
from norskallstars_backend.identity.mail import LocalMailTransport, MailWorker, cleanup
from norskallstars_backend.identity.models import (
    Account,
    DeviceSession,
    GoogleIdentity,
    MailOutbox,
    OneTimeCredential,
    RateBucket,
    RefreshCredential,
)
from norskallstars_backend.identity.security import (
    Preferences,
    Registration,
    digest,
    hash_password,
    normalize_email,
    normalize_password,
    token,
    verify_password,
)
from norskallstars_backend.identity.service import IdentityError, now
from norskallstars_backend.logging import JsonFormatter
from norskallstars_backend.storage import LocalObjectStorage

CLIENT_ID = "synthetic.apps.googleusercontent.com"
EMAIL = "synthetic@example.com"
HEADERS = {"X-NorskAllstars-Client": "android"}


@pytest.fixture
async def identity_runtime(database, integration_settings):
    cfg = Settings(**(integration_settings.model_dump() | {"google_client_ids": [CLIENT_ID]}))
    async with database.transaction() as db:
        await db.execute(text("TRUNCATE identity_accounts, identity_rate_buckets CASCADE"))
    app = create_app(cfg, database)
    service = app.state.identity
    async with httpx2.AsyncClient(
        transport=httpx2.ASGITransport(app=app), base_url="http://testserver", headers=HEADERS
    ) as client:
        yield service, client
    async with database.transaction() as db:
        await db.execute(text("TRUNCATE identity_accounts, identity_rate_buckets CASCADE"))
        await db.execute(text("DELETE FROM identity_one_time_credentials"))


@pytest.fixture
def password():
    return secrets.token_urlsafe(24)


def bearer(session):
    return {"Authorization": "Bearer " + session["access_token"]}


async def mail_token(service, email=EMAIL, purpose="verify"):
    async with service.database.transaction() as db:
        payload = await db.scalar(
            select(MailOutbox.encrypted_payload).join(Account).where(Account.email == email)
        )
        assert payload is not None
        data = json.loads(service.cipher.decrypt(payload))
        assert data["purpose"] == purpose and data["email"] == email
        assert data["token"].encode() not in payload and email.encode() not in payload
        return data["token"]


async def verified(service, client, password, email=EMAIL):
    result = await client.post(
        "/api/v1/identity/register", json={"email": email, "password": password}
    )
    assert result.status_code == 202
    raw = await mail_token(service, email)
    assert (
        await client.post("/api/v1/identity/verification/confirm", json={"token": raw})
    ).status_code == 200
    result = await client.post(
        "/api/v1/identity/sign-in",
        json={"email": email, "password": password, "device_label": "Synthetic Android"},
    )
    assert result.status_code == 200
    return result.json()


async def proof(client, session, password, purpose):
    result = await client.post(
        "/api/v1/identity/reauthenticate",
        headers=bearer(session),
        json={"password": password, "purpose": purpose},
    )
    assert result.status_code == 200
    return result.json()["reauthentication_token"]


@pytest.fixture
def google_signer():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
    jwk.update(kid="synthetic", use="sig", alg="RS256")

    def sign(input_nonce, **changes):
        claims = {
            "iss": "https://accounts.google.com",
            "sub": "synthetic-google-subject",
            "aud": CLIENT_ID,
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "nonce": input_nonce,
            "email": EMAIL,
            "email_verified": True,
            "hd": "example.com",
        }
        claims.update(changes)
        return jwt.encode(claims, key, algorithm="RS256", headers={"kid": "synthetic"})

    return sign, jwk


async def google_proof(service, client, google_signer, **changes):
    sign, jwk = google_signer
    service.google.keys = {"synthetic": PyJWK.from_dict(jwk)}
    service.google.until = time.monotonic() + 300
    challenge = await client.post(
        "/api/v1/identity/google/challenge", json={"client_id": CLIENT_ID}
    )
    assert challenge.status_code == 200
    payload = challenge.json()
    return {"challenge": payload["challenge"], "id_token": sign(payload["nonce"], **changes)}


async def test_password_hashing_and_email_normalization():
    password = SecretStr(secrets.token_urlsafe(24))
    encoded = await hash_password(password)
    assert encoded.startswith("$argon2id$") and password.get_secret_value() not in encoded
    assert await verify_password(password, encoded)
    assert not await verify_password(SecretStr(secrets.token_urlsafe(24)), encoded)
    assert not await verify_password(password, None)
    assert not await verify_password(password, "malformed")
    assert normalize_email("SYNTHETIC@EXAMPLE.COM") == EMAIL
    assert normalize_password("x" * 15).get_secret_value() == "x" * 15
    assert normalize_password("e\u0301" * 15).get_secret_value() == "é" * 15


@pytest.mark.parametrize("value", ["short", "x" * 129, "123456789012345", "x" * 15 + "\n", 123])
def test_password_policy_rejects_unsafe_inputs(value):
    with pytest.raises(ValueError):
        normalize_password(value)


@pytest.mark.parametrize("value", ["a", "x\r\n@example.com", "user@localhost", 42, "x" * 255])
def test_email_input_validation(value):
    with pytest.raises(ValueError):
        normalize_email(value)


def test_input_models_forbid_role_and_bounded_preferences(password):
    with pytest.raises(ValidationError):
        Registration(email=EMAIL, password=password, role="admin")
    for language in ["x", "../nb", "nb\n", "nb" + "-abcdefgh" * 5]:
        with pytest.raises(ValidationError):
            Preferences(interface_language=language)
    assert Preferences(interface_language="nb-NO").interface_language == "nb-NO"


@pytest.mark.parametrize(
    "change",
    [
        {"identity_pepper": "short"},
        {"identity_mail_key": "invalid"},
        {"identity_public_origin": "https://app.example.invalid/path"},
        {"identity_public_origin": "https://user:password@app.example.invalid"},
        {"google_client_ids": [CLIENT_ID, CLIENT_ID]},
        {"google_client_ids": ["https://evil.example.invalid"]},
        {"mail_transport": "smtp"},
    ],
)
def test_identity_configuration_fails_closed(settings, change):
    with pytest.raises(ValidationError):
        Settings(**(settings.model_dump() | change))


def test_independent_hashed_credential_purposes(settings):
    raw = token()
    values = {
        digest(settings.identity_pepper, purpose, raw)
        for purpose in ["access", "refresh", "verify", "reset", "reauth", "nonce", "rate"]
    }
    assert len(values) == 7 and all(raw not in value for value in values)


@pytest.mark.integration
async def test_signup_verification_login_shared_preferences_and_no_plaintext(
    identity_runtime, password
):
    service, client = identity_runtime
    session = await verified(service, client, password)
    me = await client.get("/api/v1/identity/me", headers=bearer(session))
    assert me.status_code == 200 and me.json()["email"] == EMAIL
    assert me.json()["interface_language"] == "nb" and me.json()["sign_in_methods"] == ["password"]
    assert "no-store" in me.headers["cache-control"]
    assert (
        await client.get(
            "/api/v1/identity/me", headers={"Authorization": "bearer " + session["access_token"]}
        )
    ).status_code == 200
    assert (
        await client.patch(
            "/api/v1/identity/me/preferences",
            headers=bearer(session),
            json={"interface_language": "nb-NO"},
        )
    ).status_code == 200
    second = await client.post(
        "/api/v1/identity/sign-in",
        json={"email": EMAIL, "password": password, "device_label": "Synthetic Web"},
    )
    assert (await client.get("/api/v1/identity/me", headers=bearer(second.json()))).json()[
        "id"
    ] == me.json()["id"]
    assert (await client.get("/api/v1/identity/me", headers=bearer(second.json()))).json()[
        "interface_language"
    ] == "nb-no"
    sessions = (await client.get("/api/v1/identity/sessions", headers=bearer(session))).json()
    assert len(sessions) == 2 and sum(s["current"] for s in sessions) == 1
    async with service.database.transaction() as db:
        account = await db.scalar(select(Account))
        assert password not in account.password_hash
        active = (await db.scalars(select(DeviceSession))).all()
        refresh = (await db.scalars(select(RefreshCredential))).all()
        assert all(session["access_token"] not in s.access_hash for s in active)
        assert all(session["refresh_token"] not in r.digest for r in refresh)


@pytest.mark.integration
async def test_enumeration_responses_and_unverified_signin(identity_runtime, password):
    service, client = identity_runtime
    first = await client.post(
        "/api/v1/identity/register", json={"email": EMAIL, "password": password}
    )
    duplicate = await client.post(
        "/api/v1/identity/register", json={"email": EMAIL, "password": secrets.token_urlsafe(24)}
    )
    assert first.status_code == duplicate.status_code == 202 and first.json() == duplicate.json()
    signin = {"email": EMAIL, "password": password, "device_label": "Synthetic"}
    unverified = await client.post("/api/v1/identity/sign-in", json=signin)
    unknown = await client.post(
        "/api/v1/identity/sign-in", json=signin | {"email": "unknown@example.com"}
    )
    assert unverified.status_code == unknown.status_code == 401
    assert unverified.json()["error"]["code"] == unknown.json()["error"]["code"]
    for path in ["/password/recovery", "/verification/request"]:
        known = await client.post("/api/v1/identity" + path, json={"email": EMAIL})
        missing = await client.post(
            "/api/v1/identity" + path, json={"email": "unknown@example.com"}
        )
        assert known.status_code == missing.status_code == 202 and known.json() == missing.json()
    # A second public registration did not replace the first user's password.
    raw = await mail_token(service)
    await service.verify_email(raw)
    assert (await client.post("/api/v1/identity/sign-in", json=signin)).status_code == 200


@pytest.mark.integration
async def test_single_use_expiring_purpose_bound_verification(identity_runtime, password):
    service, client = identity_runtime
    await service.register(EMAIL, SecretStr(password))
    raw = await mail_token(service)
    wrong = await client.post(
        "/api/v1/identity/password/reset", json={"token": raw, "password": password}
    )
    assert wrong.status_code == 400
    async with service.database.transaction() as db:
        await db.execute(update(OneTimeCredential).values(expires_at=now() - timedelta(seconds=1)))
    assert (
        await client.post("/api/v1/identity/verification/confirm", json={"token": raw})
    ).status_code == 400
    await service.email_request(EMAIL, "verify")
    new = await mail_token(service)
    assert new != raw
    assert (
        await client.post("/api/v1/identity/verification/confirm", json={"token": new})
    ).status_code == 200
    assert (
        await client.post("/api/v1/identity/verification/confirm", json={"token": new})
    ).status_code == 400


@pytest.mark.integration
async def test_refresh_rotation_replay_revokes_committed_family(identity_runtime, password):
    service, client = identity_runtime
    session = await verified(service, client, password)
    rotated = await client.post(
        "/api/v1/identity/sessions/refresh", json={"refresh_token": session["refresh_token"]}
    )
    assert rotated.status_code == 200 and rotated.json()["session_id"] == session["session_id"]
    assert (await client.get("/api/v1/identity/me", headers=bearer(session))).status_code == 401
    assert (
        await client.get("/api/v1/identity/me", headers=bearer(rotated.json()))
    ).status_code == 200
    replay = await client.post(
        "/api/v1/identity/sessions/refresh", json={"refresh_token": session["refresh_token"]}
    )
    assert replay.status_code == 401
    assert (
        await client.get("/api/v1/identity/me", headers=bearer(rotated.json()))
    ).status_code == 401
    async with service.database.transaction() as db:
        assert (await db.get(DeviceSession, UUID(session["session_id"]))).revoked_at is not None


@pytest.mark.integration
async def test_concurrent_refresh_serialized_and_expiry(identity_runtime, password):
    service, client = identity_runtime
    session = await verified(service, client, password)

    async def attempt():
        try:
            return await service.refresh(session["refresh_token"])
        except IdentityError:
            return None

    results = await asyncio.gather(attempt(), attempt())
    assert sum(result is not None for result in results) == 1
    with pytest.raises(IdentityError):
        await service.authenticate(next(result.access_token for result in results if result))
    new = await service.sign_in(EMAIL, SecretStr(password), "Synthetic")
    async with service.database.transaction() as db:
        await db.execute(
            update(RefreshCredential)
            .where(RefreshCredential.session_id == new.session_id)
            .values(expires_at=now() - timedelta(seconds=1))
        )
    with pytest.raises(IdentityError):
        await service.refresh(new.refresh_token)
    with pytest.raises(IdentityError):
        await service.authenticate(new.access_token)


@pytest.mark.integration
async def test_session_ownership_revoke_and_delete_require_strong_proof(identity_runtime, password):
    service, client = identity_runtime
    one = await verified(service, client, password)
    two = await verified(service, client, password, "other@example.com")
    denied = await client.delete(
        "/api/v1/identity/sessions/" + two["session_id"], headers=bearer(one)
    )
    absent = await client.delete("/api/v1/identity/sessions/" + str(uuid4()), headers=bearer(one))
    assert denied.status_code == absent.status_code == 404
    assert (await client.get("/api/v1/identity/me", headers=bearer(two))).status_code == 200
    assert (
        await client.request(
            "DELETE",
            "/api/v1/identity/me",
            headers=bearer(one),
            json={"reauthentication_token": token()},
        )
    ).status_code == 401
    raw = await proof(client, one, password, "delete")
    # Proof cannot authorize another account or another operation.
    assert (
        await client.request(
            "DELETE",
            "/api/v1/identity/me",
            headers=bearer(two),
            json={"reauthentication_token": raw},
        )
    ).status_code == 401
    assert (
        await client.post(
            "/api/v1/identity/password/change",
            headers=bearer(one),
            json={"reauthentication_token": raw, "password": password},
        )
    ).status_code == 401
    assert (
        await client.request(
            "DELETE",
            "/api/v1/identity/me",
            headers=bearer(one),
            json={"reauthentication_token": raw},
        )
    ).status_code == 200
    assert (await client.get("/api/v1/identity/me", headers=bearer(one))).status_code == 401
    assert (await client.get("/api/v1/identity/me", headers=bearer(two))).status_code == 200
    async with service.database.transaction() as db:
        assert await db.scalar(select(Account).where(Account.email == EMAIL)) is None
        assert await db.scalar(select(func.count()).select_from(DeviceSession)) == 1
        assert await db.scalar(select(func.count()).select_from(RefreshCredential)) == 1
        assert await db.scalar(select(func.count()).select_from(OneTimeCredential)) == 0


@pytest.mark.integration
async def test_password_recovery_changes_credentials_and_revokes_all(identity_runtime, password):
    service, client = identity_runtime
    session = await verified(service, client, password)
    await client.post("/api/v1/identity/password/recovery", json={"email": EMAIL})
    raw = await mail_token(service, purpose="reset")
    replacement = secrets.token_urlsafe(24)
    result = await client.post(
        "/api/v1/identity/password/reset", json={"token": raw, "password": replacement}
    )
    assert result.status_code == 200
    assert (await client.get("/api/v1/identity/me", headers=bearer(session))).status_code == 401
    assert (
        await client.post(
            "/api/v1/identity/sessions/refresh", json={"refresh_token": session["refresh_token"]}
        )
    ).status_code == 401
    assert (
        await client.post(
            "/api/v1/identity/password/reset", json={"token": raw, "password": replacement}
        )
    ).status_code == 400
    base = {"email": EMAIL, "device_label": "Synthetic"}
    assert (
        await client.post("/api/v1/identity/sign-in", json=base | {"password": password})
    ).status_code == 401
    assert (
        await client.post("/api/v1/identity/sign-in", json=base | {"password": replacement})
    ).status_code == 200


@pytest.mark.integration
async def test_password_change_and_revoke_all(identity_runtime, password):
    service, client = identity_runtime
    session = await verified(service, client, password)
    raw = await proof(client, session, password, "password")
    replacement = secrets.token_urlsafe(24)
    assert (
        await client.post(
            "/api/v1/identity/password/change",
            headers=bearer(session),
            json={"reauthentication_token": raw, "password": replacement},
        )
    ).status_code == 200
    assert (await client.get("/api/v1/identity/me", headers=bearer(session))).status_code == 401
    result = await client.post(
        "/api/v1/identity/sign-in",
        json={"email": EMAIL, "password": replacement, "device_label": "Synthetic"},
    )
    assert (
        await client.post(
            "/api/v1/identity/sessions/revoke-all", headers=bearer(result.json()), json={}
        )
    ).status_code == 200
    assert (
        await client.get("/api/v1/identity/me", headers=bearer(result.json()))
    ).status_code == 401


@pytest.mark.integration
async def test_rate_limits_are_persistent_and_do_not_log_sensitive_values(
    identity_runtime, password
):
    service, client = identity_runtime
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.addHandler(handler)
    try:
        for _ in range(6):
            result = await client.post(
                "/api/v1/identity/sign-in",
                json={"email": EMAIL, "password": password, "device_label": "Synthetic"},
            )
            assert result.status_code == 401
        result = await client.post(
            "/api/v1/identity/sign-in",
            json={"email": EMAIL, "password": password, "device_label": "Synthetic"},
        )
        assert result.status_code == 429 and result.headers["retry-after"] == "600"
        assert EMAIL not in stream.getvalue() and password not in stream.getvalue()
        async with service.database.transaction() as db:
            counts = (await db.scalars(select(RateBucket.count))).all()
            assert 7 in counts
    finally:
        root.removeHandler(handler)


@pytest.mark.integration
@pytest.mark.parametrize(
    "case",
    [
        "origin",
        "cookie",
        "header",
        "content_type",
        "query",
        "duplicates",
        "deep",
        "oversize",
        "role",
    ],
)
async def test_http_security_boundaries(identity_runtime, password, case):
    _, client = identity_runtime
    headers = {}
    content = json.dumps({"email": EMAIL, "password": password})
    path = "/api/v1/identity/register"
    expected = 400
    headers["Content-Type"] = "application/json"
    if case == "origin":
        headers["Origin"] = "https://evil.example.invalid"
        expected = 403
    elif case == "cookie":
        headers["Cookie"] = "session=untrusted"
    elif case == "header":
        headers["X-NorskAllstars-Client"] = "invalid"
    elif case == "content_type":
        headers["Content-Type"] = "text/plain"
        expected = 415
    elif case == "query":
        path += "?token=untrusted"
    elif case == "duplicates":
        content = '{"email":"synthetic@example.com","email":"other@example.com"}'
    elif case == "deep":
        content = '{"value":' + "[" * 20 + "0" + "]" * 20 + "}"
    elif case == "oversize":
        content = "x" * 32769
        expected = 413
    elif case == "role":
        content = json.dumps({"email": EMAIL, "password": password, "role": "admin"})
        expected = 422
    result = await client.post(path, content=content, headers=headers)
    assert result.status_code == expected
    assert password not in result.text and "Traceback" not in result.text


@pytest.mark.integration
async def test_google_signup_nonce_single_use_and_subject_stability(
    identity_runtime, google_signer
):
    service, client = identity_runtime
    data = await google_proof(service, client, google_signer)
    response = await client.post(
        "/api/v1/identity/google/sign-in", json=data | {"device_label": "Synthetic"}
    )
    assert response.status_code == 200
    first = (await client.get("/api/v1/identity/me", headers=bearer(response.json()))).json()
    assert first["sign_in_methods"] == ["google"]
    assert (
        await client.post(
            "/api/v1/identity/google/sign-in", json=data | {"device_label": "Synthetic"}
        )
    ).status_code == 401
    # A mutable provider email never moves an existing subject to a different account.
    changed = await google_proof(service, client, google_signer, email="changed@example.com")
    response = await client.post(
        "/api/v1/identity/google/sign-in", json=changed | {"device_label": "Synthetic"}
    )
    assert response.status_code == 200
    assert (await client.get("/api/v1/identity/me", headers=bearer(response.json()))).json()[
        "id"
    ] == first["id"]
    assert (await client.get("/api/v1/identity/me", headers=bearer(response.json()))).json()[
        "email"
    ] == EMAIL


@pytest.mark.integration
async def test_google_third_party_email_requires_platform_verification(
    identity_runtime, google_signer
):
    service, client = identity_runtime
    data = await google_proof(service, client, google_signer, hd=None)
    response = await client.post(
        "/api/v1/identity/google/sign-in", json=data | {"device_label": "Synthetic"}
    )
    assert response.status_code == 200 and response.json() == {"status": "verification_required"}
    raw = await mail_token(service)
    assert (
        await client.post("/api/v1/identity/verification/confirm", json={"token": raw})
    ).status_code == 200
    second = await google_proof(service, client, google_signer, hd=None)
    result = await client.post(
        "/api/v1/identity/google/sign-in", json=second | {"device_label": "Synthetic"}
    )
    assert result.status_code == 200 and "access_token" in result.json()


@pytest.mark.integration
async def test_google_never_auto_links_and_requires_own_reauth(
    identity_runtime, google_signer, password
):
    service, client = identity_runtime
    session = await verified(service, client, password)
    data = await google_proof(service, client, google_signer)
    assert (
        await client.post(
            "/api/v1/identity/google/sign-in", json=data | {"device_label": "Synthetic"}
        )
    ).status_code == 401
    assert (
        await client.post(
            "/api/v1/identity/me/google",
            headers=bearer(session),
            json=data | {"reauthentication_token": token()},
        )
    ).status_code == 401
    raw = await proof(client, session, password, "link")
    assert (
        await client.post(
            "/api/v1/identity/me/google",
            headers=bearer(session),
            json=data | {"reauthentication_token": raw},
        )
    ).status_code == 200
    assert (await client.get("/api/v1/identity/me", headers=bearer(session))).json()[
        "sign_in_methods"
    ] == ["password", "google"]
    next_proof = await google_proof(service, client, google_signer)
    response = await client.post(
        "/api/v1/identity/reauthenticate",
        headers=bearer(session),
        json={"purpose": "delete", "google": next_proof},
    )
    assert response.status_code == 200
    assert (
        await client.request(
            "DELETE",
            "/api/v1/identity/me",
            headers=bearer(session),
            json={"reauthentication_token": response.json()["reauthentication_token"]},
        )
    ).status_code == 200
    async with service.database.transaction() as db:
        assert await db.scalar(select(func.count()).select_from(GoogleIdentity)) == 0


@pytest.mark.parametrize(
    "change",
    [
        {"iss": "https://evil.example.invalid"},
        {"aud": "untrusted"},
        {"aud": [CLIENT_ID, "other"]},
        {"azp": "other"},
        {"exp": 0},
        {"iat": 9999999999},
        {"email_verified": False},
        {"sub": ""},
        {"nonce": "short"},
    ],
)
async def test_google_cryptographic_claim_validation(google_signer, change):
    sign, jwk = google_signer
    verifier = GoogleVerifier()
    verifier.keys, verifier.until = {"synthetic": PyJWK.from_dict(jwk)}, time.monotonic() + 300
    with pytest.raises(GoogleVerificationError):
        await verifier.verify(sign(token(), **change), CLIENT_ID)


async def test_google_wrong_signature_algorithm_and_missing_claims(google_signer):
    sign, jwk = google_signer
    verifier = GoogleVerifier()
    verifier.keys, verifier.until = {"synthetic": PyJWK.from_dict(jwk)}, time.monotonic() + 300
    bad = jwt.encode(
        {"aud": CLIENT_ID},
        secrets.token_urlsafe(32),
        algorithm="HS256",
        headers={"kid": "synthetic"},
    )
    with pytest.raises(GoogleVerificationError):
        await verifier.verify(bad, CLIENT_ID)
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    payload = jwt.decode(sign(token()), options={"verify_signature": False})
    bad = jwt.encode(payload, other_key, algorithm="RS256", headers={"kid": "synthetic"})
    with pytest.raises(GoogleVerificationError):
        await verifier.verify(bad, CLIENT_ID)
    with pytest.raises(GoogleVerificationError):
        await verifier.verify("malformed", CLIENT_ID)


@pytest.mark.integration
async def test_google_nonce_mismatch_does_not_authenticate(identity_runtime, google_signer):
    service, client = identity_runtime
    data = await google_proof(service, client, google_signer, nonce=token())
    response = await client.post(
        "/api/v1/identity/google/sign-in", json=data | {"device_label": "Synthetic"}
    )
    assert response.status_code == 401
    assert (
        await client.post("/api/v1/identity/google/challenge", json={"client_id": "untrusted"})
    ).status_code == 400


@pytest.mark.integration
async def test_outbox_delivery_retry_and_retention(identity_runtime, password, tmp_path):
    service, _ = identity_runtime
    await service.register(EMAIL, SecretStr(password))
    raw = await mail_token(service)
    storage = LocalObjectStorage(tmp_path.resolve(), 65536)
    worker = MailWorker(service, LocalMailTransport(service, storage))
    assert await worker.drain() == {"delivered": 1, "failed": 0}
    assert await worker.drain() == {"delivered": 0, "failed": 0}
    message = (
        BytesParser(policy=policy.default)
        .parsebytes(next(tmp_path.rglob("*.eml")).read_bytes())
        .get_content()
    )
    assert "#token=" + raw in message and "?token=" not in message
    assert next(tmp_path.rglob("*.eml")).stat().st_mode & 0o777 == 0o600
    async with service.database.transaction() as db:
        await db.execute(update(MailOutbox).values(expires_at=now() - timedelta(seconds=1)))
        await db.execute(update(OneTimeCredential).values(expires_at=now() - timedelta(seconds=1)))
    results = await cleanup(service)
    assert results["mail"] == results["credentials"] == 1
    assert await worker.drain() == {"delivered": 0, "failed": 0}


@pytest.mark.integration
async def test_outbox_failure_and_concurrent_lease(identity_runtime, password):
    service, _ = identity_runtime
    await service.register(EMAIL, SecretStr(password))

    class Failing:
        async def send(self, message, message_id):
            raise RuntimeError("sensitive-smtp-value")

    worker = MailWorker(service, Failing())
    assert await worker.drain() == {"delivered": 0, "failed": 1}
    async with service.database.transaction() as db:
        item = await db.scalar(select(MailOutbox))
        assert item.attempts == 1 and item.lease_until is None and item.delivered_at is None
        item.next_attempt_at = now() - timedelta(seconds=1)

    class Delivered:
        def __init__(self):
            self.count = 0

        async def send(self, message, message_id):
            self.count += 1
            await asyncio.sleep(0.02)

    transport = Delivered()
    workers = [MailWorker(service, transport), MailWorker(service, transport)]
    results = await asyncio.gather(*(w.drain() for w in workers))
    assert sum(r["delivered"] for r in results) == transport.count == 1


@pytest.mark.integration
async def test_registration_mail_failure_rolls_back_all_identity_state(
    identity_runtime, password, monkeypatch
):
    service, _ = identity_runtime

    async def failed(*args):
        raise RuntimeError("synthetic-transaction-failure")

    monkeypatch.setattr(service, "issue_mail", failed)
    with pytest.raises(RuntimeError):
        await service.register(EMAIL, SecretStr(password))
    async with service.database.transaction() as db:
        for model in [Account, MailOutbox, OneTimeCredential]:
            assert await db.scalar(select(func.count()).select_from(model)) == 0


@pytest.mark.integration
async def test_no_http_course_import_publication_or_admin_authority(identity_runtime, password):
    service, client = identity_runtime
    session = await verified(service, client, password)
    paths = client._transport.app.openapi()["paths"]
    assert all(path.startswith("/api/v1/identity/") for path in paths)
    for path in ["/v1/course-packages/import", "/v1/releases/publish", "/admin"]:
        assert (
            await client.post(
                path, json={"actor": "admin", "approval": "owner"}, headers=bearer(session)
            )
        ).status_code == 404


async def test_password_work_remains_bounded_after_request_cancellation():
    from threading import Event, Lock

    from norskallstars_backend.identity.security import PasswordCapacityError, password_job

    release, finished = Event(), Event()
    lock = Lock()
    counters = {"finished": 0, "active": 0, "maximum": 0}

    def blocking():
        with lock:
            counters["active"] += 1
            counters["maximum"] = max(counters["maximum"], counters["active"])
        release.wait(5)
        with lock:
            counters["active"] -= 1
            counters["finished"] += 1
            if counters["finished"] == 20:
                finished.set()
        return "done"

    tasks = [asyncio.create_task(password_job(blocking)) for _ in range(20)]
    try:
        # All coroutines submit synchronously before their first await.
        await asyncio.sleep(0)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        with pytest.raises(PasswordCapacityError):
            await password_job(lambda: "overflow")
    finally:
        release.set()
        assert await asyncio.to_thread(finished.wait, 5)
    assert counters["maximum"] <= 2
    assert await password_job(lambda: "available") == "available"


@pytest.mark.integration
async def test_session_device_bound_access_expiry_and_rotation_bound(identity_runtime, password):
    service, client = identity_runtime
    first = await verified(service, client, password)
    sessions = [
        await service.sign_in(EMAIL, SecretStr(password), f"Synthetic {n}") for n in range(10)
    ]
    with pytest.raises(IdentityError):
        await service.authenticate(first["access_token"])
    principal = await service.authenticate(sessions[-1].access_token)
    assert len(await service.sessions(principal)) == 10
    async with service.database.transaction() as db:
        await db.execute(
            update(DeviceSession)
            .where(DeviceSession.id == sessions[-1].session_id)
            .values(access_expires_at=now() - timedelta(seconds=1))
        )
    with pytest.raises(IdentityError):
        await service.authenticate(sessions[-1].access_token)
    # Expired access may refresh when the independent refresh credential is still valid.
    rotated = await service.refresh(sessions[-1].refresh_token)
    async with service.database.transaction() as db:
        for _ in range(254):
            db.add(
                RefreshCredential(
                    digest=service.digest("refresh", token()),
                    session_id=rotated.session_id,
                    expires_at=now() + timedelta(hours=1),
                    used_at=now(),
                )
            )
    with pytest.raises(IdentityError):
        await service.refresh(rotated.refresh_token)
    with pytest.raises(IdentityError):
        await service.authenticate(rotated.access_token)


@pytest.mark.integration
async def test_single_session_logout_and_reauth_session_binding(identity_runtime, password):
    service, client = identity_runtime
    one = await verified(service, client, password)
    two = await service.sign_in(EMAIL, SecretStr(password), "Synthetic second device")
    raw = await proof(client, one, password, "delete")
    second = await service.authenticate(two.access_token)
    with pytest.raises(IdentityError):
        await service.delete_account(second, raw)
    assert (
        await client.delete("/api/v1/identity/sessions/" + one["session_id"], headers=bearer(one))
    ).status_code == 200
    with pytest.raises(IdentityError):
        await service.authenticate(one["access_token"])
    assert (await service.me(second))["email"] == EMAIL


@pytest.mark.integration
async def test_account_deletion_rollback_preserves_proof_and_sessions(
    identity_runtime, password, monkeypatch
):
    from contextlib import asynccontextmanager

    service, client = identity_runtime
    session = await verified(service, client, password)
    raw = await proof(client, session, password, "delete")
    principal = await service.authenticate(session["access_token"])
    original = service.database.transaction

    @asynccontextmanager
    async def fail_before_commit():
        async with original() as db:
            yield db
            raise RuntimeError("synthetic-commit-failure")

    with monkeypatch.context() as patch:
        patch.setattr(service.database, "transaction", fail_before_commit)
        with pytest.raises(RuntimeError):
            await service.delete_account(principal, raw)
    assert (await service.me(principal))["email"] == EMAIL
    await service.delete_account(principal, raw)
    with pytest.raises(IdentityError):
        await service.authenticate(session["access_token"])


@pytest.mark.integration
async def test_concurrent_registration_creates_one_account_and_one_verification(
    identity_runtime, password
):
    service, _ = identity_runtime
    await asyncio.gather(*(service.register(EMAIL, SecretStr(password)) for _ in range(2)))
    async with service.database.transaction() as db:
        for model in [Account, MailOutbox, OneTimeCredential]:
            assert await db.scalar(select(func.count()).select_from(model)) == 1


@pytest.mark.integration
async def test_reauth_wrong_password_and_expired_confirmation_fail_closed(
    identity_runtime, password
):
    service, client = identity_runtime
    session = await verified(service, client, password)
    assert (
        await client.post(
            "/api/v1/identity/reauthenticate",
            headers=bearer(session),
            json={"purpose": "delete", "password": secrets.token_urlsafe(24)},
        )
    ).status_code == 401
    assert (
        await client.post(
            "/api/v1/identity/reauthenticate", headers=bearer(session), json={"purpose": "delete"}
        )
    ).status_code == 400
    raw = await proof(client, session, password, "delete")
    async with service.database.transaction() as db:
        await db.execute(update(OneTimeCredential).values(expires_at=now() - timedelta(seconds=1)))
    assert (
        await client.request(
            "DELETE",
            "/api/v1/identity/me",
            headers=bearer(session),
            json={"reauthentication_token": raw},
        )
    ).status_code == 401
    assert (await client.get("/api/v1/identity/me", headers=bearer(session))).status_code == 200


@pytest.mark.integration
async def test_google_identity_cannot_be_moved_between_accounts(
    identity_runtime, google_signer, password
):
    service, client = identity_runtime
    data = await google_proof(service, client, google_signer)
    google_session = (
        await client.post(
            "/api/v1/identity/google/sign-in", json=data | {"device_label": "Synthetic"}
        )
    ).json()
    local = await verified(service, client, password, "other@example.com")
    raw = await proof(client, local, password, "link")
    data = await google_proof(service, client, google_signer)
    assert (
        await client.post(
            "/api/v1/identity/me/google",
            headers=bearer(local),
            json=data | {"reauthentication_token": raw},
        )
    ).status_code == 409
    assert (await client.get("/api/v1/identity/me", headers=bearer(google_session))).json()[
        "email"
    ] == EMAIL
    assert (await client.get("/api/v1/identity/me", headers=bearer(local))).json()[
        "sign_in_methods"
    ] == ["password"]


@pytest.mark.integration
async def test_google_only_account_reauth_and_password_recovery(
    identity_runtime, google_signer, password
):
    service, client = identity_runtime
    data = await google_proof(service, client, google_signer)
    session = (
        await client.post(
            "/api/v1/identity/google/sign-in", json=data | {"device_label": "Synthetic"}
        )
    ).json()
    data = await google_proof(service, client, google_signer, sub="unrelated-subject")
    assert (
        await client.post(
            "/api/v1/identity/reauthenticate",
            headers=bearer(session),
            json={"purpose": "delete", "google": data},
        )
    ).status_code == 401
    await client.post("/api/v1/identity/password/recovery", json={"email": EMAIL})
    raw = await mail_token(service, purpose="reset")
    assert (
        await client.post(
            "/api/v1/identity/password/reset", json={"token": raw, "password": password}
        )
    ).status_code == 200
    response = await client.post(
        "/api/v1/identity/sign-in",
        json={"email": EMAIL, "password": password, "device_label": "Synthetic"},
    )
    assert response.status_code == 200
    assert (await client.get("/api/v1/identity/me", headers=bearer(response.json()))).json()[
        "sign_in_methods"
    ] == ["password", "google"]


@pytest.mark.parametrize(
    "change",
    [
        {"iat": True},
        {"exp": True},
        {"iat": int(time.time()) - 1000},
        {"exp": int(time.time()) + 10000},
        {"email": "not-an-address"},
        {"email_verified": "true"},
    ],
)
async def test_google_strict_fresh_claims(google_signer, change):
    sign, jwk = google_signer
    verifier = GoogleVerifier()
    verifier.keys, verifier.until = {"synthetic": PyJWK.from_dict(jwk)}, time.monotonic() + 300
    with pytest.raises(GoogleVerificationError):
        await verifier.verify(sign(token(), **change), CLIENT_ID)


async def test_google_key_fetch_cache_cooldown_and_untrusted_jku(google_signer, monkeypatch):
    sign, jwk = google_signer
    verifier = GoogleVerifier()
    calls = []

    def fetch():
        calls.append("constant-key-source")
        return {"synthetic": PyJWK.from_dict(jwk)}

    monkeypatch.setattr(verifier, "fetch_keys", fetch)
    assert (await verifier.verify(sign(token()), CLIENT_ID)).subject == "synthetic-google-subject"
    assert (await verifier.verify(sign(token()), CLIENT_ID)).email == EMAIL
    assert len(calls) == 1
    # Unknown kid does not trigger an unbounded external fetch loop.
    missing_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    missing = jwt.encode(
        {"aud": CLIENT_ID},
        missing_key,
        algorithm="RS256",
        headers={"kid": "missing", "jku": "https://evil.example.invalid/keys"},
    )
    for _ in range(3):
        with pytest.raises(GoogleVerificationError):
            await verifier.verify(missing, CLIENT_ID)
    assert len(calls) == 1


@pytest.mark.parametrize("case", ["large", "non_json", "many", "duplicate", "small_key"])
def test_google_key_document_resource_limits(google_signer, monkeypatch, case):
    _, jwk = google_signer
    payload = {"keys": [jwk]}
    if case == "many":
        payload["keys"] = [jwk] * 11
    elif case == "duplicate":
        payload["keys"] = [jwk, jwk]
    elif case == "small_key":
        small = rsa.generate_private_key(public_exponent=65537, key_size=1024)  # noqa: S505 -- invalid key must be rejected
        item = jwt.algorithms.RSAAlgorithm.to_jwk(small.public_key(), as_dict=True)
        item.update(kid="small", use="sig")
        payload = {"keys": [item]}
    raw = json.dumps(payload).encode()
    if case == "large":
        raw = b"x" * 65537
    elif case == "non_json":
        raw = b"not-json"

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, limit):
            assert limit == 65537
            return raw

    class Opener:
        def open(self, url, timeout):
            assert url == "https://www.googleapis.com/oauth2/v3/certs" and timeout == 3
            return Response()

    monkeypatch.setattr("urllib.request.build_opener", lambda *args: Opener())
    with pytest.raises((GoogleVerificationError, json.JSONDecodeError)):
        GoogleVerifier().fetch_keys()


@pytest.mark.integration
async def test_smtp_worker_requires_verified_tls_and_redacts_errors(
    identity_runtime, password, monkeypatch
):
    import ssl

    from norskallstars_backend.identity.mail import SMTPTransport

    service, _ = identity_runtime
    service.settings = Settings(
        **(
            service.settings.model_dump()
            | {
                "mail_transport": "smtp",
                "smtp_host": "smtp.example.invalid",
                "smtp_username": "synthetic",
                "smtp_password": secrets.token_urlsafe(24),
                "mail_sender": "noreply@example.com",
            }
        )
    )
    sent = []

    class FakeSMTP:
        def __init__(self, host, port, timeout, context):
            assert host == "smtp.example.invalid" and port == 465 and timeout == 5
            assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def login(self, username, password):
            assert (
                username == "synthetic"
                and password == service.settings.smtp_password.get_secret_value()
            )

        def send_message(self, message):
            sent.append(message)

    monkeypatch.setattr("smtplib.SMTP_SSL", FakeSMTP)
    await service.register(EMAIL, SecretStr(password))
    assert await MailWorker(service, SMTPTransport(service)).drain() == {
        "delivered": 1,
        "failed": 0,
    }
    assert len(sent) == 1 and sent[0]["To"] == EMAIL


@pytest.mark.integration
async def test_identity_cleanup_preserves_account_and_course_boundary(identity_runtime, password):
    service, client = identity_runtime
    session = await verified(service, client, password)
    await service.email_request(EMAIL, "reset")
    async with service.database.transaction() as db:
        await db.execute(update(DeviceSession).values(expires_at=now() - timedelta(seconds=1)))
        await db.execute(update(OneTimeCredential).values(expires_at=now() - timedelta(seconds=1)))
        await db.execute(update(MailOutbox).values(expires_at=now() - timedelta(seconds=1)))
        await db.execute(update(RateBucket).values(expires_at=now() - timedelta(seconds=1)))
    counts = await cleanup(service)
    assert counts["sessions"] == counts["mail"] == counts["credentials"] == 1
    assert counts["rate_buckets"] > 0
    async with service.database.transaction() as db:
        assert await db.scalar(select(func.count()).select_from(Account)) == 1
        assert await db.scalar(select(func.count()).select_from(RefreshCredential)) == 0
    with pytest.raises(IdentityError):
        await service.authenticate(session["access_token"])


def test_public_openapi_matches_actual_validated_routes():
    from pathlib import Path

    from norskallstars_backend.identity.openapi import schema_bytes

    generated = schema_bytes()
    committed = Path(__file__).resolve().parents[3] / "contracts/api/identity-v1.openapi.json"
    assert committed.read_bytes() == generated
    document = json.loads(generated)
    assert len(document["paths"]) == 17
    assert document["paths"]["/api/v1/identity/me"]["get"]["security"] == [{"HTTPBearer": []}]
    assert "security" not in document["paths"]["/api/v1/identity/register"]["post"]
    properties = document["components"]["schemas"]["AccountView"]["properties"]
    assert "password_hash" not in properties and "google_subject" not in properties
    assert document["components"]["schemas"]["Registration"]["additionalProperties"] is False
    assert document["paths"]["/api/v1/identity/register"]["post"]["responses"]["422"]["content"][
        "application/json"
    ]["schema"] == {"$ref": "#/components/schemas/ErrorResponse"}
    assert "HTTPValidationError" not in document["components"]["schemas"]


@pytest.mark.integration
async def test_duplicate_security_headers_are_rejected(identity_runtime):
    _, client = identity_runtime
    response = await client.get(
        "/api/v1/identity/me",
        headers=[("Authorization", "Bearer " + token()), ("Authorization", "Bearer " + token())],
    )
    assert response.status_code == 400


async def test_google_gmail_email_authority(google_signer):
    sign, jwk = google_signer
    verifier = GoogleVerifier()
    verifier.keys, verifier.until = {"synthetic": PyJWK.from_dict(jwk)}, time.monotonic() + 300
    result = await verifier.verify(
        sign(token(), email="public-synthetic-fixture" + "@gmail.com", hd=None), CLIENT_ID
    )
    assert result.authoritative_email


def test_deployed_identity_rejects_cleartext_and_raw_forwarding(settings, tmp_path):
    from fastapi.testclient import TestClient

    ca = tmp_path / "test-ca.crt"
    ca.write_text("Synthetic configuration placeholder")
    production = Settings(
        **(
            settings.model_dump()
            | {
                "env": "production",
                "database_sslmode": "verify-full",
                "database_sslrootcert": ca,
                "allowed_hosts": ["api.example.invalid"],
                "identity_public_origin": "https://app.example.invalid",
                "google_client_ids": [CLIENT_ID],
                "mail_transport": "smtp",
                "smtp_host": "smtp.example.invalid",
                "smtp_username": "synthetic",
                "smtp_password": secrets.token_urlsafe(24),
                "mail_sender": "noreply@example.com",
            }
        )
    )
    with TestClient(create_app(production), base_url="http://api.example.invalid") as client:
        for headers in [{}, {"X-Forwarded-Proto": "https", "X-Forwarded-For": "127.0.0.1"}]:
            response = client.get("/api/v1/identity/me", headers=headers)
            assert response.status_code == 400
            assert response.json()["error"]["code"] == "request_rejected"
