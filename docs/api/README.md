# API direction

Future platform endpoints use a versioned HTTPS JSON API with a reviewed OpenAPI
surface. Validate DTOs, bound payloads/pagination, and maintain an explicit error
policy without internal traces. Enforce ownership/access at resource boundaries.
Generated clients must follow compatibility review, not database models.
Stable event/operation IDs and content versions will support offline reconciliation.
The session transport and concrete endpoints are later designs; no authentication
or sync protocol is silently selected here. See ../adr/0003-api-strategy.md.
