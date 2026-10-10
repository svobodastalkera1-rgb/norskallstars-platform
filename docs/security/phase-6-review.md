# Phase 6 native Android security review

Scope: the online Kotlin/Compose consumer of the accepted Identity, Learning and
Media APIs. No backend runtime, authorization rule, database schema, importer,
publication interface, remote storage adapter or production deployment is added.
Review evidence and outstanding acceptance gates are in [Phase 6](../phase-6-review.md).

## Boundaries reviewed

- Authentication uses the existing revocable bearer/rotating-refresh model. Tokens
  are AES-GCM ciphertext in app-private no-backup storage; the key belongs to
  Android Keystore. Passwords, fresh proofs and answers remain transient. No
  tokens appear in URLs, diagnostic strings or application logs. Backup/device
  transfer exclusions and secure-window handling protect native session/UI data.
- API traffic goes to one configured origin. Release requires HTTPS with system
  trust. Debug HTTP is limited to emulator/loopback. Redirects, cookies, automatic
  mutating-request retries and body logging are disabled. GET recovery is limited
  to one fresh connection after EOF/connect/socket failure with account-generation
  checks; other HTTP/TLS/timeout failures are not retried. An authenticated 401
  follows the existing serialized session-refresh boundary once. Errors retain only a bounded
  category, never exception text/URLs/payloads. Timeouts and bounded JSON/media
  reads prevent unlimited resource consumption. Path segments cannot escape the
  API prefix. The client header is identification, never authorization.
- Concurrent 401s serialize refresh; the old refresh credential is removed from
  disk before sending it. A lost reply/process failure requires sign-in rather
  than credential reuse. Generation checks discard late replies belonging to a
  logged-out/replaced account. Invalid/revoked sessions clear account UI/media.
  Server ownership/revocation checks remain authoritative on every request.
- Sensitive changes use accepted server fresh-proof purposes and Google challenge
  validation. Operator CLI assertions are never used as authentication/RBAC.
  Google client IDs are public configuration; no provider secrets enter Android.
- All course identity, release pinning, completion, mastery, placement, translation
  and evaluation come from backend projections. Unknown presentation fails closed;
  a client acknowledgement does not authorize progression. No course-package
  parser, pilot assumption or independent evaluator is introduced.
- Images have byte/pixel/decode limits. Audio/recordings use private temporary
  files, cleaned on screen disposal, logout and next process start. Microphone
  permission requires an explicit action; delayed permission grants cannot start
  background recording. Lifecycle stop releases playback/recording. Recordings
  have a sixty-second/256-KiB cap; no background audio service is introduced.
- Recording submission requires separate voice-1 consent and a server-selected
  offer before bytes are read/uploaded. Ambiguous upload keeps the withdrawal
  identifier. Existing backend privacy, twelve-month maximum retention, ownership,
  account erasure and GC protections are preserved. No ML processing/training is
  implemented. Local files are temporary interaction state, not offline support.
- Test credentials stay in ignored mode-600 files and enter only a debuggable
  app's private files through stdin. Device tooling never prints raw
  instrumentation stacks/responses; only validated case identities/results are
  persisted locally, and generated input is not printed;
  no APK, screenshot, recording, private reports or job artifacts are published.
  Synthetic database guards reject ordinary/manual-review databases before reset.

## Findings and corrections

During client integration the existing Web Google-link fresh-proof purpose was
found to be `link_google`, while the accepted API requires `link`. Corrected only
that mismatch and added a Web component regression. No authorization was relaxed.

Native refresh cleanup is serialized with account replacement and rechecks the
account generation before removing disk credentials. A delayed-refresh regression
ensures the response cannot overwrite or clear a replacement account. Nested EOF
errors retain only bounded diagnostics; TLS errors never enter safe GET recovery.
IME Done behavior and Activity recreation are covered by the native journey.

The native dependency audit includes runtime, tests, lint and buildscript Maven
locks. Initial audits found vulnerable transitive tool dependencies; the pinned
AGP/Kotlin toolchain and explicit compatible transitive upgrades address them.
The 2026-10-09 OSV audit passed for all 312 locked runtime/test/lint/buildscript
Maven/toolchain coordinates with no known findings. This is a dated audit, not
an assurance against future advisories. No vulnerability allowlist or severity suppression is used.
Lint's dependency-update/target-version suggestions are informational and excluded
for deliberate pinned builds; correctness/accessibility/security diagnostics still
fail the build. See the [toolchain guide](../../apps/android/README.md).

## Remaining gates

A rooted/compromised device cannot be made trustworthy by client-side controls.
Backend authorization remains mandatory. Manual TalkBack, large text, device/OS
coverage and live Google provider/certificate configuration require Owner review;
synthetic/default-emulator tests do not prove provider acceptance. Live SMTP,
SMTP at-least-once behavior, private S3/IAM/provider erasure, monitored GC/retention,
backups erasure, future privacy/export, admin MFA/RBAC, explicit release migration,
license and signing/store policy gates remain open in TASKS/ROADMAP. Phase 7 offline
persistence/sync and all production deployment/publication remain unauthorized.

Hosted verification on 2026-10-10 at PR #17 implementation/correction head `54f83ac`
passed all backend/Web/Android dependency audits, confidentiality/secret guards and
Python/Web and compiled Android CodeQL checks. Both API 26/35 executed the real native
security/learning journeys (three tests each, no skips). This is dated evidence,
not live provider acceptance. Alert API access remains 403; Owner UI review is
required. Existing eleven required checks/protections were only read, not changed.
