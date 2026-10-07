# Identity — Phase 3

Authority: [ROADMAP](../../ROADMAP.md), [public product direction](product-direction.md),
[TASKS](../../TASKS.md), [ADR 0011](../adr/0011-shared-identity.md).
Phase 0/1/2/3 are now CLOSED/ACCEPTED; PR #8 merged into main at
d03336a52559cf247e1fe3a7af3c33205d7c05ee. Before Identity implementation, PR #7 merged at
fce1def7c805c59f4292fc20180c112c14bc2d61, verified before implementation.
Historical phase review records remain dated evidence.

## Objective and acceptance

One backend account for future Web and Android. In scope: email/password and
Google sign-in, verification, recovery, interface-language preference, revocable
sessions/devices, own-account/session authorization and deletion of all current
identity-owned data. Norwegian Bokmål (`nb`) is the default preference; it does
not translate or otherwise interpret any Course Package. No pilot counts, IDs,
wording or activity mix inform identity.

Out of scope: learning/progress, client UI/token persistence, entitlements/billing,
Admin UI/MFA/RBAC, HTTP course import/publication/media, storage adapters, deployment
and private corpus access. Ordinary account authentication confers no operator
publication/import permission. The Phase 2 CLI assertions remain audit intent only.

DoD: real startup/API flows and migrations; generic opaque errors; verified ownership,
one-use tokens, replay/revocation, bounded inputs/work, transactional account/token/mail
and deletion behavior; truthful locked dependencies/OpenAPI; all previous regression
suites, identity unit/integration/security tests, quality/audit/container/safeguard/
CodeQL hosted checks pass at the exact PR head. Owner accepted and merged PR #8;
Phase 4 Learning Core is now authorized, with its approved normative policies documented
in [Learning Core](learning-core.md). This is phase acceptance, not production
release acceptance. Live staging SMTP/Google verification remains open.

## HTTP inventory

All routes use `/api/v1/identity`. Health remains `/health/live`, `/health/ready`.
Development-only `/docs`, `/openapi.json`, `/docs/oauth2-redirect` remain absent in
staging/production. Error responses contain only a code and request UUID. All responses
are `no-store`; no request bodies, headers, tokens, email or URLs enter routine logs.

| Method/path suffix | Authorization | Behavior |
| --- | --- | --- |
| POST /register | Public, bounded | Generic 202; no overwrite of existing account |
| POST /verification/request | Public, bounded | Generic 202; single-use email confirmation |
| POST /verification/confirm | Single-use verification token | Confirm email; replay/expiry rejected |
| POST /password/recovery | Public, bounded | Generic 202 for known/unknown addresses |
| POST /password/reset | Single-use recovery token | Set password, revoke every session/proof |
| POST /sign-in | Verified email/password | Create bounded device session |
| POST /sessions/refresh | Rotating refresh token | New access/refresh; replay revokes session |
| POST /google/challenge | Public, explicit configured audience | Five-minute challenge/nonce |
| POST /google/sign-in | Verified Google proof and challenge | Subject-based account; no auto-link |
| GET /me | Bearer | Own account/preferences/sign-in methods |
| PATCH /me/preferences | Bearer | Own interface-language preference |
| GET /sessions | Bearer | Own active sessions; no token hashes |
| DELETE /sessions/{session_id} | Bearer + ownership | Own session logout/revoke; opaque 404 otherwise |
| POST /sessions/revoke-all | Bearer | Revoke all own sessions including current |
| POST /reauthenticate | Bearer + password/existing Google proof | Single-use purpose-bound proof |
| POST /password/change | Bearer + password-purpose proof | Set password and revoke all sessions |
| POST /me/google | Bearer + link-purpose proof + Google challenge | Link unclaimed provider; conflicts rejected |
| DELETE /me | Bearer + delete-purpose proof | Transactional identity erasure/cascade |

POST/PATCH/DELETE need `X-NorskAllstars-Client: web`, `android` or `operator` and
JSON (bodyless session DELETE can omit content type). That header never proves
identity/privilege. Browser origins must be explicitly allowed; cookies and query
parameters are rejected. Protected endpoints use Authorization: Bearer; there is
no account-id override and no privileged role in signup/preferences fields.

The checked-in [OpenAPI](../../contracts/api/identity-v1.openapi.json) is generated
from actual routes/DTOs; Backend quality detects drift. Generate from repository root:

```sh
uv run --locked --project apps/backend python -m norskallstars_backend.identity.openapi contracts/api/identity-v1.openapi.json
```

## Data and transactions

Migration 0003_identity follows immutable 0002_course_releases. Seven identity
tables cover accounts, Google subjects, device sessions, refresh history, one-use
credentials, encrypted outbox and pseudonymous rate buckets. Email canonicalization
uses validated normalized email + case folding (no provider-specific dot/alias merge).
Unique email/subject constraints and consistent row/advisory locks serialize signup,
provider linking, refresh and account writes. New accounts are verified before access.
Unverified Google third-party addresses receive platform verification.

Verification expires in 24 hours; recovery in 30 minutes. Reauthentication and Google
challenges expire in five minutes. Password reset/change and account deletion invalidate
sessions; replay detection remains committed even when returning 401. Concurrent refresh
is deliberately strict: clients serialize it, because a second use revokes the family.
A lost refresh response requires sign-in, not unsafe reuse. Access is 15 minutes;
refresh is 7 idle days; absolute session 30 days; at most 256 rotations and ten active
devices. The device label is user-controlled presentation, not a security signal.

Outbox shares account/token transactions but SMTP is an external, at-least-once
side effect. A 30-second lease, five attempts, bounded batch and recipient fixed to
the account prevent an arbitrary mail relay. Stable Message-ID supports deduplication;
provider delivery cannot be guaranteed exactly once. Re-check queue before sending;
concurrent account deletion can race already-in-flight SMTP, but deletes all tokens.
Delivered/expired payloads and expired credentials/rate buckets are cleared by the
private maintenance command; session tombstones are removed after a day, expired
sessions immediately. This technical credential retention is not the wider privacy
policy. Unverified account retention and future domain/financial retention need owner
policy before production; account deletion immediately erases current identity data.

Maintenance requires trusted operator configuration, not user HTTP or Phase 2 actor
strings. Commands run against an explicitly configured environment:

```sh
python -m norskallstars_backend.identity.cli mail --limit 20
python -m norskallstars_backend.identity.cli cleanup
```

In local/test outbox mode, mail needs `--private-directory /absolute/ignored/directory`.
See [development](../development.md). Never attach generated messages to CI/PRs.
Schedule/drain/monitor this worker and cleanup before live mail operation; Phase 12
runbooks must cover stuck leases, retries, key rotation and invalid-token reissue.

## Deployment and future security gates

Required runtime keys have no defaults. Production/staging additionally reject
outbox-only transport, HTTP links, missing Google audiences or authenticated TLS SMTP.
Google consent/client configuration, mail sender authorization and isolated staging
flow checks are Product Owner actions; no accounts/providers/deployment are created.
Staging/production Identity rejects cleartext ASGI requests; it never trusts a raw
forwarded-proto header. Terminate TLS at the process or a explicitly trusted proxy.
Behind a proxy, forwarding headers must be stripped/replaced by a separately trusted
proxy and enabled only for its explicit addresses. The current image disables proxy
headers; peer IP is the rate key. Per-operation limits are 60/IP per 10 minutes,
6/email per 10 minutes for email/password entry points and 300/global per minute;
all identity HTTP additionally bounds 120/IP and 300/global per minute. Calibrate
limits and edge abuse controls using staging evidence before release. Changing IP
never bypasses the account/global limits. Bucket counters persist denied attempts.

Account deletion hooks must expand with each later user-data domain. Premium/media
ownership and administrator MFA/RBAC are not satisfied by ordinary bearer auth.
Web token persistence/CSRF and Android secure storage await their client phases.
No production/course object-store path is introduced here: the accepted Phase 2
orphan limitation and mandatory inventory/reconciliation/retention/GC gate remain
in TASKS, PROJECT_STATE and ROADMAP before any such path becomes reachable.
