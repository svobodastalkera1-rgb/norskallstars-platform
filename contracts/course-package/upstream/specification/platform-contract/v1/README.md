# Contract v1

JSON Schema Draft 2020-12 files in this directory define package structure. The package validator additionally checks cross-file relationships that JSON Schema cannot express: global ID uniqueness, ordering, references, prerequisite cycles, file checksums, media signatures and safe archive paths.

## Package limits and safety rules

- Maximum input package / ZIP file: 64 MiB.
- Maximum total uncompressed content: 128 MiB.
- Maximum individual component or asset: 32 MiB.
- Maximum entries: 2,000.
- Maximum ZIP expansion ratio: 100:1.
- Only UTF-8 JSON and allowlisted PNG/JPEG/WebP/MP3/WAV/OGG media are accepted.
- Reject absolute paths, `..`, backslashes, control characters, hidden path segments, symlinks, duplicate ZIP names and unexpected top-level paths.
- The validator reads ZIP members in place and never extracts them. It never executes package content.
- Checksums are SHA-256 and cover all package files except `manifest.json`.

Limits are conservative defaults for this content package. A future contract version may revise them with compatibility notes.
