# CI state and gates

Phase 0 defines CI; no hosted successful run is claimed before owner-authorized
push. A green bootstrap job means its named checks passed, not that an application
build, security hardening or production acceptance exists.

| Gate | Definition | State |
| --- | --- | --- |
| Bootstrap checks | Compile tooling, validate docs/links and handoff inventory; check indexed/historical confidential paths | Active workflow; locally exercised |
| Security checks | Pinned Gitleaks on actual index and reachable main/HEAD history; redacted output | Active workflow; locally exercised |
| Backend checks | Future format/lint/types/unit/integration/security/build, dependency scanning | Pending; runtime absent |
| Web checks | Future locked install, lint/types/components/build/security | Pending; app absent |
| Android checks | Future verified Gradle wrapper, lint/unit/instrumentation/build/security | Pending; app absent |
| Application CodeQL | Python, JavaScript/TypeScript and Java/Kotlin when real sources exist | Pending |
| Dependency audit | Locked ecosystem scans and release severity gate | Pending application manifests |
| Deployment | Staging verification and explicit production approval | Absent; not authorized |

ci.yml runs real bootstrap and security checks on pushes/PRs with read-only tokens,
full checkout for history and commit-SHA-pinned actions. It uploads no artifacts
and has no secrets/private corpus dependency. Full PR HEAD is scanned, including
commits not yet on main. Dependabot reviews pinned Actions updates weekly.

application-gates.yml is manual-only. Each backend/Web/Android job currently
**fails with PENDING and exit 2**, because there is no application to check.
This is a visible fail-closed skeleton, not a fake passing test. It is not a
required main check until replaced with real application commands/locks.
Its jobs must not be interpreted as production verification or triggered as a
way to approve Phase 0. Activate real per-PR jobs as each runtime is authorized.

No CodeQL workflow is enabled for empty application directories. Bootstrap
syntax/document checks are not SAST coverage. Use CodeQL/default or advanced
setup once sources/toolchains exist, and enforce actionable alert thresholds.
Security features and branch protections are owner actions in
security/github-settings.md. Do not lower gates merely to merge a scaffold.
