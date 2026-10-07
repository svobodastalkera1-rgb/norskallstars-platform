# Phase 4 review evidence — work in progress

Phase 3 acceptance/merge is independently verified: PR #8 merged into main at
`d03336a52559cf247e1fe3a7af3c33205d7c05ee`, identical tree to accepted PR head
`0d731b9f661c922641ae1d714e5b17aa4a9ec091`. All seven required main jobs succeeded;
Product Owner accepted all15 final PR checks/Code Scanning UI. Historical Phase 3
review evidence remains unchanged. Phases 0–3 are CLOSED/ACCEPTED.

Phase 4 authority/scope/DoD: [Learning Core](architecture/learning-core.md), ROADMAP,
TASKS and public product direction. Sources agree. Owner supplied the missing
public-safe normative rules and authorized continuation. [ADR 0012](adr/0012-learning-policy-progress.md)
and [security review](security/phase-4-review.md) record the design/boundaries.

Implemented: explicit immutable LearningPolicy/provenance, operator-only selection of
already-published eligible release, pinned enrollments, linear canonical completion/
mastery gates, repeat/review without lost completion, typed deterministic/pending/
self-assessment/not-applicable evaluation, concept evidence, optional advisory placement,
private attempts/history/events and explicit translations. New authenticated Learning
API has 13 operations/11 paths; no privileged HTTP/media/production storage interface.
Migration 0004_learning adds eight learning tables and course/release composite identity
constraint. Personal learning records cascade in the existing account deletion transaction.
No upstream Contract/fixture bytes change, pilot assumptions or private access occur.

Local checks on 2026-10-07: all 226 backend tests passed against a fresh isolated
PostgreSQL test database, including the Phase 0–3 regressions and new learning tests.
The unchanged upstream Contract v1 suite passed 19/19. Ruff format, Ruff lint, strict
mypy, dependency audit (no known vulnerabilities), Identity OpenAPI byte identity,
generated Learning OpenAPI and platform policy schema checks passed. Root safeguards
passed all 25 tests; confidentiality and secret scans passed against the staged index
and reachable main history.

Docker image construction succeeded. This workspace's Compose bridge cannot connect
the migration container to PostgreSQL; the repository's host migration/test path passed.
For PR #9 implementation commit `82188982e8ecbaab5b58cbde17114785bd3cb0f5`, all
seven required jobs succeeded: [Backend CI](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/37589295536),
[Phase 0 CI](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/37589295655),
and [CodeQL Python](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/37589295686).
The CodeQL analysis check also passed. GitHub's alert-list API returned 403 for the
current integration, so this evidence does not assert an empty alert inventory; the
Product Owner should inspect the PR's Code Scanning view. Phase 4 remains unaccepted
until review and acceptance of the current PR head.

Live SMTP/Google staging acceptance, SMTP at-least-once semantics, mandatory production
orphan reconciliation/retention/GC and all later client/admin/privacy/operations gates
remain open. Real courses require owner-approved explicit versioned learning policy;
synthetic test numbers are not production defaults. No deployment, merge or Phase 5
is authorized. Phase 4 is not accepted and is not claimed ready before validation.
