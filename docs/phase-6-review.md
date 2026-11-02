# Phase 6 implementation review evidence

Phase 6 Android is implemented; hosted implementation checks passed. Product Owner
review remains pending. Dated validation/correction evidence below is historical;
each later HEAD requires separate hosted verification. This record is not Product
Owner acceptance and contains no private course material or test credentials.

Accepted Web PR #10 was merged into main
`8100927bf4717d15dfa112254c4b6acd76dccaae` on 2026-10-08. Its tree matches the
accepted `af952422215984facab7022f187e265332e36bf0` tree. Merged-main Backend CI,
Web CI, Phase 0 CI and Python/Web CodeQL workflows completed successfully.
Work proceeds on `feature/phase-6-android`; main is not modified directly.

## Scope and architecture

Authoritative scope: [ROADMAP](../ROADMAP.md), public product direction and
[Android scope/DoD](android/README.md). Phases 0–5 are CLOSED/ACCEPTED. Phase 7 is
not authorized. [ADR 0014](adr/0014-native-android-online.md) records native session,
network, state and lifecycle boundaries. No DB migration or backend product-domain
change is needed; existing HTTP contracts remain authoritative.

The native app implements account registration/sign-in/verification/recovery,
configured Google proof, fresh proof, password/link/deletion, preferences and
revocable sessions; dashboard/enrollment/curriculum/pinned lessons, placement,
translation, server-evaluated responses, replay/review/history; authenticated
images/audio and bounded explicit microphone/consent/withdrawal. Bokmål/English
UI, scrolling, loading/error/empty/expired-session behavior and system-back/lifecycle
handling are included. There is no offline content cache/attempt queue or sync.

Generated Kotlin DTO drift is checked against the three accepted OpenAPI files.
Public Course Package source/schema/fixture inventory is unchanged. Test setup
reuses the approved synthetic mechanism in a separate guarded Android database;
manual-review data and the raw inbound handoff remain untouched.

## Validation status

Completed local regression evidence (2026-10-08): backend/PostgreSQL/migrations
248/248 (124 existing dependency deprecation warnings); unchanged Contract v1
19/19; repository/receiving tests passed; four new toolchain/audit regressions extend
the suite to 29 tests; Web unit/component 25/25 and format/lint/build;
Chromium and Firefox 3/3 each. WebKit initially exceeded the unchanged 30-second
journey timeout under concurrent native/backend compilation load; its isolated
repeat passed 3/3 in 21.3 seconds. Backend container build/migration/non-root/
read-only/health/authorization/schema smoke passed on an isolated loopback port.
Backend strict mypy (45 source files), Ruff, API/policy drift and native DTO drift
passed. Locked backend/npm audits reported no known findings; Android OSV audit
passed for 312 runtime/test/lint/buildscript Maven/toolchain coordinates after
explicit remediation. Wrapper JAR matched upstream SHA-256. On 2026-10-09 native JVM tests passed
19/19 with no skips, Android Lint passed, and debug/test APKs compiled.
Final unsigned/minified R8 release assembly passed (5m43s). The final documented `python scripts/android.py device` gate passed on API 35:
3/3 tests, no failures/errors/skips (1m26s). This covers real Keystore ciphertext/
tamper rejection, bounded private microphone/playback lifecycle, and the complete
real-backend synthetic account/learning/placement/replay/pinning/history/erasure
journey with Activity recreation. API 26 and exact-head hosted checks remain pending.
Earlier device runs passed Keystore/microphone checks but failed the full journey:
UI loading races, excessive test-side polling and transport failure were investigated;
subsequent runs stalled opening Account settings because the test clicked the
disabled top navigation before Home finished loading. This was a test readiness
race, not a backend deletion failure. Those failures are
not treated as acceptance. The successful final journey awaits visible/enabled controls, uses
normal IME Done behavior, verifies Activity recreation and retains all backend
completion/replay/pinning/erasure assertions. Final repository/receiving tests passed
29/29; staged confidentiality and reachable-history guards plus redacted index/
history secret scans passed. APKs, raw device reports and generated login values
remain ignored/local.
Real Android workflow definitions replace the pending gate. PR #17 is published with explicit Owner authorization. The first hosted run
failed before compilation because setup-java rejects `17.0.20.1` as SemVer.
CI installation now downloads the exact Microsoft JDK archive with a pinned
SHA-256, uses the supported jdkfile provider and verifies the installed vendor/
version. Cleanup also requires successful local-environment initialization.
The next hosted run installed/verified the JDK but revealed setup-android
requesting the removed legacy `tools` package by default; it now requests only
`platform-tools`, with the already pinned API/build-tools installed explicitly.
These infrastructure failures are not claimed as successful Android checks.
At revision `aec1c5a`, all 35 GitHub checks reported success, including compiled
CodeQL Android and release assembly. Independent log review nevertheless found
the device jobs never executed tests: prebuilt/debug APK signatures differed at
Gradle installation, and AGP returned success after the installation error.
Those device checks are explicitly **not accepted**. Device APK preparation now
runs after emulator setup through the same sanitized wrapper as instrumentation.
The gate removes old reports before running and independently requires fresh
JUnit results for all three native journeys with no failures/errors/skips.
Regression tests reject missing, incomplete, failed, skipped and duplicate results.
At `0e8b7fe`, the push API 35 device job verified three actual tests with no
failures/errors/skips. API 26 was correctly rejected by the new gate: its runner
attempted to reinstall the preprovisioned APK without replacement permission.
Explicit `installation.installOptions += "-r"` preserves the app-private synthetic
input during test-runner installation on older devices; normal signature checks
remain enforced. The corrected exact-head hosted matrix remains pending.
At `355961c`, independent report verification again rejected API 26. Source
inspection identified the exact pinned-tool mismatch: AGP's UtpTestUtils passes
`android-test.apk-install-options[deviceSerial]`, but engine 1.0.1 requests only
the unsuffixed key. The ordinary connected task also does not consume custom-suite
JUnitEngineSpec inputs. The ineffective legacy setting was removed. The device
wrapper now injects only the constant unsuffixed `-r` property into the test JVM
via JAVA_TOOL_OPTIONS, after discarding all ambient JVM options/provider secrets.
A regression verifies that build/quality never inherit it and device mode can
receive only this constant. No signature bypass, engine downgrade, dependency
change or test assertion removal is involved. Fresh complete JUnit reports remain
mandatory; the corrected hosted matrix is pending.
The merged-main workflow results above cover the accepted base only.
See [CI names](ci.md) and [security review](security/phase-6-review.md).

Owner review must cover a debug-device account/complete synthetic lesson/replay/
placement/preferences/session-revocation/deletion journey, microphone permission
and consent behavior, screen rotation/background/foreground, TalkBack and large
text. Live Google/SMTP need separately configured isolated staging and are not
verified by mocks/default emulator tests. Production storage/retention/erasure,
export/admin/release migration/license/store gates remain explicit in TASKS.

### Hosted runner follow-up — 2026-10-10

At `32943e2`, API 35 again passed three real native tests, but API 26 still
failed before execution despite the constant JVM option. This is not accepted.
The harness now uses the official AndroidJUnitRunner/adb command-line interface
for the entire unchanged instrumentation package after Gradle APK assembly.
Only the test APK is installed at this point; the provisioned app/input remains
private. The fail-closed parser requires start and successful completion events
for all three journeys and one final successful instrumentation result. Skips,
errors, crashes, duplicates, missing events and oversized output are rejected;
only sanitized case identities/results are persisted as fresh local JUnit XML.
No tests, backend assertions, signature checks or API matrix entries were removed.
New parser regressions exercise false-green and malformed output.
The Web push run at this revision timed out downloading browser dependencies from
the hosted image's indirect HTTP Azure mirror list, before E2E. The existing
HTTPS mirror setup now also updates the referenced local mirror-list files.
Exact-head hosted validation of these corrections remains pending.

The native microphone test also called UiAutomation.grantRuntimePermission, an
API 28 method on the API 26 compatibility floor. Its isolated permission setup
now uses UiAutomation.executeShellCommand (`pm grant`) and closes the command
output descriptor; the actual permission/recording/playback/privacy/lifecycle
assertions remain unchanged. This is a test API compatibility correction, not
a production permission bypass. Both hosted API levels must execute it.

### Successful hosted implementation evidence — 2026-10-10

Implementation/correction head `54f83ac96763b0bfa21d5b7150d19956175eb15b` in
[PR #17](https://github.com/svobodastalkera1-rgb/norskallstars-platform/pull/17)
passed **35/35 checks** across push/PR events. No skipped/pending result is included.
All eleven existing required checks succeeded; main remains `8100927` and PR was
MERGEABLE/CLEAN. No merge, force push or settings change occurred.

| PR workflow | Verified result |
| --- | --- |
| [Safeguards](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/38062574303) | Bootstrap, 36 repository/receiving tests, exact-index/history confidentiality and secret checks |
| [Backend](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/38062574318) | 248 tests, 124 existing dependency warnings; 19 unchanged Contract tests; Ruff/strict mypy (45 files), drift, audit and container checks |
| [Web](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/38062574279) | 25 component/unit tests; three E2E each in Chromium, Firefox, WebKit; quality/build/drift and dependency audit |
| [Android](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/38062574299) | JVM/Lint, debug/unsigned R8 release builds, 312-coordinate OSV audit; API 26 and API 35 each independently verified 3 native tests, no failures/errors/skips |
| [CodeQL](https://github.com/svobodastalkera1-rgb/norskallstars-platform/actions/runs/38062574280) | Python, Web and compiled Java/Kotlin Android analysis/upload succeeded |

Earlier false-green/installation results above do not count as acceptance. The
new adb harness executed the complete unchanged native test package on both OS
levels and its protocol/JUnit proof passed. Local restored-toolchain JVM tests
19/19 and Lint also passed on 2026-10-10; fresh debug/test APK assembly is checked
separately. Repository/receiving regressions passed 36/36 and staged security gates
passed. Raw reports, test credentials and APKs remain ignored, never CI artifacts.

Code Scanning alerts API returned 403; successful analysis is not a claim of no
alerts. Owner must inspect the UI. The six new Android names in [CI](ci.md) are
not required yet; no protection was changed.

Phase 6 is ready for Owner review, **not accepted**. Use the
[manual review procedure](android/manual-review.md); live SMTP/Google, physical
device/TalkBack review and production storage/operations/store gates remain open.
Later documentation/fix heads require their own hosted results, reported through
PR/check metadata. Do not merge or begin Phase 7 without Owner authorization.
