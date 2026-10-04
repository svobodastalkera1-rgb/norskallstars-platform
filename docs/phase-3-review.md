# Phase 3 review evidence

Phases 0/1/2 are CLOSED/ACCEPTED. PR #7 was verified merged into current main at
fce1def7c805c59f4292fc20180c112c14bc2d61 before starting Phase 3. Main Bootstrap,
Backend and Python CodeQL workflows succeeded. Owner accepted Phase 2 required
checks, receiving/contract/synthetic/confidentiality gates and clarification;
observed healthy scanning/no alerts at review. Existing phase evidence is unchanged.

Authority: ROADMAP Phase 3 **Identity**, TASKS and public product direction accounts
section. Docs agree. Owner authorized Phase 3 subject to this reconciliation.
Implementation follows [identity architecture](architecture/identity.md),
[ADR 0011](adr/0011-shared-identity.md) and [security review](security/phase-3-review.md).

Delivered for review: validated `/api/v1/identity` and generated DTO/OpenAPI contract;
shared email/Google accounts, verification/recovery, preferences, rotating/revocable
sessions/devices, own-resource authorization and transactional identity erasure.
Migration 0003_identity adds seven tables; accepted course tables/contract bytes are
unchanged. Encrypted transactional mail queue has bounded private maintenance; no
HTTP operator jobs, course import/publication or media delivery are introduced.
No private corpus/provider credentials/user data or live external mail is used.

Local evidence (2026-10-04): 165 backend tests passed, including 83 new Identity
unit/integration/security tests and all 82 previous infrastructure/course/storage
tests. Full PostgreSQL migrations/drift/downgrade/re-upgrade, identity rollback,
crypto/provider failures, refresh replay/concurrency, IDOR, deletion/proof binding,
input limits, cancelled password work and encrypted mail leases/retry passed.
Nineteen upstream contract tests passed. The unchanged approved synthetic fixture
remains release-ineligible. Upstream RefResolver deprecation warnings are retained;
no received contract bytes or accepted test is weakened.
Ruff format/security lint, strict mypy and generated OpenAPI drift passed.
Locked runtime/dev audit found no known vulnerabilities. Twenty-four root safeguard/receiver tests and make check/security-check passed: exact
index and nine reachable commits were inspected, with no detected leaks. Private mail
(.eml) is now ignored and rejected even if forced into the index. Hosted exact-head
evidence is recorded after execution.

The image builds successfully. Standard Compose in this workspace hits the already
recorded bridge/firewall failure; safeguards/firewall are not altered. Current image passed loopback-only diagnostics: migrations, actual live/ready/identity
HTTP boundary, correlation IDs, packaged schemas, UID 10001, read-only/cap-drop and
no baked runtime key environment defaults. Hosted standard Compose is verified
separately; diagnostics do not substitute for a passing hosted Backend container job.

Mandatory Phase 2 orphan storage reconciliation/retention/GC remains visible in
PROJECT_STATE/TASKS/ROADMAP before production assets/import/storage. No such path is
introduced by Identity. Broader privacy/financial retention, future domain erasure,
client secure token persistence/CSRF, administrator MFA/RBAC, mail scheduling/key
rotation and live provider staging acceptance remain their explicit future gates.
License stays owner pending. Phase 3 needs Product Owner review; do not merge.
Phase 4 is NOT STARTED and requires separate authorization.

## Published review evidence

[PR #8](https://github.com/svobodastalkera1-rgb/norskallstars-platform/pull/8) is open;
not merged. Implementation HEAD 62b5a8a152aa2d394c8727d8cce2898ed0095680 passed
all 15 actual checks (seven required jobs for push/PR plus generated CodeQL):
[Backend PR run](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/37238976128),
[Safeguards PR run](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/37238976127),
[Python CodeQL PR run](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/37238976120).
Hosted standard Compose migration/startup/identity/runtime smoke succeeded despite
this workspace's local bridge limitation. Required job names remain unchanged.
Generated CodeQL succeeded; total repository alerts require owner UI verification
because this integration cannot read the full alerts API. No settings are changed.

These results apply to that exact implementation revision. Any subsequent head,
including evidence-only documentation updates, is separately checked and reported
in the PR; no inherited run substitutes for final-head acceptance. Review real Google/
SMTP staging setup, client persistence and deferred privacy/operations/storage gates
before their applicable milestones. Phase 3 remains awaiting Product Owner review.

Final contract/security refinement declares the actually required client header
in OpenAPI (not an authentication assertion) and filters session/proof ownership
before locking. A deterministic PostgreSQL test first reproduced a cross-account
revocation deadlock, then passed with both requests rejected and sessions intact.
The full regression suite is rerun; final-head hosted evidence belongs to the PR.
