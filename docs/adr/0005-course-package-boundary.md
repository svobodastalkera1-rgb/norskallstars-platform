# 0005 — Controlled upstream handoff without contract invention

Status: Accepted (Product Owner accepted Phase 0 on 2026-10-03)
Date: 2026-10-03

## Context

An existing Course Package Contract v1 and public-safe handoff exist upstream, but have not been transferred here.

## Decision

Reserve contracts/course-package and fixtures/course-package. Record pending/received provenance in a local inventory; accept only owner-approved public artifacts. Use the actual upstream schemas and compatibility semantics. Do not create a replacement schema, fake fixture or importer in Phase 0.

## Alternatives

Inferring package fields from product requirements risks incompatible contracts. Reading the private repository directly is not authorized. Using a private pilot for public CI violates the boundary.

## Consequences

Phase 2 waits for handoff and review. The inventory is not the upstream contract. Future import validates untrusted data before transactional staging; privileged publication is a separate audited transition. Private pilot is later private acceptance.
