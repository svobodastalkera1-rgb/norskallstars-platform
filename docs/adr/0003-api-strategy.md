# 0003 — Versioned API with explicit compatibility review

Status: Accepted (Product Owner accepted Phase 0 on 2026-10-03)
Date: 2026-10-03

## Context

Two clients and later offline behavior need stable backend interfaces distinct from the corpus interchange contract.

## Decision

Use an HTTP JSON API with a major-version namespace (initial direction /api/v1) and reviewed OpenAPI artifacts generated from validated DTOs once endpoints exist. Backward-compatible changes stay in the same major; breaking changes require migration/deprecation design. Model resource ownership, limits and controlled errors at the boundary.

## Alternatives

Unversioned implicit interfaces invite accidental breaks. GraphQL would add a second abstraction without a demonstrated product need. Backend ORM models are not a safe public interface.

## Consequences

Client contract checks and generation come with actual endpoints. Session transport, endpoint inventory and sync protocol remain later designs. Contract v1 package versions and platform API versions are independent. This ADR implements no endpoints.
