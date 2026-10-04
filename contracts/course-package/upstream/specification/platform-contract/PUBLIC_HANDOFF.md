# Public handoff boundary

This is a transfer manifest for a separate public platform repository. It is not permission to publish the authoritative private corpus source or any material outside this allowlist.

## Safe to copy after an ordinary public content review

- `specification/platform-contract/v1/{README.md,manifest.schema.json,course.schema.json,chapter.schema.json,lesson.schema.json,activity.schema.json,asset.schema.json,content-block.schema.json}`.
- `specification/platform-contract/CHANGELOG.md` and this handoff file.
- `tools/course_package.py`, `tools/validate_course_package.py`, and `tools/build_course_package.py`.
- Only `qa/automated/test_course_package.py` from the test directory; it tests the generic package contract and synthetic fixtures.
- `fixtures/README.md` and the synthetic-only `fixtures/course-package-v1/` tree.

To stage the handoff into a platform checkout, run `python tools/prepare_public_handoff.py /path/to/platform-checkout` from the course repository. The helper uses this fixed allowlist, rejects destinations inside the course repository, preflights every target path, refuses to overwrite an existing path, and rejects symlinked destination directories. Unrelated files (including `.git/`) are left untouched. The helper itself, the course repository, and any other tracked files are not part of the staged handoff. Review the staged tree before committing it to the separate platform repository.

Source-specific production and research tooling is outside this allowlist. Do not use `git clone`, copy the repository root, or copy broad `corpus/`, `specification/`, `qa/`, `tools/`, or `build/` directories into the platform repository.

## MUST NOT COPY

- Real lessons, full/partial curriculum, Bokmål texts, prompts, answers, assessment datasets, vocabulary/grammar registries, character/location information or world bible.
- Internal course-specific requirements, specifications or mapping documents.
- Illustration briefs, generation prompts, references, generated source images, unpublished audio or production metadata.
- Non-public course packages, internal QA/review artifacts, source datasets, Product Owner research or learner data.
- Secrets, credentials, access information or private repository URLs.

## Importer expectations

- Treat every package as untrusted input; validate schema, references, ordering, checksums, MIME/signatures, paths and limits before importing.
- Accept only supported schema majors/minors and respect `minimum_importer_version`.
- Never execute package content or extract ZIP entries without first validating their paths/size; the reference validator does not extract archives.
- Do not infer user progress, mastery, authentication or business rules from a course package. Those belong to the separate platform.
- Keep course payload private and access-controlled after transfer; public availability of the format does not make package instances public.

No release or deployment automation is included in this allowlist.
