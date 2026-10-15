# Trello Workflow

## Configured backlog

- Workspace: `Trello Workspace`
- Board: `APP - NextPost`
- Board URL: https://trello.com/b/CgBkRg78/app-nextpost
- Workspace ARI: `ari:cloud:trello::workspace/6aa9032829f8b45ead46cfdd`
- Board ARI: `ari:cloud:trello::board/workspace/6aa9032829f8b45ead46cfdd/6aa903892e7d7b54f23fae1b`

On 2026-10-12 the owner requested a backlog reconciliation, which was applied and verified.
The board columns are
`Validado · incrementos aprobados`, `En revisión · implementación existente`,
`Próximo · completar el MVP`, `Beta · entrega y aprendizaje`,
`Después · comunidad y participación`, `Después · cuentas y administración`, and
`Fuera del MVP inicial`. The application/verification record is in
`harness/grooming/PRODUCT-2026-10-12-reorganization.md`.

Columns organize the work; repository state remains authoritative for implementation evidence.
`Validado` refers to the approved increment, not every downstream consumer of a broad source card.
`Próximo` is a grooming queue, not approval or `Ready for implementation`. Pending validation must
remain explicit even when a historical Trello completion flag is set. Capture the actual current
list name at future intake; preserve old snapshots and card identifiers/URLs.

## Consuming a ticket

When the product owner asks to work on a ticket:

1. Resolve the exact card on the configured board. If the identifier is ambiguous, present the
   matching titles and URLs instead of guessing.
2. Read the complete current card, including description, labels, checklists, comments when relevant,
   list, due state, and URL.
3. Create or update `harness/grooming/RF-XX-grooming.md` using the template in that directory.
4. Store a readable snapshot rather than only Trello internal IDs. Always preserve the card URL.
5. Record the intake timestamp and any mismatch between the RF identifier, title, list, labels, and
   card content.
6. Update `04_PROJECT_STATE.md` to `Grooming - questions open`.

Consuming is read-only by default. Do not move, archive, complete, relabel, edit, or comment on the
Trello card unless the product owner explicitly asks for that Trello mutation.

## Grooming contract

Grooming answers four central questions:

1. What exactly are we trying to achieve?
2. Which existing code, data, integrations, and product contracts are affected?
3. What viable approaches exist, and which one should we choose?
4. How will we prove the result is correct, safe, and complete?

Codex must inspect the real repository before asserting code impact. For an empty repository, the
absence of code is itself a finding and architecture decisions must be surfaced rather than assumed.

Ask questions in coherent decision groups. For each material question, provide context, realistic
options, trade-offs, and a recommendation. Record confirmed answers in the grooming notes. Never
reinterpret silence as approval.

## Finalising the plan

When no material question remains, show the settled scope and approach to the product owner. Only
after explicit approval to finalise:

1. Create `harness/features/RF-XX-Implementation-plan.md` from
   `05_IMPLEMENTATION_PLAN_TEMPLATE.md`.
2. Make it self-contained; the harness must not need Trello or conversation history.
3. Set `Remaining questions` to `None`.
4. Set `Status` to `Ready for implementation`.
5. Update `04_PROJECT_STATE.md` accordingly.

Creating the plan does not implicitly authorize implementation.

## Harness handoff and review

Only after the product owner explicitly asks to implement or launch the harness, follow
`.codex/runbooks/opencode_implementation.md`.

After the harness exits, inspect the actual worktree and compare it with every requirement and
acceptance criterion. Re-run appropriate checks independently. Do not mark the ticket completed or
mutate Trello until the evidence supports the claim and the product owner requested the Trello
change.
