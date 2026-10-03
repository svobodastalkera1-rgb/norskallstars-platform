# Course Package controlled handoff

Status: **waiting for owner-approved public artifacts**.

Do not invent schemas, enum values, identifiers, archive layout or checksums.
The existing upstream Contract v1 is authoritative for package structure.
No access to the private corpus repository is granted by this directory.

handoff-manifest.json starts with an empty artifacts list. After controlled
transfer, each public artifact must have a repository-relative path, SHA-256,
role and public-safe approval provenance. See the documented procedure in
../../docs/corpus-integration/README.md. Until approval, this directory contains
only documentation and the pending manifest; there is no runnable fixture.
