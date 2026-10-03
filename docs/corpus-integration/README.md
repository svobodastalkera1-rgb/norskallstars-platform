# Course Package integration readiness

Contract v1 already exists upstream. This repository does not define a competing
format. The integration dependency is **pending controlled public handoff**.
Schemas, compatibility rules, PUBLIC_HANDOFF and the approved synthetic fixture
are not present. No private corpus inspection, importer or pilot test is authorized.

## Controlled transfer procedure

1. Owner supplies only the public-safe subset authorized by the actual upstream
   PUBLIC_HANDOFF. Obtain explicit confirmation and public-safe provenance.
2. Review files outside the tracked tree for secrets, real teaching material,
   embedded media/prompts and unintended generated artifacts. Approval must cover
   every file; do not attach the private pilot or an upstream repository snapshot.
3. Place approved contract/docs/schemas under contracts/course-package and an
   approved synthetic fixture under fixtures/course-package. Use the actual
   handoff layout/semantics; bootstrap prescribes neither schema fields nor block types.
4. Update handoff-manifest.json: status received, approval as a public-safe review
   reference/record, and artifacts containing path, sha256, role for every file.
   This is a local provenance inventory, not part of the upstream package contract.
5. Run confidentiality/secret checks and owner review before committing artifacts.
   Only then mark handoff ready and authorize Phase 2 importer implementation.

The upstream contract controls package structure. Compare actual compatibility
rules against platform assumptions and record a meaningful ADR if needed.
Never reinterpret this pending inventory as approval for private materials.

## Future implementation boundary

An untrusted package will cross structural/security/schema/checksum/compatibility
and semantic checks before transactional staged import. Later publication is
explicit, privileged and audited; raw archive input cannot execute code. Plan
limits and negative tests for traversal, bombs, oversized entries, duplicate paths/
IDs, malformed data, broken references and unsafe media. Contract details wait
for handoff. API delivery and protected media are platform responsibilities,
separate from corpus generation or illustration approval.

The first automated integration uses only the approved synthetic fixture. It
must make developer/demo runs independent of private content. Owner-supplied
private pilot acceptance happens in Phase 14 in a controlled private environment;
no private fixture or resulting content is uploaded to public CI artifacts.
