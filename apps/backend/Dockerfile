# Python 3.13.16 and uv 0.12.23, pinned to reviewed manifest digests.
FROM ghcr.io/astral-sh/uv:0.12.23@sha256:61d393e44e249f2e4b526b6c7ddcecce245946826e608e11c93ad4f5bba55b21 AS uv
FROM python:3.13.16-slim@sha256:bb2988715db2cf7ace7b53f38f3cffbef7c7046a656bee66245eb0ed386e2e81 AS build
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app/apps/backend
ENV UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/app/.venv
COPY apps/backend/pyproject.toml apps/backend/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project --no-cache
COPY apps/backend/src ./src
COPY contracts/course-package/upstream/specification /app/contracts/course-package/upstream/specification
COPY contracts/course-package/upstream/tools/course_package.py /app/contracts/course-package/upstream/tools/course_package.py
RUN uv sync --locked --no-dev --no-editable --no-cache

FROM python:3.13.16-slim@sha256:bb2988715db2cf7ace7b53f38f3cffbef7c7046a656bee66245eb0ed386e2e81
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid 10001 --no-create-home app \
    && mkdir /app /app/storage && chown app:app /app/storage
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY apps/backend/alembic.ini ./
COPY apps/backend/migrations ./migrations
ENV PATH="/app/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "norskallstars_backend.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--no-proxy-headers", "--no-server-header"]
