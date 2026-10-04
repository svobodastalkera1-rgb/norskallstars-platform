"""JSON events from an allowlist, never arbitrary exception/request text."""

import json
import logging
import traceback
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
EVENTS = {
    "runtime_started",
    "runtime_stopped",
    "request_completed",
    "unexpected_error",
    "dependency_unavailable",
    "request_timeout",
    "request_too_large",
}


def exception_fields(exc: Exception) -> dict[str, Any]:
    return {
        "exception_type": type(exc).__name__,
        # Useful source positions, without exception messages, values, locals or source lines.
        "frames": [
            {"file": Path(frame.filename).name, "line": frame.lineno, "function": frame.name}
            for frame in traceback.extract_tb(exc.__traceback__)[-8:]
        ],
    }


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.msg
            if isinstance(record.msg, str) and record.msg in EVENTS
            else "library_event",
            "request_id": request_id.get(),
        }
        for name in ("status", "method", "duration_ms", "exception_type", "frames", "environment"):
            if hasattr(record, name):
                data[name] = getattr(record, name)
        # Intentionally do not format message arguments, exc_info or stack_info.
        return json.dumps(data, ensure_ascii=True)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy", "psycopg"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
        logger.setLevel(logging.WARNING)
