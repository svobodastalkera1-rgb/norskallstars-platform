# Public repository security baseline

Implemented locally: confidentiality ignore rules, an indexed-path/content guard,
a pre-commit hook, pinned Gitleaks, reachable-history checks and active CI
security job definitions. Remote execution/settings remain unverified or pending.

| Layer | Bootstrap state | Later gate |
| --- | --- | --- |
| Confidential content | Index/history path rules and public handoff manifest | Human approval for every imported artifact |
| Secrets | Redacted Gitleaks in index/history and pre-commit | Owner enables GitHub alerts and push protection |
| Dependencies | Weekly GitHub Actions update config | Add locked Python/npm/Gradle ecosystems when manifests exist; scan known vulnerabilities |
| SAST | Bootstrap Python compile/static repository checks; no security coverage claim | Enable CodeQL Python, JavaScript/TypeScript and Java/Kotlin as applications exist |
| Main protection | Owner action required | PR review + actual required checks; no force pushes as normal workflow |
| Vulnerability reporting | SECURITY.md and owner enablement checklist | Private triage, supported versions and remediation policy before release |
| Runtime security | Architecture requirements only | Threat model and negative resource/auth/import/sync/billing tests |

Pin Actions to full commit SHAs. Run untrusted PRs with read-only permissions,
without repository secrets or private course materials; do not use
pull_request_target to execute contributor code. Keep artifacts/logs public-safe.
Dependency updates need review, compatibility checks and security assessment.
No security scan can establish that a document is approved for publication.

Primary references:
- [GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use)
- [GitHub secret scanning](https://docs.github.com/en/code-security/concepts/secret-security/secret-scanning)
- [GitHub push protection](https://docs.github.com/en/code-security/concepts/secret-security/push-protection)
- [CodeQL](https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-code-scanning)
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
