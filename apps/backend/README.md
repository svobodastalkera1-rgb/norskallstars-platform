# NorskAllstars backend

Python/FastAPI modular monolith; Python 3.13.16, SQLAlchemy/psycopg, PostgreSQL 17.11
and Alembic, locked with uv and pinned image digests. Phases 1/2 are owner-accepted;
Phase 3 Identity is prepared for review. No learning, Web/Android or deployment.

src/norskallstars_backend contains infrastructure, course_packages and identity.
Health endpoints remain minimal; `/api/v1/identity` is the shared account API.
Course import/publication remains operator-side, with no HTTP/admin privilege grant.
Migration 0003_identity follows the accepted course-release schema; no course changes.
Redis is absent. Encrypted transactional mail outbox has private bounded maintenance,
without public job endpoints. Deterministic tests use synthetic identities and data.

See [development](../../docs/development.md),
[identity](../../docs/architecture/identity.md),
[course integration](../../docs/architecture/course-integration.md),
[security review](../../docs/security/phase-3-review.md) and
[Phase 3 evidence](../../docs/phase-3-review.md).
