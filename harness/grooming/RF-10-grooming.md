# RF-10 - Publicar una consulta - Grooming

## Status

`Ready for implementation`

Selected by the product owner on 2026-09-28. Read-only Trello intake and repository analysis only.
The owner requested all material questions together, with product-language explanations and a
recommendation for each. The owner later explicitly approved plan finalisation.
The subsequent owner responses below settle the material product questions. Historical proposals
must be read alongside those responses, especially the rejected POC recovery complexity. The existing
ticket split remains in force. The approved plan is
`harness/features/RF-10-Implementation-plan.md`; harness launch is not authorized.

## Trello snapshot

- Title: `RF-10 · Publicar una consulta`
- URL: https://trello.com/c/gMQwBaFB/4-rf-10-publicar-una-consulta
- Board: `APP - NextPost`, https://trello.com/b/CgBkRg78/app-nextpost
- Board ID: `6aa903892e7d7b54f23fae1b`; matches the configured board.
- Workspace ID: `6aa9032829f8b45ead46cfdd`
- Card ID: `6aa9048a50938ae4dd47dc42`
- List: `Fase 2`, ID `6aa903892e7d7b54f23fae23`
- Labels / members: None / None.
- Checklists / comments: None / None. No omitted labels, checklists or comments reported.
- Start / due date: None / None.
- Archived / card complete / due complete: False / False / False.
- Position: `140737488535552`
- Captured on: 2026-09-28, before coordinator checkpoint `2026-09-28T14:30:12Z`.
  The connector does not supply the exact read timestamp.
- Last Trello activity: `2026-09-22T14:34:57.786Z`.

### Description and acceptance criteria at intake

**Historia de usuario**
Como autor, quiero publicar una consulta completa una sola vez para recibir votos.

**Criterios de fase 2 acordados**
- Publicar exige cuenta registrada, 2–10 fotos ya procesadas, pregunta válida, audiencia elegida y no superar el máximo configurable de tres consultas abiertas.
- Antes de confirmar se muestran la audiencia y el alcance real de las fotos. No hay selector de duración ni caducidad automática.
- Reintentos o doble confirmación no crean consultas duplicadas. Tras publicar se muestra el estado abierto y el acceso a compartir/resultados propios.
- Fotos, pregunta, contexto y audiencia quedan fijos. Para corregir la consulta, el autor la elimina o finaliza y crea otra.

Referencia: DEC-013/017/018/021/022.

Identifier, title, board, list and description agree. Search also returned cards mentioning RF-10;
only the exact RF-10 card above was consumed. Trello was not changed. The results/sharing criterion
crosses later consumer boundaries; it cannot be reported complete from a publication API alone.

## Intended outcome

Convert the author's reviewed, temporary comparison into exactly one durable open consultation.
Its ordered processed photos, normalized question/context and explicitly chosen audience become
immutable together. Private publication also creates its current link in that same operation.
No reader sees a partially published comparison, and retries cannot duplicate it or bypass limits.

## Current code findings and evidence

### Inspection baseline

Read AGENTS.md, all seven context files, the grooming template, phase-2 and active RF-03/RF-06 notes,
RF-07/RF-08/RF-09 grooming and their complete approved plans, plus the RF-03 shell contract.
Inspected actual models, migration, services, routes, storage, cleanup, access/link/text rules,
uploader, shell, frontend URL/control helpers, tests and deployment/configuration documentation.
Git HEAD at inspection: `94de9fabb350237af1a4d2905f84080ced185997`.
The worktree contains existing tracked and untracked RF-08/RF-09 implementation/documentation changes;
these are dependencies, not disposable files. This task changes only this note and project state.

### Reuse and remaining integration

| Foundation | Actual implementation and accepted contract | Recorded validation; RF-10 obligation |
| --- | --- | --- |
| [RF-07 plan](../features/RF-07-Implementation-plan.md), [grooming](RF-07-grooming.md) | `backend/app/photo_service.py`, `storage.py`, `cleanup.py`, `api/photos.py`; owner-bound leases, private normalized JPEGs, processing, removal and retryable purge. `frontend/src/PhotoUploader.tsx` and `usePhotoUploader.ts` provide comparison/upload state. | Project state records 110 backend tests including 3 PostgreSQL concurrency tests, 88 frontend tests, quality checks, migration round trip, container/format/private-volume smoke and restart cleanup. The three PostgreSQL tests were also rerun successfully during RF-08 review on 2026-09-28. RF-10 must prove promotion survives discard/cleanup; full composer and physical iPhone gates remain pending. |
| [RF-08 plan](../features/RF-08-Implementation-plan.md), [grooming](RF-08-grooming.md) | `backend/app/consultation_text.py`, schemas/config and matching `frontend/src/consultationText.ts`, controlled fields/display/config hook. NFC/plain-text normalization, required question, nullable context, configurable 120/500 defaults. | Completed and validated for this increment: latest recorded correction run 137 backend tests, 144 frontend tests, quality/build checks; later built HTTP config/default/override/auth checks, PostgreSQL tests and owner visual approval. RF-10 persists normalized text atomically; lower future limits must not invalidate old content or completed retries. |
| [RF-09 plan](../features/RF-09-Implementation-plan.md), [grooming](RF-09-grooming.md) | `backend/app/audience.py`, `consultation_access.py`, `private_link.py`; strict audience, pure access matrix, deterministic HMAC token and generation transitions. `frontend/src/AudienceSelector.tsx`, `PrivateLinkControls.tsx`, `ConsultationUnavailable.tsx`, `consultationLink.ts`. | Recorded independent review: 227 backend tests, 215 frontend tests, lint/type/format/build, audit, container/secret checks and desktop/320 px visual review. Three PostgreSQL tests were skipped in that RF-09 run; no persisted consultation/link concurrency was implemented or proven there. RF-10 owns real database snapshots, endpoints, link transitions and published-media enforcement. |

These are repository-recorded results, not tests rerun during this documentation task. RF-07 and
RF-09 remain `Implementation review` for full-ticket integration/device gates. A checked plan or
historical grooming header does not override current project state.

### Concrete gaps RF-10 must close

1. `backend/app/models.py` contains only Account, PhotoUploadSession and PhotoUploadImage.
   Alembic ends at `20260922_0003_photo_uploads.py`. There is no persisted Consultation, option,
   publication receipt, audience/link state, vote, results or owner consultation listing.
2. `validate_publication_images` locks the upload-session row, verifies owner/active lease, unique
   ordered IDs, current photo limits, ready state/storage key and byte presence; it does not commit.
   It validates supplied IDs, not every historical failed attempt or every unselected image.
   `backend/tests/test_publication.py` tests this helper, not publication or an atomic commit.
3. Session states are active/discarded/abandoned, with a migration CHECK constraint. There is no
   consumed/published state or consultation association. Adding only a consultation row is unsafe.
4. `discard_upload_session` revokes session images; `_abandon_expired_sessions` does likewise.
   `remove_image` checks ownership but does not require an active session: changing only the
   session state would still let a delayed image DELETE revoke a promoted image.
5. `_valid_normalized_keys` protects only ready/revoked PhotoUploadImage rows. Moving storage keys
   to a new table or changing image state without adjusting this set would let orphan sweeping
   delete published bytes. Existing ready rows can instead remain the single storage ledger.
6. Current account -> session -> image foreign keys cascade deletion. Retaining associations and
   durable purge records needs an explicit migration design; do not let deletion of a consumed
   session erase published options, or physical-file cleanup lose its database instructions.
7. PhotoUploader exposes ready IDs, blocked status and discard, but not its session ID. Its hook
   sends discard on unmount; `isPublishBlocked` only checks non-ready UI items, not minimum count,
   config readiness, valid text or audience. RF-06/RF-10 need an explicit prepare/pending/consumed
   handoff, shared uploader lifetime through preview, and safe cleanup after successful publication.
8. `get_current_account` verifies a live account from the cookie. There are no verification,
   suspension, blocking or moderation tables; do not invent such prerequisites. `main.py` uses
   SameSite=lax, HTTPS cookies outside development and credentialed origin-allowlisted CORS, but
   there is no explicit origin/CSRF guard for future consultation mutations.
9. `consultation_access.can_access` already denies terminal states even to the owner for content,
   grants owner read/manage without a token while open, and requires a current token for Private
   non-owners. Its snapshot and verifier must come from the same current database row.
10. `private_link.py` supports positive unsigned 64-bit generations. Database and JSON representation
    must preserve them exactly; a signed BIGINT or JavaScript number cannot represent the entire
    domain. Proposed exact decimal persistence/JSON-string boundary avoids silently narrowing it.
11. `App.tsx` still has Home/Profile local state and resets Home after authentication. Nginx's SPA
    fallback alone does not create `/consultations/{uuid}` routing. No live composer, published
    detail, sharing/auth return, feed, vote or results screen exists. New service/router/component
    names below describe intended boundaries, not existing files.
12. Compose persists private normalized files in `photo_storage`; it implements neither published
    photo backups nor a restore runbook. RF-07's no-backup decision covers temporary photos only.

## Dependencies, inherited decisions and conflicts

### Fixed inputs, not questions to reopen

- DEC-012/026: temporary preparation, no draft recovery; renewable 24-hour abandonment lease;
  publication promotes selected photos atomically. Original bytes are discarded (DEC-016).
- DEC-013/018 and RF-07: current server configuration governs new publication (initial 2–10 photos,
  3 open consultations); published photos/order, text and audience remain fixed. No duration or
  automatic expiry (DEC-017). A disabled Private link does not free an open-consultation slot.
- DEC-022/024: explicit Public/Private selection, neither preselected. Registered-only access;
  Private is unlisted and forwardable, not an invitee allowlist. Nickname only, no public profile.
- DEC-027: complete normalized question and optional context above photos, inert display.
- DEC-028–030 and approved RF-09: automatic Private generation 1/active link, stable owner re-copy,
  disable/replace/create-new, generic unavailable responses, current access checks without polling,
  accepted already-loaded images on idle screens, ordinary platform URL opening.
- DEC-019/021–023: only the author sees aggregates; finalization declares one/several/none and
  revokes photo access for everyone, with no image buffer; deletion/removal also revoke and purge.
  Minimal outcome retention is not permission to retain photo/text copies for analytics.
- Accepted ordering remains RF-09 -> RF-10 -> finalise/implement RF-06. No combined RF-09 ticket,
  custom native links, worker/queue, new session system or rollout decision is implied here.

### Adjacent cards re-read as dependencies, not consumed

On 2026-09-28 the following exact cards were read in full. All are on the configured board in
`Fase 2`, open/uncompleted, without labels, members, start/due dates, checklists or comments;
the connector reported no truncation of those fields.

| Card | Current dependency | Last activity |
| --- | --- | --- |
| [RF-12](https://trello.com/c/L2mZ6OFf/14-rf-12-gestionar-mis-consultas) | Owner open/finalized list, management entry and permitted non-image history. | 2026-09-22T14:35:03.249Z |
| [RF-13](https://trello.com/c/NEYa01VK/16-rf-13-eliminar-una-consulta-propia) | Confirmed author deletion, immediate access cutoff and queued photo purge; no outcome for an unfinalized deletion. | 2026-09-22T14:35:06.148Z |
| [RF-18](https://trello.com/c/GBfvkzU8/19-rf-18-consultar-resultados-como-autor) | Real author-only counts/percentages, zero/ties and non-image finalized results. | 2026-09-22T14:36:29.994Z |
| [RF-26](https://trello.com/c/47FD3mrW/28-rf-26-compartir-una-consulta-e-invitar-a-votar) | Copy/device share, generic external preview and return through sign-in/registration. | 2026-09-22T14:36:07.670Z |
| [RF-37](https://trello.com/c/Dodf7k4R/40-rf-37-proteger-y-borrar-fotograf%C3%ADas) | Private reads, no-buffer deletion, retry/recovery and restore without resurrected access. | 2026-09-22T14:36:38.547Z |

RF-11 supplies lifecycle integration; RF-14 discovery must exclude Private and terminal rows;
RF-16 voting must reuse current access and refuse incomplete comparisons; RF-19/20 implement
finalization; restricted administrator removal remains a phase-2 requirement under DEC-022.
There are no approved plans for those future implementations in `harness/features` at intake.

Historical RF-06/phase-scope notes saying uploads/storage/text/access helpers do not exist are
superseded by inspected code and approved RF-07/08/09 contracts. RF-03's Home default remains for
ordinary entry; a valid share destination is an explicit later RF-26 exception, already required
by RF-09. No accepted rule needs silently overriding. The material scope tension is that RF-10's
full card mentions results/sharing before those product screens exist (Q5).

## Candidate approach — proposals, not an implementation plan

### Persistence and atomic publication

Prefer a small relational Consultation plus ordered option association, reusing PhotoUploadImage
as the only private-file/deletion ledger. Candidate data:

- Consultation: opaque UUID, owner FK, normalized question/context, immutable audience, lifecycle
  (`open`, `finalized`, `deleted`, `removed`), UTC publication date, source upload-session identity,
  publication fingerprint/version and effective validation limits, Private generation/active state.
- Ordered options: stable UUIDs (reuse image IDs where practical), consultation/image FKs, immutable
  ordinal; unique consultation+ordinal and unique image association. No duplicate storage objects.
  Keep stable option identities separable from later physical photo deletion for DEC-023 outcomes.
- A unique source upload-session reference makes one session consumable once, across different
  request keys/tabs as well as ordinary retries. Retain a minimal successful receipt/tombstone for
  safe reconciliation; future terminal operations must not erase it then accidentally permit replay.
- Explicit consumed session state, enforced by the Alembic state constraint. No conversion of
  temporary uploads into published data during migration and no text/audience saved before publish.
- Public rows have inactive Private state; Private rows start generation 1/active atomically.
  Exact integer storage and bounded decimal-string transport can preserve RF-09's unsigned domain.

Promotion should change ownership/lifecycle references in one database transaction while keeping
the same already-verified private bytes/key. Copying/renaming files during commit adds rollback and
orphan risks without improving visibility: PostgreSQL cannot atomically commit a filesystem move.
A durable draft/staging service or distributed transaction is unnecessary for this existing store.

Proposed transaction invariants: authenticate; acquire the author's serialization lock; resolve any
already committed receipt; lock the upload session; validate the new request and current limits;
count the author's open rows under that lock; validate/lock images via RF-07; create consultation,
ordered associations and initial link state; consume the session and persist the receipt; revoke
unselected temporary objects as needed; commit once. No helper may commit partway through promotion.
The full row set is invisible until commit, and failure leaves no open consultation, promoted subset,
active link or consumed quota. File deletion of excluded objects occurs only after durable revocation.

The request's ordered selection is authoritative: every selected image must be ready and owned.
Never silently publish just the successful subset of what the author confirmed. Existing historical
failed/revoked attempts are not selected photos and should not poison a corrected session. A pending
attempt must complete or be removed before publication; use the same session lock as upload and
recheck after waiting. Unselected ready leftovers must be revoked/queued in the success transaction,
not published or left alive indefinitely. RF-06 blocks any currently failed/pending visible item.

### Idempotency, uncertainty and concurrent operations

- Recommend using the owner-bound upload-session UUID as the natural publication operation identity,
  rather than maintaining an independent retry service. Store a versioned digest of the canonical
  ordered IDs, normalized text and audience; no raw payload copy or bearer token in the receipt.
- Same owner/session and equivalent normalized payload returns the same consultation identity.
  Changed order/text/audience after successful consumption conflicts; it never edits the row or
  creates another. Two genuinely new sessions may create separate comparisons if capacity permits;
  do not deduplicate based on image similarity or equal text.
- Resolve completed publication before applying current new-publication limits or active-lease
  checks. A successful replay must still work after lease expiry, lowering limits or reaching the
  open cap. RF-08's request schema currently validates against current settings: naively composing
  that schema ahead of receipt lookup would break this. Separate strict structural/canonical parsing
  from new-publication bounds, or validate against the recorded successful bounds for replay.
- A rejected, rolled-back attempt does not consume the session: correction and explicit confirmation
  may retry. An ambiguous timeout/5xx is not proof of rollback. Reconcile against the same operation
  under the same lock before allowing a changed submission (Q2). A status read that sees no receipt
  without waiting for an in-flight publication is insufficient proof that nothing committed.
  Even a locked absence check cannot fence a delayed request that has not reached the server yet.
  Prefer convergence by retrying the frozen original request. An explicit abandon/change operation
  while the outcome remains uncertain would require a durable operation revision/cancellation fence
  that makes delayed old requests fail; do not implement it as a client abort or an empty status read.
- Replays return a current authorized outcome, not a cached old full response. A replaced/disabled
  link must not be reissued; a terminal consultation must not regain text/media through its receipt.
  Token acquisition is a separate current owner-link read. Minimal owner receipt information can
  identify the completed operation without exposing terminal content.
- Serialize cap enforcement with an Account row lock, not just `COUNT` followed by INSERT. This
  works even when the author has zero consultations. Use a consistent account -> consultation/session
  -> image lock order; future slot-freeing finalization/deletion must use compatible ordering.
  Parallel publications from different sessions compete for the last slot; only one can succeed.
- Remove/discard/abandon/upload/publication must share session locking. If withdrawal wins, publish
  fails. If publication wins, later temporary Remove/Discard cannot touch promoted rows. Heartbeat
  cannot reactivate a consumed session. No temporary read remains usable for promoted media.
- Link mutations lock the current consultation, authorize the owner and apply RF-09's expected
  generation/state transition. Lost responses reconcile with current state; never blindly rotate
  twice. A publication replay cannot reset that state. Disabling a link keeps the open slot.

### Published detail, media and audience

Add real authenticated consultation/detail/media and owner-link service/API boundaries; no such
routes currently exist. Possible route shapes are `POST /api/consultations`,
`GET /api/consultations/{id}`, `GET /api/consultations/{id}/images/{image_id}/content`, and owner-only
current-link/mutation and publication-reconciliation operations. Exact names are future plan detail.

On every request resolve the current account, current persisted consultation/lifecycle/link and
the image's association to that consultation. Invoke RF-09's policy with the same snapshot/token
verifier. UUID possession, old votes, old visits and copied media addresses grant no Private access.
Owner-link responses alone may expose the current token; reader detail must never mint/reveal it.
Public detail contains no email, storage keys, tokens, individual votes or aggregate results.
Authorized detail returns only required nickname/content/audience/state/date/ordered option metadata.

Serialize each protected read's authorization and bounded byte acquisition with link/terminal
mutations (e.g. shared row lock versus mutation lock). Copy bounded bytes while authorized, then
release the transaction before sending over a potentially slow network. A read ordered before
revocation may finish returning already-authorized bytes; a new read after committed revocation
must fail. Never stream a filesystem path later after dropping the authorization snapshot.
This is compatible with DEC-029; it makes no promise to recall downloaded photos and adds no polling.

Keep RF-07 endpoints temporary and owner-only; both old content and delete paths must reject or
safely no-op consumed/promoted targets. Adjust orphan protection, session sweeps and cascades together.
Keeping the original storage ledger/reference throughout promotion avoids a transient unreferenced
file that an already-running sweep could claim. Test sweeps overlapping commit, not only after it.

Malformed/unknown/denied Private destinations and terminal detail/media share a generic unavailable
response. Authentication remains 401. Authorized storage/service failure remains retryable 503,
not a false removal claim. If a published photo is missing, proposed behavior is to block the
comparison rather than offer fewer options, alert operations and never replace a photo in place.
No automatic finalization, outcome or quota release is inferred from storage failure (Q4).
Future RF-16 must independently check media integrity before accepting a vote.

### Confirmation, success and frontend handoff

RF-06 remains the complete composer owner. RF-10 can provide reusable publication transport/state
and confirmation/success presentation without inventing a second composer or provisional route.
Show the reviewed photos/text, explicit audience reach, immutability and absence of automatic
expiry before `Publish consultation`; details of the final confirmation are Q1. No rights checkbox
or service-rules versioning is implied by the existing brief reminder.

During submission freeze the submitted snapshot and duplicate activation. On confirmed success
clear transient authoring state through a consumed/relinquish handoff, stop its lease and revoke
local object URLs without deleting promoted data. Server safety must hold even if the browser
crashes before this callback. Preserve ordinary editing on definite validation/limit failures;
ambiguous outcome uses Q2. A 401 clears private in-memory state via the existing session-loss rule;
no cross-account receipt recovery or persisted draft is added.

The existing uploader needs an explicit session-ID result, freeze/pending contract and success
relinquish operation. Keep it mounted through preview and do not treat an inactive lease response
after commit as proof that publication failed. Cancellation during uncertainty is not guaranteed to
cancel an already committed publication; use reconciliation and then the later real delete flow.

If Q3A is accepted, provide a narrow authenticated current-owner capacity read for RF-06's entry
guidance; it is advisory, not a reservation, an owner-list implementation or a replacement for the
transactional check. Capacity lookup failure should offer retry without discarding an existing form.

The final integrated success destination is the actual open consultation with sharing/owner results
entry. RF-12/18/26 still own their list/results/device-share journeys. Do not show fabricated zero
votes or a dead Results button while those features are absent. Q5 settles increment completion
versus full-card completion; no release is authorized by this grooming.

### Error and recovery outline

| Condition | Proposed observable behavior |
| --- | --- |
| Missing/invalid question, context or audience | Existing safe 422 field-error envelope; preserve form and focus correction, never echo payload. |
| Wrong owner/session/image, mixed consultation IDs | Non-enumerating denial; no file access or mutation. |
| Wrong photo count or changed server limits | Explain current rule, preserve valid input/photos, refresh config and require correction/confirmation. |
| Open cap reached, including a concurrent last-slot race | Nothing published; preserve current live preparation; no automatic later publication (Q3). |
| Active-session lease expired/discarded before publication | No partial consultation; explain photo reselection. Live text/audience may remain if authentication is still valid; no draft recovery promise. |
| Same session already published with changed payload | Conflict plus owner-safe reconciliation; never silently overwrite or duplicate. |
| Network timeout, lost/malformed success or uncertain server error | Outcome unknown; reconcile/retry same confirmed operation, do not announce failure/success without evidence (Q2). |
| Link mutation conflict/lost response | Refresh authorized current link state; no speculative link or repeated rotation. |
| Denied or terminal detail/media | Generic unavailable; clear locally held content on actual denied request, no polling. |
| Authorized missing media/storage outage | Retryable unavailable comparison and operational signal; no replacement, partial comparison or fabricated outcome (Q4). |

### Security, privacy and operations

- Derive owner only from the verified cookie; forbid extra writable owner/lifecycle/link fields.
  No anonymous consultation text, image, preview or metadata endpoint. No edit endpoint for fixed
  published content. Opaque IDs are identifiers, never authorization secrets.
- Use RF-09's dedicated secret, fragment URL and `X-NextPost-Private-Link` credentialed header.
  No token in API URL/query/body, logs, analytics, persistent browser storage or receipt snapshots.
  Build share URLs from trusted origin; prohibit arbitrary authentication redirects.
- Protect consultation mutations with explicit trusted-origin checking appropriate to cookie auth
  and strict JSON/non-simple request requirements; reject hostile and null browser origins.
  CORS is not sufficient CSRF protection. Specify/test any missing-Origin API-client case rather
  than treating it as trusted. Web local origins remain supported; native origins/HTTPS cookie
  behavior need their later real-device gate. No new authentication transport is inferred.
- Preserve private/no-store, nosniff and no-referrer for content and owner-link responses, including
  errors where needed; the future HTML shell must also prevent referrer leakage and protected
  OpenGraph content. Fetch-to-blob with credentials/token, clean up URLs and ignore stale responses
  on account switch/unmount/denial. No service-worker/offline image cache.
- Restrict request shape/size before unbounded normalization and bound image lists/resource work.
  Avoid logging SQL parameters containing question/context or response tokens. Operational logs may
  contain opaque correlation IDs, transition/error codes and deletion age, not content or credentials.
- Preserve private persistent storage and synchronous processing; promotion needs no reprocessing,
  permanent original, public directory, image CDN, queue or new external dependency.
- Temporary no-backup policy is already accepted. Extending that to published images is Q4, not an
  inference from RF-07. A candidate first-delivery choice keeps one private durable volume and no
  image copies/versioning, accepting unrecoverable host loss. Database-only backup cannot recover
  photos. RF-37 still needs a tested restore policy: rotating the link key prevents old Private
  capabilities, but alone does not prevent restored Public/deleted content from resurfacing.
  Restored traffic must remain disabled until withdrawal/media state is reconciled or content is
  conservatively unavailable. No restore procedure is executed or claimed validated here.
- Author deletion/finalization/admin removal and physical purge remain mandatory before real-user
  phase-2 exposure. Denial tests against terminal database fixtures prove RF-10 reads only, not the
  future transition, purge or restore implementation. Q5 identifies that completion boundary.

### Migration and compatibility analysis

Propose the next Alembic migration after `20260922_0003`, adding Consultation/ordered associations,
receipt data and the consumed-session state. Add explicit FKs, unique session/image/ordinal keys,
audience/lifecycle/link-state constraints and owner+state/date indexes. Use text columns independent
of configurable current maxima; store only successful normalized values. Exact generation range and
JSON representation must agree with the approved link helper.

Existing active/expired/discarded sessions and ready/revoked/deleted images remain temporary; nullable
association fields start empty. Preserve all existing users and files. Revisit cascading deletion
so consumed sessions cannot erase publication receipts/options, and deletion cannot lose the durable
file ledger. No account-deletion product flow or new outcome persistence is implemented by this.

Models and migration constraints must agree (the current SQLite `create_all` fixtures do not exercise
the production state CHECKs). Validate both a fresh database and an upgrade populated with existing
RF-07 states, then prove temporary cleanup and published survival using the migrated PostgreSQL DB.

Old backend/cleanup binaries must not run against promoted data: they do not understand consumed
sessions/associations. Deploy the backend/migration/cleanup compatibility unit with maintenance
stopped during the transition; no mixed old cleanup process. A downgrade with published rows cannot
blindly drop references and let the old sweeper delete files. Recommend refuse unsafe downgrade,
require an explicit operator withdrawal/purge or forward repair, and test a clean round trip only
on an isolated disposable database. Never use the user's running database/volume for destructive
migration tests. A database rollback does not roll back filesystem deletion.

## Questions

### Historical consolidated question block

Las reglas ya aprobadas no se reabren. Las siguientes cinco decisiones completan lo material
identificado en esta revisión; las opciones A son recomendaciones, no decisiones aceptadas.

1. **Q1 — Último paso antes de publicar.** ¿La vista previa debe terminar con un resumen de quién
   podrá ver las fotos, que no se podrán editar y que no caducan automáticamente, seguido de
   `Publish consultation`, o quieres además un segundo diálogo de confirmación? **Recomiendo A:**
   una única confirmación explícita en la vista previa, con posibilidad de volver a editar. B añade
   una segunda interrupción para proteger frente a pulsaciones accidentales.
2. **Q2 — Se pierde la conexión al publicar.** Puede haberse publicado aunque no llegue la respuesta.
   ¿Mantenemos esa versión sin permitir cambios mientras comprobamos el resultado y ofrecemos
   reintentar la misma publicación, o permitimos editar otra versión mientras se resuelve la primera?
   **Recomiendo A:** conservar la preparación en esa pantalla y resolver primero la publicación
   original; si ya existe, abrirla, y si no se publicó, permitir corregir/reintentar. B es más flexible
   pero puede dejar una versión anterior publicada mientras el autor prepara cambios. No se promete
   recuperar el formulario si se cierra o recarga la app, ni publicar automáticamente al reconectar.
3. **Q3 — Ya hay tres consultas abiertas.** ¿Impedimos comenzar otra preparación cuando sabemos que
   se ha alcanzado el límite, o dejamos prepararla y bloqueamos solo su publicación? **Recomiendo A:**
   avisar antes de invertir trabajo y bloquear una nueva preparación. Si otra pestaña ocupa la última
   plaza mientras se está editando, conservar esa preparación abierta, explicar el límite y permitir
   reintento explícito cuando quede plaza. B permite preparar por adelantado, con el riesgo de perder
   ese trabajo si se cierra la app. El límite configurable de tres ya está aprobado; esto solo decide
   cuándo informar y bloquear en el recorrido de RF-06.
4. **Q4 — Conservación de las fotos publicadas ante una avería.** Las fotos temporales ya carecen de
   copia de seguridad; las publicadas todavía no tienen esa decisión. ¿Aceptamos para esta primera
   versión una única copia privada persistente, que sobrevive reinicios pero puede perderse si se
   pierde el almacenamiento, o exigimos recuperación de fotos publicadas antes de habilitarla?
   **Recomiendo A para la prueba de concepto:** sin copias/versiones adicionales; si falta una foto,
   mostrar comparación temporalmente no disponible y permitir reintentar, nunca comparar un conjunto
   incompleto ni sustituirla. Una pérdida confirmada se resuelve retirando la consulta, sin inventar
   una elección final; no se retira automáticamente por un fallo transitorio. B exige concretar en
   RF-37 copias, recuperación y eliminación de esas copias antes de exponer el flujo. En ambos casos
   se mantiene el borrado al finalizar/eliminar y no se restauran fotos retiradas.
5. **Q5 — Qué debe quedar terminado en este incremento.** RF-10 puede dejar publicación, detalle,
   fotos protegidas y gestión del enlace funcionando en el servidor, con controles reutilizables;
   todavía faltan el recorrido completo, resultados y retirada de fotos de otros tickets. ¿Validamos
   así este incremento y reservamos el cierre de la tarjeta completa para la integración, o quieres
   ampliar RF-10 para completar también esas pantallas y la retirada mínima ahora? **Recomiendo A:**
   mantener el orden acordado y las responsabilidades de RF-06/12/13/18/26/37, sin botones de resultados
   ficticios ni dar la tarjeta por completa antes de tiempo. Antes de usarlo con usuarios reales
   deben funcionar eliminación/finalización, retirada administrativa y borrado; B amplía materialmente
   el alcance y requiere resolver aquí esas funciones. No se está solicitando permiso para lanzar
   el harness ni cambiar el orden ya acordado.

### Owner response and simplified clarification (2026-09-28)

- Q1A accepted: one explicit publication confirmation in the preview, without a second dialog.
- Q3A accepted: warn and block starting a new preparation when the configured open cap is known
  to be reached; preserve an existing live preparation if another tab takes the last slot.
  These cross-feature RF-06/RF-10 rules are recorded in DEC-031.
- Q2: the owner considers the proposed uncertainty workflow excessive for a POC. Simplify the
  recommendation to ordinary pending feedback, duplicate-click prevention and a manual Retry of
  the same submission. The server's one-publication-per-session guarantee remains required by the
  card. Do not add a separate recovery screen, polling, automatic retries, background reconciliation
  service or cancel/change protocol. A lost response must not be presented as proof of failure;
  Retry may return the publication that already succeeded. This revised UX awaits confirmation.
- Q4: the owner requests a clearer explanation and considers the apparent scope excessive. The
  actual choice is only whether published photos need backups now: ordinary private storage already
  survives app/server restart, but cannot recover a destroyed/lost volume. Recommend no additional
  photo backup/recovery infrastructure for the POC. No published-photo durability decision has yet
  been accepted; do not infer acceptance of the earlier bundled loss/withdrawal behavior.
- Q5: the brief reference to this question does not unambiguously approve an option. Explain the
  existing ticket split plainly: RF-10 publishes, RF-06 assembles the editor, other tickets deliver
  voting/results. Recommend continuing that already-agreed order, with no scope expansion; this is
  not a new request to decide architecture or reapprove the order. Exact increment/full-card evidence
  boundaries remain documented, without turning them into additional POC product screens.

### Subsequent owner clarification — Q4 closed (2026-09-28)

The owner explicitly rejected further backup/recovery complexity for the POC. Published consultations
and their photos use ordinary persistent database/private-volume storage and remain available after
closing/reopening the application or an ordinary server restart. Add no photo backup/versioning or
special disaster-recovery infrastructure; exceptional storage loss is an accepted POC limitation.
This does not change temporary preparation: unpublished form state is still lost on close/reload
under DEC-012, and abandoned temporary photos follow DEC-026. It does not approve the earlier
bundled incident-management/automatic-withdrawal proposals or weaken normal authorization/deletion.
Recorded in DEC-032. Do not ask Q4 again or make backup design a prerequisite to RF-10.

### Subsequent owner direction — simplify Q2 (2026-09-28)

The owner's follow-up rejects further POC complexity around double publication (interpreted from
the transcribed reference to question two and double publication). Treat that as direction to use
ordinary submission UX: disable repeated activation while sending, show a concise error and allow
manual Retry. Add no special uncertainty/recovery screen, polling, background reconciliation,
editable parallel version, cancellation fence or separate publication-status API solely for this.

Keep the card's minimal server guarantee that retry/double submission creates at most one
consultation per upload session, using the existing candidate unique session association and one
transaction. A retry returns the same publication when it already succeeded. This engineering
invariant is not an extra product flow or a new question for the owner. Error copy must not assert
that nothing was published when the response was lost. Detailed recovery alternatives above are
not selected scope. Q2's POC complexity question is closed; exact routine implementation belongs
in the eventual approved contract. No finalisation or harness launch was requested.

### Grooming closure and readiness clarification (2026-09-28)

The owner asked whether anything remains to clarify before preparing the harness handoff. There
are no further material product questions. Q5 unnecessarily asked the owner to reconfirm the already
accepted ticket split/order: retain that existing scope rather than infer authorization to expand
RF-10. Publication/access/link persistence and reusable integration remain RF-10; the complete
composer, sharing journey, results and terminal operations retain their documented consumer gates.
This is application of existing decisions, not a new approval of a combined feature or release.

Q1/Q2/Q3/Q4 must not be asked again. Earlier detailed recovery/operational alternatives are not
selected requirements; the subsequent simplification and Q4 closure take precedence. Product
grooming is settled. The owner subsequently explicitly requested plan drafting/finalisation.
`harness/features/RF-10-Implementation-plan.md` is the self-contained contract and is marked
`Ready for implementation`. A separate explicit request is still required to launch the harness.

### Resolved / inherited

- 2026-09-28: explicit owner request authorizes consuming RF-10, inspection, this grooming record,
  project-state update and one consolidated question block only.
- The fixed inputs above are inherited accepted decisions and approved dependency contracts.
- 2026-09-28: Q1A and Q3A confirmed and recorded in DEC-031. Q2 needs simplification; Q4/Q5 need
  clarification at that historical checkpoint. Q4 was subsequently closed by DEC-032 as above.
  No plan finalisation or harness launch is authorized.

## Proposed scope

### In scope, subject to the questions above

- Durable immutable publication, ordered options, owner-bound idempotency/reconciliation,
  transactional cap enforcement and automatic current Private-link initialization.
- Atomic promotion plus coordinated temporary read/remove/discard/heartbeat/cleanup changes.
- Real database-backed detail/media authorization and owner-only link read/transitions using RF-09.
- Strict reusable publication client/state/confirmation-success integration and the uploader handoff
  needed by RF-06; truthful errors, preserved input and no premature success.
- Migration/compatibility design, meaningful PostgreSQL concurrency/security/storage tests and
  built-stack evidence with real processed images; documented future consumer/device gates.

### Out of scope under recommended Q5A

- Complete composer/navigation and product routing (RF-06/RF-26 integration), owner list (RF-12),
  feed/voting/results, finalization/deletion UI, outcome/history and broad administration.
- Implementing full RF-37 backup/restore and terminal-operation machinery by pretending RF-10
  access tests cover it; those remain explicit pre-exposure dependencies.
- Editable publication, draft library/recovery, anonymous media, multiple recipient links/grants,
  automatic expiry, image duplication/reprocessing, native links/picker or packaging, workers.
- Commits, pushes, deployments, Trello mutations, invitations or harness launch.

## Validation outline — proposed evidence, not results

| Area | Required meaningful proof |
| --- | --- |
| Atomicity | Inject failure before commit at consultation/option/link/receipt/promotion boundaries. No partial row, link, slot or consumed session; uploaded bytes remain private and usable if lease still valid. |
| Idempotency | Lost response, double click, concurrent same session, changed payload/order/audience, normalized-equivalent text, restart, limit change, expired consumed lease, disabled/replaced link and terminal replay. Exactly one immutable publication and no reissued stale token. |
| Limits | Last-slot race with two independent sessions and real PostgreSQL connections; zero-row author case; Public and disabled-Private both count; rollback frees no nonexistent reservation. Different owners need not serialize. |
| Promotion | Publish against remove/discard/upload/lease/abandonment; consumed temporary reads/deletes cannot expose/revoke promoted photos. Unselected/failed leftovers handled; promoted bytes survive startup/hourly/manual cleanup and overlapping orphan sweep. |
| Validation | Current 2–10/configured limits, duplicates, wrong account/session, missing/pending/failed/revoked/deleted files, no bytes, all RF-08 Unicode vectors and explicit strict audience. Invalid input never promotes images. |
| Access | Real routes/files: anonymous, owner, other account; Public/Private; current/missing/wrong/revoked/replaced token; cross-consultation image substitution; every terminal state. Same rules for full text and every image, no temporary URL bypass. |
| Link races | Competing disable/replace/create-new, stale generations and lost responses; no double rotation; reads ordered against mutation, owner lookup independent of token, public cannot acquire a Private capability; terminal state overrides. Future vote/finalization races remain consumer gates until implemented. |
| Security | Hostile/null origins, missing-Origin contract, malformed/extra/oversized fields, no raw content/token/cookie logs, no sensitive response fields, private/no-store/nosniff/no-referrer, literal XSS text and no public/static photo exposure. |
| Migration | Fresh and populated RF-07 -> RF-10 Alembic upgrades on isolated PostgreSQL; real CHECK/FK/unique constraints, generation boundaries, startup cleanup, preserved old users/uploads; refused unsafe downgrade and safe clean round trip. |
| Client | Strict response guards, double activation, frozen pending snapshot, unknown outcome/retry, definite error preservation, cap message, missing-media state, no false success, uploader consumption/unmount, 401/account-switch cleanup and stale async response rejection. |
| Integrated gates | RF-06 preview/edit lifetime and real confirmation; RF-26 actual URL/auth-return/copy; RF-12/18 owner access/results; RF-13/19/20/37 terminal transitions, purge/restore; real iPhone/TestFlight session/media/sharing. Keep each pending until actual evidence exists. |

Use the existing pytest/Ruff/mypy and frontend test/format/lint/typecheck/build/audit commands in
README and approved dependency plans. Actual migration invocation from repository root is
`.\.venv\Scripts\python -m alembic -c backend\alembic.ini ...`. Run migration round trips only with
an isolated `DATABASE_URL`; use an isolated `TEST_DATABASE_URL` for PostgreSQL concurrency tests.
Existing `test_photos_postgres.py` uses `create_all` and skips without that variable: it neither
proves an Alembic upgrade nor RF-10 concurrency. Add actual RF-10 tests rather than reporting those
three existing photo tests as publication proof.

Future built-stack smoke: two accounts, actual normalized images, Public/Private publication,
owner stable link retrieval, recipient protected reads, direct-ID rejection, link disable/replace,
duplicate request, restart and cleanup survival. Inspect desktop/320 px/200% zoom, focus, touch
targets and English confirmation/error copy in reusable mounts until real consumers exist.
Physical iPhone/TestFlight evidence still needs permanent app ID, signing and Xcode; no simulator,
component or Linux decoder test substitutes for that gate.

No implementation test suite, migration, cleanup command, deployment or storage mutation was run
during grooming. Documentation checks verify the grooming record and approved plan structure.

## Readiness checklist

- [x] Exact current RF-10 card and readable metadata captured from configured board.
- [x] Code, approved dependency contracts and recorded validation evidence inspected.
- [x] Persistence, atomicity, promotion, audience/link access and concurrency analyzed.
- [x] UX/errors, security/privacy, migrations/operations and test gaps documented.
- [x] All currently identified material questions consolidated with recommendations.
- [x] Material product questions resolved; Q5 follows the already accepted ticket split.
- [x] Q1A/Q3A confirmed, Q2 simplified and Q4 closed.
- [x] Candidate technical/operational contract reviewed against those answers.
- [x] Existing consumer/pre-exposure gates retained; no material product question remains.
- [x] Product owner explicitly approved plan finalisation.

This document is grooming, not implementation authority.
