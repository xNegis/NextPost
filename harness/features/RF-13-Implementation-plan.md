# RF-13 - Delete an owned consultation - Implementation Plan

## Status

`Ready for implementation`

The product owner approved the settled RF-13 scope, plan finalisation and autonomous harness launch
on 2026-10-20 after confirming every material grooming choice, `1A` through `12A`. Implementation
must remain limited to voluntary author deletion and must consume, not replace, RF-37.

## Source ticket

- Trello title: `RF-13 · Eliminar una consulta propia`
- Trello URL: https://trello.com/c/NEYa01VK/16-rf-13-eliminar-una-consulta-propia
- Trello list at intake: `Próximo · completar el MVP`
- Snapshot captured on: `2026-10-20T13:53:08.8789035+02:00`
- Grooming notes: `harness/grooming/RF-13-grooming.md`

## Objective

Allow an authenticated author to deliberately and irreversibly delete an owned open or already
finalized consultation after a clear, accessible, state-specific confirmation. The successful
database commit must immediately remove every consultation, photograph, direct-link, Private-link,
live-result and raw-vote access path. Physical image deletion then converges through RF-37 without
ever reopening access.

Deleting an open consultation discards all votes and produces no final selection, match, aggregate
snapshot or participant outcome. Voluntary deletion after finalization must preserve the fact that
finalization won its original terminal transition and may preserve only the future minimum private,
photo-free outcomes allowed by DEC-023. Deleted consultations disappear from My consultations and
have no archive, tombstone, trash or undo surface.

## Context and current behaviour

- `ConsultationState` currently contains `open`, `finalized`, `deleted` and `removed`.
  `backend/app/consultation_lifecycle.py` allows `open` to transition to one terminal state, treats an
  exact same-target retry as idempotent and rejects every transition between different terminal
  states. DEC-033 requires the first terminal writer that locks, validates and commits to win.
- RF-13 also has a binding requirement to delete an already-finalized consultation. DEC-042 resolves
  the apparent conflict: open author deletion writes `state=deleted`; later voluntary withdrawal of
  a finalized consultation preserves `state=finalized` and writes an irreversible
  `author_deleted_at` marker. It does not reinterpret or undo finalization.
- `Consultation` currently stores owner, user text, audience, lifecycle, publication/source-session
  data, fingerprint and Private-link generation/state. Its open-completeness constraint permits
  content/source-session detachment only after terminal state.
- `ConsultationPhoto` provides stable option identity and ordinal independently from its nullable
  image-ledger association. `Vote` references the stable option and has a unique
  consultation/voter identity with restrictive foreign keys.
- Vote submission locks `Consultation FOR UPDATE`, rechecks strict open-state authorization and
  commits under that lock. A deletion writer using the same lock therefore serializes with voting.
  RF-18 live author counts are derived from current `Vote` rows and create no final snapshot.
- RF-37 is implemented. `mark_media_for_erasure` is an open-consultation, transaction-local helper
  that deactivates the Private capability and marks every object in the unique consumed source
  session deletion-pending without committing or touching the filesystem.
  `sanitize_terminal_content` removes disallowed consultation text/audience/fingerprint/link data.
  `reconcile_terminal_media` provides verified, idempotent, retryable post-commit deletion,
  detachment and visual-ledger minimization.
- FastAPI startup, hourly maintenance and a restricted manual command already reconcile terminal
  media under PostgreSQL maintenance leadership. Total or partial storage failure retains sanitized
  retry metadata and never changes terminal access.
- RF-12 exposes owner-only `open` and `finalized` tabs through
  `GET /api/my-consultations`, plus owner detail. SQL filters by authenticated owner and lifecycle.
  `deleted` and `removed` are already omitted; finalized list/detail exposes only ID, state and
  publication date.
- Feed, direct entry, consultation detail, photo content, Private-link management, vote status,
  vote submission and live results all re-read current lifecycle. Shared/direct/media/vote paths
  require `open`; unknown, foreign and terminal targets use generic unavailability. Private reads
  carry `private, no-store`, `nosniff` and `no-referrer` headers.
- Cookie-authenticated mutations use `require_trusted_origin`. A configured Origin is accepted,
  hostile and `null` Origins are rejected, and an absent Origin retains current same-site/non-browser
  behavior. Ownership always comes from the signed session, never a request owner field or link.
- The React application uses local primary-navigation and consultation-route state. My consultations
  owns its tab, pagination, refresh and nested owner detail. `OwnerConsultationDetail` already has
  open and minimal finalized branches and is also reused after publication, from Home and through
  direct owner entry. It has no deletion control or reusable destructive dialog.
- Alembic head is `20261019_0006_media_erasure.py`. Compose has separate PostgreSQL and private-photo
  volumes; only the backend mounts photo storage. Alembic runs before Uvicorn and cleanup runs before
  the API starts accepting traffic.
- DEC-041 defines the reusable erasure contract. DEC-042 settles RF-13 lifecycle, visibility,
  minimization, expected-state and post-commit behavior. DEC-043 settles API, UX, navigation,
  observability, migration, validation and adjacent-ticket boundaries.

## Scope

### In scope

- Owner-only voluntary deletion of an open or already-finalized consultation.
- An additive `author_deleted_at`-style marker and required indexes/constraints. Open deletion also
  writes canonical lifecycle `deleted`; finalized withdrawal keeps lifecycle `finalized`.
- One consultation-row-locked transaction that proves ownership and expected state, resolves exact
  retries, consumes RF-37, removes raw votes, sanitizes disallowed content, records deletion and
  commits once.
- No-outcome deletion for open consultations and preservation only of future DEC-023 minimum
  photo-free records after finalization.
- Immediate exclusion from My consultations and generic unavailability for all consultation-backed
  detail, direct-link, Private-link, media, live-result and vote paths.
- A strict authenticated owner-management API with trusted-Origin protection and explicit
  expected-state concurrency proof.
- A state-specific accessible destructive-confirmation dialog in every owner-detail variant,
  including pending, conflict, unavailable, failure and exact-retry behavior.
- Post-success return to My consultations on the state tab from which the deletion was confirmed,
  transient success announcement and authoritative list refetch.
- Sanitized structured observability and complete unit/API/frontend/migration/real-PostgreSQL/
  storage-fault/Docker/restart/recovery validation.

### Out of scope

- Finalizing a consultation or declaring one, several or no photographs.
- RF-19/RF-20 final selections, finalized aggregate snapshots, match calculation or participant
  outcome creation.
- RF-21 complete participation history or any new participant result screen.
- RF-32 administrator authorization or removal action, public moderation, reports, suspension,
  evidence retention or an administrator console.
- Account deletion or anonymization.
- Trash, undo, recovery, reopening or a deleted-consultation/tombstone view.
- Photograph archives, analytics/model copies, moderation copies, new originals, thumbnails,
  derivatives, versions, public URLs or backups.
- A broker, worker service, general queue, general idempotency-key table or operation ledger.
- Removing copies saved externally by third parties.
- Unrelated navigation, result, voting, sharing, profile or product changes.
- Commit, push, deployment, Trello mutation or destructive work on ordinary project data/volumes.

## User experience

Every successfully loaded owned open or finalized detail exposes a destructive
`Delete consultation` action. It is not offered on reader detail, generic unavailable screens or an
administratively removed consultation. Activating it opens an accessible dialog; it does not mutate
immediately.

For an open consultation, the dialog title is `Delete consultation?` and its description must state
in plain English that access ends immediately, every photograph is permanently scheduled for
deletion, all votes are discarded without creating a result, and the action cannot be undone.

For a finalized consultation, the same title must use a distinct description stating that the
consultation will disappear from My consultations, photographs remain unavailable, only minimum
private photo-free participant outcomes may remain, and the action cannot be undone. The copy must
not imply that RF-13 creates, displays or changes those outcomes.

The dialog provides `Cancel` and `Delete consultation`. Initial focus is on the safe action. Focus is
contained while open and restored to the trigger after cancel. Escape cancels while no mutation is
pending. The dialog has an accessible name and description, visible focus, keyboard operation,
screen-reader-compatible status/error announcements and a narrow/mobile layout without overflow.
Do not require typed confirmation and do not use `window.confirm`.

After confirmation, the destructive action is disabled and reads `Deleting…`; duplicate pointer,
keyboard or touch activation cannot start another request. Cancel/close behavior must not suggest
that an in-flight request can be undone.

- On success, close/unmount detail, return to My consultations on the originating lifecycle tab,
  remove the row only after confirmed server success, refetch that tab and announce
  `Consultation deleted`. A direct, Home or publication-success owner detail also returns to My
  consultations on the matching tab. There is no deleted-detail receipt.
- On a network or unexpected pre-commit failure, retain the consultation and usable dialog, show
  `Could not delete the consultation. Try again.`, restore retry capability and avoid optimistic row
  removal.
- On `409 consultation_conflict`, explain that the consultation changed, reload authoritative owner
  detail, and require a new confirmation with the new state-specific warning. Never automatically
  convert an open confirmation into finalized withdrawal.
- On `404 consultation_unavailable`, leave no stale management controls and use the existing safe
  unavailable behavior; return/refetch My consultations as appropriate.
- On `401`, clear private UI state and return through the existing session-lost flow.
- Browser history or an old Public/Private URL does not restore access. A fresh direct entry after
  commit resolves to generic unavailable.

## Functional requirements

### FR-1 - Persist voluntary author deletion without rewriting finalization history

Add a nullable UTC `author_deleted_at` marker to `Consultation` (or an equivalently explicit name).
It identifies a successfully committed voluntary author deletion for both supported source states.

- Open author deletion sets `state=deleted` and `author_deleted_at=<server time>`.
- Finalized author deletion preserves `state=finalized` and sets the marker.
- The marker is irreversible through RF-13. No application path clears it.
- A non-null marker is valid only with `state in (deleted, finalized)`. Preserve compatibility with
  existing terminal fixtures; do not invent historical author-deletion markers for them.
- `removed` remains distinct administrator-owned history and is never converted or marked by RF-13.
- The model must continue to distinguish a finalized-but-visible consultation from a finalized and
  voluntarily withdrawn consultation.

### FR-2 - Authorize and serialize one database transaction

The deletion service must load the target consultation with `SELECT ... FOR UPDATE`, then derive all
decisions from the locked current row. It must:

1. authenticate through the existing signed session;
2. require `consultation.owner_id == current_account.id` without accepting client ownership data;
3. compare the locked current lifecycle with the strict request `expected_state`;
4. resolve an exact already-committed author deletion as idempotent success;
5. reject a different current state as a safe conflict;
6. perform every applicable RF-13 and RF-37 database effect; and
7. commit once before any fallible physical storage work.

Use the same consultation-row lock order as vote submission and future terminal writers. Do not add
priority rules, advisory product locks or a general operation ledger.

### FR-3 - Exact retry and conflict identity

The natural operation identity is authenticated owner + consultation + confirmed expected state,
proven by lifecycle and `author_deleted_at`:

- `expected_state=open` against this owner's already marked `state=deleted` row is exact replay and
  succeeds without repeating destructive effects.
- `expected_state=finalized` against this owner's finalized row with the marker is exact replay and
  succeeds without repeating effects.
- A finalized unmarked row reached by a request confirmed as open is a `consultation_conflict`; the
  request must not silently perform post-finalization withdrawal.
- A wrong expected state against another completed form is conflict, not a new deletion.
- Unknown, foreign and `removed` rows collapse to generic unavailable. Do not reveal ownership,
  administrative removal or whether an inaccessible UUID exists.

First success and exact replay return `204 No Content`. They expose no timestamp, deleted content,
vote count, outcome, storage key, retry state or erasure progress.

### FR-4 - Delete an open consultation without creating outcomes

While holding the locked open consultation:

- call RF-37 `mark_media_for_erasure` inside the same transaction;
- delete every raw `Vote` for the consultation explicitly;
- do not call RF-18 aggregation to persist counts and do not create a winner, declaration, match,
  no-choice record, participant outcome or finalized snapshot;
- call RF-37 terminal sanitization so question, context, audience, publication fingerprint and
  Private-link capability cannot survive as an archive;
- write lifecycle `deleted` and the author-deletion marker; and
- commit all effects atomically.

If any database/precondition operation fails, roll back the entire transaction. The consultation
must remain open and usable according to its previous committed state; do not leave images marked,
votes partially deleted or links partially changed.

### FR-5 - Withdraw a finalized consultation while preserving only DEC-023 data

For a locked finalized row without an author-deletion marker:

- retain lifecycle `finalized`;
- preserve any compliant future declared stable option IDs or explicit no-selection declaration,
  aggregate counts and per-participant private `Matched`/`Not matched`/`No choice` outcomes;
- never calculate, synthesize, edit or expose those records in RF-13;
- remove any residual raw `Vote` choices and sanitize all disallowed consultation content and link
  capability so only the DEC-023/DEC-041 allowlist remains;
- write `author_deleted_at` and commit once.

Compliant RF-19/RF-20 finalization will already have invoked RF-37 and removed visual access. A
legacy finalized row that still has media/source-session references remains inaccessible and must be
converged by existing RF-37 reconciliation. Do not bypass RF-37 internals, guess filesystem paths or
make finalized deletion depend on synchronous storage success.

### FR-6 - Immediate read and link invalidation

After commit:

- open deletion is denied by canonical terminal lifecycle everywhere;
- finalized withdrawal is omitted from My consultations list/detail through an explicit
  `author_deleted_at IS NULL` predicate;
- shared/direct detail, photo, link, vote and live-result paths remain denied by strict lifecycle;
- old Private tokens, link generations, browser URLs and cached UI state grant no authority;
- no authorization beginning after commit may read consultation content or photo bytes.

Maintain request-time semantics from DEC-029/041: a response authorized before commit may finish,
and externally saved bytes cannot be recalled. Do not add long read locks, client polling or claims
that already downloaded copies were removed.

### FR-7 - Consume RF-37 durable physical erasure

RF-13 must be the first production terminal consumer of RF-37's public service seam. Open deletion
must call the transaction-local marker rather than reproduce image state mutations. Physical file
deletion remains outside the product transaction and is owned by RF-37 startup/hourly/manual
maintenance.

The API reports success once the database commit succeeds. Total, partial, delete-verification or
filesystem failures after commit are operational retry conditions, not user-visible deletion
failure. They retain only RF-37's bounded sanitized retry references, remain inaccessible and
converge idempotently after maintenance or restart. Do not expose `202`, progress polling or a
user-visible `deleting` state.

### FR-8 - Keep owner lists and pagination coherent

`list_my_consultations` and `read_my_consultation` must exclude every row with a voluntary-deletion
marker, including finalized rows whose lifecycle alone would otherwise qualify. Filtering happens
in SQL before ordering, pagination and projection. A withdrawn row must not leave a short/duplicate
page, reappear through a previous cursor or load full content before the marker is checked.

The frontend may remove the current item only after `204`, then must refetch the relevant tab.
Pagination deduplication and periodic refresh must not resurrect it from stale local state. If the
last row disappears, render the existing correct empty state.

### FR-9 - Accessible destructive control

Implement the user experience above as a reusable repository-owned React dialog/control, with no
new component dependency unless already justified by the repository. Cover focus placement,
containment and restoration; Escape/cancel; labelled/described semantics; pending lockout; live
status/error messages; narrow viewport, safe-area and zoom behavior; and both state-specific texts.

The owner detail must pass the exact state displayed into the API request. A state change response
must reload before a new confirmation. Never reuse stale open wording to remove a finalized row.

### FR-10 - Sanitized observability

Emit structured, restricted logs/counters sufficient to diagnose the consumer boundary: operation
outcome, consultation ID, previous lifecycle, first/replay/conflict/error classification, number of
raw votes removed and number of images RF-37 marked. Continue using RF-37 pending/completed/failed/
overdue reporting for physical erasure.

Never log question, context, audience capability/token, request cookie, storage key/path, image data,
individual voter/account choice, exception text containing sensitive data or deleted payloads.
Consultation IDs are operational metadata and remain subject to ordinary restricted log access and
retention. Do not add a product analytics event containing deleted content.

## Technical approach

Add a focused deletion operation to the consultation domain/application boundary, leaving the API
route thin. It owns authorization, expected-state comparison, lifecycle-specific minimization and
the single commit. Reuse `decide_transition` for the open-to-deleted decision where applicable, but
do not change it to permit `finalized -> deleted`: the finalized path is a separate irreversible
withdrawal marker and leaves lifecycle unchanged.

Use RF-37's exported marker and sanitizer rather than updating `PhotoUploadImage` directly. Delete
raw votes explicitly under the consultation lock. Keep physical storage outside the request's
database transaction and rely on the existing reconciliation loop.

### Affected areas

- Frontend:
  - `frontend/src/consultationApi.ts` and focused API tests for strict delete request/response/error
    handling.
  - `frontend/src/OwnerConsultationDetail.tsx` and tests for open/finalized deletion entry points,
    state-specific confirmation and pending/error/conflict behavior.
  - A small reusable destructive dialog/hook if that keeps focus and request state explicit.
  - `frontend/src/MyConsultations.tsx`, `frontend/src/App.tsx` and their tests for returning to the
    correct tab, authoritative refresh, transient success and direct/Home/success variants.
  - `frontend/src/styles.css` for accessible destructive styling and responsive dialog layout.
- Backend/application:
  - `backend/app/consultation_service.py` or a focused deletion service for the locked transaction,
    minimization, idempotency and logs.
  - `backend/app/api/consultations.py` for the owner action and trusted-Origin/error mapping.
  - `backend/app/schemas.py` for the strict expected-state request.
  - Existing RF-37, lifecycle, access and vote services as reused dependencies, not duplicated paths.
- Domain/data model:
  - `backend/app/models.py` and one new Alembic revision after `20261019_0006`.
  - New/focused unit, API, migration and real-PostgreSQL tests.
- Storage/background work:
  - No new worker or storage implementation. Reuse `photo_erasure_service.py`, `cleanup.py` and
    existing startup/hourly/manual maintenance; extend regression tests only where needed to prove
    the real consumer.
- Configuration/deployment:
  - No new setting or service. Existing deletion alert interval, private volume and maintenance
    leadership remain authoritative.
- Documentation:
  - Update `harness/context/04_PROJECT_STATE.md` only when supported by implementation/validation
    evidence. Update operator/user documentation only where RF-13 changes an existing documented
    contract.

### Data and migration requirements

Create an additive Alembic revision; never edit `20261019_0006_media_erasure.py`.

- Add nullable timezone-consistent `consultations.author_deleted_at`.
- Add a database check that a non-null marker is compatible only with `deleted` or `finalized`.
  Do not require every historical `deleted` row to have a marker.
- Add or adjust an owner/state/marker/publication ordering index if query plans require it so both My
  consultations tabs filter before stable `(published_at DESC, id DESC)` pagination.
- Existing open and finalized rows receive `NULL` and remain visible. Existing deleted and removed
  rows remain excluded through lifecycle. Do not infer or backfill voluntary deletion history.
- Preserve current open-completeness, media-detachment, Vote foreign-key and RF-37 constraints.
- Migration tests must cover fresh head, upgrade from `0006`, preserved open/finalized content,
  compatible historical terminal fixtures, invalid marker/state combinations and indexes.
- Downgrade must refuse once any irreversible author-deletion marker is populated. If unused, it may
  remove only the additive RF-13 schema. It cannot recreate sanitized content, votes or images.

### API and integration requirements

Add:

`POST /api/my-consultations/{consultation_id}/delete`

Strict JSON request:

```json
{"expected_state":"open"}
```

where the only accepted values are `open` and `finalized`; reject missing, extra or invalid fields
through the existing bounded validation envelope.

- Require current authenticated account and `require_trusted_origin`.
- Do not accept an owner/account ID, timestamp, media identifier, deletion key or Private token.
- Return `204 No Content` for first success and exact same-state replay.
- Return `401` through the existing session boundary.
- Return `403 origin_not_allowed` for hostile or `null` Origin according to current policy.
- Return generic `404 consultation_unavailable` for missing, foreign or `removed` targets.
- Return `409 consultation_conflict` when the locked current lifecycle/marker proves the submitted
  expected state is stale or describes a different completed form.
- Set private no-store/nosniff/no-referrer headers consistently on the mutation response and errors.
- Never return deleted content, owner identity, vote/result information, storage status or whether a
  foreign UUID exists.

The frontend runtime validator must accept only the specified empty success and safe error envelope.
It must not treat a malformed `2xx` response as success.

### Security and privacy

- Signed-cookie authentication and locked server-side ownership are mandatory. A Public audience,
  valid Private capability, former author page, URL knowledge or client state never grants deletion.
- Trusted-Origin validation is required in addition to CORS and SameSite cookie behavior.
- Treat IDs and expected state as untrusted bounded input; use ORM parameters and existing UUID/
  Pydantic validation.
- Acquire the consultation lock before lifecycle-sensitive destructive work. Preserve the shared
  vote/terminal lock order to prevent late votes and deadlocks.
- Commit logical revocation before physical storage work. A storage exception cannot roll back,
  reauthorize or mutate lifecycle.
- Sanitize all disallowed text/link/fingerprint/raw-choice data. Preserve only the DEC-023/041
  allowlist and bounded retry metadata.
- Storage stays outside public roots. Do not expose keys, paths, tokens, image metadata or cleanup
  internals in API, frontend, logs or analytics.
- An already authorized response or externally saved file cannot be recalled. Product copy must not
  promise removal of third-party copies.
- Never turn a withdrawn finalized result into an author-visible result/archive. Future participant
  outcomes remain separately authorized and private to that participant under RF-21.

## Implementation sequence

1. Add the RF-13 Alembic revision, ORM marker and database invariants/indexes with migration tests.
2. Add focused deletion domain errors/result types and the row-locked service transaction, reusing
   lifecycle and RF-37 seams.
3. Implement open deletion: marker, vote removal, no outcomes, sanitization, state/marker and one
   commit; prove rollback safety.
4. Implement finalized withdrawal: retain lifecycle/permitted future outcomes, remove residual raw
   choices, sanitize, mark and commit; cover legacy media reconciliation without bypassing RF-37.
5. Update owner list/detail queries to exclude marked rows before pagination/projection and add
   regression tests for generic denial across all existing reads.
6. Add the strict owner API route/schema, trusted-Origin enforcement, safe 204/404/409 mapping,
   headers and sanitized observability.
7. Add real PostgreSQL races for delete versus vote/finalize/delete and storage-fault/restart tests
   that exercise RF-13 as RF-37's real consumer.
8. Add the strict frontend API operation and state-specific accessible confirmation with pending,
   conflict, unavailable, session-loss and retry behavior.
9. Integrate deletion across every owner-detail variant and return/refetch My consultations on the
   originating tab with transient live-region success.
10. Add frontend accessibility/responsive/navigation/list-consistency tests and perform focused
    manual mobile/keyboard/zoom validation.
11. Run the complete validation matrix, inspect the actual diff against every acceptance criterion
    and update project state only with supported evidence.

## Validation strategy

### Automated tests

Backend unit/service/API coverage must prove:

- open and finalized first deletion, exact replay and wrong-state conflict;
- owner-only authorization, generic foreign/missing/removed handling and strict request validation;
- hostile/null/trusted/missing Origin behavior consistent with existing mutation policy;
- open vote deletion with no declaration/result/outcome and finalized preservation of only the
  permitted seam;
- full rollback when any pre-commit service/RF-37/database step fails;
- immediate denial/omission across My consultations, feed, owner/reader/direct detail, photo,
  Private-link, live-result, vote-status and vote-submit routes;
- sanitized log fields and absence of content/token/key/individual-choice data;
- RF-37 total/partial storage failure after commit, exact retry, maintenance retry and eventual
  verified detachment without access restoration;
- additive migration, constraints/indexes, preservation, no backfill and downgrade refusal.

Real PostgreSQL coverage must coordinate deterministic concurrent sessions/threads and prove:

- vote commits first, then open deletion removes it without outcome;
- deletion commits first, then vote is denied;
- deletion of open commits first, then finalization loses safely;
- finalization commits first, then stale `expected_state=open` deletion conflicts and does not mark
  withdrawal;
- a newly confirmed `expected_state=finalized` request can then withdraw it;
- identical concurrent deletes yield one destructive commit and idempotent success;
- no deadlock, duplicate outcome, partial vote set or late access occurs.

Frontend coverage must prove:

- the destructive action appears only for owned open/finalized detail variants;
- exact open/finalized warning copy and no typed/native confirmation;
- dialog name/description, initial focus, focus containment/restoration, Escape/cancel, visible focus,
  pending lockout and live announcements;
- duplicate click/touch/keyboard activation emits one request;
- network/server retry, session loss, generic unavailable and conflict/reload/new-confirmation flows;
- successful return to the correct tab from My/Home/direct/success variants, row removal only after
  success, authoritative refetch, pagination deduplication and correct empty state;
- old object URLs/detail state are revoked on unmount and no stale row reappears.

### Manual validation

- Use disposable accounts, PostgreSQL data and photo volumes only.
- Exercise open deletion with votes and both Public and Private access from separate sessions. Verify
  every fresh route/link/photo/vote/result request fails immediately after commit and files disappear
  through cleanup.
- Exercise a seeded/current finalized consultation and verify it disappears without a photo/archive
  surface while permitted non-visual records remain untouched.
- Inject storage failure, confirm the UI still reports committed deletion, restart the backend,
  restore storage and verify cleanup converges without re-exposure.
- Validate the dialog at 320 px and representative mobile/tablet/desktop widths, portrait and
  landscape where practical, safe areas, 200% zoom, keyboard-only operation, focus order, Escape,
  long translated/system text behavior and no horizontal overflow or obscured actions.
- Check Docker startup migration/cleanup ordering and the supported database-with-empty/current-photo
  recovery rehearsal. Never restore an older image snapshot or use ordinary user volumes.

### Commands

From repository root, with the existing virtual environment:

```powershell
.\.venv\Scripts\python -m pytest backend\tests
.\.venv\Scripts\python -m ruff check backend
.\.venv\Scripts\python -m ruff format --check backend
.\.venv\Scripts\python -m mypy backend\app
```

Run the complete PostgreSQL-dependent suite against an isolated Alembic-upgraded test database by
setting `TEST_DATABASE_URL`; do not point it at ordinary project data.

From `frontend`:

```powershell
npm test
npm run format:check
npm run lint
npm run typecheck
npm run build
npm audit --audit-level=high
```

From repository root:

```powershell
docker compose config --quiet
docker compose build backend frontend
```

Use an isolated Compose project and volumes for migration/startup/restart/storage-failure/recovery
validation. Do not remove or alter the existing RF-37 manual-validation project or ordinary volumes.

## Acceptance criteria

- [ ] Only the authenticated author can delete an owned consultation; a Private link or Public
      visibility never grants mutation authority.
- [ ] An open or finalized consultation can be deleted after the exact accessible state-specific
      confirmation, and the action cannot be undone or reopened.
- [ ] Open deletion writes `deleted`; finalized withdrawal preserves `finalized` plus the irreversible
      author-deletion marker.
- [ ] The item disappears from My consultations immediately after successful refetch and no deleted
      tab, tombstone, archive, recovery or progress surface exists.
- [ ] Open deletion removes every raw vote and creates no final selection, aggregate, match or
      participant outcome.
- [ ] Finalized withdrawal preserves only future DEC-023 minimum private photo-free outcomes and
      removes/sanitizes every disallowed content, capability and residual raw choice.
- [ ] Consultation lock, expected state and persisted operation identity make exact retries
      idempotent and stale/different terminal requests conflict safely.
- [ ] A vote/finalize/delete race has exactly the behavior of the first committed writer; an open
      warning never silently authorizes deletion of a newly finalized consultation.
- [ ] The winning database transaction atomically revokes access, consumes RF-37, deletes/minimizes
      the correct data and commits once; pre-commit failure rolls everything back.
- [ ] Every fresh owner/reader/direct/link/photo/live-result/vote authorization is denied after
      commit, while the accepted already-authorized-response and third-party-copy limitation remains
      accurately documented.
- [ ] Physical deletion is verified and retryable through RF-37. Total, partial or restart-time
      storage failure never reopens access or turns committed deletion into user-visible failure.
- [ ] First success and exact replay return 204; missing/foreign/removed are generic 404; stale state
      is safe 409; no response exposes deleted content, ownership or cleanup state.
- [ ] Trusted-Origin, strict payload, private no-store headers and server-side ownership are covered
      by tests.
- [ ] The dialog is keyboard-, screen-reader-, zoom- and mobile-usable, prevents duplicate submit and
      leaves the user in a usable state on every pre-commit failure.
- [ ] Success returns to the matching My-consultations tab, announces deletion and reconciles server
      state without stale-row resurrection.
- [ ] Logs and counters are operationally useful and contain no user text, token, key, image or
      individual vote choice.
- [ ] Migration preserves existing open/finalized rows without synthetic backfill, keeps historical
      terminal compatibility and refuses unsafe downgrade after irreversible use.
- [ ] Unit, API, frontend, migration, real-PostgreSQL concurrency, storage-fault, Docker, restart and
      supported recovery validation pass on isolated resources.
- [ ] RF-19/RF-20, RF-21 and RF-32 behavior remains outside the implementation.

## Dependencies and ordering

- RF-07 private normalized storage and temporary cleanup remain unchanged.
- RF-09/RF-10 current request-time authorization, protected reads and publication ownership remain
  the access foundation.
- RF-11/DEC-033 supplies the canonical open-terminal lifecycle/race contract. RF-13 does not legalize
  transitions between terminal lifecycle values.
- RF-12 supplies My consultations list/detail/navigation and must filter the new marker coherently.
- RF-16 supplies raw votes and shared row-lock serialization.
- RF-18 supplies live open aggregates only; RF-13 must not convert them into finalized data.
- RF-26 direct/Private link entry must fail from current server state after deletion.
- RF-37/DEC-041 is implemented and mandatory. RF-13 is its first real terminal consumer.
- Coordinated RF-19/RF-20 follows RF-13 and will populate the DEC-023 seams; RF-13 must remain
  forward-compatible without implementing them.
- RF-21 later consumes only each participant's minimum private finalized outcome.
- Restricted RF-32 later uses RF-37 with distinct `removed` lifecycle and administrator authority.

## Risks and mitigations

- **Dual deletion representation:** open deletion is `deleted`, finalized withdrawal is a marker over
  `finalized`. Mitigate with DEC-042, explicit model names/checks, centralized service/query helpers
  and tests across every owner projection.
- **Stale confirmation changes consequences:** finalization may win after an open detail loads.
  Mitigate with strict `expected_state`, the row lock, 409/reload and a new state-specific confirm.
- **Late votes or duplicate terminal work:** concurrency can interleave destructive operations.
  Mitigate with the existing shared consultation lock order, natural operation identity, database
  constraints and deterministic real-PostgreSQL races.
- **Partial logical deletion:** vote/media/content changes must not commit separately. Mitigate with
  one service-owned transaction and injected pre-commit rollback tests.
- **Storage outage after commit:** bytes may remain privately stored. Mitigate with immediate logical
  revocation, RF-37 durable retry/verification, overdue alerting, restart/recovery tests and no
  rollback/reopen path.
- **Over-retention:** current/future raw text, votes or storage metadata could survive. Mitigate with
  lifecycle-specific allowlists, sanitizer use, residual-vote deletion and database assertions.
- **Outcome destruction:** post-finalization deletion could remove RF-19/RF-20 records. Mitigate by
  treating DEC-023 tables as preservation-only dependencies and adding forward-facing contract tests
  when those schemas arrive.
- **Enumeration or CSRF:** destructive endpoint could reveal or mutate another user's object.
  Mitigate with signed session, locked ownership, generic 404, trusted-Origin checks, strict payload
  and no client-supplied owner/link authority.
- **Stale frontend state:** rows/photos can linger after commit. Mitigate by awaiting 204, unmounting
  detail/object URLs, selecting/refetching the originating tab and testing pagination/refresh races.
- **Inaccessible destructive UI:** custom dialogs commonly mishandle focus/mobile layouts. Mitigate
  with explicit semantic/focus requirements, automated interaction tests and manual narrow/zoom/
  keyboard review.
- **Migration rollback fiction:** irreversible data cannot be reconstructed. Mitigate with additive
  compatibility, no backfill and downgrade refusal after first marker use.

## Harness handoff notes

- The worktree intentionally contains uncommitted RF-13 grooming/decision/project-state/plan
  documentation. Preserve it exactly and build on it; do not reset, revert or overwrite it.
- At launch the known RF-13 documentation changes are:
  `harness/grooming/RF-13-grooming.md`, `harness/features/RF-13-Implementation-plan.md`,
  `harness/context/03_DECISIONS.md` and `harness/context/04_PROJECT_STATE.md`.
- The existing isolated `nextpost-rf37-manual` Compose stack and dedicated data were intentionally
  left running for prior owner validation. Do not stop, remove, reuse or mutate it. Use a separately
  named disposable Compose project/volumes for RF-13 validation.
- Inspect current code before choosing whether to extend `consultation_service.py` or add a focused
  deletion module. Preserve the accepted boundaries either way; do not create speculative general
  abstractions.
- No real RF-19/RF-20 outcome tables exist. Implement preservation-compatible seams and current
  finalized fixtures only; do not invent final result product behavior.
- Do not commit, push, deploy, mutate Trello or operate on ordinary user data/volumes.
- Automated evidence does not replace the product owner's later visual/mobile review. Report manual
  checks still requiring the owner rather than claiming them complete.

## Resolved grooming decisions

- `1A`: open deletion uses `deleted`; post-finalization withdrawal preserves `finalized` plus an
  irreversible author-deletion marker.
- `2A`: deleted consultations disappear from My consultations with no tombstone/archive.
- `3A`: lifecycle-specific data allowlists remove open votes/outcomes and preserve only future
  DEC-023 photo-free minimum data after finalization.
- `4A`: strict expected-state row locking provides exact idempotency and safe terminal conflicts.
- `5A`: database commit is user success; RF-37 owns retryable physical convergence.
- `6A`: use a strict trusted-Origin owner-management POST action with no client owner/link authority.
- `7A`: use a state-specific accessible dialog without typed/native confirmation.
- `8A`: return to/refetch the originating My-consultations tab after success.
- `9A`: emit only sanitized structured deletion/cleanup events and counters.
- `10A`: additive nullable marker, no historical backfill and downgrade refusal after use.
- `11A`: require the complete unit/API/frontend/PostgreSQL/storage/Docker/restart/recovery matrix.
- `12A`: keep RF-13 separate from RF-19/RF-20, RF-21 and RF-32.

## Remaining questions

None
