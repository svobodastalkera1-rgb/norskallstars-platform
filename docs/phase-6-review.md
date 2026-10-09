# Phase 6 implementation review evidence

Phase 6 Android is implemented locally; hosted and Product Owner review remain pending. This record is not Product
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
These infrastructure failures are not claimed as successful Android checks.
Hosted checks and Kotlin CodeQL extraction remain pending. The merged-main workflow results above cover the accepted base only.
See [CI names](ci.md) and [security review](security/phase-6-review.md).

Owner review must cover a debug-device account/complete synthetic lesson/replay/
placement/preferences/session-revocation/deletion journey, microphone permission
and consent behavior, screen rotation/background/foreground, TalkBack and large
text. Live Google/SMTP need separately configured isolated staging and are not
verified by mocks/default emulator tests. Production storage/retention/erasure,
export/admin/release migration/license/store gates remain explicit in TASKS.
