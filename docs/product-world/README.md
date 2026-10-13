# Product-world authority and synchronized public copies

[World & Experience Bible v1.0](world-experience-bible-v1.md) is the Product Owner's
approved **public-safe normative product direction**, covering platform, corpus,
narrative and future visual production. It is not the private Master Specification.
The Product Owner owns this authority; neither implementation repository may
independently redefine it. The canonical v1.0 publication/export source is the
document here. The separate corpus must retain a byte-identical approved copy
and the same [version/checksum record](EXPERIENCE_BIBLE_VERSION).

Status: Platform copy recorded locally. **Corpus adoption/synchronization is
pending and has not been verified.** No private repository was accessed. Owner authorized publishing this focused Bible branch and opening a PR; merge
remains subject to Owner review.

## Authority and compatibility

Latest explicit Owner decisions govern. This Bible supersedes conflicting earlier
visual/world direction; earlier evidence remains historical. Accepted security,
privacy, accessibility, pedagogy and Learning Core behavior remain mandatory.
Read it alongside [engineering direction](../architecture/product-direction.md),
[Learning Core](../architecture/learning-core.md) and the separately unmerged design studies.
Do not treat artistic examples as executable domain policy, real course data,
IDs, ordering rules, mastery thresholds or a Contract extension.

Contemporary Norway and human continuity are foundational. Folklore develops
through cultural memory, comprehension and ambiguity. Cold/warm material qualities
inform contemporary composition; fake wood/stone UI and medieval/game skins are
not the objective. Warm light is meaningful rather than universal chrome.
Prior three-concept studies require review against this authority; none is chosen,
automatically rejected or approved for rollout. No new assets/runtime are implemented
by this documentation adoption.

XP/levels/achievements remain in the authorized production roadmap, but are
secondary to narrative chapters and do not decide canonical learning availability.
Linear progression, explicit mastery policies, advisory placement, replay and
release pinning remain unchanged. Ambient sound and RetroCel are future candidate
capabilities, not dependencies, implemented features or newly authorized phases.

## Byte identity and controlled changes

The document uses UTF-8 without BOM, LF and a final newline. Git attributes preserve
LF. `EXPERIENCE_BIBLE_VERSION` contains only version, document filename and SHA-256
of the exact canonical bytes; it is tooling provenance, not an interchange schema.

```sh
python3 scripts/experience_bible.py --index
make hooks
make check
make security-check
```

Bootstrap checks verify the document's header/version, all 24 sections, byte hash
and exact Git index as well as the working copy. Missing, altered, inconsistent or
unstaged bytes fail closed. This checks consistency, not proof of Owner approval
or the state of an inaccessible repository.
The existing opt-in hook installer also adds this verification while preserving
confidentiality/secret checks; it refuses to overwrite an unrelated hook/configuration.

For corpus adoption, the Owner transfers **only these two public files** byte-for-byte
to the corresponding `docs/product-world/` location through an explicitly authorized
corpus session. That operator independently computes SHA-256, checks version and
confirms equality with this record before recording local adoption. No symlink,
cross-repository mount, submodule, private-repository URL lookup or platform access
to private corpus is introduced.

An explicitly authorized public export of the corpus copy may be checked here:

```sh
python3 scripts/experience_bible.py --index \
  --candidate-file /path/to/approved-public-export.md \
  --candidate-record /path/to/approved-EXPERIENCE_BIBLE_VERSION
```

This command reads only the supplied bounded public file pair and requires byte identity.
It never discovers repositories, copies files or updates checksums. It cannot
certify that an exported file is still installed in another repository. Do not
point it at private documents or a private checkout without separate permission.

For any future revision, Owner approval, a deliberate version change, new exact
hash, compatibility review and coordinated updates of both copies are required.
Record acknowledgment/verification for each repository; mixed-version adoption
remains pending. Preserve prior public evidence/history. Do not repair a mismatch
by automatically normalizing/rewording the candidate or updating its accepted hash.
Major document/format changes also require reviewed verifier changes.

The existing Course Package ZIP receiver has an exact format/allowlist. It does
**not** accept this Bible or a new Experience Contract automatically. Incorporating
these public artifacts into a future handoff requires an explicitly approved
versioned format, receiver/inventory/compatibility tests and independent public
review; never loosen the current gate to receive them.

See [Experience Contract direction](experience-contract-direction.md),
[corpus adoption/audit task](corpus-adoption.md) and
[ADR 0016](../adr/0016-product-world-authority.md).
