# Development environment

Phase 0 repository tooling remains Python 3.14.2/Git with make bootstrap,
make hooks, make check and make security-check. Backend uses a separate pinned
Python 3.13.16 environment selected by apps/backend/.python-version and uv.lock.
Install uv **0.12.23** with your reviewed package manager, or into the bootstrap
venv: .venv/bin/python -m pip install uv==0.12.23. On Windows use the corresponding
.venv/Scripts/python.exe. Docker Engine and Docker Compose are required for real
local PostgreSQL/container checks; no private corpus access is needed.

## Start the Phase 1 local runtime

From the repository root:

```sh
python3 scripts/phase1.py init
python3 scripts/phase1.py up
python3 scripts/phase1.py smoke
```

init creates an ignored mode-600 password file without displaying values. up
starts PostgreSQL, builds the backend, runs an explicit migration job, then waits
for backend readiness. Ports bind only to localhost: API 8000, PostgreSQL 5433.
The default local environment is synthetic/empty and has no accounts or lessons.
Health endpoints are http://127.0.0.1:8000/health/live and /health/ready; local
OpenAPI docs are available at /docs. There are no business routes.

Use python3 scripts/phase1.py down to stop services; volumes are preserved.
Never casually delete generated credentials while retaining a database volume:
the original database password does not automatically change. Backup/reset of
local data requires an explicit developer action, not an implicit script cleanup.
Do not use this Compose definition for staging/production. The local database
role is privileged for disposable development/test provisioning only.

A Docker host must permit normal inter-container bridge traffic. This workspace
has conflicting legacy/nft forwarding rules; its bridge timeout was diagnosed
without altering the firewall. The runtime image was validated through a
loopback-only diagnostic path here, and CI exercises standard Compose. Fix host
Docker networking administratively rather than changing application security.

## Backend checks

```sh
uv sync --locked --project apps/backend
uv run --locked --project apps/backend ruff format --check apps/backend
uv run --locked --project apps/backend ruff check apps/backend
uv run --locked --project apps/backend mypy --config-file apps/backend/pyproject.toml apps/backend/src
python3 scripts/phase1.py test
python3 scripts/phase1.py audit
make check
make security-check
```

The helper also locates uv installed in the root bootstrap venv. It never inherits
NORSKALLSTARS production settings from your shell: test creates a separate
norskallstars_test database, migrates it and runs all backend tests. Integration
tests fail unless the environment is test and the database name ends in _test.
They intentionally exercise rollback and migration downgrade; never point them
at real data. A reduced unit run uses pytest -c apps/backend/pyproject.toml
apps/backend/tests -m 'not integration'; that is not full backend acceptance.

Settings are environment-only; .env.example is explanatory, not a runnable secret
source. For a direct source process, supply required configuration securely and
run uvicorn norskallstars_backend.app:create_app --factory with access logs and
proxy headers disabled. The image already selects those flags. Staging/production
require verified database TLS, mounted CA, explicit hosts, safe logging and
external secret injection; production orchestration is outside Phase 1.

Hook/scanner setup from Phase 0 still applies. Gitleaks remains checksum-pinned,
redacts output and inspects the index. Do not use full Docker environment output,
raw exceptions, private packages or sensitive logs as public CI artifacts.

## Phase 0 portability and offline scanner setup

Windows PowerShell repository tooling remains supported:

```powershell
py -3.14 -m venv .venv
.venv\Scripts\python.exe scripts/install_security_tool.py
.venv\Scripts\python.exe scripts/install_hooks.py
.venv\Scripts\python.exe scripts/check_repository.py
.venv\Scripts\python.exe scripts/confidentiality_guard.py --history main
.venv\Scripts\python.exe scripts/scan_secrets.py --history main
```

The scanner installer supports checksum-pinned Linux x64/arm64, macOS x64/arm64
and Windows x64 archives. Offline setup uses --archive /path/to/archive with
the same committed checksum. Existing unrelated hooks/hooksPath are never replaced.
Backend filesystem-adapter tests run on Linux/POSIX; Docker Desktop uses Linux
containers. On non-POSIX hosts protect ignored credential files with appropriate
user-only filesystem permissions; chmod alone does not establish Windows ACLs.
