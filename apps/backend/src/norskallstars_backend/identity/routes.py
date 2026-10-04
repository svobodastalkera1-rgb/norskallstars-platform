"""Versioned identity API. Audit/operator assertions never grant HTTP privileges."""

import json
from collections.abc import Callable, Coroutine
from dataclasses import asdict
from typing import Annotated, Any, Literal, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.responses import Response

from norskallstars_backend.config import Environment
from norskallstars_backend.identity import security as inputs
from norskallstars_backend.identity.dto import (
    Accepted,
    AccountView,
    ErrorResponse,
    GoogleChallengeView,
    ReauthenticationView,
    SessionView,
    VerificationRequired,
)
from norskallstars_backend.identity.service import Identity, IdentityError, Principal, SessionTokens


def identity(request: Request) -> Identity:
    return cast(Identity, request.app.state.identity)


def safe_response() -> dict[str, str]:
    return {"status": "accepted"}


async def boundary(request: Request) -> None:
    service = identity(request)
    if (
        service.settings.env in (Environment.STAGING, Environment.PRODUCTION)
        and request.url.scheme != "https"
    ):
        raise IdentityError(400, "request_rejected")
    if any(
        len(request.headers.getlist(name)) > 1
        for name in ("authorization", "origin", "cookie", "content-type", "x-norskallstars-client")
    ):
        raise IdentityError(400, "request_rejected")
    origin = request.headers.get("origin")
    allowed = [service.settings.identity_public_origin, *service.settings.cors_origins]
    if origin is not None and origin not in allowed:
        raise IdentityError(403, "request_rejected")
    # Explicit bearer transport; prevent accidental future cookie authentication/CSRF.
    if request.headers.get("cookie"):
        raise IdentityError(400, "request_rejected")
    if request.method in ("POST", "PATCH", "DELETE"):
        if request.headers.get("x-norskallstars-client") not in ("web", "android", "operator"):
            raise IdentityError(400, "request_rejected")
        if request.method != "DELETE" or request.url.path.endswith("/me"):
            if request.headers.get("content-type", "").split(";", 1)[0] != "application/json":
                raise IdentityError(415, "request_rejected")
    if request.url.query:
        # Tokens/passwords do not belong in URLs or access logs.
        raise IdentityError(400, "request_rejected")
    remote = request.client.host if request.client else "unknown"
    await service.rate_limit("http", remote)


bearer_scheme = HTTPBearer(auto_error=False)


async def principal(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> Principal:
    if (
        credentials is None
        or credentials.scheme.casefold() != "bearer"
        or not 32 <= len(credentials.credentials) <= 512
    ):
        raise IdentityError()
    return await identity(request).authenticate(credentials.credentials)


PrincipalDependency = Annotated[Principal, Depends(principal)]
ClientHeader = Annotated[
    Literal["web", "android", "operator"], Header(alias="X-NorskAllstars-Client")
]


def strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def invalid_constant(value: str) -> None:
    raise ValueError("Non-finite JSON value")


class IdentityRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original = super().get_route_handler()

        async def handler(request: Request) -> Response:
            await boundary(request)
            raw = await request.body()
            if raw:
                try:
                    document = json.loads(
                        raw, object_pairs_hook=strict_pairs, parse_constant=invalid_constant
                    )
                    if not isinstance(document, dict):
                        raise ValueError("Object required")
                    queue = [(document, 0)]
                    nodes = 0
                    while queue:
                        item, depth = queue.pop()
                        nodes += 1
                        if depth > 8 or nodes > 256:
                            raise ValueError("JSON resource limit")
                        if isinstance(item, dict):
                            queue.extend((value, depth + 1) for value in item.values())
                        elif isinstance(item, list):
                            queue.extend((value, depth + 1) for value in item)
                except (ValueError, RecursionError):
                    raise IdentityError(400, "invalid_request") from None
            return await original(request)

        return handler


router = APIRouter(
    route_class=IdentityRoute,
    prefix="/api/v1/identity",
    tags=["identity"],
    responses={
        status: {"model": ErrorResponse}
        for status in (400, 401, 403, 404, 405, 409, 413, 415, 422, 429, 500, 503, 504)
    },
)


async def limited(request: Request, operation: str, email: str = "") -> Identity:
    service = identity(request)
    remote = request.client.host if request.client else "unknown"
    await service.rate_limit(operation, remote, email)
    return service


@router.post("/register", status_code=202, response_model=Accepted)
async def register(
    client: ClientHeader, data: inputs.Registration, request: Request
) -> dict[str, str]:
    service = await limited(request, "register", data.email)
    await service.register(data.email, data.password)
    return safe_response()


@router.post("/verification/request", status_code=202, response_model=Accepted)
async def verification_request(
    client: ClientHeader, data: inputs.EmailRequest, request: Request
) -> dict[str, str]:
    service = await limited(request, "verify_request", data.email)
    await service.email_request(data.email, "verify")
    return safe_response()


@router.post("/verification/confirm", response_model=Accepted)
async def verification_confirm(
    client: ClientHeader, data: inputs.TokenRequest, request: Request
) -> dict[str, str]:
    service = await limited(request, "verify_confirm")
    await service.verify_email(data.token.get_secret_value())
    return safe_response()


@router.post("/password/recovery", status_code=202, response_model=Accepted)
async def recovery(
    client: ClientHeader, data: inputs.EmailRequest, request: Request
) -> dict[str, str]:
    service = await limited(request, "recovery", data.email)
    await service.email_request(data.email, "reset")
    return safe_response()


@router.post("/password/reset", response_model=Accepted)
async def reset(
    client: ClientHeader, data: inputs.PasswordReset, request: Request
) -> dict[str, str]:
    service = await limited(request, "reset")
    await service.reset_password(data.token.get_secret_value(), data.password)
    return safe_response()


@router.post("/sign-in", response_model=SessionTokens)
async def sign_in(client: ClientHeader, data: inputs.SignIn, request: Request) -> dict[str, object]:
    service = await limited(request, "sign_in", data.email)
    return asdict(await service.sign_in(data.email, data.password, data.device_label))


@router.post("/sessions/refresh", response_model=SessionTokens)
async def refresh(
    client: ClientHeader, data: inputs.Refresh, request: Request
) -> dict[str, object]:
    service = await limited(request, "refresh")
    return asdict(await service.refresh(data.refresh_token.get_secret_value()))


@router.get("/me", response_model=AccountView)
async def me(request: Request, actor: PrincipalDependency) -> dict[str, object]:
    return await identity(request).me(actor)


@router.patch("/me/preferences", response_model=Accepted)
async def preferences(
    client: ClientHeader, data: inputs.Preferences, request: Request, actor: PrincipalDependency
) -> dict[str, str]:
    service = await limited(request, "preferences")
    await service.preferences(actor, data.interface_language)
    return safe_response()


@router.get("/sessions", response_model=list[SessionView])
async def sessions(request: Request, actor: PrincipalDependency) -> list[dict[str, object]]:
    return await identity(request).sessions(actor)


@router.delete("/sessions/{session_id}", response_model=Accepted)
async def revoke_session(
    client: ClientHeader, session_id: UUID, request: Request, actor: PrincipalDependency
) -> dict[str, str]:
    service = await limited(request, "revoke")
    await service.revoke(actor, session_id)
    return safe_response()


@router.post("/sessions/revoke-all", response_model=Accepted)
async def revoke_all(
    client: ClientHeader, request: Request, actor: PrincipalDependency
) -> dict[str, str]:
    service = await limited(request, "revoke_all")
    await service.revoke(actor, None)
    return safe_response()


@router.post("/google/challenge", response_model=GoogleChallengeView)
async def challenge(
    client: ClientHeader, data: inputs.GoogleChallenge, request: Request
) -> dict[str, str]:
    service = await limited(request, "google_challenge")
    return await service.challenge(data.client_id)


@router.post("/google/sign-in", response_model=SessionTokens | VerificationRequired)
async def google_sign_in(
    client: ClientHeader, data: inputs.GoogleSignIn, request: Request
) -> dict[str, object]:
    service = await limited(request, "google_sign_in")
    session = await service.google_sign_in(
        data.challenge.get_secret_value(), data.id_token.get_secret_value(), data.device_label
    )
    return asdict(session) if session else {"status": "verification_required"}


@router.post("/reauthenticate", response_model=ReauthenticationView)
async def reauthenticate(
    client: ClientHeader,
    data: inputs.Reauthentication,
    request: Request,
    actor: PrincipalDependency,
) -> dict[str, object]:
    service = await limited(request, "reauthenticate")
    google = (
        (data.google.challenge.get_secret_value(), data.google.id_token.get_secret_value())
        if data.google
        else None
    )
    raw = await service.reauthenticate(actor, data.purpose, data.password, google)
    return {"reauthentication_token": raw, "expires_in": 300}


@router.post("/password/change", response_model=Accepted)
async def change_password(
    client: ClientHeader, data: inputs.PasswordChange, request: Request, actor: PrincipalDependency
) -> dict[str, str]:
    service = await limited(request, "password_change")
    await service.change_password(
        actor, data.reauthentication_token.get_secret_value(), data.password
    )
    return safe_response()


@router.post("/me/google", response_model=Accepted)
async def link_google(
    client: ClientHeader, data: inputs.GoogleLink, request: Request, actor: PrincipalDependency
) -> dict[str, str]:
    service = await limited(request, "google_link")
    await service.link_google(
        actor,
        data.reauthentication_token.get_secret_value(),
        data.challenge.get_secret_value(),
        data.id_token.get_secret_value(),
    )
    return safe_response()


@router.delete("/me", response_model=Accepted)
async def delete_account(
    client: ClientHeader,
    data: inputs.AuthorizedChange,
    request: Request,
    actor: PrincipalDependency,
) -> dict[str, str]:
    service = await limited(request, "delete")
    await service.delete_account(actor, data.reauthentication_token.get_secret_value())
    return safe_response()


async def identity_error(request: Request, exc: Exception) -> JSONResponse:
    from norskallstars_backend.logging import request_id

    if not isinstance(exc, IdentityError):
        raise TypeError("Invalid identity handler invocation")
    headers = {"Cache-Control": "no-store", "Pragma": "no-cache"}
    if exc.status == 429:
        headers["Retry-After"] = "600"
    if exc.status == 401:
        headers["WWW-Authenticate"] = "Bearer"
    return JSONResponse(
        {"error": {"code": exc.code, "request_id": request_id.get()}},
        status_code=exc.status,
        headers=headers,
    )
