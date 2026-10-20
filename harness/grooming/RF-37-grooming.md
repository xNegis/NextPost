# RF-37 - Proteger y borrar fotografías - Grooming

## Status

`Ready for implementation`

Selected by the product owner on 2026-10-19. This file records the complete read-only Trello
intake, repository-first investigation and the first proposed material decision batch. Every
recommendation remains unaccepted until the product owner confirms it. On 2026-10-19 the owner
confirmed `1A 5A 6A`, selected `2B` while explicitly saying that option A was not understood, and
selected `3C 4B`. Q2 therefore remains open for an informed confirmation. Q3C/Q4B remain open
because, as originally defined, their combination would discard the only durable retry reference
without verifying file absence and would contradict the ticket's binding verifiable-deletion and
retry criteria. After a concrete example, the owner confirmed `2B`, a refined `3C` and `4A`:
delete every object belonging to the consumed source session; retain retry data only while work is
pending; after verified absence, remove the visual ledger and metadata while preserving the stable
option and a non-visual deletion-completion marker. The owner then accepted every recommended
second-batch choice, `7A 8A 9A 10A 11A 12A 13A 14A`. No material question remains. The settled
scope and plan finalisation were explicitly approved on 2026-10-19, together with an autonomous
harness launch. `harness/features/RF-37-Implementation-plan.md` is the self-contained English
contract marked `Ready for implementation` with `Remaining questions: None`.

## Trello snapshot

- Title: `RF-37 · Proteger y borrar fotografías`
- URL: https://trello.com/c/Dodf7k4R/40-rf-37-proteger-y-borrar-fotograf%C3%ADas
- Short URL: https://trello.com/c/Dodf7k4R
- Board: `APP - NextPost`
- Board ID: `ari:cloud:trello::board/workspace/6aa9032829f8b45ead46cfdd/6aa903892e7d7b54f23fae1b`
- Card ID: `ari:cloud:trello::card/workspace/6aa9032829f8b45ead46cfdd/6aa90c13e51db9dc577a4123`
- List: `Próximo · completar el MVP`
- List ID: `ari:cloud:trello::list/workspace/6aa9032829f8b45ead46cfdd/6aa903892e7d7b54f23fae23`
- Labels: None; no omitted labels reported.
- Members: None
- Checklists: None; no omitted checklists reported.
- Comments: None; the complete comments read reported no next page.
- Attachments: None; the complete attachments read reported no next page.
- Custom field values: None; the complete values read reported no next page.
- Start date / due date: None / None
- Archived: False
- Card completion / due completion: False / False
- Position: `98304`
- Captured on: `2026-10-19T17:30:22.5064539+02:00`; read-only connector intake.
- Last Trello activity at intake: `2026-10-12T11:27:49.033Z`
- Available activity: card created on `2026-09-15T09:12:52.058Z`; moved from
  `Funcionalidades` to the then-named `Fase 2` list on `2026-09-22T14:33:41.749Z`.
- Intake consistency: RF identifier, title, configured board, current list and content agree. The
  live list name reflects the 2026-10-12 backlog reorganization. No Trello mutation was performed.

### Description and acceptance criteria at intake

**Reorganización del backlog · 2026-10-12**

Parte temporal ya implementada en RF-07; falta el ciclo de fotos publicadas al finalizar, eliminar
o retirar, con borrado físico verificable y reintentos. Grooming de este contrato debe coordinarse
antes de las mutaciones RF-13/RF-19/RF-20 y de la retirada manual mínima de RF-32. Se conserva la
persistencia ordinaria sin nuevas copias de fotos de DEC-032.

Ubicación: Próximo · completar el MVP. El repositorio es la fuente de estado y especificaciones
aceptadas. Esta organización no aprueba un plan ni lanza implementación.

---

**Descripción conservada del ticket**

**Historia de usuario**

Como autor, quiero que mis fotos solo estén disponibles mientras la consulta las necesita y que se
borren al terminarla.

**Criterios de fase 2 acordados**

- Las fotos procesadas se sirven desde almacenamiento privado con comprobaciones de cuenta,
  audiencia y estado en cada acceso; no hay archivos públicos permanentes. Los originales se
  descartan tras procesar.
- Finalizar, eliminar o retirar manualmente por el administrador corta el acceso de inmediato e
  inicia el borrado de todas las fotos y derivados, sin conservación de 30 días para el autor.
- Las subidas abandonadas se limpian; fallos de borrado se detectan y reintentan sin reabrir el
  acceso. Una restauración no vuelve a exponer fotos retiradas.
- Después de finalizar permanecen únicamente los datos no visuales de resultado permitidos por
  DEC-023. No se retienen fotos para analítica o modelos.

Referencia: DEC-012/016/021/022/023. Almacenamiento, copias y recuperación se concretan en el plan
técnico.

## Intended outcome

RF-37 should establish one reusable published-media revocation and physical-erasure contract that
the later RF-13 author deletion, RF-19/RF-20 finalization and restricted RF-32 administrator removal
writers must call. A terminal transaction makes every protected detail, photo, link and vote request
fail from current database state before any fallible filesystem work begins. Physical deletion then
converges through idempotent startup, periodic and restricted manual maintenance, without ever
changing the consultation back to an accessible state.

The increment must extend, not replace, RF-07's accepted temporary-upload cleanup. It should not
implement the product actions that choose a terminal state or calculate final outcomes.

## Binding decisions inherited by RF-37

- Finalization, author deletion and administrator removal revoke photograph access immediately and
  start deletion with no 30-day buffer (DEC-021/022).
- No photograph, derivative, original, archive, analytics copy or model-training copy is retained.
  Only the minimum non-visual result data in DEC-023 may survive.
- Uploaded originals and raw temporary files are already discarded by RF-07 after processing or
  failure; abandoned uploads remain under DEC-012/016/025/026 and the implemented RF-07 contract.
- Storage stays private. Every content request is authenticated and re-authorized against current
  account, audience, link and lifecycle state; URLs and UI state confer no authority
  (DEC-022/028/029).
- Ordinary published-photo persistence across app close and service restart is sufficient for the
  POC. No image backup, versioning or special disaster-recovery infrastructure is added (DEC-032).
- `open`, `finalized`, `deleted` and `removed` are the only persisted consultation lifecycles.
  Terminal writers lock and re-read the consultation; first terminal commit wins and exact retries
  need operation/payload proof (DEC-033).
- RF-37 must define this shared contract before RF-13 and RF-19/RF-20 are implemented. The restricted
  administrator removal subset must consume the same path; no separate or weaker purge exists.

## Current code findings

### Storage and RF-07 temporary lifecycle

- `backend/app/storage.py::PhotoStorage` stores only normalized JPEG bytes under a backend-owned
  `normalized/<two-character-shard>/<opaque-uuid-hex>` path and raw processing files under `tmp`.
  Keys are validated and server-generated; neither directory is exposed by Nginx.
- `backend/app/imaging.py` normalizes accepted still JPEG/PNG/WebP/HEIC/HEIF inputs to one bounded
  JPEG, preserving visible orientation while discarding source metadata. There is currently no
  thumbnail, preview derivative, original or alternate published copy to discover.
- `PhotoUploadImage` is the single file ledger. It already has `ready`, `revoked` and `deleted`
  states plus `deletion_requested_at`, `deletion_completed_at`, `deletion_attempts` and a bounded
  non-sensitive `last_deletion_error`. This is enough to represent pending, completed and failed
  deletion without inventing a general queue.
- RF-07 removal/discard/abandonment first marks image rows revoked and commits. Cleanup then deletes
  the exact storage key, calls `exists`, and marks completion only after absence. Missing files are
  already idempotent success because `unlink(missing_ok=True)` plus `exists == false` converges.
- `backend/app/cleanup.py` runs at API startup, every configured hour and through the restricted
  `python -m app.cleanup` command. It uses PostgreSQL `FOR UPDATE SKIP LOCKED` for row work, retries
  failures, logs overdue deletion after the configured 24-hour alert age, exits non-zero from the
  manual status path when overdue work remains, removes stale raw files and sweeps old unreferenced
  normalized objects.
- The orphan sweep intentionally protects files newer than one cleanup interval so it cannot delete
  a normalized object written by an upload transaction that has not committed yet. Unknown files
  outside the accepted opaque-key/partial-name grammar are ignored rather than deleted blindly.

### RF-10 publication and published reads

- Publication does not copy or move bytes. RF-10 marks the upload session `consumed` and creates
  ordered `ConsultationPhoto` rows whose `image_id` points to the same ready `PhotoUploadImage`.
  Selected normalized bytes therefore remain in the same private volume and ledger.
- Unselected objects are revoked during publication. The RF-07 cleanup keeps selected published
  objects because their image row remains `ready`; a consumed session is never abandoned.
- Published detail and photo reads reload current `Consultation` state and use the shared strict-open
  access policy before reading `ConsultationPhoto`, `PhotoUploadImage` or storage. Any terminal state
  is generic unavailable for owner and participant alike. A ready row with missing bytes is a
  retryable 503, not a terminal-state disclosure.
- Private-link state is not currently disabled by a terminal mutation because no terminal writer
  exists. Nevertheless strict lifecycle authorization already makes a terminal target unavailable.
  The eventual writer should still deactivate the current capability in its database transaction
  as defence in depth and to prevent accidental future reuse.

### RF-11, RF-16 and concurrency

- RF-11 supplies only the pure transition decision and lock/commit protocol. It explicitly requires
  database side effects and terminal state to commit once before RF-37 filesystem deletion.
- `Vote` has restrictive consultation/option foreign keys and an immutable per-consultation/account
  uniqueness rule. Vote submission locks the consultation row `FOR UPDATE`, re-authorizes current
  open state and commits under that lock. A terminal writer using the same lock therefore serializes
  correctly: either the vote commits first and must be included by finalization, or terminal state
  commits first and the vote is denied.
- Protected detail/photo reads do not lock. They authorize from one current snapshot and then read
  storage. A request authorized before terminal commit may finish with already-started bytes; every
  request authorizing after the commit is denied. DEC-029 already accepts the analogous fact that
  bytes loaded before link revocation cannot be remotely recalled.
- RF-18 live aggregates are derived from current `Vote` and `ConsultationPhoto` rows. It deliberately
  creates no finalized snapshot. RF-19/RF-20 must persist DEC-023 aggregates/outcomes in the same
  terminal transaction before raw vote-choice and image-related data can be reduced.

### Data-model implications

- `ConsultationPhoto` is both the immutable product option identity/order and the link to the image
  ledger. `Vote.consultation_photo_id` references that option, not the storage row. Stable option IDs
  and ordinals can therefore survive without bytes and are allowed by DEC-023.
- The current `ConsultationPhoto.image_id` is non-null and `RESTRICT`; the image ledger row cannot be
  removed while the option exists. Marking it `deleted` and scrubbing visual/file fields is compatible
  with current relationships, but retaining upload-attempt/session metadata indefinitely may exceed
  DEC-023's minimum. This needs an explicit retention choice rather than an implicit migration.
- Existing published consultations require no key discovery backfill: their association graph already
  identifies every promoted normalized object. Existing terminal fixtures may still point to ready
  files because real terminal writers do not exist; startup/manual recovery must reconcile terminal
  consultations into deletion-pending state.

### Docker, maintenance and recovery

- Compose has one private named volume mounted only at `/app/data` in the backend and a separate
  PostgreSQL volume. The backend runs Alembic before accepting traffic, and FastAPI's lifespan runs
  cleanup before yielding startup, then starts the periodic loop.
- The current backend service is a single instance. Row locking supports concurrent cleanup workers,
  but the filesystem orphan scan has no cluster-wide lease. RF-37 should not claim multi-replica
  safety without either constraining operation to one maintenance leader or adding a narrow lock.
- README explicitly says both local volumes are retained by ordinary `docker compose down`, warns
  that Alembic rollback does not remove or expose the photo volume, and documents the restricted
  cleanup/status command. There is no implemented backup job, snapshot policy or restore runbook.
- Under DEC-032 the supported POC restore can restore PostgreSQL into an empty/current private-photo
  volume; restoring an older image-volume snapshot would be a new, unsupported image backup path and
  could violate revocation unless a later design also restores a newer external tombstone journal.

## Dependencies and conflicts

- **RF-07:** keep its 24-hour renewable temporary lease, immediate Remove/Cancel revocation,
  startup/hourly/manual cleanup and raw/orphan rules unchanged. Published deletion should reuse the
  same storage and maintenance primitives.
- **RF-09/RF-10/RF-26:** current request-time account/audience/link/lifecycle checks remain the only
  read authority. RF-37 must not introduce public URLs, signed permanent media URLs or caching.
- **RF-11:** supplies lifecycle values and the first-terminal-commit-wins protocol; RF-37 supplies a
  transaction-local media-revocation helper and post-commit purge, not a competing state machine.
- **RF-12:** owner views already omit photos for finalized state and exclude deleted/removed rows.
  Future consumer work must preserve that photo-free projection without broken thumbnails.
- **RF-16/RF-18:** live votes and aggregates exist. RF-37 cannot erase option identities or vote
  choice rows before RF-19/RF-20 creates the permitted photo-free outcome representation.
- **RF-13:** author deletion must use the RF-37 contract. Deleting an open consultation creates no
  outcome; the RF-13 plan must decide removal of votes and disallowed content in its atomic writer.
- **RF-19/RF-20:** must be groomed and implemented as one observable declaration/finalization
  operation. It persists final selection, aggregates and participant outcomes before requesting
  media deletion in the same database transaction.
- **Restricted RF-32 subset:** administrator removal must use the identical lock, logical revocation
  and physical-deletion path. Public moderation UI, reports, account suspension and a broad admin
  console remain deferred.
- **RF-21:** consumes only DEC-023 private photo-free outcomes and must never depend on deleted image
  bytes or retained per-voter photo choices.

## Candidate approach

Provide a focused domain/service boundary with two phases:

1. A terminal consumer locks the `Consultation`, proves authorization and transition identity,
   persists its own required outcome/deletion semantics, deactivates any Private capability, marks
   every associated ready image `revoked` with a deletion request, writes the terminal lifecycle and
   commits once. RF-37 exposes the marker operation but never chooses the terminal lifecycle.
2. Existing startup/hourly/manual maintenance claims deletion-pending image rows with
   `FOR UPDATE SKIP LOCKED`, deletes the exact normalized key, verifies absence and records success
   or a sanitized retryable failure. Recovery also discovers terminal consultations whose linked
   image is still ready and marks them pending before touching files.

Keep the existing in-process maintenance instead of adding a broker/worker. Constrain a deployment
to one filesystem sweep leader (the current Compose topology) or add one narrow PostgreSQL advisory
lock around orphan scanning if multi-instance operation must be supported. Do not build general job
infrastructure.

## Questions

### Resolved decision batch 1: revocation, deletion ledger and concurrency

#### Q1 - Where is the immediate-revocation boundary?

**Confirmed 2026-10-19: A.**

- **A (recommended): database-first two-phase deletion.** The terminal consumer atomically writes
  terminal state, disables the Private capability and marks all linked images deletion-pending;
  physical deletion happens after commit. Product access is revoked at commit even if storage is
  down. This matches DEC-021/033 and RF-07's proven pattern.
- **B: delete files inside the terminal transaction.** A filesystem error makes the product action
  fail or hold locks for an unbounded time; a database rollback cannot restore already deleted
  bytes. This couples two non-transactional systems and makes recovery unsafe.
- **C: commit terminal state and discover files later without durable per-file markers.** Access is
  safe, but crashes and partial deletion cannot be distinguished or reliably retried.

Risk/trade-off: A gives immediate logical revocation and eventual physical convergence, not an
instantaneous filesystem guarantee. **Recommendation: A.**

#### Q2 - Which stored objects form the deletion set?

**Confirmed 2026-10-19 after clarification: B.** One consumed upload session can produce exactly
one consultation. The deletion set therefore includes every image/attempt belonging to that source
session, including selected published images and any already-revoked leftover. Repeated deletion of
an already absent leftover remains idempotent. No cross-consultation object can share the session.

- **A (recommended): association-led manifest.** Resolve every `ConsultationPhoto.image_id` under
  the terminal transaction and enqueue its `PhotoUploadImage.storage_key`; include every future
  derivative only if it is first represented in the same durable ledger/manifest. Current scope is
  exactly one normalized JPEG per option. Continue RF-07's separate raw/temp/orphan rules.
- **B: delete the whole source upload session.** This is simple today but binds published lifecycle
  to temporary-session internals and can accidentally include unrelated or already-revoked attempts.
- **C: scan filenames/directories by consultation ID.** Current opaque keys contain no consultation
  ID; path inference would be unreliable and unsafe.

Risk/trade-off: A requires a database query per terminal operation but is exact, auditable and
future-proof. **Recommendation: A.**

#### Q3 - Which durable deletion states and metadata should remain?

**Confirmed 2026-10-19: refined C.** Keep the existing image ledger, exact key and retry metadata
while deletion is pending or failed. Only after Q4A verifies absence, detach/delete the visual
`PhotoUploadImage` record and its storage key, dimensions, byte length, upload attempt and error
metadata. Preserve only the stable `ConsultationPhoto` option identity/ordinal and a minimal
non-visual `media_deleted_at`-style completion marker. This requires an explicit migration rather
than deleting option identities or losing retry data.

- **A (recommended): reuse the existing image ledger.** `ready -> revoked/deletion pending ->
  deleted`, with requested/completed timestamps, attempt count and sanitized last error. Treat a
  failed attempt as still pending plus error metadata, never as a state that authorizes reads. After
  verified completion, scrub `storage_key`, dimensions, byte length and error detail while retaining
  only the minimum option identity plus a completion tombstone needed for safety/audit.
- **B: add a separate general job/queue table and leave current image rows unchanged.** Cleaner
  queue semantics but duplicates RF-07 machinery and risks retaining disallowed metadata.
- **C (selected after refinement): delete the visual ledger only after verified absence.** Keep the
  stable option row and a non-visual completion marker, but remove image/upload metadata. Pending
  and failed work retains its exact key until it succeeds.

Risk/trade-off: refined C requires a focused migration to detach the stable option/deletion
tombstone from visual upload metadata, but satisfies both retry safety and DEC-023 minimization.
**Confirmed selection: refined C.**

#### Q4 - What counts as a successful physical purge?

**Confirmed 2026-10-19 after clarification: A.** The storage delete call is followed by an explicit
absence check before visual ledger data is discarded. Already absent is idempotent success; partial
sets retain exact pending references for the remainder.

- **A (recommended): verified absence for every manifest key.** `delete` is idempotent; a file
  already absent counts as success, but completion is recorded only after an explicit absence check.
  Partial success leaves only remaining keys pending. Invalid keys or unreadable storage fail closed,
  remain pending and raise restricted operational evidence.
- **B: a successful delete-system-call return.** Faster, but cannot prove the object is absent and
  does not meet the ticket's verifiable-deletion criterion.
- **C: directory/orphan sweep alone.** Cannot attribute completion to a consultation or detect a
  protected reference that was missed.

Risk/trade-off: A performs an extra filesystem check but turns absence, partial deletion and retries
into deterministic states. **Recommendation: A.**

#### Q5 - How should terminal operations race with votes and other terminal writers?

**Confirmed 2026-10-19: A.**

- **A (recommended): one consultation-row serialization point.** Every vote and terminal writer
  locks the same consultation row. A finalization that obtains the lock after a committed vote must
  include it; a vote that obtains it after terminal commit is denied. Finalize/delete/remove have no
  priority: first terminal commit wins, and retries require the owning consumer's exact operation and
  payload proof.
- **B: give administrator removal or deletion priority.** PostgreSQL cannot retroactively cancel an
  already committed competing terminal operation; product priority would create ambiguous outcomes.
- **C: rely only on state checks without a lock.** A late vote or two different terminal outcomes can
  commit across one another.

Risk/trade-off: A can make a terminal action briefly wait for an in-flight vote, but yields one
linearizable result and matches DEC-033. **Recommendation: A.**

#### Q6 - What does immediate revocation mean for a photo read already in flight?

**Confirmed 2026-10-19: A.**

- **A (recommended): request-time authorization boundary.** A read that authorizes before terminal
  commit may finish; every authorization beginning after commit is denied. Already rendered/browser
  bytes cannot be recalled. The server never issues a new successful authorization after commit.
- **B: make reads hold a shared database lock until all bytes are delivered.** This can delay or
  starve terminal actions on slow clients and complicates streaming; it still cannot erase bytes
  already received by the device.
- **C: attempt client polling/push recall.** Adds infrastructure and cannot guarantee removal of
  already loaded bytes.

Risk/trade-off: A is the strongest enforceable rule with the current request/response architecture
and is consistent with DEC-029, but it must be stated honestly. **Recommendation: A.**

### Resolved decision batch 2: recovery, operations, retention and rollout

#### Q7 - How should retries and recovery be executed?

**Confirmed 2026-10-19: A.**

- **A (recommended): extend the existing narrow maintenance path.** Run one reconciliation pass
  before API startup, every configured hour and through the restricted manual status command. Use
  row claims plus one non-blocking PostgreSQL advisory lock for filesystem/orphan reconciliation so
  multiple API replicas cannot sweep concurrently. A replica that does not acquire the maintenance
  lock skips that pass. No broker or new service.
- **B: add a dedicated worker/queue service.** It isolates filesystem work but introduces deployment,
  delivery and monitoring infrastructure disproportionate to the current POC.
- **C: startup and manual cleanup only.** Simpler, but a long-running healthy API may leave failures
  pending indefinitely until restart or operator intervention.

Risk/trade-off: A retains an in-process task, so the API process owns maintenance leadership, but
the durable database ledger makes restarts safe. **Recommendation: A.**

#### Q8 - How should recovery and anomalous storage states behave?

**Confirmed 2026-10-19: A.**

- **A (recommended): reconcile exact known state and fail closed on anomalies.** A terminal
  consultation whose consumed session still has ready images is converted to deletion-pending
  before files are touched. Missing known files are verified idempotent success; partial sets retain
  remaining keys; valid old opaque orphan/partial files are swept after the safe age. Invalid keys,
  unreadable paths and unexpected filenames are never served or silently deleted: leave them
  untouched, count/log them and require restricted operator resolution.
- **B: ignore anomalous rows/files and continue without reporting them.** Keeps normal cleanup
  moving but can conceal retained user data indefinitely.
- **C: abort the complete cleanup pass on the first anomaly.** Makes problems visible but one bad
  object can block unrelated deletions and increase retention.

Risk/trade-off: A may require operator handling for malformed foreign files, but neither hides nor
amplifies destructive scope. **Recommendation: A.**

#### Q9 - What observability and alert contract is required?

**Confirmed 2026-10-19: A.**

- **A (recommended): structured pass metrics plus a restricted failing status check.** Log counts
  for discovered, requested, completed, already absent, failed, overdue and anomalous objects; log
  no keys/paths/content. Each failure is visible immediately; pending work older than the existing
  configurable 24-hour threshold emits an error and makes the restricted status command non-zero.
  Before beta, the deployment must route that error/non-zero check to the operator's alert channel.
  Readiness remains healthy so deletion trouble cannot take the API offline or reopen access.
- **B: alert on every failed attempt as an incident.** Fastest signal but likely noisy for transient
  filesystem errors that the next hourly pass resolves.
- **C: fail `/api/ready` while any deletion is pending/failed.** Highly visible but can cause restart
  loops or total outage without improving erasure.

Risk/trade-off: A allows up to the configured retry/alert window before escalation, while failures
remain denied and visible in logs immediately. **Recommendation: A.**

#### Q10 - Which backup and restore procedure is supported for the POC?

**Confirmed 2026-10-19: A.**

- **A (recommended): database restore with an empty or current photo volume, never an older photo
  snapshot.** Keep the private image volume outside backup/versioning under DEC-032. Restore with
  public traffic disabled, run migration plus RF-37 reconciliation/status, then enable traffic.
  Restoring only PostgreSQL may lose photographs belonging to still-open consultations; that is the
  already accepted POC durability limitation. It cannot resurrect revoked bytes because an old
  photo-volume copy is never restored.
- **B: back up photographs and add an external monotonic deletion/tombstone journal that is always
  newer than any restored image snapshot.** Supports recovery of open photos but adds new image
  backup/versioning and recovery infrastructure explicitly excluded by DEC-032/current scope.
- **C: restore matching historical PostgreSQL and photo-volume snapshots, then run cleanup from the
  restored database.** A snapshot taken before revocation sees the consultation as open and can
  expose the restored bytes; it cannot meet the non-resurrection guarantee.

Risk/trade-off: A prioritizes privacy over recovery of open photographs after disaster.
**Recommendation: A.**

#### Q11 - What database content may remain after terminal purge?

**Confirmed 2026-10-19: A.**

- **A (recommended): enforce a terminal allowlist derived from DEC-023.** After verified media
  absence, remove upload sessions/attempts, storage keys, dimensions, byte lengths, question,
  context, audience/link capability and publication fingerprint when no longer needed. Retain only
  consultation/owner and option identifiers, relevant dates/state, stable option ordinals, the
  deletion-completion marker, declared option IDs, aggregate counts and participant
  `Matched`/`Not matched`/`No choice` outcomes. RF-19/RF-20 must transform raw `Vote` choices before
  they are removed; RF-13/removal before finalization deletes them without outcomes.
- **B: minimize only image bytes and image metadata in RF-37, leaving question/context/link/upload
  metadata indefinitely for later tickets.** Smaller migration now but violates the requested
  exclusive DEC-023 retention boundary unless another approved ticket later performs it atomically.
- **C: delete the complete consultation and all result records after purge.** Strong minimization but
  destroys the private non-visual results DEC-023 explicitly permits/requires.

Risk/trade-off: A requires terminal consumers to populate their permitted result fields before the
same transaction applies sanitization; RF-37 defines the allowlist/seam but does not invent those
consumer outcomes. **Recommendation: A.**

#### Q12 - How should migration, existing data and rollback work?

**Confirmed 2026-10-19: A.**

- **A (recommended): additive compatibility migration followed by irreversible-use guard.** Add the
  minimal nullable/detachable media and completion fields plus terminal allowlist support. Existing
  open consultations need no backfill and remain readable. Existing terminal rows are marked for
  reconciliation at startup. Deploy the migration before new code; keep old open-read code
  compatible during rollout. Downgrade is allowed only before any row has been detached/sanitized;
  once physical deletion or terminal minimization occurs, fail downgrade with an explicit operator
  message because lost bytes/fields cannot be reconstructed.
- **B: no migration; retain current non-null image/session/text relationships and mark image rows
  deleted forever.** Avoids rollout work but contradicts confirmed 3C and Q11 minimization.
- **C: rewrite/backfill every existing open consultation into a new media model before deployment.**
  Creates unnecessary risk and downtime for data that already identifies its source session.

Risk/trade-off: A makes rollback intentionally asymmetric after destructive work, which is more
honest than pretending a code rollback restores erased data. **Recommendation: A.**

#### Q13 - What validation evidence is required before claiming RF-37 complete?

**Confirmed 2026-10-19: A.**

- **A (recommended): the complete layered matrix.** Unit/service tests, real PostgreSQL constraints
  and vote/terminal races, injected storage failures and partial sets, fresh/populated migration and
  downgrade refusal, full regressions, built Docker private-volume smoke, startup/restart recovery,
  restricted status/alert behavior and a supported database-only restore rehearsal. Use disposable
  data/volumes and verify exact file absence plus survival of unrelated open and RF-07 temporary
  media.
- **B: unit tests and local filesystem tests only.** Fast but does not prove PostgreSQL locking,
  migration behavior, container volumes or restart convergence.
- **C: rely mainly on manual Docker inspection.** Exercises the stack but cannot deterministically
  cover races, injected errors and idempotency.

Risk/trade-off: A costs more validation time but the feature is an irreversible privacy boundary.
**Recommendation: A.**

#### Q14 - What implementation order should consumers follow?

**Confirmed 2026-10-19: A.**

- **A (recommended): RF-37 foundation, then RF-13, then coordinated RF-19/RF-20, with restricted
  RF-32 removal consuming the same contract before beta exposure.** RF-13 is the simplest real
  terminal consumer and proves deletion-without-outcome. RF-19/RF-20 then adds the more complex
  declared selection and DEC-023 outcome transformation. Administrator removal never gets a
  separate purge implementation.
- **B: RF-37, then RF-19/RF-20, then RF-13.** Delivers the main finalization loop earlier but makes
  the first consumer also carry the hardest outcome migration and concurrency surface.
- **C: implement RF-13, RF-19/RF-20 and administrator removal inside RF-37.** Reduces handoffs but
  skips their separate grooming/approval gates and exceeds this ticket's explicit scope.

Risk/trade-off: A adds one consumer integration step before finalization but validates the shared
contract on the smaller terminal operation first. **Recommendation: A.**

### Open

- None.

### Resolved

- 2026-10-19, Q1A: terminal consumers commit database revocation and deletion requests before
  fallible physical deletion.
- 2026-10-19, Q2B after clarification: delete every image/attempt belonging to the consultation's
  unique consumed source session; repeated cleanup of already absent leftovers is idempotent.
- 2026-10-19, refined Q3C: keep exact retry state while pending/failed, then remove the visual ledger
  and metadata after verified absence while preserving stable option identity/ordinal and a minimal
  deletion-completion marker.
- 2026-10-19, Q4A after clarification: only an explicit absence check completes physical purge;
  already absent is success and partial sets retain remaining references.
- 2026-10-19, Q5A: votes and all terminal writers serialize on the consultation row; first terminal
  commit wins with no priority hierarchy.
- 2026-10-19, Q6A: immediate revocation is the request-time authorization boundary; a read already
  authorized before terminal commit may finish, while no later authorization succeeds.
- 2026-10-19, Q7A: reuse startup, hourly and restricted manual maintenance; serialize filesystem
  reconciliation with a narrow non-blocking PostgreSQL advisory lock, without a worker/queue.
- 2026-10-19, Q8A: reconcile known terminal/media drift, treat verified absence idempotently, retain
  partial pending keys and report rather than silently delete malformed/unexpected objects.
- 2026-10-19, Q9A: emit sanitized structured cleanup counters and immediate failure logs; overdue
  work at the existing configurable 24-hour threshold fails restricted status and must be connected
  to an operator alert channel before beta, without failing API readiness.
- 2026-10-19, Q10A: the supported POC restore uses PostgreSQL with an empty/current photo volume,
  never an older photo snapshot; migration and reconciliation complete before traffic.
- 2026-10-19, Q11A: terminal persistence is allowlisted to DEC-023 minimum identifiers, dates,
  option/deletion markers, declared selections, aggregates and private outcomes. Disallowed text,
  link, upload, visual and raw-choice data is removed when its consumer transaction permits.
- 2026-10-19, Q12A: use an additive compatible migration and refuse downgrade after irreversible
  detach/sanitization/deletion; existing open rows need no rewrite and terminal rows reconcile.
- 2026-10-19, Q13A: completion requires the full unit/PostgreSQL/storage/concurrency/migration/
  Docker/restart/status/restore validation matrix on disposable resources.
- 2026-10-19, Q14A: implement RF-37 first, RF-13 as the first real consumer, coordinated RF-19/RF-20
  next, and restricted RF-32 removal on the same contract before beta exposure.
- Binding inherited decisions are listed above and are not reopened.

## Proposed scope

### In scope

- Reusable database-first media-revocation marker callable inside a terminal consumer transaction.
- Discovery of every published normalized object through durable consultation-photo associations.
- Immediate strict-open denial for owner, reader, link, feed, result-photo and vote consumers after
  terminal commit; Private capability deactivation as defence in depth.
- Durable pending/completed/failure evidence, idempotent verified physical deletion and retries.
- Startup, periodic and restricted manual reconciliation, including terminal rows missed by a crash
  or older code and old unreferenced normalized/partial objects under safe age rules.
- Safe handling of already absent, partially deleted, invalid, unexpected and storage-unavailable
  cases without reopening access or claiming false completion.
- Observability/status, Docker private-volume behavior and a supported restore procedure that cannot
  re-expose revoked photos.
- Compatibility/backfill and migration/rollback rules for existing consultations.
- Contract and test seams consumed later by RF-13, RF-19/RF-20 and restricted RF-32 removal.
- Explicit preservation of only DEC-023-permitted result/option data after finalization and purge.

### Out of scope

- Complete finalization and final-choice persistence or UI (RF-19/RF-20).
- Author deletion mutation or confirmation UI (RF-13).
- Public report/moderation UI, suspension, inbox or broad administrator console (RF-30–RF-32).
- Account deletion/anonymization (RF-34).
- New image copies, thumbnails, versioning, backups, archives, analytics/model datasets or retained
  moderation evidence.
- A general broker, worker platform or queue infrastructure unless later evidence proves the narrow
  existing maintenance loop insufficient.
- Changes to RF-07's accepted abandoned-upload lease/cleanup contract.
- Unrelated product, feed, voting, result, navigation or delivery changes.

## Validation outline

### Unit and service tests

- Exact association-led manifest for 2–10 photos; duplicate/cross-consultation/missing image rows;
  no original or unregistered derivative path.
- Marker helper performs no commit, chooses no terminal state, requires a locked/open consumer
  context and is idempotent only for an identical terminal operation.
- Every protected read/link/vote path denies from terminal state before storage access; deletion
  failure cannot change that result.
- Delete already absent, success, injected failure, partial set, invalid key and failed absence
  verification; state/timestamps/attempt/error and metadata scrubbing are exact.
- Startup/periodic/manual recovery marks terminal-ready associations, retries pending work, preserves
  open ready images and leaves unknown malformed files for operator attention.

### PostgreSQL and concurrency tests

- Real `FOR UPDATE` races: vote versus each terminal target; finalize versus delete/remove; two
  cleanup claimers; retry of same/different terminal payload; marker transaction rollback.
- Existing open published rows need no backfill; seeded terminal-ready rows reconcile safely.
- Direct constraints prevent a photo or deletion record belonging to a different consultation.
- Fresh upgrade, previous-head upgrade with populated consultations/votes, rollback rules and any
  populated-downgrade refusal are verified against PostgreSQL, not only `create_all`.

### Storage, Docker and recovery tests

- Built Compose uses isolated PostgreSQL/photo volumes. Publish real images, terminally seed or use
  the eventual consumer seam, prove immediate HTTP denial, inject deletion failure, restart backend,
  observe retry and verify every exact key absent while unrelated open and temporary images survive.
- Exercise startup sweep, periodic pass and restricted status command, including non-zero overdue
  status and structured counts. Stop/remove only disposable project resources.
- Restore a database backup into the supported empty/current photo-volume configuration, run
  pre-traffic reconciliation and prove no finalized/deleted/removed media is served. Explicitly prove
  that an old photo-volume snapshot is outside the supported POC contract.
- Preserve full RF-07 temporary cleanup, publication/restart persistence for open photos, current
  Public/Private authorization, RF-16 vote races and RF-18 live-result regressions.

## Readiness checklist

- [x] Desired outcome is understood at grooming level.
- [x] Scope and exclusions are confirmed by the product owner.
- [x] Code, migrations, storage, Docker and maintenance paths were inspected.
- [x] Dependencies and conflicts are confirmed.
- [x] Technical approach is selected.
- [x] Concurrency and exact immediate-revocation semantics are confirmed.
- [x] Security, privacy, deletion evidence and DEC-023 minimization are resolved.
- [x] Backup/restore and operational alerting are resolved.
- [x] Migration, compatibility and rollback are resolved.
- [x] Complete automated/integration/recovery validation expectations are agreed.
- [x] No material question remains.
- [x] Product owner explicitly approved plan finalisation.

No implementation plan may be created while these items remain open.
