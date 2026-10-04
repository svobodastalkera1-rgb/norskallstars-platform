# Course Package integration

Course Package Contract v1 arrived through controlled public receiving on
2026-10-04. The platform inventory is contracts/course-package/handoff-manifest.json;
25 upstream-approved artifacts retain their exact bytes under its upstream tree.
The format is public; package instances/corpus remain private. No private repo
access or pilot import occurred. See [repeatable receiving](receiving.md).

Schemas/reference validator define upstream Contract v1; platform-specific
resource/compatibility checks wrap them rather than invent a replacement.
The synthetic fixture is for tests only and remains release_eligible=false.
It is stored once beside upstream tests so their relative layout stays intact;
fixtures/course-package contains the consumer entry documentation.

Phase 2 introduces versioned immutable staged import and explicit audited
privileged publication, separate from future identity/Admin UI/learning behavior.
See [integration architecture](../architecture/course-integration.md).
