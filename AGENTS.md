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

Phase 0 is CLOSED and ACCEPTED. Phase 1 is CLOSED and ACCEPTED (PR #4 merged).
Phase 2 is CLOSED and ACCEPTED (PR #7 merged and verified).
Phase 3 Identity is CLOSED and ACCEPTED (PR #8 merged and verified).
Phase 4 Learning Core is CLOSED and ACCEPTED (PR #9 merged and verified).
Public-safe normative Product Owner rules are recorded in
docs/architecture/learning-core.md. Require explicit versioned learning policies;
never invent numeric pedagogical defaults or infer rules from fixtures/arbitrary
Contract extension objects. Phase 5 Web is CLOSED/ACCEPTED (PR #10 merged).
Phase 6 Android is authorized in separate PR #17 and not merged here. Read docs/web/README.md: Owner accepted selective voice
retention with separate consent, an explicit processing purpose, at most twelve
months and erasure with account deletion; the same policy applies to Android.
ML implementation/training is not authorized. Phase 7 and later need separate authorization.
Work through a feature PR; never merge without Product Owner review.
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

## Repeatable receiving

“Залил новый handoff, продолжай работу” means inspect exactly one candidate ZIP
in ignored .local/handoff and follow docs/corpus-integration/receiving.md.
Run scripts/receive_handoff.py; independently review every text/code/media
artifact before acknowledging its exact SHA and running the contract gate.
Fail closed on any discrepancy; never sanitize a rejected handoff into acceptance.
Review destination mapping and compatibility/regression tests before changing
inventoried public files. Continue only the already-authorized task/phase.
The short command never authorizes deployments, publication, destructive
migrations, secrets/billing changes or irreversible external operations.

## Product-world authority

Read docs/product-world/world-experience-bible-v1.md and docs/product-world/README.md
before product/narrative/visual work. Bible v1.0 is Owner-approved public-safe
normative direction, superseding conflicting old art guidance, not security/privacy,
accessibility, pedagogy or accepted domain behavior. Verify version/SHA and exact
index using scripts/experience_bible.py --index. Corpus synchronization is pending;
never access private corpus to infer it. Legacy visuals/studies are evidence, not
style precedent; independently review KEEP/REINTERPRET/REPLACE against Bible and
Owner-approved benchmarks. Preserve behavior/accessibility, not legacy appearance.
Experience Contract definition is pending; do not invent fields or extend Course
Package v1. RetroCel is a future candidate, not a dependency. Bible adoption does
not authorize corpus rewriting, rollout, merge or another phase.
Owner accepted Phase 5 (PR #10 merged). Phase 6 is authorized in separate PR #17,
not merged/accepted here; Phase 7 is not authorized. These decisions do not authorize new runtime work in the Bible publication task.
