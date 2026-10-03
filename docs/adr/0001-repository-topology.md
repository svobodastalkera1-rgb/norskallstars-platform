# 0001 — Public platform monorepo

Status: Accepted (Product Owner accepted Phase 0 on 2026-10-03)
Date: 2026-10-03

## Context

Backend, two clients, shared contracts and delivery documentation evolve together. Teaching content has independent private ownership.

## Decision

Keep apps/backend, apps/web, apps/android, contracts, infra and docs in one public platform repository. Keep the private corpus separate and consume only approved package artifacts.

## Alternatives

Separate application repositories add interface coordination and duplicated policy work before independent delivery needs are established. Including the corpus in this monorepo would violate confidentiality.

## Consequences

Atomic interface changes and common review improve consistency. Use path-aware app CI when applications exist; release artifacts can still be independent. The monorepo does not imply a shared runtime or importing private Git submodules.
