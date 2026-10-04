"""Pure ASGI request bounds, correlation, safe error response and safe event logging."""

import asyncio
import logging
import time
import uuid

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from norskallstars_backend.config import Environment, Settings
from norskallstars_backend.logging import exception_fields, request_id

logger = logging.getLogger("norskallstars.http")


class BodyTooLarge(Exception):
    pass


class RequestBoundary:
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        self.app, self.settings = app, settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        candidates = [value for key, value in scope["headers"] if key.lower() == b"x-request-id"]
        try:
            identifier = (
                str(uuid.UUID(candidates[0].decode("ascii")))
                if len(candidates) == 1
                else str(uuid.uuid4())
            )
        except (ValueError, UnicodeError):
            identifier = str(uuid.uuid4())
        token = request_id.set(identifier)
        started, status, sent, size = time.monotonic(), 500, False, 0

        async def bounded_receive() -> Message:
            nonlocal size
            message = await receive()
            size += len(message.get("body", b""))
            if size > self.settings.max_request_bytes:
                raise BodyTooLarge
            return message

        async def safe_send(message: Message) -> None:
            nonlocal status, sent
            if message["type"] == "http.response.start":
                status, sent = message["status"], True
                headers = list(message.get("headers", []))
                headers += [
                    (b"x-request-id", identifier.encode()),
                    (b"cache-control", b"no-store"),
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                ]
                if self.settings.env in (Environment.STAGING, Environment.PRODUCTION):
                    headers.append((b"strict-transport-security", b"max-age=31536000"))
                message = {**message, "headers": headers}
            await send(message)

        async def failure(code: str, response_status: int) -> None:
            await JSONResponse(
                {"error": {"code": code, "request_id": identifier}}, status_code=response_status
            )(scope, receive, safe_send)

        try:
            lengths = [value for key, value in scope["headers"] if key.lower() == b"content-length"]
            if len(lengths) > 1 or (lengths and (not lengths[0].isdigit() or len(lengths[0]) > 12)):
                await failure("invalid_request", 400)
                return
            if lengths and int(lengths[0]) > self.settings.max_request_bytes:
                await failure("request_too_large", 413)
                return
            try:
                async with asyncio.timeout(self.settings.request_timeout):
                    await self.app(scope, bounded_receive, safe_send)
            except BodyTooLarge:
                if sent:
                    raise
                await failure("request_too_large", 413)
            except TimeoutError:
                logger.warning("request_timeout")
                if sent:
                    raise
                await failure("request_timeout", 504)
            except Exception as exc:
                logger.error("unexpected_error", extra=exception_fields(exc))
                if sent:
                    raise
                await failure("internal_error", 500)
        finally:
            method = scope.get("method", "OTHER")
            logger.info(
                "request_completed",
                extra={
                    "status": status,
                    "method": method
                    if method in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
                    else "OTHER",
                    "duration_ms": round((time.monotonic() - started) * 1000, 2),
                },
            )
            request_id.reset(token)
