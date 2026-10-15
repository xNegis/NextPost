# Start Here

This directory contains the durable source of truth for NextPost.

## Working model

Trello contains product backlog tickets. A Trello card is consumed into repository-owned grooming
notes, analysed collaboratively, and converted into a self-contained implementation plan only after
the product owner confirms that all material questions are resolved.

The normal sequence is:

`Trello ticket -> grooming notes -> approved implementation plan -> external harness -> review`

The detailed gates and Trello board identity are defined in `06_TRELLO_WORKFLOW.md`.

## Read order

Before grooming a ticket, read:

1. `01_PRODUCT_VISION.md`
2. `02_ARCHITECTURE.md`
3. `03_DECISIONS.md`
4. `04_PROJECT_STATE.md`
5. `05_IMPLEMENTATION_PLAN_TEMPLATE.md`
6. `06_TRELLO_WORKFLOW.md`
7. Relevant grooming notes and approved plans.

Before implementation, also read the complete assigned plan and every plan it names as a dependency.

## Document responsibilities

- `harness/grooming/RF-XX-grooming.md`: mutable analysis, code-impact findings, alternatives, and
  unresolved questions for one consumed ticket. It is not implementation authority.
- `harness/features/RF-XX-Implementation-plan.md`: approved, self-contained implementation contract.
- `03_DECISIONS.md`: durable cross-feature decisions and their reasoning.
- `04_PROJECT_STATE.md`: current ticket, lifecycle state, and validated implementation status.

Repository documentation, not previous conversations, is the source of truth.

The owner's 2026-10-12 interview and backlog reconciliation are preserved in
`../grooming/PRODUCT-2026-10-12-reorganization.md`. Read it when selecting the next ticket or
reasoning about product direction; it distinguishes current MVP scope from later community ideas
and does not replace approved feature contracts.
