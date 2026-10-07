# Phase 1 backend runtime

The modular-monolith boundary remains accepted. Infrastructure is a single
installable norskallstars_backend package; product modules are deliberately absent.

| Component | Responsibility |
| --- | --- |
| config.py | Environment validation and escaped SQLAlchemy URL construction |
| database.py | Owned async engine, per-transaction sessions, migration-aware probe and disposal |
| app.py | Application factory/lifespan and minimal infrastructure routes |
| middleware.py | Request ID, bounded requests/time, safe JSON errors and response headers |
| logging.py | JSON event allowlist and value-free diagnostic frames |
| storage.py | Async vendor-neutral object operations and development-only filesystem adapter |
| migrations/ | Alembic metadata and a baseline revision without product tables |

Factory creation validates configuration but does not require a live database.
Lifespan owns pool cleanup. Liveness is process-local. Readiness bounds a real
connection/query and requires the expected migration revision. An unreachable,
uninitialized or differently versioned database yields only 503/not_ready.
Pool sizes, connection/statement timeouts and readiness duration are bounded.

Transactions use async_sessionmaker.begin: commit on successful exit, otherwise
rollback, and close in all cases. Metadata has no product tables. SQL parameters
are hidden, engine echo is off, and drivers cannot emit arbitrary message text
through the configured JSON formatter. Domain/session ownership is not yet an
application authorization model.

Config supports local (dev alias), test, staging and production. Environment and credentials
are required; no implicit development fallback, default password or .env lookup exists. Staging and
production require verified database TLS, a mounted CA, explicit service hosts,
nondefault administrator username and no DEBUG or local storage. Deployment
must provision separate least-privilege application/migration credentials;
username validation is not proof of database role privileges. No production
infrastructure or credentials are provisioned in Phase 1.

ObjectStorage defines async put/get/delete. The local adapter is development-only,
with constrained keys, size limits, directory-descriptor/no-follow access,
atomic replacement and idempotent delete. It has no HTTP asset/upload routes.
A future S3-compatible adapter must conform to this boundary; none is claimed
implemented or connected. Storage is disabled when no asset consumer exists,
so it is not a required readiness dependency in this phase.

The HTTP boundary adds bounded body reads/time, trusted-host validation, explicit
optional CORS and correlation/security headers. Requests and validation errors
never echo bodies, query strings, headers or exception messages. Logs include
safe event/type/code-position metadata; arbitrary third-party text is suppressed.
This deliberately trades low-level message detail for confidentiality. Add future
safe diagnostic event fields deliberately rather than turning raw traces back on.

There is no authentication, resource authorization, rate-limit service, domain
schema, import pipeline or production deployment. These controls must arrive
with their authorized consumer phases. See the runtime security review.

Subsequent accepted Identity/Learning boundaries supersede the Phase 1-only scope
above. Phase 5 working-tree Web/media/storage additions and pending verification:
[Web review](../phase-5-review.md) and [ADR 0013](../adr/0013-web-media-privacy.md).
