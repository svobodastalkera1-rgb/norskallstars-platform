# Tasks

## Phase 0 ACCEPTED — closeout and remaining owner actions

- [x] Product Owner accepted Phase 0 review evidence and architecture decisions on 2026-10-03.
- [ ] Product Owner explicitly authorizes Phase 1. Until then, stop application work.
- [ ] Owner configures protected main and security settings; collect evidence
  without publishing credentials or operational details.
- [ ] License remains **Product Owner pending**; add no license and make no open-source claim.
- [ ] Owner arranges controlled public handoff of Contract v1, schemas,
  compatibility rules and approved synthetic fixture. No private repo browsing.
- [ ] Owner confirms server-side confidentiality incident/support status privately.

## Phase 1 — NOT STARTED / awaiting authorization

1. Select supported backend Python/framework/dependency versions from current
   official compatibility guidance. Pin dependencies with a reviewed lockfile.
2. Bootstrap modular FastAPI service, settings validation and isolated test harness.
3. Introduce PostgreSQL local/test service definitions, SQLAlchemy ownership
   boundaries and first reviewed Alembic migrations; no product data models yet.
4. Add structured safe logs, correlation IDs, liveness/readiness and error policy.
5. Define object storage interface with test doubles/local synthetic data support.
6. Add base request limits, restrictive CORS configuration and security test seams.
7. Activate real backend lint/type/test/security/build gates and Python SAST.
8. Update state with evidence, review unresolved decisions, request phase acceptance.

Web/Android builds, Course Package importer, users/authentication and production
services are outside Phase 1 except for documented integration seams.

## Later decisions — ask at the relevant phase

- Contract compatibility is determined by the real handoff, never inferred here.
- Account/session transport, Google integration configuration and privacy retention
  need identity-phase design and owner decisions where product/legal policy applies.
- Payment providers, target markets, permitted Android purchase flow, release
  audience and minimum Android support need explicit owner input/policy checks.
- Hosting region/provider, recovery objectives, data retention, voice handling,
  analytics and leaderboard display consent must be settled before acceptance.
- Pedagogical thresholds and content-revision migration rules follow the approved
  contract and owner decisions; do not fabricate missing rules.

Missing handoff blocks Phase 2 implementation, not Phase 0 or basic Phase 1 work.
