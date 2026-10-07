# Phase 4 learning threat review

Scope: authenticated learning, immutable platform rules, account-owned evidence and
trusted operator rule selection. No production/storage delivery/import, external mail,
live Google provider, client application or private corpus is exercised. This record
is a review of implemented controls; actual test/run evidence belongs to phase-4-review.md.

| Threat / boundary | Implemented control | Added regression |
| --- | --- | --- |
| Parallel/forged identity | Accepted bearer Principal and locked account/session checks in every transaction; client user IDs/roles are invalid | Missing auth, role/account injection, revoked/deleted sessions |
| IDOR / foreign locks | Enrollment/attempt/placement/cursor ownership in SQL before row locks; opaque foreign/unknown 404 | Cross-account all-interface/cursor/placement tests; foreign locked attempt remains inaccessible without blocking |
| Completion forgery / replay | Server evaluator and persisted version-bound evidence, explicit thresholds, unique operation IDs, transactional state/events | Incorrect/client-graded responses, duplicate/concurrent submissions and idempotent credit |
| Deletion/write race | Identity account-first serialization and cascading learning FKs in the existing delete transaction | Concurrent submit/delete; no recreated or retained personal learning rows |
| Partial learning state | One PostgreSQL transaction for evaluation, progress/review/events and attempt finalization; constraints | Injected failure after state changes; rollback and retry |
| Version reinterpretation | Enrollment pins immutable release and policy; explicit operator selection only affects new enrollments | Published replacement, old learner continuity, new enrollment and policy-version conflict |
| Placement/adaptive bypass | Advisory result/acceptance and noncanonical practice; no skipped completion/mastery | Recommendation/acceptance leaves canonical state untouched and linear gates intact |
| Hidden content disclosure | Explicit DTO fields; no accepted answers, normalization/rule keys, internal metadata/notes, transcripts or storage keys; translation requires an explicit event | Curriculum/assessment projection sentinels and explicit translation |
| Private learner data | Own-account responses/results/history only, no body/identity logging, no-store; account-lifetime retention/cascade | Cross-account history and response/log sentinels; deletion erases all learning tables |
| Ambiguous grading/config | Full compatible typed policy, explicit normalization bindings and opaque extension acknowledgment; missing/unknown inputs fail closed | Missing coverage/answers, unsupported flags/extension hashes, future required evaluators |
| Parser/resource abuse | Same HTTPS/origin/cookie/header policy as Identity; 32 KiB/depth8/4096-node learning JSON, duplicate/nonfinite/NUL checks; bounded history/attempts/enrollments/compatible snapshot | Oversize/deep/duplicate/1e999/NaN/NUL, duplicate activities, persistent account rate limit |
| Public source confidentiality | Private policy instances ignored and rejected even if forced into an index; original handoff byte inventory unchanged | Real-index policy rejection and prior guard/receiving/Contract suites |
| Privileged operation confusion | Only trusted OS/DB operator CLI can select already-published release/policy; actor/approval still assertions, never RBAC | Staged/synthetic release rejection; no admin/import/publish/media HTTP surface |

Ordinary authenticated verified accounts can currently enroll in selected published
courses. Paid-content entitlements are a separate Phase 9 gate, not claimed here.
Course instances and private learner data do not become anonymous/public simply
because the source/contract are public. Client phases must render course strings
as content, never executable HTML/scripts; safe rendering/accessibility are client gates.

No concrete production numeric policy, course content or default pedagogical threshold
is provided. Explicit policy instances can contain private answers and remain external
runtime data. Catalog/list endpoints project bounded summaries rather than accumulating
large course snapshots. Learning compatibility currently caps JSON snapshot at 8 MiB
and activities per lesson at 200. These are resource limits, not pilot assumptions;
budget evolution needs evidence and compatibility review. All current tests are synthetic.

Remaining gates: live SMTP/Google staging acceptance (SMTP at-least-once), production
TLS/role/at-rest protection and operational controls, client token/CSRF/secure storage,
administrator MFA/RBAC, wider privacy/retention/export and monitoring. Required learning
records are retained for account lifetime and erased on account deletion; no indefinite
exception or actual export feature is introduced. Credential/rate-bucket maintenance
retains its previously accepted bounded security TTL, not learning responses.

Mandatory storage orphan reconciliation/retention/GC is unchanged. Learning returns
asset references, never bytes/URLs/keys and introduces no remote adapter/delivery/import.
Before such a production path, verify inventory/DB references, in-flight protection,
grace, immediate reference re-check, audited deletion, retention, retry and race tests.
