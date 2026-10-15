# RF-09 - Elegir audiencia y controlar el enlace - Grooming

## Status

`Ready for implementation`

Selected by the product owner on 2026-09-28. The owner requested read-only intake, repository
research, and all material questions together in one consolidated batch. The subsequent owner
answers below settle automatic issuance, request-time revocation checks without polling, generic
unavailability, default platform link behavior and the existing ticket order. The owner explicitly
requested plan drafting on 2026-09-28 after these decisions. The reviewed, self-contained contract
is `harness/features/RF-09-Implementation-plan.md`, marked `Ready for implementation`. Harness launch
is a separate request.

## Trello snapshot

- Title: `RF-09 · Elegir audiencia y controlar el enlace`
- URL: https://trello.com/c/vt8seQzA/12-rf-09-elegir-audiencia-y-controlar-el-enlace
- Board: `APP - NextPost`, https://trello.com/b/CgBkRg78/app-nextpost
- Board ID: `6aa903892e7d7b54f23fae1b` (matches configured board)
- Card ID: `6aa90be35fbd8151071c8c86`
- List: `Fase 2`, ID `6aa903892e7d7b54f23fae23`
- Labels: None; no omitted labels reported.
- Members: None
- Checklists: None; no omitted checklists reported.
- Comments: None; no omitted comments reported.
- Start / due date: None / None
- Archived: False
- Card completion / due completion: False / False
- Position: `140737488519168`
- Captured on: 2026-09-28, read-only intake completed before `2026-09-28T08:01:14Z`
  (local coordinator checkpoint; connector does not supply a read timestamp).
- Last Trello activity at intake: `2026-09-22T14:34:54.699Z`

### Description and acceptance criteria at intake

**Historia de usuario**
Como autor, quiero decidir cómo pueden encontrar mi consulta.

**Criterios de fase 2 acordados**
- Antes de publicar elijo Público o Privado con una explicación clara.
- Público aparece en el feed y lo puede ver cualquier cuenta registrada. Privado no aparece en el feed: requiere cuenta registrada y disponer del enlace; un enlace reenviado sirve a otra cuenta registrada.
- Ninguna de las dos audiencias permite ver fotos sin iniciar sesión. El enlace no evita las reglas de acceso, estado o retirada.
- El autor puede revocar o regenerar el enlace privado. La audiencia publicada queda fija; para cambiarla crea otra consulta.
- Finalizar, eliminar o retirar una consulta corta también el acceso por enlaces antiguos.

Referencia: DEC-011/017/018/021/022.

Identifier, title, board, list and content agree. The card does not specify initial link issuance,
the detailed revoke-without-replacement state, already-open-screen behavior or native link opening.
No Trello mutation was performed.

## Intended outcome

An author deliberately chooses the discoverability of an immutable published consultation. Every
reader must satisfy the same account, audience, link and lifecycle rules for text and photographs.
Private links can be withdrawn or replaced without silently changing the audience or the votes.

## Current code findings

- Read the seven context files, RF-06/07/08 and phase-2 grooming, and RF-03/07/08 approved plans.
  RF-03 remains in progress, RF-07 in review, and RF-08 completed according to current project state.
  Historical intake statements about absent uploads or a wholly untracked tree are superseded.
- `backend/app/models.py` contains Account, PhotoUploadSession and PhotoUploadImage only. There is
  no Consultation, audience field, link token/version, participant grant, vote or published-image
  relationship. Alembic ends at `20260922_0003_photo_uploads.py`.
- `backend/app/auth.py::get_current_account` resolves a live account from the signed account cookie.
  `backend/app/main.py` registers account, health and photo routes; cookie configuration is HttpOnly
  session middleware with SameSite=lax and HTTPS outside development. There is no consultation
  access service or explicit link-management/CSRF boundary yet.
- `backend/app/api/photos.py` serves temporary content only after owner/session checks, with
  `Cache-Control: private, no-store` and `X-Content-Type-Options: nosniff`. This must not be widened
  to grant voters access to temporary uploads.
- `backend/app/photo_service.py::validate_publication_images` locks the session and validates
  ordered, ready, owned images and actual byte presence. It does not publish. Session states are
  active/discarded/abandoned; there is no promoted state. RF-10 must coordinate photo promotion and
  cleanup before any consultation-based read is real.
- `frontend/src/App.tsx` uses local Home/Profile state and explicitly resets Home after sign-in,
  registration and session restoration. The accepted shared-link return journey will require an
  explicit exception for a validated pending consultation destination. Ordinary entry stays Home.
  This extends RF-03's feature-local contract; it must be explicit in the consuming approved plan.
- `frontend/package.json` has React and Capacitor, but no router or native link-handling package.
  `frontend/nginx.conf` already falls back to index.html; it does not implement client routing,
  private-link handling or referrer protection by itself.
- RF-08 supplies controlled text fields, shared inert text rendering and matching server validation.
  Text authorization must follow the same consultation access check as images; there must be no
  anonymous text-preview endpoint.
- RF-07's uploader owns its lease, private blobs and discard-on-unmount behavior. RF-09 must not
  change this into a public-media path. Composer/session promotion integration remains RF-06/RF-10.
- Existing uncommitted RF-08 implementation and documentation changes are present. Preserve them.
  This intake changes only grooming/project-state documentation; no test suite was rerun.

## Dependencies and conflicts

The following cards were read in full as dependencies on 2026-09-28, not separately consumed:

| Ticket | Current contract relevant to RF-09 | Last activity |
| --- | --- | --- |
| [RF-10 Publish](https://trello.com/c/gMQwBaFB/4-rf-10-publicar-una-consulta) | Atomic retry-safe publication, explicit fixed audience, processed photos, author destination and sharing entry. | 2026-09-22T14:34:57.786Z |
| [RF-12 My consultations](https://trello.com/c/L2mZ6OFf/14-rf-12-gestionar-mis-consultas) | Owner access to open/finalized consultations and management actions; private items excluded from others' feeds. | 2026-09-22T14:35:03.249Z |
| [RF-26 Share](https://trello.com/c/47FD3mrW/28-rf-26-compartir-una-consulta-e-invitar-a-votar) | Copy, optional device share menu, authenticated destination return, generic external previews and invalid old links. | 2026-09-22T14:36:07.670Z |
| [RF-37 Protect/delete](https://trello.com/c/Dodf7k4R/40-rf-37-proteger-y-borrar-fotograf%C3%ADas) | Per-read account/audience/state checks, immediate revocation, durable deletion, no re-exposure after restore. | 2026-09-22T14:36:38.547Z |

All four are open/uncompleted in Fase 2 on the configured board, with no labels, members, dates,
checklists or comments returned, and no omitted labels/checklists/comments reported.

- RF-06 consumes the selector and explanations; RF-08 supplies protected text. RF-10 owns consultation
  persistence, first publication, photo promotion and idempotency. RF-09 defines the access/link
  contract consumed by those endpoints and RF-16 voting. RF-14 must filter Private items on the
  server, not merely hide them in the browser.
- RF-11/13/19/20 and restricted administrator removal must make terminal states override any link.
  RF-21 private non-image outcomes are not a right to reopen photographs.
- Revocation/regeneration and safe post-authentication return were already accepted in the phase-2
  batch (answer 11). Public/Private, no preset audience, fixed published content, registered-only
  viewing and generic external previews must not be asked again as unsettled product questions.
- There is no RF-10 implementation plan. Claiming complete real published access in a standalone
  RF-09 increment would require moving substantial RF-10 scope. Q6 makes this delivery trade-off
  explicit. Maintain RF-09 -> RF-10 -> RF-06 grooming order unless the owner changes it.
- Native app identity/signing remain previously deferred delivery inputs. Q5 asks only about the
  desired external-link experience, not for credentials or a repetition of those setup decisions.

## Candidate approach

Confirmed behavior is identified below and in DEC-028/029/030. Remaining engineering proposals
require technical review before plan finalisation, without another questionnaire for routine
implementation choices. The approved plan must make the protocol and consumer responsibilities exact.

### Access and link lifecycle

- Use an explicit Public/Private enum and controlled required selector with neither selected.
  Explain registered-only Public discovery and forwardable, unlisted Private access in English.
  Reject missing/invalid audience on both client and server; never infer it from a URL.
- Confirmed: one current Private link is generated automatically at publication, ready to copy, with
  no independent expiry. Owner-only actions revoke or replace it after a clear confirmation.
  Copying again must return the current link, not silently rotate it.
- Owner reads/management use ownership, independent of possession of the shared token while the
  consultation is open. Non-owners need the current token for every Private access. Merely knowing
  a consultation/image ID, being signed in, having visited before or having voted is insufficient.
  No permanent account-access grants, invitee lists or per-recipient revocation are proposed.
- Revocation disables all current link-based reads/votes but is not finalization, deletion or a
  pause in the configured open-consultation cap. Regeneration atomically invalidates the previous
  link. Old links are never re-enabled. Keep prior confirmed votes; receiving a new link never grants
  a second vote. Finalization/removal/deletion override both links and the owner's image access.
- Public sharing uses a stable destination without a private access capability. Disabling a Public
  URL would not hide an item still accessible in the feed; no Public-link revoke control is proposed.

### Implementation boundaries and failure behavior

- Centralize authorization over current account, owner, audience, current link version and lifecycle.
  Apply it to text, detail, every image and voting; keep owner results separately authorized.
  Future read/vote/rotation/finalization transactions must have a defined ordering under races.
- Use cryptographically random opaque link secrets with versioned active/revoked state, no identifying
  text or email in URLs, and no secret in request logs, analytics, referrers or public metadata.
  Select an explicit at-rest strategy supporting owner re-copy after reload in the final plan;
  hash-only storage alone cannot reproduce the current link. A version-bound keyed derivation is a
  candidate; this must use a dedicated key and document key rotation, not repurpose the session key.
- Prefer an HTTPS application destination carrying the private capability in a fragment, with the
  client forwarding it in a protected request header rather than query/path logs. Validate this
  choice against ordinary platform link handling before finalisation; Q5 requires no custom native
  app-opening flow. Do not persist secret/content
  in localStorage or introduce permanent per-account grants. Same-tab reload/auth return must retain
  the validated destination without accepting arbitrary external redirects.
- Authenticated failures use a non-enumerating unavailable response; unauthenticated visitors see
  generic sign-in/registration and no consultation content. Network/server failures have Retry and
  must not be presented as definitive withdrawal. Clear inaccessible text and blob URLs on denial.
- Owner link controls belong in the eventual owner consultation detail, with current-link or
  link-disabled state, pending feedback, confirmation for destructive replacement/revocation,
  Copy and later device-share integration. No separate navigation destination is needed.
- Mutations require the verified owner, protected same-origin/CSRF handling consistent with signed
  cookies, and no GET side effects. Version/precondition checks prevent an old tab overwriting a
  newer link. Duplicate/lost-response retries must not create uncontrolled successive rotations;
  reconcile current server state before showing success or exposing a link as current.
- Use private/no-store responses and no offline photo cache. Confirmed Q2/Q3: read current database
  authorization when the link is opened and on subsequent protected server requests. Do not add
  polling, scheduled access checks or push revocation. Already-loaded photos may stay on an idle
  open screen after revocation; this is not permission for new image reads or votes. Clear denied
  content when a real request reports unavailability. No claim of remote recall is made.
- Preserve the confirmed RF-09 -> RF-10 -> RF-06 order. Propose persisting link state with consultation
  rows in the RF-10 migration; RF-09's first
  increment must not create a parallel partial Consultation model or a disconnected token database.
  Reusable functions/components can be tested before persistence exists. Production endpoint,
  transaction and real-file access proof must remain explicit integrated completion gates.
- Database restore must not reactivate revoked tokens. Full backup/restore policy belongs to RF-37;
  a candidate operational safeguard invalidates private link capabilities on restore before serving
  traffic, requiring authors to obtain fresh links. This is a technical proposal for plan review,
  not a silently accepted retention or recovery policy.

## Questions

### Consolidated product-owner batch (2026-09-28)

Historical questions and options are preserved below. The latest owner response recorded after the
clarification supersedes earlier recommendations and statements that the answers are unconfirmed.

1. **Initial Private link (Q1).** A (recommended): publish with one automatically generated current
   link; re-copy the same link until replacement/revocation, with no scheduled expiry. B: publish
   without a link and require the author to explicitly create the first one. Both keep at most one
   active link; multiple per-recipient links are not proposed. A makes Private publication immediately
   shareable; B adds a step while initially leaving the consultation owner-only.
2. **Revocation package (Q2).** Confirm the recommended behavior: revoking leaves the consultation
   open for its owner, retains all previously confirmed votes, counts toward the three-open cap,
   and allows creation of a fresh link later. Previous visitors/voters have no continuing photo or
   voting access through the revoked link. Replacement does not reset votes or enable a second vote.
   No old link is reactivated and no photo deletion is triggered solely by link revocation. The owner
   can confirm the package or specify which part should change; changes to accepted vote/lifecycle
   rules must be recorded explicitly rather than inferred from a link-management action.
3. **Already-open recipient screen (Q3).** New server reads/votes are denied immediately after
   revocation in either option. A (recommended): also check access every 30 seconds while the screen
   is visible and connected, and on return/action; clear content after denial and hide it when access
   cannot be revalidated. This adds small periodic traffic. B: recheck only on navigation, return to
   the screen and interactions; simpler, but an idle visible screen can keep showing already-loaded
   photos until its next check. Neither recalls screenshots/downloaded bytes or guarantees background
   timer execution. A precise pending/error/visibility contract belongs in the plan after selection.
4. **Unavailable-link explanation (Q4).** A (recommended): authenticated recipients see one generic
   unavailable message for invalid, revoked, replaced, finalized, deleted or removed targets, with
   navigation back into the app. This avoids disclosing existence or why access was withdrawn.
   The owner's private management and authorized participant outcome history remain separate.
   B: distinguish at least finalized from invalid/revoked links, accepting extra existence disclosure
   and a more complex error contract. Neither option reveals protected photos/text or aggregate results.
5. **External links on iPhone (Q5).** A (recommended for the first delivery): shared links open the
   web experience in the browser, retaining the destination through sign-in/registration. TestFlight
   still supports its in-app flows. B: require external links to open the installed iOS app, falling
   back to web if unavailable, in the first delivery. B adds native link configuration and device
   tests to RF-09/RF-26's delivery dependencies; app identity/signing remain separately planned.
6. **RF-09 delivery boundary (Q6).** A (recommended, preserves the existing ticket order): first
   deliver reusable audience/access/link logic and controls, then wire real consultation persistence,
   authorization endpoints and photo reads through RF-10/RF-06 and share/auth-return through RF-26.
   Do not declare the full RF-09 card complete until these integrated gates pass. B: plan RF-09 and
   RF-10 as a combined implementation increment so actual published links are demonstrable together;
   this expands the implementation contract and requires RF-10 grooming before finalisation.
   Either choice retains approval and explicit harness-launch gates.

These are all material owner choices identified in this inspection. New contradictions discovered
from the answers must be documented; do not manufacture another serial questionnaire for routine
implementation choices. Answers do not themselves authorize plan finalisation or harness launch.

### First product-owner response and clarification (2026-09-28, historical)

- Q4A explicitly accepted: use the generic unavailable response; recorded in DEC-028.
- Q1 needs a concrete explanation: publishing a Private consultation can automatically make its
  shareable address ready, instead of asking the author to separately create that address. Automatic
  issuance remains the recommendation, not an accepted answer.
- Q2 needs the object explained: revoke means disable the shared Private URL, for example after a
  friend forwarded it beyond the intended group. It is distinct from ending/deleting the consultation.
  The current card and phase-2 answer 11 already include revocation/regeneration, but the owner has
  not confirmed the detailed package. Do not silently remove these accepted capabilities or interpret
  confusion as approval.
- Q3: in light of the proof-of-concept concern, revise the recommendation to B: no periodic polling;
  enforce current access on each server read/vote and recheck on return/interaction. An already-loaded
  idle screen can remain visible. The owner has not yet confirmed this revised recommendation.
- Q5 needs a concrete example: a recipient taps a NextPost link in WhatsApp on iPhone; should it
  open the website in Safari or the installed NextPost app? Browser opening remains recommended
  for the proof of concept, without withdrawing the accepted TestFlight delivery target.
- Q6 was unnecessarily presented as a technical organizational burden. Explain that audience/link
  work precedes publication integration; retain the already requested ticket order as the working
  direction, with exact implementation boundaries proposed for review. No combined scope, completion
  claim, implementation-plan finalisation or harness launch is approved by this response.

### Latest product-owner response (2026-09-28)

- Q1: explicitly accepts automatically creating the link, ready to copy and send.
- Q2/Q3: the owner described the link resolving to a database object whose current revoked/active
  state is checked on entry. Revoked links return an unavailable page. No timer or duplicated
  30-second check is wanted. The owner explicitly accepts that someone already viewing loaded photos
  may keep seeing them until leaving. Server checks still protect each new content request and vote;
  already-open UI is not a durable authorization grant. See DEC-029.
- Q4: generic unavailable message remains confirmed. The phrase "revoked page" describes denied
  access, not a request to replace DEC-028 with disclosure of the exact reason.
- Q5: do not build a special device-specific opening flow now. Use the ordinary behavior available
  in the platform/components actually used. This is neither a guaranteed Safari-only contract nor
  a requirement to implement automatic native-app opening or a new "Open app" button. No such native
  link integration was found in the current code. See DEC-030.
- Q6: explicitly maintain the existing order. Do not broaden into a combined RF-09/RF-10 ticket.
- The owner requested confirmation of this shared understanding at that point, not plan finalisation
  or a harness launch. In the next turn on 2026-09-28 the owner explicitly requested a plan for the
  harness. The technical protocol, future migration boundary and consumer contracts are now fixed
  in the approved implementation plan; launch remains a separate gate.
- Revocation is still a link-access operation, not consultation finalization/deletion or vote reset.
  Preserve accepted consultation/vote lifecycle rules; no change to those rules was requested.

### Resolved / inherited

- 2026-09-28: RF-09 selected; read-only intake and a single consolidated question batch requested.
- 2026-09-28: Q4A confirmed: generic unavailable-link response (DEC-028).
- 2026-09-28: Automatic link creation and database checks on actual access without polling confirmed
  (DEC-029); default platform opening behavior without custom native handling confirmed (DEC-030).
- 2026-09-28: RF-09 -> RF-10 -> RF-06 order reconfirmed.
- 2026-09-28: The owner explicitly requested plan drafting after all product questions were settled.
  RF-09's reusable implementation contract was finalized; this does not launch the harness.
- DEC-009/018/022/024: English copy, immutable published audience/content, Public registered access,
  Private registered-plus-link access, forwarding allowed, no preset audience.
- Phase-2 answer 11: copy/share, destination return through authentication, generic external previews,
  revocation/regeneration are accepted capabilities. Their exact protocol remains to be specified.
- DEC-017/021/023: no automatic consultation expiry, finalization removes images, only minimum
  private non-image outcomes survive. A link cannot override these lifecycle boundaries.
- DEC-020: no public profiles, user-facing block/report/moderation system or broad abuse infrastructure.
- DEC-014: web and invited iOS TestFlight delivery and real-device checks; packaging setup is deferred.

## Proposed scope

### In scope

- Required audience choice and accurate reach explanations shared by RF-06/RF-10.
- Central account/owner/audience/current-link/lifecycle authorization contract for all consumers.
- Single-current-link creation, retrieval, revocation/regeneration semantics and reusable owner controls.
- Safe destination/auth return, generic previews, recipient unavailable states and current-access checks
  as explicit integration contracts with RF-10/RF-26, with implementation split determined by Q6.
- Security/concurrency tests and real frontend/API/database/media integration gates.

### Out of scope

- Audience editing, anonymous viewing, permanent access grants, invitee allowlists, recipient tracking,
  multiple independent recipient links, automatic expiry, password-protected links, contact import.
- Implementing feeds, votes, outcomes, full owner lists, full image retention or native packaging in
  an RF-09 foundation increment. Those consumers must enforce this contract in their own plans.
- Sending invitations or messages, publishing to social networks, deploying, mutating Trello.

## Validation outline

- Access matrix: unauthenticated, owner, registered non-owner; Public/Private; valid/missing/wrong/
  revoked/old token; active/finalized/deleted/removed; guessed IDs and photo belonging to another item.
  Prove identical protection for question/context and every photo, not only the page shell.
- Rotation/revocation: owner-only, repeated/lost responses, stale tabs, concurrent operations and
  vote/read/finalization races. No previous visitor privilege or vote reset; no active replacement
  after terminal state. PostgreSQL locking tests required when persistence is implemented.
- Frontend: no preset audience, validation/focus, copy success/failure, confirmed/cancelled revoke,
  pending/conflict/network recovery, unavailable states, Q3 checks and clearing private blobs/text.
- Authentication/URLs: direct load, refresh, browser history, sign-in/registration return, expired
  session, rejected external redirect, account switch, generic previews and no secret in logs/referrers.
  Preserve ordinary Home entry and profile/session behavior; no anonymous content leaks.
- Full-stack tests must prove promoted photos survive composer cleanup but cannot bypass current
  consultation authorization. The temporary owner-only upload endpoints remain protected.
- Manual 320 px/200% zoom, keyboard/focus/confirmation and real-iPhone browser/TestFlight flow for
  the selected Q5 behavior. Record native/environment limitations as pending, never passed.
- RF-37 restore validation must prove old private links and withdrawn media do not become accessible.
- No implementation tests run during this documentation-only intake. Final plan will list exact
  existing pytest/Ruff/mypy and frontend test/lint/typecheck/build commands and proportional smoke gates.

## Readiness checklist

- [x] Current card consumed and preserved with metadata.
- [x] Existing code and relevant approved plans inspected.
- [x] Dependencies and differences from historical notes identified.
- [x] One consolidated question batch prepared.
- [x] All material product/UX/delivery answers confirmed.
- [x] Precise technical protocol and consumer implementation split settled in the approved plan.
- [x] Data, concurrency, security, failure and validation contracts ready for handoff.
- [x] No material question remains for this reusable increment.
- [x] Product owner explicitly approved plan finalisation on 2026-09-28.
