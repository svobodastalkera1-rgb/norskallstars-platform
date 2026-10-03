# Phase 1 runtime threat/security review

Scope: infrastructure-only backend, local Docker runtime, database/migrations,
configuration, logging, health and local object operations. No product data,
identity, private packages or production deployment is exercised.

| Threat | Implemented control | Evidence / remaining boundary |
| --- | --- | --- |
| Insecure configuration | Required explicit environment/strong password, typed bounded values; deployed TLS/CA/host rules; no implicit .env | Positive/negative settings tests; live production TLS handshake not yet exercised |
| API information exposure | Minimal health payloads; generic 4xx/5xx; disabled deployed docs/debug | Runtime tests with injected sensitive exceptions/validation inputs |
| Logging leakage | Event allowlist; no message args/exception values, headers, bodies or query paths | Secret-like input/log redaction tests; raw framework access logging disabled |
| Resource exhaustion | Bounded body reads, content length, request/probe/query/connect timeouts and pools | Oversize streamed/body and timeout tests; rate limiting accompanies future sensitive endpoints |
| Untrusted host/origin | Explicit trusted hosts; no wildcard CORS, no credentialed CORS in Phase 1 | Host rejection and unallowed-origin tests; identity transport remains undecided |
| Database mishandling | Escaped URL values, hidden SQL parameters, transaction ownership and disposal | Real PostgreSQL commit/rollback/migration tests; production least-privilege roles remain deployment responsibility |
| Unsafe object paths | Strict keys; descriptor-relative no-follow access; bounded regular-file reads; atomic replace | Traversal/symlink/oversize/roundtrip tests; local root/ancestors must be trusted |
| Container privilege/data exposure | Nonroot UID 10001, runtime-only locked dependencies, positive context allowlist; read-only/cap-drop/no-new-privileges Compose app | Real image/startup inspection; local database superuser is development-only |
| Dependency compromise | Locked public-index dependencies; digest-pinned images; SHA-pinned Actions; pip-audit and Dependabot | Audit runtime plus dev packages; no claim of an OS-image CVE scan |
| Static code defects | Ruff security rules, strict mypy and prepared Python CodeQL workflow | Hosted CodeQL result must be checked separately; no repository-setting bypass |

The local generated password resides only in ignored .cache/phase1.env, mode 600.
Never expose docker inspect/config output publicly: runtime environment contains
credentials. The smoke helper captures configuration internally and prints only
safe assertions. Do not commit private acceptance outputs or logs.

Repository protections/security features are owner-configured, documented in
github-settings.md. No guard suppression or policy weakening is introduced.
Known development-host limitation: this workspace has legacy and nft forwarding
rules simultaneously; normal inter-container bridge traffic is blocked. No host
firewall was modified. A loopback-only diagnostic container validated the image
locally; the standard Compose path is also exercised on hosted CI.

This is a Phase 1 review, not production hardening acceptance. Before release,
verify real deployment TLS/roles, operational controls, OS-image vulnerabilities,
recovery and the later authentication/authorization/content delivery threat models.
