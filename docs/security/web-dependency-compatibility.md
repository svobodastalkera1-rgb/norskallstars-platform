# Web tooling compatibility migration — 2026-11-01

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

## Relationship to other PRs

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

## Local validation evidence

Final local validation: npm ci with install scripts disabled, low-severity npm
audit zero, lint/format, TypeScript/production build, three unchanged generated
contracts, 24 unit/component and four tooling/API/guard tests passed. Full browser
recheck passed 9/9 across Chromium/Firefox/WebKit. The first local run passed 8/9
and hit the existing 30-second WebKit image-decoding wait; an unchanged isolated
WebKit retry passed 3/3, then the full clean recheck passed 9/9. No assertion,
timeout or browser gate was relaxed. Repository 32/32 tests and confidentiality/
secret checks passed. Hosted results must still be verified for the actual PR head.
