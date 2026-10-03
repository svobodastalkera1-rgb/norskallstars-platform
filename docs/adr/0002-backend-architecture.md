# 0002 — Modular monolith and baseline stack

Status: Accepted (Phase 0 engineering baseline; owner review pending)
Date: 2026-10-03

## Context

An authoritative domain serves Web and Android. Bootstrap has no load evidence requiring distributed services.

## Decision

Use one Python/FastAPI backend with explicit domain ownership, PostgreSQL, SQLAlchemy, Alembic and Pydantic. Keep object storage behind an interface. React/TypeScript and Kotlin/Compose remain the client baselines. Add Redis or workers only for justified workload needs.

## Alternatives

Microservices add deployment/consistency costs without current evidence. Switching primary languages/frameworks is outside autonomous engineering scope and needs owner approval.

## Consequences

Domain interfaces must avoid direct cross-module persistence writes. Pin compatible libraries when Phase 1 starts. No backend runtime, ORM models, cache, worker, container or migration is implemented by this ADR.
