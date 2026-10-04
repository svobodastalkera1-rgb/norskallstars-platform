# Course integration runtime

Contract v1 is an immutable upstream snapshot with individually reviewed hashes.
Backend wheels include only schemas/specification and generic reference validator;
fixtures, receiving metadata and raw packages never enter runtime images.
The platform wrapper resolves schemas offline, enforces importer 1.0.0/schema 1.0.x,
strict JSON (duplicate keys/non-finite values rejected), bounded strings/depth/nodes,
ZIP/path/count/ratio/size (central directory counted before entry allocation;
multidisk/ZIP64/directory entries rejected), version fields max64 characters and upstream cross-file/checksum/media semantics.

Each accepted CourseRelease stores the full validated course/chapter/lesson/activity
JSON snapshot, manifest, schema/content/course versions, logical package digest,
original ZIP hash, importer version and schema provenance hash. Keeping JSONB
preserves extensible contract fields without creating learning-engine assumptions.
ReleaseAsset maps asset metadata/checksum to private storage keys; ReleaseEvent
records import/publication actor/approval/time. These are curriculum release
persistence, not users/progress/evaluation models. Migration 0002 owns three tables.

Import validates before any transaction. PostgreSQL advisory transaction locks
serialize course/version identity; exact logical content repeats return the same
release with no duplicate audit/assets even after ZIP repacking. Different bytes
for an existing course/version reject. New versions stage independently. All DB
writes use one transaction; storage/validation/commit failures cannot accept partial
course state. Storage uses isolated per-attempt release namespaces and verifies
stored bytes. A failed/uncertain transaction may leave private unreferenced objects;
never delete them blindly on ambiguous commit, and never expose them publicly.
Controlled orphan reconciliation/retention is future operational work.

Publication locks the staged release, requires release_eligible=true plus upstream
approval semantics, rejects flagged synthetic fixtures, verifies asset bytes, and
records an audit event atomically. Repeats are idempotent. A package flag is never
operator authorization or evidence of real-world approval by itself.

No public import/publish/media HTTP route exists. The trusted operator CLI requires
OS/runtime access, DB/storage privileges, explicit actor and approval references,
and a separate --confirm-publication option. Restrict those privileges out of band;
actor text is an audit assertion by a trusted operator, not an identity system.
This is a minimal protected transition before Phases 3/10 provide identity/RBAC/UI.
No production operation is executed or authorized by development tests.

Local/test CLI: `uv run --locked --project apps/backend python -m
norskallstars_backend.course_packages.cli import <private-zip> --actor <operator>
--approval <private-reference>` with externally injected valid settings and local
storage root. Max storage size must cover the chosen package asset size (Contract
max32MiB). Never put sensitive values in shell history/public logs. Staging/production
reject local storage; CLI fails closed without an approved production adapter.
The service accepts the Phase 1 ObjectStorage protocol; S3/delivery remains deferred.
Future integrations must provide a tested private adapter before live publication.

Validation is bounded in-memory with temporary files; it is an offline privileged
job, not arbitrary HTTP ingestion. Run unfamiliar/large packages in a constrained
worker/container with CPU/memory/temp-disk limits. No package content executes.
Upstream uses deprecated RefResolver (jsonschema 4.x locked); platform schema
validation uses modern offline Registry. Upstream migration needs reviewed handoff,
not local rewriting of its approved bytes.
