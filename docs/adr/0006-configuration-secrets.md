# 0006 — External validated configuration and secrets

Status: Accepted (Product Owner accepted Phase 0 on 2026-10-03)
Date: 2026-10-03

## Context

Public source and reusable deployments must contain no production credentials or environment-specific sensitive values.

## Decision

Use environment-provided settings with explicit validation and safe defaults for non-sensitive values. Keep .env.example public-safe and minimal. Local .env is ignored; staging/production inject secrets through approved runtime mechanisms with least privilege. Never put credentials in images, logs or build arguments.

## Alternatives

Hardcoded credentials or committed environment files expose sensitive values. A bootstrap-time dedicated secrets service creates needless complexity before a deployment environment is selected.

## Consequences

Phase 1 defines the actual settings schema and invalid-configuration behavior. Runtime providers, rotation, identity and access are later environment decisions. Phase 0 labels in .env.example are inert; no service consumes them yet.
