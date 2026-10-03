# Local/test runtime

compose.yaml provides PostgreSQL 17.11, a non-root/read-only backend image,
explicit migration job, loopback ports and separate synthetic test database.
Use python3 scripts/phase1.py init/up/test/smoke/down from the root; see
[development](../../docs/development.md). Passwords are generated into ignored
local files and are injected only at runtime. This is not production deployment.
