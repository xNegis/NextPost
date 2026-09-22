# NextPost Working Agreement

This repository is developed through a ticket-grooming and harness-engineering workflow.

The product owner and Codex collaborate on product and technical direction. Implementation is
normally delegated to an external coding harness only after a Trello ticket has been analysed and
turned into an approved, implementation-ready plan.

## Source of truth

Do not rely on previous conversations as project context.

Before analysing, planning, or implementing work, read:

1. `harness/context/00_START_HERE.md`
2. `harness/context/01_PRODUCT_VISION.md`
3. `harness/context/02_ARCHITECTURE.md`
4. `harness/context/03_DECISIONS.md`
5. `harness/context/04_PROJECT_STATE.md`
6. `harness/context/05_IMPLEMENTATION_PLAN_TEMPLATE.md`
7. `harness/context/06_TRELLO_WORKFLOW.md`

Read the active grooming notes under `harness/grooming` and all relevant approved plans under
`harness/features`.

Trello is the product-backlog input. The repository is the source of truth for accepted decisions,
current technical context, implementation plans, and implementation state. A coding harness must
never need conversation history or direct Trello access to implement an approved plan.

## Required workflow

Every new feature follows these gates in order:

1. Consume one explicitly selected Trello ticket from the configured NextPost board.
2. Record a snapshot of its title, URL, description, acceptance criteria, list, labels, and relevant
   metadata in `harness/grooming/RF-XX-grooming.md`.
3. Inspect the current repository and relevant existing plans before proposing a solution.
4. Collaboratively resolve:
   - what the feature must achieve;
   - what is in and out of scope;
   - which parts of the code and data model it affects;
   - dependencies and conflicts with other tickets;
   - viable implementation options and trade-offs;
   - UX, validation, error, security, privacy, migration, testing, and operational questions.
5. Keep unresolved questions and proposed answers in the grooming file. Proposals are not accepted
   decisions until the product owner confirms them.
6. Only when every material question is resolved and the product owner explicitly approves
   finalisation, create `harness/features/RF-XX-Implementation-plan.md` from the repository template.
7. Only after that plan is marked `Ready for implementation` may the external coding harness be
   launched using `.codex/runbooks/opencode_implementation.md`.
8. Review the harness output against every acceptance criterion and validation requirement before
   reporting the ticket complete.

Do not skip directly from a Trello card to implementation. Do not write or finalise an implementation
plan while material product or technical questions remain. Do not launch the harness implicitly;
wait for the product owner's explicit request.

## Planning rules

- The Trello card is a starting point, not automatically a complete specification.
- Plans must be self-contained and written in English for the implementation harness.
- Preserve the ticket identifier and include its Trello URL for traceability.
- Describe observable behaviour and constraints before internal implementation detail.
- Inspect real code before naming affected files or components. If the repository does not yet
  contain the relevant code, say so and describe the intended boundaries without inventing paths.
- Prefer a small coherent vertical increment. Identify unrelated or future behaviour as out of scope.
- Record durable cross-feature decisions in `harness/context/03_DECISIONS.md`.
- Update `harness/context/04_PROJECT_STATE.md` at meaningful state transitions.

## Implementation rules

When implementing an approved plan:

1. Read this file and all source-of-truth context completely.
2. Read the assigned implementation plan and its dependencies completely.
3. Inspect the existing implementation and worktree before editing.
4. Implement only the approved scope.
5. Preserve unrelated user changes.
6. Add meaningful tests and run validation proportional to risk.
7. Do not commit, push, deploy, or change Trello unless the product owner explicitly requests it.
8. Update project state only when the completion claim is supported by evidence.

If an approved plan conflicts with the code or an accepted decision, stop and report the conflict
instead of silently choosing an interpretation.

## Quality principles

- Prefer simple, explicit, maintainable designs.
- Keep business rules out of transport and presentation layers where appropriate.
- Treat authentication, authorization, user-generated text, images, and external inputs as security
  and privacy boundaries.
- Do not introduce premature abstractions or infrastructure.
- Make important failure states explicit and leave the user in a usable state.
- Do not make substantial product decisions implicitly in code.

## Codex-only orchestration pointer

This section is not an implementation instruction. External implementation agents must not open or
use `.codex/runbooks/opencode_implementation.md` and must not launch other agents.

Only the Codex coordinator, after an explicit product-owner request to launch or manage the harness,
may use that runbook.
