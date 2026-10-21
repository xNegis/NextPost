# RF-19 - Finalize a consultation - Grooming

## Status

`Material grooming complete - coordinated implementation plan ready`

On 2026-10-20 the product owner confirmed every recommended option (`Q1A` through `Q14A`) and
explicitly authorized plan finalisation and harness launch. The accepted contract is
`harness/features/RF-19-RF-20-Implementation-plan.md`.

Coordinated grooming with RF-20. RF-19 and RF-20 keep independent ticket traceability, but the
product operation, transaction, implementation and validation must remain inseparable. This file is
the canonical shared analysis and question register; `RF-20-grooming.md` mirrors the intake and
links every decision to the same question identifiers.

## Trello snapshot

- Title: `RF-19 · Finalizar una consulta`
- URL: https://trello.com/c/cPkS0GiV/20-rf-19-finalizar-una-consulta
- Board: `APP - NextPost`
- List: `Próximo · completar el MVP`
- Card state: open; not marked complete
- Labels: none
- Members: none
- Due date/start date: none
- Checklists, comments and attachments: none at intake
- Card ARI: `ari:cloud:trello::card/workspace/6aa9032829f8b45ead46cfdd/6aa90bf7090fe14d89635f94`
- Position: `131072`
- Captured on: 2026-10-20
- Last Trello activity at intake: `2026-10-12T11:29:03.529Z`

### Description and acceptance criteria at intake (verbatim)

> **Reorganización del backlog · 2026-10-12**
>
> El autor decide cuándo ha recibido suficiente ayuda y finaliza con su elección. Debe groomarse
> junto a RF-20 como una sola operación observable y coordinarse con RF-37; no son dos
> pantallas/acciones independientes ni se autoriza implementación conjunta sin planes aprobados.
>
> Ubicación: Próximo · completar el MVP. El repositorio es la fuente de estado y especificaciones
> aceptadas. Esta organización no aprueba un plan ni lanza implementación.
>
> ---
>
> **Descripción conservada del ticket**
>
> **Historia de usuario**
> Como autor, quiero finalizar una consulta cuando ya he recibido suficiente ayuda.
>
> **Criterios de fase 2 acordados**
> - Para finalizar una consulta abierta debo declarar una foto, varias fotos o ninguna y confirmar
>   esa decisión.
> - La declaración y el cierre son una sola operación; no existe cierre separado ni una elección
>   posterior. No se reabre en esta fase.
> - Finalizar detiene votos y acceso ajeno, retira las fotos para todos e inicia su borrado sin
>   buffer de 30 días.
> - Los votos válidos ya confirmados se convierten en resultados privados mínimos; si declaro
>   ninguna, no se asigna coincidencia ni desacierto.
>
> Referencia: DEC-017/021/023.

## Intended outcome

Let the authenticated author deliberately end an open consultation by declaring one, several or no
photo in one accessible confirmation and one database transaction. The winning commit freezes the
valid votes, creates the permitted photo-free final result and per-participant private outcomes,
revokes every content/link/photo read, sanitizes forbidden content, and schedules RF-37 durable
physical erasure. The operation is irreversible and never claims that the author's declaration is
objectively correct or that a photo was published elsewhere.

## Binding inherited decisions

- Only the author may finalize; there is no automatic expiry or vote threshold (DEC-017/035).
- Declaration and finalization are one operation. The author may select one, several or none and
  may disagree with the majority. None yields `No choice`, not a mismatch (DEC-021/023).
- Publication options are immutable. Existing votes are final. Participants never see aggregates
  through this increment (DEC-018/019/039).
- `open`, `finalized`, `deleted` and `removed` are the canonical stored lifecycles. The first
  terminal transaction holding the consultation row lock and committing wins; there is no priority
  among finalization, open author deletion and restricted administrator removal (DEC-033).
- The terminal commit immediately revokes new votes, protected detail, media and Private links.
  Physical filesystem work happens afterwards through RF-37 and cannot reopen access (DEC-041).
- No image, derivative, source metadata, question/context, active audience/link capability,
  publication fingerprint, upload ledger or raw per-voter photo choice may survive convergence.
  DEC-023 minimum non-visual records may survive.
- RF-19/RF-20 own finalization, declaration, definitive aggregates and the private outcome rows.
  RF-21 owns the participant history screen. RF-13 owns voluntary deletion/withdrawal and RF-32
  will own restricted administrator removal.

## Current code findings

### Lifecycle, votes and serialization

- `backend/app/consultation_lifecycle.py` is the canonical lifecycle policy. It deliberately has no
  terminal side effects and requires a consumer to prove exact retry identity after `same_target`.
- `backend/app/vote_service.py::submit_vote` locks the `Consultation` row with PostgreSQL
  `FOR UPDATE`, re-authorizes the latest state and then inserts one immutable `Vote`. A finalizer
  using the same lock will include every vote committed first and reject every vote arriving after
  finalization commits.
- `Vote` has a unique consultation/voter key and a composite foreign key proving that its selected
  `ConsultationPhoto` belongs to the same consultation. Raw votes currently retain voter and option.
- RF-18 computes open results live from raw `Vote` rows. It has no definitive snapshot and exposes
  counts only, including zeroes and ties, to the author.

### Stable options and media erasure

- `ConsultationPhoto.id` and `ordinal` already provide stable, non-visual option identity/order.
  After verified erasure RF-37 detaches `image_id`, sets `media_deleted_at` and retains the option.
- `mark_media_for_erasure` is transaction-local: it requires the locked open consultation, disables
  the Private capability and marks every image in the unique consumed source session revoked. It
  performs no commit and no filesystem I/O.
- `sanitize_terminal_content` nulls question, context, audience and publication fingerprint and
  resets Private-link state. It is explicitly intended to run only after the consumer has written
  permitted replacement outcome data.
- Startup/hourly/manual maintenance deletes exact keys, verifies absence, retries failures, removes
  image/upload metadata after success and never changes the terminal product outcome.

### RF-13 interaction

- `consultation_deletion_service.py` is the first terminal consumer. Open deletion uses the shared
  row lock, removes raw votes without outcomes, marks media, sanitizes and commits `deleted` plus
  `author_deleted_at` once.
- A later deletion of a finalized consultation preserves `state=finalized`, writes
  `author_deleted_at`, removes any residual raw votes and deliberately preserves future DEC-023
  records. RF-19/RF-20 must therefore leave finalized data compatible with this path.
- The API uses `POST /api/my-consultations/{id}/delete`, strict `expected_state`, signed-session
  ownership and trusted-Origin protection. Unknown/foreign/removed targets are generic unavailable;
  stale expected state is conflict.

### Owner UI, navigation and reads

- `OwnerConsultationDetail.tsx` already displays ordered open photos, live counts, share/link controls
  and deletion. It is the natural place for finalization; no fake Finalize action exists today.
- `MyConsultations.tsx` has separate Open and Finalized tabs, five-second non-overlapping refresh of
  the open list, authoritative refresh, notices and accessible tab keyboard behavior.
- Current finalized rows/details intentionally show only identifier, `Finalized` and publication
  date, with no photo or broken thumbnail. The schemas have no final counts, declaration or
  finalization date yet.
- Direct/protected recipient surfaces authorize every current read and collapse terminal/missing/
  unauthorized cases to generic unavailability. Photo responses are private/no-store and client
  object URLs are released when the photo-bearing view unmounts. Bytes already delivered to a
  recipient device cannot be remotely recalled.

### Missing production contracts

- No finalization service or route exists.
- No declaration/finalization record, definitive option-count snapshot or participant outcome table
  exists in the model or migration chain (current head `20261020_0007`).
- No participant-history screen exists; that remains RF-21.
- Account deletion does not exist. Current account references are restrictive; RF-34 must later
  define deletion/anonymization without causing finalization to retain prohibited account links.
- Restricted administrator removal is not implemented. RF-32 must later consume the same erasure
  and retained-outcome boundaries.

## Dependencies and conflicts

- RF-11 supplies state/locking semantics; RF-16 supplies immutable votes and the shared lock;
  RF-18 supplies current counts but not a snapshot; RF-37 supplies revocation/erasure/minimization;
  RF-12 supplies owner navigation; RF-13 already consumes finalized rows after this feature.
- RF-21 depends on outcome rows created here but must not be absorbed into this UI.
- RF-26 links and every protected read must become unusable at the finalization commit.
- A finalization service must write replacement data before deleting raw votes or sanitizing. Doing
  this in separate commits would violate DEC-023 and create recoverability/privacy gaps.
- Existing/seeded `finalized` rows predate this contract and may have no snapshot. Migration must not
  invent choices or outcomes for them.

## Candidate approach (unaccepted recommendation)

1. Add an additive migration with a one-to-one finalization record, declared-selection relation,
   definitive per-option count rows and one minimal participant-outcome row per valid voter.
2. Accept a strict tagged declaration plus client-generated operation UUID and `expected_state=open`.
3. In one locked transaction: authorize author; verify open/expected state; validate the complete
   declaration against stable options; aggregate votes; write finalization, selections, every option
   count and participant outcomes; verify invariants; delete raw votes; call RF-37 marking; sanitize;
   set `finalized`; commit once.
4. Treat the commit as product success. Let RF-37 maintenance perform fallible physical deletion.
5. Add one accessible finalization dialog to open owner detail. On success switch to the Finalized
   tab/detail, refresh author state and render a photo-free final summary.

## Open material questions and proposed answers

The product owner confirmed every `A` option below on 2026-10-20. They are accepted decisions and
are incorporated into the coordinated implementation plan.

### Q1 - Declaration contract and selection interaction

- **A (recommended):** required tagged payload: `declaration.kind=selected` with 1..N unique stable
  option IDs, or `declaration.kind=none` with no IDs. UI uses multi-select photo checkboxes plus an
  explicit mutually exclusive `Choose none` control and a review summary.
- **B:** required `selected_photo_ids` array where an empty array means none.
- **C:** single-choice only.

A makes none explicit and prevents omitted/empty ambiguity. B is smaller but easier to produce by
mistake. C contradicts accepted multi-selection.

### Q2 - Durable representation of declaration and snapshot

- **A (recommended):** normalized finalization header + declared-option join + one immutable count
  row for every stable option + denominator on the header.
- **B:** add nullable final count/declared flags directly to `ConsultationPhoto` plus a header.
- **C:** store arrays/JSON on `Consultation`.

A gives database constraints, clean RF-21/RF-13 consumption and explicit zero-vote options. B is
smaller but mixes mutable visual ledger and immutable outcome. C is compact but weakens integrity.

### Q3 - Meaning and membership of private outcomes

- **A (recommended):** create one outcome only for each committed valid voter: `Matched` when its
  option is declared, `Not matched` otherwise, and `No choice` for every voter when none is declared.
  Non-voters get no row; ties, zero votes and majority disagreement do not alter the rule.
- **B:** also create participant rows for eligible accounts that did not vote.
- **C:** treat none as `Not matched`.

A is DEC-023's literal minimum. B invents participation and greatly increases personal data. C is
already forbidden.

### Q4 - Raw-vote disposal and inconsistent legacy data

- **A (recommended):** after snapshot/outcomes pass invariant checks, delete all raw votes in the
  same transaction. If any vote cannot be mapped exactly to a stable option/account or counts do not
  reconcile, roll back and leave the consultation open for restricted repair.
- **B:** keep raw votes after finalization as a fallback.
- **C:** silently skip anomalous votes and finalize with the remainder.

A enforces minimization without fabricating or losing an unexplained result. B violates DEC-023.
C makes the final snapshot silently false.

### Q5 - Exact surviving product data and date

- **A (recommended):** retain consultation/owner ID, `finalized`, publication and finalization dates,
  author-deletion marker if later used, stable option ID/order/media-deleted marker, declaration,
  per-option counts, total denominator, participant account/outcome and RF-37 pending metadata only.
  Sanitize all free text, audience/link/fingerprint/storage/upload data at commit/convergence.
- **B:** omit a dedicated `finalized_at` and keep only publication date.
- **C:** retain question/context for author history.

A makes the outcome date honest and useful to RF-21/operations while staying inside DEC-023.
B loses the event date. C conflicts with the accepted allowlist.

### Q6 - Transaction order and success boundary

- **A (recommended):** lock and authorize -> validate declaration -> snapshot/count -> create private
  outcomes -> verify invariants -> delete raw votes -> mark RF-37 -> sanitize -> set finalized -> one
  commit. Commit is user-visible success; filesystem deletion is asynchronous/retryable afterwards.
- **B:** commit finalized first, then create results.
- **C:** physically delete files before database commit.

Only A avoids a closed consultation without outcomes and avoids irreversible file loss before a
rollbackable database operation.

### Q7 - Retry identity and idempotency

- **A (recommended):** request contains client-generated UUID `operation_id`, required
  `expected_state=open` and the tagged declaration. Persist operation ID plus a canonical payload
  fingerprint. Exact same ID+payload replays success; same ID/different payload or a new ID after a
  terminal commit is `409 conflict`.
- **B:** use only equality of the declared option set as retry proof.
- **C:** use a generic idempotency-key/request-ledger system.

A narrowly proves ambiguous network retries and follows RF-11 without new general infrastructure.
B cannot distinguish a deliberate second action from a retry. C is premature infrastructure.

### Q8 - Concurrent and stale actions

- **A (recommended):** use the shared consultation lock and first-commit-wins. Vote first is included;
  finalization first rejects the vote. Finalization versus open deletion/removal: winner commits;
  loser does nothing. If finalization beats an open deletion confirmation, deletion returns conflict
  and requires reload plus the distinct finalized-deletion warning. No expected aggregate count is
  required because votes may arrive until commit.
- **B:** give finalization priority.
- **C:** freeze voting while the dialog is open or reject if displayed counts changed.

A matches DEC-033 and avoids a client-held pseudo-lock. B is forbidden. C creates needless conflict
and cannot be enforced safely by a browser dialog.

### Q9 - Owner API and safe error semantics

- **A (recommended):** `POST /api/my-consultations/{id}/finalize`, signed-session owner only,
  trusted-Origin protected, strict extra-forbid schema. Unknown/foreign/removed/author-deleted is
  generic `404 consultation_unavailable`; stale/different terminal operation is `409`; semantic
  option errors on an authorized open consultation are `422`; pre-commit database failure is a
  retryable 5xx with no state change. Return the minimal finalized summary on first success/replay.
- **B:** generic transition endpoint accepting a target state.
- **C:** client sends owner ID or Private link as authority.

A is the narrow analogue of RF-13. B risks partial/generic state mutation. C violates authorization.

### Q10 - Entry point, confirmation and recovery UX

- **A (recommended):** Finalize appears only in open owner detail beside the real photos/counts.
  One accessible modal supports selection and review, states irreversibility/photo removal/vote cutoff,
  summarizes one/several/none, protects double click and retains choices after pre-commit errors.
  Ambiguous network failure retries the same operation ID or checks authoritative owner detail. A
  conflict closes/reloads safely; success navigates to the Finalized tab/detail with a live-region
  notice. Delete remains a separate action.
- **B:** offer Finalize directly on every Open list row.
- **C:** use two screens/actions: finalize first, declaration later.

A ensures the author sees the actual comparison and produces one confirmation. B lacks enough
context. C is forbidden.

### Q11 - Photo-free finalized presentation

- **A (recommended):** Finalized list row shows Finalized, published/finalized dates, total votes and
  `Selected Photo N[, ...]` or `No choice`. Detail shows the same plus every stable `Photo N` final
  count and selected marker, no thumbnail, question, context, audience or percentages; it retains
  the existing finalized Delete action.
- **B:** keep today's identifier/date-only tombstone.
- **C:** retain thumbnails or text so the result is recognizable.

A makes RF-19/RF-20's definitive aggregates observable to the author without visual retention and
keeps count-only RF-18 scope. B hides the implemented result. C violates minimization.

### Q12 - Legacy finalized rows and account lifecycle compatibility

- **A (recommended):** additive migration never fabricates old outcomes. A legacy finalized row
  without a finalization record remains a minimal `Final result unavailable` summary and can still be
  author-deleted. New finalized writes must have the full atomic record. Participant outcome uses an
  account FK designed to be removed/anonymized by future RF-34; no account-deletion behavior or
  historical backfill is implemented here.
- **B:** block deployment until every historical finalized row is manually resolved.
- **C:** backfill legacy rows as zero-vote `No choice`.

A is compatible and honest. B is operationally brittle. C invents product history.

### Q13 - Revocation, caches and post-commit storage failure

- **A (recommended):** rely on current request-time authorization and private/no-store headers;
  unmount the photo-bearing UI and revoke client object URLs immediately after success. Accept that
  bytes delivered before commit may finish/cannot be remotely recalled. RF-37 retries storage failure
  without changing success or exposing progress; owner sees no cleanup status.
- **B:** delay success until all files are physically absent.
- **C:** add a 30-day buffer or author-only photo access.

A matches DEC-041. B couples user success to fallible storage and risks timeouts. C is forbidden.

### Q14 - Observability, proof matrix and plan shape

- **A (recommended):** sanitized events contain consultation ID, first/replay/conflict/error,
  aggregate totals, selected-option count, outcome category counts and images marked—never text,
  tokens, storage keys, option IDs, photos or individual voter choices. Require unit/API/frontend,
  migration, real-PostgreSQL vote/finalize/delete/removal races, storage fault/retry, Docker,
  restart/recovery and accessibility evidence. Produce one coordinated self-contained
  `RF-19-RF-20-Implementation-plan.md` sourcing both tickets.
- **B:** same proof but two duplicated plans declared mutually dependent.
- **C:** separate implementation increments or lighter in-memory-only tests.

A minimizes contract drift because no valid RF-19 implementation can exist without RF-20 and vice
versa, while both ticket URLs and acceptance criteria remain explicit. B preserves filename
convention but creates circular/duplicated authority. C violates the observable-operation decision.

## Proposed scope

### In scope

- One author-only atomic finalization/declaration operation and accessible confirmation.
- One/several/none declaration, definitive counts/denominator and minimal voter outcomes.
- Raw-vote replacement, immediate logical revocation, terminal sanitization and RF-37 scheduling.
- Idempotent retry, expected-state handling and real concurrency with vote/delete/removal.
- Photo-free author list/detail result and authoritative navigation/refresh.
- Additive migration, legacy compatibility, sanitized observability and full validation matrix.

### Out of scope

- Automatic/time-based finalization, vote threshold, reopening or editing a finalized declaration.
- Separate finalization/declaration actions, vote changes, explanations/comments or notifications.
- Participant aggregate results or the RF-21 history screen.
- Reputation, ranking, expertise metrics, social publication or public results.
- Public moderation/reporting/admin UI or implementation of RF-32 authority.
- Visual archive, trash, restore, thumbnails, deletion buffer or model/analytics image retention.
- Account deletion implementation, broad router migration, native project generation or deployment.

## Initial validation outline

- Domain/service invariants for selected/multiple/none, zero votes, ties, majority disagreement,
  count/outcome reconciliation, duplicate IDs, foreign IDs and anomalous legacy votes.
- API ownership, Origin, strict schema, safe unknown/foreign/terminal errors, exact replay, payload
  conflict, database rollback and no data leakage.
- PostgreSQL races: vote/finalize both orders; two different finalizations; open delete/finalize;
  seeded removal/finalize; retry during/after commit; maintenance concurrent with finalization.
- Migration upgrade with open/voted/legacy-terminal data and downgrade refusal after irreversible use.
- Frontend selection, explicit none, review/cancel, focus trap/restore, Escape, keyboard, screen reader,
  mobile/zoom/safe-area CSS, duplicate click, retry/unknown/conflict/session loss and navigation.
- RF-37 total/partial storage failure, restart/hourly/manual convergence, verified absence, Docker
  private-volume restart and supported PostgreSQL-plus-empty/current-volume recovery.
- Regression for open results polling, voting, direct/private links, generic terminal denial,
  finalized author deletion and all existing suites/build/lint/type checks.

## Readiness checklist

- [x] Desired coordinated outcome is identified.
- [x] Scope and exclusions are confirmed.
- [x] Code impact was inspected.
- [x] Dependencies and conflicts are resolved.
- [x] Technical/data approach is selected.
- [x] UX and failure states are confirmed.
- [x] Security, privacy and retention choices are confirmed.
- [x] Migration and operational choices are confirmed.
- [x] Validation expectations are agreed.
- [x] No material question remains.
- [x] Product owner explicitly approved plan finalisation.
