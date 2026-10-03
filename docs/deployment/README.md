# Deployment direction

Local, test, staging and production must be isolated. Backend components will use
Docker; database and object storage persist outside ephemeral containers. Build
reviewed immutable artifacts, verify them in staging, then require a production
approval. Production CD is not configured or authorized in Phase 0.
Never bake credentials or private packages into images. Prefer scoped runtime
identity/secrets mechanisms; keep real topology and access details out of public
docs. Provider, region, recovery goals and rollout/rollback designs are later
decisions. Deployment readiness needs exercised recovery and observable health.
