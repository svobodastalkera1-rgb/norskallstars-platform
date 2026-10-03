# 0004 — Separate public engineering from private content

Status: Accepted (Product Owner accepted Phase 0 on 2026-10-03)
Date: 2026-10-03

## Context

The platform repository is public. The owner specification and corpus are private inputs, and secrecy of implementation is not a security control.

## Decision

Commit only public-safe code, engineering documentation and explicitly approved synthetic contract artifacts. Keep real packages/media, private specification, prompts, QA and all sensitive runtime data outside this checkout. Do not give the platform filesystem-level access to the corpus repository.

## Alternatives

Ignoring a private corpus checkout inside this tree would still expose it to staging mistakes and tools. Publishing a private product document would exceed the authorized boundary.

## Consequences

Use ignore rules, index/history guards, secret scanning and human review together. They cannot prove arbitrary content is non-private. Private acceptance happens outside public CI. Confidentiality incidents require separate owner handling; bootstrap never rewrites history.
