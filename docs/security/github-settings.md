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

Required checks were intentionally left unset until successful real Phase 1 PR
runs. Product Owner then adds the exact names in ../ci.md, selecting GitHub
Actions as the provider. Do not require pending Web/Android checks or treat zero
GitHub-required approvals as permission to bypass the explicit owner phase review.

CodeQL/application scanning was intentionally deferred until runtime existed.
Phase 1 prepares the advanced Python workflow with only analysis-upload write
permission. After reviewing the PR, verify Code scanning setup/results in GitHub;
use the committed advanced workflow rather than a duplicate default setup. If
upload is unavailable, enable the supported advanced configuration manually.
The integration never changes repository settings through an alternate API path.

License stays owner-pending. Course Package handoff stays pending before Phase 2.
Before future CD, configure isolated staging/production identities and approval;
there is no production environment or deployment authorization in this phase.
Token-default/allowed-action policies still deserve owner verification in the UI.
Keep security evidence public-safe; never publish raw configuration/incident logs.
