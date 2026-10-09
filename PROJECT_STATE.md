# Project state

Updated: 2026-10-09. Product: NorskAllstars. Platform: NorskAllstars Platform.
Phase 0: **CLOSED / ACCEPTED by Product Owner**.
Phase 1: **CLOSED / ACCEPTED by Product Owner; PR #4 merged**.
Phase 2: **CLOSED / ACCEPTED by Product Owner; PR #7 merged**.
Phase 3: **CLOSED / ACCEPTED by Product Owner; PR #8 merged**.
Phase 4: **CLOSED / ACCEPTED by Product Owner; PR #9 merged**.
Phase 5: **CLOSED / ACCEPTED by Product Owner; PR #10 merged**.
Phase 6: **Android IMPLEMENTED locally / awaiting publication, hosted checks and Owner review**.
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
Phase 5 Web/media is accepted and merged; its dated implementation evidence remains below.
Phase 6 now implements native Kotlin/Compose online account/learning/dashboard/
media/microphone journeys against existing APIs. Keystore-protected sessions,
account-generation isolation, lifecycle controls and bounded consented media are
implemented. No new product schema/migration/HTTP endpoint or offline sync is added.
Final device/hosted/Owner acceptance remains pending; sync/billing, production
infrastructure and Redis remain absent.

Runtime and decisions: docs/architecture/backend-runtime.md and ADRs 0008/0009.
Identity: docs/architecture/identity.md, ADR 0011 and docs/security/phase-3-review.md.
Migration 0003_identity adds seven identity tables without changing course tables.
Phase 2 import/publication remains operator-side; identity grants no administrative
roles or privileged HTTP course operations. Required secret keys have no defaults; production
configuration requires HTTPS identity links, explicit Google audiences and TLS SMTP.
Verification evidence: docs/phase-1-review.md. Initial Phase 1 PR runs passed
quality/tests/audit/container, Phase 0 safeguards and Python CodeQL. Each updated
PR head is verified separately; historical evidence does not substitute for it. Web has passing accepted/merged-main hosted runs. Android now has real workflow definitions; its exact-head hosted results remain pending.

## Repository governance

Product Owner completed Protect main/security configuration after Phase 0:
active default-branch ruleset, PR-only development, linear history, deletion/
force-push restrictions, conversation resolution and Squash/Rebase merge methods.
Required approvals are 0; feature PRs still require Product Owner review and
must not be auto-merged. Eleven required Actions checks are active with strict up-to-date branches: Bootstrap checks,
Security checks, Backend quality, Backend tests, Backend dependency audit, Backend
container, CodeQL Python, Web quality, Web tests, Web dependency audit and CodeQL Web.
Verified through the branch-rules API on 2026-10-09; no settings changed.

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

The Codespace previously blocked normal Compose bridge traffic through conflicting
legacy/nft firewall rules. On 2026-10-07, two reversible local rules restored only
same-project PostgreSQL forwarding; the global legacy DROP policy remains intact.
Authenticated SELECT 1 now passes both from the host and from the Compose network.
The local repair is not persistent across host/network recreation; ignored repair
and rollback tooling records the exact rules. This is environment recovery, not
application/container acceptance. Hosted Backend container checks remain separate.
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
retention and orphan GC are required before accepting that capability. Delivery/GC implementation and PostgreSQL race/failure regressions passed locally.
Implementation-head hosted verification passed; later exact-head checks and Owner
review remain separate. Live provider privacy/erasure,
cleanup scheduling/monitoring and backups remain explicit production gates.

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

## Phase 5 historical implementation and validation evidence

Authoritative scope: **Web**, defined by ROADMAP, public product direction and
[Web requirements](docs/web/README.md). Owner authorized implementation and accepted
selective speaking-recording collection with separate consent, an explicit processing
purpose, maximum twelve calendar months and account-deletion erasure. This supersedes
the earlier indefinite-retention request. ML implementation/training is not authorized.
Accepted Identity/Learning Core erasure and pinned policy/release semantics remain intact.

Feature branch: `feature/phase-5-web`, based on accepted main 9194c7c.
[PR #10](https://github.com/svobodastalkera1-rgb/norskallstars-platform/pull/10) contains
implementation commit `1eb49b7571b8850a98f043dd52ae3e118eae7533`.
Phase 5 implementation includes a React/TypeScript client, memory-only bearer sessions,
identity/fresh-proof/preferences/session/deletion journeys, learning/placement/replay/
history/translation UI, private media/recordings, dashboard and engagement evidence.
ADR 0013 records the consequential session/media/storage decisions.
Migration 0005_media adds recording mappings and hashed-object deletion audit;
0006_learning_engagement adds nullable attempt engagement evidence without reinterpreting
legacy attempts. Platform presentation bindings are optional explicit versioned rules;
legacy policy digests are preserved. Upstream Contract v1 artifacts are unchanged.

Storage inventory, S3-compatible adapter and coordinated bounded GC are implemented
in the working tree. Shared writer/exclusive cleanup PostgreSQL locks, final reference
re-checks, grace, committed expiry and durable deletion intents protect reference
integrity. Complete local PostgreSQL/race, browser and final container regressions
passed locally and on the implementation-head hosted run. Later exact-head checks
and Owner acceptance remain separate. Live
provider/erasure and scheduled operations remain production gates; no production
import, provider or deployment runs.

Earlier environment restrictions interrupted application checks. Recovery on
2026-10-07 restored Git/Docker/network/threads/PostgreSQL. Complete regression now
passes: the browser fetch receiver and downgrade naming defects have focused tests;
current-head tests cover both. Browser journeys also verify canonical completion
survives lower-scoring replay. Independent browser projects use reset synthetic
Web-test data, preserving ordinary runtime rate limits. See [Phase 5 evidence](docs/phase-5-review.md).
Implementation commit/PR are published. All 23 implementation-head checks passed, including seven required checks; every later
PR head requires separate hosted verification. This describes the earlier review point; Phase 5 acceptance follows below.

Production gates remain: isolated live SMTP/Google acceptance (SMTP at-least-once),
private S3/TLS/encryption/anonymous-denial and cleanup scheduling/monitoring/backups,
future privacy/export, administrator authorization, deterministic release migration,
license/market/retention/recovery decisions. No earlier gate is silently closed.
Phase 6 was not authorized at that review point. Current authorization follows below.

Initial completed local evidence: **243/243 backend**, **16/16 Web unit/component**,
**9/9 browser E2E/accessibility** across Chromium/Firefox/WebKit, **19/19 upstream
Contract v1** and **25/25 repository/receiving** tests passed. Ruff, strict mypy (45
source files), generated API/policy drift and Web format/lint/build passed. Final
Compose image build, migration and non-root/read-only runtime smoke passed. Locked
backend audit (91 packages) and npm audit reported no known vulnerabilities. Final
staged index/history confidentiality and redacted secret checks passed before commit.
Implementation-head hosted verification passed all 23 checks. Evidence-only updates
require separate exact-head verification; Owner review remains pending. CodeQL Python
and Web analysis succeeded; alert API returned 403, so Owner must review scanning UI.

## Phase 5 manual-review follow-up — 2026-10-08

Owner reported a usable Web/learning UI and accepted the artificial synthetic
content boundary; Phase 5 remains NOT ACCEPTED pending the follow-up. The displayed
time intentionally includes only submitted active attempts, rounded down to minutes;
idle/hidden/unsubmitted time is excluded. The notice now states update/rounding
semantics. The primary smoke seed omitted the explicit matching presentation binding,
so the client correctly failed closed but the course could not finish. Corrected
versioned test-only browser policy adds that binding; upstream Contract artifacts,
production runtime learning rules and immutable existing enrollments are unchanged.
New regressions cover heartbeat activity/idle/hidden/retry behavior, dashboard
submission/rounding and completion of both synthetic lessons. Correction validation:
245/245 backend, 24/24 Web component/unit, 9/9 E2E across Chromium/Firefox/WebKit,
19/19 Contract and 25/25 repository/receiving regressions passed. Ruff/strict mypy,
API/policy drift, Web format/lint/build, locked dependency audits and container
build/migration/runtime smoke passed. Exact correction-head hosted evidence belongs
to PR #10 metadata/delivery and must not be inferred from historical runs.
All existing deferred production gates above remain open; no merge or Phase 6.

## Phase 5 closure and Phase 6 authorization — 2026-10-08

Product Owner completed manual Web review, accepted the synthetic content boundary
and existing submitted-active-time semantics, merged PR #10 and authorized Phase 6
according to the authoritative roadmap. GitHub confirms merge at
2026-10-08T20:39:01Z: `8100927bf4717d15dfa112254c4b6acd76dccaae`.
The merged tree equals accepted correction head
`af952422215984facab7022f187e265332e36bf0` (empty diff). Merged-main
[Backend CI](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/37841026175),
[Web CI](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/37841026251),
[Safeguards](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/37841026238) and
[CodeQL](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/37841026143)
completed successfully. Historical review records are not rewritten.

Phases 0–5 are CLOSED / ACCEPTED. Phase 6 Android is authorized; Phase 7 is not.
Scope: [Android](docs/android/README.md). Work proceeds from this merged main through
a dedicated feature branch. No private corpus access, production deployment, store
publication or automatic merge is authorized. All deferred production gates remain
open, including live SMTP/Google, SMTP at-least-once semantics, private storage/erasure
operations, privacy/export, administrator authorization, explicit progress migration
and license. No production acceptance is inferred from synthetic tests.

## Phase 6 implementation and review gates — 2026-10-09

Feature branch: `feature/phase-6-android`, based on current origin/main 8100927.
Scope and DoD: [Android](docs/android/README.md); [ADR 0014](docs/adr/0014-native-android-online.md).
[Implementation evidence](docs/phase-6-review.md) and
[security review](docs/security/phase-6-review.md) distinguish dated regression runs,
final native results and unresolved hosted/device/provider gates. Native unit tests
passed 19/19, Lint and debug/test APK plus unsigned R8 release builds passed.
OSV audited 312 locked app/test/lint/buildscript coordinates with no known findings.
Contract v1 upstream files are unchanged. The final real-backend API 35 device gate passed 3/3 with no skips, including
Activity recreation, canonical/replay/placement and account/session/media erasure.
Final repository/receiving regressions passed 29/29; index/reachable-history
confidentiality and redacted secret scans passed. API 26 and hosted Android/CodeQL
checks remain pending; Phase 6 is not accepted. No feature branch
publication or PR has occurred yet. Phase 7 is NOT STARTED / NOT AUTHORIZED.

The Codespace restart removed temporary SDK/JDK caches. Verified official toolchain
archives restored local builds. The existing named PostgreSQL volume was preserved
when recreating its failed stopped container metadata; authenticated loopback DB
access passed without new firewall changes. Only the guarded Android synthetic DB
was reset. Owner manual-review data was not reset. Emulator/build work is serialized
on this two-CPU environment; previous process failures are not hidden as green tests.
