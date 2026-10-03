# Tasks

## Completed governance

- [x] Phase 0 CLOSED/ACCEPTED and published; hosted main Phase 0 CI passed.
- [x] Owner configured active Protect main and repository security features.
- [x] Owner explicitly authorized Phase 1 Core Infrastructure only.
- [ ] Owner adds actual successful PR check names to Protect main; see docs/ci.md.
- [ ] Owner reviews Phase 1 PR; no automatic merge even with zero required approvals.
- [ ] License remains Product Owner pending; add no license/make no open-source claim.
- [ ] Controlled public Contract v1 handoff before Phase 2; no private repo access.
- [ ] Owner confirms earlier server-side confidentiality incident status privately.

## Phase 1 — implementation prepared / review pending

- [x] Pin backend runtime and public-index dependencies in uv.lock.
- [x] Implement FastAPI factory, typed settings and lifespan ownership.
- [x] Add async PostgreSQL transaction boundary and real isolated test database.
- [x] Add Alembic tracking baseline without product tables; migration sanity/drift tests.
- [x] Implement bounded health, safe errors/logs, correlation IDs and request boundary.
- [x] Define storage protocol and tested development-only local adapter.
- [x] Build non-root backend image and local Compose configuration.
- [x] Replace backend pending gate with real quality/tests/dependency/container CI.
- [x] Prepare Python CodeQL analysis and runtime threat/security review.
- [ ] Verify final Phase 1 PR hosted CI and record exact revision/run evidence.
- [ ] Product Owner accepts Phase 1; authorization of Phase 2 is a separate decision.

## Phase 2 — NOT STARTED / not authorized

Proposed next plan only: controlled public handoff review/provenance, actual
Contract v1 compatibility assessment, untrusted-input validation design, transactional
staged CourseRelease import and minimal protected/audited publication, synthetic
fixture integration and negative tests. Missing contractual/security decisions
must be resolved before implementation; never infer schemas or use private pilot
in public source/CI. Product identity/administration completion stays in its phases.

## Later owner decisions

Target markets/payment/store policies, hosting/regions, privacy/retention/voice
handling, recovery objectives, client support and content-version migration rules
must be settled before their relevant acceptance gates. Do not fabricate product
rules to unblock infrastructure work.
