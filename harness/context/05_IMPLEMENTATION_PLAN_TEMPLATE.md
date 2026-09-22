# Implementation Plan Template

Create approved plans at `harness/features/RF-XX-Implementation-plan.md`.

Do not create or mark a plan ready while material questions remain. Replace every placeholder, omit
sections that genuinely do not apply, and keep the resulting document self-contained.

---

# RF-XX - Feature title - Implementation Plan

## Status

`Draft` or `Ready for implementation`

Only the product owner may authorize the transition to `Ready for implementation`.

## Source ticket

- Trello title:
- Trello URL:
- Trello list at intake:
- Snapshot captured on:
- Grooming notes: `harness/grooming/RF-XX-grooming.md`

## Objective

What user or product outcome this feature introduces and why it exists.

## Context and current behaviour

Relevant implemented behaviour, accepted decisions, dependencies, and constraints discovered by
inspecting the repository.

## Scope

### In scope

- Explicit behaviour included in this increment.

### Out of scope

- Closely related behaviour deliberately deferred or owned by another ticket.

## User experience

Describe the concrete flow, including loading, empty, validation, error, pending, success,
unavailable, destructive-confirmation, refresh, and navigation behaviour where relevant.

## Functional requirements

### FR-1 - Requirement name

Observable requirement and relevant business rules.

## Technical approach

Explain the selected approach and why it was chosen. Name actual affected modules and boundaries
only after inspecting the repository.

### Affected areas

- Frontend:
- Backend/application:
- Domain/data model:
- Storage/background work:
- Configuration/deployment:
- Documentation:

### Data and migration requirements

Entities, invariants, ownership, lifecycle, migration, rollback, and compatibility considerations.

### API and integration requirements

Externally important requests, responses, authorization, idempotency/concurrency, and failure
behaviour. Treat external payloads as untrusted runtime input.

### Security and privacy

Authentication, authorization, data exposure, image/file handling, abuse cases, retention,
deletion, logging, and secrets relevant to the feature.

## Implementation sequence

1. Ordered, independently checkable implementation step.
2. Continue through integration and documentation.

## Validation strategy

### Automated tests

- Important behaviours, invariants, regressions, and representative failures.

### Manual validation

- Flows or environmental behaviour that automated checks cannot prove.

### Commands

List the repository's exact format, lint, type, test, build, migration, or integration commands once
they exist. Do not invent commands for an empty or unknown stack.

## Acceptance criteria

- [ ] Independently verifiable outcome.
- [ ] Representative failure leaves the system in a safe, usable state.
- [ ] Important existing behaviour is verified against regression.

## Dependencies and ordering

Required earlier tickets, services, decisions, or environment setup.

## Risks and mitigations

Material technical, product, security, privacy, migration, or operational risks and the chosen
mitigation.

## Harness handoff notes

Anything the implementation agent must know about existing worktree changes, unavailable services,
required manual gates, or limits of its authority.

## Resolved grooming decisions

Summarise the decisions confirmed by the product owner so the implementation rationale is preserved.

## Remaining questions

Must be exactly `None` before the status can become `Ready for implementation`.
