# CI state and required checks

Phase 0 bootstrap/security gates remain active. Phase 1 adds real backend gates;
Web/Android remain pending and are not represented by passing placeholder jobs.
Hosted outcomes are recorded with their actual revision/run in Phase 1 review
and reported after completion; existence of a workflow is not a passing result.

| Exact status-check name | Real checks |
| --- | --- |
| Bootstrap checks | Tooling syntax/docs links and confidentiality safeguard tests/index/history |
| Security checks | Checksum-pinned redacted Gitleaks index and reachable history scan |
| Backend quality | Locked environment; Ruff format/lint/security rules; strict mypy |
| Backend tests | Real isolated PostgreSQL tests, migration roundtrip/drift and backend tests |
| Backend dependency audit | Full locked runtime/dev dependency vulnerability audit |
| Backend container | Digest-pinned image build, Compose migrations/startup and HTTP/security/runtime smoke |
| CodeQL Python | Python security-extended analysis of runtime and repository scripts |

After successful Phase 1 PR runs, the Product Owner adds these exact names to
Protect main required status checks, using the GitHub Actions provider and
confirming names in the actual PR. No required-check setting is changed here.
The owner intentionally deferred required checks until real Phase 1 runs.

The CodeQL advanced workflow uses contents/actions read and security-events write
only for analysis upload. It never receives private content or production secrets.
The owner should review Code scanning availability/results and use the committed
advanced workflow; do not activate a competing default-setup pipeline. If GitHub
rejects upload because setup is not enabled, enable the supported advanced setup
manually; do not bypass permissions or substitute a fake success.

The manual pending-client workflow still exits 2 for Web/Android; do not add those
pending names to required checks. Backend was removed from that skeleton because
backend.yml now owns its real checks. No production CD workflow is enabled.
All contributor workflows use SHA pins, no secret inputs, and no pull_request_target.
The local check guide is in development.md. Dependabot updates uv and Actions
weekly. License and Contract v1 handoff remain owner-pending decisions.
