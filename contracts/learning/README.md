# Platform learning policy

[policy-v1.schema.json](policy-v1.schema.json) describes a platform LearningPolicy,
not Course Package Contract v1. It is generated from the typed policy model; drift
is checked alongside Learning OpenAPI. Explicit rules are scoped to one release and
immutable policy version/digest. All fields are required: null explicitly means the
capability is not applicable, not an inferred numerical default.

`package_policy_inputs` maps `chapters/<id>.json#completion|review` and
`lessons/<id>.json#completion|review` to SHA-256 of each non-null extension object's
UTF-8 canonical JSON (sorted keys, no whitespace, ensure_ascii=false). It acknowledges
opaque inputs, not their business semantics; complete platform rules are separate.
`normalization` binds each boolean activity flag to a reviewed operation (trim,
case_fold, unicode_nfc); absent/false flags never silently normalize text. Deterministic
scalar answers can use Contract accepted_answers; structured comparison requires
explicit accepted_responses and exact/unordered semantics. A null display override
uses only string prompts/choices; arbitrary objects need reviewed string presentation.

Policy instances can include private answer rules and must remain outside public Git,
images and CI. `learning-policies/` and `*.learning-policy.json` are ignored/rejected;
only the schema and synthetic policies constructed in tests are public. No real policy
or default score/schedule is supplied. The operator CLI validates a bounded external
policy and selects an already-published release; it cannot publish or override eligibility.
See [normative learning architecture](../../docs/architecture/learning-core.md) and
[ADR 0012](../../docs/adr/0012-learning-policy-progress.md).
