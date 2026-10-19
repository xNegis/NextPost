# RF-16 - Cast an independent vote - Grooming

## Status

`Finalized - implementation plan approved`

Explicitly selected by the product owner on 2026-10-15. This document records the
read-only Trello intake, repository findings, viable alternatives and confirmed choices.
On 2026-10-16 the owner answered `1A 2A`, confirming that an already-voted Public
consultation remains in normal Home chronology with a `Voted` marker and that the detail
identifies only that account's recorded photo as `Your vote`. DEC-038 records the durable
cross-feature behavior. No material question remains identified. The resulting settled
scope was explicitly approved by the owner on 2026-10-16 together with plan finalization
and harness launch. The approved contract is in
`harness/features/RF-16-Implementation-plan.md`.

## Trello snapshot

- Title: RF-16 · Emitir un voto independiente
- URL: https://trello.com/c/rzoUcPdL/17-rf-16-emitir-un-voto-independiente
- Stable short URL: https://trello.com/c/rzoUcPdL
- Card ARI: `ari:cloud:trello::card/workspace/6aa9032829f8b45ead46cfdd/6aa90bf2e8053b362460c2ee`
- Board: APP - NextPost; `ari:cloud:trello::board/workspace/6aa9032829f8b45ead46cfdd/6aa903892e7d7b54f23fae1b`; matches the configured NextPost board.
- Board URL: https://trello.com/b/CgBkRg78/app-nextpost
- List: Próximo · completar el MVP; `ari:cloud:trello::list/workspace/6aa9032829f8b45ead46cfdd/6aa903892e7d7b54f23fae23`
- Captured on: 2026-10-15; live reads completed before 17:46:18 UTC /
  19:46:18 Europe/Madrid. The connector supplies no exact read timestamp.
- Last activity at intake: `2026-10-12T11:26:39.379Z`.
- Archived: false; complete: false; due complete: false.
- Started at / due date: none.
- Labels / members / comments / checklists: none. All returned truncation flags are false.
- Attachments / custom field values: none; separate live reads have no next page.
- Available activity: card creation on 2026-09-15 and a move from `Funcionalidades` to the
  historical `Fase 2` list on 2026-09-22. The current card read is authoritative for the
  renamed `Próximo · completar el MVP` list and current description.
- Intake mismatch: none in identifier, title, board, current list or content. The card's
  historical email-verification exclusion is already superseded by DEC-011, as the card says.
- Read-only board/card inspection; no Trello mutation.

### Description and acceptance criteria at intake (verbatim)

**Reorganización del backlog · 2026-10-12**

El voto expresa qué foto elegiría el participante para el objetivo que plantea el autor. Una cuenta puede sobre todo votar, sobre todo consultar o hacer ambas cosas; no se exige reciprocidad. Se conserva el voto confirmado y definitivo. Comentarios opcionales se estudian por separado en RF-41, fuera del MVP inicial.

Ubicación: Próximo · completar el MVP. El repositorio es la fuente de estado y especificaciones aceptadas. Esta organización no aprueba un plan ni lanza implementación.

---

**Descripción conservada del ticket**

**Historia de usuario**
Como usuario registrado, quiero elegir una foto sin que me influyan resultados ajenos.

**Criterios de fase 2 acordados**
- Puedo comparar y ampliar las fotos de una consulta abierta a la que tengo acceso, elegir una, revisar mi selección y confirmar o cancelar antes de enviarla.
- Cada cuenta registra como máximo un voto definitivo por consulta. Reintentos, dobles clics y envíos concurrentes no lo duplican.
- El autor no vota en su propia consulta. No se exige verificar el correo en esta fase.
- Un voto que llega después de finalizar/eliminar/retirar se rechaza sin registrarse. El votante nunca ve los resultados agregados.

**Aplazado:** comentarios, variación del orden de fotos, bloqueo entre usuarios y verificación del correo. Referencia: DEC-011/019/020/021/022.

## Sources and verified baseline

Read AGENTS.md, all seven harness/context documents, the 2026-10-12 product/backlog
reorganization, RF-14 grooming/approved plan/independent review, the approved photo,
text, audience/access, publication, lifecycle and author-management contracts, relevant
phase-2 scope decisions and the current implementation. Historical missing-code statements
in older plans are not treated as current implementation evidence.

- RF-14 is closed by explicit owner decision as `Completed and validated`, while its seven
  independent-review finding groups remain known technical debt. Closure did not make the
  failed probes pass. RF-16 must distinguish necessary prerequisite repairs from unrelated debt.
- The current authenticated shell has Home, Create, My consultations and Profile. Home is
  the default and contains the RF-14 feed. Local React state, not a URL router, owns navigation.
- Home lists all open Public consultations, including the current author's, with protected
  first-photo previews. Own cards open owner detail; other cards open
  `ReaderConsultationDetail`. Private consultations never enter Home.
- `ReaderConsultationDetail` shows complete text and ordered protected photos and supports
  enlargement. It currently has no selection, review, confirmation, vote state or mutation.
  Its controller accepts no Private token and deliberately rejects a Private detail in the
  Home-only path. RF-26 still owns actual external Private-link entry and auth return.
- `consultation_access.py` already defines `AccessOperation.vote`, denies the owner and applies
  current account, lifecycle, audience and Private-link checks. It is pure policy only; no
  persistence or route currently consumes the vote operation.
- `consultation_service.py` reloads current consultation state for protected reads. Future
  terminal consumers are required by DEC-033 to lock the consultation row and re-read state;
  no real terminal writer exists yet.
- PostgreSQL currently stores accounts, upload sessions/images, consultations and ordered
  `ConsultationPhoto` options. There is no Vote, aggregate, declaration or participant-outcome
  model and no migration after `20260928_0004_consultations.py`.
- `ConsultationPhoto.id` is the stable published option identifier exposed by detail/photo
  APIs. Its `ordinal` fixes display order. `PhotoUploadImage` is the byte/deletion ledger.
- Protected detail/photo APIs authorize every request and never return results. Feed and detail
  client payloads are strict. Existing owner management remains a separate authority boundary.
- Existing PostgreSQL tests use real row-lock/concurrency patterns, but some RF-14 feed tests
  recreate ORM metadata rather than installing Alembic head; RF-16 migration and race evidence
  must use an isolated Alembic-upgraded PostgreSQL database.
- The worktree was clean at RF-16 intake. Preserve all later unrelated user changes.

## Intended outcome

A registered non-owner opens an accessible open consultation, compares and enlarges the
immutable ordered photos without seeing any aggregate signal, selects exactly one photo,
reviews that choice and either cancels or confirms. Confirmation records one final vote.
The same account cannot create a second vote through retries, double activation, another
tab or concurrent requests.

After a lost response, reload or later sign-in, the client asks the server for the current
account's vote state and presents only that account's recorded selection if one exists.
This recovery exposes no total, percentage, leader, trend or other person's choice. A vote
request reauthorizes current account/audience/link/lifecycle state in the same transaction
as persistence; a terminal consultation or revoked Private link cannot receive a late vote.

Public voting is reached from Home. The same backend and reusable reader/vote component must
support a currently authorized Private capability, but RF-16 adds no Private discovery,
external URL route, pending destination or post-authentication return. RF-26 later supplies
that entry journey and passes the validated current token into this contract.

## Current code findings and affected boundaries

### Backend and database

- Add a new Alembic revision rather than editing `20260928_0004`.
- Add a focused Vote model/service and thin API routes. The recommended row contains an opaque
  UUID, consultation ID, voter account ID, selected `ConsultationPhoto` ID and server timestamp.
- Enforce database uniqueness on `(consultation_id, voter_id)`. Add database-level referential
  integrity proving the selected option belongs to that same consultation, not merely two
  independent foreign keys. This requires an appropriate unique candidate key on
  `consultation_photos (consultation_id, id)` and a composite vote foreign key.
- Index `(consultation_id, consultation_photo_id)` for RF-18 aggregate counts without exposing
  voter identities. Do not persist a denormalized count, percentage or result in RF-16.
- Use restrictive foreign-key behavior so a future account/terminal workflow cannot silently
  erase a vote and leave aggregate/outcome data inconsistent. RF-13/RF-19/RF-20/RF-34 must
  transform/delete votes deliberately under their own accepted contracts.
- The migration is additive and needs no backfill: existing consultations begin with zero votes.
  A downgrade may remove the new schema only while it contains no votes; refuse a populated
  downgrade rather than silently destroy participation data. Database rollback cannot restore
  later-deleted image bytes and is not a terminal-operation rollback.

### Transaction and concurrency

Recommended order for both vote-state read and vote submission:

1. Authenticate from the signed cookie and parse bounded IDs/token without trusting client owner data.
2. Begin a transaction and lock the consultation row with PostgreSQL `FOR UPDATE` for submission.
3. Build the access snapshot from that locked current row and call `can_access` with
   `AccessOperation.vote`; this rejects owner, terminal state and missing/current-invalid Private access.
4. Check an existing vote for `(consultation, account)` under the same serialization boundary.
5. If none exists, verify the selected option belongs to the locked consultation and insert once.
6. Commit once and return only the current account's recorded option.

The consultation lock deliberately serializes submissions for one consultation in this POC.
That is simpler and compatible with DEC-033's future terminal lock, so a vote cannot commit on
the far side of finalization/deletion/removal. The unique constraint remains the database backstop.
Different-account throughput can be revisited only after measurement; avoiding this lock now would
require a more complex protocol to prove the late-vote invariant.

If a vote already exists with the same option, a retry returns that existing vote as success.
If a different option already won a concurrent race, the server reports `vote_already_recorded`
without changing it, and the client reads authoritative vote state. No client idempotency key,
server idempotency table, polling loop or background job is recommended: the natural operation
identity is the consultation/account unique key.

### API and privacy boundary

Recommended focused routes, exact naming still routine implementation detail:

- `GET /api/consultations/{id}/my-vote` returns exactly either
  `{status: "not_voted"}` or `{status: "voted", photo_id: <consultation-photo UUID>}`
  for a currently authorized non-owner.
- `POST /api/consultations/{id}/votes` accepts exactly `{photo_id: UUID}` and returns the
  current account's recorded vote. It uses trusted-origin protection for cookie-authenticated
  mutation. A first insert may be 201 and an exact replay 200; the client accepts both strictly.

Both routes require the current cookie plus current Private token where applicable. A previous
visit or vote is not a standing Private grant. Unknown, unauthorized, terminal, revoked-link and
self-vote cases use a non-enumerating unavailable result at the public boundary. Invalid request
shape is a safe 422; an authorized wrong option is a safe invalid-selection response. A recorded
different option is an explicit current-account conflict, not permission to edit.

Responses and protected failures must carry `Cache-Control: private, no-store`,
`Referrer-Policy: no-referrer` and `X-Content-Type-Options: nosniff`. Do not log choice payloads,
tokens, cookies, text, bytes or storage keys. No vote endpoint returns count, total, percentage,
leading photo, ranking, timestamp, voter identity or any result derived from other votes.

### Frontend and observable flow

- Extend the focused reader detail/controller rather than owner management or the uploader.
  It receives an optional validated Private token for RF-26 reuse; Home supplies none.
- Load current detail/photos and current-account vote status with separate request generations.
  Do not enable submission until vote status is known. A `voted` response installs only the
  current account's recorded option; `not_voted` enables selection.
- Keep photo order unchanged. Use an explicit single-choice group/control adjacent to each photo
  and a separate enlarge action so selecting and enlarging are not ambiguous. Selection can change
  any number of times before confirmation.
- `Review vote` opens an inline review step with the selected photo/number and finality warning.
  `Back to photos` changes the selection; `Cancel` sends no request and returns to comparison.
  `Confirm vote` is the only write, disabled while pending. No confirmation-on-photo-click.
- After confirmation, keep the comparison readable/enlargeable and replace mutation controls with
  a definitive own-vote state. No results or social proof appear.
- On network/5xx/lost response, perform one authoritative `my-vote` reconciliation. If a vote
  exists, show it as recorded. If none exists, preserve the local reviewed choice and permit
  explicit retry. If reconciliation also fails, say that the result is unknown and offer
  `Check vote status`; do not claim success or silently resubmit.
- On 401, clear detail, URLs, selection and vote state and use the existing sign-in transition.
  Ordinary later sign-in returns Home. On current denial/terminal state, clear protected content
  and show the generic unavailable state. Missing authorized photo bytes remain retryable.
- Back returns to a revalidated Home range using the selected RF-14 navigation contract. No
  explicit Skip, auto-advance, forced next consultation, reciprocity or browser persistence.

## RF-14 debt assessment

RF-14's owner-authorized closure keeps all seven finding groups as real debt. RF-16 should
not absorb them wholesale, but the following minimum repairs are necessary to make the vote
journey meet its own accepted behavior:

- **F1 blocks RF-16:** a late preview request can sign out a later account or replace newer
  content after entering detail. Add request generation/ownership so stale preview success,
  errors and 401s cannot affect the voting scope; preserve real in-flight accounting and URL cleanup.
- **F2 partly blocks RF-16:** hidden feed requests can complete during detail, and Back/Refresh
  currently do not provide the required coherent range/focus behavior. RF-16 explicitly requires
  coherent Home return and session handling, so invalidate feed scope on detail entry and separate
  one-page Refresh from bounded Back reconciliation with cursor progress and focus fallback.
- **F4 blocks RF-16:** keyboard containment/background isolation is explicitly required for
  photo enlargement while choosing. Correct the shared dialog and cover Escape, Tab/Shift+Tab,
  focus return and detail/account changes.
- **F7 blocks the protected voting path:** add consistent private headers to vote routes and the
  consumed detail/photo/auth/validation/error paths. This is a privacy requirement, not a claim
  that every unrelated endpoint has been redesigned.

The following may remain separately recorded RF-14 debt without preventing a safe RF-16 vote:

- **F3:** missing `IntersectionObserver` fallback affects feed-card preview loading, while the
  View action and full detail remain usable. Do not expand RF-16 solely to redesign preview fallback.
- **F5:** own Home detail lacks equivalent enlargement/loading Back, but the author is prohibited
  from voting and RF-16 adds no owner vote controls.
- **F6:** permissive feed cursor grammar affects discovery robustness, not vote authorization,
  referential integrity or duplicate prevention. Keep it visible; do not couple vote migration
  to a pagination-parser correction.

If the eventual implementation cannot isolate the four necessary repairs from broader RF-14
changes, it must stop and report the conflict rather than silently reopen all RF-14 scope.

## Viable alternatives and recommendation

### Persistence and idempotency

1. **Recommended: natural unique vote plus consultation row lock.** Smallest durable model,
   exact retry recovery, real PostgreSQL guarantees and direct compatibility with DEC-033/RF-18.
   Cost: submissions to one consultation serialize, acceptable for the POC.
2. Client idempotency keys plus an operation table. Useful for arbitrary repeatable commands but
   redundant when the product permits exactly one immutable vote per account/consultation; adds
   state, expiry and reconciliation complexity without improving the invariant.
3. Optimistic insert with only a unique constraint. Higher concurrency but complicates the race
   with future terminal operations and error recovery. Not recommended before measured load.

### Vote-state delivery

1. **Recommended: dedicated viewer-scoped `my-vote` read.** Keeps aggregate/result concerns out
   of general detail, supports explicit recovery and can be consumed by RF-26 with the same token.
2. Add viewer participation fields to every detail response. Saves one request but mixes a
   viewer-specific mutable projection into RF-10/RF-14's strict immutable detail contract and
   complicates owner/general reader variants.
3. Infer state only from POST conflicts/local memory. Fails reload/new-login recovery and cannot
   honestly resolve a lost response.

### Confirmation presentation

1. **Recommended: inline review state in reader detail.** Preserves context, mobile usability and
   Back/Cancel semantics without adding another modal/focus trap.
2. Confirmation dialog. Viable but duplicates the enlargement dialog's accessibility burden and
   makes comparison/change-selection behavior less clear.
3. Immediate submit on selection. Rejected by the accepted confirmation/cancel rule.

## Questions - one consolidated material batch

### Open

None. Q1A and Q2A were confirmed on 2026-10-16. The owner subsequently approved the
settled scope, plan finalization and harness launch on the same date.

### Historical batch and alternatives

#### Q1 - What should Home do with a Public consultation after this account has voted?

- **A (recommended): keep it in normal chronology and mark it `Voted`.** Opening it shows the
  immutable own-vote state and no voting action. This preserves RF-14's all-open-Public feed,
  makes recovery discoverable and avoids pretending the consultation no longer needs other votes.
  It adds a server-derived current-account `has_voted` boolean to feed items, never a count.
- **B: keep it in normal chronology without a card marker.** The recorded state appears only after
  opening detail. This keeps the feed payload smaller but makes repeat opening less predictable.
- **C: remove it from Home after voting.** Home focuses on not-yet-voted opportunities, but this
  changes the accepted feed semantics, requires a viewer-specific SQL exclusion and makes recovery
  depend on a future participation-history destination.

#### Q2 - What should the confirmed/already-voted detail reveal about this account's vote?

- **A (recommended): show the account's own recorded photo, highlighted as `Your vote`, plus
  `Votes cannot be changed`.** This is not an aggregate result or another person's choice and is
  the clearest honest recovery after a lost response, reload or new sign-in.
- **B: show only `Vote recorded` without identifying the chosen photo.** This minimizes the
  returned projection but cannot tell the user which of two concurrent selections actually won.

The recommendations intentionally reveal only the current account's own participation. Neither
choice authorizes totals, percentages, trends, leaders, winners or participant identities.

### Resolved / inherited

- 2026-10-16: the owner answered `1A 2A`. An already-voted Public consultation remains
  in its normal chronological Home position and is marked `Voted`. Opening it shows the
  current account's recorded photo highlighted as `Your vote` plus definitive copy that
  votes cannot be changed. These are current-account participation signals only; they do
  not expose aggregate or other-voter information. DEC-038 records this behavior.
- Registration is sufficient; no email-verification check or schema is added (DEC-011).
- Author cannot vote; current account/access/lifecycle/link authorization is server-side.
- One confirmed vote is immutable; selection changes remain local before confirmation only.
- Public and current-link Private use the same vote contract. RF-26 still owns Private entry/auth return.
- Vote order is immutable publication order. No randomization, Skip, comments or reciprocity.
- Results remain entirely absent from voter APIs/UI; RF-18 owns author-only aggregates.
- Publication remains immutable and open indefinitely until a real terminal action.
- Owner visual validation remains DEC-034; no Codex/harness visual inspection unless requested.

## Proposed scope

### In scope

- Additive Vote persistence/migration with database uniqueness, same-consultation option FK,
  aggregate-supporting index and safe empty-table rollback/refusal when populated.
- Current viewer vote-status read and one final vote submission with exact-retry recovery.
- PostgreSQL consultation locking, access recheck, unique backstop and real concurrent tests.
- Public Home reader integration and reusable optional Private-token integration for RF-26.
- Single selection, changing before review, inline review, cancel, confirm and final own-vote state.
- Ambiguous-response reconciliation, already-voted recovery, reload/new-sign-in behavior.
- Current-state denial, session loss, stale content, missing media and generic unavailable handling.
- Necessary RF-14 F1/F2/F4/F7 prerequisite repairs only, as bounded above.
- Strict response guards, private headers, accessible radio/review/enlargement/focus behavior.
- Documentation and evidence without implementation overclaim.

### Out of scope

- Aggregate counts, percentages, leading/winning photo or any result for voters; author results RF-18.
- Vote editing, withdrawal, invalidation, moderation or account-abuse/rate-limit systems.
- Comments/explanations (RF-41), variable order, Skip, reciprocity, reputation or coincidence score.
- Feed ranking/filtering beyond the Q1 decision, search, public profiles or notifications.
- Private-link route/auth return/share journey (RF-26), new router or native deep-link work.
- Finalization/declaration, author deletion, administrator removal, participant history or
  published-photo purge (RF-19/20, RF-13, restricted RF-32, RF-21, RF-37).
- Automatic expiry, editable publication, new worker/queue, analytics events or deployment rollout.
- Unrelated RF-14 F3/F5/F6 corrections and independent pending device/review gates.

## Dependency and future-ticket impact

| Ticket | RF-16 impact / boundary |
| --- | --- |
| RF-14 | Reuses Home/reader/photo flow. Includes only F1/F2/F4/F7 repairs necessary for safe voting; F3/F5/F6 remain known debt. |
| RF-18 | Can aggregate Vote rows by consultation option, including zero-option joins and ties, without exposing voter IDs. RF-16 stores no denormalized result. |
| RF-19/RF-20 | Must take the same consultation lock, snapshot valid votes, create aggregate/participant outcomes and terminal state atomically, then remove or transform unnecessary per-voter photo-choice records under DEC-023. |
| RF-21 | Later consumes participant outcomes after finalization. While open, RF-16's `my-vote` is the only current-account recovery and exposes no aggregates. |
| RF-26 | Supplies the actual Private destination and authentication return, then passes the validated current token to the same detail/status/submit clients. RF-16 adds no route or pending redirect. |
| RF-37 | Physical photo deletion remains separate. Terminal revocation wins the shared consultation lock; vote FKs must not cause file deletion or preserve accessible bytes. |
| RF-13 / restricted RF-32 | Open deletion/removal must lock first, revoke state and deliberately discard votes with no outcome; RF-16 supplies no terminal shortcut. |
| RF-34 | Future account deletion must deliberately remove/anonymize account-linked votes and recalculate affected aggregates; restrictive FKs prevent silent loss. |

## Validation outline

### Backend and migration

- Fresh Alembic upgrade and populated `0004 -> new head` preserve accounts, consultations,
  photos, links and existing data; new table starts empty. Empty downgrade/upgrade passes;
  populated downgrade refuses without data loss.
- ORM and migration constraints agree. Direct SQL cannot insert two votes for one
  consultation/account or select an option from another consultation.
- API/service matrix: anonymous/stale session, owner, Public other account, Private current/
  missing/wrong/disabled/replaced token, every lifecycle, unknown consultation/photo,
  malformed UUID/body/extra field and exact safe payload/headers.
- Real PostgreSQL races: same account/same option; same account/different options; many accounts;
  double click; delayed response/retry; vote versus seeded terminal writer using the shared
  `FOR UPDATE` protocol. Exactly one vote or the terminal transition wins, never both in the
  forbidden order and never a partial/duplicate row.
- Prove service rollback on injected failures and no storage access for unauthorized or invalid
  cross-consultation option requests. Vote submission performs no image/file mutation.

### Frontend and integration

- Strict vote/status guards reject extra/missing/wrong IDs/statuses and never install malformed data.
- Selection is exactly one, can change before review, and sends nothing on Back/Cancel.
  Confirm disables duplicates; exact retry and different-winner conflict reconcile accurately.
- Loading vote state, pending submit, success, known no-vote failure, ambiguous outcome,
  reconciliation failure, 401, generic denial, terminal change and missing media are distinct.
- Reload/new sign-in recovers from the server. Own cards never show voting. Public cards use no
  token; reusable Private tests prove the current token is attached to detail/photo/status/submit.
- No response/UI contains total, percentage, leader, trend, winner, other voter or fake activity.
- Keyboard/focus: photo choice group, review action, Back/Cancel/Confirm, enlargement Escape/
  containment/return and focus after errors/navigation. Long text, RTL, 320px, safe areas and
  200% zoom get automated layout/accessibility coverage; owner performs visual acceptance.
- RF-14 regression probes for F1/F2/F4/F7 become permanent passing tests; F3/F5/F6 remain visibly
  excluded. Existing feed, owner detail, My consultations, publication, links, auth and composer pass.
- Full backend/frontend formatting, lint, strict types, tests, production build, dependency audit,
  Compose configuration/build and isolated built two-account PostgreSQL smoke. The smoke publishes
  Public and Private, casts/retries one vote, verifies self/duplicate/late denial, restart/relogin
  recovery and zero aggregate/result exposure. Private UI entry remains an RF-26 gate.

## Readiness checklist

- [x] Current selected card consumed and readable snapshot preserved without Trello mutation.
- [x] Existing implementation, RF-14 debt and relevant approved contracts inspected.
- [x] Dependencies, conflicts and future consumer boundaries identified.
- [x] Viable persistence/idempotency/status/confirmation alternatives compared.
- [x] Routine transaction, API, migration, error, security and validation direction proposed.
- [x] Q1 Home behavior for already-voted Public consultations confirmed.
- [x] Q2 own recorded-choice visibility confirmed.
- [x] Resulting UX and exact scope/exclusions contain no remaining material ambiguity.
- [x] No material question remains.
- [x] Product owner explicitly approved finalizing a self-contained English plan.

No implementation, test run, service mutation, visual inspection, commit, push, deployment or
Trello mutation occurred during grooming. The implementation plan was finalized and the owner
separately authorized the coordinator to launch the harness on 2026-10-16.
