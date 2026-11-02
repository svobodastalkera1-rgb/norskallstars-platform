# Security engineering

[SECURITY.md](../../SECURITY.md) defines private reporting and disclosure policy.
This reference describes implemented boundaries and validation. Production/provider
acceptance and Owner actions remain in [project state](../../PROJECT_STATE.md)
and [the settings record](github-settings.md); no scan is a perpetual guarantee.

| Boundary | Implemented controls / verification |
| --- | --- |
| Confidential content | Index/reachable-history guards, approved public artifact inventories, human receiving review and synthetic-only public tests |
| Secrets | Checksum-pinned redacted Gitleaks, staged-byte checks, optional local hooks and CI; externally injected runtime secrets |
| Dependencies | Locked uv/npm/Gradle graphs, audits and reviewed Dependabot updates; no advisory suppression to obtain green checks |
| Static analysis | Ruff security lint, strict backend typing and advanced CodeQL for Python, Web and Android |
| Identity / learner data | Session authentication, ownership, cross-account regressions, fresh proof, revocation and deletion semantics |
| Untrusted packages / media | Bounded validation, immutable staged releases, controlled publication, authenticated media and coordinated retention/GC |
| Clients | Memory-only browser credentials, Android Keystore-backed sessions, lifecycle cleanup and consent-based selective recording |
| Delivery workflow | Protected-main PR workflow, eleven required checks and strict up-to-date branches; additional Android checks run in CI |

Actions are pinned to full commit SHAs. Contributor workflows use read-only default
permissions and no production secrets/private course materials. Code scanning has
scoped upload permissions. Do not use pull_request_target to execute contributor
code. Logs and uploaded diagnostics must be public-safe; no raw learner responses,
credentials, private inputs or arbitrary exception payloads.

Threat reviews record threat → control → evidence/residual risk at a point in time:
[backend](phase-1-review.md), [course integration](phase-2-review.md),
[identity](phase-3-review.md), [learning](phase-4-review.md),
[Web/media](phase-5-review.md), [Android](phase-6-review.md).
Historical provider/operational gates are not silently closed by client acceptance.
See [confidentiality](confidentiality.md) and [CI reference](../ci.md).

Primary references: [GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use),
[CodeQL](https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-code-scanning),
[OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)
and [OWASP API Security](https://owasp.org/www-project-api-security/).
