# RF-13 - Delete an owned consultation - Grooming

## Status

`Finalized - implementation plan approved`

The product owner explicitly selected RF-13 on 2026-10-20. This document records the complete
read-only Trello intake, repository-first investigation, inherited binding decisions, candidate
scope and the material decision batches. On 2026-10-20 the owner confirmed the complete first
batch as `1A 2A 3A 4A 5A`, then confirmed every remaining recommendation as
`6A 7A 8A 9A 10A 11A 12A`. No material question remains. No implementation plan had been created
at the time of those choices. The owner then explicitly approved plan finalisation and autonomous
harness launch on 2026-10-20. `harness/features/RF-13-Implementation-plan.md` is the self-contained
contract marked `Ready for implementation` with `Remaining questions: None`.

## Trello snapshot

- Title: `RF-13 · Eliminar una consulta propia`
- URL: https://trello.com/c/NEYa01VK/16-rf-13-eliminar-una-consulta-propia
- Stable short URL: https://trello.com/c/NEYa01VK
- Card ARI:
  `ari:cloud:trello::card/workspace/6aa9032829f8b45ead46cfdd/6aa90bef02713a37000a832c`
- Board: `APP - NextPost`
- Board ARI:
  `ari:cloud:trello::board/workspace/6aa9032829f8b45ead46cfdd/6aa903892e7d7b54f23fae1b`
- List: `Próximo · completar el MVP`
- List ARI:
  `ari:cloud:trello::list/workspace/6aa9032829f8b45ead46cfdd/6aa903892e7d7b54f23fae23`
- State: open and not archived (`closed: false`); incomplete (`complete: false` and
  `dueComplete: false`).
- Position: `114688`
- Start date / due date: None / None
- Labels: None; no omitted labels reported.
- Members: None
- Checklists: None; no omitted checklists reported.
- Comments: None; the complete comment read reported no next page.
- Attachments: None; the complete attachment read reported no next page.
- Custom-field values: None; the complete custom-field read reported no next page.
- Captured on: `2026-10-20T13:53:08.8789035+02:00`; read-only connected Trello intake.
- Last Trello activity at intake: `2026-10-12T11:27:54.403Z`.
- Available activity: created by Negis on `2026-09-15T09:12:15.640Z`; moved by Negis from
  `Funcionalidades` to the then-named `Fase 2` list on `2026-09-22T14:33:14.966Z`; no next
  activity page was reported.
- Intake consistency: identifier, title, configured board, current list and content agree. The
  current list name reflects the 2026-10-12 backlog reorganization. No Trello mutation was
  performed.

### Description and acceptance criteria at intake (verbatim)

**Reorganización del backlog · 2026-10-12**

Retirada voluntaria del autor dentro del ciclo completo. Depende del contrato de borrado publicado
de RF-37. Eliminar sin finalizar no produce un resultado de coincidencia.

Ubicación: Próximo · completar el MVP. El repositorio es la fuente de estado y especificaciones
aceptadas. Esta organización no aprueba un plan ni lanza implementación.

---

**Descripción conservada del ticket**

**Historia de usuario**

Como autor, quiero eliminar una consulta propia y retirar sus fotos.

**Criterios de fase 2 acordados**

- Puedo eliminar una consulta abierta o ya finalizada, con confirmación clara.
- El acceso y los votos se cortan inmediatamente; todas las fotos procesadas y derivados entran en
  el borrado sin buffer de 30 días. La operación cubre también enlaces directos.
- Si elimino una consulta abierta, no se calcula ninguna coincidencia de sus votos. Si ya estaba
  finalizada, pueden permanecer únicamente los resultados privados mínimos sin imágenes definidos
  en DEC-023.
- No se promete retirar copias que terceros ya hubieran guardado fuera de NextPost.

Referencia: DEC-016/021/023 y RF-37.

## Sources and verified baseline

The investigation read `AGENTS.md`, all seven mandatory `harness/context` documents, the complete
phase-2 scope, the 2026-10-12 product reorganization, every active grooming document, and the
approved plans and reviews related to RF-11, RF-12, RF-16, RF-18, RF-26 and RF-37. RF-19, RF-20,
RF-21 and RF-32 have no feature plan or grooming file yet; their accepted boundaries come from the
phase scope, reorganization and decision log. Current code, migrations, Docker topology and relevant
unit/API/frontend/PostgreSQL/storage/recovery tests were inspected. Historical plan statements were
not treated as current-code evidence.

Before intake, the worktree was clean on `main`; `git fetch origin --prune` left
`HEAD == origin/main == bac1caa40a93ac94be5c21a906827e9fcc76e643`. No unpublished change was
present to absorb or overwrite.

## Intended outcome

An authenticated author can deliberately and irreversibly remove an owned open or finalized
consultation after a clear confirmation. The database transaction is the access-revocation
boundary: it serializes against voting and other terminal writers, invalidates all reads of the
consultation and its link capabilities, removes or minimizes non-visual data according to lifecycle,
and hands every published image to RF-37's durable erasure contract. A separately authorized future
DEC-023 participant outcome may survive; filesystem latency or failure never reopens the
consultation.

Deleting an open consultation discards its raw votes and creates no result. Deleting after
finalization preserves only the photo-free minimum outcomes allowed by DEC-023; RF-13 neither
chooses a winning photograph nor implements finalization/results. The removed consultation no
longer acts as a usable or shareable product object. Externally saved third-party copies cannot be
recalled and are not promised to be erased.

## Binding inherited decisions

- Only the author can delete an owned consultation.
- An open or already-finalized consultation can be deleted.
- Author deletion is irreversible: it cannot be undone, reopened or restored through a trash
  window, and there is no 30-day buffer.
- For competing terminal operations on an open consultation, the writer that locks, validates and
  commits first wins. A different stale terminal operation must fail safely; exact retries require
  proof of the same target and payload (DEC-033).
- The commit atomically revokes consultation, photograph, direct-link, Private-link, live-result and
  raw-vote access. A future participant's already-finalized minimum private outcome is the sole
  DEC-023 exception and is not a continued read of the deleted consultation. A read authorized
  before commit may finish and bytes already saved by a third party cannot be recalled; no new
  authorization to the consultation may succeed (DEC-028/029/041).
- Physical erasure uses RF-37's durable, verified and retryable contract. Storage failures after
  commit never restore access or roll back the product deletion.
- Deleting an open consultation removes votes without producing matches, declared selections,
  participant outcomes or final results.
- A consultation deleted after finalization may retain only DEC-023's minimum photo-free private
  outcomes: the declared option identity or explicit no-selection outcome, aggregate vote counts,
  each participant's own outcome and the minimum identifiers/timestamps needed to relate them.
- No photograph, derivative, original, archive, analytics copy, moderation copy or model-training
  copy is retained.
- Storage remains private and every read is authorized against current persisted state.
- RF-13 is the first real consumer of RF-37. RF-19/RF-20 remain the owners of finalization, the
  choice of one/several/no option, aggregate snapshots and final participant outcomes.
- RF-21 owns future participant history and may consume only the private photo-free outcome allowed
  by DEC-023. Restricted RF-32 administrator removal must later reuse RF-37 but is not RF-13.

## Current code findings

### Lifecycle and the finalized-deletion conflict

- `backend/app/consultation_lifecycle.py` and the database model expose exactly `open`, `finalized`,
  `deleted` and `removed`. `open` may transition to one terminal value; an exact same-target retry
  is recognized; every transition from one terminal value to a different terminal value conflicts.
- This correctly enforces first-terminal-commit-wins for a race on an open row, but it makes
  `finalized -> deleted` impossible. That conflicts with RF-13's binding requirement that an author
  can later delete a finalized consultation. The conflict must be resolved explicitly; changing the
  state machine silently would invalidate DEC-033 and existing tests.
- No historical or partial RF-13 implementation, endpoint, UI or migration exists in the current
  tree or reachable Git history searched by RF-13/delete terminology. Existing `deleted` rows are
  fixtures used to prove terminal access denial and RF-37 recovery.

### RF-37 erasure contract

- `mark_media_for_erasure` is transaction-local. It requires the caller to hold an `open`
  consultation backed by its own unique consumed upload session, deactivates the Private capability,
  and marks every session image revoked/deletion-pending. It deliberately performs no commit,
  lifecycle choice, filesystem operation, vote deletion or outcome work.
- `sanitize_terminal_content` clears question, context, audience, publication fingerprint and link
  capability after the owning consumer has stored any permitted replacement outcome.
- `reconcile_terminal_media` discovers terminal consultations that still have a consumed source
  session, marks legacy ready images revoked, deletes exact private objects, verifies absence,
  retains sanitized retry metadata on failure, and only then detaches stable consultation-photo
  options and removes the visual/session ledger. Repeated runs converge idempotently.
- Startup, hourly and restricted manual cleanup already call that reconciliation under a narrow
  PostgreSQL advisory leader lock. Structured counts, immediate failures and overdue deletion are
  observable without logging content. A backend restart retries pending work.
- RF-37's database constraints keep open consultations complete while allowing terminal content and
  media links to be detached. Its terminal allowlist permits stable consultation/option identifiers,
  owner, lifecycle, timestamps and deletion markers, but future consumers own stricter product
  minimization.

### Votes, live results and terminal serialization

- `Vote` stores the current account's raw selected stable `ConsultationPhoto` option with restrictive
  foreign keys and uniqueness on consultation/voter. There is no finalized result or participant
  outcome schema yet.
- Vote submission locks the consultation `FOR UPDATE`, reauthorizes the current open state, resolves
  exact same-option retries, and commits under that lock. An RF-13 writer using the same lock order
  will serialize with voting: a vote committed first is then deleted by open deletion; deletion
  committed first makes the vote unavailable.
- RF-18 author results are live aggregates over raw `Vote` rows and stable options. They never create
  a snapshot. Open deletion must delete votes before commit without calling the aggregate reader or
  materializing a result.
- RF-19/RF-20 must later persist DEC-023 final declarations, aggregates and participant outcomes and
  remove/minimize raw choices atomically before media erasure. RF-13 must preserve those future
  records on post-finalization deletion rather than implementing or guessing their schema.

### Owner lists, reads and navigation

- RF-12's `GET /api/my-consultations` has only `open` and `finalized` tabs. SQL scopes rows to the
  authenticated owner and exact lifecycle before pagination. `deleted` and `removed` never appear.
- Open list/detail returns current question, audience, protected photos and live vote counts.
  Finalized list/detail already returns only ID, state and publication date with no photo access.
  Unknown, foreign, deleted and removed targets collapse to the same
  `consultation_unavailable` 404.
- Public feed, direct entry, owner/reader detail, photo content, private-link management, vote state
  and vote mutation all re-read current state and require strict `open`; every terminal lifecycle is
  already unavailable. Responses are `private, no-store`, `nosniff` and `no-referrer`.
- The React shell uses local navigation state rather than a general URL router. My consultations
  owns its open/finalized tab state, list pagination/refresh and nested owner detail. Owner detail
  has open and minimal finalized branches but no destructive action or confirmation component.
- Direct `/consultations/{id}` entry is routed separately and returns the generic unavailable view
  after terminal commit. RF-26 Private capabilities are carried in the URL fragment and sent in a
  header; database link generation/state, not possession of an old URL, grants access.

### API, authorization and origin protection

- Cookie-authenticated mutations reuse `require_trusted_origin`: a configured Origin is accepted,
  a hostile or `null` Origin is rejected with `origin_not_allowed`, and a missing Origin is allowed
  for same-site/non-browser clients. CORS alone is not treated as authorization.
- Current owner-management routes check server-side account ownership and never trust an owner ID
  from the client. RF-13 should remain under that boundary and must not accept a Private link as
  author authority.
- Existing mutation APIs use strict request schemas, semantic error codes and exact-retry behavior.
  There is no general idempotency table or operation queue.

### Models, migrations, Docker and recovery

- Alembic head is `20261019_0006_media_erasure.py`. It makes content/source-session fields nullable
  only for terminal rows, adds verified media-deletion markers and refuses unsafe downgrade after
  irreversible use. RF-13 needs a new additive revision; editing RF-37's migration is invalid.
- The Compose topology has PostgreSQL and private backend photo volumes. Only the backend mounts
  photo storage. The backend runs Alembic before serving, then performs startup cleanup and an
  hourly maintenance loop. Frontend Nginx has no path to image storage.
- Database-only restore into an empty/current image volume is the supported POC recovery shape.
  Recovery must never recreate access to terminal content; restoring an older image volume is not
  a supported feature.
- Current tests cover lifecycle transitions, generic terminal denial, trusted-origin mutations,
  My-consultations exclusion, vote/terminal row-lock ordering, real-PostgreSQL publication/vote
  races, RF-37 marker preconditions, deletion failure/retry, partial convergence, advisory
  leadership, legacy terminal recovery, migrations and Docker restart/restore. RF-13 needs focused
  consumer tests rather than treating these foundation tests as deletion evidence.

## Dependencies and conflicts

- **RF-11 / DEC-033:** supplies the canonical open-terminal race protocol. The unresolved conflict
  is how a later author withdrawal of an already-finalized consultation is represented without
  pretending that finalization did not win its earlier terminal transition.
- **RF-12:** supplies the owner list/detail insertion point. Current behavior already excludes
  `deleted/removed`; a retained tombstone would be a product and API expansion, not a free reuse.
- **RF-16:** supplies raw votes and the shared consultation row lock. Open deletion must deliberately
  remove them without outcomes and must prove vote/delete race behavior on PostgreSQL.
- **RF-18:** live open counts disappear with the deleted consultation. It supplies no final snapshot
  and must not be called to manufacture one during deletion.
- **RF-19/RF-20:** own finalization and final result persistence. RF-13 can add a compatible
  post-finalization withdrawal marker now, but cannot define their result tables or selection rules.
- **RF-21:** will display only a participant's own minimum result. RF-13 must not remove an already
  finalized DEC-023 outcome or expose it to another participant/author.
- **RF-26:** all direct and Private URLs must become unusable from current state at commit. No URL,
  browser history or cached React state remains authority.
- **RF-37:** mandatory transaction-local marker, sanitizer, durable retry ledger and reconciliation;
  no parallel deletion path is permitted. Its open-only marker means a finalized withdrawal should
  normally find media already revoked by RF-19/RF-20; legacy anomalies remain cleanup work.
- **Restricted RF-32:** administrator removal stays a distinct `removed` operation with its own
  authorization. RF-13 must not let an author convert, reverse or inspect an administrative removal.

## Accepted approach

Add a nullable `author_deleted_at` marker to `Consultation`, set for every successful voluntary
author deletion. For an open consultation, also set canonical lifecycle `deleted`; for an already
finalized consultation, retain lifecycle `finalized` and set the marker. This preserves the meaning
of the first terminal transition while representing the later voluntary withdrawal required by the
ticket. Every owner/finalized query must additionally require `author_deleted_at IS NULL`;
shared/direct/media/vote reads already deny finalized or deleted state.

Use a strict owner action such as
`POST /api/my-consultations/{consultation_id}/delete` with
`{ "expected_state": "open" | "finalized" }`. Under the consultation row lock:

1. Prove ownership without accepting any client owner identity.
2. Resolve exact author-deletion retries from persisted state/marker.
3. Reject a stale expected state so a deletion request that loses a race to finalization does not
   silently become a second post-finalization withdrawal; the author must reload and confirm the
   newly visible consequence.
4. For `open`: call RF-37's marker, delete all raw votes, create no result, sanitize disallowed
   content, set `state=deleted` plus `author_deleted_at`, and commit once.
5. For `finalized`: preserve lifecycle and only future DEC-023 outcome rows, enforce terminal
   sanitization/link revocation, set `author_deleted_at`, and commit once. Any legacy media remains
   inaccessible and is converged by RF-37 recovery; RF-13 does not invent finalized results.
6. Return success after the database commit. Startup/hourly/manual RF-37 maintenance performs and
   retries physical work independently; a storage failure is operational, never a product rollback.

The owner accepted this lifecycle, visibility, minimization, serialization and post-commit approach
through Q1A-Q5A on 2026-10-20, then accepted the exact API, UX, navigation, observability, migration,
validation and scope boundaries through Q6A-Q12A.

## Open material questions and proposed answers

### Resolved decision batch 1 - lifecycle, visibility, data and serialization

#### Q1 - How should deletion after finalization coexist with DEC-033?

**Confirmed 2026-10-20: A.**

- **A (recommended): preserve `state=finalized` and add an irreversible author-withdrawal marker.**
  Open deletion remains `state=deleted`; later deletion of a finalized consultation records
  `author_deleted_at` and hides/revokes the product object while preserving finalization and its
  DEC-023 outcomes. Consequence: queries gain one explicit visibility predicate and the migration
  adds one nullable marker. Risk: deletion has two persisted dimensions and must be named/documented
  carefully so future code never treats a withdrawn finalized row as author-visible.
- **B: allow `finalized -> deleted` and keep final outcomes in separate records.** The visible state
  model is simpler, but this changes the accepted terminal state machine, makes a second terminal
  transition legal, and requires revising DEC-033, lifecycle tests and every consumer assumption.
  Risk: the state no longer says whether finalization happened, so outcome presence becomes the only
  proof and stale writers are easier to mishandle.
- **C: reject deletion after finalization.** This preserves current code without a marker, but
  contradicts the ticket and the binding phase-2 requirement. Risk: knowingly incomplete feature.

**Accepted rationale:** it distinguishes “finalization won” from the later privacy/visibility action
and keeps first-terminal-commit-wins intact for operations competing while the row is open.

#### Q2 - What happens in My consultations after successful deletion?

**Confirmed 2026-10-20: A.**

- **A (recommended): remove the item immediately from both tabs and expose no deleted/tombstone
  tab.** The stable database row remains only for idempotency, referential integrity, RF-37 retry and
  permitted outcomes. Consequence: the UI is simple and matches current exclusion of
  `deleted/removed`. Risk: the author has no persistent in-product deletion receipt.
- **B: keep a minimal textual `Deleted consultation` row with ID/date and no content or photos.**
  This gives visible history, but adds a third list projection, retains a product-facing tombstone
  and creates pagination/access semantics not requested by RF-12 or RF-13. Risk: users may interpret
  the row as recoverable or expect detail/results.

**Accepted rationale:** show a transient success message after navigation rather than a durable
archive. There is explicitly no trash, recovery or photo archive.

#### Q3 - Which data survives each deletion path?

**Confirmed 2026-10-20: A.**

- **A (recommended): lifecycle-specific allowlists.** Open deletion removes every `Vote`, keeps no
  result, sanitizes question/context/audience/fingerprint/link capability, and retains only stable
  consultation/owner/state/timestamps, `author_deleted_at`, stable option IDs/order and RF-37
  pending/completed markers until/after verified media removal. Post-finalization withdrawal keeps
  only that operational minimum plus future DEC-023 declared option/no-selection, aggregate totals
  and per-participant private outcome; no raw text, image, link, storage or raw-choice data survives
  beyond its required retry window. Consequence: explicit service and database tests enforce both
  allowlists. Risk: future RF-19/RF-20 schema must be reviewed against the allowlist.
- **B: retain all non-image consultation and vote rows after deletion.** Easier initially, but
  exceeds DEC-023, retains user text/raw choices without purpose and makes open deletion resemble a
  hidden archive. Risk: privacy and specification violation.
- **C: physically delete the entire consultation row.** Minimizes data, but destroys durable retry
  references, operation identity, stable outcome relationships and RF-37 convergence evidence.
  Risk: lost-response retries and partial storage failures cannot be handled safely.

**Accepted rationale:** it is the narrowest data set compatible with retry, auditing by counts and
future private finalized outcomes.

#### Q4 - How should API retries, double clicks and terminal races be identified?

**Confirmed 2026-10-20: A.**

- **A (recommended): strict `expected_state` plus persisted natural operation identity.** The owner
  action submits `open` or `finalized`; the server locks the row. A matching first deletion commits,
  an exact repeat returns the same success, and a different current state returns conflict. If a
  simultaneous finalization commits first, the stale open-deletion request does not automatically
  withdraw the newly finalized result; the client reloads and asks for a new finalized warning.
  Consequence: no general idempotency table is needed. Risk: the client must preserve the state it
  confirmed and handle 409 by reloading.
- **B: accept whichever state exists after the lock and always delete it.** This makes the click
  likely to “succeed,” but a request confirmed with the open warning could delete a newly finalized
  consultation with different data consequences. Risk: violates first-terminal-wins and informed
  destructive confirmation.
- **C: require a general client-generated idempotency key and request ledger.** It can prove exact
  payload identity, but adds reusable infrastructure outside scope and still needs expected-state
  handling for a finalize/delete race. Risk: premature general queue/operation machinery.

**Accepted semantics:** first success and exact repeat both produce `204`; a
stale competing state is `409 consultation_conflict`; unknown, foreign or administratively removed
targets are the same generic `404 consultation_unavailable`.

#### Q5 - What is the post-commit contract when physical storage fails?

**Confirmed 2026-10-20: A.**

- **A (recommended): database success remains user success; durable cleanup owns convergence.** The
  endpoint returns after the revocation/deletion transaction commits. RF-37 startup/hourly/manual
  maintenance retries failed or partial file deletion and retains only sanitized retry metadata.
  Consequence: no “deleting” product state or client polling. Risk: physical absence is eventual, so
  operations must alert on overdue work; current RF-37 reporting supplies that control.
- **B: report failure until every file has been synchronously deleted.** This suggests the product
  action failed after access was already irreversibly revoked, encourages unsafe retries/rollback
  expectations and holds a request on fallible storage. Risk: misleading UX and timeout ambiguity.
- **C: return `202 Accepted` and expose a user-visible deletion-progress resource.** More explicit
  eventual status, but creates a tombstone/status API, polling UI and general job semantics outside
  the feature. Risk: implies recoverability or continued product access.

**Accepted rationale:** user-visible errors apply only before the database commit. Post-commit
storage errors are sanitized operational signals and must never reopen access.

### Resolved decision batch 2 - API boundary and product experience

#### Q6 - Which mutation route and authorization boundary should be used?

**Confirmed 2026-10-20: A.**

- **A (recommended): owner-management action
  `POST /api/my-consultations/{id}/delete` with a strict `expected_state` body.** Require the signed
  session, server-side ownership and trusted-origin protection; never accept owner ID or Private token
  as authority. Consequence: action naming matches existing POST action routes and avoids relying on
  DELETE request-body support. Risk: it is an action endpoint rather than pure REST deletion.
- **B: `DELETE /api/my-consultations/{id}` with expected state in a header.** More conventional verb,
  but introduces a custom precondition header and client/proxy handling. Risk: easy for future
  callers to omit or misunderstand the concurrency proof.
- **C: `DELETE /api/consultations/{id}` with no precondition.** Shortest API, but mixes public and
  owner-management authority and cannot distinguish stale open/finalized confirmations. Risk:
  authorization and race regressions.

**Accepted rationale:** a strict response has no deleted content or cleanup internals. Missing Origin
keeps the current non-browser behavior; hostile and `null` origins remain rejected.

#### Q7 - What confirmation experience is proportionate and accessible?

**Confirmed 2026-10-20: A.**

- **A (recommended): one accessible state-specific modal/alert dialog, no typed phrase.** The open
  warning says access ends immediately, photos are permanently scheduled for deletion, votes are
  discarded with no result, and the action cannot be undone. The finalized warning says the
  consultation disappears, photos stay unavailable, only minimum private photo-free participant
  outcomes may remain, and the action cannot be undone. Use `Cancel` and `Delete consultation`, put
  initial focus on the safe action, trap/restore focus, support Escape, expose labelled/described
  semantics, disable duplicate submission and fit narrow mobile viewports. Risk: dialog behavior
  requires focused keyboard/screen-reader tests.
- **B: require typing a phrase or consultation identifier.** Reduces accidental activation but is
  disproportionate for one object, burdens mobile/assistive input and exposes opaque IDs. Risk:
  abandonment without materially improving authorization.
- **C: use `window.confirm`.** Small implementation, but weak control over wording, focus,
  accessibility, loading/error states and mobile layout. Risk: inconsistent critical UX.

**Accepted rationale:** on pre-commit error the dialog stays usable with a concise alert and retry;
the underlying consultation remains visible and unchanged.

#### Q8 - Where does the author go after success, and how is list state reconciled?

**Confirmed 2026-10-20: A.**

- **A (recommended): return to My consultations on the originating state tab, remove the row only
  after server success, then refetch that tab.** From success/home/direct owner detail, navigate to My
  consultations and select the relevant tab. Announce `Consultation deleted` in a live region; do not
  leave a success page or broken detail. Consequence: server state remains authoritative while the
  UI feels immediate. Risk: pagination refresh must deduplicate and avoid resurrecting stale rows.
- **B: navigate Home after every deletion.** Simple destination, but disconnects the author from
  their management task and makes list coherence less visible. Risk: a stale My-consultations cache
  can show the row later until refresh.
- **C: keep the user on a permanent deleted-detail screen.** Provides a receipt but creates the
  tombstone product surface rejected by Q2A. Risk: users may expect undo or retained results.

**Accepted rationale:** a later direct-link refresh must still produce the generic unavailable
surface; browser history is not an access grant.

### Resolved decision batch 3 - observability, compatibility and release proof

#### Q9 - What deletion observability is allowed without retaining deleted content?

**Confirmed 2026-10-20: A.**

- **A (recommended): sanitized structured events and counters only.** Record action outcome,
  consultation ID, prior lifecycle, retry/conflict classification, counts of votes removed/images
  marked, and RF-37 pending/completed/failed/overdue counts; never log question/context, link tokens,
  storage keys, image data or individual vote choices. Consequence: incidents and overdue erasure
  are diagnosable. Risk: consultation IDs remain operational metadata and need ordinary restricted
  log access/retention.
- **B: log full request/database payloads for forensic debugging.** Easier debugging, but recreates
  deleted content and capabilities in logs. Risk: direct privacy and security violation.
- **C: emit no deletion-specific signal.** Maximum log minimization, but partial storage failure and
  unexpected conflicts become operationally invisible. Risk: RF-37 overdue guarantees cannot be
  supervised.

**Accepted rationale:** reuse RF-37's error taxonomy and alert age; do not create an analytics event
containing user content.

#### Q10 - How should existing rows and future finalized outcomes be migrated compatibly?

**Confirmed 2026-10-20: A.**

- **A (recommended): additive nullable marker with no synthetic backfill.** Existing open/finalized
  rows start visible (`author_deleted_at NULL`); existing `deleted/removed` rows remain excluded.
  The migration adds indexes/constraints needed for owner filtering and rejects unsafe downgrade once
  the new marker is used. RF-13 tests seeded finalized rows now; RF-19/RF-20 later adds outcome tables
  that the marker must not delete. Risk: a down migration cannot truthfully reconstruct prior
  author visibility after irreversible use.
- **B: infer/backfill markers for every current terminal row.** Makes data uniform, but cannot know
  whether historical fixtures represent author deletion, finalization or administrator removal.
  Risk: false product history.
- **C: wait to implement any finalized deletion support until RF-19/RF-20 exists.** Avoids forward
  compatibility work, but prevents RF-13 from satisfying an accepted criterion and defeats its
  position as RF-37's first consumer. Risk: partial feature presented as complete.

**Accepted rationale:** migration tests must cover upgrade from current head, preserved open and
finalized rows, new constraints/indexes and explicit downgrade refusal after irreversible use.

#### Q11 - What validation evidence is required before RF-13 can be called complete?

**Confirmed 2026-10-20: A.**

- **A (recommended): full layered matrix including real PostgreSQL, storage failure and restart.**
  Unit tests cover transition/idempotency/minimization; API tests cover owner/foreign/missing/removed,
  origin, strict payloads and codes; frontend tests cover both warnings, keyboard/focus/mobile states,
  duplicate activation, errors/navigation/list refresh; PostgreSQL tests race delete with vote,
  finalize and a second delete; RF-37 tests inject total/partial storage failure, repeat cleanup,
  restart and database-with-empty-volume recovery; migration and Docker build/startup evidence is
  included. Consequence: the first real RF-37 consumer proves the shared contract end to end. Risk:
  larger validation cost, especially concurrency and recovery fixtures.
- **B: unit/API/frontend happy paths only.** Faster, but cannot prove row-lock winner, durable retry,
  real constraints, startup convergence or non-resurrection. Risk: core acceptance criteria remain
  unsupported.

**Accepted rationale:** use isolated databases/volumes and bounded tests; do not operate on ordinary
project data. Manual mobile validation should verify narrow-dialog layout, focus/keyboard behavior
where available, loading/error recovery and coherent navigation.

#### Q12 - Which adjacent feature boundaries must remain explicit in the RF-13 plan?

**Confirmed 2026-10-20: A.**

- **A (recommended): keep RF-13 a narrow voluntary-author-deletion consumer.** It integrates RF-37,
  deletes open votes, records withdrawal and updates owner UI. It neither finalizes nor computes
  outcomes; RF-19/RF-20 own those. It preserves but does not display future RF-21 outcomes and does
  not implement RF-32 authority. Consequence: a small coherent vertical increment with forward seams.
  Risk: finalized deletion tests use the current minimal finalized fixture until outcome tables exist.
- **B: implement finalization/results/history/admin removal together so every terminal path is
  concrete.** Reduces future integration points but combines four tickets, makes substantial product
  choices implicitly and violates the mandated ordering. Risk: unreviewable scope and privacy errors.

**Accepted rationale:** the RF-13 plan may name future compatibility requirements but must not invent
RF-19/RF-20/RF-21/RF-32 behavior.

## Proposed scope

Subject to owner confirmation of the questions above:

- Owner-only irreversible deletion of open and finalized consultations.
- Atomic consultation-row serialization, strict expected-state validation and exact retries.
- Open-deletion state transition, vote removal without outcomes, link revocation, content
  sanitization and RF-37 media marker in one transaction.
- Post-finalization voluntary-withdrawal representation that preserves only future DEC-023 outcomes.
- Immediate exclusion from owner list/detail plus existing generic denial across feed, direct,
  Private-link, photo, vote and result reads.
- State-specific accessible confirmation, loading/error/double-activation handling, post-success
  navigation and authoritative list refresh.
- Additive migration, sanitized observability and the full validation matrix.

## Explicitly out of scope

- Finalizing a consultation or declaring one, several or no photographs.
- Implementing RF-19/RF-20 final selections, aggregate snapshots or final participant outcomes.
- Implementing RF-21's complete participation history.
- Restricted or broad administrator removal from RF-32.
- Account deletion.
- Recovery, trash, undo or reopening a deleted consultation.
- Any archive of deleted consultation photographs.
- New image copies, derivatives, thumbnails or versions.
- A general job/queue/idempotency platform.
- Public moderation, reports, abuse workflows or an administration console.
- Unrelated product changes.
- A promise to remove copies that third parties stored outside NextPost.

## Initial validation outline

### Domain and service

- Open deletion locks the consultation, proves owner and expected state, calls RF-37 before commit,
  deletes all votes, creates no result, sanitizes content and commits `deleted` plus the voluntary
  deletion marker atomically.
- Finalized withdrawal preserves lifecycle/future DEC-023 records, sanitizes all disallowed content,
  marks author withdrawal and does not synthesize/alter a final selection.
- Same-state exact retries are success with no duplicate side effects. Wrong expected state,
  `removed`, foreign and unknown rows have their approved safe outcomes.
- Inject a failure before commit and prove access/data remain unchanged. Inject storage failure after
  commit and prove every product read remains unavailable while retry metadata survives.

### API and security

- Authentication, server-side ownership and trusted-origin tests, including hostile and `null`
  Origin; no Private token or client owner ID grants deletion authority.
- Strict request shape and bounded UUID/state validation; safe 204/404/409 behavior and private
  no-store headers; no content, outcome, storage key or existence disclosure.
- After commit, owner detail/list, feed, direct entry, link management, photo bytes, vote state,
  vote submit and live-result reads all fail or omit the row from fresh server state.

### PostgreSQL concurrency and migration

- Real lock races: vote-before-delete, delete-before-vote, delete-before-finalize,
  finalize-before-stale-open-delete, two identical deletes and conflicting stale state. Assert one
  winner, one commit boundary and no late vote/result.
- Upgrade from current Alembic head preserves existing rows and starts them visible; constraints and
  indexes enforce the marker/state invariants. Downgrade behavior is explicit after irreversible use.

### Frontend and accessibility

- Both state-specific warning texts, Cancel, confirm, focus placement/trap/return, Escape,
  accessible name/description, live error/success announcements and narrow viewport layout.
- Confirm is disabled during submission; double activation calls once; pre-commit failure keeps the
  consultation and allows retry; 401 returns to authentication; 409 reloads state and requires a new
  confirmation; 404 uses the safe unavailable route.
- Success returns to the correct My-consultations tab, removes/refetches without stale resurrection,
  handles an emptied page and invalidates any retained detail/photo object URLs.

### Storage, Docker and recovery

- Whole consumed session is marked, all normalized objects and leftovers are eventually absent,
  partial/total delete failure retries idempotently, and no unrelated consultation object is touched.
- Startup and periodic cleanup converge after backend restart; advisory leadership prevents competing
  leaders; overdue failures remain visible without content.
- Docker images build, Alembic applies before serving, private volumes remain isolated, and the
  supported database-with-empty/current-photo-volume recovery never re-exposes deleted media.

No validation command, container, implementation harness or manual environment was run during this
grooming intake.

## Grooming checklist

- [x] Repository was clean and synchronized with `origin/main` before work.
- [x] Mandatory context, phase scope, reorganization, active groomings and relevant plans/reviews
  were read.
- [x] Trello card and related metadata were captured read-only.
- [x] Current code, migrations, authorization, UI, Docker and relevant tests were inspected.
- [x] Binding inherited decisions, dependencies, conflicts, proposed scope and exclusions are
  recorded.
- [x] Initial validation direction is recorded.
- [x] Product owner has answered Q1-Q5.
- [x] Product owner has answered Q6-Q12.
- [x] Durable new cross-feature decisions have been recorded in `03_DECISIONS.md`.
- [x] No material question remains.
- [x] Product owner has explicitly approved finalization of an implementation plan.
- [x] `harness/features/RF-13-Implementation-plan.md` exists and is ready for implementation.

