# Current engineering state

Updated: 2026-11-03. Product: NorskAllstars / NorskAllstars Platform.
This file records current facts and remaining gates. [ROADMAP](ROADMAP.md) owns
future scope; [TASKS](TASKS.md) owns actionable work. Implementation-time state
and completed task snapshots are preserved in the
[engineering memory archive](docs/reviews/engineering-memory-before-android-closure-2026-11-02.md).
Original phase reviews remain historical evidence, not current status.

## Licensing and future public showcase

Owner selected proprietary / All Rights Reserved licensing, copyright holder
Oleg Marikov, in [LICENSE](LICENSE). Public visibility supports source inspection,
portfolio review and technical evaluation; it grants no general reuse license.
Commercial/non-commercial use requires prior explicit written permission and
attribution when authorized, subject to applicable law and binding platform terms.
Third-party licenses/notices remain intact. Historical license-pending records
remain dated evidence, not current policy.

After the approved Experience redesign/integrated slice establishes the
production-facing visual direction, the public README MUST receive a curated
product showcase with representative Web and Android screenshots using public-safe,
Owner-approved material. Current
non-normative UI screenshots must not be substituted. This is a future documentation
acceptance requirement; it is not satisfied by the current synthetic review surfaces.

## Accepted implementation

Phases 0–6 are CLOSED / ACCEPTED by Product Owner: Bootstrap, Core Infrastructure,
Course Integration, Identity, Learning Core, Web and native Android.
GitHub confirms Owner squash-merged [PR #17](https://github.com/svobodastalkera1-rgb/norskallstars-platform/pull/17)
on 2026-11-02 at 17:40:15 UTC into main
`8a05b73c2b8ae5e04ce5d80982354e4c0906951a`.
The merged tree equals accepted head `b2e633db1ac6ef835464318a73895d41f2d43f4b`.
That pre-merge HEAD passed all 35 hosted checks and all eleven required checks,
including API 26/35 device runs, audits and Python/Web/Android CodeQL.
Post-merge and future PR runs are separate observations, not inherited acceptance.

Current main includes a FastAPI modular monolith, PostgreSQL/SQLAlchemy/Alembic,
immutable release import/publication, shared Identity, canonical Learning Core,
React/TypeScript Web and native Kotlin/Compose online Android. Both clients consume
versioned backend APIs. They do not interpret Course Packages or independently
award learning credit. Storage/media/retention/GC and consented selective recording
submission are implemented; production provider operation is not verified here.
No production deployment, private corpus import or production-user claim is made.

Android session protection, Guava toolchain remediation and sanitized instrumentation
diagnostics are merged. Historical API 26 instability has UNKNOWN root cause;
accepted final runs passed without weakening the gate. Diagnostic artifacts preserve
safe lifecycle/status evidence with seven-day retention; no blind retries or raw
private output publication. Android visuals are implementation evidence, NOT
normative precedent for the upcoming Experience redesign.

## Product and integration authority

- World & Experience Bible v1.0: NORMATIVE; exact bytes/index/SHA verification retained.
- Experience Contract v1.0: APPROVED / NORMATIVE; Corpus semantic review complete.
- Course Package Contract v1: unchanged; public upstream files remain inventoried.
- First integrated slice: **014 → 015 → 016 → REVIEW-02 → READING-02**.
  Contract-level **READY**. Owner authorized the Platform implementation on
  2026-11-03; the bounded implementation is provided for review in
  [PR #43](https://github.com/svobodastalkera1-rgb/norskallstars-platform/pull/43).
  Additional methodology gate (2026-11-09): **BLOCKED_BY_CONTRACT_GAP** for
  authored practice/world scope and episode starts. The public-safe Corpus proposal
  passed dedicated review intake; [Platform review](docs/experience/semantics-proposal-review-v1.md)
  recommends **ACCEPT_WITH_MINOR_CORRECTIONS**, not semantic approval.
  Implementation is paused; approved v1 contracts remain unchanged.
  Real Corpus handoff/integrated acceptance remain pending; no private repository
  access is authorized. See [Experience implementation](docs/experience/README.md).
- RetroCel is an optional future illustration provider/candidate, not a dependency.
- Phase 7 and later are NOT STARTED and require separate authorization.

The [normative product-world index](docs/product-world/README.md) owns authority
and provenance. [Learning Core rules](docs/architecture/learning-core.md) retain
linear canonical progression, explicit versioned thresholds, release pinning,
non-destructive replay, advisory placement and private account-owned learning data.
Local reading UX grants no canonical credit. No extra reading acknowledgement/
completion/unlock, voice registry or sidecar is authorized; EXP-REQ-011 remains
deferred outside normative Experience v1.

## Repository governance

Protect main uses PR workflow, linear history, deletion/force-push restrictions,
conversation resolution and strict up-to-date branches. Eleven required check
names were read from the active ruleset during this documentation pass; see
[CI reference](docs/ci.md). No settings were changed. Owner-controlled secret
scanning/push protection and private vulnerability reporting remain expected;
[settings evidence](docs/security/github-settings.md) distinguishes dated observations.
CodeQL operates for Python, Web and Android. Scans supplement review; they are
not perpetual assurances of no vulnerabilities or a production-readiness claim.

## Deferred production and Owner gates

- Live isolated staging SMTP delivery and Google authentication acceptance remain
  open; mocks are not provider acceptance. SMTP semantics are at-least-once.
- Storage reconciliation/retention/orphan GC is implemented and regression-tested.
  Before live remote storage/media/import: verify private bucket/IAM/TLS/encryption,
  anonymous denial, provider erasure, monitored cleanup/retention SLA, failures and
  backup erasure. Preserve in-flight protection, grace, reference re-check, audit
  and retry/race guarantees. Local test success does not close operational gates.
- Future user-data export, privacy/unverified-account/financial retention decisions,
  later-domain erasure hooks, credential/mail cleanup monitoring and key rotation
  remain open before the relevant capabilities. Account-owned learning/voice
  erasure and the twelve-calendar-month maximum voice retention remain binding.
- Privileged HTTP/admin requires real authorization and administrator MFA/RBAC;
  operator CLI assertions are audit intent, not authentication.
- Release-to-release progress migration requires explicit deterministic mappings;
  never infer mappings from title, order or position. Existing enrollments stay pinned.
- Manual TalkBack/text scaling, supported device/store policy, staging provider
  configuration, release signing/publication and wider cross-client release
  acceptance remain release gates; Android merge does not close them automatically.
- Hosting/regions, markets/payment/store rules, recovery objectives and
  production backup/restore acceptance remain Owner decisions. No open-source
  license, production deployment or later phase is authorized by documentation work.
- Earlier confidentiality incident server-side purge remains a separate private
  support matter without confirmation here. Never reconstruct removed private input.

## Immediate next task

Owner review of the documentation/portfolio pass. Before implementation, separately
authorize the approved Experience integration/slice and verify its controlled public
inputs. Do not start it, redesign clients or advance the roadmap automatically.

## First Experience Platform slice — current work

PR #42 is merged/accepted on main. This dedicated work reuses accepted Phases 0–6
and implements only the approved Experience first-slice projection/presentation
on Web and native Android using clearly synthetic data. No new roadmap phase,
Course Package change, migration, production provider or RetroCel dependency.
Exact-head checks and Owner cross-client visual acceptance remain review gates;
INTEGRATED_SLICE_COMPLETE is not claimed. Real Corpus handoff remains pending.
