# Release strategy

CHANGELOG.md records user-visible or engineering milestone changes under
Unreleased until a reviewed release. Phase 0 has no production release/tag.
The planned product version scheme is SemVer; public API and upstream Course
Package versions are independently reviewed contracts. A backend/client release
must state compatibility and migrations rather than assume matching version numbers.

After real builds exist, PR CI covers formatting/static analysis/tests/security
and builds. Reviewed main/release artifacts are promoted to isolated staging,
verified, and approved for production. Use immutable artifacts and retain safe
recovery evidence. Critical/high security findings block a production release
unless the owner explicitly records accepted risk. Store publication, deployment,
signing and external provider changes need their own authorization.

Do not claim a production-ready version from a bootstrap tag, demo or skipped
checks. License selection remains an owner action; no license is assumed here.
