# RF-06 - Prepare a consultation - Implementation Plan

## Status

`Ready for implementation`

## Source ticket

- Trello title: `RF-06 · Preparar una consulta`
- Trello URL: https://trello.com/c/kLphAXQ1/10-rf-06-preparar-una-consulta
- Trello list at intake: `Fase 2`
- Snapshot captured on: `2026-09-22T10:35:35+02:00`; current card wording rechecked read-only
  on 2026-09-22
- Grooming notes: `harness/grooming/RF-06-grooming.md`

## Objective

Give a registered author one polished, temporary flow for preparing, previewing and publishing a
real consultation. The author enters from primary navigation, selects and verifies photos, supplies
the question and optional context, explicitly selects Public or Private, reviews the exact content
and reach, and publishes once through RF-10's atomic contract.

Preparation exists only in the current app session. It is never exposed to other accounts and does
not become a recoverable draft. After publication, the author sees the persisted consultation and,
for Private consultations, the current private-link controls.

## Context and current behaviour

- `frontend/src/App.tsx` owns authentication and a local authenticated destination. It currently
  renders only Home or Profile. There is no router.
- `frontend/src/Navigation.tsx` exposes Home and Profile as accessible primary-navigation buttons.
- RF-07 provides real temporary upload sessions, configured photo limits, selection-order items,
  progress/error/retry/removal, private object URLs, lease renewal, discard, freeze and relinquish.
  `PhotoUploader` currently exposes only `discard`; its public boundary needs a small extension so
  the composer can inspect the ready photos/session, freeze editing and relinquish after success.
- RF-08 provides `ConsultationTextFields`, `ConsultationTextDisplay`, shared normalization and
  validation, the configured limits hook and the helpful default question. The untouched default
  question is valid but must not make the composer dirty.
- RF-09 provides `AudienceSelector`, strict audience values, protected consultation/link contracts,
  fragment-safe private links and `PrivateLinkControls`.
- RF-10 provides `PublishSummary`, `usePublishConsultation`, capacity, atomic/idempotent publication,
  protected detail/media reads, owner link operations and cleanup-safe photo promotion.
- Publication consumes an upload session. `relinquish()` must run before the successful composer
  unmounts so RF-07's unmount cleanup cannot request deletion of promoted media.
- Published question, context, audience and photo order are immutable. Consultations do not expire
  automatically. The configured baseline is 2–10 photos and at most three open consultations.
- The worktree contains the uncommitted RF-07 through RF-10 implementation. Preserve it. RF-06 must
  integrate these contracts rather than replace or duplicate them.

## Scope

### In scope

- Add `Create` as a third permanent authenticated primary-navigation destination.
- Add a polished three-step in-session wizard: Photos, Details, Review and publish.
- Keep photo uploads and all form values alive while moving backward and forward in the wizard.
- Preserve gallery-selection order; allow removal and reselection, with no reorder control.
- Reuse current server configuration, text/audience validation and photo readiness to gate progress
  and publication.
- Show a faithful author-only review with the actual ready images in publication order, normalized
  text, audience reach, immutability/no-expiry copy and one Publish action.
- Handle publication pending, definite failure and idempotent manual Retry without losing the form.
- Warn about dirty internal exits, Cancel, reload and app/browser close where the platform permits;
  discard the temporary session on a confirmed internal exit.
- Replace the wizard after success with a narrow persisted owner detail view loaded by consultation
  ID, including protected photos and current Private-link controls when applicable.
- Add focused component/integration tests, responsive/accessibility styling and documentation/state
  updates supported by validation evidence.

### Out of scope

- Recoverable drafts, autosave, reopening unfinished work, cross-device preparation or a draft list.
- Drag/drop or any other photo reordering control.
- A client router, addressable consultation routes, feed/search/profile discovery, shared-link entry,
  authentication return paths or native deep links; RF-26 owns the complete share journey.
- Voting, results, close/finalize, author deletion, administrator removal and participant feedback.
- Changing published content, automatic expiry, background retry/polling or a publication recovery
  screen.
- New consultation/upload/link endpoints, backend business rules, database tables, migrations,
  workers, queues, storage services, backup/versioning or native project generation.
- Full RF-37 published-photo lifecycle work beyond consuming its existing temporary cleanup rules.

## User experience

An authenticated user always sees Home, Create and Profile. Selecting Create first loads current
capacity/configuration. While those checks are pending, show an accessible loading state. A
retryable failure offers Retry. If the server says the author cannot start another consultation,
explain that they must close one before creating another and offer Back Home. Capacity is guidance,
not a reservation; the server remains authoritative at publication.

The composer is one mounted experience with an ordered progress indicator and these steps:

1. **Photos.** Explain the current minimum/maximum and briefly remind the author to share only
   photos they have permission to use. Use the existing picker, progress, processing, retry,
   enlarge and removal behaviour. Continue is enabled only when every selected item is ready and
   the ready count is within current limits.
2. **Details.** Show the RF-08 default question, optional context and Public/Private selector. No
   audience is initially selected. Validate with the shared normalization/limit functions. Continue
   focuses or identifies the first invalid field; Back returns to the live Photos step.
3. **Review and publish.** Freeze photo mutation and show the real ready images in fixed selection
   order, the normalized question/context, the selected reach, photo count and existing immutable/
   no-expiry explanation. This is the faithful preview and the only publication confirmation.
   `Back to edit` returns to Details and unfreezes photos. `Publish consultation` sends one frozen
   snapshot and becomes `Publishing…`; all navigation and duplicate submission are blocked while
   the request is pending.

An upload or field problem stays in the wizard with clear local feedback. A publication validation,
capacity, conflict or network failure stays on Review, preserves the exact snapshot and offers the
existing manual Retry. If the server reports an expired upload session, explain that the photos must
be selected again and return to a usable Photos state. An unauthenticated response clears private
local state and returns to Sign in.

The untouched default question alone is not dirty. The composer becomes dirty permanently for that
preparation after the user changes question/context, chooses or changes audience, or starts photo
selection. Back/forward between wizard steps is never treated as exit. Cancel or selecting Home/
Profile/Create while dirty opens one accessible confirmation with `Keep editing` and `Discard`.
Keep editing restores focus and state. Discard leaves immediately, clears local object URLs and
requests temporary-session deletion; server cleanup remains the fallback if that request fails.
With no dirty change, navigation leaves directly. Install a native `beforeunload` warning only while
dirty and unpublished. Reload/app close may lose the preparation and does not promise recovery.

On confirmed publication, relinquish the upload session, clear dirty state and load the persisted
detail by the returned consultation ID. The success view shows normalized question/context, actual
protected images in stored order and a clear published message. A Private consultation also loads
the owner's current link and wires Copy, Disable, Replace, Create new and Refresh through the
existing generation-aware operations; Public never requests or renders owner-link controls. Detail,
media or link failures show a retryable partial-page error without substituting temporary preview
data. `Back Home` leaves the success view. Starting Create again begins an empty preparation.

The layout must work at 320 px, normal desktop width, 200% zoom and iOS safe areas. Step names,
status/error announcements, form associations, focus movement, confirmation focus and keyboard
operation must remain accessible. All product copy is English.

## Functional requirements

### FR-1 - Permanent Create entry and capacity guidance

Add `create` to the authenticated destination model and render Home, Create and Profile consistently.
Entering a fresh Create destination checks current consultation capacity/configuration. It must not
create an upload session until photo selection starts and must not imply that capacity is reserved.

### FR-2 - One transient wizard state

The composer owns one in-memory state for step, text, audience, photo/upload state, dirty state,
validation and publication result. Step changes must not unmount the active uploader or lose object
URLs, upload progress, the upload session or entered fields. Reload starts over.

### FR-3 - Real ordered photo preparation

Use RF-07's effective limits and upload lifecycle. The review and publication payload use
`readyImageIds` and displayed images in the original gallery-selection order. Pending, processing,
failed, inactive-session, too-few and too-many states block progress/publication. RF-06 adds no
reordering or alternative persistence.

### FR-4 - Shared text and audience rules

Initialize from `initialConsultationText()`, validate/normalize with RF-08 and require an explicit
RF-09 Public or Private choice. Do not reproduce limits or normalization in the composer. Show
field-level feedback and the real reach of the selected audience.

### FR-5 - Faithful review and one confirmation

Review uses shared text display plus the actual selected image object URLs. It accurately states
photo count, reach, immutability and no expiry. The page's Publish action is the single confirmation;
do not add a second modal.

### FR-6 - Atomic publication handoff

Submit one immutable `PublishSnapshot` containing the active session ID, ordered ready image IDs,
normalized question/context and selected audience through `usePublishConsultation`. Prevent double
submission while pending. Retry the hook's retained snapshot so RF-10 idempotency can return the
same consultation after a lost response. Preserve the form on definite failure.

### FR-7 - Safe upload-session ownership transfer

Freeze mutation for Review/pending publication. On success, call RF-07 relinquish before removing
the composer, then clear dirty state. Never call discard/remove for the consumed session or promoted
photos. On confirmed pre-publication discard, use RF-07 discard and leave without waiting for the
network cleanup response.

### FR-8 - Dirty exit behaviour

Dirty state follows the product definition above and is latched for the current preparation.
Intercept internal navigation and Cancel before changing destination. Use an accessible in-app
confirmation. Register `beforeunload` only while dirty and unpublished. Session loss clears state
without a discard prompt because the user can no longer act on the private session.

### FR-9 - Persisted success/detail and owner link

After success, refetch detail and each protected photo from RF-10 by the returned ID. Revoke all
created media object URLs when replaced or unmounted. For Private only, load the owner link and
perform generation-aware transitions; on stale generation or uncertain failure, preserve the last
known state and offer Refresh. Clipboard failure receives visible feedback and must not expose the
token through logs or query strings.

### FR-10 - Authentication, errors and usable state

Every API uses the signed cookie and existing strict response guards. Any 401 returns to Sign in and
clears private client state. Loading, retry, validation, upload, publication, detail/media and link
failures must be explicit. Never show another consultation's data, a substituted image or a fake
success state.

## Technical approach

Create a focused `ConsultationComposer` container that coordinates existing RF-07–RF-10 primitives
and reports exit/session-loss events to `App`. Keep `App` as the small destination owner rather than
introducing routing. Keep the uploader mounted across the wizard and toggle step visibility with
semantic/accessible markup.

Extend `PhotoUploader` minimally with a coherent snapshot callback or equivalent typed boundary for
`items`, `readyImageIds`, `sessionId`, effective config, readiness and inactive state, plus imperative
`discard`, `relinquish` and `setFrozen` operations. Do not duplicate `usePhotoUploader`. The exact
prop names may follow local style, but the composer must receive one internally consistent snapshot
and must perform relinquish before successful unmount.

Add a narrow success/detail container that owns protected-media object URLs and Private-link state
while reusing `ConsultationTextDisplay` and `PrivateLinkControls`. It is a local post-publication
destination inside Create, not a general consultation route or voter detail page.

### Affected areas

- Frontend: `frontend/src/App.tsx`, `Navigation.tsx`, `PhotoUploader.tsx`, their tests,
  `frontend/src/styles.css`; new focused composer, review-photo and published-success components and
  tests; existing RF-07–RF-10 hooks/APIs are consumed and changed only where their integration
  boundary is insufficient.
- Backend/application: no intended production change. Existing capacity, publication, detail,
  media and owner-link routes remain authoritative.
- Domain/data model: no change.
- Storage/background work: no change; consume existing discard, lease, promotion and cleanup rules.
- Configuration/deployment: no new setting, service, secret, package or volume.
- Documentation: update README only if the integrated user flow/validation commands need it, and
  update project state from evidence.

### Data and migration requirements

RF-06 persists no draft or wizard state and adds no database column, table or Alembic revision.
Published persistence is entirely RF-10. Temporary objects stay under RF-07/RF-37 cleanup; promoted
objects stay under RF-10. No data backfill, migration rollback or compatibility deployment is
required.

If implementation appears to require a schema change, stop and report a plan conflict instead of
inventing one. Do not modify or downgrade the existing RF-10 migration as part of this ticket.

### API and integration requirements

Consume the existing contracts:

- application configuration and temporary upload session/image/lease/discard operations from
  `photoApi.ts` through `usePhotoUploader`;
- `GET /api/consultation-capacity` before a fresh preparation;
- `POST /api/consultations` through `usePublishConsultation` with the active session and frozen
  ordered snapshot;
- `GET /api/consultations/{id}` and each
  `GET /api/consultations/{id}/photos/{photo_id}/content` for persisted success;
- `GET /api/consultations/{id}/private-link` and the existing create/disable/replace mutations for
  a Private owner's link.

Do not add endpoint aliases or combine detail and token responses. Do not send a Private token in a
query string. Treat all JSON and blobs as untrusted; retain the existing runtime guards. Capacity is
advisory. Publication conflict/cap responses and link-generation conflicts must leave a retryable,
truthful UI. The backend remains responsible for atomicity, idempotency, ownership, concurrency and
request-time authorization.

### Security and privacy

- Render all user text as text; do not use raw HTML.
- Keep temporary and published images behind the existing authenticated APIs and object URLs. Revoke
  object URLs on removal, discard, replacement, session loss and unmount.
- Do not persist preparation, IDs, text, audience or private tokens in local/session storage, URLs,
  logs or analytics.
- Never render a Private token for Public consultations or expose it to non-owner detail consumers.
- Preserve cookie credentials, same-origin mutation protection, safe error messages and exact
  server authorization. Client hiding is not authorization.
- Navigation and publication races must not delete promoted photos or leave the user believing an
  uncertain request definitely failed. Use the existing frozen snapshot/idempotent retry boundary.
- Discard is best effort at exit; the existing server lease and cleanup remain the safety net.

## Implementation sequence

1. Extend authenticated navigation and App destination handling with Create, including a guarded
   navigation request path that can be intercepted by the composer.
2. Add the composer state machine, capacity/config loading and accessible three-step shell without
   introducing a router.
3. Extend the uploader integration boundary and mount the real Photos step; prove state/session/
   object URLs survive wizard movement and that discard/relinquish are distinct.
4. Integrate RF-08 text, RF-09 audience and shared validation into Details; implement the accepted
   dirty-state definition and focusable validation feedback.
5. Build the actual-photo Review step, freeze/back behaviour and single RF-10 publication action.
6. Implement pending/error/manual Retry/session-expiry/session-loss paths and the exact successful
   relinquish ordering.
7. Add the persisted success/detail/media view and Private owner-link controller with object-URL and
   generation-conflict cleanup.
8. Add internal-exit/Cancel confirmation and conditional `beforeunload`; cover Home/Profile/Create
   navigation and clean/dirty/pending/success cases.
9. Finish responsive, safe-area, zoom, keyboard, focus and live-region styling without adding a new
   visual framework.
10. Run focused and full repository validation plus a built-stack two-account smoke. Record evidence
    and keep the real-iPhone/TestFlight gate explicit if that environment is unavailable.

## Validation strategy

### Automated tests

- Navigation renders Home/Create/Profile, applies `aria-current` correctly and reports Create.
- Capacity loading, retry, cannot-start and fresh-start paths; entering Create does not create an
  upload session before selection.
- Wizard step order, progress semantics, button gating and mounted state preservation backward and
  forward.
- Photo selection order, real preview images, remove/reselect, progress/error/retry, count limits,
  inactive session and no reorder control.
- Default question is clean; text edits, audience selection and photo-selection start latch dirty.
- Shared text normalization/limits, explicit audience and first-error focus; no duplicated constants.
- Review fidelity, freeze/unfreeze, one confirmation, pending double-click protection and immutable/
  no-expiry/reach copy.
- Publication sends the exact ordered frozen snapshot. Validation/network/cap/conflict errors retain
  state; manual Retry reuses it; session loss clears it.
- Success calls relinquish before unmount and never discards consumed media. Pre-publication discard
  calls discard and navigation continues even if cleanup fails.
- Clean navigation, dirty Keep editing/Discard, Cancel, Home/Profile/Create and conditional
  `beforeunload`; no prompt after success/session loss.
- Persisted detail/media load and ordering, object-URL revocation, retryable unavailable media and no
  preview-data substitution.
- Private owner link load/copy/disable/replace/create/refresh and stale-generation behaviour; Public
  makes no owner-link request.
- Existing account, profile, upload, text, audience, access, link and publication suites remain green.

### Manual validation

- At 320 px, desktop and 200% zoom, complete Photos -> Details -> Review, move backward/forward,
  enlarge/remove/retry a photo, verify focus/order/status announcements and publish once.
- Exercise dirty Home/Profile/Cancel exits with Keep editing and Discard; verify refresh/close gets
  the platform-native best-effort warning and reopening starts clean.
- Full isolated Compose flow with two accounts and real normalized images: publish Public and
  Private, verify persisted image order/detail, no preparation exposure, wrong-account/media denial,
  Private link copy/disable/replace/create and old-link rejection.
- Simulate lost-response Retry and last-slot capacity race; exactly one durable consultation exists
  for one upload session and the UI remains usable.
- Restart the ordinary stack and verify the success detail/photos/link still load; run cleanup and
  confirm promoted files survive while discarded temporary files remain eligible.
- On a real invited iPhone/TestFlight build, verify gallery selection including an ordinary HEIC/
  HEIF photo, upload progress, safe areas, wizard navigation, dirty-close limits, publication,
  persisted detail and sharing/copy affordance. If signing/TestFlight is unavailable, record this as
  an unresolved external validation gate rather than claiming it passed.

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

Use an isolated test PostgreSQL database and disposable smoke volumes. Do not run downgrades or
cleanup experiments against the user's active data. Use `docker compose up --build -d` for the
built-stack smoke and `docker compose exec backend python -m app.cleanup` for cleanup status.

## Acceptance criteria

- [ ] A registered author has a permanent Create navigation destination and can start only when
      current configuration/capacity is available; no upload session is created just by visiting.
- [ ] One polished Photos -> Details -> Review/publish wizard preserves live uploads and form values
      across steps and uses English, accessible, responsive UI.
- [ ] The author selects 2–10 configured photos through the real picker, sees progress/retry/remove/
      enlarge states and keeps gallery-selection order without a reorder control.
- [ ] The helpful default question, optional context and explicit Public/Private choice use shared
      validation/configuration and show the actual audience reach.
- [ ] Review displays the actual ready photos, normalized text and reach faithfully, freezes mutation
      and provides exactly one Publish action with immutable/no-expiry guidance.
- [ ] Publication submits one ordered frozen RF-10 snapshot; pending blocks duplicates, definite
      failure preserves the wizard and manual Retry remains idempotent.
- [ ] Success relinquishes the consumed upload session before unmount, never deletes promoted media
      and loads persisted detail/photos by consultation ID.
- [ ] Private success shows current generation-aware link controls; Public does not request or reveal
      a link. Link/media/detail failures remain safe and retryable.
- [ ] The accepted dirty definition drives internal confirmation and conditional native unload
      warning; confirmed discard leaves immediately with server cleanup as fallback.
- [ ] Reload/app close does not promise recovery, session loss clears private state and no preparation
      appears in another account, discovery surface or persistent client storage.
- [ ] RF-06 adds no backend rule, endpoint, schema migration, worker, router, draft library, feed,
      voting/result/finalization/deletion flow or fake future control.
- [ ] Focused/full automated checks and isolated built-stack two-account validation pass. Real-iPhone/
      TestFlight evidence is recorded honestly and remains a named gate if unavailable.

## Dependencies and ordering

- Read AGENTS.md, all source-of-truth context, RF-06 grooming and the complete approved RF-07,
  RF-08, RF-09 and RF-10 plans before editing.
- RF-01/RF-02 authentication and RF-03 authenticated navigation are implemented foundations.
- RF-07 supplies temporary photo/session/cleanup behaviour; RF-08 supplies text/configuration;
  RF-09 supplies audience/access/link primitives; RF-10 supplies atomic publication, persisted reads
  and link state. Their current uncommitted implementation is part of the integration baseline.
- RF-26 later owns addressable sharing/authentication return. RF-12/RF-18 own author lists/results;
  RF-14/RF-16 voting consumes published detail; RF-19/RF-20/full RF-37 own terminal lifecycle.
- A restricted administrator removal path remains required before real-user exposure but is not an
  RF-06 implementation task.

## Risks and mitigations

- Uploader unmount discards a published session: keep it mounted through the wizard and relinquish
  synchronously before switching to success; test call ordering.
- Preview differs from publication: derive preview and payload from one normalized frozen snapshot
  and the same ordered ready items.
- Navigation bypasses cleanup/warning: route all authenticated destination changes and Cancel through
  one App/composer guard; add `beforeunload` only for dirty state.
- Capacity changes during preparation: present capacity as guidance and preserve the form on the
  authoritative publication rejection.
- Retry publishes twice: retain exactly the original snapshot and depend on RF-10 session
  idempotency; disable the action while pending.
- Private token/media leak: use existing protected APIs, fragment links and object URLs; never store,
  log or query-string private data.
- Object-URL memory/privacy leak: centralize ownership and revoke on every replacement/exit path.
- Overbuilding the POC: keep state in memory, use local destinations and reuse current components;
  add no routing, draft persistence, worker, polling or new backend abstraction.
- Mobile behaviour claimed without evidence: keep the real-iPhone/TestFlight validation gate explicit.

## Harness handoff notes

- This is an integration over a dirty worktree containing RF-07 through RF-10. Preserve all existing
  changes and inspect their exact current contracts before editing.
- Prefer small typed components and one explicit composer state machine. Do not refactor unrelated
  authentication/profile/backend code or replace the existing styling system.
- The `PhotoUploader` boundary may be extended, but RF-07 upload ownership, automatic unmount
  cleanup and `relinquish` semantics must remain intact for other consumers/tests.
- Do not weaken server authorization or use temporary preview data as persisted success fallback.
- Do not commit, push, deploy, mutate Trello, generate native projects, use the coordinator runbook
  or launch another agent. The external harness implements; Codex coordinates and reviews.
- Record exact automated, Compose and manual evidence. Do not mark the physical-iPhone gate passed
  without a signed real-device run.

## Resolved grooming decisions

- `Create` is a third permanent primary-navigation item.
- The composer is a polished three-step Photos, Details, Review and publish wizard.
- Photos retain gallery-selection order; the POC has no reordering control.
- The untouched default question is clean. Text/audience changes or starting photo selection make
  the preparation dirty. Internal exits confirm; refresh/app close uses best-effort native warning.
- Temporary preparation is deliberately non-recoverable. Session loss clears it.
- Publication uses the preview's single action and RF-10's idempotent contract; no second dialog.
- Success is a narrow persisted owner detail view, with current link controls for Private. It is not
  a router, feed, voter view or RF-26 share journey.
- RF-06 is a frontend integration with no schema migration or new backend persistence.
- The product owner explicitly approved plan finalisation on 2026-09-28. Harness launch remains a
  separate explicit action.

## Remaining questions

None
