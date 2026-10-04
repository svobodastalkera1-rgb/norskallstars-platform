# Project state

Updated: 2026-10-04. Product: NorskAllstars. Platform: NorskAllstars Platform.
Phase 0: **CLOSED / ACCEPTED by Product Owner**.
Phase 1: **CLOSED / ACCEPTED by Product Owner; PR #4 merged**.
Phase 2: **CLOSED / ACCEPTED by Product Owner; PR #7 merged**.
Phase 3: **AUTHORIZED — Identity; implementation prepared for Product Owner review on a feature branch**. Production readiness: **not achieved**.

## Actual implementation

Backend infrastructure now exists: FastAPI factory/lifespan, typed configuration,
async PostgreSQL/SQLAlchemy transaction/pool lifecycle, Alembic migration discipline,
liveness/readiness, safe structured logs/errors and request IDs/bounds, object
storage protocol/local development adapter, locked dependencies, local Docker
runtime and real backend/CodeQL CI definitions. Phase 2 now adds bounded generic package validation, immutable versioned
release persistence, idempotent staged import, asset references and audited
privileged publication. Phase 3 implements the Identity module: shared accounts, verification/recovery,
Google cryptographic proof validation, interface-language preference, revocable
opaque sessions and account/session ownership/deletion. Learning engine, Web/Android,
sync/billing, production infrastructure and Redis remain absent.

Runtime and decisions: docs/architecture/backend-runtime.md and ADRs 0008/0009.
Identity: docs/architecture/identity.md, ADR 0011 and docs/security/phase-3-review.md.
Migration 0003_identity adds seven identity tables without changing course tables.
Phase 2 import/publication remains operator-side; identity grants no administrative
roles or HTTP course operations. Required secret keys have no defaults; production
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
Phase 3 Identity is authorized; Phase 4 is not authorized. Never merge without
Product Owner review. Future “Залил новый handoff,
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
Phase 3 Identity introduces none of those paths; the gate remains mandatory.

## Phase 3 review and deferred identity gates

Feature implementation is not owner acceptance or a production deployment. Exact
local/hosted evidence is recorded in docs/phase-3-review.md and the PR. No real
Google/SMTP credentials or users are used in public tests. Owner must configure and
verify isolated staging providers/mail delivery before live operation. Client token
persistence/CSRF and OS-protected storage belong to Web/Android phases; administrator
MFA/RBAC to Phase 10. Wider privacy/unverified-account/financial retention decisions,
later-domain erasure hooks, worker scheduling/monitoring and key rotation remain
production gates. License remains pending. Phase 4 is NOT STARTED/awaiting authorization.
