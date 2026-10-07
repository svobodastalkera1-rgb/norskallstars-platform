# Project state

Updated: 2026-10-07. Product: NorskAllstars. Platform: NorskAllstars Platform.
Phase 0: **CLOSED / ACCEPTED by Product Owner**.
Phase 1: **CLOSED / ACCEPTED by Product Owner; PR #4 merged**.
Phase 2: **CLOSED / ACCEPTED by Product Owner; PR #7 merged**.
Phase 3: **CLOSED / ACCEPTED by Product Owner; PR #8 merged**.
Phase 4: **CLOSED / ACCEPTED by Product Owner; PR #9 merged**.
Phase 5: **Web scope reviewed; conditional authorization, implementation stopped pending required voice/privacy policy**.
Phase 6: **NOT STARTED / NOT AUTHORIZED**.
Production readiness: **not achieved**.

## Actual implementation

Backend infrastructure now exists: FastAPI factory/lifespan, typed configuration,
async PostgreSQL/SQLAlchemy transaction/pool lifecycle, Alembic migration discipline,
liveness/readiness, safe structured logs/errors and request IDs/bounds, object
storage protocol/local development adapter, locked dependencies, local Docker
runtime and real backend/CodeQL CI definitions. Phase 2 now adds bounded generic package validation, immutable versioned
release persistence, idempotent staged import, asset references and audited
privileged publication. Phase 3 implements the Identity module: shared accounts, verification/recovery,
Google cryptographic proof validation, interface-language preference, revocable
opaque sessions and account/session ownership/deletion. Accepted Phase 4 adds
versioned learning policies, pinned enrollments, attempts/evaluation/progress/review,
advisory placement and authenticated curriculum/history/translation APIs.
Web/Android, sync/billing, production
infrastructure and Redis remain absent.

Runtime and decisions: docs/architecture/backend-runtime.md and ADRs 0008/0009.
Identity: docs/architecture/identity.md, ADR 0011 and docs/security/phase-3-review.md.
Migration 0003_identity adds seven identity tables without changing course tables.
Phase 2 import/publication remains operator-side; identity grants no administrative
roles or privileged HTTP course operations. Required secret keys have no defaults; production
configuration requires HTTPS identity links, explicit Google audiences and TLS SMTP.
Verification evidence: docs/phase-1-review.md. Initial Phase 1 PR runs passed
quality/tests/audit/container, Phase 0 safeguards and Python CodeQL. Each updated
PR head is verified separately; historical evidence does not substitute for it. Web/Android gates remain pending.

## Repository governance

Product Owner completed Protect main/security configuration after Phase 0:
active default-branch ruleset, PR-only development, linear history, deletion/
force-push restrictions, conversation resolution and Squash/Rebase merge methods.
Required approvals are 0; feature PRs still require Product Owner review and
must not be auto-merged. Seven required Actions checks are active with strict up-to-date branches: Bootstrap checks,
Security checks, Backend quality, Backend tests, Backend dependency audit, Backend
container and CodeQL Python. Verified through the ruleset API on 2026-10-04.

Owner confirmed private vulnerability reporting, dependency graph, automatic
submission, Dependabot alerts/security updates, malware alerts, secret scanning
and push protection enabled. CodeQL had been deferred pending actual runtime;
Phase 1 advanced Python CodeQL operates on main. Owner verified no alerts at
the acceptance point; this is a dated observation, not a perpetual guarantee. See docs/security/github-settings.md.

## Content and licensing

Contract v1 public handoff passed receiving: archive, dual inventory/checksums,
independent confidentiality/secret review, 7 schemas/23 refs, synthetic fixture
and 19 upstream tests. The 25 accepted files are byte-inventoried under
contracts/course-package/upstream; raw ZIP/transfer metadata remain local. No private corpus access or pilot import is authorized.
License remains **Product Owner pending**; no license is added and the project
is not announced as open-source.

Reachable public main was cleaned in the earlier confidentiality incident.
Server-side purge remains a separate support-review matter without confirmation
here. Do not recover removed private input or publish incident object identifiers.

## Known limitations / next step

This workspace's conflicting legacy/nft firewall rules block normal Compose
bridge traffic. Firewall protections were not changed; the built image was
validated using a loopback-only diagnostic container and host PostgreSQL.
Hosted Backend container checks exercise standard Compose independently.
Live deployed TLS/roles, production storage/delivery, release image scanning and
later domain security remain future work, not production-readiness claims.

Phase 1 acceptance reconciliation: GitHub confirms PR #4 merged into main at
03009f38b100731cc3ad375a941da3447bc6a9bb; all three main engineering workflows
completed successfully. Owner confirmed default-branch scanning healthy/no alerts.
No implementation is reopened; Phase 1 review evidence is historical.

Phase 2 acceptance reconciliation: PR #7 merged through the protected workflow
into main at fce1def7c805c59f4292fc20180c112c14bc2d61. Main backend, bootstrap
and CodeQL workflows completed successfully. Owner accepted the receiving,
contract, synthetic, confidentiality and clarification gates and confirmed healthy
code scanning/no alerts at review. Historical review records remain unchanged.
Never merge without Product Owner review. Future “Залил новый handoff,
продолжай работу” follows docs/corpus-integration/receiving.md and only resumes
already-authorized work. It grants no production/irreversible authorization.

## Mandatory deferred storage gate

Failed/ambiguous imports can retain private objects outside PostgreSQL transactions.
Committed DB state remains atomic; unmapped objects cannot automatically publish.
Owner accepts this operational limitation only for the current development phase.
Before production storage, remote persistent storage, media delivery, externally
reachable assets or production imports: implement and verify reconciliation,
retention and orphan GC, including in-flight protection, grace period, immediate
reference re-check, auditable deletion, safe retry and race/failure tests.
Accepted Identity/Learning Core introduce no storage/media delivery interface.
Phase 5 course audio/image delivery crosses this boundary: reconciliation,
retention and orphan GC are required before accepting that capability. No such
delivery/GC has been implemented or verified yet.

## Phase 3 acceptance and deferred identity gates

Product Owner accepted Phase 3 and its clarification/deferred gates. GitHub confirms
[PR #8](https://github.com/svobodastalkera1-rgb/norskallstars-platform/pull/8) merged
at 2026-10-04T23:00:27Z into main at
d03336a52559cf247e1fe3a7af3c33205d7c05ee. Its tree is byte-identical to accepted PR
head 0d731b9f661c922641ae1d714e5b17aa4a9ec091 (`git diff` is empty).
All 15 final PR checks succeeded. All seven required jobs on merged main succeeded:
[Backend](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/37242146348),
[Safeguards](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/37242146391),
[CodeQL](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/37242146312).
Owner reviewed Code Scanning/CodeQL UI and reported no blocking alerts at acceptance;
this does not assert perpetual absence of alerts. Historical docs/phase-3-review.md
remains unchanged, including its review-time status. No Phase 3 implementation is
reopened. No real Google/SMTP credentials or users are used in public tests.

Live SMTP delivery and live Google authentication have NOT been acceptance-tested
against configured staging infrastructure/providers. Both are explicit production
gates before their respective live capabilities. SMTP delivery remains at-least-once,
not exactly-once; staging must verify the documented retry/duplicate-delivery behavior.
Owner must configure and verify isolated staging providers/mail delivery. Client token
persistence/CSRF and OS-protected storage belong to Web/Android phases; administrator
MFA/RBAC to Phase 10. Wider privacy/unverified-account/financial retention decisions,
later-domain erasure hooks, worker scheduling/monitoring and key rotation remain
production gates. License remains pending.

## Phase 4 authority and normative rules

ROADMAP Phase 4 is Learning Core; sources agree. Product Owner supplied public-safe
normative rules after the scope review and authorized continuation. They are recorded
in [Learning Core](docs/architecture/learning-core.md): optional advisory placement,
evaluator-independent evidence, linear canonical mastery gates, release/policy-pinned
progress and account-lifetime private learning data erased with account deletion.
No default numeric pedagogical threshold is authorized; require explicit versioned
platform policy. Contract v1 bytes/semantics remain unchanged. Phase 4 is accepted
and merged; its design rules remain authoritative for the Web client.

Phase 4 implementation/review evidence: docs/phase-4-review.md and ADR 0012.
Migration 0004_learning adds eight learning tables; account-owned learning rows
cascade on account deletion. Ordinary Identity grants no import/publication/admin
permission. Compatible learning-policy selection fails closed without explicit
rules; there is no default pedagogical percentage. All 226 backend tests passed
against a fresh isolated PostgreSQL database; the Contract v1 suite passed 19/19,
strict typing, lint, schema drift, dependency audit and repository confidentiality
checks passed. All seven required hosted jobs and CodeQL analysis passed on
implementation commit
82188982e8ecbaab5b58cbde17114785bd3cb0f5 in PR #9. The subsequent evidence-update
head 17cc29bc3071e88d27385b744e8372d72fee72de also passed all seven required hosted
jobs and CodeQL analysis. These are historical implementation-time observations;
the post-merge acceptance evidence follows below.
Local Docker bridge routing blocks the containerized migrator in this workspace; the
supported host migration and complete backend test path both passed.

## Phase 4 post-merge acceptance reconciliation

GitHub confirms [PR #9](https://github.com/svobodastalkera1-rgb/norskallstars-platform/pull/9)
merged at 2026-10-07T08:17:59Z into main at
`9194c7c0ca8d67cb7936be8508ef6df029a03364`. The main tree equals accepted PR head
`351308a2f604266c7ebeffc2c4e1653188d22bfc` (`git diff` is empty).
Merged main workflows completed successfully:
[Backend CI](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/37592844028),
[Phase 0 CI](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/37592844092),
[Python CodeQL](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/37592844072).
Product Owner accepted the required checks, hosted CI, conflict and confidential
artifact review, and reported no blocking Code Scanning alerts at acceptance.
This is a dated observation, not a guarantee about later alerts. Historical
docs/phase-4-review.md and docs/security/phase-4-review.md remain unchanged.

## Phase 5 scope and decision gate

Sources agree on Phase 5 **Web**: ROADMAP, public product direction, Web direction
and accepted Identity/Learning Core contracts. Complete scope, dependencies and
acceptance gates are recorded in [Web direction](docs/web/README.md).
Product Owner conditionally authorized the phase. Voice purpose, local versus
submitted audio, retention and deletion are required decisions explicitly left
open by the product baseline/TASKS. Contract v1 supports speech activities but
does not define private learner audio storage; current learning HTTP accepts JSON
responses only. Do not invent a recording policy, change Contract v1 or silently
replace the full speaking journey with a local-only implementation. Await the
requested Product Owner decision before Phase 5 implementation.

Deferred gates remain open: live SMTP/Google staging acceptance and SMTP
at-least-once delivery verification; storage reconciliation/retention/GC; wider
privacy/retention and future data export; administrator MFA/RBAC; explicit safe
release-to-release progress migration; and Product Owner license selection.
Phase 5 activates storage GC for asset delivery and browser session/CSRF review;
live provider acceptance is required for any live-provider-dependent journey.
No Phase 5 runtime, provider acceptance, storage GC or Phase 6 work is completed.
