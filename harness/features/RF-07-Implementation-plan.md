# RF-07 - Subir y comparar varias fotografías - Implementation Plan

## Status

`Ready for implementation`

## Source ticket

- Trello title: `RF-07 · Subir y comparar varias fotografías`
- Trello URL: https://trello.com/c/x8VPrsF9/3-rf-07-subir-y-comparar-varias-fotograf%C3%ADas
- Trello list at intake: `Fase 2`
- Snapshot captured on: `2026-09-22T15:24:06Z`
- Grooming notes: `harness/grooming/RF-07-grooming.md`

## Objective

Provide the private photo-upload and processing foundation that RF-06 needs for consultation
preparation. An authenticated author can select ordinary still photos, including HEIC/HEIF from an
iPhone gallery, upload them with per-photo progress and retry feedback, and inspect normalized
photos without cropping. Raw originals and metadata are not retained.

This increment includes the minimum RF-37 protection required before a real upload can exist:
owner-only temporary reads, immediate revocation on Remove/Cancel, renewable active-composer
leases, cleanup after a client disappears, durable deletion retries, and storage outside the public
web root. It does not expose a standalone product screen. It supplies a tested reusable frontend
component and backend contract for RF-06 to integrate into the real composer.

## Context and current behaviour

- The frontend is a React/TypeScript/Vite application with Capacitor dependencies. `App.tsx` and
  `Navigation.tsx` currently provide authenticated Home/Profile local navigation. There is no
  composer, file picker, router, image UI package, native project, or native picker plugin.
- `frontend/src/api.ts` contains account/session/profile requests only. Existing calls use the
  signed `HttpOnly` account cookie and treat API responses as untrusted runtime data.
- The FastAPI backend has account and health routes only. `backend/app/models.py` contains only
  `Account`; Alembic ends at the accounts migration. There is no upload session, image model,
  processing dependency, private-media route, cleanup service, or consultation model.
- `backend/app/config.py` is the server settings boundary. Docker Compose persists PostgreSQL only;
  the backend has no private media volume. The Python 3.13 slim container must prove the chosen
  JPEG/PNG/WebP/HEIC/HEIF decoder stack during its build and tests.
- RF-01/RF-02 supply registration and signed-cookie authentication. RF-03 code supplies shared
  authenticated navigation but is still recorded as implementation in progress; RF-07 must avoid
  coupling its component to an unfinished navigation change.
- DEC-012/013/015/016/025/026 define temporary authoring, configurable 2–10 photos, direct iPhone
  gallery formats, normalized-only storage, the minimum RF-37 protection, and the active-composer
  lease. DEC-007 excludes a queue/general worker without proven need.

## Scope

### In scope

- Owner-bound temporary upload sessions created on demand for a live composer.
- A renewable lease that keeps the session and all its photos alive without a maximum editing
  duration while the authenticated composer remains open and connected.
- Private upload and owner-only reads for JPEG, PNG, WebP, HEIC and HEIF still images.
- Server-side byte/decoder validation, orientation application, sRGB JPEG normalization, metadata
  removal, transparency flattening on white, resource bounds, and raw-byte deletion.
- Initial limits of 2–10 publishable photos, 15 MiB per input, 40 megapixels decoded, 2560 pixels on
  the longest output edge, and three open consultations, all from one startup-validated server
  configuration source. Values are exposed read-only to the authenticated client where useful.
- Stable per-photo transfer, processing, success, error, removal, retry, ordering and enlargement
  behaviour in a reusable RF-06-facing component.
- Immediate logical revocation for Remove/Cancel; hourly cleanup, startup sweep, durable deletion
  retry and a restricted manual cleanup command.
- A server application-service contract that RF-10 can later call to validate ordered, ready,
  unique, owner-bound image IDs in an active session before atomic publication.
- Focused automated tests, container validation with accepted formats, and documented manual web
  and real-iPhone validation gates.

### Out of scope

- RF-06's navigation entry, complete composer, question/context fields, audience control, faithful
  voter preview, unsaved-change dialog and publication confirmation.
- Consultation creation, publication idempotency, promotion transaction, feed/detail access,
  Private links, voting, results, finalization, or deletion of published consultation media.
- A saved/recoverable draft, upload-session listing, reopening after reload, autosave, or recovery
  across devices.
- Permanent originals, video, animated images, filters, crop/edit tools, social imports, public
  static image URLs, image CDN, image versioning, or backup of unpublished temporary photos.
- A native picker unless real-iPhone evidence proves the shared platform picker insufficient.
- Native project generation, TestFlight distribution, Android packaging, a general worker/queue,
  or an administrator settings UI.

## User experience

RF-07 delivers a reusable photo section for the RF-06 composer; it is not added to primary
navigation independently.

1. On first photo selection, the component creates an authenticated temporary upload session. The
   ordinary platform picker advertises JPEG, PNG, WebP, HEIC and HEIF as selection hints; server
   validation remains authoritative.
2. Each selected file appears as its own item. During transfer it shows determinate upload progress
   when the platform supplies it. Once bytes reach the server and before the response returns, the
   item says `Processing photo…`. The author may continue viewing other completed items.
3. A successful item is replaced with the normalized server image. Its full proportions remain
   visible with no forced crop. An accessible enlarge action opens the normalized image in a modal
   or equivalent contained view, with keyboard dismissal, focus return and no background action.
4. A failed item stays in its original list position with a concise English error and `Try again`
   and `Remove` actions. Retry creates a new server attempt for the same UI position and revokes any
   superseded server object. It does not silently duplicate the photo.
5. The component shows the effective minimum and maximum from the server. It prevents choosing more
   than the current maximum as guidance; the server independently enforces the maximum under races
   or direct API calls. RF-10 will enforce the minimum at publication. Pending or failed items are
   never reported as publishable.
6. Removing a ready, pending or failed item updates the UI immediately, revokes the related server
   object if one exists, and requests physical deletion. A retryable cleanup/API error is reported
   without restoring the photo to publishable state.
7. While mounted, authenticated and connected, the component renews the upload-session lease.
   Renew approximately every five minutes and also when the page becomes visible or connectivity
   returns; the server-provided deadline remains authoritative. There is no editing time limit while
   renewal succeeds.
8. Explicit Cancel from RF-06 will call the session-discard operation. Browser close/reload may send
   a best-effort discard signal, but correctness never depends on it. If the client disappears, the
   lease stops; 24 hours after the last successful renewal the server revokes the session and queues
   its files for deletion. Reload starts a new composer and cannot recover the old session.
9. HTTP 401 clears private photo state and returns control to the existing session-loss flow. An
   expired/revoked session is not recoverable; the component explains that the author must select
   the photos again. Other network/server errors remain local and retryable.

## Functional requirements

### FR-1 - Effective configuration

Extend the server configuration with:

- `CONSULTATION_MIN_PHOTOS`, default `2`;
- `CONSULTATION_MAX_PHOTOS`, default `10`;
- `MAX_OPEN_CONSULTATIONS`, default `3`;
- `PHOTO_MAX_INPUT_BYTES`, default `15728640` (15 MiB);
- `PHOTO_MAX_PIXELS`, default `40000000`;
- `PHOTO_MAX_OUTPUT_EDGE`, default `2560`;
- private storage root, lease duration (24 hours), cleanup interval (one hour), and deletion-alert
  age (24 hours).

Validate at startup that the minimum is at least two, the maximum is not below the minimum and
supports at least five, and every resource/lifecycle value is positive and internally coherent.
Invalid deployment configuration prevents startup. A restart applies changes.

Provide an authenticated read-only application-config response containing only non-secret values
needed for UI guidance. The server remains authoritative if configuration changes during an
existing client session. Do not duplicate product limits as independent frontend constants.

### FR-2 - Temporary upload session and lease

An authenticated account can create an opaque owner-bound upload session. It is internal processing
state, is not a consultation/draft, has no title/audience/text, is never listed, and cannot be loaded
as a recovered form.

Creating and renewing a session returns its ID and lease deadline. Renewal requires the same signed
in owner and an active session. Successful renewal moves the deadline to 24 hours after server time.
The client should renew well inside that window and on visibility/connectivity recovery; do not use
client clocks as authority.

Unknown/non-owned resources return the same not-found result. An owner addressing an expired or
revoked session receives a stable inactive-session error. A session with any non-ready item cannot
pass the future publication validation service.

### FR-3 - Secure bounded upload

Accept exactly one multipart file per attempt plus a client-generated opaque attempt UUID. Stream
and count bytes rather than loading an unbounded body. Stop and reject once the configured input
limit is exceeded. Treat name, extension, declared MIME and picker `accept` as untrusted hints.

Identify and decode actual JPEG, PNG, WebP, HEIC or HEIF content using maintained Pillow and
pillow-heif integration (plus FastAPI multipart support). Permit the primary still image in ordinary
HEIC/HEIF containers even when auxiliary images exist. Reject video, animated/multi-frame
JPEG/PNG/WebP content, corrupt/truncated input, invalid/zero dimensions, unsupported color content,
decompression-bomb/resource overflow and all unapproved formats with stable safe error codes.

Reserve an attempt transactionally before processing so ready plus in-flight attempts cannot exceed
the configured maximum. The `(upload_session_id, attempt_id)` pair is unique. A transport retry with
the same attempt ID returns the already completed result or a stable in-progress/conflict result;
it must not create another publishable image. A user-requested retry uses a fresh attempt ID and
revokes the superseded object.

### FR-4 - Normalization and original disposal

Apply visible orientation before resizing. Convert the primary still image to sRGB, preserve aspect
ratio, cap the longest edge at the configured value without upscaling, and encode a display JPEG at
a documented fixed quality suitable for photo comparison. Flatten alpha/transparency against
white. Write to a new opaque storage key; never derive a path from account input or a filename.

Do not copy EXIF, XMP, IPTC, GPS, comments, original filename or other source metadata into the
output. Reopen/verify the completed derivative before making it ready. Remove raw and partial files
in `finally` paths for success and ordinary failure. Startup cleanup handles remnants after process
termination. Store only the normalized dimensions and non-sensitive operational fields needed for
authorization/lifecycle.

### FR-5 - Private media reads

Normalized files live under the configured backend-only volume, outside frontend/Nginx roots.
Temporary-image reads require a valid signed session and matching upload-session owner on every
request. Database state is checked before touching the file. A revoked, expired, deletion-pending,
deleted, unknown or non-owned image is never served.

Return the normalized image with the exact image content type, `Cache-Control: private, no-store`,
`X-Content-Type-Options: nosniff`, and no source filename. Do not return a permanent public URL,
storage key, filesystem path or credentials. Missing bytes for an otherwise ready row make the
object unavailable, record an operationally detectable inconsistency and never fall back to source
data.

### FR-6 - Remove, cancel and cleanup

Deleting an image or discarding a session changes authorization state transactionally before
filesystem deletion. It is idempotent for the owner. All affected files receive durable
deletion-pending state so a storage failure cannot restore access.

An hourly cleanup service and startup sweep must:

- mark active sessions abandoned when their server lease expired at least 24 hours after the last
  successful renewal;
- revoke and queue every image belonging to abandoned/discarded sessions;
- clean stale processing attempts and raw/partial remnants;
- retry pending physical deletion idempotently;
- verify file absence before marking deletion complete; and
- make items still pending after 24 hours visible through structured operational logging and a
  failing restricted cleanup/status command exit code.

Implement this as a small FastAPI lifespan maintenance task plus a directly callable/testable
service and restricted command. Do not add a queue or general worker. Multiple concurrent cleanup
calls must be safe even though the initial Compose deployment has one backend process.

### FR-7 - Reusable photo UI and comparison

Add a focused reusable component/hook that owns the temporary upload-session ID, lease renewal,
ordered UI items and cleanup callbacks. It exposes to RF-06 only ordered ready image IDs, current
statuses, whether publication is blocked, and explicit discard/removal actions. It must not persist
the session ID or photo list in local/session storage.

Use `XMLHttpRequest` or an equivalent browser API for real upload-progress events with credentials;
continue using strict runtime guards for JSON responses. Use authenticated blob fetching for private
images and revoke browser object URLs when replaced/unmounted. Status and errors use accessible live
regions without repeatedly announcing progress noise. Controls remain keyboard operable, labelled,
focus-visible and at least 44 by 44 CSS pixels where touch interaction applies.

The layout supports 320 px width, practical mobile portrait/landscape, desktop and 200% zoom. Photos
use `object-fit: contain` or equivalent so comparison and enlargement never crop content. Do not add
the component to `Navigation` or invent an RF-07-only product destination.

### FR-8 - RF-10 publication handoff

Provide a backend application-service function, tested independently of HTTP, that receives owner
ID, active upload-session ID and an ordered image-ID list. It locks/validates the relevant rows and
returns the ordered ready images only when:

- the session is active, owned by the account and its lease is valid;
- IDs are unique, belong to that session and are all ready/non-revoked;
- the count is within the current configured minimum and maximum; and
- normalized bytes exist.

The function performs no publication in RF-07 because no consultation model exists. RF-10 must call
it inside its publication transaction, add the consultation ownership relationship, and atomically
promote exactly those files. No public/voter read is authorized by RF-07.

## Technical approach

Keep HTTP handlers thin. Separate configuration, upload-session/image lifecycle, image processing,
private storage and cleanup into testable backend modules. Use PostgreSQL rows as the durable source
of lifecycle/authorization state and the private volume for bytes. Do not store image blobs in
PostgreSQL.

Process each bounded upload synchronously in the request. The frontend can distinguish network
transfer from server processing while waiting. This avoids a worker for the initial load while
retaining explicit states and cleanup after crashes. If real measurements later show unsuitable
latency or memory, return to grooming before adding background infrastructure.

### Affected areas

- Frontend API: extend `frontend/src/api.ts` or a focused photo API module with config/session/
  lease/remove/discard/private-image calls and an upload-progress transport.
- Frontend components: add a reusable photo upload/comparison component and hook plus focused tests;
  integrate styles into `frontend/src/styles.css`. Do not modify authenticated destination scope.
- Backend configuration: extend `backend/app/config.py` and environment examples with validated
  consultation/photo/storage/cleanup settings.
- Backend models/migration: extend `backend/app/models.py` or split models coherently; add the next
  Alembic migration for upload sessions, attempts/images and durable deletion state.
- Backend services: add focused image-processing, private-storage, lifecycle/publication-validation
  and cleanup modules.
- Backend API: add an authenticated photo/config router and reuse/refactor the current signed-session
  account resolution rather than duplicating authorization logic.
- Backend lifecycle/operations: wire startup/hourly cleanup through FastAPI lifespan and add a
  restricted command usable from the backend container.
- Dependencies/container: add multipart and maintained Pillow/pillow-heif dependencies; validate
  Python 3.13 Linux installation. Add a private named volume to Docker Compose.
- Documentation: update `.env.example`, README/operator guidance and project state only when evidence
  supports the implementation status.

### Data and migration requirements

Create relational records equivalent to:

- `photo_upload_sessions`: UUID, owner account foreign key, state, lease expiry, created/updated
  timestamps, discard/abandon timestamps as applicable.
- `photo_upload_attempts` or `consultation_images`: UUID, session foreign key, unique client attempt
  UUID per session, lifecycle state, opaque storage key, normalized width/height/byte length,
  created/updated timestamps, deletion-requested/completed timestamps and retry metadata.

Use explicit constrained state values and indexes for owner lookup, lease-expiry sweeps and pending
deletion. Foreign keys must not allow account deletion to leave privately readable media; later
account-deletion work may refine the lifecycle, but current deletion/cascade behavior must revoke
and clean dependent temporary media safely. Store UTC-aware server timestamps.

The migration downgrade removes only the new tables/indexes. Files are external to Alembic; document
that downgrade requires the restricted cleanup command first or an explicit operator decision to
remove the RF-07 volume. Never make migration rollback expose files.

### API and integration requirements

Use concrete routes equivalent to:

- `GET /api/application-config` — authenticated non-secret effective limits.
- `POST /api/photo-upload-sessions` — create owner-bound session; return ID/lease deadline.
- `POST /api/photo-upload-sessions/{session_id}/lease` — renew active owner lease.
- `POST /api/photo-upload-sessions/{session_id}/images` — multipart file plus attempt UUID; return
  ready normalized-image metadata after processing.
- `GET /api/photo-upload-sessions/{session_id}/images/{image_id}/content` — owner-only normalized
  bytes.
- `DELETE /api/photo-upload-sessions/{session_id}/images/{image_id}` — immediate logical removal.
- `DELETE /api/photo-upload-sessions/{session_id}` — immediate discard/revocation of all images.

Successful create/upload responses use typed, minimal payloads. Delete/discard are idempotent.
Return stable machine codes for unauthenticated, not found/non-owned, inactive session, limit
reached, too large, too many pixels, unsupported format, animated input, invalid image, processing
failure and temporary unavailability. Do not echo unsafe filenames/parser details. HTTP/body limits,
request cancellation and transaction rollback must leave no publishable orphan.

The client treats every JSON payload and header as untrusted. HTTP 401 invokes RF-02's session-loss
behavior. The component handles inactive session separately by clearing its private state and asking
for re-selection. RF-06 will call the explicit discard callback on confirmed Cancel; F10 will own
the final publication endpoint and transaction.

### Security and privacy

- Authenticate all config, session, upload, media, lease and delete operations with the existing
  signed cookie; derive owner identity only from the verified session.
- Use non-enumerable authorization responses for unknown/non-owned session and image IDs.
- Validate content after bounded streaming and decoded resource checks. Configure Pillow's bomb
  protection and treat warnings as rejection at the accepted pixel ceiling.
- Keep raw/partial and normalized files out of public roots. Use restrictive directory/file
  permissions where the platform permits and defend every path against traversal.
- Strip metadata by constructing a fresh output image and passing no source metadata to the encoder;
  test GPS, EXIF orientation, comments and representative HEIC metadata explicitly.
- Never log image bytes, cookies, filesystem/storage keys, source filenames, GPS/metadata or signed
  URLs. Structured logs may include internal IDs, safe state transitions and cleanup ages.
- Revoke in the database before deleting bytes. Reads always consult current database state, so
  deletion failures cannot restore access.
- Temporary photos have no backup/versioning. Published-photo backup/retention is deliberately left
  to the complete RF-37 plan.
- Apply private/no-store response headers. Do not expose raw originals, public URLs or directory
  listings.

## Implementation sequence

1. Add validated settings/environment examples and authenticated effective-config response, with
   startup-failure and API tests.
2. Add multipart/Pillow/pillow-heif dependencies and prove the Python 3.13 container builds before
   relying on them.
3. Add the upload-session/image lifecycle migration and models with constrained states, indexes,
   ownership, unique attempt IDs, lease and durable deletion fields.
4. Implement private storage and bounded image processing with fixture-based tests for every accepted
   format, orientation, metadata, transparency, animation, corruption and resource limit.
5. Implement application services for create/renew, upload idempotency, remove/discard, owner-only
   read and RF-10 validation; cover ownership, concurrency and state transitions.
6. Add the authenticated API routes, stable errors and private response headers, then run backend
   and PostgreSQL integration tests.
7. Implement startup/hourly cleanup plus restricted retry/status command; test clock-controlled
   lease expiry, immediate revocation, restart recovery, duplicate cleanup and storage failures.
8. Add the Docker private volume/configuration and verify files are unavailable through frontend
   and static server paths.
9. Add strict frontend API transports and the reusable photo component/hook with upload progress,
   processing, retry, ordering, removal, enlargement, lease and session-loss states.
10. Run all repository checks and full Compose smoke validation with two accounts and direct API
    authorization attempts. Record the unavailable real-iPhone/TestFlight gate rather than claiming
    it passed on Windows.

## Validation strategy

### Automated tests

- Configuration: defaults; valid overrides; max below min; min below two; non-positive resource/
  lifecycle values; exact authenticated config payload with no storage secrets.
- Processing fixtures: JPEG, PNG, WebP, real HEIC and HEIF; EXIF orientations; GPS/comments; alpha;
  large dimensions; corrupt/truncated/spoofed content; animation/multi-frame rejection; primary still
  with HEIC auxiliaries; output dimensions, aspect ratio, sRGB/JPEG signature and metadata absence.
- Storage: opaque safe keys, no public-root writes, raw/partial deletion on success/failure, missing
  normalized bytes, write failure and restart remnants.
- Session/API: authentication; non-owner indistinguishability; lease renewal; server-time deadlines;
  explicit discard; expired session; per-session max including concurrent attempts; same-attempt
  replay; new retry attempt; delete idempotency; response headers; no original/source metadata.
- Cleanup with injected clock/storage: active lease never purged; expired lease revoked; hourly/
  startup/manual paths; durable retry; concurrent sweeps; file absence verification; alert/status
  after 24 hours pending; access remains denied throughout failure.
- Publication handoff service: ordered unique ready IDs; wrong owner/session; missing, pending,
  failed, revoked, deleted or absent bytes; below/above changed limits; transactional locking.
- Frontend transport/component: accept hints; server config guidance; per-item progress to processing;
  success; every stable error; retry in same UI position with new attempt; removal; ordered ready IDs;
  publish-blocking status; lease timer/visibility/online renewal; 401; inactive session; unmount cleanup;
  object-URL revocation; enlarge dialog accessibility and no-crop rendering.
- Existing account, profile, health, migration and frontend suites remain green.

Use meaningful PostgreSQL-backed concurrency/integration tests for row locking and uniqueness; the
existing SQLite unit fixture alone cannot prove those properties.

### Manual validation

- In the web app/component integration harness, select accepted formats, observe transfer and
  processing states, enlarge portrait/landscape images, retry a failed upload, remove photos and
  discard the session. Confirm direct/static URLs do not work and a second account cannot read.
- Leave an editor connected beyond an artificially shortened test lease while heartbeats succeed;
  confirm files remain. Stop the client, advance the controlled test configuration, run cleanup and
  confirm access revocation and physical removal. Simulate deletion failure and retry.
- Inspect representative normalized outputs to confirm visible orientation, no crop, acceptable
  comparison quality, no GPS/source metadata and no originals in storage.
- Validate layout and keyboard/screen-reader behavior at 320 px, mobile portrait/landscape,
  desktop and 200% zoom.
- Build and run the full Docker Compose stack with PostgreSQL and private volume. Exercise restart,
  startup sweep and the restricted cleanup command.
- On a real iPhone/TestFlight build when the permanent app ID, Apple signing and Xcode environment
  exist, select ordinary JPEG/HEIC/HEIF gallery photos, inspect the actual picker representation,
  upload over normal and interrupted networks, background/foreground the app, verify cookie auth,
  orientation, progress/retry, enlargement and safe-area layout. If the shared picker fails this
  gate, return to grooming for the smallest native-picker change; do not drop accepted formats.

The reusable component may be mounted in a non-committed development/test harness for RF-07 manual
checks. Do not ship a temporary RF-07 route or navigation item. Final end-to-end product validation
occurs when RF-06 integrates it.

### Commands

From the repository root:

```powershell
.\.venv\Scripts\python -m pytest backend\tests
.\.venv\Scripts\python -m ruff check backend
.\.venv\Scripts\python -m ruff format --check backend
.\.venv\Scripts\python -m mypy backend\app
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python -m alembic downgrade -1
.\.venv\Scripts\python -m alembic upgrade head
Push-Location frontend
npm test
npm run format:check
npm run lint
npm run typecheck
npm run build
npm audit --audit-level=high
Pop-Location
docker compose config
docker compose build backend
```

Full PostgreSQL/private-storage/API smoke validation:

```powershell
docker compose up --build
```

Use the implemented restricted cleanup module's documented `python -m ...` command inside the
backend container; the plan does not invent its final module name before implementation chooses the
coherent service layout.

## Acceptance criteria

- [ ] An authenticated owner can create one temporary upload session and upload actual JPEG, PNG,
      WebP, HEIC and HEIF still photos within configured bounds; unauthenticated and other accounts
      cannot upload to or read it.
- [ ] Actual decoded content, byte size and pixel count are server validated; spoofed, corrupt,
      animated/video, oversized and unsupported inputs receive safe stable errors.
- [ ] Every ready image is a verified normalized sRGB JPEG with correct visible orientation, full
      aspect ratio, maximum 2560-pixel edge, no carried source/GPS metadata and no retained original.
- [ ] The initial 2–10 photo, three-open-consultation, 15 MiB, 40 MP and 2560-pixel values come from
      one startup-validated server configuration and relevant non-secret values reach the client.
- [ ] Each UI item communicates upload progress, processing, success or failure and supports removal
      and retry; retry retains list position without creating an extra publishable image.
- [ ] Ready normalized photos can be compared and enlarged without forced crop in an accessible,
      responsive component; the component is not exposed as a provisional product destination.
- [ ] While the authenticated connected component renews its lease, photos remain available without
      a maximum editing duration. Reload does not recover the composer.
- [ ] Remove/Cancel revokes access immediately. A missing client results in revocation after 24
      hours without renewal and hourly physical cleanup; failures remain denied, detectable and
      retryable, including after restart.
- [ ] Temporary images, storage keys, source filenames and filesystem paths are never public or
      returned as durable URLs; private responses disable shared/persistent caching.
- [ ] The RF-10 handoff validates owner, active lease, ordered unique IDs, ready state, byte presence
      and current min/max without creating a consultation or authorizing voter reads.
- [ ] PostgreSQL-backed concurrency tests prove maximum-count and attempt-idempotency invariants;
      full backend/frontend checks and Docker Compose/private-volume smoke tests pass.
- [ ] Representative real-iPhone gallery selection and HEIC/HEIF behavior are recorded before
      phase-2 delivery; lack of an available signed iOS environment is reported as an external
      validation gate and is never misreported as success.
- [ ] Existing registration, sign-in, session restoration, profile, sign-out, health/readiness and
      production frontend behavior remain green.

## Dependencies and ordering

- Depends on RF-01/RF-02 account and cookie-session behavior. It may reuse RF-03's shared frontend
  foundation but must not assume RF-03 is complete without checking current project state.
- Implements the minimum RF-37 protection accepted in DEC-025. The rest of RF-37 still owns
  published-media authorization, finalization/deletion/removal, backups and recovery policy.
- Must precede RF-06 implementation because RF-06 needs real processed photos and private preview.
- RF-06 owns product navigation/composer integration and explicit Cancel wiring. RF-08/09 own text
  and audience. RF-10 owns the publication endpoint, transaction/idempotency and atomic promotion.
- A real iOS validation environment depends on permanent application ID, Apple team/signing, Xcode
  and TestFlight setup (DEC-014); implementation can proceed on web/container fixtures, but phase-2
  delivery cannot claim the real-device criterion before that gate passes.

## Risks and mitigations

- **Parser/resource attack:** stream-count compressed bytes, enforce decoded pixels, reject animation,
  keep a format allowlist and use maintained decoder libraries in the verified container.
- **Metadata/privacy leak:** construct fresh sRGB output, pass no source metadata, test GPS/EXIF/XMP/
  comments, discard raw/partial data in every path.
- **Authorization race:** database state precedes file access/deletion; lock lifecycle transitions and
  make revoked state irreversible from cleanup retries.
- **Orphan files after crash:** durable attempt/deletion rows, opaque storage keys, startup sweep,
  hourly cleanup and manual retry/status command reconcile database and storage.
- **Browser disappears without Cancel:** renewable server lease makes abandonment independent of an
  unreliable exit request while allowing an open connected editor to remain active indefinitely.
- **Background/suspended device exceeds grace:** session expires after 24 hours without contact and
  requires reupload; UI must not promise draft recovery.
- **Duplicate concurrent uploads:** unique attempt IDs, transactional reservation and PostgreSQL
  tests prevent extra ready images and enforce current max.
- **HEIC build/device mismatch:** verify Linux dependencies and real representative fixtures; retain
  a real-iPhone gate and escalate before changing DEC-015.
- **Synchronous processing latency:** strict bounds and explicit Processing UI keep the initial path
  simple; measure before considering a worker.
- **Temporary-volume loss:** unpublished photos intentionally have no backup and require reupload.
  Published-image durability is not silently decided in this plan.
- **Premature product surface:** deliver a reusable tested component without a temporary route;
  RF-06 supplies the real author journey.

## Harness handoff notes

- The repository is entirely untracked and contains user/bootstrap work plus RF-01/RF-02 and RF-03
  changes. Preserve unrelated files and inspect the current worktree before editing.
- Implement only RF-07 plus the minimum RF-37 protection in this plan. Do not add RF-06 navigation/
  composer, consultations, publication, audience, voter access or published-media lifecycle.
- Use English for identifiers, comments, tests, API errors and user-facing copy (DEC-009).
- Do not commit, push, deploy, mutate Trello, generate native projects, create a TestFlight build or
  launch another agent.
- Do not weaken authentication, make storage public, retain originals, or add a queue/general worker.
- The Windows workspace cannot prove the real-iPhone gate. Complete all automatable/container work,
  clearly report that external gate and do not mark it passed without evidence.
- Update project state only when the implementation and independent validation support the claim.

## Resolved grooming decisions

- RF-07 is required before RF-06 can use real, faithful processed-photo previews.
- The first RF-07 increment includes private storage, owner-only temporary reads, immediate
  revocation and abandoned-upload cleanup from RF-37 (DEC-025).
- Temporary upload records are processing/lifecycle state, not saved drafts. An open authenticated
  connected composer renews a lease and has no editing time limit. Missing renewal for 24 hours
  means abandonment; explicit Remove/Cancel revokes immediately (DEC-026).
- Successful publication will promote selected photos atomically, but RF-10 owns and implements
  that transaction after consultation persistence exists.
- Initial accepted inputs are still JPEG, PNG, WebP, HEIC and HEIF. Use the shared platform picker
  first and return to grooming only if real-device evidence requires a native picker.
- Server processing validates actual content, uses the HEIC/HEIF primary still, preserves visible
  orientation, normalizes to an sRGB JPEG, removes metadata, flattens alpha on white and rejects
  video/animation/corrupt or oversized input.
- Initial configurable values are 2–10 photos, three open consultations, 15 MiB input, 40 MP decoded
  and 2560-pixel maximum output edge. Configuration is server-owned, startup validated, exposed
  read-only where needed and changed by restart.
- Uploads process synchronously within strict bounds; no queue/worker is introduced. Transfer and
  processing remain distinct visible client states.
- Retry creates a fresh attempt for the same UI position; transport replay of the same attempt is
  idempotent. Only ready, active, owner-bound images can pass the RF-10 validation handoff.
- Temporary unpublished photos have no backup/versioned copy. Published-photo backup and deletion
  policy remains in the complete RF-37 scope.
- The reusable photo component is implemented and tested without a provisional navigation entry;
  RF-06 owns its product integration.

## Remaining questions

None
