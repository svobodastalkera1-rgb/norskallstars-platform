# Working on NorskAllstars Platform

Treat everything committed here as public. Product name: NorskAllstars.
Repository name: norskallstars-platform. Never rename the separate private corpus.

Before substantial work, read PROJECT_STATE.md, ROADMAP.md, TASKS.md,
docs/architecture/README.md, relevant ADRs, and docs/security/confidentiality.md.
The public engineering baseline in docs/architecture/product-direction.md
supports continuation without a private specification or previous chat.
If a required product decision is missing, request Product Owner input.
Do not invent contractual data structures or silently narrow release scope.

## Phase control

Phase 0 is ACCEPTED by Product Owner. Phase 1 is NOT STARTED and requires
separate explicit authorization; acceptance of Phase 0 does not authorize it.
Do not implement application runtime,
identity, importers, learning, billing, administration, sync, or deployments
as part of bootstrap. Keep actual implementation status in PROJECT_STATE.md.
Subsequent phases follow design, implementation, validation, security review,
and documentation. Update TASKS.md and state when completing meaningful work.

## Confidential inputs

Never commit a Master Specification, real corpus, private packages, prompts,
production media, private QA, user data, secrets, dumps, backups, or sensitive
logs. Read private inputs only with authorization. Keep them outside this
checkout. Do not reconstruct removed confidential documents from Git history.
Do not access the private corpus repository without separate owner permission.
Course integration accepts only an explicitly approved public handoff; the
pending manifest under contracts/course-package records that dependency.
Do not place private material in issues, PRs, job logs, or CI artifacts.

## Engineering workflow

Work on a focused branch. Inspect git status before edits and preserve unrelated
work. Use ADRs for significant technical changes. Changes to the principal
stack, product requirements, content visibility, or weaker security need owner
approval. Normal engineering choices are yours to make and document.
Run relevant real checks; never add placeholder passing tests, suppress security
findings to obtain green CI, or treat a skipped/pending check as acceptance.
Before commits run make check and make security-check, inspect the staged diff,
and ensure the confidentiality guard examines index contents.
Full-history checks target current main and the proposed branch, not reflogs or
removed history. Ignore patterns and scanners supplement human review.

Do not push, deploy, publish, change repository settings/visibility, rewrite
history, delete remote refs, or perform external irreversible actions unless
explicitly authorized for that action. Phase 0 needs no such operations.
Do not print secret values or attach private scan output publicly.
