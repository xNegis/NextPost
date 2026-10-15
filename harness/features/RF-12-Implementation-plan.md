# RF-12 - Manage my consultations - Implementation Plan

## Status

`Ready for implementation`

On 2026-10-12 the product owner selected Q1A (fourth primary navigation destination).
After being asked explicitly to approve the proposed scope and plan finalization, the
owner replied "Vamos al lio". This approves this implementation contract. It does not
authorize the external harness, implementation, commits, pushes, deployment or Trello
changes. Harness launch requires a subsequent explicit request.

This contract delivers the coherent author-recovery increment below. Completion of this
increment does not certify every broad RF-12 Trello criterion or the full phase-2 loop.

## Source ticket

### Authorized review correction supplement - 2026-10-12

Following the independent review, the owner authorized the proposed correction/validation
work (`venga, vamos`). Correct the findings in
`harness/grooming/RF-12-implementation-review.md` within this feature scope. The closure
authorization also permits the smallest compatible transitive source-map-js patch/lockfile
change needed to remove the reported advisory. Preserve direct dependency versions;
add no new package, broad upgrade or feature. This narrow remediation supersedes the
no-dependency-change boundary only for that advisory. All other authority limits and
owner visual/device gates remain unchanged.

- Trello title: RF-12 · Gestionar mis consultas
- Trello URL: https://trello.com/c/L2mZ6OFf/14-rf-12-gestionar-mis-consultas
- Trello list at intake: Próximo · completar el MVP, configured APP - NextPost board
- Snapshot captured on: 2026-10-12, successful live read before 12:02:21 UTC /
  14:02:21 Europe/Madrid; connector supplies no exact read timestamp
- Last activity at intake: 2026-10-12T11:26:33.597Z
- Grooming notes: harness/grooming/RF-12-grooming.md

The current card requests a private Open/Finalized list with dates, states and vote counts;
access to own results, sharing, finalization declaring one/several/none and deletion;
and permitted text-only finalized data with no photos or broken thumbnails. The card
snapshot includes its 2026-10-12 reorganization note, which explicitly identifies missing
consumer contracts. Preserve the card and this traceability; do not change Trello.

## Objective

Let an authenticated author find a published consultation after leaving Create, closing
or reloading the app, signing in again or an ordinary server restart. The author can
reopen its current authorized open detail and manage the existing Private link.

Provide a private list of current Open and Finalized rows and a separate minimum
non-image finalized summary. Real vote/results/finalization/deletion capabilities remain
with their owning tickets. Do not invent votes, outcomes, actions or successful sharing.

## Context and current behaviour

- App.tsx owns local Home/Create/Profile navigation and defaults to Home on ordinary
  authentication/restoration. Navigation.tsx renders wide top and narrow bottom navigation.
  Home is a welcome card; there is no router or owner consultation list.
- ConsultationComposer.tsx implements the real Photos -> Details -> Review/publish wizard,
  dirty-exit confirmation, upload-session handoff and post-publication PublishedSuccess.
  Its publishedId exists only in component memory. Leaving Create loses that reference,
  although RF-10's published row/photos persist.
- PublishedSuccess.tsx fetches current open detail and ordered protected photo blobs,
  displays Open and loads owner Private-link controls for Private only. Its Published/live
  heading describes publication success and must not appear on ordinary returning detail.
- consultationApi.ts implements capacity/publication/open detail/media and owner-link
  clients. Its open-only detail guard is intentional. It has no owner list/terminal reader.
- backend/app/models.py contains accounts, upload sessions/images, Consultation and
  ConsultationPhoto. Consultations have owner_id, immutable normalized question/context,
  audience, canonical state and published_at. There are no vote, aggregate, declaration
  or participant-outcome models and no terminal transition timestamps.
- backend/app/api/consultations.py and consultation_service.py implement publication,
  capacity, protected open detail/media and real owner Private-link read/disable/replace/
  create. No owner-list or terminal-mutation route exists.
- consultation_access.py allows the open owner to read Private without a token, including
  while their link is disabled. Public detail is also available to other registered
  readers; protected detail access alone does not prove management ownership.
- consultation_lifecycle.py contains the canonical open/finalized/deleted/removed enum
  and pure transition policy. It performs no database, outcome or photo mutation.
- RF-07 cleanup revokes temporary abandoned/discarded files and retries durably requested
  deletion. RF-10 consumes upload sessions and preserves promoted ready photos. No current
  terminal operation queues every published photo for physical deletion.
- PublishedSuccess currently risks unreleased object URLs when a later media load fails
  or the component exits before installing the complete URL array. It also collapses
  generic denied detail into retryable error; photo errors are collapsed in the client.
  Its event-triggered link refresh/mutation needs protection against late responses.
  Resolve these issues in the shared detail integration required by this increment.
- Composer cap copy currently asks the author to close one, although no such operation
  exists. Replace that implication with truthful cap guidance and a real list destination.
- The existing consultation index is owner/state/created_at. No new product data is needed
  for the bounded POC list; no migration is part of this contract.
- The working tree contains extensive uncommitted user/dependency implementation and
  documentation. Preserve it. Historical intake observations in older plans are not
  descriptions of current code.

Binding decisions: DEC-004–009 (stack, session, copy), DEC-012/018 (temporary preparation
and immutable publication), DEC-017/019/021–023 (no expiry, author-only aggregates,
atomic declaration/finalization, no image buffer, minimum outcomes), DEC-028–033
(unavailability, links, persistence and lifecycle), DEC-034 (owner visual validation),
DEC-035 (purpose-based community) and DEC-036 (fourth primary destination).

## Scope

### In scope

- My consultations as a fourth authenticated primary destination; Home remains default.
- Owner-only Open/Finalized list, text-only rows, actual publication date/state, newest
  first, bounded pagination, empty/loading/error/refresh states.
- Owner-only management read with separate open and minimum finalized response variants.
- Returning open detail with full current text, audience, ordered actual photos and
  existing Private-link controls; neutral wording and Back to My consultations.
- Minimum finalized identifier/date/state summary, with no photos or original free text.
- Shared/refactored open detail/media/link controller used by publication success and
  returning detail, with robust object-URL cleanup and failure/session-loss handling.
- Publication-success View in My consultations action without changing the existing
  success destination; real cap-to-list navigation and truthful guidance.
- Composer dirty/pending navigation regression protection for the new destination.
- Focused tests, complete relevant quality checks and isolated built-stack verification.

### Out of scope

- Vote model, vote counts (including invented zero), percentages, results, winning photo,
  voter identities/choices, rankings, coincidence metrics or participant feedback.
- Finalization, choosing final photos, deletion, administrator removal or physical purge
  of published photos. No state setter or partial terminal operation.
- Public share button, recipient link entry, authentication-return routing, device share
  menu, native deep links or other RF-26 journey. Existing Private copying remains real
  link copying and must not be described as a validated complete recipient flow.
- Editable publication, saved drafts, automatic expiry, countdown, reopening, new
  lifecycle date, photo archive/thumbnail/backup, image versioning or offline cache.
- Feed, search, public profiles, follow relationships, comments, moderation UI, broad
  administration, account deletion/export or beta rollout.
- Router, browser-persistent navigation/content, new dependency, worker, queue, scheduler,
  native project/signing/TestFlight distribution or deployment changes.
- Additional free-text/audience retention for finalized outcome presentation; RF-08 FR-5
  and DEC-023 allow minimum outcome records, not copying original text into history.

## User experience

### Navigation and recovery

Primary navigation order is Home, Create, My consultations, Profile. Use the existing
semantic component, visible label My consultations, repository-owned SVG, active/focus
semantics, desktop top/mobile bottom presentation and safe-area clearance. Longer labels
may wrap; no horizontal scroll or icon-only substitution. Each control is at least 44px.

After ordinary sign-in, registration or session restoration, Home remains initial.
Selecting My consultations opens its Open tab and loads current-owner rows from the
server. Reopening the app needs no stored consultation ID; primary navigation recovers
the persisted collection.

Selecting My consultations from an unpublished dirty composer uses the existing
Keep editing/Discard confirmation. Keep editing restores the live wizard; confirmed
Discard revokes temporary client URLs and requests RF-07 cleanup. Pending publication
must not be interrupted through the new navigation or create a late destructive discard.
The successful handoff still relinquishes before composer unmount.

After publication, retain the existing Published success feedback and Back Home.
Add View in My consultations, opening the newly published consultation as an owner
detail inside the My consultations destination. Back from that detail opens Open.
Do not automatically redirect away from RF-06 success.

At capacity, say "You've reached the limit of {limit} open consultations. You can't
start another consultation right now." Offer View my consultations and Back Home.
Do not ask the author to activate a nonexistent close/delete action. This increment
does not release slots; disabling a link leaves the consultation open.

### List

Heading My consultations. Accessible Open and Finalized tabs select current lifecycle,
with Open initially selected. Each independently loads and refreshes.

Open rows show complete question (bounded by its published text contract), Public or
Private, Open, and Published followed by the actual publication date. They are text-only;
selecting View consultation opens the owner detail. No thumbnails or context in the list.

Finalized rows show Consultation followed by the canonical UUID as a wrapping reference,
Finalized and Published date. The identifier is not a new persisted title. Selecting
View consultation opens its minimum summary. No question/context, audience, photo count,
photo IDs/URLs, token, aggregate or declared selection is inferred.

Both tabs sort descending published_at, then descending UUID. Render at most 20 per
page by default. Load more appends the next page, prevents duplicate activation and
does not duplicate IDs. Hide Load more when no next cursor exists.

An empty Open success says "You have no open consultations." with Create consultation
through existing capacity/config checks. Empty Finalized says "You have no finalized
consultations." No Finalize CTA. Loading and failed requests must never look like empty
success. Do not show a fake "no votes" or outcome.

Refresh starts from the first page. Preserve chosen tab and loaded-page count in memory
while opening detail. On Back, revalidate the previously loaded range from page one using
fresh cursors, for at most the previous number of pages, stopping early if exhausted;
replace rather than combine stale pages. Keep previously loaded rows during a retryable
revalidation failure with clear failure feedback. Navigation away from the destination
may reset tab/page state; app reload starts from Home. No persistence or scroll-history
framework is required. There is no polling or background refresh.

### Owner detail

Open detail uses Your consultation, actual Open status, Published date, Public/Private
reach, complete question then optional complete context, and actual ordered photos.
Reuse ConsultationTextDisplay and display images without forced crop. Returning to an
existing consultation must not celebrate a new publication.

Fetch the owner management response first; ownership is checked on the server. Then
fetch each photo through the existing protected media API using cookie authentication.
Do not accept a Private token as management authority or fall back to temporary preview
images. Hold image URLs only in memory and install the complete successful comparison.
If any photo fails, clear/revoke partial URLs and show a usable error with Retry and Back.

For Private only, fetch the current owner link and show the existing Copy, Disable,
Replace, Create new and Refresh controls. Confirm Disable/Replace; Cancel changes
nothing. Re-copy is stable until a real transition. A disabled link does not prevent the
author opening photos and does not release capacity, finalize or delete the consultation.
For Public, show audience reach and make no owner-link request or share-control promise.

Private copy retains the fragment token and manual-copy fallback. State briefly near
these controls that "Opening shared links is not available yet." This reflects the
missing recipient entry journey; do not describe Copy as a complete working invitation
or add any fake recipient route. Remove/update that limitation only through later RF-26.

Finalized detail is a separate text-only summary showing reference, Finalized and Published
date. State "Photos are no longer available." This is an access statement, not a claim
that physical deletion was verified. Make no photo/detail/link requests and no outcome
claim. Back to My consultations and Refresh remain usable.

### Failures and current state

- Initial list/detail loading communicates status and keeps primary navigation usable.
- Network, 5xx, invalid nominal-success payload or authorized missing photo bytes:
  safe local retryable error; do not claim deleted, empty, or successful publication.
- Failed Load more preserves successful rows and offers retry for that page. Disable
  duplicates during pending requests. Failed refresh labels retained rows as not refreshed.
- Any 401 clears private list/detail/link state, every owned blob URL and pending
  navigation state and delegates App's existing Sign in transition.
- Valid UUID for unknown/non-owner/deleted/removed owner target: the same generic
  consultation_unavailable response and generic unavailable view with Back to list.
  A Public reader or valid Private-link holder cannot reach someone else's management.
- If an open detail/media/link request reports consultation_unavailable, clear current
  protected text/photos/link, then make at most one owner-read reconciliation for that
  user operation. If now finalized, render only the minimum finalized summary; if denied,
  show generic unavailable. If it still reports open, keep a safe unavailable state with
  manual Refresh rather than looping. A network error on reconciliation stays retryable
  with content cleared.
- An uncertain or stale-generation link mutation invalidates the client assumption of
  current link. Do not claim success or permit Copy/repeating mutation until Refresh
  rereads the authoritative link. No automatic mutation retry or link rotation.
- Ignore late responses after account change, item change, tab change or unmount.
  Revoke URLs from superseded requests even when they were never installed in React state.
- An idle screen is not polled. Already loaded bytes may remain until a real new denied
  request or navigation, as accepted by DEC-029. Every server request still reauthorizes.

## Functional requirements

### FR-1 - Private collection

List only the authenticated account's current open or finalized consultation rows.
Scope in SQL, not client filtering, and exclude deleted/removed/upload-session rows.
Owner access to Private rows does not depend on link active state or possession.

### FR-2 - Separate state projections

Open list/detail expose only the exact allowlisted fields below. Finalized projections
contain exactly id, state and published_at. Use canonical lifecycle and a discriminated
response union; unknown state never falls back to open.

Do not broaden the existing open-only protected detail/media/link API for terminal access.
Do not weaken can_access to permit all owner terminal reads. The new owner summary is
separately authorized by account ownership and contains no protected content.

### FR-3 - Stable pagination

Use state filter open|finalized, default open, page size default 20, maximum 50, minimum 1.
Order by published_at DESC, id DESC and fetch limit+1 to derive next_cursor. Subsequent
pages select keys strictly below the cursor tuple within current owner and selected state.

Cursor encodes version 1, chosen state, UTC publication timestamp and UUID, with bounded
URL-safe encoding (maximum 512 characters). Validate grammar, version, canonical state,
timestamp and UUID before querying. No content/token/owner field in the cursor. A cursor
is not an access grant; reuse across accounts never exposes another owner's rows.
Reject cursor/filter mismatch or malformed input with safe validation_error, not parser
internals or an empty page. No signed grant, snapshot session or pagination table needed.

Intervening publications may appear only on Refresh; state changes may remove rows.
Client append deduplicates IDs. No promise of an immutable collection snapshot.

### FR-4 - Real navigation and composer integration

Add one local authenticated destination and focused list/detail components. Preserve
Home default, Profile sign-out, existing dirty confirmation, publication pending safety,
idempotent Retry and promoted-session relinquish. Success-to-owner-detail is explicit;
cap-to-list is truthful and does not invent an available release operation.

### FR-5 - Open photos and link management

Reuse real stored open detail/media and current generation-aware owner mutations.
Protect ordered comparison and stable token transport. The new management endpoint
checks owner before calling shared open projection; it must not authorize a general
Public reader as an owner. Terminal summary performs no storage or link work.

### FR-6 - Resource and request ownership

All created object URLs have one explicit owner. Revoke on partial failure, superseded
request, item change, retry/refresh replacement, unavailable result, session loss and
unmount. Abort or invalidate requests by component/request generation. Event-triggered
refresh must not rely on an unused cleanup callback. No old response can restore
private data after sign-out or an account/item switch.

### FR-7 - Honest functionality and retention

No votes/results/terminal controls, synthetic metrics or recipient-sharing success claim.
No original question/context/audience in finalized presentation, even if old database
rows still hold those columns. Do not copy, backfill or retain that data for history.
Actual field erasure and complete finalized outcomes belong to terminal/RF-37 consumers.

### FR-8 - Accessibility and presentation

English copy and existing light visual base. Accessible tabs, loading/status/alerts,
keyboard focus, logical headings, labelled publication dates, wrapping/dir support for
user text, 44px targets, mobile safe areas and content clearance for four destinations.
Owner visual gate under DEC-034; automated coverage does not certify it.

## Technical approach

Extend the existing consultation services and router with narrow current-owner reads,
plus state-specific response schemas. Keep domain/query logic outside HTTP handlers and
UI markup. Use a dedicated local list/detail container; keep App as destination/session
owner. Extract shared open-detail/media/link logic from PublishedSuccess so publication
success and returning detail reuse one robust implementation with distinct wording.

No global state library, routing package, general history abstraction or future vote/
outcome model is needed. Existing tables/indexes suffice for the POC read increment.

### Affected areas

- Frontend: frontend/src/App.tsx, Navigation.tsx, ConsultationComposer.tsx,
  PublishedSuccess.tsx, consultationApi.ts, styles.css and their tests.
  Reuse ConsultationTextDisplay.tsx, PrivateLinkControls.tsx, ConsultationUnavailable.tsx
  and consultationLink.ts. Add focused owner-list/detail/shared-controller components or
  hooks in frontend/src; these files do not yet exist and names may follow conventions.
- Backend/application: backend/app/consultation_service.py,
  backend/app/api/consultations.py and backend/app/schemas.py; focused service/API tests.
- Domain/data model: reuse models.py and consultation_lifecycle.py; no new model/column
  or mutation. Keep consultation_access.py semantics intact.
- Storage/background work: no change. Shared frontend blob ownership is repaired;
  private server storage, cleanup/promotion and physical deletion boundaries remain.
- Configuration/deployment: no new setting, package, volume, service or native project.
- Documentation: README explains author recovery and the limited implemented capabilities;
  update project state only from evidence, retaining consumer/visual/device gates.

### Data and migration requirements

No migration, backfill or downgrade. Existing Consultation fields support these reads.
Use published_at as publication time, not created_at/updated_at as a closure surrogate.
Serialize an unambiguous valid UTC ISO timestamp once (no appended Z after an offset).
Format in English using the browser's local timezone and a machine-readable time element.

Do not edit migration 20260928_0004 or add a speculative index. If measured query behavior
requires indexing at later scale, report evidence separately. If this implementation
appears to require new product persistence or terminal data, stop and report the conflict.

### API and integration requirements

Add these real routes:

1. GET /api/my-consultations?state=open&limit=20&cursor=...
   - Verified cookie account only; no target owner/account parameter.
   - 200: exactly {items: [...], next_cursor: string|null}.
   - Open item: exactly id (UUID string), state ("open"), question (string),
     audience ("public"|"private"), published_at (UTC timestamp string).
   - Finalized item: exactly id, state ("finalized"), published_at.
   - Empty authorized collection: items [] and next_cursor null.
2. GET /api/my-consultations/{consultation_id}
   - Verified owner and latest persisted state, no token-based authorization.
   - Open 200: exactly id, state ("open"), owner_nickname, question, context
     (string|null), audience ("public"|"private"), published_at, photos.
     photos use existing exact id/width/height metadata in immutable stored order.
   - Finalized 200: exactly id, state ("finalized"), published_at.
   - Unknown/non-owner/deleted/removed: 404
     {"detail":{"code":"consultation_unavailable"}} without cause/content.
   - No writable state/action or terminal side effect.

Both routes require cookie authentication; missing/malformed/stale session returns the
existing 401 unauthenticated. Invalid query/UUID gets safe existing 422 validation_error
without raw supplied content; no information about target existence. Use explicit
response allowlists and private/no-store, no-referrer, nosniff headers on new reads.
For finalized select only the necessary columns; never build an open detail and redact it.

Current open photos still use GET /api/consultations/{id}/photos/{photo_id}/content.
Preserve the distinction between 404 consultation_unavailable, 401 unauthenticated,
503 unavailable (ImageUnavailableError) and network/unexpected failure in the frontend
photo client so callers can reconcile lifecycle versus retry media. Keep existing
callers compatible and do not expand media access.

Reuse GET /api/consultations/{id}/private-link and POST private-link/disable|replace|create
with expected_generation as an exact decimal string. Preserve trusted-origin protection,
confirmation, row locking and current open/owner authorization. The list carries no
generation/token; load on detail only. Do not change audience, counts/cap or photos.

Frontend JSON is untrusted: validate exact state/allowed fields, UUIDs, canonical audience,
bounded page size, valid UTC timestamps, photo metadata and cursor type/bounds.
Reject terminal payloads containing content/photos/token rather than silently rendering
a partial redacted result. No link secret or internal storage IDs in management responses.
Existing publication/open-only reader contracts remain compatible.

Read current database state on each request, avoiding stale ORM identity reuse across
requests. RF-12 adds no write or lock protocol for terminal state. Later terminal consumers
must use DEC-033 locks/atomic side effects; do not simulate those with a state setter now.

### Security and privacy

- Derive ownership solely from get_current_account; query filter and per-ID check prevent
  cross-account management even for Public consultations and valid Private token holders.
- Keep Private links fragment-based, tokens in protected headers where existing recipients
  require them; owner management reads need no token. Build copy URL only from trusted
  application origin. No arbitrary return target.
- No private collection/text/token/media in localStorage, sessionStorage, logs, analytics,
  offline caches, anonymous HTML/SEO metadata or public file roots.
- Render user text inertly; no raw HTML, Markdown execution or automatic linkification.
- Clear account-bound state and all URLs on session loss/sign-out; late responses fail closed.
- Terminal metadata never leaks photos/free text/links; protected open routes stay denied
  for all terminal states, including the author.
- Physical deletion completion is never inferred from an unavailable photo or finalized row.
  Deletion failures remain RF-37 work and cannot restore authorization.

## Implementation sequence

1. Add allowlisted list and owner open/finalized schemas and cursor validation.
2. Implement owner-scoped ordered queries and per-ID projections; reuse current open
   projection only after explicit owner check. Add exact privacy/access/pagination tests.
3. Register GET routes, safe validation/errors and private headers; test actual HTTP paths.
4. Add typed runtime-validated frontend clients and media error distinction.
5. Extract/refine shared open detail/photo/link controller from PublishedSuccess; cover
   partial URL cleanup, unmount/late results, current-state reconciliation and link refresh.
6. Add My consultations list/tab/pagination/minimum finalized detail and neutral open detail.
7. Add fourth navigation and composer dirty/pending/success/cap integrations while preserving
   ordinary Home default and publication/session handoff.
8. Complete accessible responsive styling and focused integration/regression tests.
9. Run full relevant quality checks and isolated PostgreSQL/built-stack author-recovery smoke.
   Report exact evidence and pending visual/device/consumer gates; update state accordingly.

## Validation strategy

### Automated tests

- New routes: valid owner, anonymous/invalid/stale session, two accounts, both audiences,
  Private link enabled/disabled, Public non-owner, token holder who is not owner, unknown
  ID and every state. Deleted/removed share exact generic unavailable behavior.
- Payload: exact keys by state; no email, storage/source-session/fingerprint/key/generation/
  token or vote data. Finalized excludes original text/audience/media even with populated
  legacy fields; spy/assert no storage/read-detail/link call.
- Query/cursor: more than 20 rows, identical published_at ties, canonical UUID ordering,
  empty/exhausted page, bounds/default/filter, malformed/oversized/version/state mismatch,
  cross-account cursor reuse, state changes between pages, no duplicate client append.
- Use isolated PostgreSQL with existing Alembic head for UUID/timestamp ordering and
  owner-scoped cursor queries, not only SQLite create_all. This proves reads, not a
  nonexistent vote-versus-finalization race.
- Client guard: unknown/missing states, forbidden finalized keys, wrong types/IDs/audiences/
  dates/cursor, HTTP 401/404/422/503/5xx and network failures.
- App/UI: fourth destination/active state/Home default, tabs/list/detail/back/refresh/
  Load more, empty distinct from failed, retained rows on later failure, new publication
  entry, 401 cleanup, account/item/tab switches and late-response suppression.
- Detail/media: full text and stored photo order, neutral return wording, all-or-error
  comparison, denied request reconciliation to minimum terminal summary, retryable missing
  bytes and every object URL released on partial/superseded/unmount/session-loss path.
- Links: Private-only request, Public/finalized no link API, confirm/cancel, copy and manual
  fallback, pending double activation, exact generation, disabled-owner access,
  lost-response/stale conflict requires authoritative Refresh before copy/mutation.
- Composer: new navigation Keep editing/Discard, pending guard, no premature discard,
  successful relinquish-before-unmount and explicit View in My consultations; cap copy
  and list entry do not suggest an available terminal action.
- No edit/vote/result/share-public/finalize/delete controls, fake counts, broken thumbnails,
  expiry/date promises or fabricated outcomes. Inert/wrapping long Unicode text.
- Existing account/profile/photo/text/audience/link/publication/lifecycle/composer suites
  remain green. Include meaningful accessibility/layout regression checks for four labels.

### Manual validation

- Run isolated built frontend/backend/PostgreSQL with two accounts and real normalized
  images. A publishes Public and Private, leaves Create, finds both from own list,
  reopens stored photo order/text, reloads/signs in and recovers again.
- B sees no A management rows and cannot use A's owner read, even for Public or with
  A's valid Private capability. Existing eligible protected-reader access remains unchanged.
- A disables/replaces/creates its link; after next actual requests old links deny,
  current link persists across restart, owner detail still works when disabled, capacity
  is unchanged. Do not claim recipient frontend/auth-return tested.
- Restart ordinary test services and recover persisted consultations; run existing cleanup
  only on disposable smoke storage to prove promoted images survive.
- Seed finalized/deleted/removed fixtures only in isolated tests to prove projection/access.
  These do not prove actual finalization, outcome retention or physical photo deletion.
- Product owner performs visual validation at 320px, desktop, 200% zoom and relevant
  safe areas, four-label navigation clearance, keyboard/focus, tabs and long text (DEC-034).
  Codex/harness must not use browser screenshots/visual inspection without a specific request.
- Real iPhone/TestFlight navigation/session/copy/device evidence remains a named external
  delivery gate while native ID/signing/project environment is unavailable. Do not claim it
  from component tests. RF-06/RF-07/RF-09/RF-11 pending gates remain independently tracked.

### Commands

From repository root, using the existing environment:

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

Set TEST_DATABASE_URL only to an isolated disposable PostgreSQL database for live tests.
Use the existing Alembic configuration to install head on that database:

```powershell
.\.venv\Scripts\python -m alembic -c backend\alembic.ini upgrade head
```

Use an isolated Compose project with disposable database/private-photo volumes for the
built smoke. Existing commands inside that isolated project include
docker compose up --build -d and docker compose exec backend python -m app.cleanup.
Do not run cleanup/downgrade or remove volumes against active user data.
No new migration, downgrade, Docker installation repair or native generation is required.
Skipped PostgreSQL/failed Docker/unavailable device checks are reported as unverified
gates, never passed.

## Acceptance criteria

- [ ] Authenticated primary navigation has Home, Create, My consultations and Profile;
      ordinary sign-in/registration/restoration still defaults to Home.
- [ ] The author recovers published Public/Private consultations after leaving Create,
      app reload, signing in again and ordinary test-service restart.
- [ ] Owner-only Open/Finalized list uses actual state/publication date and stable bounded
      newest-first pagination; deleted/removed/temporary preparations are excluded.
- [ ] Open rows show question/audience; finalized rows and summary expose exactly minimum
      identifier/date/state, no original text/audience/photos/link/outcome fabrication.
- [ ] Neutral returning open detail shows full current text and actual stored photo order,
      with usable Back/Refresh and no publication-success celebration.
- [ ] Private link controls perform real owner operations, stable copying, confirmations,
      exact generation and reconciliation; Public/finalized make no link request.
- [ ] Disabled Private link preserves owner read/capacity/photos. Copy does not imply a
      functioning recipient journey; its limitation is visible.
- [ ] Loading, both empty states, initial/later-page errors, Retry/Refresh/unavailable and
      session-loss states are distinct, truthful and usable.
- [ ] Cross-account management cannot be granted by Public access, a Private token,
      guessed IDs or a reused cursor; server ownership and privacy headers are proven.
- [ ] Finalized branch touches no storage or protected-detail/link surface. Existing
      open-only detail/media/link authorization stays unchanged for terminal states.
- [ ] Partial/superseded photo loads and exits release every created object URL; no late
      response restores private content after account/item/tab change or session loss.
- [ ] New composer exits retain dirty confirmation/pending protection; publication retains
      Retry and relinquish semantics and adds an explicit owner-detail entry.
- [ ] Cap guidance offers a real list destination without a nonexistent close/delete action.
- [ ] No votes/results/counters/terminal action, Public sharing route, router, draft persistence,
      expiry, new model/migration/worker/package or photo-retention copy is introduced.
- [ ] English, semantic tabs/navigation, focus/status/error handling, wrapping, 44px targets
      and safe-area clearance are covered; owner visual gate is reported separately.
- [ ] Full automated quality checks, isolated PostgreSQL list query and built two-account
      recovery smoke have exact evidence. Future consumer/device gates remain explicit.
- [ ] Documentation states completion only for this approved increment, not the broad
      card or phase-2 loop; no unauthorized Trello/commit/push/deploy operation occurs.

## Dependencies and ordering

Read complete approved RF-03/RF-06/RF-07/RF-08/RF-09/RF-10/RF-11 plans and inspect current
code before implementation. RF-01/RF-02 supply authentication; RF-03 navigation conventions;
RF-06 composer/success; RF-07 storage/cleanup; RF-08 text; RF-09 access/link primitives;
RF-10 durable publication/capacity/read/link operations; RF-11 canonical lifecycle.
Their pending independent review/visual/integration/device gates are not closed by RF-12.

| Full RF-12 criterion | Delivery boundary |
| --- | --- |
| Own Open/Finalized section, dates/states | This increment; actual terminal integration awaits consumers |
| Vote counts and own aggregate results | RF-16 vote persistence then RF-18; no placeholder now |
| Sharing | Existing Private controls recovered here; RF-26 recipient/auth-return/Public/device journey |
| Finalize declaring one/several/none | RF-19/RF-20 as one observable operation, with RF-37 |
| Delete and photo erasure | RF-13 plus RF-37 published revocation/purge/retry; restricted RF-32 removal subset |
| Finalized counts/selections | RF-18/RF-19/RF-20 minimum non-image outcomes, separate from this summary |
| No Private in others' feeds | This list is owner-scoped; RF-14 must server-filter its distinct feed |

RF-21 participant history and RF-23 incentives remain separate. Future terminal operations
lock/recheck and commit database outcome/revocation/deletion requests atomically under
DEC-033; RF-12 provides no partial shortcut. Minimum outcomes after later deletion/removal
need future contracts and must not be lost through a list filter or rewritten terminal state.

Published-photo cleanup and accepted restricted administrator removal remain safeguards
before real-user exposure. This approved development increment is not authorization for
beta deployment or a waiver of DEC-010's complete phase-2 finish line.

## Risks and mitigations

- Owner data leaks through general reader access: dedicated owner query/per-ID authorization,
  allowlisted state projections and two-account tests.
- Terminal free text/photo retention by UI reuse: separate minimum branch with no storage,
  link or protected-detail dependency; exact schema tests.
- Photo URL leaks or stale account data: explicit request-generation/URL ownership and
  partial-failure/unmount/session-switch tests.
- Uncertain link response uses stale capability: disable copy/mutation assumptions and
  reconcile by authoritative Refresh, never automatic rotation retry.
- Unstable ties/state-changing pages: publication-time/UUID keyset order, owner/state filter,
  client deduplication and bounded explicit refresh; no false snapshot guarantee.
- Composer exit deletes promoted photos: preserve pending guard and synchronous relinquish
  ordering, test actual navigation/handoff integration.
- Long fourth navigation label: wrapping and safe-area/content clearance, automated coverage
  and owner visual validation.
- User interprets missing capabilities as success: omit fake counters/actions, truthful cap
  and Private copy limitation; distinguish increment evidence from full-card criteria.
- Unavailable environment mistaken for completion: report current Docker/PostgreSQL/device
  gates and keep them pending; do not repair/reset user environments as a shortcut.

## Harness handoff notes

- Read AGENTS.md, all seven source-of-truth context files, product reorganization notes,
  RF-12 grooming, this entire plan and the named approved dependencies.
- Preserve extensive dirty tracked/untracked application and documentation work. No reset,
  unrelated refactor, dependency replacement or migration rewrite.
- Implement exactly the owner-recovery increment. Do not build later voting/results/
  finalization/deletion/share entry solely to make the broad card look complete.
- Use English identifiers/comments/tests/copy and the existing stack/session/visual base.
  If code or an accepted decision materially conflicts, stop and report rather than
  reinterpret or expand scope.
- Do not commit, push, deploy, mutate Trello, create native builds, send invitations,
  operate on active user storage or launch agents. External implementation agents must
  not open the Codex-only orchestration runbook.
- Codex coordinates a harness launch only after the owner's subsequent explicit request.
  This plan is self-contained; the harness needs no conversation history or Trello access.
- Recheck validation environment when authorized. Historical Docker startup failure is
  dated evidence, not a current assertion; RF-11 later has healthy container evidence.
- No browser-based visual inspection/screenshot/zoom work unless specifically requested
  by the owner (DEC-034). Record owner visual and real-iPhone gates honestly.
- Report acceptance evidence per item and future consumer gates. Update project state
  only when implementation and independent review support the claimed lifecycle.

## Resolved grooming decisions

- 2026-10-12: Q1A confirmed; My consultations is fourth primary destination, preserving
  Home default and future community role (DEC-036).
- 2026-10-12: owner approved the proposed coherent list/detail/Private-link/minimum-finalized
  increment and plan finalization in response to the explicit approval question.
- No material product question remains. Routine route/schema/cursor/component/date/resource
  choices are specified here under the owner's technical delegation.
- Votes/results/finalization/deletion/physical published purge/recipient sharing remain
  named dependencies; no fake action or count is shipped.
- Accepted immutable publication, temporary preparation, registered audiences, no expiry/
  reopening, minimum finalized retention and no photo buffer remain unchanged.
- Harness launch remains a separate subsequent authorization.

## Remaining questions

None
