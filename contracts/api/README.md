# Platform API contracts

[identity-v1.openapi.json](identity-v1.openapi.json) is generated from Phase 3
FastAPI routes/validated DTOs; Backend quality checks exact drift. Compatibility
changes require explicit review under ADR 0003. No generated client/runtime is
introduced here. See [identity API](../../docs/architecture/identity.md).
These contracts do not redefine upstream Course Package v1.

[learning-v1.openapi.json](learning-v1.openapi.json) describes the authenticated
Phase 4 learner API. Both domain snapshots contain their reachable schemas and
are generated from the actual app. Identity bytes remain unchanged. The complete
app OpenAPI combines them; no generated client is implemented in Phase 4.
