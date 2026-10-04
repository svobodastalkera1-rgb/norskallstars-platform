# Controlled public handoff receiving

The platform consumes an approved public contract; never clone or inspect the
private corpus. Everything committed/logged here is public. The short command
“Залил новый handoff, продолжай работу” resumes this procedure and only the
currently authorized phase/task. It grants no deployment/publication, destructive
migration, secrets/billing change, merge or other irreversible authorization.

1. Read project state/tasks and inspect Git status. Reconcile owner state against
   PR/main/checks/protections where observable; stop on material contradictions.
2. Owner places **exactly one ZIP and no other entry** into `.local/handoff/`.
   This is ignored inbound staging, never an approved source tree. Archive older
   candidates outside the checkout first. Never select a ZIP arbitrarily.
3. Run `python scripts/receive_handoff.py`. It verifies staging is nonsymlinked,
   ignored, untracked/index-excluded and absent from reachable main/HEAD history
   by path **and blob identity**. It prints filename/size/new SHA before review.
   Exit 1 at the review gate is intentional; it is not acceptance.
4. Archive checks run before extraction: finite limits (20 MiB input/total,
   10 MiB/file, 500 files, ratio 100), traversal/absolute/hidden/special paths,
   case collisions/duplicates, special entries/encryption/compression types.
   Handoff manifest format, exact allowlisted structure, complete inventory,
   per-file size/hash and SHA256SUMS (including manifest) must agree.
5. Review all text, code and media independently in a disposable controlled
   directory under ignored `.cache/`, after archive checks. Do not run inbound
   code during inspection. Review private content/answers, internal QA/adapters,
   prompts/source media, URLs/paths/accounts, secrets and metadata. Synthetic
   flags must be explicit and release_eligible false. Heuristics/scanners cannot
   prove arbitrary content synthetic: unresolved findings reject the whole ZIP;
   never clean it automatically. Keep findings/scan outputs private/redacted.
6. Build the trusted platform image (`docker compose --env-file .cache/phase1.env
   -f infra/development/compose.yaml build backend`). Only after independent
   code/content review run:
   `uv run --locked --project apps/backend python scripts/receive_handoff.py --reviewed-sha <actual-sha> --contract-gate`.
   This reruns gates, redacted Gitleaks, Draft 2020-12 schema/offline refs, supplied
   validator and generic tests in a disposable container: no network, credentials,
   writable source/root filesystem or host capabilities; bounded CPU/memory/PIDs/
   temporary disk and execution deadline. The image is pinned to its local image ID
   for the run. SHA argument acknowledges review, not sender authentication.
7. Any gate failure stops import/development dependent on the candidate. Fix an
   operator invocation/environment error explicitly; never suppress a real
   artifact finding. Preserve candidate unchanged and request replacement or
   owner decision. New contract major/format/allowlist needs an explicit reviewed
   receiver/compatibility change; current tooling deliberately rejects it.
8. Produce a per-file destination mapping **before copying/staging**. Accepted
   source/specification, schemas, synthetic fixture and generic tests/tools stay
   once under `contracts/course-package/upstream/`, preserving upstream relative
   layout/bytes. The platform remains a consumer. Root transfer README,
   RECEIVING_INSTRUCTIONS, HANDOFF_MANIFEST and SHA256SUMS are local metadata;
   raw ZIP is never persisted publicly. Upstream nested READMEs stay with code.
9. Compare all proposed hashes with the existing platform handoff inventory.
   Report contract/tool/fixture changes, review compatibility and run upstream
   plus platform regression/security/integration tests. Never infer semantics
   from provisional content, counts/IDs/activity distribution or real pilot.
10. Update platform handoff-manifest.json with approval, candidate SHA and every
    accepted destination/hash/role, in the same commit as artifacts. Never blindly
    copy a tree or force-add ZIP/staging. Run make check/security-check against
    the exact index and current main/proposed branch. Open a feature PR, verify
    actual hosted checks, stop before merge/new phase. All protections remain.

The receiver reports acceptance of receiving only; it performs no public copying,
commit, push, repository-setting change or product import. No inbound ZIP is used
by public CI. Regression tests construct synthetic receiving data.
