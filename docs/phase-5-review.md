# Phase 5 — Web: implementation and pending review evidence

Updated 2026-10-07. **IMPLEMENTED / AWAITING PRODUCT OWNER REVIEW; not accepted.**
Authoritative sources agree on Web: ROADMAP Phase 5, TASKS, public product direction,
[Web scope](web/README.md), accepted Identity/Learning Core and Owner's voice policy.
The complete phase includes responsive accessible learning/identity/media/preferences/
dashboard journeys; no Android, ML, billing, admin, export or deployment is included.

## Reconciliation and Git state

PR #9 is merged; current observed main is 9194c7c0ca8d67cb7936be8508ef6df029a03364,
byte-identical to accepted Phase 4 head. Its merged Backend/Bootstrap/Python CodeQL
runs succeeded. Historical Phase 0–4 review evidence is unchanged.
Phases 0–4 are CLOSED / ACCEPTED. Feature branch: `feature/phase-5-web`.
[PR #10](https://github.com/svobodastalkera1-rgb/norskallstars-platform/pull/10) is open against
main; implementation commit is `1eb49b7571b8850a98f043dd52ae3e118eae7533`.
Implementation push runs passed Backend/Web/safeguards and Python/Web CodeQL.
Evidence-only revisions require their own exact-head checks. Do not merge.

Earlier sandbox restrictions denied Docker, PostgreSQL/GitHub network and `.git`
writes. On 2026-10-07, environment recovery verified Git metadata writes, Docker
build, local HTTP/threads, authenticated host/Compose PostgreSQL and external
registries/GitHub CLI. Two reversible project-scoped firewall rules resolved the
legacy/nft bridge conflict while preserving global DROP. This repair is local and
non-persistent. Complete local application regression subsequently passed; final
index review still precedes commit/push/PR. Hosted checks and Owner review remain separate.

## Implemented structure

- `apps/web`: React/TypeScript/Vite, Bokmål/English UI; typed generated client DTOs,
  memory session client, identity/account/session/fresh-proof/deletion and Google
  provider boundary, dashboard/course navigation, lesson/placement/history/translation,
  activity presentations, scoped media, microphone and retained-recording withdrawal.
- Backend `media`: private recording mappings/provenance, authenticated scoped
  assets, consented offers/uploads/withdrawal and private bounded reconciliation.
- Backend storage: inventory protocol, local and S3-compatible implementations,
  shared transaction writer coordination and exclusive orphan cleanup.
- Learning: private dashboard aggregate, nullable bounded engagement evidence and
  explicit optional presentation bindings in versioned PLATFORM policy. Legacy policy
  identity remains stable; upstream Contract v1 is not changed/interpreted in Web.
- CI: real Web quality/tests/dependency jobs and CodeQL JavaScript/TypeScript,
  preserving existing required backend/security/Python CodeQL checks. Android pending.
- ADR 0013: Web sessions, media/privacy, selective consent and coordinated retention.

No business identity/grade policy is duplicated in the client. Existing enrollments
remain pinned. Replay/placement do not manufacture completion. No numerical mastery
threshold, pilot IDs/counts, release migration or private data is introduced.

## Persistence and external interfaces

Migration 0005_media adds `media_recordings` (account/attempt cascade, unique offer
per activity, consent/selection/expiry/checksum/private key) and `storage_deletions`
(hash-only operational intent/outcome). 0006_learning_engagement adds nullable attempt
active seconds/sequence/timestamp and a DB nonnegative constraint. Old timing remains
unknown. Upgrade/downgrade/drift passed against the isolated PostgreSQL test database.

All new API paths require the accepted bearer/session model. Mutations also require
existing explicit-origin/client/JSON protections. Foreign resources return opaque errors;
no client account ID, `--actor` or approval assertion is an authorization boundary.

| Method | New path | Boundary |
| --- | --- | --- |
| GET | `/api/v1/learning/dashboard` | Own private aggregates, no answer bodies |
| POST | `/api/v1/learning/attempts/{attempt_id}/engagement` | Owned attempt, sequential/idempotent bounded evidence |
| GET | `/api/v1/media/enrollments/{enrollment_id}/lessons/{lesson_id}/assets/{asset_id}` | Own enrollment, release/access/declared asset and integrity |
| GET | `/api/v1/media/recordings` | Bounded own selected offers/retained mappings, no bytes/keys |
| POST | `/api/v1/media/recording-offers` | Owned speech attempt, separate explicit consent, server sampling |
| POST | `/api/v1/media/recordings/{recording_id}` | Owned selected offer, bounded opaque audio, checksum retry |
| DELETE | `/api/v1/media/recordings/{recording_id}` | Own withdrawal/reference erasure |

Built Web is public; all private backend resources remain authenticated. No privileged
HTTP import/publication/policy/GC or recording-download endpoint is introduced.

Voice defaults to disabled sampling. Selected audio is private, at most twelve
calendar months, erased with account deletion/withdrawal; no ML/training permission.
Failed writes can leave private unreferenced objects, with committed DB rollback intact.
GC expires mappings before storage operations, waits out participating writers, applies
grace/final reference checks and persists deletion intent independently before the side
effect. Physical erasure requires a scheduled, monitored worker/backups policy.

## Current checks: completed versus pending

| Check | Actual current observation |
| --- | --- |
| Web | Prettier, ESLint and strict TypeScript/Vite build passed; **16/16** unit/component tests passed |
| Full backend | **243/243 passed**, including PostgreSQL, ASGI, migration upgrade/downgrade/drift, races and previous phases; 122 upstream deprecation warnings |
| Ruff / strict mypy | Passed; 45 typed source files |
| Generated API/policy drift | Identity/Learning/Media OpenAPI and platform schema checks passed |
| Contract v1 | **19/19** upstream tests passed; approved upstream tracked bytes unchanged; upstream RefResolver deprecation retained without modifying inventoried artifacts |
| Receiving/bootstrap | **25/25** root tests passed, including hostile archive/inventory/confidentiality regression; final staged snapshot passed |
| Repository/index/history | Final staged make check and make security-check passed; exact index and current main/proposed reachable history scanned |
| Public candidate | Human public-file review and final exact-index confidentiality/Gitleaks scans passed; no ZIP/private corpus/credentials detected |
| Backend dependency audit | Current locked 91-package audit: no known vulnerabilities |
| Web dependency audit | Current npm lock: zero known vulnerabilities |
| Browser E2E/accessibility | **9/9 passed**, three cases each in Chromium (7.4s), Firefox (11.9s), WebKit (11.3s); canonical completion and lower-scoring replay, media/localization/keyboard/accessibility |
| Container | Final image built; Compose migrator/readiness and non-root/read-only runtime smoke passed |
| Hosted/required checks | Implementation HEAD `1eb49b7`: **23/23 successful checks**, all seven required names passed for push and PR events; evidence-only revisions require their own result |
| CodeQL | Python and Web analysis jobs and generated CodeQL results check succeeded; alert API returned 403, so absence of alerts is not asserted; Owner UI review required |

The backend test DB retained an earlier development schema: its migration-drift check
initially detected Numeric precision mismatch. Reset only guarded `norskallstars_test`
to base and reapplied current migrations; the full suite then passed without changing
accepted schema/tests. Browser projects now each reset only synthetic `web_test` state;
this avoids shared IP-rate bucket interference without altering runtime rate limits.

Tests add sampling/expiry/malformed audio/ownership/deletion races/storage rollback,
GC grace/in-flight/retry, private asset integrity, engagement idempotency/ownership,
policy identity/binding validation, insecure configuration, offline exact downgrade
SQL and S3/versioning boundaries. Web tests cover refresh/old-account responses,
resource limits/unsafe media, structured activities, microphone denial/teardown,
ambiguous upload withdrawal and Google-only fresh deletion proof. All previous tests
are preserved; endpoint/table inventory assertions extend to the new interfaces.

## Stable hosted check names and remaining actions

Keep required: Bootstrap checks; Security checks; Backend quality; Backend tests;
Backend dependency audit; Backend container; CodeQL Python, with strict up-to-date branches.
Once they genuinely pass on the Phase 5 PR, Owner can add: **Web quality**, **Web tests**,
**Web dependency audit**, **CodeQL Web**. No repository settings changed. Review both
advanced CodeQL categories; do not add a competing default-setup workflow.

Implementation is published through PR #10; all implementation-head hosted workflows
passed. Every evidence-only revision still requires actual exact-head results. Local
backend/browser/container/locked audit gates above have passed. Raw ZIP/private corpus/real media/user data must stay absent.
Stop before merge and Phase 6.

Owner manual acceptance: review responsive desktop/mobile/keyboard journeys, published
synthetic-policy navigation/placement/replay, unknown/pending evaluation, explicit
translations, record/deny/play/delete/consent/withdraw, Google-only/account deletion and
no browser persisted tokens. Provision isolated SMTP/Google/S3 privately and verify
live behavior; mocks cannot prove acceptance. Confirm sampling/purpose notice, cleanup
frequency/erasure/backups/operational alarms and private unversioned bucket configuration.

Still deferred: SMTP/Google staging acceptance and SMTP at-least-once semantics; real
S3/provider/cleanup operations, future privacy export, administrator authorization,
explicit release-progress migration, license and production release/operations gates.
No later roadmap phase or external deployment is started.

## Implementation-head hosted evidence

At `1eb49b7571b8850a98f043dd52ae3e118eae7533`, all 23 PR checks succeeded,
including duplicate push/PR jobs and the generated CodeQL results check. PR has
no merge conflicts; no merge/auto-merge is authorized. Completed PR workflows:

- [Safeguards](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/37677242414)
- [Backend](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/37677242748)
- [Web](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/37677242453)
- [Python and Web CodeQL](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/37677242635)

Hosted push logs independently confirm 243 backend tests, 19 upstream Contract tests
and all three isolated browser projects passed. Final evidence-only HEAD results
are reported in PR metadata and delivery; these implementation runs are not inherited
acceptance for later revisions. No GitHub settings were changed. Read-only API confirms
Protect main Active, seven required checks, strict up-to-date policy and no bypass actors.
Code Scanning alerts API is inaccessible to this integration (403); Owner must inspect
Python/Web results and blocking alerts in the GitHub UI.

## Limitations and next step

Tokens intentionally do not survive page reload. Audio remains opaque and is not
server-decoded/evaluated; maximum bytes and container signatures do not establish
safe decoder input. Inventory is bounded; versioned S3 buckets are unsupported and
rejected. Physical erasure depends on monitored operator cleanup and provider/backups
acceptance. The local Codespace firewall repair is reversible and non-persistent;
it is not published as application infrastructure.

Product Owner should review PR #10 and both CodeQL categories; verify the manual
journeys above, then make an explicit acceptance/merge decision. Phase 6 remains
NOT STARTED / NOT AUTHORIZED. No real corpus, pilot or inbound ZIP was read/imported
for Phase 5. Account/privacy/export, live SMTP/Google, storage operations, administrator
RBAC, release migration and license gates remain visible in TASKS and project state.
