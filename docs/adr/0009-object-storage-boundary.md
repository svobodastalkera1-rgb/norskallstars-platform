# 0009 — Vendor-neutral object boundary with development-only local storage

Status: Accepted (Phase 1 engineering decision; Product Owner accepted Phase 1 on 2026-10-04)
Date: 2026-10-03

## Context

Future protected assets need storage independent of domain logic or container disk.
No asset pipeline or production media is authorized in Phase 1.

## Decision

Define an async put/get/delete protocol. Supply a local Linux/POSIX adapter only
for local/test development, with constrained keys, bounded data, atomic writes
and symlink-safe directory-descriptor access. Disable storage when unused and
reject local storage in staging/production. A later S3-compatible adapter will
implement the same boundary rather than introduce vendor calls into domains.

## Alternatives

Building a production provider client now would add credentials/resources before
an asset consumer exists. Accepting arbitrary filesystem paths would blur the
input/storage boundary. Container ephemeral disk is not production object storage.

## Consequences

No media endpoint, package pipeline or production provider integration is delivered.
Readiness checks only required Phase 1 dependencies. The local adapter assumes
its configured root/ancestors are trusted and runs on POSIX; it is not a multi-user
filesystem security perimeter, signed-delivery system or transactional database.
Future concurrency/publication semantics follow the approved integration design.
