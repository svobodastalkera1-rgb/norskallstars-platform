# NorskAllstars

NorskAllstars Platform is being built for learning Norwegian Bokmål through
comprehensible input and the Natural Method. The production direction includes
a responsive Web client and a native Android client backed by the same services.

**Status: Phase 0 CLOSED/ACCEPTED; Phase 1 Core Infrastructure prepared for review.**
A real backend runtime now provides health endpoints, PostgreSQL/migrations,
configuration/logging and a storage boundary. Learning functions, accounts,
Course Package import, Web/Android clients and production deployment are not
implemented. Production v1.0 remains the release goal; see the [complete roadmap](ROADMAP.md).
Phase 2 has not started.

## Architecture direction

A monorepo will hold a Python/FastAPI modular monolith, PostgreSQL persistence
with SQLAlchemy/Alembic, Pydantic validation, React/TypeScript Web, and native
Kotlin/Jetpack Compose Android. Phase 1 supplies Docker packaging and an object
storage boundary. Redis or workers require a demonstrated use case. No production
infrastructure is provisioned.

| Location | Responsibility | Current state |
| --- | --- | --- |
| apps/backend/ | Backend infrastructure; later domain modules | Phase 1 runtime and tests |
| apps/web/ | Responsive learning client | Boundary documentation |
| apps/android/ | Native client and later offline capability | Boundary documentation |
| contracts/ | Public API and Course Package interfaces | Integration placeholders |
| infra/ | Local runtime; future deployment definitions | Local Docker Compose |
| docs/ | Engineering, ADRs, security and delivery guidance | Implemented |
| scripts/ | Repository and confidentiality checks | Implemented |

License selection remains pending Product Owner decision; no license is added.

See [architecture](docs/architecture/README.md) and the [ADR index](docs/adr/README.md).

## Course content boundary

The separate private NorskAllstars Corpus repository owns teaching materials.
This platform does not inspect its directory layout or embed real content.
Integration will use the existing versioned Course Package Contract v1, through
a controlled public handoff. Schemas and the approved synthetic fixture have
**not yet been supplied here**; no substitute contract or fake fixture is defined.
[Integration readiness](docs/corpus-integration/README.md) records the import gate.
A future development/demo environment must run with synthetic content alone.

## Local development

Install Git and Python **3.14.2** for repository tooling. Backend Python **3.13.16**
and dependencies are managed separately by pinned uv and uv.lock.
From the repository root on Linux/macOS:

```sh
make bootstrap
make hooks
.venv/bin/python scripts/check_repository.py
.venv/bin/python scripts/confidentiality_guard.py --history main
.venv/bin/python scripts/scan_secrets.py --history main
```

The security installer downloads a version/checksum-pinned Gitleaks binary.
Windows PowerShell equivalents and offline setup are in the
[development guide](docs/development.md). For the Phase 1 local backend, install Docker/Compose and run:

```sh
python3 scripts/phase1.py init
python3 scripts/phase1.py up
python3 scripts/phase1.py smoke
```

These commands generate ignored local credentials, start PostgreSQL/backend and
verify health. See the development guide for tests, host-network prerequisites
and lifecycle commands. No private package is required or accepted.

## Public repository security

Security must hold even when the implementation is fully visible. Confidential
content and operational secrets belong outside this checkout. Ignore rules,
a staged-file guard, secret scanning and review reduce accidental disclosure;
none is a guarantee or an authorization to publish data.
See [SECURITY.md](SECURITY.md), [CI status](docs/ci.md), and the
[owner settings checklist](docs/security/github-settings.md).

Start a new engineering session with [AGENTS.md](AGENTS.md),
[PROJECT_STATE.md](PROJECT_STATE.md), and [TASKS.md](TASKS.md).
