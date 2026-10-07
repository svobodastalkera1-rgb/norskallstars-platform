# 0012 — Versioned learning policies and release-pinned canonical progress

Status: Accepted engineering decision within authorized Phase 4; owner review pending
Date: 2026-10-06

## Context

Phase 4 Learning Core follows accepted Identity/immutable CourseRelease ingestion.
Owner's public-safe normative rules require linear mastery gates, advisory placement,
replaceable evaluators, release continuity and private account-lifetime learning data.
Contract v1 is an interchange format: completion/review/normalization extension objects
are not an approved platform algorithm. No pedagogical numeric defaults exist.

## Decision

Add a learning module and an explicit versioned platform LearningPolicy, separate
from the unchanged Course Package Contract. Scope each immutable rule set to an
immutable release and digest it. Require complete lesson/activity coverage, explicit
thresholds/normalization bindings/review intervals/assessment bands, and canonical-JSON
hash acknowledgment of every opaque package completion/review extension. The original
snapshot is retained; arbitrary extension keys are never interpreted as algorithms.
Unsupported semantics fail selection, not the existing generic package importer.

Trusted OS/DB operators select only already-published eligible releases/rules and
record approval/audit. No HTTP policy selection, course import/publication or media
endpoint is introduced. Existing enrollments pin both release and policy forever
unless future explicit safe migration tooling is authorized; current selection serves
only new enrollments. PostgreSQL composite FKs enforce matching course/release/policy.

Use the accepted Identity principal and account-before-session locking for every
learning transaction. Filter ownership before foreign row locking. Account deletion
cascades all enrollments/attempts/progress/events/placement in its existing transaction;
shared course/policy provenance is not personal data. Required responses/evaluations
are account-private, retained for account lifetime, never routine logs and exportable
later. No new deletion-retention exception or separate auth mechanism is introduced.

Separate evaluator and placement strategy interfaces from progress persistence.
Explicit exact/multiset comparison plus activity-bound normalization implements
local deterministic evaluation; rubric/external_future stay pending, none stays
not-applicable, self-assessment is explicit. Required gates cannot depend on an
unimplemented evaluator. No assumed Norwegian linguistic correction is added.

Canonical completion is sticky and earns credit once. Replays/review update current
mastery/history and explicit deterministic review scheduling without revoking previous
completion/unlocks. Placement acceptance allows recommended noncanonical practice,
never skipped completion/mastery or canonical prerequisite bypass. Versioned explicit
concept rules aggregate known lesson scores; unknown evidence never becomes zero.

## Alternatives

Inferring semantics from synthetic/pilot values would violate normative inputs.
Changing upstream schemas locally would invalidate the handoff. Numeric defaults or
latest-version reinterpretation silently change the product. Client-owned completion
or a second auth model breaks server authority. Introducing media delivery/remote
storage now requires the deferred production GC gate and is outside this design.

## Consequences

Real courses need owner-approved explicit learning policies; test policies are synthetic
examples, not production defaults. Bounded compatible selection limits lesson activities
to 200 and JSON snapshots to 8 MiB for the current runtime; larger content needs reviewed
resource-budget evolution, not disabled safeguards. Individual requests are 32 KiB;
history pages max100, open attempts max20 and account enrollments max100. Catalog/list
queries project summaries rather than load every snapshot. Scores use Decimal precision
and DB Numeric(30,28), independent of nine-place threshold precision; no percentage is
hardcoded. Future release migration, export, clients and premium/admin/media paths need
their separate scope/security review. Storage GC and live SMTP/Google gates remain open.
