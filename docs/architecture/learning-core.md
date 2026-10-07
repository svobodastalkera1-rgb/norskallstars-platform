# Learning Core — Phase 4 normative baseline

Authority: [ROADMAP Phase 4](../../ROADMAP.md), [public product direction](product-direction.md),
[TASKS](../../TASKS.md), and Product Owner's public-safe Phase 4 decisions on 2026-10-04.
Phases 0–3 are CLOSED/ACCEPTED; PR #8 is merged at
`d03336a52559cf247e1fe3a7af3c33205d7c05ee`. Phase 4 is authorized; Phase 5 is not.
These rules are public platform requirements, independent of private corpus/pilot content.

## Objective and complete scope

The backend owns the canonical learning behavior shared by future Web/Android:
structured course/chapter/lesson navigation, versioned activities, deterministic
advisory placement, evaluation, mastery/review, attempts, progress and learning events.
It consumes immutable Contract v1 releases and accepted Identity sessions. Applicable
prerequisites, explicit translation requests, historical version identity and unlimited
review of completed material are part of the direction. Language preferences never
translate lesson content automatically. Progress is account-private.

Out of scope: Web/Android clients, offline/sync, gamification, billing/entitlements,
Admin UI/MFA/RBAC, ML/LLM/adaptive canonical paths, production deployment/private import,
actual user export, media delivery/production storage and automatic pronunciation scoring.
Retain exportable identity/version/attempt/result/response/timestamp data for a later export.
Course import/publication remains operator-side; ordinary accounts receive no such privilege.

## Normative Product Owner decisions

Placement is optional and advisory. It uses an authenticated learner, published
release, explicit versioned assessment/rules and responses; returns recommendation,
score where applicable and rule provenance. A learner may accept it or start at the
beginning. It never grants skipped completion/mastery, deletes earlier access or
rewrites canonical progress. Keep a replaceable strategy boundary; no ML is required.

Evaluation supports `deterministic`, `rubric`, `self_assessment`, `none` and
`external_future`. Deterministic grading needs explicit answers/rules; normalize only
under explicitly bound activity flags. No broad linguistic correction is authorized.
Rubric/external evaluation can remain pending; self-assessment needs explicit learner
confirmation. Instructional `none` is not scored. Preserve raw/normalized responses,
result, evaluator/version/provenance and timestamps when needed for learning history.
An external evaluator must be replaceable and cannot become a core-engine prerequisite.

The canonical path is linear with completion/mastery gates. Thresholds come from
versioned course metadata or separate public platform policy where supported; there
is **no hardcoded/default pedagogical percentage**. Completed lessons allow unlimited
replay without additional canonical completion credit or loss of previous unlocks.
Completion means required conditions satisfied; mastery means its applicable threshold
satisfied; review is subsequent interaction and lower review scores cannot revoke
canonical completion. Unknown, not evaluated, not applicable, zero and false remain
distinct. Persisted evidence/versioned rules determine progress, never client claims.

New enrollments use the explicitly selected published release. Started enrollments
stay pinned to their original release/policy; publishing/selecting a new version does
not reinterpret history. Migration is explicit, deterministic and requires a safe
mapping. Never infer mappings from title, position or array index. Unmapped progress
remains on its original release. Preserve a migration boundary for future tooling.

Learning state is private user-owned data. Keep only progress/evaluation/history,
cross-device continuity and necessary support/security/audit evidence. Retained
responses belong to the user/release/lesson/activity/evaluator and may contain personal
information. Never log answer bodies or disclose another learner's data. Retain
required records for account lifetime; account deletion erases learning data in the
accepted deletion transaction. No indefinite retention exception is invented. Individual
progress/history deletion and actual export are not Phase 4 features. Persist at least
release identity, progress/completion, attempts/results/responses and timestamps to
support future export.

Canonical progress remains independent of recommendation/evaluator engines. Future
adaptive strategies may suggest practice, pacing, review or placement, but cannot
silently rewrite canonical progress. Content IDs and release provenance come from
Contract v1, never provisional pilot properties.

## Integration design and boundaries

Platform LearningPolicy is a separately versioned artifact scoped to one immutable
release; it is not a Course Package schema modification. Every lesson/activity must
have explicit compatible rules. Required numeric thresholds, review intervals,
normalization bindings and placement bands have no implicit product defaults.
Synthetic tests supply explicit synthetic policies; they do not set production values.
A real course needs owner-approved versioned policy before selection/enrollment.

Contract `completion`/`review` extension objects remain untouched. The platform policy must explicitly acknowledge the exact SHA-256 of every
non-null object as opaque input. It provides the complete authoritative platform
rules separately; there is no interpretation of arbitrary extension fields.
Missing, stale or extra acknowledgments reject learning selection. They
remain valid for generic Phase 2 import. Unknown normalization flags or ambiguous
prompt/choice objects require explicit supported bindings/presentation in platform
policy. Do not guess a pilot's object shapes or silently redefine upstream fields.
Missing required Contract capability would stop for a minimal reviewed Contract change.

Expected data: immutable policy/provenance and selected release; account-owned
release-pinned enrollment, attempts/results, progress/review, events and placement
results. Use PostgreSQL constraints and consistent Identity account/session locking;
deletions cascade in the account transaction. Preserve immutable snapshots and all
Phase 0–3 safeguards. New interfaces use accepted bearer Identity, server ownership,
revocation/deletion checks, strict bounded inputs, abuse limits and opaque errors.
No client user ID, actor/approval assertion or client header is authorization.

Content projections distinguish selected published curriculum from staged content,
hidden answers/internal metadata and user state. Course instances remain authenticated/
access-controlled despite the public format. Media references are IDs only: no object
keys, URLs or stored bytes are exposed. Placement acceptance can guide noncanonical
practice; it cannot bypass linear canonical gates. Replays retain one canonical
completion, independent of later practice/review accuracy.

## Definition of Done and acceptance gates

Complete the full scope above with explicit policies and deterministic acceptance
examples. Require real unit/domain, PostgreSQL/migration/drift/rollback/concurrency,
API/OpenAPI, ownership/cross-account, revocation/deletion-race, input/resource/abuse,
privacy/logging and synthetic end-to-end tests. Preserve all Phase 0–3, Contract v1
and receiving/handoff regressions. Ruff, strict mypy, make check/security-check,
dependency audit, container sanity, all seven actual hosted required jobs and CodeQL
must pass at the exact PR head. State/docs must describe actual implementation.
Product Owner reviews before merge. Do not start Phase 5.

Live staging SMTP/Google acceptance remains open before its production gate; SMTP
is at-least-once. Mocks do not verify live providers. Mandatory orphan reconciliation/
retention/GC applies before any production/remote storage, media delivery, externally
reachable stored assets or production import: inventory/DB references, in-flight
protection, grace, immediate re-check, auditable deletion, retention, safe retry and
race/failure tests. No such path is in the current learning design. Client security,
administrator MFA/RBAC, wider privacy/operations and license decisions remain in TASKS.

## Implemented HTTP inventory

All methods below use `/api/v1/learning`, accepted bearer authentication and own-account
session checks. POST also requires `X-NorskAllstars-Client` and JSON. No caller supplies
an authorization user ID. Foreign/unknown owned resources return the same opaque 404.

| Method / path suffix | Behavior |
| --- | --- |
| GET /courses | Bounded selected published-course summaries |
| POST /enrollments | Idempotently enroll own account on current selected release/policy |
| GET /enrollments | Bounded own enrollment summaries, without loading all snapshots |
| GET /enrollments/{id} | Pinned curriculum/progress, concept evidence and rule provenance |
| GET /enrollments/{id}/lessons/{lesson} | Available/completed or recommended-practice lesson projection; hidden fields omitted |
| POST /enrollments/{id}/attempts | Start canonical/practice attempt with operation ID; enforce linear gates |
| POST /attempts/{id}/submit | Evaluate required/optional submitted activities; atomic progress/history/events; exact repeats idempotent, changed repeats 409 |
| POST /enrollments/{id}/history | Cursor-bounded own attempts/results/responses; foreign cursor 404 |
| GET /enrollments/{id}/review | Completed lessons due under explicit versioned schedule |
| GET /enrollments/{id}/placement | Optional versioned assessment projection, without answers |
| POST /enrollments/{id}/placement | Idempotent advisory score/recommendation and provenance; no completion credit |
| POST /enrollments/{id}/placement/{result}/accept | Record own recommendation for noncanonical practice; linear gates remain |
| POST /enrollments/{id}/translations | Explicit supplied reference_text lookup and idempotent learning event |

Curriculum/text is plain content; clients must not execute HTML/JavaScript in it.
Raw assessment/attempt responses remain potentially sensitive owner data. Account deletion
cascades every personal learning row. Required unit evidence is the mean of explicitly
required scored activity results, with binary exact/multiset matching or explicit
self-assessment. Unscored required activities can complete only under explicit acknowledged
conditions without score/mastery gates. No future evaluator is required for core progress.
Policy concept rules explicitly list lesson evidence; missing scores are unknown, never zero.
Review intervals, success threshold and reset/retain behavior are explicit policy inputs.
