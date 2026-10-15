# RF-11 - Consultation lifecycle states - Implementation Plan

## Status

`Ready for implementation`

The product owner rejected new lifecycle-transition dates and explicitly requested this detailed
plan on 2026-09-29 after reviewing the consolidated grooming decisions. This finalizes the RF-11
implementation contract. It does not authorize the external harness, a commit, push, deployment or
Trello mutation.

## Source ticket

- Trello title: `RF-11 · Estados de una consulta`
- Trello URL: https://trello.com/c/5bQ0jXnq/13-rf-11-estados-de-una-consulta
- Trello list at intake: `Fase 2`, on the configured `APP - NextPost` board
- Snapshot captured on: `2026-09-29T16:42:16+02:00`
- Last Trello activity at intake: `2026-09-22T14:36:27.224Z`
- Grooming notes: `harness/grooming/RF-11-grooming.md`

## Objective

Establish one explicit and reusable consultation-lifecycle contract for every current and future
consumer. A persisted consultation is internally `open`, `finalized`, `deleted` or `removed`.
Publication creates only `open`; temporary preparation remains an upload-session concern. Protected
reads, photo access, link management and later voting are available only while the latest persisted
state is `open`.

This increment makes the existing open state strict and visible, removes duplicated lifecycle
definitions, and provides a pure transition policy for later terminal operations. It does not add a
finalization, deletion or administrator-removal action. Those operations remain owned by RF-13,
RF-19/RF-20 and the restricted-administrator/RF-37 work, where their database, outcome and file
side effects can be committed coherently.

There is no automatic expiry, duration selection, reopening or lifecycle-transition date. The
existing publication date remains unchanged.

## Context and current behaviour

- RF-10 added `ConsultationState` in `backend/app/models.py` with `open`, `finalized`, `deleted` and
  `removed`. Alembic revision `20260928_0004` enforces exactly those strings and publication creates
  only `open`.
- `backend/app/consultation_access.py` separately duplicates the same values in
  `ConsultationLifecycle`. Its pure `can_access` policy already denies every non-open lifecycle for
  protected read, vote and manage operations.
- `backend/app/consultation_service.py` creates open consultations, counts open capacity, converts
  the ORM state into the access-policy enum and reloads current state for protected reads. It has no
  state-transition function and must not gain a partial terminal mutation in RF-11.
- `backend/app/api/consultations.py` returns `state` on publication and protected detail. These
  endpoints can only succeed for an open consultation, but `backend/app/schemas.py` currently types
  the response as an unconstrained string.
- `frontend/src/consultationApi.ts` likewise accepts any string for published/detail state. The
  post-publication `PublishedSuccess` screen says the consultation is live but does not render an
  explicit state label.
- `ConsultationUnavailable.tsx` already supplies safe generic unavailable copy. It does not reveal
  whether a consultation is missing, Private without a valid link, finalized, deleted or removed.
- No vote model, final-choice model, owner consultation list, terminal endpoint, administrator role,
  published-photo deletion operation or outcome projection exists. RF-11 must not invent any of
  them.
- RF-07/RF-10 provide a private photo ledger and protected media reads. Promoted photos are preserved
  from temporary cleanup; RF-37 later owns terminal purge and retry/recovery.
- The local worktree contains substantial uncommitted implementation and documentation changes from
  RF-06 through RF-10. They are user/project work and must be preserved.
- At plan finalization, the ordinary automated suites pass: 265 backend tests with four live-
  PostgreSQL tests skipped in that environment and 263 frontend tests, plus formatting, lint, strict
  type checks, production build and dependency audit. Docker Desktop 4.86 currently fails to start
  because its local inference-manager socket cannot be initialized; this is an environment gate for
  later Compose validation, not permission to weaken tests.

## Scope

### In scope

- One canonical backend lifecycle enum/value source for `open`, `finalized`, `deleted` and `removed`,
  reused by persistence and access policy without changing stored values.
- A pure terminal-transition decision contract covering apply, same-target retry candidate and
  conflicting terminal state.
- Explicit consumer documentation for row locking, current-state recheck, authorization, payload
  identity and atomic side effects.
- Strict backend success responses that expose only `open` from publication and protected-detail
  endpoints.
- Strict frontend runtime/type validation that rejects any unexpected state on those open-only
  success contracts.
- A visible, accessible `Open` status on the existing post-publication owner view.
- Complete terminal-state regression tests for protected detail, every photo and Private-link
  management, retaining the generic unavailable response.
- Documentation updates that hand the lifecycle and concurrency contract to RF-12/13/16/19/20/37.

### Out of scope

- `finalized_at`, `deleted_at`, `removed_at`, `state_changed_at` or any other new lifecycle date.
- A database migration or change to the accepted persisted enum strings/constraints.
- Duration, expiry date, automatic closure, scheduled work, queue, worker or expiry copy.
- A state-changing HTTP endpoint or service that can leave a partially finalized/deleted/removed
  consultation without its required outcome and photo side effects.
- Final-choice selection, finalization confirmation, outcome computation or retained result records
  (RF-19/RF-20/DEC-023).
- Author deletion and confirmation (RF-13).
- Vote storage, one-vote enforcement, late-vote transactional races or aggregate results
  (RF-16/RF-18).
- Physical deletion of published images, retry alerts, backups or restore safety (RF-37).
- Owner consultation list/history (RF-12), participant history (RF-21), feed (RF-14), sharing journey
  (RF-26), moderation UI or broad administrator roles.
- Reopening or changing a finalized declaration.

## User experience

### Open owner state

After successful publication and protected detail loading, the existing persisted owner view shows a
compact text status `Open`. It must not rely on color alone. The existing `Published` heading and
`Your consultation is now live.` copy may remain; the status clarifies the lifecycle without adding
an expiry date or duration.

The state presentation uses the server response and is not computed from local publication success,
elapsed time or a client clock. It survives a normal reload/re-fetch through the existing protected
detail route.

### Unexpected state or invalid response

Publication and protected-detail success contracts are open-only. If the client receives a missing,
unknown or non-open state in a nominal success response, treat the payload as invalid/unavailable.
Do not render photos, link controls or invented state copy from it. Preserve the existing retryable
error behavior and session-loss handling.

### Terminal and unavailable state

For current protected detail, media and Private-link surfaces, a non-open persisted state remains
unavailable even to the author. The existing photo-bearing detail endpoint must never become an
owner history endpoint. Generic user-facing unavailable copy must not distinguish finalized,
deleted, removed, missing, invalid-link or unauthorized cases.

Later RF-12/RF-18/RF-21 owner/participant projections may show permitted text-only outcomes through
separate contracts. They must not reuse this protected photo detail response after terminal state.

### No expiry or transition dates

Do not display a countdown, closing date, state-change date, expiry promise or duration control.
RF-11 adds no new date field. The existing `published_at` remains available for future consumers as
the publication date; it must not be relabelled as a finalization/deletion/removal date.

## Functional requirements

### FR-1 - Canonical persisted lifecycle

Use one canonical lifecycle value definition for `open`, `finalized`, `deleted` and `removed` across
the ORM and access policy. Preserve the current database strings, ordering-neutral semantics and
Alembic constraint. Avoid parallel hand-maintained enums whose values can drift.

Preparation states (`active`, `discarded`, `abandoned`, `consumed`) remain on
`PhotoUploadSessionState`; they are not consultation lifecycle values.

### FR-2 - Open-only publication and protected-detail success

Publication creates and returns exactly `open`. Protected consultation detail succeeds only after
current-state authorization and returns exactly `open`. Backend response schemas must express this
open-only invariant rather than an arbitrary string.

No fallback should coerce an unknown database value to open. Invalid/corrupt state must fail safely
without exposing text, photos, link tokens or storage identifiers.

### FR-3 - Pure transition policy for consumers

Add a small domain policy that accepts the current lifecycle and requested terminal target. It must
return or express three distinct outcomes:

1. `apply`: current is `open` and requested target is `finalized`, `deleted` or `removed`;
2. `same_target`: current already equals the requested terminal target, meaning the consumer may
   investigate an exact retry but must not automatically claim success;
3. `conflict`: current is terminal and requested target differs, or either input is unsupported.

The policy must never mutate an ORM row, commit a transaction, delete a file, compute an outcome or
authorize an actor. It prevents duplicated transition interpretation while leaving atomic side
effects to the owning ticket.

`same_target` is not sufficient proof of idempotency. RF-19/RF-20 must compare a stable
finalization request identity/fingerprint and declared selection. RF-13 and restricted removal must
define equivalent retry evidence appropriate to their operations. Without matching evidence, the
consumer returns a safe conflict.

### FR-4 - First terminal commit wins

Document and test the consumer protocol:

1. authenticate and authorize the actor for the requested operation;
2. begin the transaction and lock the consultation row with PostgreSQL `FOR UPDATE`;
3. read the current lifecycle under that lock;
4. evaluate the shared transition policy;
5. for `apply`, perform every required database side effect in the same transaction and write the
   terminal state last or as part of the same atomic unit;
6. commit once; only after durable revocation may physical-file deletion/retry proceed according to
   RF-37;
7. for `same_target`, return the existing result only after operation/payload identity is proven;
8. for `conflict`, change nothing and return a safe, owner-appropriate conflict.

There is no priority ordering among finalization, author deletion and administrator removal. The
transaction that commits first determines the terminal state. A losing operation cannot overwrite,
reinterpret or reopen it.

### FR-5 - Current-state authorization

Every protected detail, text, photo, Private-link management and later vote request uses the latest
committed database lifecycle. Only `open` can pass lifecycle authorization. Terminal states return
generic unavailable behavior on protected content routes.

RF-11 must preserve DEC-029: already-rendered bytes are not recalled or polled away, but every new
request/reload is reauthorized. No browser-persistent offline access or cached terminal photo is
introduced.

### FR-6 - Strict frontend contract

In `frontend/src/consultationApi.ts`, type open-only publication/detail state as the literal `open`.
Runtime guards must require exact equality, not merely `typeof state === "string"`. An unexpected
state throws the existing safe unavailable/invalid-response error path.

Do not create a client-side terminal state machine that can authorize content. Frontend state is
presentation only; the backend database remains authoritative.

### FR-7 - Visible Open presentation

Render the exact English label `Open` on `PublishedSuccess` after the persisted detail has loaded.
Use existing visual primitives or a small status element consistent with the light design. The
label must remain readable without color, at narrow widths and at 200% zoom, and must not imply an
expiry date.

Loading, retryable failure, session loss and Private-link loading/mutation behavior remain unchanged.
Public success must still make no link request.

### FR-8 - Generic terminal unavailability

For `finalized`, `deleted` and `removed`, prove the same protected-route result for owner and other
accounts where applicable: no consultation text, photo bytes, media metadata, link token, internal
state or existence detail leaks. Continue using the existing generic `consultation_unavailable`
contract and safe `This consultation is unavailable` presentation.

Do not expose the internal terminal cause through status codes, detail bodies, headers, logs or
timing-dependent alternate code paths where practical.

### FR-9 - No dates, migration or premature operations

Do not add lifecycle-transition date columns, a migration, terminal HTTP routes, an administrator
role, an outcome table, a vote table, a deletion job or scheduled expiry. Preserve the current
`published_at`, created/updated technical fields and schema revision.

## Technical approach

Create a focused domain module, for example `backend/app/consultation_lifecycle.py`, containing the
canonical enum and pure transition decision types/function. It must have no FastAPI, SQLAlchemy
session, storage or configuration dependency. Persistence can import the enum from this module; the
access policy can reuse it directly. If a compatibility alias is needed for existing imports, keep
one documented alias rather than a second independent enum.

Keep HTTP handlers and `consultation_service.py` thin. They consume the shared enum, enforce exact
open-only responses and retain current authorization. Do not add a callable database mutation that
sets a terminal state without the consumer-owned side effects.

### Affected areas

- Backend domain: new `backend/app/consultation_lifecycle.py` (or an equivalently focused module).
- Backend persistence: `backend/app/models.py` imports the canonical lifecycle without changing
  columns or stored values.
- Backend access: `backend/app/consultation_access.py` reuses the canonical lifecycle and keeps
  non-open denial.
- Backend schemas/service: `backend/app/schemas.py` and focused projection code express open-only
  success; no route or mutation is added.
- Backend tests: add lifecycle-policy tests and expand consultation access/service/API terminal-state
  coverage.
- Frontend client: `frontend/src/consultationApi.ts` uses exact open literals/guards.
- Frontend presentation: `frontend/src/PublishedSuccess.tsx` and tests add the accessible `Open`
  state; reuse `ConsultationUnavailable` unchanged unless a regression fix is necessary.
- Documentation: README consumer notes, `03_DECISIONS.md`/`04_PROJECT_STATE.md` evidence after review.
- Storage/background/configuration/deployment: no change.

### Data and migration requirements

No migration is allowed or required. Preserve:

- `consultations.state` storage and its existing `open|finalized|deleted|removed` constraint;
- existing `open` default and index behavior;
- `published_at`, `created_at` and `updated_at` meanings;
- existing rows and RF-10 publication fingerprints/link state;
- source upload-session and published-photo associations.

Add a test that the canonical lifecycle values exactly match the accepted database/model set so a
future code-only rename cannot drift from migration `20260928_0004`. Do not edit the historical
migration merely to move the Python enum.

### API and integration requirements

No endpoint or method is added.

Existing successful response contracts become stricter:

- `POST /api/consultations` returns `state: "open"`;
- `GET /api/consultations/{id}` returns `state: "open"` only after current-state authorization;
- photo content and owner Private-link routes continue to reject all terminal states with the
  existing safe unavailable behavior.

Do not expose transition targets or internal causes through a new public lifecycle endpoint.
RF-12 later defines the owner list projection; RF-13/19/20 define their mutation requests and
idempotency payloads.

### Security and privacy

- Treat the database lifecycle as an authorization input on every protected request.
- Never trust a frontend `Open` label or cached response to authorize later media/vote access.
- Keep internal terminal causes hidden from unauthorized/recipient content surfaces.
- Do not make finalized photos accessible to their author through the existing detail/media API.
- Do not log consultation text, link tokens, storage keys, photo bytes or user-supplied filenames.
- Do not make files public, weaken no-store/no-referrer headers or add a static media path.
- Preserve trusted-origin protection on current cookie-authenticated mutations; RF-11 adds none.
- A corrupt/unknown lifecycle fails closed.
- Consumer terminal actions must revoke database access atomically before asynchronous/retryable
  physical deletion, so file-deletion failure cannot reopen access.

## Implementation sequence

1. Add the canonical lifecycle/transition-policy module with exhaustive pure unit tests.
2. Reuse its lifecycle enum in ORM/access code while preserving stored strings and compatibility.
3. Tighten backend publication/detail response schemas and projections to literal `open`; add safe
   invalid/corrupt-state coverage.
4. Expand access/service/API tests across `finalized`, `deleted` and `removed` for owner, other
   account, Public/Private, photo association and Private-link operations.
5. Tighten frontend publication/detail types and runtime guards to exact `open`; test missing,
   unknown and terminal values as invalid responses.
6. Add the accessible `Open` presentation to the persisted post-publication view without changing
   existing loading/error/link flows.
7. Add concise consumer documentation for RF-12/13/16/19/20/37, including first-commit-wins locking,
   exact-retry proof, generic unavailability and no lifecycle dates.
8. Run the complete repository validation suite. Run Compose configuration/build and an isolated
   smoke when Docker is healthy; record the current environment blocker honestly if it persists.
9. Update project state only from verified evidence. Do not mark later terminal/vote/photo consumers
   implemented or complete.

## Validation strategy

### Automated tests

- Canonical values are exactly `open`, `finalized`, `deleted`, `removed` and match the ORM/migration
  contract.
- Transition matrix: open to each terminal target is `apply`; same terminal target is
  `same_target`; different terminal target is `conflict`; terminal to open and unknown inputs fail.
- The pure policy has no database commit/storage side effect and cannot authorize an actor.
- Publication persists/returns open and remains idempotent under existing RF-10 tests.
- Protected detail returns open only; every terminal state yields the same safe unavailable result
  for owner and non-owner without text/photo/internal-state leakage.
- Each protected photo route rejects terminal lifecycle even with an exact photo ID and valid/stale
  Private token.
- Owner link read/disable/replace/create rejects every terminal state and cannot reveal/generate a
  token.
- Existing access-policy tests still cover unauthenticated, owner vote denial, Public/Private and
  invalid-operation behavior.
- Frontend runtime guards accept only `open` and reject missing, arbitrary, finalized, deleted and
  removed values.
- PublishedSuccess displays `Open` only after valid persisted detail loads and preserves Public/
  Private link behavior, loading, retry and session loss.
- Existing account/profile/photo/text/audience/link/publication/composer suites remain green.

Live vote-versus-terminal and terminal-versus-terminal PostgreSQL races cannot be claimed in RF-11
because the owning mutations do not yet exist. The consumer plans must use the documented lock order
and add those real tests when implementing RF-13/RF-16/RF-19/RF-20/restricted removal.

### Manual validation

- Publish through the existing composer and confirm the persisted success view visibly says `Open`
  for Public and Private consultations.
- At 320 px, ordinary desktop and 200% zoom, verify the status is readable without color, does not
  overflow and does not introduce an expiry/date promise.
- Confirm Public success makes no Private-link request and Private success retains current link
  controls.
- Simulate malformed/terminal detail responses in a controlled test build and verify no photos/link
  controls render from them; retry/back/session-loss behavior remains usable.
- When Docker is healthy, run the isolated built-stack publication/restart smoke and verify the
  `Open` state comes from persisted detail after restart.
- Keep real terminal-operation, late-vote and physical-deletion checks explicitly pending for their
  owning tickets.

### Commands

```powershell
.\.venv\Scripts\python -m pytest backend\tests
.\.venv\Scripts\python -m ruff check backend
.\.venv\Scripts\python -m ruff format --check backend
.\.venv\Scripts\python -m mypy backend\app
Push-Location frontend
npm test
npm run format:check
npm run lint
npm run typecheck
npm run build
npm audit --audit-level=high
Pop-Location
docker compose config --quiet
docker compose build backend frontend
```

No Alembic upgrade/downgrade is required because RF-11 must add no migration. If the implementation
unexpectedly requires one, stop and report a conflict with this approved plan instead of inventing
schema scope.

## Acceptance criteria

- [ ] Persistence and access use one canonical lifecycle definition with exactly the existing four
      values; preparation remains outside consultation lifecycle.
- [ ] The shared pure policy exhaustively distinguishes apply, same-target retry candidate and
      conflict, prohibits reopening and performs no persistence/storage side effect.
- [ ] Consumer documentation requires authorization, PostgreSQL row locking, current-state recheck,
      atomic database side effects, first-terminal-commit-wins and exact retry proof.
- [ ] Publication and protected-detail success responses expose exactly `open`; unknown/corrupt/
      terminal state fails closed.
- [ ] Frontend types and runtime guards accept exactly `open` for these responses and never render
      protected terminal content from an invalid success payload.
- [ ] The persisted post-publication owner view visibly and accessibly displays `Open` without an
      expiry, duration or state-change date.
- [ ] Finalized, deleted and removed consultations yield the same safe unavailable behavior across
      detail, every photo and owner Private-link operations without leaking cause or content.
- [ ] No lifecycle date, migration, terminal endpoint, outcome/vote table, worker, expiry mechanism,
      deletion operation, administrator system or later-ticket UI is added.
- [ ] Existing RF-01 through RF-10 behavior remains green under the complete automated quality suite.
- [ ] Compose/build/manual evidence is recorded honestly; Docker environment failure is not reported
      as product success and does not justify changing scope.
- [ ] RF-13/RF-16/RF-19/RF-20/RF-37 consumer race/side-effect gates remain explicit and are not
      claimed complete by this reusable increment.

## Dependencies and ordering

- Depends on RF-10 consultation persistence/publication and RF-09 request-time access policy. Read
  their complete approved plans and inspect current code before editing.
- RF-06 supplies the current post-publication view where `Open` becomes visible. Preserve its wizard,
  dirty-state and success/link behavior.
- RF-12 consumes lifecycle for the private author list and may use existing `published_at`; RF-11
  supplies no new dates.
- RF-13 consumes `open -> deleted`; RF-16 must lock/recheck open when committing a vote;
  RF-19/RF-20 consume `open -> finalized`; restricted administrator removal/RF-37 consume
  `open -> removed` and terminal media purge.
- RF-18/RF-21 consume retained non-image outcomes after RF-19/RF-20. They must not depend on the
  protected photo-detail endpoint for terminal data.
- Implement RF-11 before those consumers so they share one transition vocabulary and lock contract.
  Full RF-11 card validation completes only as the named consumer gates are exercised.

## Risks and mitigations

- **Duplicate enum drift:** one canonical definition plus exact value/constraint tests.
- **Partial terminal operation:** RF-11 provides no database mutation; consumer plans must commit
  state and database side effects atomically.
- **Same state mistaken for safe retry:** `same_target` is only a candidate; exact operation/payload
  proof remains mandatory.
- **Stale vote after closure:** consumer row-lock protocol and current-state recheck; real race test
  belongs to RF-16/RF-19/20.
- **Terminal cause leakage:** keep generic unavailable response and test all terminal states through
  the same protected paths.
- **Owner photo retention by accident:** finalized owner history uses a separate later text-only
  projection; current media/detail stays open-only.
- **Frontend treated as authority:** exact type/guard improves safety but every protected server
  request still reloads authoritative state.
- **Scope absorption:** no endpoint, migration, vote/outcome/deletion/admin machinery or future
  screen in this increment.
- **Docker environment failure:** retain green local evidence, record the external blocker and rerun
  isolated Compose validation after Docker is repaired; never reset Docker data as a shortcut.

## Harness handoff notes

- Read `AGENTS.md`, all seven source-of-truth context files, RF-11 grooming and this plan completely.
  Read RF-09/RF-10/RF-06 plans where their access/publication/UI contracts are consumed.
- Preserve the dirty worktree and every unrelated user/dependency change. Do not commit, push,
  deploy, mutate Trello or reset Docker data.
- Implement only the reusable lifecycle foundation. Do not add a convenient terminal endpoint or
  direct state setter; without outcome/photo/vote side effects it would violate accepted invariants.
- Keep English identifiers, comments and product copy. Do not expose protected data or internal
  terminal causes in errors/logs.
- Docker Desktop 4.86 failed locally at plan finalization on its `dockerInference` runtime socket.
  Local automated suites were green. Recheck Docker; if it remains unavailable, complete all other
  checks and report the exact unverified Compose gate rather than modifying Docker installation/data.
- External agents must not open the Codex-only coordinator runbook or launch other agents.

## Resolved grooming decisions

- Persisted lifecycle is open/finalized/deleted/removed; unavailable is an access result and
  preparation remains an upload-session state.
- No automatic expiry, duration, reopening or separate close-without-choice action.
- RF-11 is a reusable foundation; actual mutations and side effects remain with RF-13/RF-16/
  RF-19/RF-20/RF-37.
- No lifecycle-transition dates or migration. Existing `published_at` remains unchanged.
- First terminal commit wins after a row lock/current-state check. No terminal action has priority.
- Same-target state alone does not prove idempotency; consumers must prove exact operation/payload
  identity before returning an existing result.
- Protected terminal detail/media/link access stays generically unavailable; later permitted owner/
  participant history uses separate non-image projections.
- The existing owner success view gains a server-backed, accessible `Open` label and strict open-only
  response validation.
- The product owner explicitly requested plan finalisation. Harness launch remains separate.

## Remaining questions

None
