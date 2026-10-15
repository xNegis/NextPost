# RF-08 - Explicar el objetivo de la consulta - Grooming

## Status

`Ready for implementation`

Research started on 2026-09-22; recorded on 2026-09-23 after an interrupted turn.
This is a grooming record; implementation authority is the approved self-contained plan at
`harness/features/RF-08-Implementation-plan.md`. The owner answered `1A 2A` and explicitly approved
plan finalisation on 2026-09-23. All material questions are resolved. Harness launch is not approved.

## Trello snapshot

- Title: `RF-08 · Explicar el objetivo de la consulta`
- URL: https://trello.com/c/lcZAWVWd/11-rf-08-explicar-el-objetivo-de-la-consulta
- Board: `APP - NextPost`, https://trello.com/b/CgBkRg78/app-nextpost
- Board ID: `6aa903892e7d7b54f23fae1b` (matches configured board)
- Card ID: `6aa90be25de870fbdaad9b5a`
- List: `Fase 2`
- Labels: None; response reports no omitted labels.
- Members: None
- Start date / due date: None / None
- Archived: No
- Card completion / due completion: False / False
- Position: `140737488502784`
- Checklists: None; response reports no omitted checklists.
- Comments: None; response reports no omitted comments.
- Captured on: 2026-09-22 UTC, during this task's read-only intake, before the
  `2026-09-22T21:08:23Z` research checkpoint; exact read timestamp was not returned by the connector.
- Last Trello activity at intake: `2026-09-22T14:34:52.044Z`

### Description and acceptance criteria at intake

**Historia de usuario**

Como autor, quiero explicar qué decisión intento tomar para que los votos tengan contexto.

**Criterios de fase 2 acordados**

- La pregunta se precarga con un ejemplo útil, como “Which photos should I post?”, y puedo editarla.
- El contexto es opcional y muestra una indicación que ayuda a añadir detalles relevantes.
- Pregunta y contexto aparecen junto a las fotos. Son texto simple, con límites visibles y validación antes de publicar.
- No se necesitan categorías, etiquetas ni conexión con cuentas sociales.

Referencia: DEC-009/018 y grooming de fase 2.

Identifier, title, list and content agree. The card does not settle what happens after deliberately
clearing the default question or whether longer context is initially collapsed. Trello was read only.

## Intended outcome

Authors explain the comparison through an editable question and optional context. Voters see the
same plain text that the author reviewed. RF-08 supplies reusable text editing, validation and
presentation boundaries for RF-06 and RF-10, without introducing recoverable drafts or independently
shipping the composer.

## Current code findings

- Read `AGENTS.md`, all seven context documents in their required order, the grooming template,
  `PHASE-2-scope.md`, RF-06/RF-07 grooming, RF-07's complete approved plan, and RF-03 grooming/plan.
  No RF-08, RF-09 or RF-10 grooming file or implementation plan existed at intake. Their related
  discussion is in the phase scope and RF-06 notes.
- Initial and resumed `git status --short` are clean. Historical statements that the repository is
  entirely untracked describe earlier intake, not the present worktree.
- `frontend/src/App.tsx` still has Home/Profile local navigation. There is no consultation composer,
  published detail, text editor or publication endpoint. New text components/services are intended
  boundaries; their final filenames have not been invented as existing paths.
- `backend/app/models.py` now contains Account, PhotoUploadSession and PhotoUploadImage. There is
  no Consultation entity or question/context column. RF-07's upload session deliberately contains
  no question, context or audience. Alembic currently ends at `20260922_0003_photo_uploads.py`.
- `backend/app/config.py` owns startup-validated settings. The authenticated
  `GET /api/application-config` in `backend/app/api/photos.py`, with its response schema in
  `backend/app/schemas.py` and client in `frontend/src/photoApi.ts`, exposes photo limits and the
  maximum open consultations. RF-08 can extend this established contract with text limits.
- `backend/app/main.py` already maps request-validation failures to HTTP 422 with
  `detail.code = validation_error` and `detail.field_errors`. Reuse this envelope; do not echo
  submitted free text in errors or logs.
- `backend/app/validation.py` and `frontend/src/validation.ts` contain account rules only. Password
  length already uses Python code-point length and JavaScript `Array.from(value).length`, providing
  a local precedent for consistent Unicode text counting.
- `frontend/src/PhotoUploader.tsx` exposes ordered ready image IDs, a publish-blocked callback,
  session-loss callback and imperative discard. `frontend/src/usePhotoUploader.ts` maintains private
  blob URLs, upload state and lease renewal. Neither public result exposes the upload-session ID;
  its hook cleanup discards the server session on unmount. Editor/preview must therefore share a
  live uploader lifetime; simply replacing the editor with preview would discard its photos.
- The current photo publish-blocked flag reports non-ready items; it does not itself enforce the
  minimum photo count. RF-06 must compose text/config/count/session/photo validation, and RF-10
  must enforce all authoritative publication rules.
- `backend/app/photo_service.py::validate_publication_images(db, storage, account_id, session_id,
  ordered_ids, now)` locks the session and validates owner, active lease, unique ordered IDs,
  configured count, ready state and byte presence. It returns rows without committing or publishing.
  It validates the supplied IDs, not every historical attempt in the session.
- There is no promoted session/image state or consultation relationship yet. RF-10 must implement
  atomic promotion and coordinate cleanup so published files cannot be discarded by a composer
  unmount or abandoned-session sweep. These are future integration requirements, not RF-08 changes.
- RF-07's automated validation is recorded in project state; it was not rerun as part of this
  documentation-only grooming. Real iPhone/TestFlight and final composer checks remain pending.

## Dependencies and conflicts

- **RF-06:** owns navigation, transient composer state, dirty tracking, preview/edit preservation,
  discard, session loss and publication handoff. RF-08 supplies controlled text fields, normalized
  text validation and a shared presentation component. The uploader lifecycle/ID gaps above must be
  resolved during RF-06/RF-10 integration, without adding image lifecycle scope to RF-08.
- **RF-07:** supplies effective configuration and private image contracts. Text must not be added
  to its temporary upload records or cause additional session creation or lease renewals.
- **RF-09:** owns authorization/link enforcement. Read its current card as a dependency only:
  https://trello.com/c/vt8seQzA/12-rf-09-elegir-audiencia-y-controlar-el-enlace
  (`Fase 2`, last activity `2026-09-22T14:34:54.699Z`). Public requires registration; Private
  requires registration plus link; revocation/regeneration and finalization invalidate old access.
  Text belongs to the same protected consultation content; external previews remain generic as
  accepted in the phase-2 response. RF-08 adds no anonymous text endpoint.
- **RF-10:** owns persistence, publication request, authoritative validation, transaction,
  idempotency and photo promotion. Read its current card as a dependency only:
  https://trello.com/c/gMQwBaFB/4-rf-10-publicar-una-consulta
  (`Fase 2`, last activity `2026-09-22T14:34:57.786Z`). It requires a valid question, processed
  photos, explicit audience and the configured open-consultation cap. RF-08's text validator must
  be called inside that publication flow before any state is committed.
- **Accepted decisions:** English product copy (DEC-009), temporary preparation (DEC-012), immutable
  publication (DEC-018), shared faithful preview (confirmed RF-06 boundary), registered audiences
  (DEC-022/024), and minimum outcome retention (DEC-023) remain fixed.
- **Stale notes:** RF-06 and phase-scope historical findings say uploads/config/private storage are
  absent and lifetime/config decisions remain open. RF-07's approved plan, implemented code and
  current project state supersede those historical statements. Public/Private supersede the older
  Community/Link only wording. No accepted product contradiction blocks RF-08.
- **Ordering:** RF-08 -> RF-09 -> RF-10 -> finalise and implement RF-06. RF-08 may become a tested
  reusable increment before a product route exists, as RF-07 did. Integrated publication and voter
  access proof belongs to the consuming tickets; it must not be claimed by isolated component tests.

## Settled contract

The following technical package resolves routine details under the owner's delegation and applies
the confirmed Q1/Q2 answers. The approved plan now records the self-contained implementation contract.

### Text and editing

- Preload the actual editable value `Which photos should I post?` once when creating a composer.
  Context starts empty. Suggested guidance: `For example, where will you post these photos, and
  what would you like people to compare?` This guidance is never stored as user content.
- Use `Question` and `Context (optional)` labels. Question is a single-line field; context permits
  paragraphs. Product chrome is English; user text may use other languages and emoji, without
  translation or language detection.
- Start with maximum 120 code points for question and 500 for context. The phase-2 owner response
  explicitly left the proposed exact limits to technical/content finalisation; do not ask again.
  Extend the existing server config and authenticated response; restart applies changes. Validate
  positive integer bounds and that the default question fits. No independent client limit constants.
- Normalize line endings, use NFC, and trim surrounding whitespace consistently in client/server.
  Preserve internal context line breaks; flatten question line breaks/tabs from pasted input to
  spaces. Reject unsupported control characters and malformed Unicode with field errors; preserve
  legitimate language/emoji joining characters. Define identical normalization fixtures in the plan.
  Count normalized Unicode code points, not bytes or UTF-16 units; composite emoji may count as more
  than one. No word-count, question-mark or semantic-quality requirement.
- Empty normalized context becomes null. A cleared question stays empty and requires correction
  before preview/publication. Do not restore the default automatically or add a default-restoration
  action. The server independently rejects missing, null or normalized-empty questions (Q1A).
- Show current/max counters. Allow correction of excess pasted/typed content, mark it invalid, and
  block progression/publication without silent truncation. Do not interfere with IME composition.
  Validate on blur and attempted progression; update an already displayed error while correcting.
- Show safe field-specific English errors and focus the first invalid field when progression is
  attempted. Keep entered text on validation/network/server failure. Loading or invalid configuration
  blocks progression and offers retry without discarding text. No per-keystroke server request.

### Presentation, accessibility and privacy

- Use one text display component for preview and eventual voter detail; RF-06 composes it with
  processed photos. Show the complete question followed by complete context above the photos,
  without collapse, expansion controls or truncation. Omit an empty context block (Q2A).
- Render text through React text nodes, with wrapping and appropriate text direction. No HTML or
  Markdown interpretation, automatic clickable URLs, mentions, embeds or social integrations.
  Literal markup and URL text remain text. No content classification or profanity service is added.
- Provide visible labels, descriptions/counters linked to fields, `aria-invalid`, associated error
  messages, restrained live announcements, visible focus and keyboard operation. Validate 320 px,
  200% zoom, long unbroken strings, RTL text and mobile keyboard/IME behavior. Touch actions use
  the established 44 px minimum. No new accessibility product decision is required.
- Keep unpublished text in the live composer memory. Do not put it in upload-session rows,
  local/session storage, URLs, logs, telemetry or analytics. Clear it with the composer on confirmed
  discard/sign-out/session loss. Returning from preview preserves it under RF-06's accepted rule.
- Apply consultation audience/lifecycle access to published text as well as photos. Do not use it
  for anonymous previews or copy it into retained outcome statistics. DEC-023 does not authorize
  extra free-text retention; any later history-title retention proposal requires separate grooming.
  RF-08 introduces no persistence, backup, deletion worker or new data-retention mechanism.

### Data, API and operations

- Add a reusable strict backend text value/schema with `question: string` and optional nullable
  `context`, plus a pure validator producing normalized values and field errors. Omitted/null context
  is allowed; non-string values are rejected. A missing question is rejected by the server; the
  default is an editor convenience, never an API fallback for malformed requests.
- Extend application-config additively with question/context maxima and strengthen runtime checking
  of the added values. Existing photo fields remain compatible. No standalone save-draft or
  validate-text HTTP endpoint is needed.
- RF-10 will store normalized question/context with the consultation and publish them atomically
  with its other content. RF-08 needs no database migration. Do not create a Consultation table early
  just to hold text. RF-10 owns the future migration, ownership and read response.
- RF-10 should return the established 422 field-error envelope, preserve retry safety, and include
  normalized text in its immutable publication/idempotency contract. It must validate current limits
  if configuration changed since the editor loaded. Previously published text is not invalidated
  merely because a limit is lowered; only new publication uses the new limit.
- Extend `.env.example`, configuration documentation and relevant deployment configuration when
  implementing. Invalid settings fail startup. No new dependency, service, queue or operational
  credential is needed for RF-08. Error reporting may identify field/code, never raw user content.

### Alternatives considered

- Reusable fields, presentation and validators fit the accepted per-ticket boundaries and permit
  RF-06/RF-10 to consume tested behavior. Recommended.
- Adding a complete composer or publication endpoint in RF-08 would cross the confirmed RF-06/RF-10
  boundaries and the owner's requested order. Not proposed.
- Persisting prepublication text as a draft conflicts with DEC-012 and RF-07's upload-only session.

## Questions

### Open

None. A post-answer review found no new material blocker in RF-08's scope, integration boundaries,
UX, validation, errors, security, privacy, data, API, limits, accessibility, tests or operations.
RF-06/RF-10's identified upload-integration work and the physical-iPhone delivery gate remain
explicit consuming-ticket requirements; they do not prevent finalising RF-08's reusable increment.

### Historical single consolidated batch — answered on 2026-09-23

1. **Product / empty question — blocking for finalisation:** after the author deletes the preloaded
   question, should the editor (A, recommended) keep it empty and require correction before preview/
   publication, or (B) offer an explicit `Use default question` action before continuing? Both retain
   the accepted valid-question requirement; neither silently substitutes text in the publication
   API. A is the smallest flow and respects deliberate editing. B adds a recovery shortcut.
2. **Voter UX / context visibility — blocking for the shared presentation contract:** should preview
   and voter detail (A, recommended) show the full question and up to 500 characters of context above
   the photos, or (B) show the full question and initially collapse context behind `Show context`?
   A makes the author's intent available before comparing without another action. B makes a shorter
   screen but risks voters missing context. Empty context is omitted in both options; preview must
   mirror the selected behavior. Feed-specific compact cards remain RF-14 scope.

No further material question was identified for security, privacy, schema, API, configuration,
accessibility, validation, operations or ticket boundaries within this increment. Their derived
approach is recorded above for review, without presenting routine technical decisions as blockers.
The answers alone did not approve finalisation. The closed contract was subsequently presented and
the owner explicitly approved creation of the implementation plan on 2026-09-23.

### Resolved / inherited

- The owner explicitly selected RF-08 and requested read-only Trello intake, repository research,
  one consolidated question batch, and RF-08 -> RF-09 -> RF-10 -> RF-06 ordering.
- Helpful editable default question and optional guided context were accepted in the phase-2 batch.
  Exact 120/500 limits were left for technical/content finalisation.
- Plain text, no categories/tags/social connection, English product copy, immutable publication,
  transient preparation and shared faithful preview are inherited requirements, not new questions.
- 2026-09-23: The owner answered `1A 2A`. Clearing the default leaves the question empty and requires
  correction before preview/publication. Shared preview/voter detail shows the question and full
  optional context above the photos. These cross-ticket rules are recorded in DEC-027.
- 2026-09-23: Routine details in the settled contract were reviewed under the owner's delegation.
  No new material question arose.
- 2026-09-23: The owner explicitly approved finalisation and requested notification when the plan
  was ready. The English plan is now `Ready for implementation`; this does not authorize harness
  launch. The plan makes the delegated Unicode normalization, configuration fields, component
  contracts and validation gates concrete without expanding product scope.

## Approved scope

### In scope

- Reusable controlled text fields and shared plain-text presentation for RF-06 and voter detail.
- Matching normalization/validation in TypeScript and Python, effective configurable text limits,
  safe field errors, accessible counters and documented integration contracts.
- Tests of the delivered units/components/config API and a consuming-ticket validation checklist.

### Out of scope

- RF-06's complete composer/navigation, photo lifetime changes, RF-09 links/authorization services,
  RF-10's persistence/publication, RF-14 feed implementation and actual voting/results/history.
- Saved drafts, rich text, automatic linkification, translation, categories, tags, social accounts,
  text suggestions from AI, content moderation services, new infrastructure or native packaging.

## Validation outline

- Matching frontend/backend fixtures for default, empty/whitespace question, optional null/empty
  context, exact bounds and overflow, normalization, accented/decomposed text, emoji, RTL, line
  endings, control characters, malformed Unicode and non-string payloads.
- Config API authentication, positive/incompatible settings, effective overrides, strict client
  guards, missing/malformed values and retry behavior; retain photo contract regression coverage.
- Controlled-field preservation, counters, blur/submit errors, overflow without truncation, IME,
  question-clearing choice, context-display choice, absent context and escaped markup/URLs.
- Keyboard, accessible labels/error association/focus, screen-reader announcements, narrow/zoomed
  layout and safe wrapping. Use a development/test mount without adding a temporary product route.
- RF-06 integration must prove edit -> preview -> edit fidelity, live uploader preservation,
  discard/session loss and text preservation on retry. RF-10 must prove server-side rejection and
  atomic immutable persistence; RF-09 must prove text cannot bypass consultation authorization.
- Real iPhone/TestFlight keyboard, text selection, zoom/safe-area and integrated composer checks
  remain explicit future device gates, alongside RF-07's existing manual gates.
- Implementation will run backend pytest/Ruff/mypy and frontend test/format/lint/typecheck/build,
  with config smoke appropriate to the additive API change. No migrations or image cleanup reruns
  are needed solely for this documentation-only grooming. No tests were claimed as run here.

## Readiness checklist

- [x] Desired outcome is unambiguous.
- [x] Existing scope boundaries and exclusions were identified.
- [x] Code impact and RF-07 integration contracts were inspected.
- [x] Dependencies and historical-document conflicts were identified.
- [x] Routine technical approach is selected and documented under the owner's delegation.
- [x] Material UX choices Q1/Q2 are confirmed.
- [x] Security/privacy/data/API/operations implications have a documented approach.
- [x] Automated and manual validation requirements are outlined.
- [x] No material question remains.
- [x] Product owner explicitly approved plan finalisation.
