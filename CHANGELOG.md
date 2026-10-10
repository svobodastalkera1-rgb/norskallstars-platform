# Changelog

## Unreleased

- Phase 0 bootstrap: architecture boundaries, project workflow, confidentiality
  safeguards, development tooling and CI definitions; accepted by Product Owner.
- Phase 1 backend infrastructure, local Docker runtime, real PostgreSQL/tests,
  safe configuration/logging/health/storage and backend/CodeQL CI; owner accepted (PR #4 merged).
- No production release delivered.

Phase 3: shared identity, validated versioned API/OpenAPI, email/Google proof flows,
verification/recovery, preferences, server-revocable sessions, ownership checks,
transactional identity deletion and encrypted mail outbox. Owner accepted; PR #8 merged.
Phase 2 orphan reconciliation/retention/GC remains mandatory before production
asset storage/media/import operations. Live staging SMTP/Google acceptance remains
open; SMTP delivery is at-least-once. Phase 4 was accepted by Product Owner and
merged through PR #9; no deployment performed.

Release policy: [docs/releases.md](docs/releases.md).

Phase 2: controlled public Contract v1 receiving, repeatable fail-closed handoff
tooling, bounded generic validation, immutable staged releases/assets/audit,
idempotent import and privileged publication boundary. Owner accepted; PR #7 merged.

Phase 4: immutable versioned learning policies, release-pinned enrollments,
canonical completion/mastery/review, deterministic evaluator/placement seams, private
attempts/history/events, account-deletion cascade and authenticated curriculum API.
Contract v1 is unchanged; owner acceptance and merged main verification completed
on 2026-10-07. Historical review evidence remains unchanged.

Phase 5 Web follows Owner-accepted selective voice/privacy policy: separate consent,
explicit purpose, at most twelve months and account-deletion erasure.

Phase 5 (PR #10, review pending): responsive Bokmål-first Web,
Identity/Learning API client, private media/consented selective recordings,
coordinated retention/orphan cleanup, dashboard engagement evidence and real
Web/CodeQL workflow definitions. Complete local backend/browser/container regression
and locked dependency audits passed; all implementation-head hosted checks passed,
with Owner acceptance and later evidence-head verification remaining separate;
no production release or Phase 6 implementation.

Phase 5 closure: Product Owner accepted the corrected synthetic Web journey and
merged PR #10 at `8100927`; merged-main workflows passed. Earlier evidence above
remains historical. Phase 6 Android is now authorized; native implementation and
validation proceed on a feature branch. No Phase 7 or production release.

Phase 6: native Kotlin/Compose online account/learning/dashboard/media client,
protected device sessions and lifecycle/permission controls, generated API DTOs,
pinned/checksummed toolchain, genuine Android CI and Java/Kotlin CodeQL definitions.
Local unit/lint/debug/release evidence is recorded in docs/phase-6-review.md;
API 26/35 hosted device gates each passed 3/3; all 35 implementation-head hosted
checks passed. Owner acceptance remains pending. No migration,
privileged HTTP, private content, offline sync, signing or deployment is added.
