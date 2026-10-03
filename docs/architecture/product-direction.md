# Public engineering direction

This is a public-safe engineering baseline, not the private Product Owner source
document or a copy of it. The current owner instructions settle product naming
and Phase 0 boundaries. Production v1.0 remains the intended complete release.
Change product requirements only with owner approval; resolve absent details at
the phase that needs them.

## Learning and clients

- Norwegian Bokmål is the primary interface language and learning language.
  Design localization from the start; changing interface language must not
  automatically translate lesson content. Optional supplied translation is
  explicitly requested by the learner and recorded as a learning event.
- Curriculum is structured, with course/chapter/lesson navigation and applicable
  prerequisites. Placement is deterministic and advisory. Rendering and activity
  evaluation use the approved Course Package semantics, not embedded real lessons.
- Recognition, constrained answers and open responses must be representable when
  supported by Contract v1. Do not promise automatic grading of every activity.
  Evaluators, mastery and review scheduling remain deterministic domain components.
- Audio playback and illustrated lessons must work on both clients. Speaking
  workflows handle permission, recording, playback, deletion and submission where
  supported; automatic pronunciation scoring is not a v1.0 promise.
- A completed lesson can be repeated while preserving canonical completion and
  unlocked progress. Record attempts and applicable learning events without
  unnecessary personal data. Historical progress stays tied to content versions.
- Dashboard direction includes course/lesson location, continuation, progress,
  review needs, learning time, suitable accuracy statistics, achievements and
  account access status. Both clients deliver the core learning journey.
- Responsive Web and native Android must be accessible. Client separation keeps
  presentation away from domain/data rules. Document deliberate platform differences.

## Accounts and access

- One account serves Web and Android, with email/password and Google sign-in,
  verification, recovery, preferences and revocable sessions/devices.
- Resource ownership and paid-content access are checked server-side. Protect
  media delivery without claiming that a user-authorized asset is impossible to copy.
- Self-service account deletion includes session invalidation and defined
  deletion/anonymization, with lawful financial retention designed before release.
- Voice, telemetry and account data require purpose, minimization, retention and
  deletion decisions. Never emit sensitive payloads into routine logs.

## Offline and content evolution

Android needs both automatic cache and explicit downloads with bounded storage,
cleanup and removal, offline media and activities, and reconnect behavior. Stable
operation identifiers, retry/deduplication, partial failures, content versions and
conflict outcomes must prevent silent progress loss. Canonical backend state
and retained historical records must survive repeated submissions/course updates.

## Gamification, billing and administration

XP, levels, streaks, achievements and a privacy-conscious leaderboard accompany
learning without blocking it. There is no social network or lives/pay-to-continue
mechanic. The persistent free tier and premium monthly/yearly plans use a central
account entitlement model; a trial is not required. Billing adapters isolate
providers/markets from learning rules. Promotions support discounts or timed
access with eligibility, expiration, limits and replay/race protection. Verify
current store/payment rules for chosen markets before selecting purchase flows.

Administration is operational rather than a curriculum authoring CMS. It covers
accounts, access/subscriptions/promotions, course releases/publication, statistics,
flags, status and audited actions. Privileged operations require strong separate
authorization, MFA/RBAC and appropriate session/re-authentication policy.

## Delivery and acceptance

Packages are untrusted until structural/security/schema/checksum/compatibility
and semantic checks succeed. Import must be transactional and staged; publication
is explicit, authorized and audited. The approved synthetic fixture is the first
integration evidence. Owner-supplied private pilot acceptance comes later and
must never enter public source, CI, job output or downloadable artifacts.

Production needs PostgreSQL migrations, durable object storage, HTTPS, safe
logging, monitoring/alerts, error tracking, health checks, dependency audits,
validated recovery and controlled staging-to-production promotion. Performance
budgets cover bounded payloads, media use, realistic data and query behavior.
Test critical domain rules, ownership/premium/admin bypass, unsafe import/upload,
replayed promotion/sync operations and complete cross-client journeys.

Google Play readiness requires current target API, signing, permissions, account
removal, privacy/Data Safety and market-specific billing evidence. Re-check live
policies at release; no store rules or legal assumptions are frozen by bootstrap.

No ML/LLM dependencies, adaptive teaching, generated runtime curriculum/media,
automated ML scoring, social messaging or user-generated public content are in
v1.0. Keep extension seams without constructing an ML platform.

The [roadmap](../../ROADMAP.md) and final acceptance evidence retain the full
production direction. Empty skeletons or a synthetic demonstration cannot close
production acceptance.
