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

## Phase 3 — Identity / CLOSED / ACCEPTED

- [x] Shared accounts, email/password and Google sign-in; verification/recovery.
- [x] Preferences, revocable sessions/devices and account-owned authorization.
- [x] Self-service account deletion with complete identity/session invalidation.
- [x] Typed secret/configuration, migrations, threat review and regression suites.
- [x] PR #8 implementation 62b5a8a passed hosted required checks/CodeQL (15 successful).
  Every later head is verified separately; no inherited/fake green checks.
- [x] Product Owner accepted PR #8, all 15 final checks and Code Scanning UI.
- [x] PR #8 merged; accepted tree verified on main d03336a; seven required main jobs passed.
- [ ] Acceptance-test live SMTP delivery against configured isolated staging,
  including at-least-once retries/duplicate semantics, before production mail operation.
- [ ] Acceptance-test live Google authentication against configured staging
  credentials/provider before production Google authentication.
- [ ] Before production: owner privacy/unverified-account/financial retention policy;
  later-domain erasure hooks; broader compromised-password/edge abuse review;
  mail/credential cleanup scheduling, monitoring and explicit key rotation.
- [ ] Web/Android phases: secure token persistence and browser CSRF/cookie adapter
  review if introduced; Phase 10 separate administrator MFA/RBAC.

## Phase 4 — Learning Core / CLOSED / ACCEPTED

- [x] Verify Phase 3 merge/acceptance and read all authoritative scope sources.
- [x] Confirm scope agreement and record complete known capabilities/dependencies,
  expected persistence/API/privacy boundaries and gates in
  [Learning Core](docs/architecture/learning-core.md).
- [x] Product Owner supplied public-safe placement, evaluator/normalization,
  completion/unlock, mastery/review, content-version and learning-data policies.
  Rules are recorded in Learning Core; numeric thresholds require explicit versioned
  policy, with no application pedagogical defaults.
- [x] Design/implement Phase 4 feature work, including
  all deterministic components, user-owned attempts/progress/events, account-erasure
  interaction, bounded authenticated APIs and DB constraints/concurrency behavior.
- [x] Validate all previous regressions, new domain/API/ownership/race/security tests,
  migrations/OpenAPI, dependency/security/container and actual hosted required checks/CodeQL.
- [x] Product Owner accepted PR #9, hosted required checks, Code Scanning and public
  artifact review; merged implementation verified on main 9194c7c on 2026-10-07.
- [x] Confirm merged main Backend CI, Phase 0 CI and Python CodeQL completed successfully.

## Phase 5 — Web / conditional authorization; product decision pending

- [x] Read authoritative scope; sources agree on Phase 5 Web. Record capabilities,
  dependencies, privacy boundaries and acceptance gates in [Web scope](docs/web/README.md).
- [ ] Product Owner defines voice purpose, local versus submitted recording behavior,
  retention and deletion. Do not infer this policy from generic JSON responses or
  invent a Course Package Contract extension; implementation is stopped pending decision.
  Owner clarified: local-only recordings apply when processing is unnecessary.
  Owner now requests random selective server audio retention and indefinite
  retention of all user data after account deletion until optional Owner cleanup.
  Reconcile this explicit policy change with accepted erasure semantics, retained
  categories/purpose/notice and applicable privacy rights before implementation;
  preserve current erasure tests meanwhile. Future ML remains outside Phase 5.
- [ ] Design reviewed browser session/token handling and stable backend API projections.
- [ ] Implement complete responsive accessible Bokmål-first React/TypeScript client:
  identity, learning/replay/review/placement, dashboard, preferences, localization,
  course audio/images and the approved microphone workflow.
- [ ] Implement and verify storage reconciliation/retention/orphan GC before serving
  course assets. Preserve in-flight protection, grace, final reference checks and audit.
- [ ] Verify provider staging gates for any live SMTP/Google-dependent journey;
  mocks do not satisfy provider acceptance; SMTP remains at-least-once.
- [ ] Add real Web quality, dependency/security, browser accessibility/E2E and code
  scanning checks; run all accepted backend/Contract/receiving/confidentiality regressions.
- [ ] Deliver feature PR with exact-head hosted evidence; await Product Owner review.
- [ ] Phase 6 NOT STARTED; no Android implementation is authorized.

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
