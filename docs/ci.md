# CI state and required checks

Phase 0 bootstrap/security gates remain active. Phase 1 adds real backend gates;
Phase 5 introduces real Web workflows; Phase 6 replaces the pending Android
workflow with real native quality/build/dependency/device gates.
Unexecuted definitions are not hosted success.
Hosted outcomes are recorded with their actual revision/run in phase review evidence and each PR
and reported after completion; existence of a workflow is not a passing result.

| Exact status-check name | Real checks |
| --- | --- |
| Bootstrap checks | Tooling syntax/docs links and confidentiality safeguard tests/index/history |
| Security checks | Checksum-pinned redacted Gitleaks index and reachable history scan |
| Backend quality | Locked environment; Ruff format/lint/security rules; strict mypy; generated Identity/Learning OpenAPI and platform policy schema drift |
| Backend tests | Real isolated PostgreSQL, migration/drift, receiving/import/security and upstream tests |
| Backend dependency audit | Full locked runtime/dev dependency vulnerability audit |
| Backend container | Digest-pinned image build, Compose migrations/startup and HTTP/security/runtime smoke |
| CodeQL Python | Python security-extended analysis of runtime and repository scripts |
| Web quality | Prettier, ESLint, strict TypeScript/build and generated client drift |
| Web tests | Component/session/media tests and real PostgreSQL Chromium/Firefox/WebKit E2E/accessibility |
| Web dependency audit | Full npm lock vulnerability audit at low severity |
| CodeQL Web | JavaScript/TypeScript security-extended analysis |
| CodeQL | GitHub Advanced Security code-scanning results check |

Product Owner activated the first seven checks as required in Protect main,
with strict up-to-date branches, after accepting Phase 1. All seven are supplied
by GitHub Actions. Generated CodeQL (GitHub Advanced Security) succeeds but is not
configured as required. This state was verified on 2026-10-04; no settings are
changed by development PRs. Retired pending names must never be required.

The CodeQL advanced workflow uses contents/actions read and security-events write
only for analysis upload. It never receives private content or production secrets.
The owner should review Code scanning availability/results and use the committed
advanced workflow; do not activate a competing default-setup pipeline. If GitHub
rejects upload because setup is not enabled, enable the supported advanced setup
manually; do not bypass permissions or substitute a fake success.

The former pending-client workflow now owns real Phase 6 Android checks.
Backend and Web remain in their dedicated workflows. No production CD is enabled.
All contributor workflows use SHA pins, no secret inputs, and no pull_request_target.
The local check guide is in development.md. Dependabot updates uv, npm, Gradle and Actions weekly. License remains owner-pending; Contract v1 public receiving has passed.

After actual successful Phase 5 PR runs, Owner should add exactly **Web quality**,
**Web tests**, **Web dependency audit**, **CodeQL Web** to Protect main if desired,
preserving the existing seven checks and strict up-to-date branches. No settings
were changed. Review both advanced CodeQL language categories in Code Scanning;
no competing default-setup workflow is needed. All 23 implementation-head PR checks passed (PR #10, `1eb49b7`); later revisions
need separate exact-head results. Alert API access returned 403; Owner UI review
remains required. See [Phase 5 evidence](phase-5-review.md).

Web test setup uses separate bounded install/unit/build/browser steps. Temporary
Ubuntu runners use official HTTPS Ubuntu package mirrors with bounded APT timeouts
and retries; repository signatures/TLS verification remain enabled. This avoids
stalls observed on the runner's Azure HTTP mirror. Browser tests remain mandatory;
failed installs fail the job. Compose cleanup runs only after local configuration
initialization succeeded, and still runs if later integration tests fail.

Phase 6 introduces these exact names (definitions are not yet hosted evidence):

| Exact status-check name | Coverage |
| --- | --- |
| Android quality | API DTO drift, wrapper hash, Kotlin warnings-as-errors, Android lint and JVM/network/security tests |
| Android build | Debug and unsigned/minified release build, locked/checksummed dependencies |
| Android dependency audit | Fail-closed OSV Maven audit of locked dependencies/toolchain |
| Android device tests (API 26) | Real synthetic backend/native UI, Keystore/permission/lifecycle |
| Android device tests (API 35) | Same native journeys on newer OS |
| CodeQL Android | Manual compiled Java/Kotlin security-extended analysis |

The branch-rules API on 2026-10-08 confirms all seven original backend/bootstrap
checks plus Web quality, Web tests, Web dependency audit and CodeQL Web are now
required with strict up-to-date branches (eleven total). No settings were changed.
Only add the Android names above after exact-head hosted success and Owner review.
Keep all existing protections/checks. Device inputs/reports, APKs, screenshots, logs
and recordings are not uploaded as public artifacts. Gradle runs do not enable build
scans. No private provider credentials enter client or CI configuration.
