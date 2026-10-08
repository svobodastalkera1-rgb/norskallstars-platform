# 0013 — Web sessions, private media and bounded voice retention

Status: Accepted engineering decision within authorized Phase 5; implementation review pending
Date: 2026-10-07

## Context

Phase 5 delivers the responsive React/TypeScript client against accepted Identity
and Learning Core. Product Owner accepted separate voice consent, an explicit
processing purpose, selective collection, at most twelve months and erasure with
account deletion. The earlier indefinite-retention request is superseded; accepted
Identity/Learning Core account erasure remains intact. ML is not implemented.

## Decision

Keep bearer access/refresh credentials exclusively in tab memory. Reload requires
sign-in; no localStorage, IndexedDB, cookies or URL credentials are introduced.
Serialize refresh within the API client; never retry a used refresh token after an
ambiguous network failure. Clear account-owned UI state and recording/media blobs
on logout/revocation/deletion. No backend rules or package interpretation in Web.

Deliver assets through bounded authenticated enrollment/lesson-scoped API calls,
checking published eligibility, pinned release, lesson access and declared asset
references. Return only allowlisted image/audio bytes with digest verification,
no storage keys or vendor URLs. Object URLs are temporary browser presentation.

Add optional private recording offers scoped to owned attempts/speech activities.
Separate explicit consent version/purpose from ordinary learning submission. Server
samples once per attempt/activity; sampling rate is explicit environment configuration,
zero/disabled when unset. Unselected audio never leaves the browser. Selected offers
expire; bounded audio containers and checksums are verified before storage. Store
only necessary consent/provenance metadata and compressed audio, with a calendar-year
maximum expiry. No collection for model training is authorized. Operator processing
of speaking responses is the purpose; a future evaluator needs separate authorization.
Learner responses remain evaluated by accepted modes, with future evaluation pending.

Account deletion cascades recording mappings; withdrawal/deletion also removes access.
A private cleanup worker expires records and reconciles orphan objects. Physical
object erasure follows bounded scheduled cleanup, including account deletion; no
indefinite tombstone retaining user identity is added. Backups/production scheduling
and provider acceptance remain explicit production gates.

Object inventory is an optional storage capability separate from put/get/delete.
All platform writes and GC acquire the same PostgreSQL transaction advisory lock:
writers share it until their reference transaction commits, GC holds it exclusively.
GC checks references immediately before deletion, observes an explicit grace period,
bounds inventory/batches, records pseudonymous object-key hashes and deletion outcomes,
and retries idempotently. Course references in staged AND published releases are
retained. Failed imports remain atomic; their orphan objects become collectible.
Existing local adapter is development-only; S3-compatible storage uses verified TLS,
explicit external credentials and a private bucket, without vendor-domain coupling.

## Alternatives and consequences

Persistent browser bearer tokens enlarge credential exposure; a cookie/BFF would
change accepted transport. Memory sessions sacrifice reload continuity deliberately.
Anonymous static course assets would bypass release/access boundaries. Uploading every
recording then sampling would violate minimization. Compression is not anonymization.
Distributed storage/DB cannot share a transaction, so references/access are removed
transactionally and objects reclaimed by coordinated retryable cleanup. Long imports
can delay exclusive GC; resource bounds and PostgreSQL timeouts limit that cost.
No Redis, ML platform, administrator HTTP, export feature or production deployment.
