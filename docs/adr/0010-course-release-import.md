# 0010 — Immutable staged releases and privileged operator transitions

Status: Accepted engineering decision; Phase 2 owner review pending
Date: 2026-10-04

## Context

Actual Contract v1 is now received. It contains extensible payload and provisional
synthetic content; learning/identity/admin UI are later phases. Import must be
repeatable and publication protected before those phases.

## Decision

Preserve byte-inventoried upstream schemas/tools; wrap them with bounded platform
validation. Store immutable versioned CourseRelease JSONB snapshots, asset mappings
and transition audit, retaining package/version/schema provenance. Serialize same
course/version with PostgreSQL transaction locks and reject conflicting versions.
Object writes use isolated release namespaces; DB rollback never accepts partial
state. Use a trusted operator service/CLI for explicit audited publication, with
OS/DB/storage privileges as its access boundary; expose no anonymous HTTP command.

## Alternatives

Mapping every activity/block to premature learning tables risks locking current
pilot semantics into architecture. Anonymous endpoints would weaken release safety.
Implementing full accounts/Admin UI now crosses phase boundaries. Distributed DB
and object-store atomicity cannot be claimed; invisible private orphans are safer
than blind deletes after uncertain commits.

## Consequences

Clients/learning later consume reviewed release interfaces, not ORM internals.
Private storage adapter/live publication and orphan retention need operational
acceptance; no production pipeline is exercised now. Actor/approval records are
trusted operator assertions until identity/RBAC is implemented. Synthetic releases
remain staged. Future handoffs need compatibility/security regression gates.
