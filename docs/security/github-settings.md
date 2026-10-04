# GitHub settings and owner actions

After Phase 0, Product Owner confirmed the following manual setup. The ruleset
was independently checked via read-only API before Phase 1: Protect main is active
and targets the default branch, with deletion/non-fast-forward restrictions,
linear history, pull requests and conversation resolution; approvals 0 and
allowed merge methods Squash/Rebase. No settings are changed by this PR.

Completed owner actions:
- Protect main as above; direct development in main is prohibited.
- Private vulnerability reporting enabled.
- Dependency graph and automatic dependency submission enabled.
- Dependabot alerts, malware alerts and security updates enabled.
- Secret scanning and push protection enabled.

Product Owner configured seven required Actions checks after Phase 1 (verified
via ruleset API on 2026-10-04): Bootstrap checks, Security checks, Backend quality,
Backend tests, Backend dependency audit, Backend container, CodeQL Python. Strict
up-to-date branches are required. Generated CodeQL remains advisory, not a required
ruleset entry. No Web/Android pending checks are required. Zero required approvals
does not override explicit Product Owner review/merge requirements.

Phase 1 PR #4 was merged by the approved workflow. All three main engineering
workflows succeeded. Owner verified default-branch scanning healthy and no alerts
at acceptance. Advanced Python CodeQL operates; no duplicate default setup or
settings bypass is introduced. Review new results per PR; acceptance-time absence
of alerts is not a guarantee about later commits. License stays owner-pending.
Controlled Contract v1 public receiving passed for Phase 2.
Before future CD, configure isolated staging/production identities and approval;
there is no production environment or deployment authorization in this phase.
Token-default/allowed-action policies still deserve owner verification in the UI.
Keep security evidence public-safe; never publish raw configuration/incident logs.
