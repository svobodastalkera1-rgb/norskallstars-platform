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

## Phase 5 — Web / CLOSED / ACCEPTED

- [x] Read authoritative scope; sources agree on Phase 5 Web. Record capabilities,
  dependencies, privacy boundaries and acceptance gates in [Web scope](docs/web/README.md).
- [x] Product Owner accepted selective voice collection with separate consent,
  explicit purpose, at most twelve months and account-deletion erasure. The earlier
  indefinite-retention request is superseded; ML remains outside Phase 5.
- [x] Implement memory-only browser sessions and stable API projections; ADR 0013.
- [x] Complete local security/runtime review; exact hosted head remains a separate gate.
- [x] Implement responsive Bokmål-first React/TypeScript client in the working tree:
  identity, learning/replay/review/placement, dashboard, preferences, localization,
  course audio/images and the approved microphone workflow.
- [x] Verify 9/9 Chromium/Firefox/WebKit journeys/accessibility and 243/243 backend
  PostgreSQL/migration/media/security/race regressions after the latest fixes.
- [x] Implement storage inventory, reference coordination, expiry/retention and GC.
- [x] Complete local PostgreSQL/race/failure verification of course delivery/GC;
  in-flight protection, grace, final reference checks and durable audit tested.
- [x] Pass final container build/migration/runtime smoke, Web 16/16 component tests,
  locked backend/npm audits and unchanged Contract 19/19 regressions.
- [ ] Verify provider staging gates for any live SMTP/Google-dependent journey;
  mocks do not satisfy provider acceptance; SMTP remains at-least-once.
- [x] Add real Web quality/tests/dependency and CodeQL Web workflow definitions.
- [x] Verify all 23 implementation-head hosted checks, including the seven required
  names and Backend/Web/Contract/receiving/confidentiality/CodeQL regressions.
- [x] Final correction-head hosted checks passed; Owner completed review and merged PR #10.
  Alert API access remains distinct from Owner Code Scanning UI review.
- [x] Restore environment capabilities for Docker/network and `.git` writes;
  2026-10-07 probes passed, including authenticated Compose-network PostgreSQL and
  Docker build. A scoped reversible local firewall repair preserves global DROP;
  reapply after host/network recreation if needed. Complete local application
  validation passed; feature commit/push/PR and hosted results remain separate gates.
- [x] Open [PR #10](https://github.com/svobodastalkera1-rgb/norskallstars-platform/pull/10)
  against protected main; implementation-head hosted results passed.
- [x] Investigate manual-review time semantics and missing smoke-course matching
  binding; clarify submitted-only time and add explicit versioned synthetic binding.
- [x] Pass correction regressions: 245 backend, 24 Web unit/component, 9 cross-browser
  E2E, 19 Contract and 25 repository/receiving tests, quality/audits/container gates.
- [x] Owner completed the corrected synthetic manual journey and accepted existing
  submitted-active-time semantics; immutable enrollment policies remain intact.
- [x] Product Owner accepted Phase 5 and merged PR #10; tree and merged-main CI verified.

## Phase 6 — Android / AUTHORIZED

- [x] Verify PR #10 merge/tree and successful merged-main Backend/Web/Safeguards/CodeQL.
- [x] Reconcile Phase 5 acceptance without rewriting dated evidence.
- [x] Establish authoritative online native scope in [Android](docs/android/README.md).
- [x] Implement native Kotlin/Compose account, learning, dashboard, media and microphone journeys.
- [x] Review native credential storage, lifecycle, permissions and account isolation.
- [x] Pin/verify toolchain and dependency locks/checksums; implement real lint,
  JVM/build/OSV/device/compiled CodeQL workflow definitions.
- [x] Final native 19/19 JVM tests, Lint, debug/test APK and R8 release builds;
  API 35 real-backend device 3/3. Failures/repeats recorded in docs/phase-6-review.md.
- [ ] Verify exact-head hosted Android/CodeQL and API 26/35 matrix; definitions
  and local builds are not hosted acceptance.
- [x] Run accepted backend/PostgreSQL/Web/Contract/receiving/container regressions.
- [x] Inspect staged public changes; exact index/history confidentiality and secret gates pass.
- [x] Publish feature branch and PR #17 with explicit Product Owner authorization;
  never merge automatically.
- [ ] Product Owner reviews Phase 6; Phase 7 remains NOT AUTHORIZED.


## Mandatory future production storage gate

- [x] Phase 5 implements storage reconciliation/retention/GC with shared writer/
  exclusive GC locks, grace, final reference re-check, durable deletion intents and
  retry/idempotency; local PostgreSQL race/failure tests passed.
- [x] Implementation-head hosted GC/media regression passed.
- [x] Owner accepted Phase 5; PR #10 merged tree and merged-main checks verified.
- [ ] Before live production/remote storage/media/import: acceptance-test private
  unversioned S3 bucket, IAM/anonymous-denial/encryption and provider erasure; schedule
  monitored cleanup with retention SLA, failure alerts and backups erasure policy.
  Unmapped orphans remain private; DB rollback is atomic. Functional test success
  must not silently close live operational acceptance.

## Later owner decisions

Target markets/payment/store policies, hosting/regions, privacy/retention/voice
handling, recovery objectives, client support and content-version migration rules
must be settled before their relevant acceptance gates. Do not fabricate product
rules to unblock infrastructure work.
