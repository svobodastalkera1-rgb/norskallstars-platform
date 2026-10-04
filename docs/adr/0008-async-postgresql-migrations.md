# 0008 — Async PostgreSQL lifecycle and baseline revision

Status: Accepted (Phase 1 engineering decision; Product Owner accepted Phase 1 on 2026-10-04)
Date: 2026-10-03

## Context

Phase 1 introduces a real ASGI service and PostgreSQL without product models.
Connection ownership, startup behavior and migration readiness need a defined boundary.

## Decision

Use Python 3.13.16, async SQLAlchemy 2.1 with psycopg 3, bounded pools and explicit
transaction contexts. Pin runtime/tools in uv.lock. Create engines without
startup connections; dispose in lifespan. Readiness probes PostgreSQL and the
expected Alembic revision, while liveness never probes external services.
An empty baseline revision initializes Alembic tracking only, providing a real
schema-version anchor before product tables are authorized.

## Alternatives

Sync database calls inside async routes would block the event loop unless
consistently offloaded. A second driver/migration connection model adds needless
configuration. Creating future user/course tables would exceed Phase 1.
Requiring all dependencies at startup would obstruct liveness during outages.

## Consequences

Readiness is false before migration or when revisions differ. Migration runs are
explicit, not automatic per application worker. Future revisions must update the
expected application revision and include compatibility/recovery review. No
product migration exists. Application/migration role provisioning remains an
environment responsibility; TLS validation must be verified before deployment.
