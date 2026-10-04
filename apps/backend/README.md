# Backend infrastructure

Phase 1 implements an infrastructure-only FastAPI modular-monolith foundation.
Python 3.13.16, async SQLAlchemy/psycopg, PostgreSQL 17.11 and Alembic are pinned
through pyproject.toml, uv.lock and image digests. No product domain tables or
business endpoints exist. Only /health/live and /health/ready are delivered.

src/norskallstars_backend contains the factory, typed settings, pool/transaction
boundary, safe JSON logging, request middleware and object-storage interface.
migrations tracks an empty baseline; tests exercises runtime and isolated real
PostgreSQL behavior. There is no Redis, worker, importer or application client.

See [runtime setup](../../docs/development.md),
[runtime architecture](../../docs/architecture/backend-runtime.md), and
[Phase 1 review](../../docs/phase-1-review.md).

Phase 1 is owner-accepted. Phase 2 course release validation/import/operator
transitions are described in docs/architecture/course-integration.md from root.
