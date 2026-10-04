# Tasks

## Completed governance

- [x] Phase 0 CLOSED/ACCEPTED and published; hosted main Phase 0 CI passed.
- [x] Owner configured active Protect main and repository security features.
- [x] Owner authorized and accepted Phase 1 Core Infrastructure.
- [x] Owner added seven real required checks and enabled strict up-to-date branches.
- [x] Owner reviewed/accepted Phase 1 and merged PR #4 through protected workflow.
- [ ] License remains Product Owner pending; add no license/make no open-source claim.
- [x] Controlled public Contract v1 receiving gate passed; no private repo access.
- [ ] Owner confirms earlier server-side confidentiality incident status privately.

## Phase 1 — CLOSED / ACCEPTED

- [x] Pin backend runtime and public-index dependencies in uv.lock.
- [x] Implement FastAPI factory, typed settings and lifespan ownership.
- [x] Add async PostgreSQL transaction boundary and real isolated test database.
- [x] Add Alembic tracking baseline without product tables; migration sanity/drift tests.
- [x] Implement bounded health, safe errors/logs, correlation IDs and request boundary.
- [x] Define storage protocol and tested development-only local adapter.
- [x] Build non-root backend image and local Compose configuration.
- [x] Replace backend pending gate with real quality/tests/dependency/container CI.
- [x] Prepare Python CodeQL analysis and runtime threat/security review.
- [x] Initial Phase 1 PR hosted runs passed; revision/run evidence is recorded.
- [x] Owner verified successful PR checks and healthy default-branch Code scanning/no alerts.
- [x] Product Owner accepted Phase 1 and authorized Phase 2 subject to receiving gate.

## Phase 2 — CLOSED / ACCEPTED

Receiving completed; implementation follows: controlled public handoff review/provenance, actual
Contract v1 compatibility assessment, untrusted-input validation design, transactional
staged CourseRelease import and minimal protected/audited publication, synthetic
fixture integration and negative tests. Missing contractual/security decisions
must be resolved before implementation; never infer schemas or use private pilot
in public source/CI. Product identity/administration completion stays in its phases.

- [x] Fail-closed local staging/archive/inventory/confidentiality/contract gates.
- [x] Byte-preserving public-only transfer; raw ZIP and transfer metadata excluded.
- [x] Generic bounded validation and immutable staged release/asset/audit persistence.
- [x] Identity/version conflict handling, transactional rollback and concurrency tests.
- [x] Complete security/compatibility tests and initial real hosted CI; open PR #7.
- [x] Owner reviewed/accepted PR #7, required checks, scanning and clarification.
- [x] PR #7 merged; accepted implementation verified on current main.

## Phase 3 — Identity / AUTHORIZED

- [x] Shared accounts, email/password and Google sign-in; verification/recovery.
- [x] Preferences, revocable sessions/devices and account-owned authorization.
- [x] Self-service account deletion with complete identity/session invalidation.
- [x] Typed secret/configuration, migrations, threat review and regression suites.
- [ ] Verify exact PR-head hosted required checks/CodeQL; no fake green checks.
- [ ] Product Owner reviews/accepts Phase 3 PR; never auto-merge.
- [ ] Configure/verify real isolated staging Google/SMTP before live operation.
- [ ] Before production: owner privacy/unverified-account/financial retention policy;
  later-domain erasure hooks; broader compromised-password/edge abuse review;
  mail/credential cleanup scheduling, monitoring and explicit key rotation.
- [ ] Web/Android phases: secure token persistence and browser CSRF/cookie adapter
  review if introduced; Phase 10 separate administrator MFA/RBAC.
- [ ] Phase 4 remains NOT STARTED / awaiting separate authorization.

## Mandatory future production storage gate

- [ ] Before production/remote persistent object storage, HTTP media delivery,
  externally reachable assets or production imports: implement storage inventory
  reconciliation against committed DB references, in-flight import protection,
  grace period, reference re-check immediately before deletion, auditable deletion,
  retention, safe retries/idempotency and race/failure tests. Accepted Phase 2
  orphans are private/unmapped and DB rollback remains complete; this development
  limitation must not silently become a production retention policy.

## Later owner decisions

Target markets/payment/store policies, hosting/regions, privacy/retention/voice
handling, recovery objectives, client support and content-version migration rules
must be settled before their relevant acceptance gates. Do not fabricate product
rules to unblock infrastructure work.
