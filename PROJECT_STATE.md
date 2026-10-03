# Project state

Updated: 2026-10-03. Product: NorskAllstars. Platform: NorskAllstars Platform.
Current phase: **Phase 0 prepared; awaiting Product Owner review**.
Phase 1 authorization: **not granted**. Production readiness: **not achieved**.

## Actual implementation

The starting main contained only README.md and specification ignore rules.
Bootstrap adds component boundaries, seven ADRs, public product direction,
phase/release memory, zero-dependency repository tooling, a reproducible tooling
setup, staged confidentiality checks, pinned Gitleaks, and CI skeletons.
No backend server, database, importer, Web/Android application, user model,
authentication, learning functions, or deployed environment exists.

The component paths are documented reservations, not bootstrapped applications.
Application dependencies, lockfiles, SDK/toolchain decisions, and Docker runtime
files belong to subsequent authorized phases.

## Content integration

The real Contract v1, schemas, PUBLIC_HANDOFF and synthetic fixture are external
inputs awaiting controlled transfer. The handoff manifest is pending and empty.
Private corpus access is not authorized. No private pilot or real content is
present. Follow docs/corpus-integration/README.md; do not fill gaps by guessing.

## Verification and CI

Run make check and make security-check. These validate repository boundaries,
local document links, indexed file contents, current-main confidentiality paths,
and secrets in index and reachable history. Active CI definitions cover those
checks. Application gates are pending and manual invocation fails explicitly.
No hosted CI run, CodeQL coverage, or successful application build is claimed.
Local validation passed: 12 guard tests, index/main secret and confidentiality
checks, workflow linting, ignore scenarios and clean-snapshot bootstrap/hook
execution. See docs/ci.md and docs/phase-0-review.md for remaining gates.

## Owner actions / known limitations

- Review Phase 0 and explicitly authorize Phase 1 before application work.
- Supply approved public-safe Course Package artifacts with provenance.
- Configure main protection, required checks, security features and private
  vulnerability reporting per docs/security/github-settings.md. Public API
  reported main unprotected at bootstrap audit; no settings were changed.
- Choose licensing before adding a license or claiming open-source usage rights.
- Resolve later product decisions when their phase needs them; see TASKS.md.
- Prior confidentiality incident: reachable public main was cleaned separately.
  Server-side removal remains a support-review matter, with no purge confirmation
  available to this implementation session. No confidential identifiers, removed
  object links, or private document text are reproduced here. Do not restore it.

Next: owner review. Proposed Phase 1 scope is in TASKS.md, not work in progress.
