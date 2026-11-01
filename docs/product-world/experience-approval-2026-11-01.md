# Experience Contract v1 — Product Owner approval

Version: 1.0. Status: APPROVED / NORMATIVE EXPERIENCE CONTRACT v1.
Decision date: 2026-11-01. Authority: explicit Product Owner approval in this task.
Canonical document: [Experience Contract v1](experience-contract-v1.md).
This approval closes semantic review, not implementation or release acceptance.

## Dated provenance, without retroactive approval

| Date / step | Recorded status and evidence |
| --- | --- |
| 2026-10-15 — initial reconciliation/candidate | REVIEW_CANDIDATE_NOT_APPROVED; eleven public-safe Corpus requirements mapped, speculative reading/speaker annotations still conditional |
| 2026-10-17 — Platform → Corpus review export | Historical local source commit `2d499b35e5b1b965e6bfee13d948117d89d0b624`; candidate transfer was not contract approval |
| 2026-10-31 — Corpus review and Owner acceptance of recommendation | ACCEPT_WITH_MINOR_CORRECTIONS; nine requirements FULLY_PRESERVED, 009 AMBIGUOUS, 011 not required for first slice; see [dated record](corpus-semantic-review-2026-10-31.md) |
| 2026-10-31 — Platform corrections | READY_FOR_PRODUCT_OWNER_APPROVAL at local source commit `c812c6200a9d4aba83cbda50344e5a4c812d75dc`; no added reading state/gate, attribution/text/audio sufficient, speculative annotations/sidecar removed |
| 2026-11-01 — final Product Owner decision | APPROVED / NORMATIVE EXPERIENCE CONTRACT v1; semantic review cycle closed, contract-level slice READY |

Earlier local branches/commits and original review archive are preserved. This
publication branch starts at public main `5669565dea726313ec2cf07d3d4f14ce3a825137`
and carries only approved final documentation and necessary provenance/mapping.
It does not publish earlier receiver/exporter code, raw archives, transfer metadata,
private audit evidence or unrelated UI/Android work. No shared history is rewritten.
Local source commit identifiers establish the recorded lineage, not a claim those
commits are already on public main. No private Corpus repository was accessed.

## Approved semantic decisions

- Keep CONTENT AVAILABILITY, canonical LEARNER PROGRESSION and CLIENT PRESENTATION /
  LOCAL READING UX separate. Existing Learning Core remains authoritative.
- No additional reading acknowledgement, completion state or mandatory unlock gate
  absent explicit authoritative course data; local scroll/last-opened state grants
  no canonical learning credit. No second reading progression model.
- EXP-REQ-011: NOT_REQUIRED_FOR_VERTICAL_SLICE, deferred outside normative v1.
- Existing attribution and text/audio association suffice; no speaker annotation,
  voice/character-voice registry, provider metadata or annotation sidecar.
- Course Package Contract v1 remains unchanged; no mandatory v1 change blocks slice.
- Approved first-slice sequence: 014 → 015 → 016 → REVIEW-02 → READING-02.
  Contract-level readiness READY; implementation has NOT started. Planning labels
  do not replace exact validated content/release identity or authorize private import.
- World & Experience Bible v1.0 remains normative. RetroCel is not a dependency.

No implementation, UI redesign, slice, Corpus editing/adoption, renderer integration,
production deployment, Android merge or new roadmap phase is authorized here.
Corpus Bible synchronization and deployment/provider/privacy/storage/license gates
remain separate; no claim of production readiness is made.

Android PR #17 was rechecked on 2026-11-01: OPEN/unmerged at
`1317521dff118001d87beb700131d67945c813a9`. It remains separate from this publication.
The Owner authorized a normal feature PR and hosted checks; merge still requires
Product Owner review. STOP before implementation, slice and merge.
