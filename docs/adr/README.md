# Architecture decision records

ADRs record consequential engineering decisions and alternatives, not tasks.
Number them sequentially. Create a proposed record from template.md, discuss
material product/security deviations with the owner, and mark accepted only
within authorized engineering scope. Supersede an accepted ADR with a new linked
record rather than erasing decision history. Product Owner accepted the Phase 0 engineering
choices on 2026-10-03; future changes follow the same review process.

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-repository-topology.md) | Public platform monorepo | Accepted |
| [0002](0002-backend-architecture.md) | Modular monolith and baseline stack | Accepted |
| [0003](0003-api-strategy.md) | Versioned backend API and contract evolution | Accepted |
| [0004](0004-content-boundary.md) | Public engineering / private content separation | Accepted |
| [0005](0005-course-package-boundary.md) | Controlled handoff; no invented Contract v1 | Accepted |
| [0006](0006-configuration-secrets.md) | Validated external configuration and secret injection | Accepted |
| [0007](0007-environments.md) | Isolated local/test/staging/production environments | Accepted |
| [0008](0008-async-postgresql-migrations.md) | Async PostgreSQL lifecycle and baseline revision | Accepted; Phase 1 owner-accepted |
| [0009](0009-object-storage-boundary.md) | Vendor-neutral object boundary and development adapter | Accepted; Phase 1 owner-accepted |
| [0010](0010-course-release-import.md) | Immutable staged releases and privileged transitions | Accepted; Phase 2 owner-accepted |
| [0011](0011-shared-identity.md) | Transactional shared identity and opaque sessions | Accepted; Phase 3 owner-accepted, PR #8 merged |
| [0012](0012-learning-policy-progress.md) | Versioned learning policies and release-pinned canonical progress | Accepted; Phase 4 owner-accepted, PR #9 merged |
