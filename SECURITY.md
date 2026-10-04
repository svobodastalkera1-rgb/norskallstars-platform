# Security policy

## Reporting

Do not report exploitable vulnerabilities, secrets or private content in public
issues. Use the repository Security tab's private vulnerability reporting action
enabled by Product Owner after Phase 0.
If that action is unavailable, request a private reporting channel from the
owner without including exploit details or confidential payloads publicly.
Do not upload private corpora or user data as reproduction artifacts.

There is no production release or supported-version maintenance promise yet.
Before release, maintainers must define supported versions, triage ownership,
notification and fix procedures. No response-time SLA is claimed in bootstrap.

## Baseline

Treat the source and exposed interfaces as public knowledge. Use explicit
server-side authorization, least privilege, fail-closed validation, safe defaults,
data minimization and defense in depth. Administrative and content-delivery
permissions must not rely on client flags or unguessable identifiers.

Review boundaries: identity/session policy, resource ownership, entitlements,
admin MFA/RBAC, package/archive input, upload/media delivery, sync replay,
browser injection/CSRF, billing callbacks/promotions, and sensitive logging.
Domain controls remain future implementation requirements. Phase 1 runtime
controls and evidence are in docs/security/phase-1-review.md.

Repository controls and remaining owner actions are documented in
[security baseline](docs/security/README.md),
[confidentiality](docs/security/confidentiality.md), and
[GitHub settings](docs/security/github-settings.md).
