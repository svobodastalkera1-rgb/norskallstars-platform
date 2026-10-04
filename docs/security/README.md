# Public repository security baseline

Implemented locally: confidentiality ignore rules, an indexed-path/content guard,
a pre-commit hook, pinned Gitleaks, reachable-history checks and active CI
security job definitions. Owner-confirmed repository settings are recorded in github-settings.md; Phase 1
adds runtime guards, dependency audit and a Python CodeQL workflow.

| Layer | Bootstrap state | Later gate |
| --- | --- | --- |
| Confidential content | Index/history path rules and public handoff manifest | Human approval for every imported artifact |
| Secrets | Redacted Gitleaks in index/history and pre-commit | Owner confirmed alerts/push protection enabled |
| Dependencies | Weekly GitHub Actions update config | uv lock/audit and update config now exist; npm/Gradle remain deferred |
| SAST | Ruff security lint and prepared Python CodeQL | Verify hosted Python analysis; client languages wait for runtime |
| Main protection | Active Protect main ruleset | Seven real checks active with strict up-to-date branches; no bypass/automatic merge |
| Vulnerability reporting | Private vulnerability reporting enabled by owner | Private triage, supported versions and remediation policy before release |
| Runtime security | Phase 1 threat review and bounded/safe infrastructure | Threat model and negative resource/auth/import/sync/billing tests |

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

Phase 3 adds [identity threat review](phase-3-review.md): ownership, Google/token
verification, session replay, input/abuse bounds, account deletion and private mail.
No course HTTP publication/admin authority or production storage is added.
