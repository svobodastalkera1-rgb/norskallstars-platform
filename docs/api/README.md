# API direction

Future platform endpoints use a versioned HTTPS JSON API with a reviewed OpenAPI
surface. Validate DTOs, bound payloads/pagination, and maintain an explicit error
policy without internal traces. Enforce ownership/access at resource boundaries.
Generated clients must follow compatibility review, not database models.
Stable event/operation IDs and content versions will support offline reconciliation.
Phase 3 now supplies the versioned [Identity API](../architecture/identity.md)
and [reviewed OpenAPI](../../contracts/api/identity-v1.openapi.json). ADR 0011
defines actual bearer-session transport; sync remains a later phase. See ../adr/0003-api-strategy.md.

Phase 4 supplies authenticated [Learning Core](../architecture/learning-core.md)
and [Learning OpenAPI](../../contracts/api/learning-v1.openapi.json). Identity remains
its sole authentication model. The separate platform learning policy does not
redefine Course Package v1; no importer/publication/admin/media API is introduced.
