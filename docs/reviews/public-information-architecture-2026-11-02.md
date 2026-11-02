# Public information architecture audit — 2026-11-02

Scope: documentation only, after Owner-accepted Android PR #17 merged at
`8a05b73c2b8ae5e04ce5d80982354e4c0906951a`. No runtime, contract, dependency,
visual rollout or private content changes.

## Ownership and disposition

A = product/portfolio; B = stable engineering reference; C = current execution
memory; D = historical/review evidence; E = obsolete/duplicated/misleading claim.

| Surface | Classification | Disposition |
| --- | --- | --- |
| Root README | A; former C/D/E content | Product proposition, implemented capabilities, architecture, boundaries, setup and navigation; remove transient phase/PR status |
| SECURITY | B; former C/E content | Reporting/scope/disclosure policy; controls and operational evidence linked separately |
| ROADMAP | Future direction / C | Preserve full production scope; close accepted Android, leave later phases unauthorized |
| PROJECT_STATE | C; accumulated D/E snapshots | Current accepted baseline, authority and deferred gates; archive previous snapshots |
| TASKS | C; accumulated D/E checklists | Current review, separately authorized integration and production gates; completed lists archived |
| AGENTS | B operating instructions with phase limits | Update accepted Android, preserve workflow/confidentiality/no-automatic-phase constraints |
| docs index | B navigation; previously absent | Add routes for architecture, development, security, product and evidence readers |
| Architecture / ADR indexes | B; stale E client status | Describe current Web/native clients and accepted decisions; do not rewrite ADR history |
| Product-world index | B authority/provenance | Keep normative pointers and copy boundaries; remove CI/merge diary from index |
| Security baseline / CI reference | B; stale E bootstrap limits | Describe actual Python/Web/Android checks; eleven required contexts, dated setting evidence separate |
| Development / Android guide | B; stale E runtime/client statements | Correct directly misleading runtime/client descriptions, retain commands/toolchain pins |
| Changelog / dated phase reviews | D | Retain historical delivery evidence; correct current Unreleased authority summary |

Original PROJECT_STATE and TASKS contents from the baseline commit are preserved
in the [dated archive](engineering-memory-before-android-closure-2026-11-02.md),
with relative links rebased. Original phase/security review records remain in
place. No useful evidence was discarded to make the README look cleaner.

## Capability evidence used for README

| Claim | Current implementation evidence |
| --- | --- |
| Shared identity and revocable sessions | [Identity module](../../apps/backend/src/norskallstars_backend/identity/), [API](../../contracts/api/identity-v1.openapi.json), [ADR 0011](../adr/0011-shared-identity.md) |
| Canonical learning, release pinning and replay | [Learning module](../../apps/backend/src/norskallstars_backend/learning/), [normative rules](../architecture/learning-core.md), [API](../../contracts/api/learning-v1.openapi.json) |
| Controlled immutable course release ingestion | [Course integration](../architecture/course-integration.md), [ADR 0010](../adr/0010-course-release-import.md) |
| Web learning/account/media surfaces | [Client source](../../apps/web/src/), [component/browser tests](../../apps/web/tests/) |
| Native online client and secure platform adapters | [Android source](../../apps/android/app/src/main/java/com/norskallstars/platform/), [unit tests](../../apps/android/app/src/test/), [device tests](../../apps/android/app/src/androidTest/), Owner-merged PR #17 |
| Storage, media, recording consent and cleanup | [Media module](../../apps/backend/src/norskallstars_backend/media/), [ADR 0013](../adr/0013-web-media-privacy.md), [media API](../../contracts/api/media-v1.openapi.json) |
| Migrations and regression/security gates | [Backend](../../apps/backend/), [workflows](../../.github/workflows/), [repository tests](../../tests/) |

These establish code/test capability, not production deployment, scale, live
provider acceptance, final visual approval or real course acceptance. Public
examples remain synthetic and release-ineligible. No private inputs were used.

## Remaining public presentation limits

No production deployment, production adoption or approved Experience visual
showcase is claimed. Owner subsequently selected proprietary / All Rights Reserved
terms in [LICENSE](../../LICENSE); earlier license-pending snapshots are historical. Current visuals are not normative examples
of the future world direction; do not substitute speculative mockups as evidence.
Historical documents intentionally retain dated pending statuses and detailed
reviews. Their index and current-state pointers make that context explicit.
The integrated Experience slice remains contract READY / IMPLEMENTATION NOT STARTED.
