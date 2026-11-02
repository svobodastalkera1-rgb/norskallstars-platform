# Security policy

## Scope and supported versions

This policy covers the NorskAllstars Platform backend, Web and Android clients,
public contracts, repository tooling and CI configuration. There is no production
release or versioned security-maintenance commitment yet. Reports against current
main are welcome; include the affected commit/version and environment.
No response-time SLA is promised.

## Report a vulnerability privately

Use [GitHub private vulnerability reporting](https://github.com/svobodastalkera1-rgb/norskallstars-platform/security/advisories/new)
from this repository's Security tab. If unavailable, ask the maintainer for a
private channel without including exploit details in a public Issue or PR.

Include a concise description, affected component/commit, impact, and minimal
reproduction using synthetic data where possible. Do not attach credentials,
private packages, real course content, user data, sensitive logs or production
configuration. Coordinate disclosure with the maintainer while the report is
assessed and remediated; do not publish confidential reproduction material.

## Security boundaries

Source code and interface details are public knowledge. Access control must hold
server-side through authenticated sessions, resource ownership and least privilege.
Client flags, opaque identifiers and operator audit assertions do not establish
privileged authorization.

Treat archives, uploads, external data and user input as untrusted. Preserve
fail-closed validation, bounded processing, safe configuration, data minimization
and privacy-conscious diagnostics. Learner records and retained recordings are
account-owned data. Production secrets and private Corpus material must remain
outside public source, CI logs, Issues, PRs and artifacts.

[Security engineering](docs/security/README.md) describes implemented controls;
[confidentiality](docs/security/confidentiality.md) defines the public/private
boundary. Operational verification and release gates are tracked separately in
[project state](PROJECT_STATE.md), not treated as security guarantees.
