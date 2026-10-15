# RF-12 - Gestionar mis consultas - Grooming

## Status

`Ready for implementation`

Explicitly selected by the product owner on 2026-10-12. These grooming notes preserve
analysis and alternatives; the approved implementation authority is now
`harness/features/RF-12-Implementation-plan.md`, marked `Ready for implementation`.
No harness launch is authorized. Preserve all pre-existing tracked and untracked work.

On 2026-10-12 the owner answered `a` to Q1, accepting My consultations as a fourth
primary destination. After the explicit scope/finalization approval question, the owner
replied "Vamos al lio" on 2026-10-12, approving the proposed increment and plan finalization.
No material question remains. Harness launch requires a subsequent explicit request.

## Trello snapshot

- Title: RF-12 · Gestionar mis consultas
- URL: https://trello.com/c/L2mZ6OFf/14-rf-12-gestionar-mis-consultas
- Stable short URL: https://trello.com/c/L2mZ6OFf
- Card ARI: `ari:cloud:trello::card/workspace/6aa9032829f8b45ead46cfdd/6aa90bec90fb1cfc9068a8f1`
- Board: APP - NextPost; `ari:cloud:trello::board/workspace/6aa9032829f8b45ead46cfdd/6aa903892e7d7b54f23fae1b` (matches configured NextPost board)
- List: Próximo · completar el MVP; `ari:cloud:trello::list/workspace/6aa9032829f8b45ead46cfdd/6aa903892e7d7b54f23fae23`
- Captured on: 2026-10-12, successful current-card read before 12:02:21 UTC
  (14:02:21 Europe/Madrid). The connector supplies no exact read timestamp.
- Last Trello activity: `2026-10-12T11:26:33.597Z`
- Position: 16384
- Archived: false; complete: false; due complete: false
- Started at / due date: none
- Labels / members / checklists / comments: none; returned truncation flags are false.
- Attachments / custom field values: none; separate live reads report no next page.
- Intake mismatch: none. RF identifier, title, board and current list agree.
- Initial reads were rate-limited (429); a subsequent authenticated read succeeded.
  This snapshot comes from that successful current read, not the reorganization JSON.
- Trello was read only.

### Description and acceptance criteria at intake (verbatim)

**Reorganización del backlog · 2026-10-12**

Primera propuesta de siguiente ticket a seleccionar para grooming: permitir volver a encontrar una consulta después de salir de Create. Lista/gestión de consultas propias no existe aún. Votos, resultados y acciones terminales deben integrarse solo cuando sus contratos estén disponibles; no se aprueba un plan con esta ordenación.

Ubicación: Próximo · completar el MVP. El repositorio es la fuente de estado y especificaciones aceptadas. Esta organización no aprueba un plan ni lanza implementación.

---

**Descripción conservada del ticket**

**Historia de usuario**
Como autor, quiero encontrar mis consultas abiertas y finalizadas para gestionar mis decisiones.

**Criterios de fase 2 acordados**
- Mi sección privada muestra consultas abiertas y finalizadas, con fecha, estado y número de votos; no muestra vencimientos porque no hay caducidad.
- Desde una consulta abierta puedo ver resultados propios, compartir, finalizar declarando una/varias/ninguna foto o eliminar.
- Después de finalizar se muestran los datos textuales permitidos sin imágenes ni miniaturas rotas. Mis consultas Privadas no aparecen en feeds ajenos.

Referencia: DEC-017/019/021/022/023.

## Sources and authority

Read AGENTS.md, all seven harness/context documents, the 2026-10-12 product reorganization
notes, RF-03/RF-06/RF-07/RF-09/RF-11 grooming and the phase-2 scope notes. Relevant approved contracts
reviewed: RF-03, RF-06, RF-07, RF-08, RF-09, RF-10 and RF-11. Older code observations in
those documents are dated intake findings; the working tree below is the current baseline.
DEC-035 and PRODUCT-2026-10-12-reorganization supersede historical product ordering.
RF-11 remains in Implementation review pending owner visual validation. RF-06 retains
its integrated smoke/device gates; RF-03/RF-07/RF-09 retain their recorded gates.
No historical tests or Docker failures have been reasserted as fresh evidence.

## Intended outcome

An authenticated author can find a published consultation after leaving Create, closing
or reloading the app, or signing in again; reopen its authorized open detail and manage
its existing Private link. The accepted complete phase-2 goal additionally includes
real votes/results, finalization, deletion and private non-image outcomes. Those remain
visible dependencies, not capabilities supplied by a list alone.

## Current code findings

- frontend/src/App.tsx owns local Home/Create/Profile destinations, defaults to Home on
  authentication/restoration and unmounts destinations when leaving. Home is a welcome
  card. There is no owner consultation list, addressable consultation entry or router.
- frontend/src/ConsultationComposer.tsx contains the live wizard and stores publishedId
  in component memory. Leaving or reloading loses that navigation reference, but not
  the published database row/photos. It mounts PublishedSuccess after publication.
- frontend/src/PublishedSuccess.tsx fetches persisted open detail and all photos;
  shows Open, full question/context and PrivateLinkControls only for Private.
  Its Published/live heading is inappropriate for an ordinary returning-owner detail.
  Public has no owner-link request or share control.
- frontend/src/consultationApi.ts has capacity, publication, protected open detail/media
  and owner Private-link clients. It has no list or owner terminal projection.
  Detail runtime guards deliberately accept exactly open.
- backend/app/models.py persists Consultation, ConsultationPhoto, owner_id, question,
  context, audience, state and published_at. Canonical states are open/finalized/deleted/
  removed. Associations preserve publication order. There is no vote, final declaration,
  aggregate count or participant outcome model, and no terminal transition date.
- backend/app/api/consultations.py and consultation_service.py implement real publication,
  advisory capacity, protected detail/media and persisted owner link read/disable/replace/
  create. There is no current-owner list or terminal mutation API.
- consultation_access.py allows an open Private owner to read without a token, including
  when their link is disabled. It grants non-owner Public read access; therefore the
  existing protected detail endpoint alone is insufficient to authorize an owner
  management screen. The new management contract must verify owner_id server-side.
- consultation_lifecycle.py supplies a pure transition decision and concurrency contract.
  It changes no database state, votes or files.
- backend/app/cleanup.py retries durably revoked files, verifies absence and cleans expired
  temporary sessions. Publication consumes sessions; promoted ready files survive cleanup.
  No operation currently revokes/queues every published photo at finalization/deletion/
  removal. Setting a terminal state or hiding a row would not implement physical erasure.
- Alembic 20260928_0004 has owner/state/created_at indexing, not a dedicated publication-time
  list index. Existing persistence is sufficient for the proposed read increment; no new
  product column/table/backfill is needed. Do not modify historical migrations.
- Integration issues relevant to reused detail: PublishedSuccess accumulates object URLs
  before publishing them into state; later media failure/unmount can leave earlier URLs
  unreleased. Its media client collapses non-401 failures to unavailable and the view
  collapses detail errors into retryable failure. The reused owner detail needs explicit
  generic-unavailable versus network/storage-failure handling and full URL cleanup.
  Link refresh returns a cleanup callback but event callers do not consume it; guard late
  results from navigation/account changes. An uncertain mutation must require refresh
  before treating the old link as current.
- Composer cap copy currently says "Close one before starting another." No close action
  exists. RF-12 must present truthful limit guidance and a real path to the list, without
  suggesting the author can release a slot in this increment.

Inspected the named production modules, current migration, PrivateLinkControls, link
helpers and existing consultation/composer/App tests. No application code was changed.

## Inherited accepted constraints

- English product copy; existing React/FastAPI/PostgreSQL and signed-cookie session.
- Temporary preparation is not a draft library and must never appear in this list.
- Publication is immutable; Public and Private both require registered accounts.
  Private is unlisted and forwardable, not an invitee allowlist.
- No expiry, countdown, reopening or extra lifecycle date; published_at is publication time.
- Only authors see future aggregates, never voter identities or individual choices.
- Finalization declares one/several/none and closes in one operation. It immediately
  revokes access and requests physical deletion, with no owner photo buffer.
- Deleted/removed unfinalized consultations have no declared outcome. Minimum finalized
  non-image outcomes may survive later deletion/removal; that future history contract
  does not authorize retaining original free text, photos or another lifecycle transition.
- RF-08 FR-5 explicitly forbids copying question/context into retained outcome data.
  Finalized presentation therefore uses identifier/date/state and later permitted numeric
  outcomes, not the original question/context or audience metadata. Do not reopen this
  accepted privacy rule merely to make historical cards more recognizable.
- New requests reauthorize; no polling or recall of previously downloaded bytes.
- Owner visual validation belongs to the product owner (DEC-034).

## Candidate approach and alternatives

Recommended: one private author destination containing a compact text list and a
returning-owner detail. Reuse current open media/link contracts behind an explicit
owner-only management read. Add a separate minimal finalized projection. Connect only
real available operations. This is independently useful now without changing the full
phase-2 finish line.

Alternative: list only, with no way to reopen. Smaller but fails the stated management
goal and leaves existing link controls inaccessible after leaving Create.
Alternative: wait for votes/results/finalization/deletion and deliver the entire card
together. Fully satisfies the broad card at once but delays recovery of existing
consultations and bundles multiple ungroomed contracts, including physical deletion.
Alternative: add full routing/share entry now. Improves external link usability but
absorbs RF-26 and its authentication-return/device/access contract. Not recommended.

The approved increment can later be completed and validated as that increment; the full
RF-12 Trello criteria remain pending until the named consumers have evidence.

## Approved observable scope (2026-10-12)

### List and navigation

- Accepted primary destination (Q1A): visible label My consultations beside Home,
  Create and Profile; header My consultations. Keep Home default and reserved for
  future RF-14 community discovery. The owner confirmed Q1A on 2026-10-12.
- Same local destination model, desktop top/mobile bottom navigation, visible labels,
  active/focus semantics, safe areas and 44px targets; no router or browser persistence.
- Open tab by default, Finalized tab available with independently truthful empty state.
  Only current account rows in the chosen state, newest published_at first with UUID
  tie-break. Text-only list avoids automatic photo loads and retained thumbnails.
- Open rows: question, Public/Private, Open and labelled publication date. No invented
  votes, percentages, "0 votes", best photo, closing dates or fake action buttons.
- Finalized rows: a display reference derived from consultation ID, Finalized and
  publication date. No question/context, audience, photos, photo URLs or link tokens.
  This reference is an identifier, not a new stored title. No outcome is inferred.
- Finalized rows may open the same minimal text-only owner summary. Real aggregates
  and declared option labels arrive with RF-18/RF-19/RF-20; do not fetch photo detail.
  Actual production finalization cannot be exercised until those operations exist.
- Never list deleted/removed rows or upload sessions. Future private retained-outcome
  history after deletion/removal needs the owning contracts; RF-12 does not erase it.
- Empty Open state: "You have no open consultations." with a real Create action through
  existing capacity/config checks. Empty Finalized state: "You have no finalized
  consultations." No promise of an available Finalize action.
- Load on entry/tab change and explicit Refresh; no polling. Bound pages, initially
  20 rows, Load more while a next cursor exists. Preserve page/tab in memory when
  returning from detail; refetch on return to reconcile changes. Refresh starts at
  first page; a later-page failure preserves loaded rows and retries that page.
- Publication retains its existing success feedback; add View in My consultations.
  Do not silently change RF-06 publication destination. Fresh app entry still reaches
  Home, from which primary navigation makes consultations recoverable.
- Every exit from an unpublished dirty composer uses the existing guard, including the
  new destination. Pending publication protection and relinquish-before-unmount remain.
- Cap guidance states the configured limit is reached and offers View my consultations.
  Explain that freeing a slot requires future finalization/deletion without presenting
  those as available actions. Link disable does not free a slot or delete photos.

### Returning-owner detail and real link management

- Authorized open detail: neutral heading Your consultation, full question/context,
  publication date, audience, server Open label and photos in stored order. Back to
  My consultations and Refresh. No edit, vote, results, finalize or delete controls.
- Reuse/refactor the persisted detail/media/link controller from PublishedSuccess,
  keeping its post-publication wording separate. Do not mount a "Published/live"
  success message just because the author reopens an old consultation.
- Private: load current owner link only on detail; copy/disable/replace/create-new with
  existing confirmations, expected-generation protection, pending prevention and refresh.
  Clipboard errors permit manual copying. Indicate that link copying is available but
  the recipient entry/authentication-return journey remains RF-26 work.
- Public: display registered audience reach; no unusable Share/Copy destination button
  until RF-26 provides real link entry. RF-12 does not claim end-to-end sharing.
- Link disabled: owner still reads the open consultation. It remains open, uses capacity,
  retains photos and is inaccessible to other accounts until a new link is created.
- Do not reuse the link token as proof of ownership or persist it outside memory.

### Loading, failure and privacy

- Initial loading is distinct from empty success. Network/5xx/invalid-response failures
  show Retry and keep navigation usable; never label them deleted or empty.
- 401 clears list/detail/link/object URLs and returns to Sign in. Ignore late results
  from the previous account, item, tab or unmounted view.
- Unknown/non-owner/deleted/removed target gives generic unavailable and Back to list.
  If an open item became finalized, reread the owner projection and render only its
  permitted summary. Do not relax open-only protected detail/media.
- Missing authorized photo bytes: explicit retryable photo-load failure, no substitute,
  broken image or invented complete comparison. Revoke every created URL on partial
  failure, replacement, unavailable result, session loss and unmount.
- Terminal projection never reads storage, derives media URLs or calls link APIs.
  Stale client rows cannot authorize a request; every request checks current server state.
- List/detail responses private/no-store and no-referrer; no local/session storage,
  offline photo cache, content/token logging, public metadata or extra data copies.
  Render questions inertly and wrap long/Unicode text.
- An uncertain link mutation is not reported successful; Refresh reconciles current
  server state before copying/retrying against an assumed current generation.

## Technical choices resolved by coordinator

Routine engineering selections, subject to final approved scope; not new product decisions:

- Add narrowly scoped list/owner-read services in backend/app/consultation_service.py,
  routes in backend/app/api/consultations.py and strict schemas in backend/app/schemas.py.
  Proposed routes: GET /api/my-consultations and GET /api/my-consultations/{id}.
  These routes do not exist yet. Derive account exclusively from get_current_account,
  scope queries server-side, and use no writable owner ID or global list filtered by JS.
- A discriminated owner response separates open content from finalized minimum metadata.
  Ownership check precedes reusable open projection; terminal branch has no content/
  storage/link access. Keep existing generic public/protected routes unchanged in meaning.
- Bounded state filter open|finalized and validated cursor over published_at/id, maximum
  page size 50; reject malformed/oversized input, prevent duplicate appends. Cursor is
  only pagination, never authorization; every page re-scopes to the current owner.
  A refresh reconciles intervening publication/state changes; no snapshot-sync machinery.
- Use existing UTC publication timestamps and browser-local English date formatting,
  labelled Published, never relabel updated_at as a finalization date.
- No new data model, vote_count default, lifecycle setter, migration or package expected.
  Existing index is adequate for POC bounded owner queries. Revisit an additive index
  only with query evidence, never alter the historical migration.
- frontend/src/App.tsx / Navigation.tsx / ConsultationComposer.tsx integrate entry/guard/
  success/cap paths; consultationApi.ts adds strict clients; PublishedSuccess.tsx and
  PrivateLinkControls.tsx inform the shared detail controller; styles.css extends the
  existing visual base. New focused list/detail components may follow local conventions
  (they do not exist yet). Update tests alongside each boundary.
- No worker, scheduler, native project, media derivative or deployment configuration.

## Dependencies and card-criterion traceability

| Card criterion / capability | Current baseline | Proposed RF-12 increment / later owner |
| --- | --- | --- |
| Private own Open/Finalized section | Persistence exists, list absent | Owner list and minimum summary now; real terminal integration later |
| Date/state | published_at and canonical states exist | Show actual publication date/state; no new transition date |
| Vote count | No vote entity or aggregation | Omit now; RF-16 persistence then RF-18 trusted counts |
| Own results | No results contract | RF-18; only aggregate counts/percentages, never identities |
| Sharing | Private token/link operations and copy exist; no recipient route | Recover Private controls now; RF-26 Public share/recipient auth-return/platform journey |
| Finalize one/several/none | Pure lifecycle policy only | RF-19/RF-20 one observable operation, coordinated with RF-37 and votes/outcomes |
| Delete | No author mutation | RF-13 after RF-37 published cleanup contract; no fake action |
| Text-only finalized outcome | Minimum IDs/date/state available, outcomes absent | Minimal owner projection now; actual counts/selections via RF-18/19/20 |
| No Private in others' feeds | No feed currently | Owner-scoped RF-12; RF-14 must enforce public/open server-side |
| Photo erasure | Temporary cleanup/retry works; published terminal trigger absent | RF-37 plus terminal consumers; no buffer/retained thumbnail |

RF-11 supplies canonical lifecycle; RF-10 supplies persistence/capacity/media/links;
RF-06 supplies composer and publication entry. Their pending visual/integration/device
gates remain unchanged. RF-14 feed is distinct from private owner management.
RF-21 private participant history and RF-23 reputation are separate consumers.

Restricted manual administrator removal (accepted RF-32 subset) and published-photo
cleanup remain required before real-user exposure. An RF-12 list is not permission to
release a beta lacking those safeguards. No result, cleanup or moderation capability
is claimed by storing enum values or testing manually seeded terminal rows.

## Questions - one consolidated material batch

### Open

None. The owner approved scope and plan finalization on 2026-10-12.

### Resolved

Q1A accepted on 2026-10-12: the owner answered `a`. My consultations is a fourth
primary destination; Home remains default and the future community entry. Recorded
as DEC-036. This answer does not approve plan finalization or harness launch.

Historical alternatives presented:

Q1 - Where should the author return to their consultations?

- A (recommended): add a fourth primary destination, My consultations. Home remains the
  default and future community entry; owner management is directly reachable from every
  authenticated screen. Costs one additional mobile navigation item.
- B: put a My consultations entry on Home with its local list/detail subview, keeping
  three primary items. Fewer items, but another navigation step and future RF-14 Home
  layout must retain this access.
- C: place My consultations under Profile. Keeps three items and groups private data,
  but hides a core repeated product action behind account navigation.

No additional question asks the owner to choose API routes, pagination, timestamps,
component structure, resource cleanup or to reapprove already accepted product rules.
Choosing Q1 alone did not approve plan finalization. The subsequent explicit approval
response "Vamos al lio" confirms the proposed increment and authorizes finalization.
The approved plan specifies the exact API, UX, validation and handoff contract.

- 2026-10-12: explicit selection, repository-first review, current read-only Trello intake
  and permission to create grooming notes/update project state.
- Inherited accepted decisions above remain in force. DEC-036 records only the accepted
  navigation choice; it does not adopt the rest of the proposed increment implicitly.
- 2026-10-12: after the coordinator explicitly asked to approve the proposed scope and
  plan finalization, the owner replied "Vamos al lio". The approved self-contained
  English plan is now `harness/features/RF-12-Implementation-plan.md`, marked
  `Ready for implementation`. This is not a harness-launch request.

## Validation outline (future implementation, not performed in grooming)

- Service/API: two-account ownership isolation across both audiences and all four states,
  no anonymous access, no token-based owner grant; exact permitted response fields and
  headers; finalized branch never calls storage/detail/link and emits no free text/media.
- Query: stable ties, ordered pagination beyond 20 rows, malformed cursors/filters/bounds,
  no duplicates, unknown states fail closed, deleted/removed/temp excluded, disabled
  Private included for its owner. Use isolated PostgreSQL to exercise actual query/schema.
- UI/API: strict guards and terminal discriminants; date correctness with timezone
  offsets; loading versus empty/error; initial and Load more Retry; active tab/page return,
  stale/account-switch results; 401 cleanup; unavailable back path; no future buttons,
  synthetic counters or broken thumbnails.
- Detail: full open text/order; no success celebration on return; all object URLs revoked
  on partial photo failure/unmount/account change; denied new requests clear content.
- Private controls: real copy feedback, confirm/cancel, disable/replace/create persistence,
  stale generation and uncertain response requiring Refresh, old-link denial and owner
  access after disable; Public and terminal make no owner-link requests.
- Composer regression: dirty exit Keep editing/Discard for new destination, publish
  pending guard, idempotent retry, relinquish handoff, success-to-list, truthful cap
  guidance; link mutation does not release capacity or delete photos.
- Built isolated stack: publish Public/Private as A, leave Create, reload/sign in, recover
  from list, reopen ordered real photos, mutate link, reject owner access from B; restart
  backend and recover again. Temporary cleanup must preserve promoted photos.
- Seeded finalized fixtures prove projection/privacy only, not real finalization, outcome
  computation or physical deletion. Real vote/result/finalization/deletion races and
  purge-failure/absence proof remain later consumer gates.
- Run appropriate full existing backend/frontend tests, formatting, lint, strict typing,
  production build and isolated integration validation after authorized implementation.
  No downgrade, active-volume cleanup or Docker repair in grooming.
- Owner validates visual/accessibility layout at 320px, desktop, 200% zoom/safe areas under
  DEC-034. Automated component/accessibility/layout checks remain technical validation.
  Actual web/iPhone/TestFlight navigation/session/link/device evidence stays explicit.

## Readiness checklist

- [x] Current selected card consumed and recorded read-only.
- [x] Code impact and relevant approved contracts inspected.
- [x] Existing decisions and consumer dependencies identified.
- [x] Routine technical direction selected.
- [x] Navigation Q1 resolved by the product owner (Q1A, 2026-10-12).
- [x] Proposed increment, exclusions and failure/validation behavior confirmed.
- [x] No material question remains identified.
- [x] Product owner explicitly approved implementation-plan finalization (2026-10-12).

No implementation, test run, browser visual inspection, commit, push, deployment or
Trello mutation was performed for this grooming.
