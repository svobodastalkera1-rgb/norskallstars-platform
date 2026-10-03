# NorskAllstars

NorskAllstars Platform is being built for learning Norwegian Bokmål through
comprehensible input and the Natural Method. The production direction includes
a responsive Web client and a native Android client backed by the same services.

**Status: Phase 0 — Bootstrap, ACCEPTED by Product Owner.** The repository
currently contains architecture, development tooling, confidentiality controls,
and CI definitions. No learning application, API server, or deployable release
exists yet. Phase 1 is NOT STARTED and awaits separate authorization. Production v1.0, rather than an MVP, is the
release goal; see the [complete roadmap](ROADMAP.md).

## Architecture direction

A monorepo will hold a Python/FastAPI modular monolith, PostgreSQL persistence
with SQLAlchemy/Alembic, Pydantic validation, React/TypeScript Web, and native
Kotlin/Jetpack Compose Android. Docker and an object storage abstraction are
planned; Redis or workers require a demonstrated use case. There are no runtime
services or infrastructure resources provisioned in bootstrap.

| Location | Responsibility | Current state |
| --- | --- | --- |
| apps/backend/ | API and domain modules | Boundary documentation |
| apps/web/ | Responsive learning client | Boundary documentation |
| apps/android/ | Native client and later offline capability | Boundary documentation |
| contracts/ | Public API and Course Package interfaces | Integration placeholders |
| infra/ | Environment and deployment definitions | Design only |
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

Install Git and Python **3.14.2** for bootstrap tooling; no application dependencies
are required. This pin does not decide the future backend's supported Python version.
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
[development guide](docs/development.md). There is no application start command
in Phase 0. Do not run a database or import a private package for bootstrap.

## Public repository security

Security must hold even when the implementation is fully visible. Confidential
content and operational secrets belong outside this checkout. Ignore rules,
a staged-file guard, secret scanning and review reduce accidental disclosure;
none is a guarantee or an authorization to publish data.
See [SECURITY.md](SECURITY.md), [CI status](docs/ci.md), and the
[owner settings checklist](docs/security/github-settings.md).

Start a new engineering session with [AGENTS.md](AGENTS.md),
[PROJECT_STATE.md](PROJECT_STATE.md), and [TASKS.md](TASKS.md).
