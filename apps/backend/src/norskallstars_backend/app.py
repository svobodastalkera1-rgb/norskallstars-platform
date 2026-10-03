"""Infrastructure-only application factory; no business endpoints."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import JSONResponse

from norskallstars_backend.config import Environment, Settings, load_settings
from norskallstars_backend.database import Database
from norskallstars_backend.logging import configure_logging, exception_fields, request_id
from norskallstars_backend.middleware import RequestBoundary
from norskallstars_backend.storage import LocalObjectStorage, ObjectStorage

logger = logging.getLogger("norskallstars.runtime")


def create_app(settings: Settings | None = None, database: Database | None = None) -> FastAPI:
    settings = settings or load_settings()
    configure_logging(settings.log_level)
    database = database or Database(settings)
    storage: ObjectStorage | None = None
    if settings.storage_backend == "local":
        if settings.storage_root is None:
            raise RuntimeError("Invalid local storage configuration")
        storage = LocalObjectStorage(settings.storage_root, settings.storage_max_bytes)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info("runtime_started", extra={"environment": settings.env.value})
        try:
            yield
        finally:
            await database.close()
            logger.info("runtime_stopped")

    development = settings.env in (Environment.LOCAL, Environment.TEST)
    app = FastAPI(
        title="NorskAllstars Platform",
        lifespan=lifespan,
        debug=False,
        docs_url="/docs" if development else None,
        redoc_url=None,
        openapi_url="/openapi.json" if development else None,
    )
    app.state.database, app.state.storage = database, storage
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=False,
            allow_methods=["GET"],
            allow_headers=["X-Request-ID"],
        )
    app.add_middleware(RequestBoundary, settings=settings)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            {"error": {"code": "http_error", "request_id": request_id.get()}},
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            {"error": {"code": "invalid_request", "request_id": request_id.get()}}, status_code=422
        )

    @app.get("/health/live", include_in_schema=False)
    async def liveness() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/health/ready", include_in_schema=False)
    async def readiness() -> JSONResponse:
        try:
            async with asyncio.timeout(settings.readiness_timeout):
                ready = await database.ready()
        except Exception as exc:
            logger.warning("dependency_unavailable", extra=exception_fields(exc))
            ready = False
        return JSONResponse(
            {"status": "ready" if ready else "not_ready"}, status_code=200 if ready else 503
        )

    return app
