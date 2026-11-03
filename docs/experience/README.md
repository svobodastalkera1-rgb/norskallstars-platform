# First Experience slice — Platform implementation

Owner authorization: 2026-11-03. Scope: Platform-side Web/native online Experience
using public-safe synthetic data, pending controlled Corpus handoff. No private
unit content is known, inferred or copied. The target authored sequence is only
an integration identifier: 014 → 015 → 016 → REVIEW-02 → READING-02.

Normative sources: [Experience v1](../product-world/experience-contract-v1.md),
[Bible](../product-world/world-experience-bible-v1.md),
[reconciliation](../product-world/experience-reconciliation-v1.md),
[Corpus review](../product-world/corpus-semantic-review-2026-10-31.md),
[Learning Core](../architecture/learning-core.md), ADRs 0012/0013/0014.
The prior capability scan remains dated baseline evidence on its analysis branch;
current source/API/tests determine current capability. No prior visual is precedent.

## Requirement matrix — established before implementation

| Approved requirement | Classification | Smallest implementation / invariant |
| --- | --- | --- |
| EXP-REQ-001/002/003 authored character/location/scene continuity | ALREADY_SUPPORTED | Approved text/media carry continuity; no runtime entity simulation or registry |
| Immutable release identity, pinned enrollment, ownership/access | ALREADY_SUPPORTED | Reuse existing Identity/Learning/media endpoints; no new principal or release lookup |
| EXP-REQ-007 ordered text/image/audio/dialogue and block identity | PRESENTATION_ONLY | Ordered sequence in each client; continuous reading, contextual controls |
| EXP-REQ-007 activity_ref interleaving, no duplicate activity/credit | PRESENTATION_ONLY | Render first authored reference at its position; unreferenced activities once in declared lesson order; existing one attempt submission |
| EXP-REQ-004 activity stimulus_refs | API_PROJECTION_REQUIRED | Add allowlisted asset descriptors to existing ActivityView from the same pinned content; reuse existing authorized media delivery |
| EXP-REQ-006/010 approved transcript / explicit text-audio association | API_PROJECTION_REQUIRED | Add block transcript projection; preserve text and authored block order; no inferred playlist/speaker registry |
| EXP-REQ-006 existing attribution / speaker context | ALREADY_SUPPORTED | Preserve authored text; do not expose speaker_notes or unknown metadata |
| EXP-REQ-005/010 inspectable images, alt text, focus/back recovery | PRESENTATION_ONLY | Accessible enlargement, bounded existing media; native back/dismiss and Web focus return |
| Explicit translation | ALREADY_SUPPORTED | Reuse on-demand authorized translation; no automatic fetch/display |
| EXP-REQ-008 chapter learning order, linear mastery, semantic completion, replay | ALREADY_SUPPORTED | Ornament renders existing completion state; never changes thresholds or awards credit |
| EXP-REQ-009 reading availability versus local UX versus progression | ALREADY_SUPPORTED | No scroll/acknowledgement completion or reading-specific unlock; no new persistence |
| Contextual correct/incorrect/completion feedback | PRESENTATION_ONLY | Server evaluation only; unknown/pending/not-applicable stay distinct; ignition/hearth visual language |
| Character/location/prop/weather/light registry | NOT_REQUIRED_FOR_SLICE | Authoring-only; consume approved renderer-independent assets, not private registries |
| Chapter opening/closing artwork schema | NOT_REQUIRED_FOR_SLICE | Not required by accepted first-slice reconciliation; use existing lesson illustrations, no invented chapter asset semantics |
| EXP-REQ-011 separate reading kind | NOT_REQUIRED_FOR_SLICE | Deferred outside normative v1 |
| Ambience, timed playlists, RetroCel, offline/sync | NOT_REQUIRED_FOR_SLICE | No inferred roles, provider, scheduling or next-phase work |

No DOMAIN_CHANGE_REQUIRED item or migration is justified. No Course Package v1
change is proposed. Existing course asset identities, block/activity references
and authenticated projections suffice. API additions are presentation-safe DTOs,
not a Course Package/Experience schema extension. Unknown or unresolved media
references fail closed; private notes, answer keys, storage keys and source URLs
must never enter these descriptors.

## Design and implementation boundary

OUTSIDE: deep fjord/forest shell and monumental quiet hierarchy. JOURNEY: chapter
sequence and meaningful incomplete/completed ornament. SHELTER: warm focused
reading/task surface and server-confirmed completion. Cold/warm state remains
client rendering, never a domain glyph or pedagogical rule. IGNITION is brief
feedback; HEARTH is settled warmth. Reduced motion uses immediate equivalent states.

Limit the implementation to learner home/path, lesson/reading, task and result
surfaces on both clients. Identity/settings/history/placement behavior is retained;
no unrelated visual rollout. Reading and compact learning use distinct densities.
Synthetic media is explicitly non-production, release-ineligible and unrelated
to the private target units. The original inventoried fixture bytes remain unchanged.

## Delivery gate

Target intermediate state: PLATFORM_IMPLEMENTATION_READY_FOR_CORPUS_HANDOFF.
INTEGRATED_SLICE_COMPLETE is prohibited until a validated Corpus package passes
controlled receiving/import and authored end-to-end acceptance. No private Corpus
access, content reconstruction, deployment, provider integration or next phase.

## Implemented technical surface

The existing authorized lesson endpoint adds `ActivityView.stimuli` (asset identity,
image/audio type, alt text and optional approved transcript) and `BlockView.transcript` (explicit block transcript, or the exact declared audio
asset transcript when the block has none).
Descriptors resolve only within the enrolled immutable release. No URLs, storage
keys, answer keys, speaker notes or arbitrary metadata are projected. Existing
media delivery still checks authenticated account, enrollment ownership, lesson
availability and declared asset association. Placement does not project stimuli
that its existing delivery boundary cannot serve. OpenAPI and generated Web/native
DTOs describe these additive fields. There are no new endpoints, tables, migrations,
package fields, entity registries or progression policies.

Each client builds a presentation sequence from backend block order and explicit
activity references. The first reference places the task; repeated references keep
their context without duplicating the answer interaction. Unreferenced activities
appear once in declared lesson activity order. Invalid identities fail rather than
being guessed. Submission still uses the existing attempt transaction/evaluator.
The clients never parse Course Packages, infer narrative scenes or award credit.
Audio is associated with its authored block/task and transcript; native playback
remains lifecycle-bound, Web uses native audio controls. No timed queue/ambience is
inferred. On-demand translation remains an explicit authenticated operation.

## Design primitives

| Primitive | Shared meaning | Web | Native Android |
| --- | --- | --- | --- |
| Outside | Cool, substantial shell; no reward-state meaning | Fjord/iron background, editorial hierarchy | Scoped dark Compose scheme, native navigation/back |
| Journey | Existing chapter/order and canonical completion | Flat chapter sequence; accessible count plus decorative empty/filled markers | Native list, same semantic count/markers |
| Shelter | Focus, context and legibility | Warm paper prose with continuous gold seam; contained dark task workspace | Continuous paper blocks, gold edge; native task controls |
| Ignition | Server-confirmed correct result | Brief 220 ms reveal, explicit symbol/text and semantic green/warm edge | Short color transition with explicit symbol/text |
| Hearth | Settled confirmed completion | 900 ms warm surface transition; no loop | Settled warm result surface; no loop |
| Inspection | Same authorized media, larger view | Modal dialog, Escape, focus return, responsive image | Native dialog, Back, bounded zoom/pan |

Semantic palette: iron `#101e24`, mist `#eef1e9`, paper `#eee9dc`, ink `#1b302f`,
firelight `#edc185`; success retains green and incorrect retains coral with explicit
text/symbols. Ornament is presentation, never a domain ID/state. Corners are square
or 2 dp; separators replace nested cards; elevation is reserved for native modal
behavior. System fonts and editorial serif prose require no remote fonts/assets.
Narrative measure is about 68 characters; tasks about 46 rem. Narrative spacing
uses 16–64 px, task grouping 10–28 px, utility controls retain comfortable targets.
Neither client redesigns account/security/history surfaces in this slice.

Web respects `prefers-reduced-motion`; Compose transitions respect the system
animator duration scale. No autoplay, ambient layer, reward sound, permissions or
sensory effects are added. Keyboard/screen-reader labels, native Back, touch sizes,
text scaling, IME and existing microphone/session protection remain requirements.
Success, incorrect, pending and not-applicable remain distinct. Content-only units without activities have no attempt start/submit affordance;
there is no invented reading acknowledgement. Backend completion
is never inferred from marker color, scrolling, playback, reading or acknowledgement.

## Synthetic review environment

`apps/backend/tests/experience_fixture.py` derives an explicitly artificial geometry
course in memory from the approved public fixture. The source package remains
`release_eligible=false`; original inventoried files are untouched. The guarded
browser/native test seed uses the existing isolated test-only publication derivative
and explicit versioned test policies. This is not permission to publish synthetic
packages through production paths. Three synthetic units exercise text/image/audio,
interleaved tasks and longer reading. They do not correspond to the private five
units. Reading has no new authored acknowledgement/unlock semantics. Merely opening
or scrolling it changes no canonical state; existing explicit Learning Core attempt
rules remain authoritative.

### Web manual review

From repository root, with the documented pinned toolchain/Docker available:

```sh
make bootstrap
python3 scripts/phase1.py init
npm --prefix apps/web ci
npm --prefix apps/web run build
python3 scripts/web_e2e.py prepare
python3 scripts/web_e2e.py serve
```

`prepare` resets only the dedicated `norskallstars_web_test` database, not normal
local/manual data. Open `http://127.0.0.1:8000/` (Codespaces: privately forward 8000).
Read the generated `chromium:experience` credentials locally from ignored mode-600
`.cache/web-e2e/login.json`; never attach or print them in public evidence. No SMTP,
Google or production credentials are required. Sign in, start **PUBLIC-SAFE
Synthetic Experience Lab**, inspect the path, Continue, enlarge/close the geometry
image, play the synthetic chime and request translation. Start the task, submit
responses, inspect correct/incorrect feedback and replay. Complete the second unit
with its explicit matching/self-acknowledgement policy, then open **Synthetic
continuous reading**. Verify that reading/scrolling does not increment completion:
this lab remains at two completed exercise units out of three listed units. It
does not invent a reading acknowledgement merely to display 100%. Real authored
progression must be verified against the controlled handoff, not inferred here.
Synthetic review answers: first unit chooses **water** and its acknowledgement.
Second unit pairs **yellow square → water**, **blue circle → shade**, enters
`An invented square signals water.` and acknowledges its activities. These are
public artificial test values, not real authored answers.
A rubric result may remain pending while its explicit completion policy is met;
this is not a fabricated score. All content/answers for this artificial fixture are
public test data; no real course or learner content is required.

For reproducible local Web review screenshots (synthetic learning surfaces only):

```sh
python3 scripts/web_e2e.py prepare
NORSKALLSTARS_VISUAL_EVIDENCE=1 npm --prefix apps/web run e2e -- --project chromium --timeout=120000
```

Narrow 390, intermediate 820 and desktop 1440 px images go only to ignored
`.cache/experience-review/web`. They are review evidence, not an approved README
showcase or production visual acceptance. The separate review command allows time
for the additional full-page renders; normal browser CI retains its unchanged 30-second
test limit and does not capture images. Browser traces/videos remain disabled.

### Android manual review

Follow the pinned [native setup](../../apps/android/README.md). In one terminal:

```sh
python3 scripts/phase1.py init
python3 scripts/android_e2e.py prepare
python3 scripts/android_e2e.py serve
```

Build/install the private debug build for that isolated backend in another terminal:

```sh
cd apps/android
./gradlew :app:assembleDebug -PdevelopmentOrigin=http://10.0.2.2:8001 --no-daemon
cd ../..
adb install -r apps/android/app/build/outputs/apk/debug/app-debug.apk
```

The emulator must reach the host's privately forwarded 8001; see native setup for
Windows/physical-device networking. Use the ignored Android seed login file and
its `android:experience` account. Exercise the same synthetic course/path, image
inspection and native Back/zoom, chime playback, explicit translation, task results,
replay and reading without implicit credit. Test compact API 26 and typical API 35
phones, larger font scale, TalkBack and system animation disable. No provider is
needed. APKs remain ignored/private. Existing secure-window policy is retained;
OS screenshots can be blocked intentionally. Do not disable it for visual evidence.
Manual native review uses the installed app; CI publishes only sanitized device
diagnostics, never account input, screenshots or raw instrumentation output.

## Security review and remaining acceptance

The new interface is an additive projection under existing authentication/ownership,
not a new privileged operation. Cross-account/anonymous denial and release pinning
remain server enforced. Existing bounded media decoding/delivery and request limits
remain unchanged; no external asset URLs or markup execution are introduced. Free-form
answers stay in existing protected persistence and are not normal-log payloads.
Inspection reuses authorized bytes and disposes object URLs/native temporary media;
no extra durable cache or sharing is introduced. No storage/provider/GC boundary is
newly crossed, and existing cleanup/privacy regressions must continue to pass.

Live SMTP/Google, actual remote bucket/privacy/erasure/retention operations, export,
privileged admin authorization and deterministic release migration remain their
existing explicit future gates. The real Corpus package is not available/accepted
here. Actual media size, long-form authored layout, narrative continuity and final
visual quality require the controlled handoff and Owner cross-client review. No
legacy artwork is a design anchor; no final illustration production is included.

For local synthetic-only native evidence, the instrumentation journey accepts the
opt-in runner argument `experienceReview=synthetic-only`. It captures its own Compose
learning root into the debuggable app's private cache (`synthetic-review-*.png`),
without disabling the secure window. It is absent in normal CI and never publishes
screenshots. Run only on the documented reset synthetic test device; retain any
copied evidence under ignored `.cache/experience-review/android`. Do not use this
test option for real accounts/content or upload raw device state. The instrumentation
still runs all required tests and the normal fail-closed gate remains mandatory.
