# Owner GitHub settings checklist

No remote setting changes are made by Phase 0. The public branch API reported
main unprotected on 2026-10-03. Other features require owner verification rather
than simulated enablement. Settings availability can depend on account/plan.

- [ ] Protect main with a branch rule/ruleset: pull requests, at least one owner
  review where staffing permits, dismissal/reapproval after substantive changes,
  resolved conversations, and required passing checks from trusted Actions runs.
- [ ] After a real hosted run, require **Bootstrap checks** and **Security checks**
  from Phase 0 CI. Confirm actual check names in GitHub before configuring them.
  Add backend/Web/Android gates only once implemented and exercised.
- [ ] Restrict direct pushes, force pushes and branch deletion; minimize bypass
  roles. Document unavoidable solo-maintainer limitations instead of claiming
  independent review is always possible.
- [ ] Enable/verify secret scanning alerts and repository push protection.
  Keep personal push protection enabled as a supplement, not a substitute.
- [ ] Enable Dependabot alerts/security updates; review weekly Actions updates.
  Add ecosystem update jobs and vulnerability scans when real lockfiles exist.
- [ ] Enable private vulnerability reporting and confirm the SECURITY.md route works.
- [ ] Configure GitHub Actions read-only default token permissions and allowed
  actions; require full-SHA pins and protect workflow/security-policy changes.
- [ ] Enable CodeQL/code scanning for real application sources when available;
  security findings and severity policy must become actual release gates.
- [ ] Before future CD, configure isolated staging/production environments and
  production approval with least-privilege runtime credentials. Do not configure
  production access just to finish bootstrap.

Retain private screenshots/settings evidence or public-safe confirmation; never
commit admin credentials, bypass details or internal incident object links.
