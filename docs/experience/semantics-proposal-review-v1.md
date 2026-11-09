# Corpus Experience semantics proposal — Platform review

Date: 2026-11-09. Disposition: **ACCEPT_WITH_MINOR_CORRECTIONS**.
Status: **REVIEW_ONLY / NOT_APPROVED / NOT_IMPLEMENTED**.
PR #43 remains **BLOCKED_BY_CONTRACT_GAP** pending joint Product Owner/contract
approval and separately authorized implementation. This review does not amend
[Experience v1](../product-world/experience-contract-v1.md),
[Course Package v1](../../contracts/course-package/README.md), or the
[Bible](../product-world/world-experience-bible-v1.md).

## 1. Receiving and independent review

Candidate: `.local/outbound/corpus-platform-experience-semantics-proposal-v1.zip`.
Size: 9,226 bytes. SHA-256:
`c39622ba287f754d62bd2ca964c4819f84318c50aa1d39e19fb9d13b45f980d8`.
Type: `CORPUS_EXPERIENCE_SEMANTICS_PROPOSAL`; format `1.0.0`;
status `RECONCILIATION_PROPOSAL`, approval `NOT_APPROVED`.

A dedicated, one-off review profile validated this exact Owner-identified path;
no Course Package receiver was overloaded or changed. The common trusted bounded
archive reader was reused. This is not a claim that the checked-in Course Package
CLI supports this new type or that a permanent general-purpose receiver was added.

Receiving evidence:

- `.local/` ignored; no tracked/index entries; candidate path and ZIP blob absent
  from reachable local/remote branch and tag history. No symlink staging/file.
- Expected archive SHA matched before reading members. Common preflight enforced
  safe paths, duplicates/case collisions, regular files, compression/encryption,
  central-directory limits, 500 entries, 20 MiB archive/total, 10 MiB/file and 100:1
  expansion bound. No inbound code executed or uncontrolled extraction performed.
- Exact allowlist: `HANDOFF_MANIFEST.json`, `README.md`, `SHA256SUMS`,
  `proposal.md`, `examples.json`. Manifest discriminator/status/version checked;
  three payload inventory entries matched sizes and SHA-256. SHA256SUMS covered
  all payloads plus manifest, with no missing/extra/duplicate records.
- Manifest references the exact current normative Experience and Bible hashes.
  Producer baseline `de610cc327312e43c426303dd49c3866093b2204` is sender-asserted
  provenance, not independently verified Corpus history or authentication.
- All five files independently inspected. Examples explicitly synthetic and not
  a Course Package. UTF-8/strict JSON, confidentiality heuristics and redacted
  Gitleaks passed. No real lesson content/media, credentials, private URLs or
  executable payload accepted. Relative authoring implementation descriptions
  remain in ignored input; they are not needed in this public report.

Accepted **for review only**: README, proposal and synthetic examples. Manifest
and checksums are local integrity evidence. All original files remain under ignored
review staging; none are copied into runtime or tracked upstream contract paths.
Only this derived public-safe assessment is a repository deliverable. Checksums
establish byte identity; Product Owner routing establishes review authorization,
not approval of semantics.

## 2. Sufficiency and the necessary correction

`content_scope` with `canonical_episode` / `standalone_practice` is sufficient
for the reviewed story-versus-example distinction at an explicitly authored block
occurrence. It covers text, dialogue, explanation, summary and image/audio context
without a character registry or inference about the truth of individual sentences.
A canonical question or repetitive sentence is not necessarily a world fact.

`episode_start` is sufficient for a boundary at an authored content position,
including several starts within one unit, **if it remains independent of scope**.
The proposal currently contradicts that independence: it requires canonical scope
and rejects a practice block with `episode_start=true`. An episode beginning with
practice would have its boundary moved after that practice or become unrepresentable.

**Correction C1:** define `episode_start=true` as a boundary before the marked
supported content block, not a claim that its content is canonical. Permit it with
standalone practice as well as canonical scope; absence of scope must not itself
invent canonicality. Remove the proposed cross-property requirement and update the
synthetic discussion cases accordingly. A boundary before practice does not turn
that practice into an episode fact. An alternative policy restricting starts to
canonical material needs an explicit Owner decision and cannot satisfy the stated
practice-first case unchanged.

No third marker, episode identifier, end marker, graph, timeline or world state is
needed for the cases in this review. The two markers do not claim episode-membership
queries, chronology or cross-unit episode identity. A future need for those would
be a separate requirement, not inferred from this proposal.

## 3. Backend/domain and API review

Evidence: [import/publication](../../apps/backend/src/norskallstars_backend/course_packages/service.py),
[release persistence](../../apps/backend/src/norskallstars_backend/course_packages/models.py),
[validation](../../apps/backend/src/norskallstars_backend/course_packages/validation.py),
[lesson projection/evaluation](../../apps/backend/src/norskallstars_backend/learning/service.py),
[DTOs](../../apps/backend/src/norskallstars_backend/learning/dto.py).

| Boundary | Current capability | Required future disposition, not implemented here |
| --- | --- | --- |
| Import/staging | Validates archive/schema/references before transactional import; full documents retained | Validate approved known markers, target types and strict JSON types before any accepted state/storage mutation; malformed marker rejects whole import |
| Snapshot | Stores documents, package/archive digests, importer version and schema-derived contract digest | Preserve exact occurrence markers/absence; bind approved semantic revision/interpretation immutably to release acceptance |
| Publication | Release eligibility, operator authorization and asset integrity remain enforced | Require semantic conformance for dependent releases; flags alone are not permission or conformance |
| Release pinning | Enrollment pins immutable release and versioned learning policy | No relabelling, snapshot rewrite or reinterpretation of old enrollments |
| Domain | No narrative role/start model; raw extension storage is not interpretation | Two bounded content attributes and revision provenance suffice; no learning-state or world-state model |
| Safe API | Current BlockView omits both markers | Project only typed approved fields at their exact block position; no raw extension dictionary |
| Activity/media/transcript | Existing scoped assets, stimuli, transcripts and activity references | Preserve block occurrence context; do not attach scope globally to a reusable asset/activity identity or guess from nearest text |
| Replay/progress | Server attempts distinguish canonical/practice learning interactions | Attempt kind is unrelated to content scope; rendering/reset/replay produces no evaluation, completion, mastery, placement or unlock credit |

**Correction C2:** specify immutable semantic adoption before rollout. Existing
schema `contract_digest` alone does not bind an Experience revision: unchanged
schema bytes can support different semantic documents. Use an approved immutable
release acceptance binding to the semantic revision/digest; choose its concrete
representation during implementation design. Do not reinterpret previously stored
unknown extension properties just because a newer server now recognizes their names.
New authored labels require a new package/release identity; old releases retain
legacy interpretation. The existing importer version field can help establish
provenance, but is not itself an approved semantic adoption policy.

No learning-credit effect is required by these markers. Current evaluation consumes
activities, answers and pinned policies, not narrative attributes. Future tests
must verify unchanged attempt/progress/events across rendering, repeated rendering,
replay and reading-only boundaries. This is a design finding, not proof of an
unimplemented evaluator/projection integration.

## 4. Missing markers, media and validation

Accept the proposed defaults:

- Missing scope means UNSPECIFIED, a derived absence state, not canonical and not
  a third package enum. No inheritance across blocks or units.
- Missing/false start means no authored start asserted, not continuation, same day
  or a known timeline. Ordinary unit navigation remains navigation.
- `null`, unknown scope, nonboolean start and markers on unsupported block types
  must fail approved semantic validation, not be coerced or silently dropped.
- New semantic-dependent content needs explicit authored coverage/conformance;
  missing-marker compatibility does not prove the slice preserves intended roles.
  Only authoring review can detect an omitted intended marker; no text classifier.

**Correction C3:** clarify occurrence versus child rendering. Text, asset and
transcript rendered as parts of one block share that block's presentation context;
this is not scope inheritance to another block or to the global asset. A reused
image/audio asset can occur in different scopes. An activity stimulus/reference
must not silently inherit narrative status from a neighbouring block. Existing
activity interaction remains a task; it does not assert canonical facts. Confirm
that required standalone examples are carried by supported content blocks; the
proposal does not authorize scope on activity records or new stimulus semantics.
If authors require an independently scoped activity-only occurrence, that exact
capability needs separate resolution rather than guessing.

An unmarked block following practice must not visually remain inside an asserted
practice group. Clients may compact adjacent explicitly equal scopes, but a group
must close at unspecified/different scope or a new start. This is composition,
not inferred authored grouping.

## 5. Web and Android

Evidence: [Web sequence](../../apps/web/src/experience.ts),
[Web surfaces](../../apps/web/src/Learning.tsx),
[native sequence](../../apps/android/app/src/main/java/com/norskallstars/platform/ui/Experience.kt),
[native surfaces](../../apps/android/app/src/main/java/com/norskallstars/platform/ui/PlatformApp.kt).
Both currently render ordered content/tasks, but neither consumes these proposed
markers. Existing task framing and lesson navigation are not substitutes.

The corrected two-marker model can support both clients without corpus-specific
logic. Use the same scope/default/boundary truth table and authored block identity;
retain client-specific HTML/Compose layout, Back, scrolling, IME and focus behavior.
Preserve cold shell, warm reading/task surfaces, gold continuity line, semantic
progress, IGNITION/HEARTH and reduced-motion equivalents. No redesign is authorized.

A standalone example needs an explicit interface-language accessible label, not
color or ornament alone. A new episode may use a non-linguistic visual separator
with localized accessible text such as “New episode”; it need not teach new
Norwegian vocabulary. A plain decorative line/ARIA separator alone communicates
separation, not its narrative meaning. Web can use labelled semantic groups and
appropriate heading/separator relationships; Android equivalent heading/group
semantics. Do not make every boundary a focus stop or move focus on playback,
rerender or marker encounter. Screen-reader order must match authored order.
Animations are optional; static boundaries must remain equally understandable.

**Correction C4:** approve an enforceable client delivery/conformance policy before
activation. Current Web code does not read these fields; native JSON explicitly
ignores unknown keys. Additive JSON compatibility therefore does not preserve
experience. Minimum importer version protects ingestion only, not installed old
clients. Capable-client deployment/negotiation or a separately verified fallback
must protect every route delivering dependent content, including pinned enrollments,
replay and direct lesson/media contexts. A generic old-client screen is not a
verified fallback. Capability checks are presentation compatibility, never account
authorization, new mastery conditions or fabricated learning locks.

## 6. Adversarial case matrix

| Case | Corrected two-marker result | Current proposal qualification |
| --- | --- | --- |
| Practice about recurring canonical characters | Explicit standalone scope; no world-fact assertion | Sufficient; names never inspected |
| Canonical repetitive/drill-like language | Explicit canonical scope preserved | Sufficient; syntax/type never used as role |
| Several practice blocks inside an episode | Each explicitly scoped; canonical return explicitly scoped | Sufficient; no range inheritance or episode restart implied |
| Episode begins with practice | Start boundary before practice, scope stays standalone | C1 required; current canonical-only rule is insufficient |
| No markers | Unspecified; no start assertion; no inferred chronology | Safe conservative default |
| Old package without markers | Original release/presentation retained | Safe; not evidence of new conformance |
| Old snapshot with previously ignored same-named properties | Original interpretation retained | C2 required; never activate by presence alone |
| Replay of completed content | Same framing; sticky completion unchanged | Sufficient with learning regression tests |
| Reading/content-only unit | Framing only; no new attempt/acknowledgement | Sufficient; no reading completion credit |
| Boundary immediately after completed activity | Render once before next marked authored content block | Sufficient; no duplicate activity or result event |
| Several boundaries in one unit | Render each explicit start in authored order | Sufficient; no guessed episode IDs |
| Same image/audio in different contexts | Scope follows occurrence, not asset identity | C3 clarifies projection/rendering |
| Unknown enum/string boolean/null | Whole marked import rejected | Schema alone does not enforce this |
| Old client silently ignoring markers | Must not receive dependent experience without valid fallback | C4 is a rollout prerequisite |

## 7. Version and naming recommendation

Keep `content_scope`, `canonical_episode`, `standalone_practice` and
`episode_start`. The names are adequate when scope is defined as presentation
context, not a factual-truth annotation, and start does not imply chronology or
completion. No stylistic renaming or new enum is justified. Resolve C1 in meaning,
not by renaming the boolean.

Recommend **Experience Contract 1.1**, separately Owner-approved, rather than a
retroactive v1.0 clarification: these are new authored machine-readable semantics,
validation and compatibility obligations absent from approved v1.0. Preserve v1.0
bytes/approval history. Publish a versioned Course Package v1 optional-extension
semantic addendum/cross-reference through the contract-owner handoff; do not claim
Course Package documentation is unchanged.

No structural schema or transport bump is inherently necessary. The unchanged
content-block schema has `additionalProperties=true`. A local synthetic schema
experiment accepted proposed valid markers AND unknown scope, null scope and string
boolean, confirming both structural compatibility and missing semantic validation.
This was schema inspection, not import of an unapproved package.

Keep package `schema_version=1.0.0` only if owners explicitly approve this extension
policy and revision/conformance binding. Current validation enforces schema 1.0 and
rejects `minimum_importer_version > 1.0.0`; supporting implementation will need its
actual reviewed version and corresponding tests. Do not invent that version now or
silently export schema 1.1.0. Semantic documentation version, importer version,
Experience revision, package/course version, schema version and review-envelope
format are separate axes. If owner version policy requires a Course Package semantic
version increase, record it explicitly without falsely claiming a wire-schema edit.

## 8. Decisions and stop gate

Product Owner / contract owners must approve:

1. C1 independence and practice-first/unspecified-scope start behavior.
2. C2 immutable semantic revision/adoption binding and legacy same-named extensions.
3. C3 supported content occurrences, media/transcript context and activity limits.
4. C4 old-client rollout/conformance policy and accessible framing requirements.
5. Experience 1.1 and versioned Course Package extension documentation policy.
6. Separate implementation authorization after joint semantic approval.

Corpus owns authored markers, precise placement and export conformance. Platform
owns semantic import validation, immutable binding, safe API/client delivery and
cross-client rendering. Neither repository unilaterally changes the normative
integration agreement. No real Course Package was received. No normative contract,
application runtime, schema, Corpus, progress behavior or PR merge changed.

This review accepts the minimal two-marker direction with the corrections above;
it does not approve the submitted wording unchanged or unblock PR #43.
