# RF-07 - Subir y comparar varias fotografías - Grooming

## Status

`Ready for implementation`

## Trello snapshot

- Title: `RF-07 · Subir y comparar varias fotografías`
- URL: https://trello.com/c/x8VPrsF9/3-rf-07-subir-y-comparar-varias-fotograf%C3%ADas
- Board: `APP - NextPost` (configured board; card board matches)
- List: `Fase 2`
- Labels: None
- Members: None
- Due date: None
- Card completion: Not complete
- Checklists: None
- Comments: None
- Captured on: `2026-09-22T15:24:06Z`
- Last Trello activity at intake: `2026-09-22T14:34:49.267Z`

### Description and acceptance criteria at intake

**Historia de usuario**

Como autor, quiero añadir fotos que otras personas puedan comparar con facilidad.

**Criterios de fase 2 acordados**

- Cada consulta publicada contiene entre 2 y 10 fotos; ambos límites se cambian en la configuración compartida de la aplicación y el servidor los hace cumplir.
- Se admiten imágenes fijas JPEG, PNG, WebP, HEIC y HEIF, incluidas fotos elegidas directamente de la galería del iPhone.
- Se validan los archivos, se conserva su orientación visible, se elimina la localización/metadatos de origen y se sirve una versión procesada compatible. El archivo original se descarta tras procesarlo.
- Se muestran progreso, error y reintento por foto; las fotos pueden ampliarse sin recorte obligatorio. No se publica con subidas pendientes o fallidas.
- Tamaños y límites de recursos concretos se fijan en el plan técnico, priorizando simplicidad y prueba real en iPhone.

Identifier, title, list, and card content agree. This card was selected by the product owner's
conditional approval after discussion that F06's real-photo editor depends on F07. Trello was read
only.

## Intended outcome

An authenticated author can choose ordinary gallery still images, including iPhone HEIC/HEIF,
upload them privately, see trustworthy per-photo progress and errors, retry a failure, and compare
processed photos at useful size. The upload foundation supplies F06's temporary editor and F10's
publication check without exposing unsubmitted or withdrawn media.

## Current code findings

- `frontend/src/App.tsx` and `Navigation.tsx` provide authenticated Home/Profile navigation but no
  composer, file picker, photo comparison, or preview. `frontend/src/api.ts` has account/session
  requests only. The Capacitor packages exist, but `ios/` is not generated; no native photo plugin
  is installed.
- `backend/app/models.py` contains only `Account`; `backend/app/main.py` includes health/accounts
  routers only. There is no consultation/upload model, image validation or processing package,
  private media endpoint, or cleanup path. The account cookie currently carries the account ID.
- `backend/pyproject.toml` has FastAPI/SQLAlchemy/PostgreSQL dependencies, but no image decoder or
  multipart package. `docker-compose.yml` persists PostgreSQL only; no private image volume or
  scheduled cleanup process exists. `backend/Dockerfile` uses Python 3.13 slim.
- The worktree is entirely untracked; preserve all existing files. RF-03 code exists but its plan
  remains in implementation progress in project state, so integration must be checked.

## Dependencies and conflicts

- RF-06 owns the editor, photo-list interaction and author preview. It requires F07's actual image
  upload and processed-image state; a fake/local-only F06 release was rejected (DEC-010/012).
- RF-37 owns private media authorization and deletion of removed/abandoned/published media. Its
  minimum access and cleanup contract must be designed and working before real upload is exposed.
- RF-10 owns atomic publication and must reject pending/failed photos and counts outside active
  limits. RF-09 owns audience/link checks for voter media; F07 must not invent public file URLs.
- DEC-013 sets configurable minimum 2, maximum 10 and a shared effective configuration source;
  DEC-015/016 require JPEG/PNG/WebP/HEIC/HEIF, real iPhone gallery selection, normalized display,
  orientation, metadata stripping and raw-original removal. DEC-021/022 cut media access at end or
  removal. DEC-007 avoids a worker absent a proven need.
- Web and invited iOS TestFlight are accepted targets (DEC-014), but the permanent app ID, signing,
  Xcode, native project, and physical-device check are separate delivery prerequisites.

## Candidate approach

### Accepted direction

- Use an owner-bound temporary upload session, persisted only to track private processed image
  objects and eventual cleanup. The consultation form itself remains transient (DEC-012). Avoid a
  recoverable draft library. An upload can be referenced by F06 only after successful validation
  and processing, and by F10 only if it still belongs to the author/session and is not discarded.
- Start with the shared platform file input/picker, and use a native picker only if real-device
  tests show that it cannot satisfy DEC-015. Use synchronous request processing for a bounded image
  workload first; progress can cover network transfer, followed by an explicit processing state.
  A distinct background worker needs evidence and a new decision.
- Validate bytes and decoded format server-side with a fixed still-image allowlist. Treat filename,
  extension, MIME, and browser `accept` as hints. Reject animation/multi-frame sources for the first
  version rather than silently choosing a frame. Normalize orientation and color into a broadly
  renderable display derivative with no carried source metadata; discard raw bytes on both success
  and failure. Preserve full image proportions and allow enlargement without mandatory cropping.
- Propose an initial 15 MiB compressed-file ceiling, 40 megapixel decoded-pixel ceiling, and a
  2560-pixel longest-edge display derivative, with server limits exposed as effective client
  guidance. These are technical proposals from the earlier phase-2 research, not accepted limits.
  Test representative large iPhone photos before finalizing values.
- Keep normalized files outside web roots. Every read requires authentication and server-side
  owner/audience/state authorization. For temporary uploads only the owner may read. The physical
  storage mechanism, purge schedule, backup policy, and restricted removal interface belong to a
  coordinated RF-37 contract.

### Alternatives and trade-offs

1. Client-only data URLs would avoid server storage during editing, but cannot provide the accepted
   processed-image preview, real upload progress/retry, or safe F10 handoff; not recommended.
2. A permanent private draft model would ease recovery but conflicts with DEC-012's simple temporary
   preparation and adds unnecessary lifecycle complexity; not recommended.
3. Browser file input plus synchronous processing is the simplest initial path, but requires a real
   iPhone check and strict resource limits. Native picker or background processing is a fallback only
   if device or workload evidence warrants it.

### Accepted technical package

- **Storage and active composer lifetime:** Keep normalized files in a backend-only persistent
  volume, outside Nginx's root, with opaque keys and database rows linking each to its owner and
  temporary composer session. This row is processing state, not a saved draft. While the authenticated
  composer remains open and connected, it renews a lease periodically; there is no maximum editing
  duration and viewing does not define retention. Successful publication atomically promotes the
  selected processed files into the consultation. Remove/Cancel revokes them immediately.
- **Cleanup when the client disappears:** Closing, reloading, crashing, or losing contact stops the
  lease. After 24 hours without a successful renewal, the server marks the session abandoned,
  revokes its reads and queues its files for deletion. A best-effort exit request can accelerate
  cleanup but is not required. A durable pending-deletion marker survives restart. An hourly backend
  maintenance pass, startup sweep and restricted manual retry remove revoked files and verify absence
  before marking deletion done. Failed deletion stays denied, retries hourly and triggers an
  operational alert after 24 hours. This is maintenance inside the existing backend, not a queue or
  general worker. If a device is offline or suspended for more than the lease grace period, its
  server session is abandoned; returning starts a new composer and requires reupload, consistent
  with the absence of draft recovery.
- **Temporary-image durability:** Propose no backup or versioned copy of unpublished temporary
  images. Losing that private volume means an author must reupload, consistent with DEC-012's
  non-recoverable preparation. Published-image backup and failure policy belong to RF-37 and are
  not decided by F07. The earlier question about accepting loss of published photos was premature.
- **Processing/limits:** Bounded synchronous decoding with an allowlist; suggested 15 MiB upload,
  40 MP decoded image, and 2560-pixel longest display edge. Produce an sRGB JPEG derivative with
  visible orientation applied and no metadata fields copied; flatten transparent pixels against
  white. Reject animation, zero/invalid dimensions, corrupt files, and resource overflow. For
  HEIC/HEIF, decode the primary still image even when the container has auxiliary images; do not
  reject an ordinary iPhone photo solely for those auxiliary images. Delete raw temporary
  bytes in success, failure, and interrupted-process recovery. Confirm container decoder behavior
  and actual iPhone output before claiming DEC-015 complete.
- **Configuration:** Extend `backend/app/config.py` with startup-validated min/max photo count,
  max open consultations, and file/pixel limits. Expose non-secret effective values via a narrow
  authenticated config read for UI guidance. A restart applies changes. Reject invalid settings
  on boot rather than silently falling back; no duplicated frontend constants or admin screen.
- **Retry and ordering:** Each attempt gets an opaque identifier. Only a processed, non-revoked
  image can be referenced for publication. A retry creates a replacement attempt and revokes the
  failed/old one. The client maintains order, and the publication request supplies the ordered IDs;
  the server checks ownership, uniqueness, count, processing state and current configuration.
  Network retries must not make extra publishable images or leak old objects. F10 owns final
  transaction/idempotency.

## Questions

### Open

None.

### Resolved

- 2026-09-22: The product owner explicitly approved finalisation of RF-07. The self-contained plan
  is `harness/features/RF-07-Implementation-plan.md`, marked `Ready for implementation`. This does
  not authorize implementation or harness launch.
- 2026-09-22: The owner corrected the abandonment model. Publication promotes photos; Remove or
  Cancel revokes them; an open and connected composer keeps all temporary photos alive for as long
  as the author needs through a renewable lease. Only disappearance without Cancel stops renewal.
  After 24 hours without a successful renewal the server treats it as abandoned. This is processing
  state, not a recoverable draft. Temporary files have no backup (DEC-026).
- 2026-09-22: The owner approved restart-based server configuration and the initial 2?10 photo,
  15 MiB input, 40 MP decoded, and 2560-pixel output limits, subject to evidence-based technical
  adjustment without narrowing the accepted formats.
- 2026-09-22: The owner approved the proposed shared picker, synchronous validation/normalization,
  primary-still HEIC/HEIF behavior, metadata removal, progress/processing/error/retry states, and
  no-crop enlargement. A native picker is considered only if real-iPhone evidence requires it.
- 2026-09-22: The owner approved an integrated first RF-07 increment with minimum RF-37 private
  storage, owner-only temporary reads, removal revocation, and abandoned-upload cleanup (DEC-025).
  The broader RF-37 lifecycle remains separately owned. This does not approve implementation yet.
- 2026-09-22: The owner selected F07 after confirming it is prerequisite to implementing F06 with
  real photos. This selection authorizes grooming, not plan finalization or implementation.
- DEC-013/015/016 fix the initial configurable photo-count and accepted format/normalization/raw
  original rules. DEC-012 fixes temporary, non-recoverable preparation. DEC-014 fixes web and iOS
  TestFlight delivery. DEC-021/022/023 fix the no-buffer media cutoff and data-retention boundary.

## Proposed scope

### In scope (confirmed)

- Actual private still-image upload, validation, normalization, and processed-image state for F06.
- Per-photo upload/processing/error/retry contract and proportional comparison/enlargement support
  that F06 can use.
- Effective photo-count and resource guidance backed by enforced server configuration.
- Minimum RF-37 private read and cleanup capabilities necessary to avoid orphan/public photo data
  (DEC-025).

### Out of scope (confirmed)

- The F06 composer, context, audience choice, and publication confirmation UI.
- A recoverable draft library, permanent original retention, video/GIF animation, cropping tools,
  filters, editing, social photo import, or public static image URLs.
- Automatic consultation expiry, full admin UI, Android packaging, or a background worker without
  measured need.

## Validation outline

- Automated backend/API/storage tests for content sniffing, malicious/oversized inputs, accepted
  formats, orientation, metadata stripping, bounds, owner-only reads, count enforcement, session
  loss, retry/duplicate attempts, removal and cleanup, and publication eligibility handoff.
- Automated frontend tests for selection, progress/processing/error/retry, ordering/removal,
  enlargement without crop, configured count guidance, and session/error states.
- Container build with HEIC/HEIF decoder and PostgreSQL/private storage; manual browser and real
  iPhone gallery upload, orientation, comparison, auth, and network interruption checks.

## Readiness checklist

- [x] Desired outcome is unambiguous.
- [x] Scope and exclusions are confirmed.
- [x] Code impact was inspected.
- [x] Dependencies and conflicts are resolved.
- [x] Technical approach is selected.
- [x] UX and failure states are confirmed where applicable.
- [x] Security, privacy, retention, and abuse implications are resolved where applicable.
- [x] Data migration and operational implications are resolved where applicable.
- [x] Test and manual validation expectations are agreed.
- [x] No material question remains.
- [x] Product owner explicitly approved plan finalisation.
