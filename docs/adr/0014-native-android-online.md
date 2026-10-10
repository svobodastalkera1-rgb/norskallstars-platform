# 0014 — Native online client, protected sessions and ephemeral media

Status: Accepted engineering decision within authorized Phase 6; implementation review pending
Date: 2026-10-08

## Context

Accepted Web PR #10 is merged. Phase 6 adds native Android online journeys;
Phase 7 owns content caching/downloads/offline attempts and synchronization.
The existing backend remains authoritative for identity, authorization,
learning policies, evaluation, release pinning, progress and media access.

## Decision

Use Kotlin/Jetpack Compose, lifecycle-owned ViewModel/StateFlow and separate
HTTP/platform adapters. Generate Kotlin DTOs from the three accepted OpenAPI
contracts with drift checks. Render only backend presentations; never load
Course Packages, implement answer grading or infer policy from synthetic IDs.

Store the native device session as AES-GCM ciphertext in app-private no-backup
storage; key material stays in Android Keystore. Disable app backups/screenshots.
No password, Google proof or learner response is persisted by the client. Serialize
refresh; durably discard its stored credential before making a rotation request.
An ambiguous rotation/process failure requires sign-in rather than credential
reuse. Account-generation checks reject old-account replies. Logout, revocation
and deletion clear credentials, private UI and ephemeral media. Existing backend
session/device and fresh-proof semantics are the sole identity mechanism.

Use a single explicitly configured HTTPS origin, system trust, no cookies,
redirects or HTTP debug logging. Mutating/challenge/refresh/fresh-proof calls never
replay automatically. A GET may recover once on a fresh connection after an EOF,
connection or socket failure, subject to the same account-generation guard. Each
call remains bounded by the transport timeout; Other HTTP errors, TLS errors and timeouts
are not retried; an authenticated 401 uses the existing serialized session-refresh
boundary once before retrying the unauthorized operation. Only debug builds
may use narrowly allowlisted emulator/loopback cleartext origins. A public Google
client ID enables Credential Manager with backend-issued nonce/challenge proof;
it supplies no authorization itself. Live provider acceptance remains separate.

Native media interaction uses private ephemeral files, with startup cleanup,
screen/account cleanup and background microphone/player release. This is not
offline content persistence. Enforce bounded downloads/image decoding and bounded
mono AAC/MP4 recording. Ask microphone permission only on user action. Apply
accepted voice-1 consent/server sampling before reading/uploading audio, preserve
withdrawal after an ambiguous upload, and expose retained-record withdrawal through
existing ownership-protected APIs. No ML evaluator/training or media URL bypass.

Active-time evidence uses foreground/recent input and existing sequenced backend
heartbeats; background/idle time is excluded. Evidence never grants learning credit.
Use stable operation UUIDs within a current interaction; durable offline retries
and synchronization remain Phase 7.

## Consequences

Native session continuity differs deliberately from memory-only Web sessions.
Encrypted state is device-bound; uninstall/key loss requires sign-in. A failed
logout network call still removes local credentials; server expiry/revocation
remains authoritative. Unsubmitted responses and local clips are ephemeral; no
offline acceptance is claimed. Device/provider accessibility, actual staging
authentication and production storage/erasure still need their explicit gates.
No backend domain schema/migration, privileged HTTP, import or production
deployment is introduced. Android API 26 is the engineering compatibility floor;
final supported-device/store policy remains a release acceptance decision.
