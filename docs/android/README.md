# Phase 6 — Android: authoritative online scope

Product Owner authorized Phase 6 after merging accepted Web PR #10 on 2026-10-08.
Sources agree: [ROADMAP Phase 6](../../ROADMAP.md),
[public product direction](../architecture/product-direction.md), accepted
[Identity](../architecture/identity.md), [Learning Core](../architecture/learning-core.md),
[Web/voice policy](../web/README.md) and [API strategy](../adr/0003-api-strategy.md).
This consolidates existing client requirements, without adding pedagogical policy.

## Objective and complete scope

Deliver a native Kotlin/Jetpack Compose online client using the same account and
canonical backend learning state as Web. Separate presentation, application state
and network/platform adapters. Clients consume versioned domain API projections;
they never parse Course Packages or independently grade/unlock lessons.

In scope: email registration/sign-in, verification/recovery, Google integration
behind explicit provider configuration, preferences, session/device management,
fresh proof for password/link/deletion, account deletion and revocation handling.
Provide dashboard, course/chapter/lesson navigation, enrollment/release pinning,
advisory placement, explicit translation, supported activity presentations,
server evaluation, canonical mastery gates, replay, review and paginated history.
Preserve unknown/pending/not-applicable states. No invented numeric thresholds.

Support authenticated course images/audio, user-initiated microphone permission,
bounded record/play/delete and optional server-selected submission with separate
voice-1 consent. The accepted maximum twelve-calendar-month retention, processing
purpose, withdrawal and account-erasure policy applies equally to Android. No ML
training or automatic pronunciation evaluation is authorized. Bokmål is primary;
explicit UI localization does not translate learning content. Loading, empty,
offline/error, session-revoked and denied-permission states are required. Accessibility,
large text, scrollable/adaptive layouts, system back and lifecycle safety are part
of the client. Android-specific session protection must be reviewed/tested.

## Boundaries and dependencies

Dependencies: accepted Phase 0 safeguards; Phase 1 runtime; Phase 2 immutable
releases/provenance; Phase 3 accounts/revocable sessions; Phase 4 pinned learning
policies; Phase 5 stable media/dashboard APIs and storage reconciliation. Only
public-safe synthetic fixtures may enter source/tests/CI. Preserve Contract v1 bytes.

No expected product DB/schema changes: existing backend is authoritative. New
external surface is the Android app consuming existing versioned HTTP endpoints.
No importer, publication or admin HTTP is introduced. Native credentials must
never go to URLs, logs, backups or arbitrary hosts; clear account-owned UI/media
on logout, revocation and deletion. Free responses and microphone bytes are private.
Limit requests, replies and recording duration/size. Review rotation ambiguity,
cross-account responses, lifecycle cancellation, disk remnants, TLS/redirects,
permission denial and untrusted media decoding. Backend authorization remains
mandatory regardless of client behavior or client headers.

Out of scope: Phase 7 persistent content cache/downloads/offline attempts/sync;
Phase 8 gamification; billing, admin, release migration, user-data export, ML,
production deployment, signing/store publication and private pilot acceptance.
Do not invent later-phase account access or achievement balances.

## Acceptance gates

Complete online journeys and shared backend semantics; reproducible pinned toolchain
and verified wrapper/dependencies; unit/network/security tests, Compose/device
journeys, synthetic end-to-end account/learning/media coverage and accessibility
review. Run existing backend/PostgreSQL/migration/API, Web, Contract v1, receiving,
confidentiality, dependency/security/container and CodeQL regressions. Stable real
Android CI gates replace the pending gate. Never call skipped checks successful.
Exact-head hosted checks and Product Owner manual device review precede acceptance.

Live SMTP/Google acceptance remains mandatory before live provider operation;
mocked credentials/device tests do not close staging gates. Existing storage GC
must remain functional; actual remote bucket privacy/erasure, scheduled cleanup and
backups still need production acceptance. Export/admin/migration/license remain
pending. Adding an online native consumer does not authorize production providers.
Any unmet device/provider gate must be reported explicitly. Stop before merge and
before Phase 7.
