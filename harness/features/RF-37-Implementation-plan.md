# RF-37 - Protect and delete photographs - Implementation Plan

## Status

`Ready for implementation`

The product owner approved the settled RF-37 scope, plan finalisation and autonomous harness launch
on 2026-10-19. Implementation remains limited to this contract; RF-13, RF-19/RF-20 and the
restricted RF-32 consumer operations are not part of this plan.

## Source ticket

- Trello title: `RF-37 · Proteger y borrar fotografías`
- Trello URL: https://trello.com/c/Dodf7k4R/40-rf-37-proteger-y-borrar-fotograf%C3%ADas
- Trello list at intake: `Próximo · completar el MVP`
- Snapshot captured on: `2026-10-19T17:30:22.5064539+02:00`
- Grooming notes: `harness/grooming/RF-37-grooming.md`

## Objective

Establish one reusable, database-first revocation and verifiable physical-erasure contract for
published consultation photographs. Future author deletion, author finalization and restricted
administrator removal must be able to revoke every photograph in their terminal database
transaction, commit once, and let restart-safe maintenance converge physical storage afterwards.

No storage failure may restore application access. The implementation must identify every object in
the consultation's unique consumed upload session, retry partial or failed deletion, verify real
absence before discarding its retry reference, and leave only the minimum non-visual option/deletion
data allowed by DEC-023. It must preserve RF-07's temporary-upload contract and add no general queue,
public media path, image backup, terminal product action or finalized outcome implementation.

## Context and current behaviour

- RF-07 stores one normalized JPEG per accepted still image in a private backend volume through
  `PhotoStorage`. Raw upload files are deleted after processing/failure. Temporary sessions use a
  renewable 24-hour lease; remove, discard and abandonment mark image rows revoked before deletion.
- `PhotoUploadImage` is the current durable file ledger. It has ready/revoked/deleted states,
  deletion requested/completed timestamps, attempt count and a bounded sanitized error.
- `backend/app/cleanup.py` performs startup, hourly and restricted manual cleanup. It claims image
  rows with `FOR UPDATE SKIP LOCKED`, unlinks exact opaque keys, checks `exists`, retries failures,
  reports work beyond the configured 24-hour threshold, removes stale raw files and sweeps old
  unreferenced normalized objects.
- RF-10 promotes photographs without copying or moving bytes. One consumed
  `PhotoUploadSession` is uniquely referenced by one `Consultation`; its selected images remain
  `PhotoUploadImage` rows referenced in order by `ConsultationPhoto.image_id`. Unselected objects in
  that session are already revoked. A consumed session cannot publish again or serve temporary
  owner-preview reads.
- Current storage contains no original, thumbnail, alternate resolution, public copy or versioned
  derivative. The complete current published deletion set is every image/attempt belonging to the
  unique consumed source session. Any future derivative must join that durable manifest before it
  can be written; filename or directory inference is forbidden.
- RF-09/RF-10 authorization reloads the current consultation for each protected detail/photo read.
  `can_access` permits only `open`; finalized, deleted and removed are generic unavailable. Media
  bytes are read only after authorization. Already authorized requests may finish, but authorization
  beginning after terminal commit must fail.
- RF-11 defines `open`, `finalized`, `deleted` and `removed` plus the first-terminal-commit-wins
  protocol. It performs no persistence or storage work. Terminal consumers must lock the
  consultation row, re-read state, write all database effects and commit once before physical work.
- RF-16 vote submission locks that same consultation row and rechecks open-state authorization. A
  vote and terminal writer therefore serialize: a vote committed first is visible to finalization;
  a vote obtaining the lock after terminal commit is denied.
- RF-18 derives live open counts from `Vote` and `ConsultationPhoto`. No finalized aggregate or
  participant outcome exists. RF-19/RF-20 must transform raw choices into DEC-023 data before those
  raw choices can be removed. RF-13/removal before finalization produces no outcome.
- `ConsultationPhoto` is the stable product option identity/order and `Vote` references it directly.
  Its current `image_id` is non-null and restricts deletion of `PhotoUploadImage`. The option can
  survive without bytes once migration makes the visual association detachable.
- Compose has separate PostgreSQL and private-photo named volumes. Only the backend mounts the photo
  volume. Alembic runs before Uvicorn; FastAPI startup cleanup runs before the application accepts
  traffic. There is no worker, broker, backup job or restore automation.
- DEC-032 deliberately provides no photo backup/versioning for this POC. Supported restoration may
  lose still-open photos but must never resurrect revoked ones.
- DEC-041 records the accepted cross-feature erasure, recovery, observability, restore, minimization,
  migration, validation and consumer-order contract.

## Scope

### In scope

- An additive migration and ORM changes that allow a published option to retain stable identity and
  order after its visual ledger is detached, with a minimal non-visual deletion completion marker.
- A focused RF-37 domain/service boundary that a terminal consumer calls while holding the locked
  consultation row and before its single commit. It marks every object in the unique consumed source
  session deletion-pending and deactivates Private access without committing or selecting a terminal
  lifecycle itself.
- Whole-consumed-session discovery: selected published images, revoked leftovers, failed attempts,
  existing deleted rows and any future registered derivative all converge safely.
- Startup/hourly/manual reconciliation for terminal consultations missed by a crash or old fixture,
  durable deletion retry, explicit post-delete absence verification and partial-set recovery.
- A narrow PostgreSQL maintenance-leader lock around filesystem/orphan reconciliation so multiple
  API replicas cannot sweep the shared volume concurrently.
- Removal of the visual/image ledger and upload-session data only after every exact object is
  verified absent. Preserve stable option ID/ordinal plus a minimal `media_deleted_at`-style marker.
- A terminal sanitization seam and schema compatibility for DEC-023. It must support future consumer
  removal of no-longer-permitted question/context/audience/link/fingerprint/upload/raw-choice data,
  but must not invent final selections, aggregates or participant outcomes in RF-37.
- Sanitized structured cleanup/reporting counts, immediate failure logging, overdue status and a
  documented operator alert requirement before beta.
- A supported POC restore procedure using PostgreSQL plus an empty/current private photo volume,
  with migration and reconciliation before traffic; historical photo-volume restoration is forbidden.
- Documentation and comprehensive automated/PostgreSQL/Docker/restart/restore validation artifacts.

### Out of scope

- RF-19/RF-20 finalization, declared one/several/none selection, aggregate snapshots, participant
  outcomes or finalization UI.
- RF-13 author deletion endpoint, confirmation or complete deletion semantics.
- The restricted RF-32 administrator removal command/API itself, public moderation/reporting UI,
  suspension, inbox, evidence archive or general administrator console.
- Account deletion or anonymization.
- New originals, thumbnails, derivatives, copies, caches, archives, versioning, photo backup,
  analytics/model datasets or moderation evidence.
- A broker, worker service, general job framework or unrelated scheduler.
- Any weakening or redesign of RF-07's active lease, abandoned-upload, raw-file or temporary cleanup
  contract.
- Feed, voting, result, sharing, navigation, visual UI or unrelated product changes.
- Commit, push, deployment, Trello mutation, active-user-volume cleanup or native distribution.

## User and operator experience

RF-37 adds no product action or new screen. Existing open consultation experiences remain unchanged.
When a future terminal consumer commits, owner/reader/link/photo/vote access becomes unavailable from
current database state. An already authorized response or bytes already rendered on a device cannot
be recalled; no authorization beginning after commit may succeed.

Physical deletion is operationally asynchronous and invisible to the user. A storage error never
changes the terminal lifecycle or re-enables a link. Maintenance retries automatically at startup
and hourly. The restricted command reports concise counts and exits non-zero when overdue work or an
unresolved anomaly requires intervention. It must not expose keys, paths, content, account data,
question/context, capabilities or image metadata.

An operator restoring the POC must keep traffic disabled, use an empty or current photo volume, run
Alembic and RF-37 reconciliation/status, resolve failures, and only then permit traffic. Restoring an
older photo-volume snapshot is unsupported and prohibited because it could resurrect bytes whose
revocation occurred after the snapshot.

## Functional requirements

### FR-1 - Database-first terminal media marker

Provide a service operation for use inside an existing terminal transaction. The caller must have
loaded and locked the current `Consultation` row with `FOR UPDATE`, authorized its actor, evaluated
RF-11's transition and persisted any operation-specific data. The RF-37 operation must:

- require an open consultation and its unique consumed source session;
- set `private_link_active = false` as defence in depth;
- mark every ready or pending image in that source session revoked with a deletion request;
- preserve already revoked work and normalize legacy deleted/failed/no-key rows for reconciliation;
- never commit, choose/write the terminal lifecycle, calculate outcomes or perform filesystem I/O;
- be safe when invoked once in the winning transaction and deterministic under rollback.

Document the required lock/order: consultation row first; consumer database effects and RF-37 media
marker in the same transaction; terminal state write; one commit; physical cleanup afterwards.

### FR-2 - Whole-consumed-session manifest

The unique `Consultation.source_session_id` is the deletion-manifest root. Process every
`PhotoUploadImage` belonging to that session, not only current `ConsultationPhoto` associations.
This includes already-revoked unselected images and failed/partial attempts. Repeated work over an
already absent or removed object is idempotent. Reject or report a session that is not consumed, is
missing, is shared contrary to constraints, belongs to another account or has inconsistent option
associations; do not broaden deletion through guessed paths.

### FR-3 - Immediate access revocation

All existing protected detail, photo, feed projection, owner link and vote paths must continue to
authorize from current database lifecycle. Tests must prove no route touches storage or returns
protected content after terminal commit, including with a formerly current Private link and as the
owner. Deletion pending/failed/completed never changes terminal state or creates a new read grant.

The linearization point is request authorization. A request authorized before terminal commit may
finish. Do not add read locks held across byte delivery, polling, push recall or client-side claims
that downloaded/rendered bytes were erased.

### FR-4 - Verifiable idempotent physical deletion

For each exact valid key, call the storage delete operation and then explicitly verify absence.
Already absent is successful idempotent completion. Mark/detach an object complete only after the
absence check. If any key fails deletion or verification, retain that exact key and retry metadata;
continue independent objects without claiming the entire session complete. Never store raw exception
text that may contain paths or secrets.

### FR-5 - Durable retry and visual-ledger minimization

While work is pending/failed, retain the minimum exact `PhotoUploadImage` key/state/request time,
attempt count and sanitized error required to retry. Once one selected image is verified absent,
detach its stable `ConsultationPhoto` from the visual row and set its non-visual deletion timestamp;
then remove that visual ledger row and its key, dimensions, byte length, attempt/error metadata.

After every image/attempt in a consumed session is absent and its rows are removed, detach
`Consultation.source_session_id`, remove the consumed upload session, and leave only stable option
ID/ordinal/deletion marker plus the terminal consultation fields currently permitted. Never delete
`ConsultationPhoto` merely to remove bytes because Vote and future result records use its ID.

### FR-6 - Recovery reconciliation

Each maintenance pass first finds terminal consultations that still retain a consumed source session
or visual associations, including rows created by pre-RF-37 fixtures or a crash between terminal
commit and ordinary cleanup. It must durably mark any remaining ready images revoked before file
access. Commit logical reconciliation before filesystem deletion, as RF-07 already does.

Missing known files converge as verified success. Partial sets keep remaining work. A valid opaque
unreferenced normalized file older than the configured safe age remains covered by the orphan sweep.
Invalid database keys, unreadable paths and unexpected filenames are never served or silently
deleted; record sanitized anomaly counts/errors and require restricted operator handling. One bad
object must not block safe deletion of unrelated objects.

### FR-7 - Maintenance leadership and idempotency

Reuse the existing FastAPI startup pass, hourly loop and `python -m app.cleanup` command. Do not add
a worker. Acquire one stable application-specific PostgreSQL session advisory lock before the full
filesystem/reconciliation pass and release it in `finally`. A periodic/startup replica that cannot
acquire it skips cleanly; the restricted manual command must report `busy` distinctly and exit
non-zero rather than running concurrently.

Keep per-row `FOR UPDATE SKIP LOCKED` protections where useful. The advisory lock is not a product
transaction lock and must never be held by request handlers. Local unit tests may inject a lock
adapter, but PostgreSQL integration must prove real leader exclusion and recovery after connection
close/crash.

### FR-8 - Observability and restricted operation

Extend `CleanupReport` and the restricted command with counts for terminal sessions discovered,
objects requested, deleted, already absent, failed, overdue, completed sessions and anomalies,
alongside existing temporary cleanup counts. Logs and command output use internal IDs only where
necessary and never storage keys, filesystem paths, content, source filenames, capability tokens,
questions or account data.

Every failed attempt logs a sanitized error. Work whose deletion request age reaches the existing
`PHOTO_DELETION_ALERT_SECONDS` default of 24 hours logs at error level, contributes to overdue count
and makes manual status exit non-zero. API liveness/readiness remain independent. Document that beta
deployment must route these errors or a scheduled status check to its operator alert channel; do not
invent a monitoring vendor in this ticket.

### FR-9 - DEC-023 terminal minimization seam

Define explicit allowlisted terminal sanitization helpers/contracts rather than generic ORM deletion.
After a consumer has persisted its permitted replacement data, the eventual terminal state may keep
only consultation/owner/option identifiers, relevant dates/state, stable ordinals/media-deletion
markers, declared option IDs, aggregate counts and participant Matched/Not matched/No choice outcomes.

The schema must permit later removal/nulling of question, context, audience/link generation and
activity, publication fingerprint and source upload references. RF-37 must not create final selection,
aggregate or participant-outcome tables merely to use that seam. It must not delete raw finalized
Vote choices until RF-19/RF-20 has persisted permitted outcomes. RF-13/restricted removal before
finalization will delete votes without outcomes in their own approved consumer transaction.

Existing seeded terminal fixtures may have no valid outcome replacement. Purge their image bytes for
privacy, but do not fabricate outcomes or silently destroy data needed to expose a repository/code
conflict; report unresolved non-visual minimization for the owning future consumer.

### FR-10 - Supported restore and non-resurrection

No photo backup/versioning is added. The only supported POC restore uses a PostgreSQL backup with a
new empty photo volume or the current non-restored volume. It must never attach an older image-volume
snapshot. Run migration and startup/manual reconciliation with traffic disabled. A restored open row
whose bytes are absent remains a retryable missing-media condition; do not recreate bytes or change
lifecycle. A restored terminal row is denied and reconciled before traffic.

Document the accepted consequence: a database-only disaster restore can lose images from still-open
consultations. Future image backup requires a new approved design with an external monotonic
revocation journal newer than every restorable snapshot.

### FR-11 - Compatibility and rollback

The migration is additive for current open data. At minimum it must make the option-to-image and
consultation-to-source-session relationships detachable, add the non-visual media deletion marker,
and make terminal-sanitized content fields safely nullable with constraints that still require the
complete current contract for `open` consultations. Existing open rows need no destructive backfill.

Migration/application ordering must allow the migration to land before RF-37 code without changing
open reads/publication. A downgrade may proceed only if no option/session/content row has been
irreversibly detached or sanitized. Once used, downgrade must fail with a clear operator message;
neither Alembic nor code rollback may pretend to restore erased bytes or content. Never remove the
photo volume automatically during migration.

### FR-12 - Consumer boundary and ordering

Expose well-named transaction-local APIs and documentation for RF-13, RF-19/RF-20 and restricted
RF-32. Do not expose a public terminal endpoint in RF-37. RF-13 is the first intended real consumer,
followed by coordinated RF-19/RF-20; restricted administrator removal must use the identical path
before beta. A future consumer that bypasses this marker/purge/minimization contract is invalid.

## Technical approach

Add a focused module such as `backend/app/photo_erasure_service.py` rather than expanding HTTP
handlers. Separate pure/database marking, reconciliation/claiming and post-absence finalization so
transaction ownership is explicit and unit-testable. Keep `PhotoStorage` as the only filesystem path
authority and extend it only for safe inventory/anomaly reporting; never accept user paths.

The preferred schema shape is:

- `consultation_photos.image_id` becomes nullable while retaining its unique FK when present;
- `consultation_photos.media_deleted_at` is nullable and must be null while an open option has an
  image; after deletion it records the verified-absence completion time;
- `consultations.source_session_id` and `fingerprint` become nullable for completed terminal cleanup;
- `consultations.question` and `audience` become nullable for later terminal sanitization; `context`
  already is nullable; open-state constraints require valid non-null publication fields;
- current Private link columns may remain structurally present but terminal marking sets active false
  and terminal sanitization resets generation to its non-capability value;
- no new job/queue table is introduced because `PhotoUploadImage` already owns pending/failure state;
- no outcome/result schema is introduced by RF-37.

Use explicit SQL constraints so `state = 'open'` still requires question, valid audience,
source-session, fingerprint and non-null image associations for every open option. Terminal rows may
be detached/sanitized. Preserve the Vote composite FK to stable `ConsultationPhoto` IDs.

### Affected areas

- Backend models/migration: `backend/app/models.py`, new Alembic revision after
  `20261016_0005_votes.py`.
- Domain/services: new focused erasure module; narrow integration with `backend/app/cleanup.py`,
  `backend/app/photo_service.py`, `backend/app/storage.py` and lifecycle/access helpers.
- Startup/operations: `backend/app/main.py`, cleanup command/report and settings only if an existing
  value cannot be reused. Do not add a new configurable interval/alert duplicate.
- Consultation service/API: regression hardening only; no new public route. Existing reads must
  tolerate terminal-null fields only through their already minimal terminal projections.
- Frontend: no production feature change expected. Add regression tests only if strict response
  guards or terminal projections need protection.
- Deployment/docs: `docker-compose.yml` only if required for safe maintenance execution; README and
  an explicit restore/operations section. Keep the private volume mount and public isolation.
- Tests: focused erasure, cleanup, storage, access, migration and live PostgreSQL concurrency suites;
  disposable built-stack validation helper/override under `harness/validation` if useful.

### Data and migration requirements

- Inspect actual PostgreSQL constraints from revisions 0003–0005 before editing. Use Alembic, never
  model-only schema changes.
- Preserve every existing open consultation, selected image, source session, vote and storage key on
  upgrade. Open API behavior must be byte-for-byte compatible where schemas are unchanged.
- Rebuild affected checks explicitly so open rows cannot be created with nullable publication/media
  fields. Terminal nullability must not make publication accept missing data.
- Existing terminal rows are not destructively backfilled in the migration. Runtime reconciliation
  handles their media. Do not synthesize a final choice or participant outcome.
- The populated downgrade guard checks every irreversible indicator, including detached option image,
  media deletion timestamp, detached source session or sanitized terminal content. Refuse before
  dropping columns/constraints.
- File bytes remain external to Alembic. Upgrade/downgrade never unlinks, restores or moves them.

### API and integration requirements

- No new public API endpoint is approved.
- Existing protected APIs keep generic terminal unavailability and private `no-store`, `nosniff`,
  `no-referrer` headers. Anonymous response behavior is unchanged.
- The transaction-local marker accepts ORM/domain identifiers, not paths or external payloads. Its
  preconditions/errors are internal and explicit so consumers cannot accidentally call it after
  committing or without the consultation lock.
- The restricted cleanup command remains the operational interface. Preserve existing temporary
  cleanup output while adding deterministic machine/operator-readable counts and exit behavior.
- Publication must continue to reject absent/revoked bytes and to make one source session consumable
  exactly once. It must not race terminal cleanup for the same consultation/session.

### Security and privacy

- Database terminal state is authoritative before filesystem deletion. Never compensate a failed
  unlink by reopening, reactivating a link or rolling back a committed terminal state.
- Do not log or return image bytes, opaque keys, paths, filenames, raw storage exceptions, cookies,
  link tokens, question/context or account identity.
- Keep storage outside public roots and credentials/paths out of API/config responses.
- Treat every database key/path as untrusted even though server-generated; validate through
  `PhotoStorage` and fail closed.
- Never recursively delete a computed directory or follow symlinks. Work on exact validated files;
  anomalous files remain for restricted review.
- No historical photo volume may be restored under the supported runbook. A future backup design is
  a new product/security decision.
- DEC-023 minimization is an allowlist. Absence from the allowlist is not permission to keep data for
  analytics, debugging, moderation, models or possible future features.

## Implementation sequence

1. Add focused tests that capture the current RF-07/RF-10 storage graph, whole consumed-session
   manifest and strict terminal access before production changes.
2. Add and verify the additive Alembic migration plus ORM nullability/completion fields, open-state
   constraints, populated upgrade and irreversible-use downgrade refusal.
3. Implement the transaction-local whole-session revocation marker and tests for preconditions,
   rollback, idempotent existing states, Private deactivation and no commit/filesystem behavior.
4. Extend cleanup reconciliation to discover terminal source sessions, commit logical revocation,
   process every exact object, verify absence, handle partial failures and detach/remove visual rows
   only after success.
5. Add maintenance advisory leadership, busy behavior and real PostgreSQL multi-runner tests.
6. Add anomaly inventory/reporting without broad deletion; preserve RF-07 safe-age orphan/raw sweeps.
7. Implement post-session detachment and the explicit terminal minimization seam without fabricating
   RF-19/RF-20 outcomes or deleting required finalized choices prematurely.
8. Extend sanitized structured reporting, overdue exit behavior and operator documentation.
9. Document and test the supported database-only restore/pre-traffic reconciliation procedure.
10. Run full local and PostgreSQL suites, migration matrix, quality checks, Compose build and isolated
    built-volume/restart/failure/restore smoke; independently inspect the diff for scope and privacy.

## Validation strategy

### Automated tests

- Marker service: locked/open/consumed happy path; Public/Private; 2 and 10 options; entire-session
  leftover/failed/revoked rows; wrong owner/session/state; inconsistent association; rollback; no
  commit; no storage call; Private deactivation.
- Access: owner/reader/current and stale Private tokens, detail/photo/feed/link/vote all deny every
  terminal state before storage; open behavior unchanged; in-flight semantics are documented rather
  than falsely simulated as remote recall.
- Deletion: success, already absent, injected unlink failure, false-success presence, partial set,
  invalid key, unreadable storage and repeated pass. Only verified objects detach; failed keys remain.
- Reconciliation: terminal-ready legacy row, crash-shaped pending state, existing deleted row with
  present/absent bytes, malformed/unexpected object reporting, valid old orphan, recent uncommitted
  object, RF-07 abandoned/discarded/active/consumed regressions.
- Data minimization: selected option ID/ordinal survives; visual row/key/dimensions/attempt/error and
  consumed session disappear only after success; open consultation fields cannot be null; terminal
  schema permits future allowlisted sanitization; raw finalized votes are not deleted without a
  permitted replacement.
- PostgreSQL concurrency: vote versus each seeded terminal writer; two terminal targets first-commit
  semantics remain; two cleanup processes/advisory leadership; lock release after failure/connection
  close; `SKIP LOCKED`/partial retries; no cross-consultation deletion.
- Migration: fresh head; populated 0005 -> head preserving open photos/votes; open constraints;
  pre-use downgrade/upgrade; refusal after each irreversible indicator; no filesystem side effect.
- Reporting: exact counters, sanitized logs/output, busy command, transient failure, overdue 24-hour
  threshold and non-zero exit; readiness remains healthy.
- Full existing backend/frontend suites and quality checks remain green.

### Manual and built-stack validation

- Use an isolated Compose project and disposable database/photo volumes only. Build images and start
  healthy services.
- Create two accounts; publish real Public and Private consultations with selected and leftover
  images; cast votes; record exact database keys only inside the restricted disposable test harness.
- Exercise the RF-37 internal consumer seam through test-only/controlled database setup, never a new
  public product endpoint. Prove terminal HTTP denial immediately for owner/reader/link/photo/vote.
- Inject one storage deletion failure, run cleanup, prove access remains denied and only the failed
  key remains pending. Restart backend, prove startup retry and exact absence; unrelated open and
  active RF-07 images survive.
- Run two cleanup contenders and prove only one filesystem reconciliation leader.
- Exercise the restricted command's success, busy, failed and overdue exit/status output.
- Rehearse supported restore into a new empty photo volume with traffic disabled. Upgrade and run
  reconciliation before traffic; terminal content remains denied and no revoked bytes appear. Record
  that open photos are missing rather than silently reconstructed.
- Do not restore an old image snapshot even in ordinary validation as though it were supported.
- Stop and remove only the disposable project's services/volumes after evidence is captured.

### Commands

Use the repository's existing environments and exact commands, adjusting only disposable database
URLs/project names:

```powershell
Set-Location backend
..\.venv\Scripts\python -m ruff check app tests
..\.venv\Scripts\python -m ruff format --check app tests
..\.venv\Scripts\python -m mypy app
..\.venv\Scripts\python -m pytest

Set-Location ..\frontend
npm test -- --run
npm run format:check
npm run lint
npm run typecheck
npm run build
npm audit --audit-level=high

Set-Location ..
docker compose config --quiet
docker compose build backend frontend
```

Run live PostgreSQL suites with a disposable `TEST_DATABASE_URL`, including migration and
concurrency tests. Use a uniquely named disposable Compose project/override for the built smoke.
Run `python -m app.cleanup` only inside that disposable backend. Do not run cleanup, downgrade,
restore or volume removal against active/ordinary user data.

## Acceptance criteria

- [ ] A future terminal consumer can mark the complete unique consumed session for deletion inside
      its locked single database transaction without committing or touching storage.
- [ ] Terminal commit immediately denies every owner/reader/link/photo/vote authorization; a failed
      or delayed physical deletion never restores access.
- [ ] Every selected image, revoked leftover, failed attempt and registered object in the consumed
      session is handled; no path inference, public URL, original, derivative copy or archive exists.
- [ ] Physical completion requires explicit absence verification. Already absent is idempotent;
      partial/failing work retains exact retry data and succeeds after restart.
- [ ] After verified absence, visual/upload/session rows and metadata are removed while stable option
      identity/order and a minimal non-visual deletion marker survive.
- [ ] RF-07 active, removed, discarded and abandoned temporary uploads keep their accepted behavior.
- [ ] Startup, hourly and manual cleanup are restart-safe; PostgreSQL leadership prevents concurrent
      filesystem sweep; no worker/queue is introduced.
- [ ] Missing, malformed, unreadable and unexpected states fail closed, are observably reported and
      cannot block unrelated safe deletion or expand destructive scope.
- [ ] Sanitized metrics/logs and restricted status identify failures and overdue work; overdue status
      is non-zero, API readiness stays healthy and beta alert integration is documented.
- [ ] The supported PostgreSQL-plus-empty/current-photo-volume restore runs reconciliation before
      traffic and cannot resurrect revoked photos; historical photo snapshots are explicitly unsupported.
- [ ] The additive migration preserves populated open consultations/votes, enforces complete open
      rows, supports terminal detachment and refuses downgrade after irreversible use.
- [ ] DEC-023 allowlisting is explicit. RF-37 fabricates no outcome, retains no image/model/archive
      copy and does not delete finalized raw choices before an approved consumer persists outcomes.
- [ ] Real PostgreSQL vote/terminal and maintenance races, storage faults, migration matrix, Docker
      private-volume restart and supported restore evidence all pass on disposable resources.
- [ ] No RF-13/RF-19/RF-20/RF-32 public product action, moderation UI, account deletion, unrelated
      refactor, deployment, commit, push or Trello change is included.

## Dependencies and ordering

- RF-07 provides normalized private storage, durable temporary deletion fields and the maintenance
  baseline. Preserve its accepted contract and tests.
- RF-09/RF-10 provide current access, publication, source-session uniqueness and protected media.
- RF-11/DEC-033 provide terminal locking and first-commit semantics.
- RF-16 provides immutable votes and the shared consultation-row locking point.
- RF-18 provides open-only live counts and intentionally no terminal snapshot.
- RF-37 must be implemented first. RF-13 is the first intended real terminal consumer and proves
  deletion without outcomes. Coordinated RF-19/RF-20 follows with outcome transformation. Restricted
  RF-32 removal must consume the same boundary before beta. None is implemented in this plan.
- RF-21 later consumes only permitted photo-free participant outcomes.

## Risks and mitigations

- **Irreversible cross-store operation:** commit logical revocation first; retain exact durable work;
  verify absence before detaching metadata; never compensate by reopening.
- **Deleting the wrong object:** root the manifest in the unique consumed session and exact validated
  opaque keys; no recursive path/glob/consultation-ID inference.
- **Lost retry reference:** keep visual ledger/key until explicit absence; partial completion removes
  only proven objects.
- **Multiple maintenance replicas:** one PostgreSQL session advisory leader plus per-row locking;
  release in `finally` and prove crash recovery.
- **Old terminal fixtures:** reconcile media for privacy but do not fabricate outcomes or silently
  destroy unresolved non-visual data.
- **DEC-023 over-retention:** explicit allowlist and detachable schema; future consumers must persist
  replacements before sanitizing raw data.
- **Restore resurrects bytes:** never restore an older photo snapshot; empty/current volume and
  pre-traffic reconciliation are the only supported POC procedure.
- **Rollback expectation:** populated downgrade refusal explicitly communicates irreversibility.
- **Operational invisibility:** structured counts, immediate errors, overdue non-zero status and beta
  alert handoff without taking the API offline.

## Harness handoff notes

- Read `AGENTS.md`, every `harness/context` source-of-truth file, RF-37 grooming and this complete
  plan. Read complete approved RF-07, RF-09, RF-10, RF-11, RF-12, RF-16, RF-18 and RF-26 plans and
  relevant implementation reviews before editing.
- The worktree contains uncommitted RF-37 grooming/context/plan documentation owned by the
  coordinator. Preserve it exactly and implement around it. Do not reset, revert or overwrite
  unrelated files.
- Implement only RF-37 foundation. Do not implement the later terminal product actions to make tests
  convenient; use service-level or isolated fixture seams.
- Treat current code/constraints as evidence. If the approved nullable/detachment design conflicts
  materially with Vote integrity, current migrations or DEC-023, stop and report rather than silently
  keeping extra data or deleting stable option IDs.
- Do not commit, push, deploy, modify Trello, operate on ordinary/active volumes, generate native
  projects or launch agents. Keep code/tests/docs/report in English.
- Product-owner visual validation is not relevant unless a production UI unexpectedly changes; if it
  does, that is likely out of scope and must be reported.

## Resolved grooming decisions

- `1A`: terminal database revocation/deletion request commits before physical work.
- `2B`: delete every object/attempt in the consultation's unique consumed source session.
- Refined `3C`: retain retry ledger only while pending/failed; after verified absence remove visual
  ledger/metadata and keep stable option identity/order plus minimal completion marker.
- `4A`: explicit absence verification defines physical completion.
- `5A`: votes and terminal writers serialize on the consultation row; first terminal commit wins.
- `6A`: immediate revocation is request-time authorization; a request authorized earlier may finish.
- `7A`: startup/hourly/manual maintenance with narrow PostgreSQL advisory leadership; no worker.
- `8A`: reconcile known drift; missing is idempotent; partial remains pending; anomalies are reported
  and left for restricted handling rather than ignored or broadly deleted.
- `9A`: sanitized metrics/logs, 24-hour overdue failing status and beta operator alert integration;
  readiness remains healthy.
- `10A`: supported restore is PostgreSQL plus empty/current photo volume and pre-traffic reconcile;
  old photo snapshots are forbidden.
- `11A`: allowlist terminal persistence to DEC-023 and remove disallowed data when the owning consumer
  has produced permitted replacements.
- `12A`: additive compatible migration with irreversible-use downgrade refusal.
- `13A`: require the full unit/PostgreSQL/storage/migration/Docker/restart/status/restore matrix.
- `14A`: RF-37, then RF-13, then coordinated RF-19/RF-20, with restricted RF-32 before beta.

## Remaining questions

None
