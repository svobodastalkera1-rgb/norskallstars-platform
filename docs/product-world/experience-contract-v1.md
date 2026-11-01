# Experience Contract v1

Version: **1.0**. Status: **APPROVED / NORMATIVE EXPERIENCE CONTRACT v1**.
Product Owner approval date: **2026-11-01**.
This is the sole normative Experience v1 document. Implementation has NOT started;
no deployment or Corpus adoption is claimed. See the dated
[approval and provenance record](experience-approval-2026-11-01.md).
Authority: Bible v1.0 and the Product Owner-accepted
[Corpus semantic review](corpus-semantic-review-2026-10-31.md).
See the corrected [reconciliation](experience-reconciliation-v1.md).
Course Package Contract v1 remains unchanged.

## 1. Smallest useful boundary

Experience Contract v1 is a versioned interpretation and presentation agreement
using existing Course Package identities, content and safe backend projections.
It adds no course data schema, annotation sidecar, renderer contract, entity/voice
registry or second progression model. Most required changes are future client
composition and safe projections, not new authored fields.

Preserve course/release identity, chapters/lesson references, block ordering,
asset references/alternatives and activity stimulus references. Never infer identity
from titles, array positions, provisional pilot IDs or visual resemblance. Corpus
owns character/location/scene continuity in authoring and approved rendered content;
Platform does not need its private continuity registries.

Approved normative semantics:

1. **Context belongs to its authored position.** Display ordered text, images,
   audio and dialogue. Activities referenced at a block position stay associated
   with that position; do not duplicate them when also enumerating activities.
   Handle unreferenced activities deterministically under existing package/policy
   semantics without inventing an authored scene model.
2. **Assessment media is contextual.** Project only declared stimulus refs from
   the pinned release, preserving owning-account and lesson-availability media
   authorization. No new asset discovery/private URL surface.
3. **Images must be inspectable.** Preserve meaningful alternative text and readable
   detail. Enlargement, focus recovery and native back are client requirements,
   not corpus widget fields. Optional dimensions describe assets; they grant no
   access and promise no new delivery variant or generated thumbnail.
4. **Speech remains intelligible and text-accessible.** Existing authored attribution
   and text/audio association sufficiently represent current speaker context.
   Preserve these associations and approved transcripts without inferring identity
   from filenames or voices. No new public_speaker_label annotation, voice registry,
   character-voice registry, TTS/provider metadata or production voice infrastructure
   belongs to v1. Do not expose raw speaker_notes, answer keys, internal production
   notes or arbitrary metadata as display attribution.
5. **Reading is continuous prose, not an obligatory quiz.** Existing text/image/audio
   blocks carry reading. Corpus does not require or author an additional reading
   completion acknowledgement, reading-specific completion state or mandatory
   reading unlock gate unless authoritative course data explicitly supplies such
   semantics. Never infer them from reading composition or client behavior.
   Preserve the existing Learning Core rules described below.
6. **Translation is requested.** Keep explicit on-demand translation separate from
   target-language transcripts. Do not translate automatically or disclose answers.
7. **Progress stays semantic.** Existing completion/mastery/access/replay states
   remain server-authoritative. Ornament, illumination, density and motion belong
   to clients and preserve accessibility/reduced motion. No visual-state fields
   or second reading-progress engine belong in the domain or Course Package.

## 2. Reading: availability, progression and local UX

| Layer | Authority and meaning | Prohibited inference |
| --- | --- | --- |
| CONTENT AVAILABILITY | Existing published release, content references, authorization, prerequisites and accepted Learning Core availability rules determine which content the learner can access | Reading styling, opening a page or scrolling cannot bypass existing access/prerequisites; no additional reading unlock gate is invented |
| LEARNER PROGRESSION | Existing release/policy-pinned Learning Core evidence, explicit versioned rules, canonical completion/mastery and replay remain authoritative | No new reading acknowledgement, completion state, mastery credit or mandatory quiz is imposed by Experience v1; no second progression model |
| CLIENT PRESENTATION / LOCAL READING UX | Clients may have non-authoritative presentation state such as scroll position, last opened or local reading progress where separately implemented/authorized | These values are not authored completion/mastery, canonical learning evidence or permission to unlock content; this document does not implement or authorize persistence/sync of new user data |

Absence of extra Corpus semantics is not a request for a new reading policy.
It also does not waive existing unit-level Learning Core requirements or change
already pinned rules. Explicit authoritative course data must be handled through
its existing approved integration/policy boundary, never guessed from opaque
extension objects, reading titles or display behavior. Any genuinely new semantic
requirement later needs separate review; it is not a current v1/slice blocker.

## 3. Existing primitive inventory

This approved v1 adds no annotation fields or transport/schema.
All references remain scoped to one immutable release, validated under unchanged
Course Package v1 and projected through allowlisted authenticated APIs. Reject
unknown/cross-release/conflicting references. Never expose raw package/authoring
metadata to clients. Public authored data and private learner state remain distinct.

| Existing primitive | Purpose; producer → consumer | Required / slice necessity | Lifecycle / validation | Boundary, privacy and client relationship |
| --- | --- | --- | --- | --- |
| course_id, course version, immutable release identity | Content scope; Corpus package → importer/domain/projection | Required binding; slice yes | Existing validated identity; no latest-release reinterpretation | Approved content identity; domain pins release; both clients consume safe DTOs |
| chapter_id, ordered lesson_refs | Coherent chapters; Corpus → domain/projection/clients | Required where present; 008 not specifically first-slice | Existing order/references/prerequisites; no inferred arc IDs | No private narrative planning or new chapter-art schema |
| lesson_id, block_id/order/type | Authored sequence; Corpus → safe lesson projection | Required; slice yes | Existing ID/order semantics; preserve explicit content transitions | No private scene-state registry; Web/native compose independently |
| block asset_ref and alt_text | Relevant illustration/speech; Corpus → media/domain/projection | Required when media used; slice yes | Known approved asset, meaningful text alternative | Existing scoped access; clients provide inspection without domain layout fields |
| asset id/version/checksum, optional dimensions | Stable approved bytes; Corpus → storage/projection/clients | Identity required; dimensions optional; inspectability required | Immutable checksums, bounded MIME/size/decoding | Renderer-independent assets; no generation metadata or invented variants |
| block activity_ref, activity stimulus_refs | Interaction/media context; Corpus → domain/safe projection/clients | Required where authored; slice conditional on activities | Resolve same release; no duplicate credit or access bypass | Existing fields; future safe stimulus projection, not new course semantics |
| approved attribution, audio transcript, explicit text/audio association | Accessible speech and current speaker context; Corpus → allowlisted projection/clients | Preserve where authored; slice yes | Retain exact approved association/language; no guessed role/transcription | Existing public content only; no raw notes, learner recordings, voice/character registry or new label field |
| explicit learning-policy identity/digest and server progress | Canonical access/completion/replay; Platform → safe API/clients | Existing foundation required | Existing explicit validation, pinned enrollment, sticky completion | Account-private state; never public handoff data; local reading UX grants no canonical credit |

Characters, locations, props, wardrobe, weather, light and scene-state registries
remain authoring concerns; no open metadata dictionary is introduced. Existing
approved images may serve compact and enlarged views within delivery limits.

## 4. Removed proposals and deferred planning

The earlier conditional public_speaker_label, presentation_intent annotation,
annotation envelope, profile_version/package_digest sidecar fields and associated
new mapping lifecycle are removed before v1 approval. Existing attribution,
text/audio association and client reading composition suffice; the Corpus review
provides no justification for new authored payload. This removal does not remove
ordered reading, context, transcript, media/accessibility or the nine preserved
requirements.

EXP-REQ-011 is **NOT_REQUIRED_FOR_VERTICAL_SLICE** and outside the normative v1
surface. A distinct standalone optional reading kind remains a legitimate deferred
planning candidate, not an approved feature, schema or obligation. Revisit only
if separately required; do not implement it to complete v1. Existing valid units
and ordered blocks suffice for the first slice without Course Package changes.

## 5. Lifecycle, readiness and acceptance

Historical lifecycle:
REVIEW_CANDIDATE_NOT_APPROVED → Corpus semantic review
ACCEPT_WITH_MINOR_CORRECTIONS → corrected Platform candidate
**READY_FOR_PRODUCT_OWNER_APPROVAL** (2026-10-31) → Product Owner approval:
**APPROVED / NORMATIVE EXPERIENCE CONTRACT v1** (2026-11-01).
The semantic review cycle is closed. Earlier candidate/review/correction states
remain historical, not retroactive approvals. No claim of implementation,
deployment, Corpus adoption or verified Corpus Bible synchronization is made.

Contract-level readiness for 014 → 015 → 016 → REVIEW-02 → READING-02: **READY**.
The nine FULLY_PRESERVED requirements remain intact, EXP-REQ-009 is resolved without
new authored semantics, and EXP-REQ-011 is deferred/not required for the slice.
Current speaker attribution is sufficient; there is no mandatory Course Package v1
change or remaining contract-level ambiguity identified by the accepted review.
READY does not authorize the slice or certify clients, media, exact unit mapping,
content acceptance or production integrations. Those remain separate future gates.

After separate implementation authorization, future
conformance evidence must cover ordered reading/media/activities, image inspection
and focus recovery, attribution/transcript/translation associations, existing
canonical completion/replay/access, absence of fabricated reading progress,
cross-account denial, malformed/cross-release refs and resource limits. Web/native
accessibility and lifecycle evidence remain client-specific. No tests of future
runtime implementation are claimed by this documentation correction.

Course Package v1 and Learning Core remain unchanged. No new schema/parser/importer,
UI, Corpus modification, slice, RetroCel, wider migration, deployment, Android merge
or subsequent phase is authorized. STOP before implementation; merge still requires
Product Owner review of the publication PR.
