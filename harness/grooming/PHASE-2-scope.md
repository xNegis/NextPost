# Phase 2 scope - working proposal

## 2026-10-12 reconciliation

This document preserves the historical phase-2 inventory, discussion and owner answers.
Its code observations and proposed delivery ordering are historical. The current owner-interview
reconciliation and backlog continuation are in `PRODUCT-2026-10-12-reorganization.md`;
the exact pre-change Trello snapshot is `TRELLO-2026-10-12-before-reorganization.json`.
Accepted DEC-010 through DEC-035 and approved plans still govern scope. The reorganization does
not approve new feature specifications, reclassify implementation evidence or launch a harness.

## Status

`Grooming - awaiting product-owner confirmation of the proposed technical direction`. This is a cross-ticket scoping note, not an approved implementation plan or an intake snapshot for every card. On 2026-09-22 the product owner confirmed the full author-and-voter phase outcome through RF-21, then narrowed safety/social scope and resolved finalization, audience, image-deletion, and outcome-data retention rules (DEC-018–023). Web and invited iOS TestFlight remain the first delivery targets (DEC-014). The simple technical direction below is proposed for review before individual plans are finalized.

## Backlog inventory

At initial read-only intake on 2026-09-22, the configured `APP - NextPost` board had 40 open cards: 3 in `Fase 1`, 5 in `Fase 2`, 30 in `Funcionalidades`, and 2 in `Descartadas del MVP`. Trello list membership was backlog organisation, not accepted implementation status. Later on 2026-09-22, after the owner explicitly asked to organise Trello, the phase-2 cards were moved/ordered and descriptions aligned with accepted decisions. The verified current counts are 3 in `Fase 1`, 16 in `Fase 2`, 19 in `Funcionalidades`, and 2 in `Descartadas del MVP`. Card completion flags were not changed; repository state remains authoritative for implementation status.

The repository currently implements account entry and profile/navigation only. RF-01 and RF-02 are recorded as completed and validated; RF-03 code exists but project state still records implementation in progress. There is no consultation, upload, private image serving, voting, moderation, or lifecycle code.

### Concrete integration findings

- `frontend/src/App.tsx` and `frontend/src/Navigation.tsx` hold two authenticated destinations in local state. Consultation details and shareable links will need an explicit URL/deep-link strategy; RF-03 deliberately did not add a router.
- `backend/app/models.py` and the current Alembic chain contain only accounts. There are no account verification, suspension, role, block, consultation, image, vote, or report entities. The existing cookie identifies an account but has no account-state invalidation mechanism.
- `docker-compose.yml` persists PostgreSQL only. The backend container has no persistent private-file volume, object storage, scheduler, queue, or media-processing package. The initial image and deletion design must explicitly add the chosen storage and reliable cleanup boundary; automatic consultation expiry is deferred (DEC-017).
- `frontend/package.json` has React and Capacitor but no routing, upload, or image UI package. Native projects remain ungenerated; DEC-014 makes iOS TestFlight preparation and real-device testing explicit before phase-2 delivery.
- These findings are planning constraints, not selections of new libraries or infrastructure.

## Accepted phase-2 outcome

An authenticated author can prepare, publish, share or expose, monitor, finalize by declaring one or more photos or none, and delete a consultation. Another registered account can browse the chronological Public feed or open a Private unlisted link, compare photos, and vote selectively with confirmation. Only the author sees aggregate results; participants may later see private outcome feedback. Publication is immutable and there is no automatic closure. Finalization removes stored consultation photos with no author-only buffer. A restricted administrator can manually remove a consultation; user-facing safety screens are deferred (DEC-017–022).

## Proposed inclusion map

### Core author and voter loop - accepted phase grouping

| Ticket | Why it belongs in the proposed flow |
| --- | --- |
| [RF-06 Prepare](https://trello.com/c/kLphAXQ1/10-rf-06-preparar-una-consulta) | Entry, composition, preview, abandonment. |
| [RF-07 Photos](https://trello.com/c/x8VPrsF9/3-rf-07-subir-y-comparar-varias-fotograf%C3%ADas) | Real upload, validation, processing, comparison. |
| [RF-08 Context](https://trello.com/c/lcZAWVWd/11-rf-08-explicar-el-objetivo-de-la-consulta) | Voter-facing question and context. |
| [RF-09 Audience/link](https://trello.com/c/vt8seQzA/12-rf-09-elegir-audiencia-y-controlar-el-enlace) | Required audience choice and enforceable access; currently in Trello's `Fase 2` list. |
| [RF-10 Publish](https://trello.com/c/gMQwBaFB/4-rf-10-publicar-una-consulta) | Atomic, retry-safe publication. |
| [RF-11 States; expiry deferred](https://trello.com/c/5bQ0jXnq/13-rf-11-estados-de-una-consulta) | Open, manually closed, and unavailable states. Automatic expiry criteria move to a later phase (DEC-017). |
| [RF-12 My consultations](https://trello.com/c/L2mZ6OFf/14-rf-12-gestionar-mis-consultas) | Author needs to find the published item and act on it. |
| [RF-13 Delete](https://trello.com/c/NEYa01VK/16-rf-13-eliminar-una-consulta-propia) | Author withdrawal and image removal. |
| [RF-14 Discover](https://trello.com/c/WVW0cmEp/5-rf-14-descubrir-consultas-que-necesitan-votos) | Community audience needs a way to reach consultations. |
| [RF-16 Vote](https://trello.com/c/rzoUcPdL/17-rf-16-emitir-un-voto-independiente) | The central contribution. |
| [RF-17 Skip](https://trello.com/c/zNKJrbnD/18-rf-17-saltar-una-consulta-sin-votar) | Explicit Skip action deferred; scrolling past without voting is sufficient (DEC-019). |
| [RF-18 Results](https://trello.com/c/GBfvkzU8/19-rf-18-consultar-resultados-como-autor) | Author-only aggregate counts/percentages; voter aggregate access is deferred (DEC-019). |
| [RF-19 Close](https://trello.com/c/cPkS0GiV/20-rf-19-finalizar-una-consulta) | Voluntary finalization closes and stops exposure/voting; no separate choice-free closure action (DEC-021). |
| [RF-20 Final choice](https://trello.com/c/iud9aWtV/21-rf-20-declarar-la-elecci%C3%B3n-final) | Author declares one, several, or no photos as part of finalization (DEC-021). |
| [RF-21 Participation history](https://trello.com/c/J1t1OjVt/22-rf-21-consultar-mi-historial-de-participaci%C3%B3n) | Private, photo-safe outcome feedback for voters; part of the accepted phase finish line. |
| [RF-26 Share](https://trello.com/c/47FD3mrW/28-rf-26-compartir-una-consulta-e-invitar-a-votar) | Makes link-only audience useful, including sign-in/registration return path and safe external previews. |

### Trust and operational cards - owner deferred user-facing features, minimum operations open

| Ticket | Dependency to resolve before real-user exposure |
| --- | --- |
| [RF-29 Block](https://trello.com/c/ICe07E3K/31-rf-29-bloquear-y-desbloquear-usuarios) | Deferred from the first MVP (DEC-020); nickname only appears on consultation content. |
| [RF-30 Report](https://trello.com/c/RnAiil62/30-rf-30-denunciar-contenido-o-comportamiento), [RF-31 Review](https://trello.com/c/KD7MoWMj/32-rf-31-revisar-denuncias-como-moderador), [RF-32 Act](https://trello.com/c/jQPe9AZ6/33-rf-32-retirar-contenido-y-suspender-cuentas) | User-facing report and moderator screens deferred (DEC-020). A restricted manual administrator removal action is accepted (DEC-022), without the rest of the full cards. |
| [RF-33 Abuse limits](https://trello.com/c/YOPHhFvQ/35-rf-33-aplicar-l%C3%ADmites-y-controles-de-abuso) | Broad abuse system deferred (DEC-020); configurable photo and three-open-consultation limits remain accepted. |
| [RF-36 Service rules](https://trello.com/c/uhjijsYo/38-rf-36-consultar-y-aceptar-las-reglas-del-servicio) | Versioned acceptance UI deferred (DEC-020); a short photo-rights reminder is accepted (DEC-022). |
| [RF-37 Image retention](https://trello.com/c/Dodf7k4R/40-rf-37-proteger-y-borrar-fotograf%C3%ADas) | Private serving, closure access cutoff, deletion and abandoned upload purge are fundamental to the photo flow. |
| [RF-40 Parameters/roles](https://trello.com/c/EWXQTHiC/41-rf-40-administrar-par%C3%A1metros-funcionales-y-permisos) | Broad administration and role UI deferred (DEC-020); one restricted file/configuration source for effective photo and open-consultation limits is accepted (DEC-013/018). |

### Candidate later phases or separate beta-readiness work

| Tickets | Reason to defer from the core consultation flow |
| --- | --- |
| [RF-15 Following feed](https://trello.com/c/izEIVUjN/15-rf-15-ver-consultas-de-personas-que-sigo), [RF-24 Follow](https://trello.com/c/GavvxLcv/25-rf-24-seguir-y-dejar-de-seguir-usuarios) | Social graph and its feed are not required for community or link-only consultation. |
| [RF-22 Thank](https://trello.com/c/9TI488uU/23-rf-22-agradecer-una-ayuda-%C3%BAtil), [RF-23 Coincidence metric](https://trello.com/c/bRPbzohn/24-rf-23-mostrar-coincidencia-del-criterio-con-transparencia), [RF-25 Reciprocity](https://trello.com/c/YeU0csET/26-rf-25-reconocer-la-reciprocidad-en-el-reparto-de-consultas) | Reputation and allocation incentives depend on enough trustworthy participation and final choices. |
| [RF-27 In-app notifications](https://trello.com/c/rMzwznMW/27-rf-27-recibir-notificaciones-dentro-de-la-app), [RF-28 Notification preferences](https://trello.com/c/fcVHHYz8/29-rf-28-gestionar-preferencias-de-notificaci%C3%B3n) | The author can check results through RF-12; voter feedback can be checked through RF-21. Notifications add another privacy and event-processing surface. |
| [RF-34 Account deletion](https://trello.com/c/kS00KTWL/34-rf-34-eliminar-mi-cuenta), [RF-35 Data copy](https://trello.com/c/MsETBJ3z/36-rf-35-solicitar-una-copia-de-mis-datos) | Separate account-data lifecycle contracts remain to be groomed; this phase-scoping exercise does not declare them unnecessary or use launch type to decide their placement. |
| [RF-38 Feedback/help](https://trello.com/c/5U4VU3yn/37-rf-38-enviar-feedback-y-solicitar-ayuda-en-la-beta), [RF-39 Beta metrics](https://trello.com/c/FEykWEOZ/39-rf-39-consultar-indicadores-de-uso-de-la-beta) | Beta operation and learning rather than the first consultation transaction; groom separately from the core flow. |
| [RF-XX Verify email](https://trello.com/c/XPk7aCx4/8-rf-xx-verificar-el-correo), [RF-XX Password change/recovery](https://trello.com/c/rrCJIFf3/7-rf-xx-cambiar-la-contrase%C3%B1a) | Currently in `Descartadas del MVP`. DEC-011 resolves the RF-16 conflict for phase 2: registration suffices for voting; verification remains later. Account recovery remains a separate decision. |

RF-01 to RF-03 remain phase-1 foundations and are not reassigned by this proposal.

## Delivery surfaces and smallest coherent increments

- Web and the same Capacitor application on iOS TestFlight are accepted delivery surfaces. The user asked to keep the app simple: prefer one composer and the platform file picker first, with a native photo plugin only if real-device testing proves the browser path insufficient. This is a technical recommendation, not yet an approved picker contract.
- The phase-2 finish line remains the full loop (DEC-010), but implementation can proceed in small vertical increments. Each increment must make its actual capabilities and limits clear; registered-only image access, cleanup, and restricted administrator removal must work before exposing real uploads (DEC-021/022).
- The iOS build needs a permanent app ID and signing configuration before `ios/` is generated (DEC-004/014). A real-device acceptance matrix must cover photo selection, format returned by the picker, upload retry, cookie-backed authentication, app background/foreground, internal and shared links, and safe-area layout. The current Windows workspace cannot itself establish an Xcode/TestFlight build outcome.
- [Apple's photo-format guidance](https://support.apple.com/en-ca/116944) says iPhones can capture HEIF/HEIC and that conversion during sharing depends on the method. [Apple's picker documentation](https://developer.apple.com/documentation/photosui/phpickerconfiguration-swift.struct/assetrepresentationmode) allows different asset representations. **Inference:** do not assume the current web file picker or iOS wrapper always delivers JPEG; test actual devices against DEC-015's accepted-upload contract.
- [Apple's TestFlight overview](https://developer.apple.com/help/app-store-connect/test-a-beta-version/testflight-overview/) describes build upload, tester invitations, and possible review for external testers. This is an operational handoff, not authorization to distribute now.
- The current signed-cookie web session (DEC-008) has only been validated in browser/Compose flows. [Capacitor's cookie documentation](https://capacitorjs.com/docs/apis/cookies) describes iOS third-party-cookie constraints and native cookie support. **Inference:** the iOS build needs an explicit signed-in-session integration test against the real HTTPS API; do not assume the current `localhost` CORS setting and cookie behaviour carry over unchanged. If a different transport is truly required, raise it as a decision against DEC-008 rather than silently changing authentication.

## Proposed delivery order within phase 2

1. Design and verify registered-only image access, no-buffer deletion, abandoned-upload cleanup, and restricted administrator removal before exposing real uploads. Registration-based voter eligibility is accepted (DEC-011); user-facing block/report/moderation is deferred (DEC-020/022).
2. Establish consultation state, owner access, private image storage/processing/serving, parameter configuration, and cleanup mechanisms (RF-07/11/37/40; crosscutting security and failure tests). No scheduled expiry is required.
3. Build preparation, context, audience, confirmation, publication, author detail, and sharing as one coherent path (RF-06/08/09/10/12/26).
4. Add chronological community discovery, selective confirmed voting, and author-only results with server-side eligibility and race protection (RF-14/16/18; explicit RF-17 Skip is deferred).
5. Add atomic author finalization and multi/none declaration, deletion, no-buffer image removal, and text-only participant feedback (RF-11/13/19/20/21/37).
6. Validate the integrated flow, including restricted administrator removal and a brief photo-rights reminder. Full RF-29–33/36 and broad RF-40 screens are deferred (DEC-020/022). Release rollout can be decided separately.

This is ordering for grooming and implementation planning, not an instruction to launch a harness or a claim that every item is approved. The final contracts can be separate RF plans with explicit shared decisions and integration checks.

## Cross-ticket acceptance journeys to specify and verify

These are proposed integration checks for the accepted phase outcome. Exact error copy, limits, and retention windows still need decisions.

1. **Author path:** signed-in account starts preparation; adds and removes permitted photos; enters question/context; chooses audience; previews exactly the voter-facing content; confirms once; sees one open consultation; reloads and finds it in a private owner list.
2. **Community voter path:** a different eligible account scrolls a newest-first list of accessible public consultations, freely passes items, compares enlarged processed photos without prior results, and confirms one final vote. Concurrent retries cannot create extra votes; aggregate results remain author-only.
3. **Link path:** a recipient can follow an unlisted Private link, but must sign in or register before viewing photos; the destination is restored afterwards. Private consultations stay out of feeds. Revocation, regeneration, finalization, and removal invalidate old access.
4. **End path:** author sees correct counts including zero/ties, declares one or several photos or none, and confirms finalization once. No more votes or third-party image reads succeed. The author also loses image access; all stored consultation photos enter immediate no-buffer deletion. Eligible participants get allowed text-only feedback through private history. An explicit none is not a mismatch.
5. **Withdrawal and operating removal:** author deletion or restricted administrator removal immediately cuts application access to the consultation and every processed image or derivative and starts the same no-buffer deletion path. No user-facing report or moderator UI is accepted for this MVP (DEC-020/022).
6. **Boundary and recovery:** ownership, audience, lifecycle, and account-state rules hold through direct API and media URLs, not only UI filters. Uploads rejected or abandoned cannot become public or permanent. Backup restore does not revive access to removed content. Failed processing or cleanup is detectable and recoverable.

## Image-format research and accepted direction

- [MDN's image format guide](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Image_types) lists JPEG, PNG, and WebP as broadly renderable browser formats. It does not establish HEIC as a universal web display format. **Inference:** if HEIC uploads are accepted, the voter-facing derivative should be converted to a broadly supported format rather than served as HEIC.
- The [pillow-heif plugin documentation](https://pillow-heif.readthedocs.io/en/stable/pillow-plugin.html) describes HEIC decoding and metadata handling, so server-side support is feasible but requires a new native-backed dependency and validation in the chosen container. Its orientation [documentation](https://pillow-heif.readthedocs.io/en/stable/reference/HeifImage.html) warns that HEIF orientation handling differs from simply applying an EXIF rotation tag.
- [Pillow's image security guide](https://pillow.readthedocs.io/en/stable/handbook/security.html) documents decompression bombs and recommends explicit format allowlists and pixel/resource limits. The browser file-input `accept` value is only a [selection hint](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/accept), not server validation.
- **Accepted (DEC-015):** allow direct iPhone gallery selection without manual conversion. Initial still-image inputs include JPEG, PNG, WebP, HEIC, and HEIF. Validate actual content on the server, preserve visible orientation, and produce a broadly displayable derivative without source location metadata. Unsupported, malformed, or oversized files need clear feedback. Exact multi-frame handling and size/pixel limits remain open.
- **Rejected for this delivery:** limiting inputs to JPEG/PNG/WebP and asking iPhone testers to change camera settings or manually convert ordinary gallery photos.
- **Accepted (DEC-016):** discard original uploaded bytes after normalization; retain only the processed image and required derivatives. RF-37's retention, backup, and deletion policy must cover these retained files and temporary raw files on failure.
- [PyPI's pillow-heif release files](https://pypi.org/project/pillow-heif/) include CPython 3.13 Linux wheels, matching NextPost's current Python 3.13 container target. Together with the working FormCadence pattern below, this makes HEIC/HEIF a bounded extra decoder dependency rather than a separate iOS UI. **Inference:** retaining HEIC support is proportionate to direct iPhone gallery selection, provided a container build and actual iPhone upload are validated. If those gates reveal disproportionate difficulty, return to the owner before changing DEC-015.

### Existing FormCadence reference (read-only inspection, 2026-09-22)

- The neighbouring `C:/Users/anton/Desktop/FlexGym` repository is the FormCadence implementation. Its `frontend/src/screens/BodyWeightPhotosScreen.tsx` uses ordinary HTML file inputs for gallery and camera selection, includes `.heic`/`.heif` in picker hints and client checks, and supports multiple gallery selection. Its `backend/app/services/image_processing.py` registers `pillow-heif`, accepts JPEG/PNG/WebP/HEIF, applies orientation, normalizes to metadata-free JPEG, and does not retain the uploaded original. This is a relevant pattern, not a NextPost implementation contract.
- `backend/tests/test_image_processing.py` and `backend/tests/test_body_progress_photos.py` include generated HEIF and `photo.heic` upload tests. Thus HEIC support is present in the code and automated tests.
- FormCadence's `harness/context/05_PROJECT_STATE.md` still records a signed TestFlight build, installation, and focused physical-iPhone validation as pending. Do not claim that repository proves an end-to-end iPhone gallery upload; NextPost must validate it on a real device.
- NextPost has different audience, consultation lifecycle, and retention rules. Its eventual plan must be self-contained and may borrow only the useful processing approach after those rules are settled. The product owner confirmed on 2026-09-22 that originals should be discarded after processing (DEC-016), matching this narrow part of FormCadence's behaviour.

## Shared-limit configuration approach

- **Accepted requirement:** the two-to-ten photo count and three-open-consultation cap come from one restricted application configuration source, are easy to change without editing business rules, and are enforced by the server (DEC-013/018).
- **Deployment configuration (recommended, mechanism unaccepted):** one server-owned settings file/source exposes effective values through a narrow read contract; the client displays those values, while the server revalidates upload and publication. An authorized operator changes settings and restarts/redeploys the service. This meets “not hardcoded” without building administration screens, but changes are not immediate.
- **Runtime administration:** authorized admins change validated values without restart, with versioned audit history. This supports rapid tuning but adds new data, roles, concurrency, and UI/API surface under RF-40.
- In either model, a consultation already published keeps its accepted image set. The app must handle a limit changing while someone is preparing: give an understandable error and let the author adjust without losing valid uploads. Invalid configurations fail clearly before serving contradictory guidance.

## Lifecycle mechanism to settle (unaccepted details)

- DEC-017 removes `expires_at`, automatic consultation closure, and any duration selector from phase 2. The owner confirmed that a consultation stays open until its author finalizes or deletes it, or the administrator removes it. Finalization declares one, several, or no photos and closes atomically (DEC-021).
- Finalization, deletion, and administrator removal have no author-only image buffer: revoke image access immediately and initiate physical deletion of all processed photos/derivatives (DEC-021/022). Physical deletion of abandoned files still requires a reliable process when no user opens the app. The current Compose stack has only frontend, backend, and database; it has no scheduler or persistent image volume. The plan must make failures detectable/retryable without turning a deletion failure into renewed access.
- The data model must distinguish immediate access revocation from later physical deletion, record pending cleanup work durably, and make retries idempotent. The exact files retained, deadlines, backup cycle, and failure alerting remain product/operations decisions; none are accepted yet.

## Material details still open after the owner's follow-up

The owner resolved the non-image outcome contract in DEC-023. The remaining work is to turn the
accepted rules into self-contained per-ticket contracts, with the following implementation choices
still proposed rather than approved as a final plan.

1. **Deletion operation:** Select simple private storage with no deliberate post-finalization image buffer; define how physical deletion and backup/caches are handled when a storage operation fails. Access must remain revoked. The owner rejected the 30-day photo window (DEC-021); an implementation plan must not reintroduce it under another name.
2. **Implementation and validation:** Select file/resource bounds, a shared restricted configuration mechanism, and TestFlight signing path when available. Validate author/voter journeys, publication/vote/finalization races, access matrix, image metadata and deletion, administrator removal, and web/iPhone usability. These are engineering and delivery decisions unless a new product trade-off appears.

### Simple technical direction for plan review (proposed)

- Current `backend/app/config.py` is the server-owned settings entry point. Extend it with validated
  minimum/maximum photos (initially 2/10), maximum open consultations (initially 3), and file
  limits. Put deployable values in the existing `.env`/Compose configuration; a service restart
  applies changes. Expose effective non-secret values through a narrow authenticated read response
  so the UI and server enforce the same settings. No runtime admin parameter screen.
- Keep unpublished form state in the client session. Prepublication uploads use an opaque,
  owner-bound temporary upload session and private processed files; no recoverable draft library.
  Purge abandoned uploads on a bounded timer, initially proposed as 24 hours since last activity.
- Add private persistent image storage outside the frontend/Nginx public root. Every image response
  checks the current account, Public/Private audience, consultation state, and link capability; do
  not issue permanent public file URLs or rely on the UI to hide inaccessible images. Normalized
  files are the only long-lived images while a consultation is open; originals are discarded after
  processing (DEC-016).
- For the first host, prefer a restricted persistent backend volume or equivalent private store
  without image versioning or image backups. PostgreSQL backups alone do not contain photos. This
  keeps finalization/deletion free of intentionally retained image copies; it means a host/storage
  loss may also lose photos of still-open consultations, which must be stated in the operational
  handoff. Revisit this storage choice before broader rollout if durability needs change.
- Finalization records the selected set (possibly empty), freezes outcome rows, revokes image
  authorization, and requests deletion of every processed image. Author deletion and restricted
  administrator removal use the same revocation/deletion boundary. A durable deletion marker and
  repeatable cleanup pass detect/retry storage failures without re-exposing files. A small periodic
  maintenance task within the existing backend process can purge abandoned/retry files without
  introducing a queue or general worker; startup also runs a sweep. Do not report a physical purge
  as complete until file absence is verified.
- Once finalized, retain non-image outcome data as DEC-023 permits. While open, one vote per
  account/consultation is enforced transactionally and concurrent finalization rejects late votes.
  A finalized item's author view can display aggregate counts with stable photo labels but no
  photos; private participant history uses Matched, Not matched, or No choice without leaking other
  voters' choices.
- Keep file processing deliberately narrow: still JPEG, PNG, WebP, and HEIC/HEIF input; normalized
  JPEG output preserving visible orientation and excluding source metadata; reject video/animation.
  Initial proposed ceilings are 15 MiB and 40 megapixels per input and 2560 pixels for the longest
  output edge, subject to container and real iPhone validation. The owner delegated these
  resource-limit details to Codex with a preference for simplicity.
- Use a restricted, logged administrator command or equivalent internal endpoint to remove a
  consultation; do not create a public moderation UI or roles console. The exact operator identity
  and deployment access must be explicit in the RF-32/RF-37 handoff.
- `frontend/src/App.tsx` and `Navigation.tsx` currently switch local Home/Profile state. Shareable
  consultation URLs and sign-in return-to-destination require a real route/deep-link boundary;
  select a small routing solution in the RF-09/RF-26 plan rather than inventing consultation views
  with local-only navigation. Native iOS packaging and signed-cookie/API validation remain an
  explicit delivery gate (DEC-014).

## Consolidated product-owner question batch sent (2026-09-22)

This preserves the questions and proposals sent to the owner. The answers are recorded below and in
DEC-018/019/020; do not read an unqualified proposal in this historical batch as accepted scope.
Technical implementation details can be selected by Codex in the individual plans once product
rules are agreed.

1. **Scope:** Confirm the core RF-06–14 (excluding RF-15), RF-16–21, and RF-26 grouping, with the
   necessary RF-29–33/36/37/40 safety capabilities. Keep following, reputation, notifications,
   account export/deletion, and beta feedback/metrics as separately groomed work? RF-11 contributes
   states only; automatic expiry is deferred.
2. **Never closed:** Is an author's inaction allowed to leave a consultation and its photos available
   to its chosen audience indefinitely, until author withdrawal or moderation removal? Recommendation:
   say this explicitly before publication; no hidden timer or automatic intervention.
3. **Authoring text:** Should the default, editable question be “Which photo should I post?” with
   optional plain-text context? Choose visible question/context limits. Recommendation: 120/500
   characters; no categories, social-account links, or rich text.
4. **Audience:** Default to Link only (less exposure) or Community? Should audience be immutable after
   publication? Recommendation: Link only default; explicit Community choice; no post-publication
   widening or audience switching.
5. **Preview and abandonment:** Should preview show the same processed photos/question/context as a
   voter, without voting controls, and return to the intact editor in the same session? Warn on
   internal exit/sign-out and best-effort browser close/refresh; explicit Discard is confirmed once?
6. **Published edits and concurrency:** Keep photos/question/context fixed after publication, with
   closing or deleting and creating another consultation to correct an error? How many open
   consultations may one account have? Recommendation: fixed content and a configurable cap of three
   open consultations per author initially.
7. **Photo edge cases:** Accept still photos only, with HEIC/HEIF primary image normalized; reject
   video, GIF animation, and unsupported multi-frame input? Recommendation: an initial 15 MiB and
   40-megapixel input ceiling, with the processed derivative limited to 2560 pixels on its longest
   edge, all validated and adjustable without changing the upload flow. Codex can refine these
   technical limits with device evidence unless the owner has a product requirement for them.
8. **Discovery and skip:** Use one simple Community queue with only eligible open consultations,
   prioritizing fewer votes and longer wait? After Skip, hide the item for that session but allow it
   again later? No follows, categories, or personalized ranking in this phase.
9. **Voting:** One immutable confirmed vote per registered eligible account, author excluded,
   photo order varied across voters but stable within a viewing session? Keep choices editable until
   confirmation, and never show aggregate results first?
10. **Results and privacy:** Author sees live aggregate counts/percentages, including zero and ties;
    a voter sees aggregate results only after voting while the consultation is open and accessible?
    Do not expose identities or individual choices to the author?
11. **Sharing and links:** Allow copy/share for Community and Link only. A Link only URL is
    unlisted but forwardable to any eligible registered account. Allow revocation/regeneration,
    making old links unusable; external previews remain generic and sign-in returns to the target?
12. **Identity surface:** Show the author's nickname on a consultation and provide Block/Report there
    without introducing a public profile page yet? Provide block management in the private profile?
13. **Close and final choice:** Author may close without choosing; declaring one photo or “none”
    while open closes it as part of confirmation; a later declaration is allowed while retained
    photos exist. First declaration is final; no reopening or silent edits?
14. **Participant feedback:** Keep a private, text-only participation history after closure, with
    Open/Pending/Matched/Not matched/Unavailable states; no post-closure photo access or public
    feedback? If no final choice, avoid treating the vote as a mismatch.
15. **Closed-photo retention:** How long may the author see processed photos and declare a final
    choice after voluntary closure? Recommendation: a fixed window such as 30 days, then physical
    purge; results and text-only histories need their own retention rule.
16. **Deletion timing:** On author deletion or moderation removal, cut access immediately; how soon
    must stored images be physically purged, and how long may backups retain inaccessible copies?
    Set the abandoned-upload purge time too. Recommendation: explicit short, operationally
    achievable windows rather than promising instantaneous physical erasure.
17. **Block effects:** Should blocking cut both parties' future content access and interaction,
    including direct links, while previous valid votes remain in aggregate totals? Unblock does not
    restore prior follows or notify the other party.
18. **Reporting and moderation:** Include the usable report → restricted review → remove/suspend
    path in phase 2? Should moderators be able to reverse a mistaken action while data remains,
    invalidate proven fraudulent votes, and give the affected account a reason/review route? Define
    if minimal account reporting is reachable from consultation identity rather than public profiles.
19. **Moderation evidence:** If a report concerns photos later deleted, may a restricted evidence
    copy be retained, and for how long? Recommendation: no default duplicate of photos; any
    exception requires a defined purpose, access list, and deadline.
20. **Limits and roles:** Accept configurable server-side limits for uploads, open consultations,
    voting, sign-in, and reports, with clear retry feedback? Manage moderator roles and settings via
    restricted operational configuration initially, without a broad admin settings UI?
21. **Service rules:** Include readable terms/privacy/content rules and an unprechecked, versioned
    acceptance step before registration/use, plus the photo-rights reminder? The owner must supply
    or approve actual policy copy and a contact route; specify whether existing accounts must
    accept a new version before further use.
22. **iOS handoff:** The web and invited TestFlight target is accepted. When phase-2 implementation
    is ready, who supplies the permanent app ID, Apple team/signing access, and invites? This is a
    delivery dependency rather than a reason to hold product grooming.

## Product-owner response to the complete batch (2026-09-22)

- **1:** Accepted the suggested core grouping; subsequent answers defer user-facing RF-29–33/36
  and broad RF-40 administration (DEC-020).
- **2:** Rejected the framing of indefinite visibility and emphasized that an author must end their
  consultation and select which photo or photos they chose. The case in which the author never acts
  still needs a precise answer; no automatic expiry was reintroduced.
- **3:** Accepted a helpful default title/question, giving “Which photos should I post?” as an
  example, plus optional context with guiding placeholder text. The proposed exact character limits
  were not explicitly repeated and can be finalized as a technical/content detail.
- **4:** Wants two clearly named modes, Private (link) and Public. Whether Public allows anonymous
  photo viewing or means all registered accounts is unresolved.
- **5:** Accepted faithful preview, editor return, and reasonable unsaved-change warnings.
- **6:** Rejected post-publication edits after considering vote integrity. Accepted an initial cap
  of three open consultations per author, easily changed alongside the photo limits in one
  application configuration source (DEC-018).
- **7:** Delegated still-image edge-case and resource bounds to Codex, emphasizing simplicity.
- **8:** Wants a Reddit-like vertically scrolling feed of all visible public consultations, newest
  first, without personalization or a complex allocation algorithm (DEC-019). Users may scroll
  past anything they do not want to vote on.
- **9:** Accepted a final, non-editable vote with a confirmation/cancel opportunity. Did not
  understand the proposal to vary photo order; it is not accepted (DEC-019).
- **10:** Author sees aggregate totals/percentages, never individual voters by photo; voters see
  no aggregate results. Optional voter comments were suggested tentatively and need a separate
  scope decision (DEC-019).
- **11:** Accepted link copying/sharing, retained destination through sign-in/registration,
  revocation/regeneration, and generic external previews, subject to manageable complexity.
- **12:** Wants only author nickname on consultations. Public profiles, Block, and Report are
  deferred (DEC-020).
- **13:** Said OK to the earlier proposal of closing without choosing, declaring one photo or none
  later, and a final non-reopenable choice. This conflicts with answer 2's required selection of
  “photo or photos”; exact rule remains open.
- **14:** Wants optional selective voting while scrolling, plus a private participation/history
  view showing whether votes matched the author's eventual selection. Sees retained participation
  data as useful for later algorithm work; actual model use is not approved by this alone.
- **15:** Accepted 30 days as an author post-closure photo-access window.
- **16:** Wants photos and other heavy image data removed from storage after closure, deletion, or
  withdrawal, while useful database vote/coincidence metadata remains. Timing after closure
  conflicts with answer 15; exact retained fields and deadlines remain open.
- **17–21:** Does not want block, report/moderation, evidence retention, broad abuse/role controls,
  or versioned service-rule acceptance in the first MVP (DEC-020). Whether a minimal internal
  content-removal route, contact method, and photo-rights notice are still acceptable is open.
- **22:** Permanent iOS app ID/signing owner will be decided later; this does not hold product
  grooming, but it remains a TestFlight delivery dependency.

## Follow-up resolution from the product owner (2026-09-22)

- Finalization requires the author to declare one, several, or no photos, and confirmation closes
  the consultation in that same action. There is no separate close-now/choose-later path. A
  consultation left untouched stays open without a time limit (DEC-017/021).
- Public means visible to every registered account. Private means visible only to registered
  accounts with the link. An unauthenticated visitor sees no consultation photos in either mode
  (DEC-022).
- The owner withdrew the earlier 30-day post-closure photo window. Finalization, deletion, and
  administrator removal revoke photo access and start deletion without a deliberate buffer. No
  archived photo copy is kept for later model work (DEC-021/022).
- When an open consultation is deleted or removed before finalization, there is no declared
  outcome to retain for coincidence analysis. The minimum non-image records from finalized
  consultations and their exact lifetime still need a precise data contract.
- Explicit Skip, optional voter comments, an overall coincidence metric, and varied photo order
  are deferred. Users freely scroll past posts and can see per-consultation private history
  outcomes (DEC-019).
- A restricted administrator can manually remove problematic consultations; no user-facing
  report/block/moderator screens are added. The composer gives a brief photo-rights reminder
  (DEC-020/022).
- Permanent TestFlight app ID and signing arrangements are deferred until packaging work.
- The owner subsequently confirmed the narrow non-image outcome contract: delete photos at
  finalization, keep only aggregate and per-participant Matched/Not matched/No choice records while
  the relevant accounts exist, retain those outcomes after later deletion of a finalized
  consultation, and derive no coincidence outcome from deletion before finalization (DEC-023).

## Resolved cross-ticket decisions

- 2026-09-22: Phase 2 covers the complete consultation loop through final choice and private voter feedback (DEC-010).
- 2026-09-22: Registration is enough for phase-2 voting; email verification is deferred (DEC-011). Other access/eligibility rules remain in force.
- 2026-09-22: An invitation-only start is likely but is not a dependency for defining phase-2 functionality. Do not hold grooming on a rollout-type choice.
- 2026-09-22: First delivery targets are web and invited iOS TestFlight, with real-device validation and native build prerequisites (DEC-014). Simplicity favours shared web UI and the platform file picker unless testing proves that insufficient.
- 2026-09-22: iPhone testers must select ordinary gallery photos without manual conversion. JPEG/PNG/WebP/HEIC/HEIF are initial still-image inputs, with server-side validation and compatible derivatives (DEC-015). FormCadence code and tests demonstrate a relevant pattern but not completed physical-iPhone evidence.
- 2026-09-22: Store only normalized consultation image data and necessary derivatives; delete the original upload after processing or failure (DEC-016). HEIC/HEIF support stays in scope because an existing local pattern and available Python 3.13 Linux wheels make it a bounded decoder addition; validate the real build and device path before implementation completion.
- 2026-09-22: Preparation is temporary and not recoverable after close/reload; any prepublication server files require abandoned-upload cleanup (DEC-012).
- 2026-09-22: Publishable consultations initially require 2–10 photos, with both values configurable and displayed/enforced from one effective source (DEC-013). Configuration delivery and change timing remain open.
- 2026-09-22: Consultations have no automatic duration or expiry in phase 2. The author can close voluntarily; moderation removal and author deletion are separate actions (DEC-017). RF-11's expiry-specific criteria are deferred, while cleanup after abandonment or closure remains necessary.
- 2026-09-22: Published photos/text/audience are fixed; three open consultations per author and the photo-count limits share one restricted, easily editable configuration source (DEC-018).
- 2026-09-22: Public feed is a newest-first scroll with optional selective voting. Votes require final confirmation and cannot change. Only the author sees aggregate results, without individual voter identities (DEC-019).
- 2026-09-22: Consultation identity is the author's nickname only. Public profile, user-facing block/report/moderation, broad abuse/admin surfaces, and versioned service-rule acceptance are deferred from the first MVP (DEC-020). Restricted manual administrator removal was subsequently accepted (DEC-022).
- 2026-09-22: Finalization declares one, several, or no photos and closes atomically. No author-only 30-day image buffer remains; images are removed on finalization/deletion and unfinalized consultations stay open until acted upon (DEC-017/021).
- 2026-09-22: Public photos are visible to all registered accounts; Private photos only to registered accounts holding the link. Restricted manual administrator removal and a brief photo-rights reminder are accepted without the full safety screens (DEC-022).
- 2026-09-22: Once finalized, retain only minimum non-image aggregate and account-linked outcome records for private history/statistics while relevant participant accounts exist. Deleting an unfinalized consultation produces no coincidence outcome; deleting a finalized one does not erase its already recorded private outcomes (DEC-023).
- 2026-09-22: The authoring form starts with neither Public nor Private selected; an explicit choice is required before publication (DEC-024). This supersedes the historical proposal for a default audience in the question batch above.

The accepted high-level phase outcome is recorded in DEC-010. Other proposals in this note still require product-owner confirmation. Finalisation of each implementation plan remains a separate explicit gate.
