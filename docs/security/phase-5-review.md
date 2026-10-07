# Phase 5 working-tree security review

Date: 2026-10-07. Engineering implementation/review in progress, **not accepted**.
Full local backend (243), Web unit/component (16) and browser E2E/accessibility (9)
regressions passed, including cross-account/race/failure checks. Locked backend/npm
audits found no known vulnerabilities. Final container smoke passed. Hosted checks
and Owner review remain pending; live provider/operations acceptance is not claimed.
See [scope](../web/README.md), [ADR 0013](../adr/0013-web-media-privacy.md) and
[current evidence](../phase-5-review.md).

| Boundary | Implemented control | Review coverage / remaining acceptance |
| --- | --- | --- |
| Browser identity | Tab-memory bearer credentials, serialized rotation, ambiguous refresh failure clears session; no cookies/browser persistence/URL tokens | Session/cross-browser regression passed; live provider acceptance pending |
| Account isolation | API response generation guards; account UI/blob teardown; backend Phase 3 locked ownership | PostgreSQL/cross-account regressions passed locally |
| Sensitive actions | Existing purpose-bound password/linked Google fresh proof; explicit deletion confirmation | Live Google-only reauthentication in isolated staging |
| HTTP input | Existing HTTPS/origin/host/client/duplicate-key/JSON/body/time/rate guards; media string budget isolated from Identity | Malformed/oversized/unauthenticated route regressions passed locally |
| Course media | Pinned published eligible release, owned enrollment/access and declared asset; checksum/MIME/output bounds; no storage keys/signed URLs | Asset authorization/integrity tests passed locally |
| Recording | User-initiated permission only; stop tracks/revoke blobs; 60-second/256-KiB browser limit; separate consent; server sampling before upload | Real permission/record/playback behavior on supported browsers/devices |
| Private audio | Owned attempt/speech binding; one sample decision per offer; bounded signature/checksum; stable upload retry; opaque errors | PostgreSQL deletion/upload races and sample/expiry tests passed locally |
| Withdrawal/erasure | Own bounded listing after reload; mapping deletion/account cascade; worker physical erasure | Scheduled cleanup SLA, backups/provider erasure acceptance |
| Storage GC | Shared writer/exclusive GC transaction lock; committed mapping expiry; bounded inventory/batch; final re-check; durable audit intent before deletion; retries/grace | Database race/failure/retry tests passed; operational scheduling still required |
| S3 | Explicit HTTPS/credentials; verified TLS; timeouts/retries/bounded reads; AES256; reject enabled/suspended versioning | Actual private bucket/ACL/IAM/encryption/anonymous-denial and provider verification |
| UI rendering | React text escaping; no raw HTML; CSP, no-referrer, nosniff/frame restrictions; media allowlist | Final bundle browser/accessibility regressions passed |
| Learning data | Backend-only grades/completion/access, pinned policies; explicit presentation bindings; nullable legacy timing; private account aggregates | Canonical/placement/replay/pinning/ownership regressions passed |
| Operations | Import/publication/policy/GC stay operator-side; no HTTP admin or client actor assertion | Future administrator MFA/RBAC and production runbooks |

Corrections during review: native fetch receiver no longer binds to Api; offline
migration downgrade uses the already-named constraint; selected upload ambiguity
retains withdrawal capability; permission requests are serialized; Google-only
accounts have linked-provider fresh-proof deletion/password flows; withdrawal
works after a new browser session; downloads are capped before full buffering.
Deletion intent is independently committed before an external delete, so a crash
cannot erase all audit evidence. Expiry mapping commits separately so later failures
cannot restore a DB reference after its external object was deleted.

Microphone bytes are untrusted **opaque data**, not validated safe decoder input.
No server decoder, ML job/training or external evaluator is introduced. A future
processor requires purpose authorization, stronger parsing/sandbox/resource controls
and its own security review. No public recording GET/playback/download endpoint exists.
User withdrawal is not backend administration. An authorized downloaded course asset
can be copied; this design does not promise copy prevention.

Engagement is bounded server-time evidence gated by visible/recently active client
reports, never trusted proof of learning, mastery, billing or gamification. No
client-supplied account ID authorizes a request. Full responses/audio, emails,
credentials and provider tokens are not added to routine logs.

Remaining risks/gates: XSS can access memory sessions (minimized exposure does not
eliminate XSS); browser refresh deliberately requires login. Failed imports/uploads
can retain unmapped private objects until scheduled GC. Account/withdrawal erasure
removes references immediately; physical storage/backups require verified operations.
GC requires all platform writers to participate in its lock protocol; external bucket
writes/deletes must not bypass it. Current inventory covers owned current keys only;
versioned buckets fail closed. No live private S3/SMTP/Google acceptance is claimed.
No production deployment is authorized. Phase 6 has not started.
