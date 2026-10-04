# Infrastructure boundary

Phase 1 provides local/test Docker definitions; no production resources exist.
Future definitions live under development/ and deployment/. Select Docker for
backend packaging and independent durable object storage. Do not create services
without a runtime to exercise or add production identifiers/secrets here.
No production provider, region, domain, bucket, network rule or deployment
credential is chosen by this bootstrap. See docs/deployment/README.md.
