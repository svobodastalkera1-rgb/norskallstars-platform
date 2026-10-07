# CI state and required checks

Phase 0 bootstrap/security gates remain active. Phase 1 adds real backend gates;
Phase 5 introduces real Web workflows; Android remains explicitly pending.
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
changed by development PRs. Web/Android pending names must never be required.

The CodeQL advanced workflow uses contents/actions read and security-events write
only for analysis upload. It never receives private content or production secrets.
The owner should review Code scanning availability/results and use the committed
advanced workflow; do not activate a competing default-setup pipeline. If GitHub
rejects upload because setup is not enabled, enable the supported advanced setup
manually; do not bypass permissions or substitute a fake success.

The manual pending-client workflow still exits 2 for Android; do not add those
pending names to required checks. Backend was removed from that skeleton because
backend.yml now owns its real checks. No production CD workflow is enabled.
All contributor workflows use SHA pins, no secret inputs, and no pull_request_target.
The local check guide is in development.md. Dependabot updates uv, npm and Actions weekly. License remains owner-pending; Contract v1 public receiving has passed.

After actual successful Phase 5 PR runs, Owner should add exactly **Web quality**,
**Web tests**, **Web dependency audit**, **CodeQL Web** to Protect main if desired,
preserving the existing seven checks and strict up-to-date branches. No settings
were changed. Review both advanced CodeQL language categories in Code Scanning;
no competing default-setup workflow is needed. All 23 implementation-head PR checks passed (PR #10, `1eb49b7`); later revisions
need separate exact-head results. Alert API access returned 403; Owner UI review
remains required. See [Phase 5 evidence](phase-5-review.md).
