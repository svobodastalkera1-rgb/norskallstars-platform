# Changelog

## Unreleased

- Phase 0 bootstrap: architecture boundaries, project workflow, confidentiality
  safeguards, development tooling and CI definitions; accepted by Product Owner.
- Phase 1 backend infrastructure, local Docker runtime, real PostgreSQL/tests,
  safe configuration/logging/health/storage and backend/CodeQL CI; owner accepted (PR #4 merged).
- No production release delivered.

Phase 3: shared identity, validated versioned API/OpenAPI, email/Google proof flows,
verification/recovery, preferences, server-revocable sessions, ownership checks,
transactional identity deletion and encrypted mail outbox. Owner review pending.
Phase 2 orphan reconciliation/retention/GC remains mandatory before production
asset storage/media/import operations. No Phase 4 work or deployment performed.

Release policy: [docs/releases.md](docs/releases.md).

Phase 2: controlled public Contract v1 receiving, repeatable fail-closed handoff
tooling, bounded generic validation, immutable staged releases/assets/audit,
idempotent import and privileged publication boundary. Owner accepted; PR #7 merged.
