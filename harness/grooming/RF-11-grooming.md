# RF-11 - Estados de una consulta - Grooming

## Status

`Ready for implementation`

The product owner explicitly requested the detailed implementation plan on 2026-09-29. The
self-contained contract is `harness/features/RF-11-Implementation-plan.md`, marked
`Ready for implementation`. This approval finalizes the plan; it does not launch the harness.

## Trello snapshot

- Title: `RF-11 · Estados de una consulta`
- URL: https://trello.com/c/5bQ0jXnq/13-rf-11-estados-de-una-consulta
- Board: `APP - NextPost`
- List: `Fase 2`
- Labels: None
- Members: None
- Due date: None
- Started at: None
- Card completion: Not complete
- Checklists: None
- Comments: None
- Captured on: `2026-09-29T16:42:16+02:00`
- Last Trello activity at intake: `2026-09-22T14:36:27.224Z`

### Description and acceptance criteria at intake

**Historia de usuario**

Como autor, quiero conocer el estado de mi consulta y cuándo deja de recibir votos.

**Criterios de fase 2 acordados**

- Estados pertinentes: preparación temporal, abierta, finalizada por su autor y no disponible por
  eliminación o retirada del administrador.
- Una consulta abierta acepta votos autorizados. Finalizar exige declarar una, varias o ninguna
  foto y detiene nuevos votos, incluso desde pantallas antiguas.
- No hay plazo, fecha de vencimiento ni cierre automático: sigue abierta hasta que el autor finaliza
  o elimina, o el administrador la retira.
- Finalizar retira el acceso a las fotos e inicia su borrado sin periodo adicional de visualización.

**Deferred:** automatic expiry and duration selection. Reference: DEC-017/021/022.

Intake note: the identifier, title, board and `Fase 2` list agree with the repository phase inventory.
The card is open and incomplete. It has no labels, members, dates, checklists or comments. Trello was
read only.

## Intended outcome

Give every persisted consultation one server-authoritative lifecycle whose current state consistently
controls visibility, image access, voting eligibility and author presentation. An open consultation
remains open indefinitely. Finalization, author deletion and restricted administrator removal are
distinct terminal causes, all of which immediately stop third-party access; only finalization creates
an outcome. Preparation remains a temporary authoring session rather than a persisted consultation
state.

## Current code findings

- RF-10 added `ConsultationState` with `open`, `finalized`, `deleted` and `removed`, mirrored by the
  PostgreSQL check constraint in Alembic revision `20260928_0004`. Publication creates only `open`.
- `ConsultationLifecycle` and `can_access` already deny every protected read, vote and link-management
  operation when the current persisted lifecycle is not `open`. Protected detail and media routes
  collapse denied terminal reads to the generic `consultation_unavailable` response.
- Public and Private protected reads reload the current database row on each request. There is no
  client-side lifecycle authorization shortcut and no automatic-expiry column, scheduler or worker.
- `GET /api/consultations/{id}` returns a state string for an accessible open consultation. The
  frontend validates only that it is a string; it does not use a closed union or visibly label the
  current state. The post-publication screen says that the consultation is live but does not show an
  explicit `Open` status.
- `ConsultationUnavailable` already provides generic copy: `This consultation is unavailable. It may
  have ended or been removed.` It intentionally does not reveal whether a resource was deleted,
  removed, private, missing or terminal.
- No service or endpoint currently transitions a consultation after publication. There is no
  `finalized_at`, `deleted_at`, `removed_at` or general lifecycle-change timestamp, no final-choice
  table, no vote model and no terminal-operation audit record.
- RF-07/RF-10 already maintain a private file ledger. Promoted photos survive temporary cleanup, and
  missing bytes make the consultation unavailable. No published-photo finalization/deletion purge
  operation exists yet.
- The complete automated repository suites pass at intake: 265 backend tests with four live-
  PostgreSQL tests skipped in the ordinary run, 263 frontend tests, backend/frontend formatting,
  linting, strict type checks, production build and dependency audit. The isolated Compose smoke
  could not be rerun because Docker Desktop 4.86 crashes while initializing its inference-manager
  socket; this is an environment failure, not RF-11 evidence.

## Dependencies and conflicts

- DEC-017 removes automatic duration and expiry. RF-11 must not add `expires_at`, an expiry state, a
  duration selector, scheduled closure or expiry copy.
- DEC-021 fixes finalization as one atomic action that declares one, several or no photos, closes the
  consultation, stops access/voting and starts no-buffer image deletion. RF-19 supplies this action
  and RF-20 supplies the declaration/outcome rules; RF-11 must not invent a separate close action.
- DEC-022 distinguishes restricted administrator removal from finalization/deletion. The broad
  moderation UI is deferred, but a restricted operational removal mechanism is still required before
  real-user exposure.
- DEC-023 allows minimum non-image outcome records only after finalization. Deleting or removing an
  unfinalized consultation produces no outcome. A finalized item may retain private minimal outcome
  records after later deletion/removal.
- RF-12 owns the author's list of open and finalized consultations and its state/date/vote-count
  presentation. RF-11 should define the projection contract it consumes without implementing that
  complete list.
- RF-13 owns author deletion and confirmation. RF-16 owns vote persistence and the race in which a
  vote arrives as a terminal action commits. RF-19/RF-20 own finalization/final choice. RF-37 owns
  durable photo purge, retry/recovery and restore safety.
- RF-10 already reserved all accepted terminal enum values. Changing their names or meanings would
  require a migration and coordinated updates to access checks, indexes and consumers.

## Candidate approach

### Recommended direction

Treat RF-11 as the shared lifecycle contract and smallest reusable foundation for its consuming
tickets, without absorbing their user actions:

1. Keep `open`, `finalized`, `deleted` and `removed` as internal persisted states. Treat
   `unavailable` as an external access result, not a fifth database lifecycle.
2. Treat temporary preparation as `PhotoUploadSession` state, not as a `Consultation` row/state.
3. Introduce a focused domain transition policy that defines which actor/action may leave `open`,
   prohibits reopening and rejects invalid repeated/cross-terminal transitions. Later RF-13,
   RF-19/RF-20 and restricted removal must call it rather than writing state directly.
4. Serialize every terminal transition and vote commit on the current consultation row. Re-check
   `open` inside the transaction so a stale screen cannot add a vote after a terminal action wins.
5. Keep protected detail/media/link reads generically unavailable for every non-open state. Provide
   separate owner-only text/outcome projections later through RF-12/RF-18/RF-21; never make the
   existing photo detail endpoint serve finalized content.
6. Add no lifecycle-transition timestamps. Keep the existing publication date for the existing
   publication fact and avoid a generic event-sourcing/audit framework, expiry infrastructure or
   background worker.
7. Make the current post-publication view visibly say `Open` and use a strict frontend lifecycle
   union. Full open/finalized lists and terminal controls stay with their tickets.
8. Record RF-11 as a reusable increment whose full end-to-end acceptance remains gated by the real
   RF-16 vote and RF-13/RF-19/RF-20/RF-37 terminal consumers.

### Alternatives and trade-offs

- **Recommended — reusable lifecycle foundation:** respects the accepted ticket split, removes
  duplicated state logic and gives later mutations one concurrency contract. It cannot alone prove
  real finalization/deletion/vote races, so those gates remain explicit.
- **Combine RF-11 with finalization, choice and deletion now:** creates an immediately terminal flow,
  but silently absorbs RF-13/RF-19/RF-20/RF-37, including votes/outcomes and physical deletion. This
  is too broad and conflicts with accepted ownership.
- **Only add an `Open` badge:** creates a visible change but leaves transition/concurrency invariants
  undefined and does not provide the lifecycle foundation the downstream tickets require.

## Questions

### Open

None.

### Resolved

- 2026-09-29: The product owner explicitly selected RF-11 and asked to begin it after closing prior
  work.
- 2026-09-29: The complete current Trello card was consumed read-only through the authenticated
  project connection. No Trello mutation was performed.
- 2026-09-22 decisions already settle that there is no automatic expiry, duration selector,
  reopening or separate choice-free close action (DEC-017/021).
- Preparation is temporary and is not a persisted consultation lifecycle (DEC-012).
- Finalization, author deletion and administrator removal immediately revoke public/private access
  and begin no-buffer photo deletion; only finalization creates an outcome (DEC-021/022/023).
- Internal terminal causes may remain distinct while unauthorized/non-owner reads receive generic
  unavailable behavior (DEC-028 and the implemented RF-09 access contract).
- 2026-09-29: The product owner rejected lifecycle-transition dates. RF-11 adds no `finalized_at`,
  `deleted_at`, `removed_at` or `state_changed_at`; the existing `published_at` remains the only
  product event date in this increment.
- 2026-09-29: By requesting the detailed final plan after reviewing the consolidated batch, the
  product owner accepted the recommended retry/concurrency rule: consumers lock the consultation,
  the first terminal commit wins, an exact proven retry may return the existing result, and a
  different later terminal action conflicts safely. No terminal priority or reopening exists.
- 2026-09-29: The product owner approved RF-11 as a reusable lifecycle-foundation increment. Full
  end-to-end state validation remains attached to RF-13/RF-16/RF-19/RF-20/RF-37 rather than being
  silently absorbed into RF-11.
- 2026-09-29: The product owner explicitly requested plan finalisation. Harness launch remains a
  separate action.

## Proposed scope

### In scope

- One explicit, server-authoritative consultation lifecycle contract using the accepted internal
  states and actor/action transition rules.
- No-reopen and no-expiry invariants.
- Transaction/locking requirements shared by later vote and terminal mutations.
- Strict backend/frontend lifecycle projections and a visible `Open` state in the existing
  post-publication owner view.
- Generic unavailable behavior for non-open protected detail, media and private-link access.
- Focused automated tests and consumer contracts for RF-12/13/16/19/20/37.
- No lifecycle-transition timestamps or migration.

### Out of scope

- A duration, expiry date, automatic close, scheduler, queue or worker.
- Finalization UI/API, final-choice persistence or outcome computation (RF-19/RF-20).
- Author deletion and its confirmation (RF-13).
- Vote persistence, one-vote enforcement or result aggregation (RF-16/RF-18).
- The complete author consultation list/history (RF-12), participant history (RF-21), discovery
  feed (RF-14) or sharing journey (RF-26).
- Physical published-photo deletion/retry/restore operations beyond the shared immediate-revocation
  contract (RF-37).
- A moderation console or broad administrator system; restricted removal remains a later consumer.

## Validation outline

- Domain tests for allowed `open -> finalized/deleted/removed` transitions, actor authorization,
  no reopen, invalid cross-terminal actions and exact-retry semantics once confirmed.
- PostgreSQL transaction tests proving a stale vote cannot commit after finalization/deletion/removal
  and two competing terminal operations produce one coherent winner when their consumer services
  exist.
- API tests that every non-open state denies detail, each photo and private-link operations with the
  same safe unavailable contract, including stale direct links and already-open screens making new
  requests.
- Model/schema tests that the existing lifecycle values remain aligned without a migration.
- Frontend tests for strict state validation, visible Open presentation, generic unavailable copy,
  session handling and no expiry/date promise.
- Consumer validation under RF-13/RF-16/RF-19/RF-20/RF-37 for atomic final choice, late-vote denial,
  immediate media cutoff, physical deletion retry and restore without re-exposure.
- Run the full backend/frontend quality suites and an isolated PostgreSQL/Compose smoke once the
  implementation plan is approved and Docker is healthy.

## Readiness checklist

- [x] Desired outcome is unambiguous.
- [x] Scope and exclusions are confirmed.
- [x] Code impact was inspected.
- [x] Dependencies and conflicts are resolved.
- [x] Technical approach is selected.
- [x] UX and failure states are confirmed where applicable.
- [x] Security, privacy, retention, and abuse implications are identified.
- [x] Data migration and operational implications are resolved where applicable.
- [x] Test and manual validation expectations are agreed.
- [x] No material question remains.
- [x] Product owner explicitly approved plan finalisation on 2026-09-29.
