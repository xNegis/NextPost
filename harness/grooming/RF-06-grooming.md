# RF-06 - Preparar una consulta - Grooming

## Status

`Implementation review`

The product owner explicitly approved plan finalisation on 2026-09-28. The self-contained contract
is `harness/features/RF-06-Implementation-plan.md`, marked `Ready for implementation`. The explicitly
launched harness completed on 2026-09-28. Independent local automated review passed on 2026-09-29;
the isolated built-stack two-account smoke remains pending because Docker Desktop fails during local
startup. The real iPhone/TestFlight gate remains external.

## Trello snapshot

- Title: `RF-06 · Preparar una consulta`
- URL: https://trello.com/c/kLphAXQ1/10-rf-06-preparar-una-consulta
- Board: `APP - NextPost` (configured board; card board ID matches)
- List: `Fase 2`
- Labels: None
- Members: None
- Due date: None
- Card completion: Not complete
- Checklists: None
- Comments: None
- Captured on: `2026-09-22T10:35:35+02:00`
- Last Trello activity at intake: `2026-09-15T09:19:10.552Z`

### Current card recheck (2026-09-22)

The same card remains open in `Fase 2`, without labels, members, due date, checklists, or comments.
Its last activity is now `2026-09-22T14:34:46.299Z`. The description was revised after the
original intake to align with DEC-012/013/015/018/022/023. The current wording is:

> **Historia de usuario**  
> Como autor registrado, quiero preparar y previsualizar una consulta antes de publicarla.
>
> **Criterios de fase 2 acordados**  
> - Inicio visible desde la navegación. La preparación es temporal y solo visible para su autor; no hay biblioteca de borradores ni autoguardado permanente.  
> - Puedo añadir y retirar fotos, escribir una pregunta y contexto opcional, elegir Público o Privado y ver una vista previa fiel a la del votante.  
> - Al salir con cambios se avisa donde la plataforma lo permita; los archivos abandonados se limpian según RF-37.  
> - Se recuerda brevemente que debo tener permiso para compartir las fotos.

This is a recheck, not a replacement of the historical intake snapshot. The card URL and identifier
still match. Trello was read only.

### Description and acceptance criteria at intake

**Historia de usuario**

Como usuario, quiero preparar una consulta antes de publicarla para comprobar las fotos, el contexto y la audiencia.

**Comportamiento y criterios de aceptación**

- Puedo iniciar una consulta desde una acción visible en la navegación principal.
- Durante la preparación puedo añadir y retirar imágenes, completar contexto y cambiar la audiencia.
- La consulta en preparación no aparece en feeds, búsquedas, enlaces compartidos ni perfiles ajenos.
- Puedo previsualizar cómo se presentará al votante antes de confirmar la publicación.
- Si abandono la pantalla con cambios sin publicar, se me advierte; los archivos abandonados se retiran conforme a RF-37.

**Límite del MVP:** no se exige una biblioteca de borradores sincronizados entre dispositivos ni autoguardado permanente.

Intake note: identifier, title, list, and content agree. The card specifies preparation before publication but does not settle whether a draft is only in browser memory or persisted privately, nor whether publication is part of this increment.

## Intended outcome

An authenticated author can assemble and inspect a consultation before deciding to publish it. Preparation remains invisible to other accounts. The experience must make loss of unsaved work clear and handle image data according to an explicit retention boundary.

## Current code findings

- `frontend/src/App.tsx` holds authenticated navigation in local state and displays Home or the private Profile view. `frontend/src/Navigation.tsx` has only Home and Profile. There is no router, consultation composer, image picker, or preview.
- `frontend/src/api.ts` handles account/session/profile requests only. The backend in `backend/app/models.py`, `backend/app/schemas.py`, `backend/app/api/accounts.py`, and `backend/app/main.py` has only account data and endpoints; there are no consultation, audience, upload, image serving, or publication contracts.
- There is no private image storage, image processing, deletion mechanism, worker, or consultation migration. Any server-side draft or upload requires these boundaries to be designed and validated.
- RF-03's approved plan established small responsive authenticated navigation, English product copy, and the light visual foundation. Its implementation files are present, while `04_PROJECT_STATE.md` still records its implementation as in progress; its completion has not been inferred.
- The worktree is wholly untracked. Existing files must be preserved.

## Dependencies and conflicts

- RF-03 provides the navigation into which a visible preparation action would fit. RF-01/RF-02 provide the authenticated account and signed cookie.
- [RF-07](https://trello.com/c/x8VPrsF9/3-rf-07-subir-y-comparar-varias-fotograf%C3%ADas) owns upload, image-count/format limits, processing, retry, and comparison. Its card still describes maximum count and HEIC as open, but the repository now records 2–10 and direct HEIC/HEIF-compatible iPhone selection in DEC-013/015.
- [RF-08](https://trello.com/c/lcZAWVWd/11-rf-08-explicar-el-objetivo-de-la-consulta) owns default question, optional context, text limits, and voter presentation.
- [RF-09](https://trello.com/c/vt8seQzA/12-rf-09-elegir-audiencia-y-controlar-el-enlace) owns Community versus Link only, access checks, discovery, and link lifecycle.
- [RF-10](https://trello.com/c/gMQwBaFB/4-rf-10-publicar-una-consulta) owns publication validation, confirmation, idempotency, and immutable published content.
- [RF-11](https://trello.com/c/5bQ0jXnq/13-rf-11-estados-de-una-consulta) contributes lifecycle states, but its automatic expiry and duration criteria are deferred by DEC-017; RF-19 provides voluntary author closure.
- [RF-37](https://trello.com/c/Dodf7k4R/40-rf-37-proteger-y-borrar-fotograf%C3%ADas) owns private image serving and abandoned-upload deletion. Finalization/deletion now trigger no-buffer consultation photo deletion (DEC-021); exact failure/backup mechanics remain to be designed.
- [RF-36](https://trello.com/c/uhjijsYo/38-rf-36-consultar-y-aceptar-las-reglas-del-servicio) contains an upload-rights reminder and rules acceptance. The owner deferred the full feature from this MVP (DEC-020) but accepted a brief photo-rights reminder in authoring (DEC-022).
- DEC-004 through DEC-009 constrain the stack, sessions, absence of a worker by default, and English product copy. No relevant approved consultation plan exists yet.
- DEC-014 adds web and invited iOS TestFlight as first delivery targets. RF-06 photo selection, navigation-away warning, session behaviour, and preview must be checked on a real iPhone. Native project generation still requires permanent app ID and signing choices.
- `harness/grooming/PHASE-2-scope.md` records the complete-board inventory and a proposed cross-ticket phase boundary. It is a working proposal, not an implementation contract.

## Accepted RF-06 direction and remaining design

### RF-06 boundary confirmed by the product owner (2026-09-22)

1. RF-06 owns the authenticated composer entry, temporary in-session editing state, photo list
   interaction, question/context and Public/Private inputs, faithful author preview, return to the
   intact editor, rights reminder, and discard/navigation warnings. The form is lost on reload or
   app close. Publication is a handoff to RF-10 and must not be represented as successful until its
   server confirmation succeeds.
2. RF-07 owns actual upload, content validation, orientation/metadata-safe normalization, progress,
   retry, and effective photo-count constraints. RF-37 owns private file serving and durable purge of
   removed/abandoned files. RF-09 owns enforceable audience/link access; RF-08 owns text limits and
   voter-facing presentation. RF-06 consumes these contracts rather than duplicating their rules.
3. Design and validate the RF-07/RF-37 upload-session and cleanup contracts before real photo
   authoring is exposed. An owner-bound temporary upload session with durable server-side cleanup
   is the preferred simple boundary: no recoverable draft record or public media URL, and cleanup
   does not depend on a browser exit request. Exact lifetime, storage, retry, and recovery details
   belong in those ticket plans and remain open. The composer can keep only IDs and transient UI
   state. Removing an image revokes its use immediately and schedules physical deletion.
4. Reuse one presentation component for preview and voter detail, with preview clearly identified
   and voting disabled. If the processed image is not yet available, the author sees processing or
   retry state, not a false final preview. Only successfully processed images may be published.
5. On internal navigation, sign-out, or explicit discard with edits, show a clear discard choice;
   cancelling preserves the editor. Browser refresh/close uses the platform's best-effort warning.
   Failed cleanup remains recoverable server-side. A failed publication retains the in-session form
   and offers retry; server idempotency and open-consultation limits belong to RF-10.
6. Build RF-06 against the existing React shell (`App.tsx`, `Navigation.tsx`, `api.ts`) after RF-03
   integration is verified. The current backend has accounts only; consultation, upload, and media
   endpoints/models/migrations do not yet exist. URL routing is needed for later shareable details,
   but RF-06's local editor/preview transition need not choose that routing solution.

The product owner confirmed this RF-06 boundary and the order of defining upload and cleanup
before exposing real photos. RF-06 is a coherent part of the complete phase-2 loop (DEC-010), not
an independently released form with mock images. RF-06 implementation readiness still depends on
approved contracts for its real upload and publication handoffs. This confirmation does not approve
plan finalisation or code implementation. Exact temporary-session lifetime and cleanup mechanics
remain proposed design details for RF-07/RF-37 grooming.

## Re-grooming checkpoint after RF-07 through RF-10 (2026-09-28)

The product owner reactivated RF-06 grooming after RF-10 completed independent validation. The old
dependency blockers in this file are now historical:

- RF-07 and its minimum RF-37 boundary provide owner-bound temporary sessions, private normalized
  media, progress/retry/removal, a renewable 24-hour lease, explicit discard, abandonment cleanup,
  HEIC/HEIF processing and the configured 2–10 limits. `usePhotoUploader` now also exposes the
  publication session ID plus freeze, relinquish and discard operations.
- RF-08 provides the default question, normalized question/context rules, server-owned limits,
  controlled fields and the shared text display.
- RF-09 provides the unselected Public/Private control, reach copy, current access policy, private
  link helpers and owner link controls.
- RF-10 provides the capacity read, atomic/idempotent publication, cleanup-safe promotion,
  protected detail/media reads, current-link endpoints, publication controller and the single
  confirmation summary. Its approved increment is completed and validated, including live
  PostgreSQL concurrency and restart persistence.

### Current repository findings

- `frontend/src/App.tsx` still has only authenticated `home` and `profile` destinations.
  `Navigation.tsx` renders those two buttons in a sticky desktop bar and mobile bottom bar. There is
  no composer destination, routing layer, dirty-navigation interception or `beforeunload` handling.
- `PhotoUploader.tsx` renders the tested upload list but its public component boundary currently
  exposes only `discard`; RF-06 needs either a small extension or a composer-owned use of
  `usePhotoUploader` to access session ID, ready items and URLs, freeze and relinquish without
  duplicating upload behavior.
- `ConsultationTextFields`, `ConsultationTextDisplay`, `AudienceSelector`, `PublishSummary`,
  `useConsultationConfig` and `usePublishConsultation` are reusable. `PublishSummary` currently
  states only the photo count, so RF-06 must compose the actual ready-photo presentation around it
  for a faithful preview.
- `consultationApi.ts` already supplies strict clients for capacity, publication, detail, published
  media and owner link operations. No RF-06 backend endpoint, draft table or migration is needed.
- There is no frontend destination for a newly published consultation. RF-06 must define a narrow
  success destination without accidentally implementing RF-12 lists, RF-14 feed, RF-16 voting or
  RF-26's complete shared-link/authentication-return flow.
- The attempted 2026-09-28 browser recheck of the existing Trello URL reached Trello's sign-in wall,
  so no newer card metadata could be verified through the available browser session. The complete
  2026-09-22 snapshot/recheck above remains the captured backlog input. Trello was not mutated.

### Candidate integration boundary

RF-06 can now be a frontend vertical integration over the implemented contracts. It should create no
draft persistence or parallel business rules. A single composer owns transient question/context,
audience, photo-uploader and mode state; it loads capacity/config before allowing preparation,
validates the combined snapshot, keeps the uploader mounted between edit and preview, freezes it only
while publishing, and relinquishes it only after confirmed success. Cancel/discard clears local
object URLs and requests temporary-session revocation; missing exit requests remain covered by the
server lease. Session loss clears private local state and returns to sign-in.

The main risks are state loss at the edit/preview boundary, mistakenly discarding promoted photos,
duplicate validation rules, accidental persistence of private tokens/files, navigation that bypasses
the discard warning, and claiming iPhone behavior without a signed real-device check. Focused
component/state tests, a built two-account flow and an explicit external iPhone gate cover these
risks. No data migration is expected for RF-06.

### Direction confirmed on 2026-09-22

The product owner rejected an isolated, local-only RF-06 release and confirmed phase 2 as a complete author-and-voter flow through final choice and participant feedback. RF-06 was therefore groomed with its upload, context, audience, publication, access, voting, lifecycle, safety, and retention dependencies. Its composer contract is now settled; rollout audience is not a grooming gate.

### Options and trade-offs considered

1. **Browser-memory preparation as an isolated release:** ruled out by the product owner's complete-flow direction. It remains a possible internal implementation technique for the editor, not a shippable endpoint by itself.
2. **Private persisted draft and uploads:** enables recovery and a direct path to RF-10, but requires consultation schema, owner-only APIs, private file storage/serving, processing, upload limits, lifecycle cleanup, and operational purge. These are substantial RF-07/RF-37 decisions, including how to delete abandoned data if the browser closes.
3. **Integrated phase-2 planning (accepted direction):** define a usable prepare-to-publish-to-vote lifecycle across related tickets, then implement in coherent verified increments with explicit integration gates.

Temporary preparation without a recoverable draft library is accepted (DEC-012). RF-07 through RF-10 have since settled the upload-session mechanics and the RF-06 integration boundary. Rollout type is not a prerequisite for these decisions.

## Questions

### Open

None. The product owner resolved the complete 2026-09-28 batch and explicitly approved plan
finalisation on 2026-09-28.

### Resolved

- 2026-09-28: The product owner answered `1A, 2B - un wizard bonito, 3A, 4A, 5A`. The natural-language
  wizard direction is authoritative over the earlier A/B label mismatch: RF-06 uses a polished
  progressive wizard rather than one long page. The settled flow is:
  1. `Create` is a third permanent primary-navigation destination beside Home and Profile.
  2. The composer is a three-step in-session wizard: **Photos**, **Details**, then **Review and
     publish**. Back/forward navigation preserves the mounted uploader and all inputs. The final step
     is the faithful preview and single RF-10 confirmation; there is no extra publish dialog.
  3. Photos retain gallery-selection order in editor, preview and publication. There is no reorder
     control in the POC; remove/reselect is sufficient.
  4. The untouched default question does not make the wizard dirty. A text/audience change or the
     start of photo selection does. Internal exit/Cancel offers `Keep editing` or `Discard`;
     confirmed discard leaves immediately while server cleanup remains retryable. Refresh/app close
     uses the native best-effort warning. Session loss clears local private state without recovery.
  5. Confirmed publication replaces the wizard with a narrow persisted success/detail view loaded
     by consultation ID. It shows normalized text and actual published photos; Private also shows
     its automatically created link controls. `Back to Home` is available. General routing, feed,
     voting and RF-26's complete shared-link return flow remain out of scope.
- 2026-09-22: The product owner confirmed the concrete RF-06 composer boundary and the order of defining real-upload and cleanup contracts first. This closes the RF-06 scope/ordering confirmation, but does not approve plan finalisation or harness launch.
- 2026-09-22: The product owner confirmed that the author must explicitly choose Public or Private; neither is preselected. The shared RF-06/RF-09 rule is recorded in DEC-024.
- 2026-09-22: The product owner explicitly selected RF-06 for grooming; the complete card was consumed read-only from the configured board. No Trello mutation was performed.
- 2026-09-22: The product owner selected integrated phase-2 planning rather than shipping an isolated local-only preparation screen. The exact ticket set and product rules remain open.
- 2026-09-22: The product owner confirmed the proposed complete phase outcome through author final choice and private voter feedback, plus necessary trust and operational controls (DEC-010). Individual feature specifications remain open.
- 2026-09-22: Phase-2 voting will allow registered accounts without email verification (DEC-011). This does not change RF-06's authoring rules. The likely invitation-only rollout is not a dependency for feature scope.
- 2026-09-22: The product owner chose temporary, non-recoverable preparation (DEC-012) and configurable initial photo-count limits of minimum 2, maximum 10 (DEC-013).
- 2026-09-22: The first usable delivery is web plus invited iOS TestFlight (DEC-014). The product owner wants to keep the first app simple; initial image formats are subsequently resolved in DEC-015.
- 2026-09-22: The product owner confirmed direct iPhone gallery selection without manual conversion (DEC-015). FormCadence code already supports HEIC/HEIF uploads and normalization, although its project state leaves physical-iPhone validation pending. NextPost must prove its own device path.
- 2026-09-22: The product owner confirmed that original uploaded bytes are discarded after processing, leaving only normalized image data (DEC-016). HEIC/HEIF stays in the initial format set as a bounded decoder addition, subject to container and physical-device validation; unexpected difficulty must be raised before dropping it.
- 2026-09-22: The product owner chose voluntary author closure only for phase 2, with no automatic duration or expiry (DEC-017). Any copy or Trello criterion implying a closing date is superseded for this phase.
- 2026-09-22: In the consolidated phase-2 response, the owner accepted a guided default question and optional context, faithful preview and reasonable abandonment warnings, immutable publication, three configurable open consultations, a chronological public feed, confirmed final voting, and author-only aggregates (DEC-018/019). The owner deferred public profile, user-facing block/report/moderation and full service-rule flows (DEC-020). The then-open close/selection, viewing, retention, and comment questions were followed up in DEC-019/021/022.
- 2026-09-22: The owner clarified that finalization declares one, several, or no photos and closes in one action; an unfinalized consultation stays open without expiry (DEC-017/021). Public and Private photos both require a registered account, with the latter also requiring the link. A restricted administrator may manually remove a consultation; a brief photo-rights reminder is accepted (DEC-022). The 30-day post-closure photo buffer, explicit Skip action, comments, overall coincidence metric, and varied photo ordering are deferred (DEC-019/021).
- 2026-09-22: The owner confirmed minimum non-image aggregate and per-participant outcome retention after finalization, even if the finalized consultation is later deleted; deleting an unfinalized consultation yields no coincidence outcome (DEC-023). RF-06's eventual plan must integrate with this lifecycle but does not own the outcome calculations.
- Accepted repository decisions require English product copy and the existing React/FastAPI/PostgreSQL and cookie-session foundation.

## Proposed scope

### In scope (confirmed boundary)

- A visible authenticated entry into consultation preparation from shared navigation.
- Image selection/removal and upload integration, context and audience editing, and an accurate author preview in the full publication journey.
- Warning on leaving with changes and abandoned-file handling aligned with RF-37.
- Accessible, responsive states and tests proportional to the chosen architecture.

### Out of scope (confirmed boundary)

- Public feeds, shared links, voting, results, and profile consultation lists.
- A synchronized library of drafts or permanent autosave; temporary preparation is accepted (DEC-012).
- Independent implementation of RF-07 through RF-11 and RF-37 within the RF-06 ticket; their contracts must be coordinated and may be implemented in separate increments.

## Validation outline

- Test selection/removal, state preservation across wizard steps, navigation warning and discard,
  authorized media reads, isolation from discovery, retry/concurrency handling, invalid files, upload
  failure/retry and abandoned-file cleanup. RF-06 adds no migration or backup contract.
- Manually check refresh/close warning limits, mobile layout, keyboard access, screen-reader labels, and the complete prepare-to-publish handoff.
- Check that the UI reflects actual server publication and audience/access state, including failures and retries.

## Implementation-plan design requested by the product owner (2026-09-22)

This is the historical 2026-09-22 reviewable design in grooming, not an approved implementation plan.
The 2026-09-28 re-grooming checkpoint and consolidated question batch above supersede its stale code
and dependency observations. At that time, the dependency cards were re-read on the configured
Trello board and the repository did not yet contain consultation, upload, image-storage or
publication implementation. Their criteria agreed with DEC-012/013/015/016/017/018/021/022/023.
They were read as dependencies, not separately consumed tickets; no Trello card was changed.

### Candidate RF-06 implementation sequence

1. Integrate a visible `Create consultation` entry with the RF-03 authenticated navigation and
   existing session-loss flow. Keep the current Home/Profile behaviour intact.
2. Introduce one transient composer state for photo order/identifiers, question, optional context,
   audience selection, upload progress/error, preview mode, and dirty state. Keep it in the current
   app session only; reload begins a new preparation and never claims recovery.
3. Consume the RF-07/RF-37 owner-bound temporary-upload API and effective limits. Offer platform
   gallery selection, per-photo progress and retry, removal and enlargement. Show only processed,
   authorized images in the faithful preview. Reject publication while any upload is pending or
   failed, or the active photo count is outside the effective limits.
4. Consume RF-08's shared question/context validation and voter presentation and RF-09's audience
   semantics. Provide an editable helpful default question, optional plain-text context with
   guidance, and clearly explained Public/Private selection with no initial choice. Show a short
   photo-rights reminder.
5. Use the same content presentation for preview and published voter detail, but mark preview as
   author-only and suppress voting. Returning to edit preserves the live form and image references.
6. Warn on internal exit and sign-out when dirty, with Continue editing and Discard choices.
   Browser/app close or reload warning is best effort. Discard requests immediate revocation of
   temporary images; server-side cleanup still handles missing or failed exit requests.
7. Hand off a valid preview to RF-10's publication confirmation. Show actual audience reach before
   submission. Keep the form on validation, network, or server failure; retry through RF-10's
   idempotent contract. On confirmed success, clear temporary state and replace the wizard with
   RF-06's narrow persisted success/detail view. RF-06 does not create its own publication rule.

### Implementation boundary and evidence

- Frontend likely affects `frontend/src/App.tsx`, `Navigation.tsx`, `api.ts`, new composer and shared
  presentation components, styles, and focused tests. The exact component split can follow the
  implemented dependency contracts.
- RF-07 through RF-10 now provide the backend and reusable frontend contracts. RF-06 must consume
  them rather than invent upload, media, publication, or cleanup persistence.
- Test editor state, selection/removal, limits from server configuration, processing/error/retry,
  preview fidelity, return to edit, discard and cancelled navigation, failed publication recovery,
  session loss, and the success handoff. Verify keyboard/mobile layouts and a real iPhone picker,
  along with API authorization and cleanup tests owned by the dependency contracts.
- Do not launch the RF-06 harness before a self-contained plan is explicitly approved and marked
  ready for implementation. The product questions are resolved; plan approval is the remaining
  gate.

### Audience decision settled

The author must actively choose Public or Private; the editor preselects neither (DEC-024). Show
the real reach of each option in the editor and again before publication. Missing or invalid
audience prevents publication on both client and server.

The RF-07/minimum-RF-37 temporary-upload contract, RF-08 text limits, RF-09 link/access contract and
RF-10 idempotent publication contract are implemented and validated. RF-06 remains an integration
increment and does not absorb the later full RF-37, RF-26, feed, vote or results scopes.

## Readiness checklist

- [x] Desired outcome is unambiguous.
- [x] Scope and exclusions are confirmed.
- [x] Code impact was inspected.
- [x] Dependencies and conflicts are resolved.
- [x] Technical approach is selected.
- [x] UX and failure states are confirmed where applicable.
- [x] Security, privacy, retention, and abuse implications are resolved where applicable.
- [x] Data migration and operational implications are resolved where applicable (no RF-06 schema
      change; reuse existing cleanup and publication operations).
- [x] Test and manual validation expectations are agreed.
- [x] No material question remains.
- [x] Product owner explicitly approved plan finalisation on 2026-09-28.
