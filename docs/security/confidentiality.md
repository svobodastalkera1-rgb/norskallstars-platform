# Confidentiality boundary

All committed content, job logs, PR descriptions and artifacts must be safe for
public disclosure. The private corpus remains the source of teaching content;
this platform consumes versioned packages, never its internal directory layout.
Product Owner specifications remain outside the public checkout. Translate
necessary requirements into engineering decisions, not verbatim private text.

Never publish real lessons/exercises/curriculum, private course packages, prompts,
production images/audio, character references, private QA, credentials/tokens/
keys, production configuration, dumps, user data, backups or sensitive logs.
Prefer external storage over ignored folders: ignore rules can be overridden
with git add -f and do not remove tracked content or earlier history.

The guard inspects actual index bytes, not just working-tree files. It rejects
prohibited artifact paths and package/media archives unless individually approved
through the public handoff manifest. Approved synthetic artifacts must match a
recorded SHA-256. Gitleaks separately scans secrets with redacted diagnostics.
Humans must check whether arbitrary filenames/content contain private material.
No path heuristic can recognize every real lesson or arbitrary secret.

Use make hooks after bootstrap. The local hook scans index contents before each
commit; CI rechecks without relying on local hooks. If a private/secret artifact
is found, stop, keep values out of output, and request owner incident handling.
Do not rewrite history or rotate real production secrets without authorization.
Do not restore previously removed history. Server-side object retention is a
separate matter from the reachable-history checks in this repository.

Only owner-approved public schemas, PUBLIC_HANDOFF documentation, compatibility
rules and synthetic fixture may cross the corpus boundary. Follow the controlled
procedure in ../corpus-integration/README.md. Private pilot acceptance is later,
outside public CI, with only sanitized evidence retained publicly.
