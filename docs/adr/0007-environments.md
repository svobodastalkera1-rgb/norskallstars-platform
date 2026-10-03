# 0007 — Isolated environments and minimal bootstrap tooling

Status: Accepted (Phase 0 engineering baseline; owner review pending)
Date: 2026-10-03

## Context

Production delivery needs reproducible local/test behavior and independent staging/production without copying real content into development.

## Decision

Define local, test, staging and production as distinct data/configuration/security boundaries. Bootstrap needs only pinned Python tooling and Git. Introduce Docker local/test PostgreSQL with Phase 1 runtime checks; use synthetic content only. Later promote immutable artifacts through staging verification and production approval.

## Alternatives

Shared databases/buckets or production content in development blur privacy and failure boundaries. Kubernetes/Redis/multi-service bootstrap infrastructure lacks a justified requirement.

## Consequences

No services, clusters, storage, CD credentials or deployments are created in Phase 0. Local/test must be disposable and isolated; staging/production secrets, data and recovery policies are separate. Future provider/region choices require evidence and relevant owner decisions.
