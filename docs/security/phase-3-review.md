# Phase 3 identity threat review

Scope: public-safe Identity API and private mail maintenance. No privileged course
HTTP, real users/mail/provider credentials, production object storage, media delivery,
Web/Android client or deployment is exercised. Historical Phase 1/2 reviews remain
unchanged. Phase 3 derives from the production roadmap, not provisional pilot data.

| Boundary/threat | Implemented control | Regression evidence |
| --- | --- | --- |
| Credentials/config leakage | Independent required redacted keys; external TLS SMTP/Google configuration in staging/production; generic startup failure; no image secrets | Invalid config/secret representation tests; Docker positive build context; index/history Gitleaks |
| Password compromise/CPU exhaustion | Argon2id; NFC, 15–128 length and initial blocklist; two workers/twenty slots retained through cancellation | Real hashes/verification, invalid inputs, cancellation/queue regression |
| Enumeration/brute force/mail spam | Equal password work, generic signup/recovery/resend responses; persisted HMAC IP/account/global buckets; no raw addresses | Unknown/unverified/duplicate responses; persistent 429 and log redaction tests |
| Bearer theft/replay | Hash-only tokens, short access, rotating refresh, replay commits revocation; absolute/idle/rotation/device bounds | Rotation/replay, concurrent rotation, access/refresh expiry and ten-device tests |
| Ownership/privilege bypass | Server session principal, account-first row locks, ownership filters before row locks and opaque 404; no roles or account override | IDOR/session isolation and cross-account deadlock regression; role rejection; no course/admin routes |
| Google forgery/SSRF/provider merge | Fixed verified HTTPS JWKS, no redirects/proxies; bounded key cache/fetch; RS256, audience/issuer/expiry/freshness/azp/verified-email/subject/nonce | Actual RSA crypto; wrong signature/algorithm/claims; unknown keys/cooldown/resource tests; nonce replay |
| Account linking takeover | Provider subject identity; no email auto-merge; link needs fresh own-session proof; third-party email locally verified | Existing email conflict, provider ownership/conflict, Google-only verification/recovery and reauth tests |
| Browser CSRF/input ambiguity | Bearer-only, no ambient cookies; explicit origins, HTTPS in staging/production, custom mutation header, JSON, no URL tokens; 32 KiB/depth/node/duplicate/header/field limits | Origin/cookie/header/content-type/query/oversize/deep/duplicate/role tests; generic errors |
| Password/reset/deletion race | Account row locks, purpose/account/session bound single-use proof, full transactional cascade/invalidation | Expired/wrong-purpose/wrong-account/session proof; recovery/revoke-all/deletion rollback tests |
| Mail queue/external effects | Fernet payloads, account-fixed recipient, transactional outbox, SKIP LOCKED lease, expiry, bounded retry, verified SMTP TLS; no debug HTTP | Byte encryption, transaction rollback, TLS transport assertions, lease/retry/retention tests |
| Error/log/cache disclosure | Existing safe formatter, no body/header/query/email; generic errors, no-store and production docs disabled | Sensitive sentinel/logging tests and retained infrastructure suite |
| Prior accepted boundaries | Contract bytes/import/storage unchanged; no corpus access; no new publication authority | Previous 40 integration tests, 19 upstream tests, 23 guard/receiver tests; confidentiality index/history scans |

## Findings and remaining gates

No production-readiness claim is made. Deterministic Google tests use ephemeral
RSA test keys and controlled key retrieval; SMTP tests use a controlled transport
and assert system-CA hostname verification. They do not replace actual configured
provider/staging acceptance. Owner must verify allowed Google audiences/consent,
Google Web/native proof flows, sender authentication and SMTP delivery before
live operation. No provider/account registration or external mail is performed here.

Routine logs deliberately omit email, IP, account IDs and request payloads; diagnostics
retain safe exception types/frame positions. Operational abuse detection and edge
limits need production hardening. The initial local password blocklist is limited;
review broader compromised-password coverage without disclosing passwords off-platform
before release. Account/voice/telemetry and lawful financial retention require owner
policy; future domain deletion hooks cannot be skipped. Mail worker/cleanup scheduling,
monitoring and controlled key rotation are production operations gates. In-flight mail
can arrive after account deletion, but its token is invalid; delivery is at least once.

Bearer transport requires reviewed secure client persistence (no localStorage approval),
Web CSRF/cookie adapter review if introduced and Android OS-protected secrets. API keys,
authenticated ordinary accounts, client headers and Phase 2 audit flags do not grant
administration/publication. Phase 10 requires separate MFA/RBAC design.

Phase 2 private orphan-object storage is an accepted development-only operational
limitation. Identity adds no production/remote asset storage or media route. Before
any production import/media/storage path: mandatory inventory reconciliation, active
import protection, grace/reference re-check, auditable deletion, retention, retries
and race/failure tests remain release gates. Never blindly delete after ambiguous commit.

Final security review reproduced a cross-account session-revocation deadlock in
an adversarial two-transaction test. Ownership filters now precede row locking
for session/proof lookups; both unauthorized requests return 404 without locking
foreign sessions or revoking either account. This was fixed within Phase 3 before
owner review; the failing regression was demonstrated against the earlier code.
