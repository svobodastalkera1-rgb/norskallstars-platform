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

init creates/extends an ignored mode-600 database/identity key file without displaying values. up
starts PostgreSQL, builds the backend, runs an explicit migration job, then waits
for backend readiness. Ports bind only to localhost: API 8000, PostgreSQL 5433.
The default local environment has no real users or lessons; use synthetic accounts only.
Health endpoints are http://127.0.0.1:8000/health/live and /health/ready; local
OpenAPI docs are available at /docs. Phase 3 exposes the documented Identity API;
no course import/publication or media HTTP routes exist.

Use python3 scripts/phase1.py down to stop services; volumes are preserved.
Never casually delete generated credentials while retaining a database volume:
the original database password does not automatically change. Backup/reset of
local data requires an explicit developer action, not an implicit script cleanup.
Do not use this Compose definition for staging/production. The local database
role is privileged for disposable development/test provisioning only.

A Docker host must permit normal inter-container bridge traffic. This Codespace
previously had conflicting legacy/nft forwarding rules. Environment recovery on
2026-10-07 added two reversible, project-scoped PostgreSQL rules without changing
the global DROP policy or Docker-owned nft rules; authenticated Compose-network
queries now pass. Local ignored repair/rollback tooling is under
`.cache/environment-diagnostics/`; it is specific to this workspace, not a
project dependency or production configuration. After host/network recreation,
recheck connectivity and the host firewall before rerunning container validation.
Do not disable firewall protections or change application security to fix routing.

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

## Phase 3 identity development

Re-run `python3 scripts/phase1.py init` after updating an older checkout: it preserves
existing credentials and adds independent identity pepper/mail encryption keys.
Nothing prints their values. Do not commit generated keys or local email files.
Local transport defaults to encrypted DB outbox. A private mailbox is optional:

```sh
python3 scripts/phase1.py mail
python3 scripts/phase1.py identity-cleanup
```

Read local `.eml` files privately; the one-use token is in a URL fragment and must
be submitted through the Web account UI or as JSON to verification/reset API.
Delete local mailbox files after testing; they are mode 600 and never CI artifacts.
The helper always targets the generated local environment, not inherited production
settings. The command manages only expired identity tokens/mail/rate/session rows;
it does not implement the deferred course object reconciliation gate.

Identity mutations use JSON and `X-NorskAllstars-Client: operator`, `web` or `android`.
That header is request shape, not authorization. Protected routes require the actual
opaque bearer session; cookies/URL tokens and unapproved origins are rejected.
No real emails are sent by tests. Native/Web Google audiences and authenticated
TLS SMTP must be configured privately for staging/production; provider checks there
remain owner actions, not simulated CI acceptance. See [identity architecture](architecture/identity.md)
for endpoints, lifetimes, transaction behavior and exact limits.

```sh
uv run --locked --project apps/backend python -m norskallstars_backend.identity.openapi contracts/api/identity-v1.openapi.json --check
```

## Phase 4 learning development

Apply Alembic head explicitly before readiness/learning checks. Learning uses the
accepted Identity session model; every learner endpoint needs a verified account
and bearer access token. Mutations require the existing client header/JSON boundary.
The API inventory/semantics are in docs/architecture/learning-core.md and the
reviewed contracts/api/learning-v1.openapi.json. Accepted Phase 5 Web and the
authorized Phase 6 native Android client consume these same contracts.

An authorized OS/DB operator can select an already-published eligible release and
bounded external policy (never a private policy checked into public Git):

```sh
python -m norskallstars_backend.learning.cli select <release-uuid> <external-policy-path> --actor <operator> --approval <approval-reference>
```

This changes only new-enrollment selection and immutable learning-policy audit;
it never publishes/imports a package or migrates existing progress. Assertions
are operator intent, not HTTP authentication/RBAC. Use synthetic test data locally;
private corpus/pilot import and production operations are not authorized.
No concrete/default pedagogical threshold or production policy is supplied.

Run existing backend-test/backend-audit plus make check/security-check. Backend
quality checks Identity/Learning OpenAPI and platform policy schema drift. To
regenerate reviewed learning artifacts from typed code, use learning.openapi and
learning.policy_schema modules with their destination paths; review compatibility.

## Phase 5 Web and media development

Node **24.21.0**, npm lock and uv **0.12.23** are pinned. Complete local runtime:

```sh
python3 scripts/phase1.py init
python3 scripts/phase1.py up
```

Visit http://127.0.0.1:8000. The built client is included in the read-only non-root
backend image. The empty local database contains no users/corpus; registration
and verification use the existing private outbox workflow. Publishing real/private
packages into this public checkout is never part of local setup.

For frontend hot reload, start `npm ci --ignore-scripts && npm run dev` in apps/web
with backend running. The API proxy stays on loopback; Compose explicitly permits
127.0.0.1:3000 and serves 127.0.0.1:8000. Use matching hostnames in browser and
configured origins. Credentials are tab-memory only; reload signs out deliberately.

```sh
make web-check
make web-test
cd apps/web && npm run contracts && npm audit --audit-level=low
```

From root, install browsers with `cd apps/web && npx playwright install --with-deps
chromium firefox webkit`, then run `make web-e2e`. Browser setup creates and resets
ONLY `norskallstars_web_test` before each independent browser project, with the
guarded approved synthetic derivative. This isolates learner/rate-bucket state while
retaining ordinary runtime rate limits. Stop the Compose backend before E2E because
the test server binds the same local port; the database can remain running.
Generated mode-600 `.cache/web-e2e/login.json` is ignored; never publish it, browser
error contexts, screenshots, videos or traces. Integration testing requires Docker
and network access; mocks do not close this gate. `scripts/phase1.py test` still runs
all backend/PostgreSQL/Contract regressions against the separate backend test DB.

Local storage maintenance: `make storage-cleanup` uses the same Compose backend
volume/configuration. It is a private operator command, never HTTP. For a separately
configured source/staging worker run `python -m norskallstars_backend.media.cleanup`
with that environment's injected configuration. Do not mix buckets/databases.

Voice sampling defaults to **0**; operational rate must be explicitly configured
(0..0.25), with consent still required per speaking activity. Client recording is
bounded to 60 seconds and 256 KiB; server enforces 256 KiB, container signature and
checksum, stores opaque bytes and does not decode/train/evaluate speech. Recorded
containers do not prove decoder safety; any future processor needs separate review.
An offer expires in one hour; retained mappings expire by twelve calendar months.
Account erasure/withdrawal removes mappings immediately; physical erasure requires
scheduled cleanup. GC scans only owned namespaces, refuses >100,000 inventory/
references, handles at most 100 objects per run and honors 300..86,400-second grace
(default 3,600). Hash-only deletion audit is retained up to 365 days; no learner
response/account ID is stored in it. Schedule, monitor and verify erasure/backups
against production policy before operating remote storage.

S3 requires explicit HTTPS endpoint, bucket/region and externally injected keys.
No credential discovery or signed URL is used; requests use verified TLS, bounded
timeouts/retries and AES256 server-side encryption. Verify private bucket ACL/policy,
least privilege, inventory/deletion semantics and anonymous denial in isolated staging.
The adapter/stub tests do not prove live provider acceptance. Enabled or suspended bucket versioning is rejected before reads/writes/deletes/
inventory because delete markers do not erase historical objects. This adapter
requires an unversioned bucket and permission to inspect versioning. A future
version-aware adapter/lifecycle needs separate verified erasure semantics.

Google browser build uses a public client identifier only: `docker build --build-arg
VITE_GOOGLE_CLIENT_ID=your-public-web-client-id.apps.googleusercontent.com ...`.
Never pass secrets through VITE variables/build args. Configure matching backend
Google audiences and live SMTP privately, then perform staging acceptance; unconfigured
providers are shown as unavailable. No deployment/provider registration is performed.

## Phase 6 native online development

See [Android setup and synthetic device tests](../apps/android/README.md).
Android tests use their own guarded database and port 8001; Web manual-review data
is preserved. Phase 7 content caching/downloads/offline queues remain unauthorized.
