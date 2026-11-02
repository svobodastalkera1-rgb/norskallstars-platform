# NorskAllstars documentation

Start with the [product and architecture overview](../README.md). Choose a route:

| Reader / purpose | References |
| --- | --- |
| Understand the system | [Architecture](architecture/README.md), [decisions](adr/README.md), [API contracts](api/README.md) |
| Explore learning semantics | [Learning Core](architecture/learning-core.md), [versioned learning policies](../contracts/learning/README.md) |
| Understand content isolation | [Course Package integration](corpus-integration/README.md), [confidentiality boundary](security/confidentiality.md) |
| Explore product/world authority | [World & Experience](product-world/README.md), [public product direction](architecture/product-direction.md) |
| Run or contribute | [Development](development.md), [Web](web/README.md), [Android toolchain](../apps/android/README.md), [agent instructions](../AGENTS.md) |
| Review security engineering | [Reporting policy](../SECURITY.md), [controls](security/README.md), [CI gates](ci.md) |
| Review source-use terms | [Proprietary license notice](../LICENSE); third-party rights remain separate |
| Plan future work | [Roadmap](../ROADMAP.md), [current state](../PROJECT_STATE.md), [tasks](../TASKS.md) |
| Inspect delivery evidence | [Review index](reviews/README.md), [changelog](../CHANGELOG.md), [release strategy](releases.md) |

Architecture/contracts describe semantics and boundaries. Current state/tasks
record execution; dated reviews record what was verified at that time. A prior
green check or acceptance does not certify a future revision or live provider.
No private Corpus, package, credentials or production-user data is needed to read
these documents or run the public-safe development environment.
