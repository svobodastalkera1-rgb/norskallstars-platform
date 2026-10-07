# NorskAllstars backend

Python/FastAPI modular monolith; Python 3.13.16, SQLAlchemy/psycopg, PostgreSQL 17.11
and Alembic, locked with uv and pinned image digests. Phases 1–3 are CLOSED/ACCEPTED;
Identity PR #8 is merged. Phase 4 Learning Core is authorized under the normative
product rules in [Learning Core](../../docs/architecture/learning-core.md).
Learning feature implementation/validation is in progress; no Web/Android or
deployment is implemented.

src/norskallstars_backend contains infrastructure, course_packages, identity and learning.
Health endpoints remain minimal; `/api/v1/identity` is the shared account API.
Course import/publication remains operator-side, with no HTTP/admin privilege grant.
Migration 0004_learning follows 0003_identity and adds pinned learning/account data.
Redis is absent. Encrypted transactional mail outbox has private bounded maintenance,
without public job endpoints. Deterministic tests use synthetic identities and data.

See [development](../../docs/development.md),
[identity](../../docs/architecture/identity.md),
[course integration](../../docs/architecture/course-integration.md),
[security review](../../docs/security/phase-3-review.md) and
[Phase 3 evidence](../../docs/phase-3-review.md).
