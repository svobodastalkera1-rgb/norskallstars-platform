# Web tooling compatibility migration — 2026-11-01

## Baseline security integration

The independent integration branch starts directly at main
`5669565dea726313ec2cf07d3d4f14ce3a825137`. It combines the exact backend lockfile
from PR #26 (`6aa7570197144e7a55e28f22bd8e705b3dc666e6`), the undici fix from
PR #23 (`8d753d2c8647d6aa85db193eac43e5631986118a`) and Web matcher/tooling code
from PR #25 (`deac27a85d4876cee84f07b6c6be07e905643dac`). No compatibility conflict
was encountered. No remediation is redesigned; Web package files, adapter/tests
and backend lockfile are identical to their validated source PRs.

PR #25's project-state/task notes are excluded from the focused integration diff.
No Experience Contract publication, Android, Corpus, vertical-slice or unrelated
Dependabot changes are included. Original PRs remain open/unmodified; identify
#23/#25/#26 as superseded only after the integration actually lands. PR #24 can
then be cleaned against the new main separately. No automatic merge/closure.

The PR relationships and older-base warnings later in this document describe the
original Web-only PR #25. The integration includes both security baselines so
Backend and Web audits can pass together without weakening global required checks.

Integration local validation passed on 2026-11-01: strict backend audit and low-
severity npm audit both report zero vulnerabilities; Backend 245/245, Contract
19/19, Web unit/component 24/24, tooling/API guards 4/4, all three isolated browser
projects 9/9 and repository 32/32 passed. Ruff, strict mypy, type/build, unchanged
OpenAPI generation/drift, lock/frozen validation, confidentiality/secret and diff
checks passed. Actual hosted checks must additionally pass on the integration PR.

Scope: dependency security and development-tool compatibility only. No application
behavior, Experience Contract semantics, Course Package v1, Corpus, UI design,
private material or new roadmap phase changes.

## Dependency evidence and reviewed resolution

The npm advisory GHSA-g3hv-75wg-m249 affects minimatch <11.0.1. The original
lockfile contains 10.2.6 (ESLint/TypeScript-ESLint) and 5.1.9 (Redocly).
The thirteen moderate audit findings are the vulnerable leaf plus its dependent
chains, not thirteen independent application vulnerabilities.

| Consumer path | Parent versions retained | Previous minimatch constraint | Reviewed resolution |
| --- | --- | --- | --- |
| eslint | 10.12.0 | ^10.2.5 | Scoped override ^11.0.1; resolved 11.0.3 |
| eslint → @eslint/config-array | 0.23.5 | ^10.2.4 | Scoped override ^11.0.1; resolved 11.0.3 |
| typescript-eslint → @typescript-eslint/typescript-estree | 8.71.1 | ^10.2.2 | Scoped override ^11.0.1; resolved 11.0.3 |
| openapi-typescript → @redocly/openapi-core | 7.13.0 → 1.34.20 | 5.1.9 | Scoped override ^11.0.1; resolved 11.0.3; legacy import adapter |

Registry checks found that ESLint 10.14.0/config-array 0.23.5 and TypeScript-ESLint
8.72.1 still require minimatch 10; compatible Redocly 1.34.x releases through
1.34.22 still pin 5.1.9. openapi-typescript 7.13.0 still requires Redocly ^1.34.6
and imports its deep ref-utils paths. Redocly 2.72.1 removes minimatch but its
exports map does not expose those paths. It is not a compatible drop-in parent
upgrade for the current generator. No compatible upstream-only version set was
found; Owner explicitly authorized a separate compatibility migration.

The selected parent versions remain unchanged. Four narrow overrides advance
only the affected leaf to the security-fixed major; no global override, audit
suppression, forced install/downgrade or unrelated dependency update is introduced.
The new @isaacs/nonrecursive-glob-match 1.0.3 dependency belongs to minimatch 11's
fixed matching implementation. Old minimatch/brace-expansion copies are removed.
Node 24.21.0 remains pinned and satisfies the new leaf's engine requirement.

## OpenAPI adapter and update discipline

Redocly 1 calls the minimatch 5 CommonJS function export; minimatch 11 exposes the
named minimatch function. The explicit repository-owned preparation command is the first step of
`npm run contracts` and adapts exactly that import. It does not modify the
minimatch algorithm, dependency version, lockfile, advisory or audit result.
The three generated client contracts must remain byte-identical.

`apps/web/scripts/prepare-openapi-tooling.mjs` accepts only the exact reviewed
original or already-adapted SHA-256 of Redocly's utils.js. Changed source fails
closed and requires compatibility review. It checks regular files/directories,
rejects symlink redirects, bounds input, validates adapted bytes and is idempotent.
An interrupted preparation fails subsequent hash checks; a fresh npm ci restores
locked upstream bytes. No general-purpose vendor patch engine or install hook is
introduced. Existing CI still uses `npm ci --ignore-scripts`; preparation is
part of the explicitly invoked contracts command, not an install/pre/post lifecycle
hook or permission for third-party install scripts.

Tests cover exact adaptation/idempotence, unknown-source refusal without writes,
symlink refusal, and the actual Redocly URL/header matching API: intended URLs
receive only synthetic test headers and unrelated hosts/paths do not. This catches
the real callable-export incompatibility rather than merely checking package names.
Lint/type/build and unchanged generated contracts exercise the retained consumers.

On dependency updates, review any checksum failure. Remove the scoped overrides/
adapter only after supported parent releases use a safe matcher and all regression,
contract-drift and security gates pass. Never update accepted hashes automatically
to suppress failure. Compatibility is established for this repository's exercised
APIs, not every feature of the upstream tools.

## Historical relationship of Web-only PR #25 to other PRs

This migration is stacked on Dependabot PR #23's exact undici 8.11.2 → 8.12.3
commit. That commit removes the eight undici advisories/high finding. The migration
diff excludes its change; PR #23 remains independently required/useful and is not
merged, closed or superseded automatically. Local npm audit at low severity must
report zero vulnerabilities for the combined dependency graph.

PR #24 separately remediates the backend lockfile and publishes approved Experience
documentation. This migration changes neither that branch nor contract semantics.
Backend audits against this PR's older base may still fail until the independent
backend security fix reaches its base; required checks are not weakened to bypass
that dependency. Other Dependabot tool/action/type upgrades are not incorporated.

At review time, unrelated open Dependabot proposals are #2/#3/#18/#21/#22
(Actions), #5 (backend hatchling), and #11–#15 (TypeScript, formatter, type and
test-library updates). They are not incorporated or superseded; retain their
independent review. No existing PR is merged or closed by this migration.

## Reproduction

```sh
cd apps/web
npm ci --ignore-scripts
npm audit --audit-level=low
npm ls minimatch --all
npm run format
npm run lint
npm run build
npm run contracts
git diff --exit-code -- src/identity.generated.ts src/learning.generated.ts src/media.generated.ts
npm run test
```

From the repository root run `make web-e2e`, `make check`, `make security-check`
and `git diff --check`. Browser journeys use only the existing synthetic mechanisms;
never publish generated credentials, browser traces or sensitive artifacts.

## Historical local validation evidence for Web-only PR #25

Final local validation: npm ci with install scripts disabled, low-severity npm
audit zero, lint/format, TypeScript/production build, three unchanged generated
contracts, 24 unit/component and four tooling/API/guard tests passed. Full browser
recheck passed 9/9 across Chromium/Firefox/WebKit. The first local run passed 8/9
and hit the existing 30-second WebKit image-decoding wait; an unchanged isolated
WebKit retry passed 3/3, then the full clean recheck passed 9/9. No assertion,
timeout or browser gate was relaxed. Repository 32/32 tests and confidentiality/
secret checks passed. Hosted results must still be verified for the actual PR head.
