# Experience Contract — direction, not an implemented contract

Status: **definition and bilateral approval pending**. Authority: Bible v1.0 §21.
No Experience Contract schema, payload/version, parser or importer exists yet.
This document records requirements to resolve through public-safe collaboration;
it must not be interpreted as a replacement or extension of Course Package v1.

## Responsibilities and intended capabilities

The corpus owns pedagogical content, authored narrative, character/location/prop
continuity and production assets in private storage. The platform owns presentation
capabilities, accessibility/native behavior and server-authoritative progress,
identity, authorization and media handling. Clients consume stable platform
API/domain representations rather than interpreting raw Course Packages.

The shared contract should eventually make explicit which experiential primitives
the platform supports and which the approved corpus requires, including narrative
reading, sequential illustration/dialogue, chapter/arc continuity, entity references,
speech/translation affordances and any separately approved ambient media behavior.
Required versus optional capability handling, version compatibility and safe
degradation need explicit agreement. Pedagogically necessary media must not
silently disappear under an optional presentation fallback.

Entity examples in the Bible are conceptual, not required identifier syntax or
Course Package fields. Renderer changes must preserve recognized entities without
binding domain logic to a generation prompt, art vendor or current pilot.

## Definition gate

1. Inventory existing accepted platform APIs/domain/media capabilities and actual
   Contract v1 semantics using public artifacts. Obtain only sanitized corpus
   requirements through Owner-approved handoff; never infer them from private data
   or the current provisional pilot.
2. Map each required experience to a currently supported semantic capability;
   distinguish platform presentation policy from content interchange needs.
3. Report exact gaps, incompatible versions and minimal proposals to Owner. If
   Course Package semantics must change, stop for a controlled upstream contract
   revision; do not invent extension keys or reinterpret accepted fields.
4. Agree a versioned public-safe specification, conformance examples/tests and
   handoff provenance before implementation in an explicitly authorized task/phase.

Package provenance, immutable snapshots, publication eligibility, bounded untrusted
ingestion, transaction behavior, account ownership and media privacy remain intact.
This document grants no runtime, private corpus, renderer/ML, publication or phase
authorization. Existing Course Package Contract v1 and its inventory remain unchanged.
