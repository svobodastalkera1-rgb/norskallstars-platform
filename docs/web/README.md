# Phase 5 — Web: authoritative scope and decision gate

Scope reviewed on 2026-10-07; implementation awaits required Product Owner voice
policy. This document consolidates existing requirements; it introduces no new
product rule. Sources agree:

- [ROADMAP Phase 5](../../ROADMAP.md): responsive accessible client, core learning,
  audio/images, microphone flows, dashboard, preferences and localized interface.
- [Public product direction](../architecture/product-direction.md): Bokmål-first
  UI, explicit translations, speaking permission/record/play/delete/submit where
  supported, dashboard direction and voice privacy decisions.
- [Accepted Identity](../architecture/identity.md) and
  [Learning Core](../architecture/learning-core.md): canonical authentication,
  account ownership, progress, placement, evaluation and release continuity.
- [API boundary](../api/README.md), ADRs
  [0003](../adr/0003-api-strategy.md), [0009](../adr/0009-object-storage-boundary.md),
  [0011](../adr/0011-shared-identity.md) and
  [0012](../adr/0012-learning-policy-progress.md), plus
  [security baseline](../security/README.md) and
  [confidentiality](../security/confidentiality.md).

## Objective and complete in-scope capabilities

Deliver the production-oriented responsive accessible React/TypeScript learning
client against stable backend API contracts. Implement account sign-in/registration,
verification/recovery, Google integration, preferences, session management and
self-service deletion using accepted Identity. Browser token persistence/refresh,
CSRF/origin policy and sensitive fresh-proof flows require explicit security review;
no localStorage token persistence has been approved.

Implement course/chapter/lesson navigation, enrollment and pinned-release
continuation, optional advisory placement, lesson activities, server evaluation,
canonical completion/mastery gates, replay, review, private attempts/history and
explicit available translations. The backend decides access and progress. Preserve
unknown, pending and not-applicable results; never fabricate mastery or evaluate
answers using client copies of accepted answers. Clients consume domain/API
representations, not Course Package files or provisional pilot assumptions.

Support course audio playback and images, and microphone permission, recording,
playback, deletion and submission where supported by the approved voice policy.
Include permission denial, unsupported capability and playback/recording errors.
Automatic speech/ML evaluation is outside the production v1.0 promise.

Provide dashboard location/continuation, progress, review needs, learning time and
applicable accuracy statistics from server evidence, plus account/preferences
journeys. Achievements and paid access arrive in their authoritative later phases;
do not invent balances, awards or entitlements. Build explicit UI localization with
Bokmål primary; changing UI language never automatically translates lesson content.
Accessibility, responsive layouts, bounded requests and clear loading/empty/error/
revoked-session states are part of the complete client, not later demo polish.

## Boundaries and expected changes

Dependencies are accepted Phase 0 safeguards, Phase 1 runtime/storage boundary,
Phase 2 immutable validated releases/provenance and eligibility, Phase 3 Identity,
and Phase 4 policies/progress. Only approved public synthetic fixtures enter tests.
No private corpus repository, real pilot, raw handoff ZIP or private policy is used.

Expected external interfaces are the Web UI, existing versioned Identity/Learning
APIs, and bounded authenticated course-media delivery. Any necessary API projection
must preserve compatibility, ownership and backend domain authority. Exact new
endpoint paths require design and OpenAPI drift tests; none are implemented here.
No privileged import/publication/policy selection is exposed to ordinary accounts.

Expected backend changes include safe media access and transactional storage
reference/reconciliation support, with migrations where persistence is needed.
Private audio storage and its persistence model depend on the pending voice policy.
Avoid new learner state that merely duplicates canonical backend progress.

Review authentication, object ownership, cross-account/session isolation, resource
limits, enumeration, input/output leakage, origin/CSRF/XSS/token exposure, concurrency,
idempotency and logging for each new interface. No learner response/audio, credential
or token enters routine logs or public artifacts. New private data requires explicit
retention, deletion/account-erasure and exportability semantics.

Out of scope: native Android (Phase 6), offline/sync, gamification, entitlements/
billing, Admin UI/MFA/RBAC, ML/LLM, release-progress migration implementation,
actual privacy export, production deployment/publication and private pilot acceptance.
Keep deferred export/migration/admin gates visible; no silent scope reduction.

## Activated gates and Definition of Done

Course-media delivery makes the previously deferred storage gate mandatory:
reconcile inventory with committed references, protect active imports, require a
grace period and immediate pre-delete reference re-check, audit deletion, define
retention, retry safely and test races/failures. No media capability can be accepted
until this is implemented and verified. Browser session security is now in scope.
Live SMTP/Google-dependent journeys require configured staging provider acceptance;
mocks do not close that gate, and SMTP remains at-least-once.

DoD is the complete in-scope client and necessary backend boundaries, resolved
voice policy, reproducible development/build, reviewed API contracts/migrations,
privacy/account-deletion behavior, meaningful unit/component/browser/E2E and
accessibility tests, media/ownership/security/race tests, updated documentation and
successful hosted checks at the exact PR head. Required existing checks remain
Bootstrap checks, Security checks, Backend quality, Backend tests, Backend dependency
audit, Backend container and CodeQL Python. Add real stable Web quality/test/build/
dependency checks and JavaScript/TypeScript code scanning when runtime exists;
ask Product Owner to add appropriate real check names to the ruleset.

Run all backend/PostgreSQL/migration/OpenAPI, Contract v1, receiving/handoff and
confidentiality regressions, Ruff, strict mypy, dependency audits, container checks,
CodeQL, `make check` and `make security-check`. Test cross-account and revoked-session
behavior, replay/pinning/placement semantics, keyboard interaction and sensitive
browser storage/network behavior. Do not weaken old tests or claim synthetic/mock
provider tests prove production acceptance. Deliver a feature PR; stop before merge
and before Phase 6.

## Required Product Owner decision — voice policy

Product direction requires purpose, minimization, retention and deletion decisions
for voice; TASKS leaves voice handling pending. Contract v1 identifies `speech`
responses but does not define learner recordings or their storage. Existing learning
submission accepts bounded JSON, with no binary upload or recording lifecycle.

Product Owner must determine whether recordings remain local to the browser or
are privately submitted as activity responses. For submission, define purpose,
retention and deletion, including individual recording and account deletion.
Generic account-lifetime JSON-response retention must not silently become an audio
collection policy. Do not extend Contract v1 or substitute local-only speaking
without approval. Implementation is stopped until this required decision is supplied.
