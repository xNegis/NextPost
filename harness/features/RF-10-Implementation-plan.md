# RF-10 - Publish a consultation - Implementation Plan

## Status

`Ready for implementation`

The product owner resolved the material grooming questions and explicitly requested this plan on
2026-09-28. This finalises the RF-10 implementation contract. It does not authorize the external
harness, a commit, push, deployment or Trello mutation.

## Source ticket

- Trello title: `RF-10 · Publicar una consulta`
- Trello URL: https://trello.com/c/gMQwBaFB/4-rf-10-publicar-una-consulta
- Trello list at intake: `Fase 2`, on the configured `APP - NextPost` board
- Snapshot captured on: 2026-09-28, before coordinator checkpoint `2026-09-28T14:30:12Z`
- Last Trello activity at intake: `2026-09-22T14:34:57.786Z`
- Grooming notes: `harness/grooming/RF-10-grooming.md`

## Objective

Turn one reviewed temporary comparison into exactly one durable open consultation. Ordered
processed photos, normalized question/context and explicitly chosen audience become immutable in
one database transaction. Private publication creates its current shareable link in that same
transaction. Retries and double activation return the same consultation rather than creating a
duplicate, and no partial consultation or partially promoted image set becomes visible.

Published consultations and photos survive app close/reopen and ordinary service restart through
PostgreSQL and the existing private photo volume. The POC adds no image backup, versioning or special
disaster recovery (DEC-032). Unpublished preparation remains temporary (DEC-012/026).

## Context and current behaviour

- RF-07 implemented owner-bound upload sessions, normalized private images, lease renewal,
  discard/abandon cleanup and `validate_publication_images`. It has no consumed/published state;
  temporary reads are owner-only. `PhotoUploader` exposes ready IDs but not its session ID and
  currently discards its session on unmount.
- RF-08 implemented matching frontend/backend question/context normalization and configurable
  120/500 defaults. It has no persistence or publication route.
- RF-09 implemented canonical Public/Private values, an authoritative access policy, versioned
  Private-link capabilities and reusable frontend controls. It deliberately created no Consultation
  table or live route; RF-10 must persist and enforce those rules.
- `backend/app/models.py` currently contains Account, PhotoUploadSession and PhotoUploadImage.
  Alembic ends at `20260922_0003_photo_uploads.py`. No consultation, ordered option, publication
  endpoint, owner link endpoint or published-media route exists.
- Cleanup currently understands temporary upload state only. Discard, abandonment, image removal
  and orphan sweep must all be made safe for promoted files.
- The frontend still has Home/Profile local navigation and no composer, consultation route, feed,
  vote or results screen. RF-06 later integrates the full product editor/preview journey.
- DEC-013/017/018/022/024/027–032 and the approved RF-07/08/09 plans are binding inputs.

## Scope

### In scope

- Consultation persistence with immutable normalized text, audience, owner, open lifecycle,
  publication time, source upload session and current Private-link state.
- Ordered consultation-photo associations reusing the existing normalized file objects; no file
  copy, rename or reprocessing during publication.
- Atomic validation and promotion of selected ready images, with cleanup of unselected temporary
  images and protection of promoted images from temporary cleanup.
- One successful publication per owner-bound upload session. Duplicate clicks and manual Retry of
  the same normalized payload return the same consultation.
- Transactional enforcement of the configurable maximum open consultations under concurrency.
- Authenticated published-detail and per-photo reads using RF-09 access checks on every request.
- Owner-only current-link retrieval and disable/replace/create-new endpoints using generation
  preconditions and the existing RF-09 transitions.
- Advisory current-owner capacity read for RF-06's early guidance; it reserves no slot.
- Reusable frontend publication state and uploader handoff: expose session ID, freeze while sending,
  prevent repeated activation, Retry the same submission and relinquish promoted uploads safely.
- One reusable preview confirmation showing audience reach, immutability and no automatic expiry.
- Alembic migration, PostgreSQL concurrency/security tests, built-stack smoke and documentation.

### Out of scope

- RF-06's complete composer, product navigation and routing.
- RF-12 owner list, RF-14 feed, RF-16 voting, RF-18 results, RF-19/20 finalization/final choice,
  RF-21 history and RF-26's complete share/authentication-return journey.
- Author deletion, administrator removal and physical deletion of published photos. Later services
  must use the lifecycle/file ledger introduced here; terminal-state denial tests do not claim those
  operations implemented.
- Fake result/share controls, anonymous access, editable publication, drafts/autosave, automatic
  expiry, recipient allowlists, multiple recipient links or a publication recovery screen.
- Backups, photo versioning, object storage, CDN, worker/queue, custom native links, native project
  generation, signing or TestFlight.

## User experience

1. RF-06 will keep the uploader mounted through edit and preview. The summary states who can see the
   photos, that published content cannot be edited and that the consultation does not expire. The
   author can return to edit.
2. One `Publish consultation` action is the final confirmation. Disable it while pending; do not add
   a second dialog.
3. Definite field/photo/limit errors preserve the live preparation. If another tab takes the last
   open slot, keep the current form and allow explicit retry after capacity becomes available.
4. Network/server failure shows a concise error and `Try again`. Retry sends the same frozen
   submission. There is no polling, background retry, separate recovery screen or parallel version.
   If the first request committed, Retry returns that consultation instead of duplicating it.
5. Success returns the consultation ID and open state. Private publication also makes its automatic
   current link available through the owner link read. The uploader stops renewal and clears local
   blobs without sending temporary discard for promoted images.
6. Published content remains after app close/reopen and ordinary restart. Catastrophic private-volume
   loss is an accepted POC limitation and creates no recovery promise.
7. Authorized registered readers see complete text and ordered photos. Public allows any registered
   account; Private requires the current link for non-owners. Denied/terminal access uses the generic
   unavailable state; network/storage failure remains retryable.

## Functional requirements

### FR-1 - Persisted consultation and ordered photos

Add records equivalent to:

- `consultations`: UUID, owner FK, normalized question, nullable context, canonical audience,
  lifecycle, `published_at`, unique source upload-session FK, versioned payload fingerprint,
  Private-link generation and active state.
- `consultation_photos`: consultation FK, existing PhotoUploadImage FK and immutable ordinal, with
  unique `(consultation_id, ordinal)` and unique image association.

Use opaque UUIDs and UTC-aware server timestamps. Lifecycle supports at least `open`, `finalized`,
`deleted` and `removed`; RF-10 creates only `open`. Public rows have no active Private capability;
Private rows start generation 1 active. Keep PhotoUploadImage as the single private-file/deletion
ledger. Do not store originals, duplicate derivatives or raw link tokens.

### FR-2 - Consumed upload lifecycle

Extend upload-session state with terminal `consumed` and update ORM plus Alembic constraints. A
consumed session records its consultation and cannot be renewed, uploaded to, discarded, abandoned
or reused.

Selected images remain in the file ledger and are readable only through consultation routes.
Temporary content/remove/discard routes must reject or safely no-op consumed/promoted objects.
Cleanup must preserve promoted keys, revoke and queue unselected temporary objects, and retain
retryable deletion for those revoked objects. Server state is authoritative even if the client
never receives success or crashes before cleanup of its local state.

### FR-3 - Atomic publication

Expose an authenticated JSON endpoint accepting upload-session UUID, ordered unique image UUIDs,
question, optional context and audience. For a new publication, one transaction must:

1. derive owner only from the verified cookie and lock the author for cap serialization;
2. lock and validate the owned active upload session;
3. validate strict request shape, current RF-08 text rules and RF-09 audience;
4. enforce current photo bounds and open-consultation cap;
5. lock/validate selected ready images, ownership and actual normalized bytes;
6. create the open consultation, ordered associations and initial Private link state;
7. consume the session and durably revoke unselected temporary objects; and
8. commit once.

No helper may commit partial state. Failure before commit leaves no consultation, link, consumed
slot or partial promotion. Physical deletion of leftovers follows durable revocation through the
existing cleanup path. Historical failed/revoked attempts need not be selected; every selected ID
must be ready. RF-06 blocks visible pending/failed items, while the server remains authoritative.

### FR-4 - Simple idempotent Retry

Use source upload-session UUID as the publication operation identity and enforce one consultation
per source session. Store a versioned fingerprint over canonical ordered IDs, normalized text and
audience.

- Same owner/session and equivalent normalized payload return the existing consultation, including
  after restart or a lost response.
- Changed order/text/audience for a consumed session returns conflict and never edits or duplicates.
- A rolled-back attempt leaves the session active for correction and retry.
- Independent upload sessions remain independent; never deduplicate by image similarity or text.

Resolve an existing success before applying new-publication lease/cap/current-limit rejection. A
Retry must still return its completed consultation after consumption or later limit changes. Return
current authorized state and never reset a later disabled/replaced link. Add no separate status
endpoint, polling or recovery subsystem solely for the POC.

### FR-5 - Concurrent cap enforcement

Count lifecycle `open` consultations against `MAX_OPEN_CONSULTATIONS`; audience and link enabled
state do not change the count. Serialize publications for one author using the Account row or an
equivalent PostgreSQL lock that works when the author has zero consultations. Two sessions racing
for the final slot yield exactly one success. Different authors need not serialize.

Document one lock order for publication and future slot-releasing actions: author/account, then
consultation or upload session, then photos. The advisory capacity endpoint returns open count,
limit and `can_start`, but reserves nothing and never replaces the transactional check.

### FR-6 - Published detail and media access

Provide authenticated detail and photo-content routes. Every request loads current persisted
consultation/lifecycle/link state and verifies the photo belongs to that exact consultation. Build
one RF-09 `AccessSnapshot`, verify a presented token against the same row, and invoke `can_access`.

Detail returns only consultation ID, owner nickname, normalized question/context, audience, open
state, publication time and ordered photo IDs/dimensions. Exclude email, storage keys, raw token,
individual votes and aggregate results. Only the owner link endpoint returns a current Private token.

Media responses use authenticated fetch-to-blob and include `Cache-Control: private, no-store`,
`X-Content-Type-Options: nosniff` and `Referrer-Policy: no-referrer`. Denied/cross-consultation reads
must not touch storage. Missing authorized bytes return retryable unavailability and a safe
operational log; never serve a partial comparison or substitute another photo.

Coordinate reads with link/terminal mutations using a consistent consultation-row lock or equivalent
snapshot. A bounded read authorized before a mutation may finish; requests after committed
revocation fail. Add no polling or promise to recall downloaded bytes (DEC-029).

### FR-7 - Persisted owner link management

For Private open consultations, provide owner-authenticated current-link read, disable, replace and
create-new operations. Use RF-09 transitions, expected generation and a consultation row lock.
Stale/repeated operations conflict without rotating again. Lost response is handled by refetching
current state. Public/terminal consultations cannot mint a Private link; audience is immutable.

Persist RF-09's unsigned 64-bit generation exactly, for example with bounded `NUMERIC(20,0)`, and
serialize it as a decimal string so JavaScript loses no precision. Narrowing the accepted protocol
requires returning to grooming. Never persist raw tokens.

### FR-8 - Frontend publication and uploader handoff

Extend the uploader so its parent can obtain the upload-session ID for publication, freeze changes
while sending and relinquish a consumed session after success. Relinquish revokes local object URLs
and stops lease renewal without calling temporary-session DELETE. Existing discard remains for
actual cancellation.

Add a strict publication client/controller with idle, pending, success and error states. It accepts
one immutable snapshot, prevents duplicate activation and retries the same snapshot manually. HTTP
401 follows existing session loss; field/limit/session/conflict/unavailable remain distinguishable
enough for RF-06 to preserve or clear state correctly.

Provide a controlled summary reusable by RF-06 with existing shared text/photo presentation,
audience reach, immutable/no-expiry copy, one Publish action and return-to-edit callback. It owns no
product route or complete composer.

### FR-9 - Security and mutation protection

Derive owner only from the verified cookie and reject writable owner/lifecycle/link/result/storage
fields. Add an explicit trusted-origin check for state-changing cookie-authenticated consultation
routes and require JSON where applicable; credentialed CORS alone is not CSRF protection. Document
and test hostile, null and missing Origin behavior for browser/native clients.

Keep the RF-09 fragment and `X-NextPost-Private-Link` transport. No token in API URLs, query/body,
logs, configuration, analytics or persistent browser storage. Build links only from the trusted app
origin. Do not expose text/photos in anonymous HTML, metadata, static roots or errors. Do not log
raw question/context, cookies, tokens, keys, filenames or bytes. Bound text/list request work before
database access and treat every frontend response as untrusted.

## Technical approach

Keep handlers thin and transaction/access rules in focused services. Reuse PhotoUploadImage as the
file ledger and associate it with ordered options. Promotion is a database lifecycle transition over
the same bytes, avoiding an impossible database/filesystem atomic move. Use PostgreSQL row locks for
capacity, session/image races and link mutations. Keep processing synchronous with no new service.

### Affected areas

- Backend models/migration: Consultation, ConsultationPhoto, consumed session state, constraints.
- Backend services: new consultation publication/read/link services; refactor
  `backend/app/photo_service.py` for caller-owned transactions and row locks.
- Backend API/schemas: consultation router; reuse `get_current_account`, RF-08 validation and RF-09
  access/link functions.
- Storage/cleanup: update `backend/app/cleanup.py` and every temporary mutation/read path so
  promoted files survive and leftovers remain retryable.
- Backend app/security: router registration and explicit mutation-origin protection.
- Frontend: extend `PhotoUploader.tsx`, `usePhotoUploader.ts`, `photoApi.ts`; add focused publication
  client/controller/summary and connect existing PrivateLinkControls to real API contracts.
- Deployment: no new dependency, secret, volume or service.
- Documentation: README consumer/operation notes and evidence-based project state.

### Data and migration requirements

Add the next Alembic revision after `20260922_0003` with explicit audience/lifecycle/session-state
checks, unique source session, unique photo/ordinal associations, owner/state/date indexes and
coherent Public/Private link constraints. Existing upload rows remain temporary; no existing file
is promoted automatically. Revisit cascades so deleting a consumed upload session cannot erase a
published association or its durable file ledger.

Validate fresh and populated RF-07 upgrades on PostgreSQL. Models and migration constraints must
agree; SQLite `create_all` is insufficient. Do not run old cleanup code against promoted data:
deploy migration/backend/cleanup compatibility together with maintenance stopped during transition.

Downgrade with published rows is unsafe because old cleanup cannot protect them. Refuse it clearly
unless the database is isolated/disposable and has no published rows, or require an explicit later
withdrawal/purge operation. Never silently drop references/files. Database rollback cannot restore
physically deleted bytes.

### API and integration requirements

Use routes equivalent to:

- `GET /api/consultation-capacity`
- `POST /api/consultations`
- `GET /api/consultations/{id}`
- `GET /api/consultations/{id}/photos/{photo_id}/content`
- `GET /api/consultations/{id}/private-link`
- `POST /api/consultations/{id}/private-link/{disable|replace|create}`

Exact names may follow local conventions, but methods, authentication, idempotency and separation
of reader versus owner-token responses must remain. Publication uses the existing safe 422 field
envelope. Stable codes distinguish photo/session invalidity, cap reached, consumed-payload conflict
and retryable unavailable without exposing another account's IDs or parser detail.

## Implementation sequence

1. Add migration/models for consultations, ordered photos and consumed sessions; prove fresh and
   populated PostgreSQL upgrades.
2. Refactor publication validation for caller-owned transactions/locks. Update remove/discard/
   renew/read/cleanup/orphan sweep for consumed/promoted state.
3. Implement atomic publication with author cap locking, source-session idempotency, automatic
   Private link state and unselected-image revocation.
4. Add publication/capacity schemas/endpoints, safe errors and mutation-origin protection.
5. Add protected detail/media routes using RF-09 and exact consultation-photo association.
6. Add owner current-link/transition routes with row locks and expected generation.
7. Extend uploader session/freeze/relinquish behavior; add strict publication/link API clients,
   controller and one-step confirmation summary.
8. Add PostgreSQL races, cleanup/promotion, access/security and frontend-state tests; keep all
   dependency suites green.
9. Run migrations, quality checks and full built-stack two-account smoke with real normalized
   images, retry, restart, cleanup and link transitions. Update documentation/state from evidence.

## Validation strategy

### Automated tests

- Validation: text/audience, current limits, duplicate/wrong-owner/mixed-session/non-ready/missing
  images, byte absence, normalized-equivalent text and photo ordering.
- Atomicity: injected failures at consultation/option/link/session/revocation stages leave no partial
  publication; valid preparation remains usable after rollback.
- Idempotency: duplicate activation, concurrent same session, lost-response Retry, restart,
  consumed lease, later cap/limit changes and changed-payload conflict.
- PostgreSQL races: two sessions for last slot; publish versus remove/discard/upload/lease/cleanup;
  orphan sweep overlapping promotion; concurrent link transitions. Assert final states/deadlock-free
  lock order.
- Cleanup: promoted keys survive startup/hourly/manual cleanup; temporary endpoints cannot revoke
  them; unselected items delete; deletion failure remains denied/retryable.
- Access: anonymous/owner/other, Public/Private, valid/missing/wrong/stale/disabled token,
  cross-consultation photo and every lifecycle; exact safe fields/headers.
- Link: generation boundaries/string transport, owner-only mutation, stale precondition, refetch and
  no old-token revival.
- Security: hostile/null/missing origins, extra/oversized fields, no token/content/key leakage,
  inert malicious text and no static media exposure.
- Frontend: session handoff, freeze, duplicate prevention, same-snapshot Retry, error preservation,
  relinquish without DELETE, unmount/account-switch cleanup, strict guards and one confirmation.
- Existing account/profile/photo/text/audience/link/config suites remain green.

Use a real isolated PostgreSQL `TEST_DATABASE_URL`; existing RF-07 races are regression coverage,
not RF-10 proof. Use Alembic against an isolated test database, not only `create_all`.

### Manual validation

- Temporary test mount at 320 px, desktop and 200% zoom: one Publish action, return to edit,
  pending/error/Retry, keyboard/focus and accurate Public/Private/immutability/no-expiry copy.
- Full Compose smoke with two accounts and actual normalized images: Public/Private publish,
  duplicate/Retry, restart, cleanup survival, ordered reads, wrong/direct access denial and all link
  transitions with old-link rejection.
- Limit-one concurrent sessions: exactly one success; existing form receives cap error; advisory
  capacity reserves nothing.
- Inspect volume/database: no duplicated derivative/original, promoted key preserved, unselected
  temporary keys removed through cleanup.
- Keep RF-06, RF-12/18, RF-26, terminal deletion/restore and physical-iPhone/TestFlight gates pending
  until their real consumers/environments provide evidence.

### Commands

```powershell
.\.venv\Scripts\python -m pytest backend\tests
.\.venv\Scripts\python -m ruff check backend
.\.venv\Scripts\python -m ruff format --check backend
.\.venv\Scripts\python -m mypy backend\app
.\.venv\Scripts\python -m alembic -c backend\alembic.ini upgrade head
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

Run downgrade/upgrade only on a disposable database with no published rows; unsafe published-data
downgrade must refuse. Use `docker compose up --build -d` for smoke and
`docker compose exec backend python -m app.cleanup` for cleanup status. Do not delete user volumes.

## Acceptance criteria

- [ ] A registered owner publishes one durable open consultation from one active owned session with
      valid current text, explicit audience and current photo/cap limits.
- [ ] Consultation, photo order, consumed session and initial Private-link state commit atomically;
      injected failure leaves no partial state.
- [ ] Duplicate activation/manual Retry returns the same consultation; changed content for a
      consumed session conflicts without editing or duplication.
- [ ] Concurrent publications cannot exceed the author cap; capacity guidance reserves no slot and
      an existing live preparation can retry later.
- [ ] Selected files promote without copy/reprocessing and survive every temporary cleanup path;
      unselected objects remain revocable/deletable.
- [ ] Temporary read/remove/discard/lease routes cannot expose or revoke promoted media.
- [ ] Content, order and audience are immutable; there is no duration or automatic expiry.
- [ ] Private publication starts generation 1 active; owner link reads/transitions persist safely
      under stale/concurrent/lost responses.
- [ ] Detail/text/every image enforce current account, lifecycle, audience, association and Private
      token; denied/direct/stale/terminal access leaks nothing.
- [ ] Missing bytes yield retryable unavailability; never partial/substituted comparison.
- [ ] Published rows/photos survive app close and ordinary restart on the existing stores; no backup,
      versioning or disaster-recovery infrastructure is added.
- [ ] Frontend primitives support one confirmation, pending duplicate prevention, simple Retry,
      preserved form on definite failure and success relinquish without delete.
- [ ] No complete composer/feed/vote/result/finalization/deletion UI, fake control, native link,
      worker or storage service is introduced.
- [ ] Migration, PostgreSQL races, repository checks and full built-stack two-account smoke pass with
      exact evidence; deferred consumer/device gates remain explicit.

## Dependencies and ordering

- Depends on RF-01/RF-02 authentication and the implemented RF-07/08/09 contracts. Read their full
  approved plans and inspect the dirty worktree before editing.
- RF-03 Home/Profile remains intact; RF-10 adds no fake route. RF-06 integrates the composer;
  RF-26 integrates routing/copy/auth return; RF-12/18 supply list/results.
- RF-14/16 consume open detail/access. RF-13/19/20/37 supply terminal actions, published-photo
  deletion and restore. Restricted administrator removal remains required before real-user exposure.
- Sequence remains RF-09 -> RF-10 -> finalise/implement RF-06. Full RF-09/RF-10 ticket completion
  waits for named integration/device gates; this is a coherent implementation increment.

## Risks and mitigations

- Cleanup deletes promoted files: one ledger, explicit consumed associations, coordinated path
  changes and cleanup/publication races.
- Partial promotion: no file move; one relational commit; delete only durably revoked leftovers.
- Cap race: per-author PostgreSQL lock and last-slot test.
- Lost response duplicates: unique source session plus fingerprint; manual Retry returns original.
- Delayed temporary DELETE revokes publication: consumed/association checks and shared lock order.
- Private leak: current policy per request, fragment/header token, owner-only token response,
  origin checks, private/no-store/no-referrer and safe logs.
- Generation precision: exact DB domain, decimal-string API and boundaries.
- Volume loss: accepted POC limitation; retryable unavailability, never partial comparison.
- Premature completion: preserve consumer/deletion/iPhone gates and add no placeholders.

## Harness handoff notes

- Read AGENTS.md, all source-of-truth context, this plan and RF-07/08/09 plans before editing.
  Preserve substantial uncommitted dependency/user changes.
- Keep the POC simple: no recovery screen, polling, background retry, backups, worker, custom native
  links or combined later tickets. Still implement transactionality, deduplication, cap locking,
  cleanup-safe promotion and per-request authorization.
- Use English identifiers/comments/copy and safe errors. Never expose text, tokens, keys or media in
  logs/public paths.
- Run destructive migration/cleanup checks only on explicit isolated databases/volumes. Never use
  the user's active data for downgrade tests.
- Record exact evidence and pending gates. Do not commit, push, deploy, mutate Trello, generate native
  projects, use the coordinator runbook or launch other agents.

## Resolved grooming decisions

- One preview Publish action; no second dialog (DEC-031).
- Early cap guidance blocks a new preparation but reserves nothing; preserve a live form after a
  last-slot race (DEC-031).
- POC retry is pending/error/manual Retry with server one-publication-per-session deduplication; no
  special recovery/status flow.
- Published data survives ordinary close/restart on existing stores; no backup/versioning/special
  recovery, and extraordinary volume loss is accepted (DEC-032).
- Temporary preparation remains non-recoverable and abandoned files follow DEC-026.
- Current 2–10/three-open limits, RF-08 text, explicit RF-09 audience, immutable content, no expiry
  and automatic Private link apply.
- Current request-time authorization has no polling or recall of loaded bytes (DEC-028–030).
- Preserve ticket split: RF-10 supplies persistence/protected reads/link management; later tickets
  own complete composer, results, sharing and terminal flows.
- The owner explicitly requested plan finalisation. Harness launch remains separate.

## Remaining questions

None
