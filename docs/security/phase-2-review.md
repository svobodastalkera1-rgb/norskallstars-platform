# Phase 2 security review

Scope: public handoff receiving, generic untrusted package validation, immutable
DB import, private asset references and trusted operator publication. No private
corpus/pilot, identity/Admin UI/client/production deployment is exercised.

| Threat | Control / regression evidence |
| --- | --- |
| Accidental inbound publication | .local ignore + index guard; receiving verifies ignored/untracked/path-and-blob history; ZIP/transfer metadata excluded |
| Archive traversal/special paths | No direct extraction; full preflight, strict path syntax, hidden/special names, duplicate/case collision rejection |
| ZIP bombs/resource exhaustion | Central preflight before ZipFile allocation, count/input/file/total/ratio limits, known compression; JSON size/depth/node/string limits; offline constrained operator job |
| Inventory substitutions | Exact manifest and SHA256SUMS inventory/byte hashes; candidate SHA printed before review and identity-bound acknowledgment |
| Confidential content | Independent text/code/media review, fail-closed heuristics and redacted Gitleaks; exact public provenance inventory and human review |
| Schema remote lookup/parser faults | Only checked-in schemas, offline Registry/all refs checked; strict JSON duplicates/constants; exceptions fail closed with safe codes |
| Semantic/media errors | Upstream schemas/reference/ordering/cycle/checksum/MIME checks plus bounded platform checks; no payload execution |
| Partial/conflicting import | Validation first, one transaction, same-version advisory lock, unique identities; rollback/storage failure/concurrency tests |
| Asset corruption/exposure | Private per-release storage namespace, checksum verification on import/publication; no delivery/public media routes |
| Unauthorized or synthetic publication | Trusted OS/runtime/DB/storage operator boundary, separate explicit confirmation/approval/audit; release-ineligible/flagged synthetic rejected; no anonymous HTTP |
| Diagnostic leakage | Generic CLI response; Phase 1 safe logging/errors preserved; no package validation strings/payload/paths logged |
| Build/dependency compromise | Runtime wheel includes reviewed contract only; context positive allowlist excludes inbound/private data; locked audit and SHA-pinned CodeQL remain |

Acceptance limitations: sender checksums are integrity, not authenticity. SHA
acknowledgment cannot automate semantic privacy review. Supplied executable tools
are independently reviewed, then automatically run in a no-network, no-credentials
read-only disposable container with CPU/memory/PID/temp-disk/deadline bounds. Do not rely on heuristics to recognize arbitrary
real teaching text. Real packages and diagnostics stay private.

Publication requires trusted operator access and externally verified approval;
package flags alone are not authorization. Application identity/RBAC is deferred,
not silently replaced by anonymous API. Staging/production CLI fails closed without
a production storage adapter. Generic ObjectStorage service boundary is ready;
no real production publish is performed. Private orphan objects may survive failed
imports and need controlled retention/reconciliation; no partial DB release is
accepted. A constrained operator worker is needed for large/unfamiliar packages.
The approved upstream validator uses deprecated RefResolver; its exact bytes are
retained with jsonschema 4.x pinned. An upstream modernization handoff is later work.
OS-image scanning and live environment TLS/least-privilege verification remain
existing later acceptance requirements; neither is claimed here.
