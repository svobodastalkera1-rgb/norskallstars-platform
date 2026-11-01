# Corpus ↔ Platform Experience Reconciliation v1

Status: reconciliation for **APPROVED / NORMATIVE EXPERIENCE CONTRACT v1**.
Updated: 2026-11-01. [Product Owner approval](experience-approval-2026-11-01.md)
closes semantic review; implementation and the approved first slice have NOT started.
Historical correction date: 2026-10-31. [Accepted Corpus semantic findings](corpus-semantic-review-2026-10-31.md)
resolve the earlier reading/speaker questions. Original receiving/validation evidence
below remains dated historical evidence, not a new review or current implementation claim.
Date: 2026-10-15. Bible v1.0 remains normative. This document preserves the
independence of authored requirements and current technical capability.

Historical local verification: 2026-10-17. GitHub main/Android facts below were
rechecked unchanged. `make check` passed all **49 repository/tooling tests**, of
which **27 receiving tests** cover the unchanged Course Package and new Experience
paths. New Python tooling/tests passed Ruff lint/format. `make security-check`,
exact-index confidentiality/hash verification, Bible working/index verification
and `git diff --check` passed. The current SHA-bound candidate was received again
successfully. No backend/Web/Android runtime suites were rerun for this tooling/
design-only change; no new hosted CI run is claimed or publication authorized.

## 1. Evidence, receiving and scope

Sources: Product Owner-approved public-safe Corpus Requirements v1.0.0 (received
2026-10-15; candidate identity and receiving evidence recorded below),
[accepted semantic review](corpus-semantic-review-2026-10-31.md),
[Bible](world-experience-bible-v1.md), and implementation evidence in the public
[learning DTO](../../apps/backend/src/norskallstars_backend/learning/dto.py),
[learning service](../../apps/backend/src/norskallstars_backend/learning/service.py),
[media boundary](../../apps/backend/src/norskallstars_backend/media/service.py) and
[Contract v1 schemas](../../contracts/course-package/upstream/specification/platform-contract/v1/README.md).
The authoritative capability scan remains preserved in local source commit
`15c0cd6836e471b738cba9001cb386b22b70c2c0`; this focused documentation PR does not
publish that earlier analysis/tooling branch. Relevant capability distinctions are
retained in the matrix below. Historical checks/receivers on those local branches
are evidence, not a claim they are delivered by this documentation-only PR.

Historical GitHub snapshot, verified 2026-10-17: main `5669565dea726313ec2cf07d3d4f14ce3a825137`.
At that snapshot Android PR #17 was OPEN/unmerged at
`1317521dff118001d87beb700131d67945c813a9`. All Android implementation assessments
below refer to **UNMERGED_CANDIDATE**, never MAIN. MAIN has no Android runtime;
FUTURE_REQUIRED means adaptation/acceptance after its authoritative baseline is
resolved. No client code is copied into this branch.

Candidate: `norskallstars-experience-review-2026-10-15.zip`, 5,389 bytes,
SHA-256 `ad2edf3a4a68b332f28230360f76c1d0103f20d84448ed008396868a19226c9e`.
The existing Course Package receiver correctly rejected its structure. The separate
Experience receiving path on preserved local commit `6b728549a05bd7d91e1447ee199fe43cd7cb6937`
then verified Git boundary, bounded archive, fixed structure, manifest discriminator,
all inventory/checksums, typed payload, independent review of all four text files,
and pinned redacted Gitleaks. Two unchanged public-safe payload files were accepted in that local receiving
work; ZIP/transfer metadata are excluded from this publication PR. This proves public transfer
integrity, not private repository installation, Corpus Bible byte equality,
pedagogical/content acceptance or Experience Contract approval.

The candidate internally says review/proposed. Owner approval of its public-safe
handoff permits this analysis; producer labels are retained, not upgraded. The
received bundle itself supplies neither private units nor their IDs. The sequence
`014 → 015 → 016 → REVIEW-02 → READING-02` is the Owner's approved first-slice sequence,
not a runtime identity mapping or permission to obtain those units.

## 2. Complete requirement matrix

Each row separates package representation, stored domain, safe API and client.
Platform status describes end-to-end MAIN support; authoring-only runtime work is
NOT_APPLICABLE. Slice column is the producer flag, not a newly inferred priority.
Android is ABSENT on MAIN for every runtime row; the column assesses only its
UNMERGED_CANDIDATE. Candidate support does not count as delivered main support.

| ID / name | Priority; slice; runtime; clients | Platform | Course Package v1 | Backend domain / API projection | Web MAIN | Android candidate | Gap classification | Disposition | Corpus semantic disposition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EXP-REQ-001 Recurring character identity | REQUIRED; yes; no; BOTH | NOT_APPLICABLE | NOT_APPLICABLE: authored identity rendered in media/dialogue | NOT_APPLICABLE: no runtime registry needed | SUPPORTED as approved images/text; not authoring tooling | SUPPORTED as rendered content | NO_GAP for runtime | KEEP authoring-owned identity; do not transfer private registry | FULLY_PRESERVED |
| EXP-REQ-002 Recurring location identity | REQUIRED; yes; no; BOTH | NOT_APPLICABLE | NOT_APPLICABLE: approved media/content carry continuity | NOT_APPLICABLE: no geographic registry | SUPPORTED rendered locations | SUPPORTED rendered locations | NO_GAP for runtime | KEEP continuity in authoring | FULLY_PRESERVED |
| EXP-REQ-003 Scene-local continuity | REQUIRED; yes; no; BOTH | NOT_APPLICABLE | SUPPORTED ordered authored blocks; registry NOT_APPLICABLE | NOT_APPLICABLE scene-state API | SUPPORTED explicit textual/visual facts; not an entity simulation | SUPPORTED same | NO_GAP for runtime registry | KEEP scene/prop/time/weather constraints outside runtime | FULLY_PRESERVED |
| EXP-REQ-004 Illustration as comprehension support | REQUIRED; yes; yes; BOTH | PARTIAL | SUPPORTED image block/asset/alt, activity stimulus_refs | Domain SUPPORTED immutable media refs; API PARTIAL: ActivityView omits stimulus_refs | PARTIAL: block images work; activity-bound media absent | PARTIAL: same projection limitation | API_PROJECTION_GAP; CLIENT_COMPOSITION_GAP | BRIDGE safe stimulus projection and scoped activity rendering | FULLY_PRESERVED |
| EXP-REQ-005 Thumbnail and image enlargement | REQUIRED; yes; yes; BOTH | PARTIAL | SUPPORTED image, optional dimensions; no UI encoding needed | Domain SUPPORTED asset; API PARTIAL dimensions absent | PARTIAL static bounded image, no inspection overlay | PARTIAL downsampled/height-bound image, no inspection UI | CLIENT_COMPOSITION_GAP; API_PROJECTION_GAP | EXTEND accessible inspection, optional safe dimension projection | FULLY_PRESERVED |
| EXP-REQ-006 Clear role speech and transcript | REQUIRED; yes; yes; BOTH | PARTIAL | SUPPORTED existing attribution, audio/transcript/text associations; internal notes are not display labels | Domain stores content; API PARTIAL safe transcript/association projection | PARTIAL audio playback; accessible association/projection work remains | PARTIAL same projection/client work | API_PROJECTION_GAP; CLIENT_COMPOSITION_GAP | BRIDGE safe existing attribution/text/audio association; no new labels or registries | FULLY_PRESERVED |
| EXP-REQ-007 Ordered scenes and visual callbacks | DESIRABLE; yes; yes; BOTH | PARTIAL | SUPPORTED ordered blocks, activity_ref, returning approved media | Domain SUPPORTED order/references; API SUPPORTED block activity_ref, no new scene entity | PARTIAL all activities follow all blocks | PARTIAL same separation | CLIENT_COMPOSITION_GAP | BRIDGE sequence-preserving composition; no callback registry | FULLY_PRESERVED |
| EXP-REQ-008 Chapter presentation in learning order | REQUIRED; no; yes; BOTH | SUPPORTED functional order, PARTIAL experiential composition | SUPPORTED chapter identity/order/lesson_refs/prerequisites | Domain/API SUPPORTED ordered chapters and authoritative availability | SUPPORTED chapter/list; visual evolution needed | SUPPORTED candidate chapter/list | DESIGN_SYSTEM_GAP; CLIENT_COMPOSITION_GAP | KEEP rules/order; EVOLVE through EXTEND presentation only | FULLY_PRESERVED |
| EXP-REQ-009 Reading as continuous prose | REQUIRED; yes; yes; BOTH | PARTIAL presentation; no new progression semantics required | SUPPORTED existing ordered prose/image/audio; no additional reading state/gate required | Existing Learning Core policy/progress remains authoritative; API SUPPORTED blocks | PARTIAL prose composition/local UX, not canonical completion | PARTIAL normal lesson text; native reading UX future | CLIENT_COMPOSITION_GAP | BRIDGE prose presentation; KEEP existing availability/progression, no additional authored acknowledgement or state | RESOLVED by accepted correction |
| EXP-REQ-010 Responsive and accessible reading/media | REQUIRED; yes; yes; BOTH | PARTIAL | SUPPORTED alt/text/order; presentation NOT_APPLICABLE | Domain SUPPORTED content; API PARTIAL safe transcript associations | PARTIAL existing responsive/focus/native controls, new inspection/composition unverified | PARTIAL native semantics, new inspection/scaling unverified | CLIENT_COMPOSITION_GAP; API_PROJECTION_GAP; DESIGN_SYSTEM_GAP | EXTEND acceptance-tested interactions, not neutralize art direction | FULLY_PRESERVED |
| EXP-REQ-011 Standalone optional reading identity | DESIRABLE; no; yes if later authorized; BOTH | ABSENT distinct kind, not needed now | Existing lesson/review units suffice for slice; distinct reading kind absent | No new reading entity/API required for v1 | No distinct kind needed for slice | No distinct kind needed for slice | COURSE_PACKAGE_GAP_CANDIDATE only for separately required future feature | DEFER outside normative v1 surface; NOT_REQUIRED_FOR_VERTICAL_SLICE | NOT_REQUIRED_FOR_VERTICAL_SLICE; deferred |

The accepted Corpus review found nine FULLY_PRESERVED requirements (001–008/010),
009 AMBIGUOUS before correction and 011 not required for the first slice. The table
now records 009 RESOLVED, retains all nine preserved meanings and defers 011.
Semantic preservation does not mean runtime capability gaps have been implemented.

SUPPORTED means the named technical capability exists, not artistic or live-provider
acceptance. Authoring-only rows are required Corpus constraints, not rejected
requirements. There is no reason to build private entity management in Platform.
Row 008's original requirement remains REQUIRED outside the first slice; its slice
flag false is not permission to remove chapters or linear gates.

## 3. Layer ownership map

| Concept | Layers genuinely needed | Excluded layers / reason |
| --- | --- | --- |
| Character/location identity; props/wardrobe/weather/light; local scene facts | AUTHORING_ONLY; PUBLIC_HANDOFF contains generic requirements only | No entity registry in COURSE_PACKAGE/BACKEND_DOMAIN/API_PROJECTION: 001–003 explicitly say not runtime |
| Versioned approved asset, block, chapter, activity identity/order | COURSE_PACKAGE → BACKEND_DOMAIN → allowlisted API_PROJECTION → CLIENT_PRESENTATION | No private production identifiers or renderer instructions |
| Image as assessment stimulus | COURSE_PACKAGE stimulus_refs → BACKEND_DOMAIN snapshot → API_PROJECTION safe authorized refs → CLIENT_PRESENTATION | No new generated media pipeline or renderer dependency |
| Readable transcript / existing authored attribution | COURSE_PACKAGE existing attribution/text/audio association → safe API_PROJECTION → CLIENT_PRESENTATION | No new speaker label or voice registry; never expose raw speaker_notes, answer keys, internal QA or full metadata |
| Reading composition / authored sequence | PUBLIC_HANDOFF behavior agreement; COURSE_PACKAGE existing blocks/order → safe API_PROJECTION → CLIENT_PRESENTATION | No presentation_intent annotation; reading composition/local state never selects canonical completion/mastery |
| Canonical completion, mastery, access/replay, release pinning | BACKEND_DOMAIN explicit versioned policy → API_PROJECTION → CLIENT_PRESENTATION | No ornamental state, colors, timing or renderer in domain |
| Inspection dialog, cinematic frame, ornament, illumination/motion | CLIENT_PRESENTATION / design system | No new course or domain fields for triangles, amber, animation or viewport |
| Reading availability versus progression versus local UX | Existing content references/authorization and Learning Core availability; existing BACKEND_DOMAIN progression; non-authoritative CLIENT_PRESENTATION state | No extra authored acknowledgement/completion/unlock rule unless authoritative data explicitly supplies it; no inference from scrolling or opening |

## 4. Revisit scan gaps without promoting speculation

- **Chapter artwork:** not required by 008 (identity/title/order/prerequisites).
  DEFER new bindings/endpoints. Bible permits future artwork; no slice blocker.
- **Activity-specific media:** explicitly required where applicable by 004.
  Existing stimulus_refs and media authorization suffice for storage/access;
  project only safe references and render them. No package evolution identified.
- **Scene grouping/interleaving:** 003 keeps scene registry authoring-only; 007
  uses ordered blocks and explicit content transitions. Preserve activity_ref
  position in clients. No new scene/arc/callback schema justified.
- **Audio roles:** 006 requires intelligible role speech/transcript, not a voice
  registry, dialogue sequencer, synthesis provider or ambience mixer. Accepted
  Corpus findings confirm existing attribution and text/audio association suffice.
  No new role label/voice infrastructure; never expose internal speaker_notes.
- **Safe projections:** required for stimulus refs/transcripts and potentially
  dimensions/existing public attribution. Authorize against pinned release,
  lesson availability and owning account; never return raw immutable package JSON.
- **Wardrobe/weather/light/props:** identity production concerns, not runtime
  fields. **Ambience/RetroCel:** no incoming requirement; remain deferred.

## 5. Course Package gap register

| Candidate | Missing semantic / why Experience alone cannot supply it | Minimal possible future change | Slice effect |
| --- | --- | --- | --- |
| CP-C01, EXP-REQ-011 | Distinct reading runtime unit kind; a sidecar hint cannot make `kind: reading` valid under the closed lesson/review enum | Separately reviewed optional reading kind plus validator/import/API compatibility if Owner requires independent kind; no schema drafted here | NOT a blocker: 011 explicitly not first-slice; ordered reading inside existing valid unit works |

EXP-REQ-011 is NOT_REQUIRED_FOR_VERTICAL_SLICE and excluded from normative
Experience v1. CP-C01 is retained only as a conditional future planning candidate,
not a present contract blocker. Requirements 004–010 use existing approved package
semantics and Learning Core rules; safe projections/client work remain future work.
No new speaker annotation or reading schema is required. No change to Course
Package v1 files, validator, fixture or flexible extension semantics.

## 6. First-slice dependencies and acceptance

Contract-level readiness for 014 → 015 → 016 → REVIEW-02 → READING-02: **READY**.
The accepted minor correction resolves the only contract ambiguity; no mandatory
Course Package v1 change is required. Product Owner approved the contract on
2026-11-01. Separate implementation/content/client gates below remain; READY is not runtime
readiness, Corpus adoption or authorization to start the slice.

The Owner sequence is a planning label only. Exact release/unit IDs, source content
and media are not available here; do not infer IDs from numbers, titles or order.
Future public tests remain synthetic. Actual private slice delivery/acceptance must
use a separately authorized private operational environment, never this repository.

| Dependency | Classification | Layer / acceptance evidence |
| --- | --- | --- |
| Final Owner contract approval | COMPLETE, explicit 2026-11-01 decision | Normative v1; separate implementation authorization is still required |
| Exact valid unit/release mapping and approved selected media, from authorized handoff | BLOCKER before actual integrated-content acceptance | COURSE_PACKAGE/content operations; no source content imported in this task |
| Existing identity, pinned enrollment, canonical gates, replay, immutable releases | REQUIRED; already implemented on MAIN | BACKEND_DOMAIN/API; preserve ownership, rollback, pinning and replay regressions |
| Safe activity stimulus projection and context rendering | REQUIRED where selected activities use stimuli | API/Web; alt and authorized scoped image/audio, no cross-account access/key leakage |
| Inspectable image with return focus / native back and readable detail | REQUIRED | Web and FUTURE_REQUIRED Android; keyboard, screen reader, text scale, touch, error/loading tests |
| Accessible speech text and speaker context where authored | REQUIRED | API/client; source-to-transcript fidelity, no internal notes, speech clarity checked by Owner |
| Ordered text/media/activity composition and explicit translation | REQUIRED; translation backend already implemented | Client/profile; preserve author order, on-demand translation and answer privacy |
| Continuous reading; existing availability/progression; non-authoritative local UX | REQUIRED meaning resolved; no additional contract-level policy blocker | No extra Corpus acknowledgement, completion state or mandatory unlock gate unless explicitly in authoritative data; zero fabricated mastery, preserve replay |
| New persistence/domain tables | DEFERRED; no requirement established | Immutable snapshots and existing policy/state sufficient unless approved profile later proves otherwise |
| Course Package revision / distinct reading kind | DEFERRED; not slice blocker | CP-C01 separate decision only |
| Cinematic Nordic composition, reading density, concentrated exercise, feedback/ornament | REQUIRED for visual slice acceptance | DESIGN_SYSTEM/client; real screenshots, responsive states, reduced motion, contrast/focus preserved |
| Chapter artwork/milestone artwork, ambience | DESIRABLE Bible expression; DEFERRED new runtime semantics | No incoming requirement establishes required media bindings |
| Android baseline and corresponding native adaptation | BLOCKER for combined Web+Android acceptance; Web design may proceed separately only if authorized | Resolve PR #17 independently; compact/modern-phone evidence and native lifecycle/back/IME tests |
| Asset size/delivery budget, safe dimensions and scoped storage | REQUIRED | Existing full-blob delivery limit 10 MiB; measure image/audio bandwidth and decoding on mobile; no unrequested remote provider |

Backend/domain work should be zero new learner tables in the minimal path; explicit
compatible existing policy bindings and safe DTO mapping remain the baseline.
No additional reading policy is inferred from the correction. Future API projections
require OpenAPI/client drift checks and no raw notes/answers/metadata. No annotation
sidecar or mapping lifecycle is required by v1; pinned releases/progress stay intact.

Required evidence before integrated acceptance: synthetic end-to-end ordered lesson
and reading paths; correct/incorrect/selection/completion/replay; availability and
cross-account tests; transcript/translation distinction; missing/corrupt/oversized
media; responsive Web and native evidence; keyboard/screen reader/text scaling;
reduced-motion and bandwidth/loading checks; required CI/CodeQL/security/Contract
and receiving regressions. Mocks are not external-provider or private-content
acceptance. No such future implementation tests are claimed in this design task.

## 7. Proposed waves — none started

| Wave | Minimal work | Exit / authorization dependency |
| --- | --- | --- |
| A — semantic approval | COMPLETE: [Experience v1](experience-contract-v1.md) approved by Owner on 2026-11-01 | Separate implementation authorization remains; no package change or implementation wave started |
| B — minimum safe projections | Expose approved stimulus/transcript information, dimensions only if needed; preserve scoped media; update generated DTOs | Security/ownership/answer-leakage tests; schema/API drift; no public admin/import |
| C — selected Corpus adoption | Separately authorized corpus operator maps selected units and approved media to profile, preserving accepted pedagogy | Controlled handoff; no private data committed here; exact release/policy provenance |
| D — Web representative slice | Reading, inspectable image, audio, ordered exercise, feedback, completion/path/replay | Bible-based visual evidence and accessibility, not full rollout |
| E — Android adaptation | Adapt accepted semantic slice to authoritative native baseline | PR #17 resolved by Owner separately; no importing candidate as main implicitly |
| F — integrated Owner acceptance | Review actual selected sequence and client states in authorized environment | Content fidelity, progression, UI/native security and visual approval |
| G — wider migration | Plan legacy KEEP/REINTERPRET/REPLACE only after slice approval | Separate authorization; never automatic rollout/next phase |

## 8. Product Owner decision register

| ID | Current disposition after accepted Corpus review | Remaining gate / effect |
| --- | --- | --- |
| PO-E01 | APPROVED / NORMATIVE EXPERIENCE CONTRACT v1 on 2026-11-01; semantic review closed | Not implementation/deployment/Corpus adoption; separate execution authorization remains |
| PO-E02 | RESOLVED: no additional Corpus reading acknowledgement/completion state/mandatory unlock gate unless explicitly authored in authoritative data; retain existing Learning Core | No unresolved v1 semantic; client reading/local state is non-authoritative and does not alter access/mastery |
| PO-E03 | RESOLVED: existing attribution and text/audio association suffice | No new speaker label, voice registry, character-voice/TTS/provider model; future safe projections preserve existing meaning |
| PO-E04 | Future exact unit/release/media mapping still needs authorized receiving | Separate content/implementation gate; no contract-level blocker and no slice started |
| PO-E05 | Android authoritative baseline remains a separate Owner workflow | Not a v1 semantic blocker; no Android merge/adaptation in this task |
| PO-E06 | EXP-REQ-011 NOT_REQUIRED_FOR_VERTICAL_SLICE, deferred outside normative v1 | Conditional later feature only; CP-C01 does not block current v1 or slice contract readiness |

## 9. Non-goals, unknowns and preserved gates

No UI redesign, runtime/projection/domain/migration implementation, Course Package
change, corpus edit/read, renderer/RetroCel integration, vertical slice, deployment,
merge or new phase. No private entity names, lessons, prompts or authoring QA are
introduced. No proof of Corpus Bible synchronization or actual selected-content
fitness is claimed. Renderer independence is achieved by consuming approved assets,
not executing a rendering system. Warm illumination, ornament, feedback/motion and
progress imagery remain client design choices over semantic completion/mastery.

Preserve live SMTP/Google staging acceptance, at-least-once SMTP semantics, production
storage provider/retention/GC scheduling/monitoring/backups, consented selective
recording retention/erasure, future export/privacy, real privileged authorization,
explicit release migration and pending license. No external boundary is activated
by documentation-only analysis; none of these gates is marked complete.
