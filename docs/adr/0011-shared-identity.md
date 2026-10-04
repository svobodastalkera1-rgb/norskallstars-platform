# 0011 — Shared transactional identity and opaque sessions

Status: Accepted engineering decision within authorized Phase 3; owner review pending
Date: 2026-10-04

## Context

ROADMAP Phase 3 and product-direction.md require shared Web/Android accounts,
email/password and Google sign-in, verification/recovery, preferences, revocable
sessions/devices, ownership authorization and self-service deletion. Clients,
learning, billing, administration/MFA and production deployment remain later phases.
Phase 2 operator audit assertions are not authentication or authorization.

## Decision

Use an identity module in the existing modular monolith and PostgreSQL transaction
boundary. Use `/api/v1/identity` (ADR 0003), validated DTOs and a generated, reviewed
OpenAPI contract. Authenticate opaque bearer access tokens against committed
server sessions. Store purpose-separated HMAC digests, not plaintext tokens.
Access expires in 15 minutes, refresh after 7 idle days, sessions after 30 absolute
days or 256 rotations. Rotation invalidates previous access; refresh replay commits
family revocation before responding with an error. Limit active devices to ten.
These are documented security limits, not trusted device attestation.

Passwords use NFC normalization, 15–128 characters, an initial common-password
blocklist and Argon2id (64 MiB, three iterations, one lane). Two dedicated workers
and twenty pending slots bound computation even if requests are cancelled. Persist
HMAC rate buckets across instances; no Redis is necessary for this scope.

Use single-use verification/recovery tokens and five-minute, session/account/purpose
bound reauthentication proofs for password changes, Google linking and deletion.
Commit encrypted mail outbox messages with account/token state; a private operator
worker uses authenticated, certificate-verified SMTP TLS. Local private mail files
are available only in local/test. No HTTP worker, recipient override or mail-debug
endpoint exists. Delivery is at least once with bounded leases/retries; SMTP cannot
be rolled back. Credential expiry/consumption remains authoritative.

Validate Google signatures with reviewed PyJWT/cryptography, fixed HTTPS JWKS,
bounded fetch/cache, explicit issuer/audience/authorized-party, freshness/expiry,
verified email, subject and single-use nonce challenge. Provider subject is the
identity key. Never auto-link based on email equality. Google is authoritative for
Gmail/Workspace email only; other addresses require platform email verification.
Existing-account linking requires that account's authenticated session and fresh
password or existing Google proof. No caller chooses roles or account ownership.

Bearer credentials are returned only in JSON; no cookie authentication is introduced.
Require explicit origin allowlists and a custom client header for mutations (request
shape/CSRF mitigation, not authentication). Reject cookies, URL parameters, duplicate
JSON/critical headers, oversized/deep JSON and unknown fields. Future Web must review
secure browser token persistence/CSRF before implementation: no localStorage tokens
are approved here. Android secure token persistence belongs to Phase 6. A future
cookie/BFF adapter requires its own security/compatibility review.

Delete the account and all identity-owned credentials/providers/sessions/mail in
one transaction after fresh, single-use reauthentication. There are no user-linked
learning/financial records yet. Future domains must add explicit erasure/anonymization
hooks; lawful financial retention and broader privacy policies remain owner decisions
before applicable production acceptance. No course release is account-owned here.

## Alternatives

Self-contained long-lived JWT sessions complicate immediate revocation and account
delete. Managed identity would add a provider dependency and does not remove local
ownership obligations. Automatically merging provider emails enables account takeover.
Adding Redis without demonstrated need duplicates PostgreSQL coordination. Privileged
course HTTP or Admin UI would expand Phase 3 and require separate MFA/RBAC design.

## Consequences

PostgreSQL is required for identity authorization and rate enforcement: fail closed
on outage. Tokens/keys/mail never belong in logs, OpenAPI examples or CI artifacts.
Pepper rotation invalidates credentials; mail-key rotation requires an explicit queue
migration/reissue procedure. Staging/production require external keys, HTTPS origin,
explicit Google audiences and SMTP settings; deployment is not performed here.
Live provider/browser/device acceptance waits for owner configuration and later
clients; deterministic tests verify real crypto and DB behavior without credentials.
Course import/publication remains operator-side, untouched by ordinary identity.
Storage reconciliation remains a mandatory separate production gate.

References: [Google ID token verification](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token),
[OWASP authentication guidance](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html),
[PyJWT usage](https://pyjwt.readthedocs.io/en/stable/usage.html).
