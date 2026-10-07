# Production roadmap

NorskAllstars targets Production v1.0. An internal milestone is not a substitute
for release acceptance. Phases 0–4 are CLOSED/ACCEPTED (Learning Core PR #9 merged).
Phase 5 Web is authorized under Owner-accepted voice/privacy policy.
Every phase needs design, implementation, meaningful tests, security review,
documentation, and a state update. Foundational failures block downstream work.

| Phase | Outcome and acceptance direction | Status |
| --- | --- | --- |
| 0 — Bootstrap | Public monorepo boundaries, ADRs, project memory, developer setup, confidentiality controls and honest CI gates | CLOSED / ACCEPTED by Product Owner |
| 1 — Core Infrastructure | Backend skeleton, validated configuration, PostgreSQL migrations, structured logging, health, test support, storage interface and basic security policies | CLOSED / ACCEPTED by Product Owner |
| 2 — Course Integration | Integrate approved Contract v1 and synthetic fixture; validate untrusted packages, create versioned staged releases and authorized audited publication | CLOSED / ACCEPTED by Product Owner |
| 3 — Identity | Shared accounts, email and Google sign-in, verification, recovery, session/device revocation, authorization and account deletion lifecycle | CLOSED / ACCEPTED by Product Owner; PR #8 merged |
| 4 — Learning Core | Structured curriculum, versioned lessons/activities, deterministic placement/evaluation/mastery/review, attempts, progress and learning events | CLOSED / ACCEPTED by Product Owner; PR #9 merged |
| 5 — Web | Responsive accessible client with core learning, audio/images, microphone flows, dashboard, preferences and localized interface | IMPLEMENTED / AWAITING PRODUCT OWNER REVIEW; not accepted |
| 6 — Android | Kotlin/Compose client, shared semantic learning behavior and online API integration with platform-specific UX | Not started |
| 7 — Offline / Sync | Android cache/downloads, local persistence, offline media/attempts, version-aware idempotent sync and explicit conflict handling | Not started |
| 8 — Gamification | XP, levels, streaks, achievements and privacy-conscious leaderboard independent of learning availability | Not started |
| 9 — Entitlements / Billing | Account-wide free/premium access, monthly/yearly plans, promotions and payment adapters with verified market/platform policies | Not started |
| 10 — Administration | Operational admin UI with MFA/RBAC, user/account/access management, releases, flags, statistics and audited actions | Not started |
| 11 — Production Hardening | Threat model, authorization/privacy/dependency audits, performance/failure tests and demonstrated backup recovery | Not started |
| 12 — Operations | Observability, alerts, error tracking, deployment/runbooks, backup restoration and rollback | Not started |
| 13 — Release Candidate | Staging RC, critical cross-client E2E and supported browser/device/OS validation | Not started |
| 14 — Private Corpus Acceptance | Owner-supplied private pilot used only in controlled private acceptance; sanitized evidence covering content, media, release versions and publication | Not started |
| 15 — Google Play / Production | Approved production Web delivery and signed Android release, store/privacy/policy evidence and operational readiness | Not started |

Phase 2 must include a minimal protected release-publication path. Phases 3 and
10 later complete identity and the operational UI; do not defer staged release
safety until Phase 10 or assume anonymous administration is acceptable.

## Release acceptance

Backend, Web and Android must operate as one system. Acceptance includes the
learning/account journey, synthetic and private-pilot integration, cross-device
progress, loss-resistant Android offline reconciliation, complete gamification,
selected-market billing, secured administration, accessible clients, operational
recovery, and current Google Play compliance. Critical/high security findings
block release unless the owner explicitly accepts a documented risk.

Required journeys include account verification through lesson completion and
sync; synthetic import through staging/publication and authorized access; and
Android offline completion followed by reconciliation. Production cannot be
announced without evidence for the full direction in
[product direction](docs/architecture/product-direction.md).

Phase 4 scope and normative policies are recorded in
[Learning Core](docs/architecture/learning-core.md). This baseline preserves the entire
phase; it does not defer placement/mastery/review to later phases or narrow scope.
Identity acceptance does not close live SMTP/Google staging acceptance. Those checks
remain mandatory before their respective production-readiness gates. SMTP delivery
is at-least-once and must be verified with that delivery model.

ML/LLM learning, adaptive curricula, generative production content, social feeds,
and hearts/lives gating are outside v1.0. The roadmap is not an MVP cut-down.

Mandatory production storage gate (accepted Phase 2 deferral): before any production
object storage/media delivery, externally reachable assets, remote persistent
storage or production imports, implement and verify orphan reconciliation/retention/GC
with in-flight protection, grace period, immediate reference re-check, auditable
deletion, safe retry and race/failure tests. It belongs to the first phase that
introduces these paths and must be satisfied by Production Hardening/Operations
in all cases; accepted Identity and Learning Core introduce none. Phase 5 course
media delivery crosses the asset-delivery boundary and must close this gate.
See [Web scope and receiving dependencies](docs/web/README.md).
