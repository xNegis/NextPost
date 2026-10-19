# RF-26 - Compartir una consulta e invitar a votar - Grooming

## Status

`Completed and validated`

Selected by the product owner on 2026-10-19. This file records the read-only Trello intake,
repository inspection and confirmed material decision batch. The owner selected
`1A 2A 3A 4A 5A 6A 7A 8B` on 2026-10-19. The owner subsequently approved plan finalisation and
autonomous harness execution. The implementation and independent technical review are complete,
and the product owner explicitly reported `VALIDADO` after the private-LAN mobile review on
2026-10-19.

## Trello snapshot

- Title: `RF-26 · Compartir una consulta e invitar a votar`
- URL: https://trello.com/c/47FD3mrW/28-rf-26-compartir-una-consulta-e-invitar-a-votar
- Short URL: https://trello.com/c/47FD3mrW
- Board: `APP - NextPost`
- Board ID: `ari:cloud:trello::board/workspace/6aa9032829f8b45ead46cfdd/6aa903892e7d7b54f23fae1b`
- Card ID: `ari:cloud:trello::card/workspace/6aa9032829f8b45ead46cfdd/6aa90c02d29e80b551172ace`
- List: `Próximo · completar el MVP`
- List ID: `ari:cloud:trello::list/workspace/6aa9032829f8b45ead46cfdd/6aa903892e7d7b54f23fae23`
- Labels: None; no omitted labels reported.
- Members: None
- Checklists: None; no omitted checklists reported.
- Comments: None; no omitted comments reported.
- Attachments: None
- Custom field values: None
- Start date / due date: None / None
- Archived: False
- Card completion / due completion: False / False
- Position: `81920`
- Captured on: `2026-10-19T14:34:51.8761378+02:00`; read-only connector intake.
- Last Trello activity at intake: `2026-10-12T11:26:45.219Z`
- Available activity: card created on `2026-09-15T09:12:34.578Z`; moved from
  `Funcionalidades` to the then-named `Fase 2` list on `2026-09-22T14:33:38.522Z`.
- Intake consistency: RF identifier, title, configured board, current list and card content agree.
  No Trello mutation was performed.

### Description and acceptance criteria at intake

**Reorganización del backlog · 2026-10-12**

El recorrido de compartir permite que las personas invitadas lleguen a una consulta y vuelvan a
ella tras registrarse/iniciar sesión. Invitación privada a los primeros participantes no implica
construir un sistema de códigos, lista cerrada o acceso por invitación; ese mecanismo no ha sido
solicitado.

Ubicación: Próximo · completar el MVP. El repositorio es la fuente de estado y especificaciones
aceptadas. Esta organización no aprueba un plan ni lanza implementación.

---

**Descripción conservada del ticket**

**Historia de usuario**

Como autor, quiero compartir un enlace a mi consulta para invitar a personas a votar.

**Criterios de fase 2 acordados**

- Puedo copiar el enlace y usar el menú de compartir del dispositivo si está disponible; copiar
  sigue funcionando si no lo está.
- Tanto Público como Privado requieren una cuenta registrada para ver fotos y votar. Privado es no
  listado: cualquier cuenta registrada con un enlace reenviado puede acceder.
- Quien deba iniciar sesión o registrarse vuelve al destino original. La previsualización externa
  es genérica y no expone fotos.
- Un enlace revocado, reemplazado, finalizado, eliminado o retirado deja de dar acceso.

**Aplazado:** contactos del dispositivo y publicación automática en redes. Referencia:
DEC-011/022.

## Intended outcome

An author can share an address for an open Public or Private consultation. A recipient who opens
that address sees no protected consultation data until a registered account is authenticated. The
same-tab sign-in or registration journey preserves the validated consultation destination and then
opens the real reader comparison, where the account may vote under RF-16's current rules.

Public addresses contain no capability. Private addresses carry the current fragment capability
and remain forwardable: any registered account with the still-current link may use it. Current
account, audience, consultation lifecycle, link generation and vote eligibility are rechecked on
the server. Sharing creates no invitee record, permanent access grant or closed recipient list.

## Accepted constraints inherited by RF-26

- Registration alone is sufficient account eligibility; email verification is not required
  (DEC-011).
- Public and Private photographs require an authenticated account. Private is unlisted and requires
  the current link for a non-owner; forwarding the link is allowed (DEC-022).
- Published content and audience are immutable; open consultations do not expire automatically
  (DEC-017/018).
- A Private link is issued automatically, is stable until an explicit transition, and is checked on
  every actual protected request. There is no polling or remote recall of already-loaded bytes
  (DEC-029).
- Invalid, revoked, replaced, finalized, deleted, removed and unknown destinations collapse to the
  same authenticated unavailable result; network/server failure stays retryable (DEC-028).
- Ordinary platform URL opening is sufficient. RF-26 must not promise universal/app-link opening or
  add bespoke native-link infrastructure (DEC-030).
- Public remains discoverable; its stable address is not independently revocable while the
  consultation remains open. Private disable/replace/create-new does not erase votes, release the
  open-consultation slot, finalize or delete photos (RF-09/RF-10).
- Votes are immutable and author self-voting is forbidden. A current Private link is accepted by
  the real detail, media, own-vote and vote endpoints (RF-16/DEC-038).
- Product copy is English (DEC-009). Web and invited iOS TestFlight remain the phase-2 delivery
  targets, with real-device evidence required where the environment exists (DEC-014).
- The product owner owns visual validation; automated accessibility/layout tests remain required
  (DEC-034).

## Current code findings

### Frontend shell and authentication

- `frontend/src/App.tsx` is still the sole application-state coordinator. It has local authenticated
  destinations (`home`, `create`, `my`, `profile`) and auth phases, but it never reads
  `window.location.pathname` or browser history. `checkSession` and `enterAuthenticated` both force
  `home`; `returnToSignIn` also discards every product destination. This is the direct gap for
  post-authentication return.
- `SignInForm.tsx` and `RegistrationForm.tsx` report the new account through callbacks. They do not
  know or accept redirect URLs, which is useful: App can retain one parsed internal destination
  without allowing the forms or server to accept an arbitrary return target.
- Authentication uses a signed `HttpOnly`, `SameSite=Lax` cookie. No server-side session row,
  OAuth callback or redirect endpoint exists. RF-26 should preserve this mechanism rather than
  introduce native tokens or a redirect database.
- The current nginx configuration already falls back to `index.html`, so a direct
  `/consultations/{uuid}` web request can load the SPA. The React app does not yet consume that
  path, handle `popstate`, or keep route/history state synchronized.

### Existing link and access contract

- `frontend/src/consultationLink.ts` already strictly builds and parses only same-origin
  `/consultations/{uuid}` destinations, with a single optional `#access=v1...` fragment. It rejects
  query strings, duplicate/unknown fragment fields, malformed UUIDs/tokens, arbitrary origins and
  public non-HTTPS origins. Localhost and private/link-local IP HTTP origins are allowed for device
  review. Private tokens are sent only in `X-NextPost-Private-Link` on credentialed fetches.
- The fragment never reaches the HTTP server. It is currently neither copied into browser storage
  nor connected to App routing. Keeping the original URL in the address bar lets a reload reparse
  it without persisting the bearer capability elsewhere.
- `backend/app/consultation_access.py` centralizes current account/audience/lifecycle/link decisions.
  `backend/app/api/consultations.py` and `consultation_service.py` enforce it on real open detail,
  photo, own-vote and vote requests. Private direct-ID reads without the current token are denied.
- Consultation IDs are UUIDs and Private capabilities are versioned HMAC-SHA-256 values derived
  under a server-only key. The database stores only generation/active state, not raw tokens.
- Protected consultation API paths use credentialed requests, generic unavailable errors and
  private/no-store, nosniff and no-referrer response policy. External static HTML contains no
  consultation question, nickname, photo or result metadata.

### Author share controls

- RF-10 persists one stable Private link and implements owner-only read, disable, replace and
  create-new operations with generation preconditions and a database row lock. RF-12 exposes those
  real controls from publication success and returning owner detail.
- `PrivateLinkControls.tsx` shows the complete Private URL and provides `Copy link`, Disable,
  Replace and Create new. Copy currently uses only `navigator.clipboard.writeText`; failure asks the
  author to copy manually. It provides no positive copied feedback and no device Share action.
- `OwnerConsultationDetail.tsx` creates Private URLs from `window.location.origin`, catches an
  invalid deployment origin so detail cannot crash, and still displays the truthful limitation
  `Opening shared links is not available yet.` Public owner detail has no copy/share address at all.
- No component calls `navigator.share` or `navigator.canShare`. There is no automatic posting,
  contact access, invite code or recipient list.

### Recipient detail, voting and navigation

- `ReaderConsultationDetail.tsx` and its controller already load protected full text and all ordered
  photo blobs with an optional Private token. RF-16 adds vote-status recovery and immutable vote
  submission using the same token. It distinguishes generic unavailable from retryable failure and
  cleans object URLs on denial, supersession and unmount.
- The real reader exists only after a Public Home card is selected. `HomeFeed.tsx` stores that
  selection in component memory and always labels the return action `Back to Home`; it cannot open
  an addressable Private item or restore a direct Public route.
- Owner detail is a separate server-authorized projection. The general direct-detail response does
  not currently say whether the authenticated account is the author. RF-26 must decide what an
  author opening their own shared URL sees; it must never present an author with a usable vote flow.
- Home, My consultations and reader detail all deliberately keep in-memory pagination/selection.
  RF-26 needs only an addressable consultation-entry boundary; it need not convert every primary
  destination into persistent routes or promise restoration of feed scroll/pages.

### Lifecycle and unavailable states

- Persisted consultation states are `open`, `finalized`, `deleted` and `removed`. Existing protected
  detail/media/vote authorization is strict-open. Finalized author summaries are separate and do not
  grant photo access.
- Real finalization, author deletion, administrator removal and published-photo purge are still
  owned by RF-19/RF-20, RF-13, the restricted RF-32 subset and RF-37. RF-26 can test seeded terminal
  denial but cannot claim those mutations or deletion side effects are implemented.
- Link disable/replace is real now. An already-open recipient may keep rendered photos until a new
  request; refresh, reopening, photo/vote request or any later protected read reauthorizes against
  current database state.

### Worktree and validation context

- The worktree contains substantial tracked and untracked RF-14/RF-16/RF-18 and real-device
  correction work. It belongs to the current repository baseline and must be preserved.
- RF-12, RF-14, RF-16 and RF-18 approved increments are completed and validated at the current
  checkpoint, although RF-14 retains explicitly accepted technical debt. RF-09/RF-06/RF-07/RF-11
  retain their recorded integration, visual or device gates.
- Real iPhone evidence exists for photo selection/publication, Private owner detail and Home scroll,
  but not yet for `navigator.share`, external consultation entry, cookie restoration from a shared
  URL or post-authentication destination return.

## Dependencies and conflicts

- RF-01/RF-02 supply automatic registration/sign-in and cookie restoration. RF-03/RF-06/RF-12 own
  the current local authenticated shell and dirty-composer navigation guards.
- RF-09 supplies strict same-origin fragment links, current-link lifecycle and access policy;
  RF-10 supplies real persisted Public/Private detail, media and owner link endpoints.
- RF-14 supplies Public discovery/reader presentation; RF-16 supplies current Private-capable voting.
  RF-26 should route to these real components rather than duplicate their data loading or vote rules.
- RF-11 defines strict-open external access. RF-13/RF-19/RF-20/restricted RF-32/RF-37 must later
  perform real terminal writes and physical deletion; RF-26 owns their generic consumer denial only.
- The approved RF-06/RF-12 plans explicitly excluded a router and assigned recipient routing/auth
  return to RF-26. Adding a narrow addressable consultation route is therefore expected, but a full
  application-wide routing rewrite would exceed the identified need and risk current composer guards.
- A Private token in the fragment is a bearer capability plus account requirement. Putting it in a
  query, API path, server redirect, log, analytics field, cookie, `localStorage` or `sessionStorage`
  would conflict with RF-09's approved security contract.
- Contacts, invitation codes, allowlists, closed lists, messaging, automatic social-network posting,
  analytics/tracking and per-recipient grants are excluded. An operating-system share sheet may list
  installed apps, but NextPost does not read the contact book or post without the user's explicit
  choice in that system UI.

## Candidate approach

The product owner confirmed the approach below through choices `1A 2A 3A 4A 5A 6A 7A 8B` on
2026-10-19 and later explicitly approved plan finalisation and autonomous harness execution.

### Narrow URL-entry state machine

Confirmed direction: keep App as the shell and add one explicit consultation route boundary using
the existing strict parser plus the browser History API. On startup, parse the current same-origin
URL before deciding the post-session destination. Retain only the parsed UUID/token in memory while
the auth forms are mounted; keep the original path/fragment in the address bar so refresh can reparse
it. After registration, sign-in or valid session restoration, open the direct consultation instead
of forcing Home. Ordinary `/` authentication continues to land on Home.

Do not accept a `returnTo` query/body/cookie or arbitrary URL. Do not send the fragment to the auth
API. Clear protected reader data immediately on session loss/account change, but retain the original
link URL so another registered account may authenticate and use the same still-current forwarded
Private link. Explicit navigation away replaces/pushes a safe internal URL and drops the in-memory
token with the unmounted view. Add `popstate` handling and preserve the current dirty-composer guard;
do not promise restoration of feed paging or composer drafts.

### Share action

Confirmed direction: every open owner detail, including immediate publication success, gets one
`Share consultation` section. Public uses `/consultations/{uuid}`; Private uses the current active
fragment link and retains its existing disable/replace/create controls. `Copy link` remains visible
on all supported devices. Show `Share` only when the Web Share API is callable; invoke it directly
from the user gesture. A user cancellation is neutral. A real share failure keeps the link and Copy
available with concise feedback. Clipboard failure keeps a selectable read-only URL/manual-copy
fallback. Success is announced accessibly without claiming the recipient opened or voted.

Use one generic share payload with a NextPost label and URL; do not include the author's nickname,
question, context, audience, photos, results or token anywhere except the Private URL itself. Do not
fetch contacts or choose an external application. Runtime capability detection, not user-agent
sniffing, decides whether the device share control appears.

### Recipient entry

Confirmed direction: an anonymous structurally valid consultation route shows a generic
consultation-entry auth context with Sign in and Create account, but no request for protected detail
and no consultation-derived metadata. Once authenticated, load the real route. A registered
non-owner gets the existing reader/vote view. An owner gets the existing owner detail rather than a
self-vote error; this likely requires a small server-derived viewer-role projection or an explicit
owner-read resolution, never trusting client memory or the shared URL.

Authenticated invalid/currently unauthorized/terminal targets use the existing generic unavailable
view. Syntax-invalid consultation paths can use the same generic unavailable presentation without a
server lookup. Network/5xx or missing authorized photo bytes remain retryable and are not described
as revocation. Leaving direct detail goes to Home through an explicit action; browser Back follows
the actual history when available.

### Origin and external preview

Continue to construct only a validated same-origin URL, always using `window.location.origin` as
selected in Q8B. This preserves the current simple behavior and makes localhost/private-LAN device
review links match the address the author is actually using. The strict existing origin validator
continues to reject credentials, paths, queries, fragments and non-HTTPS public hosts. Deployment
must therefore ensure the browser-visible production origin is the intended public origin; a proxy
or host misconfiguration can otherwise become user-visible in copied links. The shipped static
document and metadata remain generic NextPost content; no anonymous consultation-specific
OpenGraph/SEO preview is added.

## Questions

### Confirmed decision batch (2026-10-19)

#### Q1 - Where is sharing offered, and who gets an in-product share control?

**Confirmed: A.** Sharing is an author control on every open Public or Private owner detail,
including publication success. RF-26 adds no recipient re-share control.

- **A (recommended):** show Copy and optional device Share to the author on every open Public or
  Private owner detail, including publication success and returning My consultations/Home owner
  detail. Recipients can still forward a URL outside NextPost, but get no additional in-product
  re-share button in this increment. This satisfies the author story, keeps one management surface
  and avoids implying recipient tracking or endorsement.
- **B:** also show an in-product Share action to registered recipients. This makes forwarding easier,
  especially for Private links, but expands the intended actor and normalizes uncontrolled
  redistribution more prominently; it still cannot be restricted to named invitees.
- **C:** sharing only immediately after publication. This is smaller but conflicts with recovery via
  My consultations and makes later re-sharing unnecessarily difficult.

#### Q2 - How should the device share menu and copy fallback be presented?

**Confirmed: A.** Copy remains visible; Share is capability-detected; manual selection remains the
fallback; cancellation is neutral and real failures retain Copy.

- **A (recommended):** Copy is always visible; Share appears only when `navigator.share` is callable.
  Clipboard failure leaves a selectable full URL and manual-copy instruction. Share cancellation is
  silent; a real failure shows feedback and preserves Copy. This directly matches the ticket and is
  resilient on browsers/WKWebView implementations without Web Share.
- **B:** one Share action that internally falls back to clipboard. This is visually smaller but hides
  what will happen and makes clipboard/share errors and accessibility feedback less clear.
- **C:** always show both and disable Share when unsupported. This advertises unavailable capability
  and adds noise without improving the fallback.

#### Q3 - What should the device share payload contain?

**Confirmed: A.** Use generic English NextPost invitation text plus the URL, with no protected or
user-generated consultation fields in the share text.

- **A (recommended):** a generic English label such as `Vote on a photo consultation in NextPost`
  plus the URL, identical for Public and Private. It helps the recipient without exposing question,
  context, nickname, audience or photos to the selected external app.
- **B:** URL only. This minimizes disclosed text but produces a less understandable message.
- **C:** include the consultation question/author. This is friendlier but exports protected/user-
  generated content beyond NextPost and conflicts with the generic-preview privacy posture.

#### Q4 - How much routing infrastructure should RF-26 introduce?

**Confirmed: A.** Add only the narrow consultation route/history boundary and preserve the current
local primary-navigation/composer model.

- **A (recommended):** add one narrow `/consultations/{uuid}` route state to the existing App using
  the strict parser and History API, including refresh and `popstate`, while keeping primary
  destinations/local composer state as they are. This is the smallest coherent change and limits
  regression risk to current dirty-navigation guards.
- **B:** adopt a client router and migrate all Home/Create/My/Profile/detail navigation now. This may
  be cleaner long term, but is a larger shell rewrite with more history, focus, dirty-form and test
  surface than RF-26 requires.
- **C:** keep everything in memory and use a query/callback after authentication. This fails direct
  reload/back behavior and would pressure the design toward an unsafe or persistent return target.

#### Q5 - What should an author see when opening their own shared URL?

**Confirmed: A.** Resolve viewer role on the server and show the existing neutral owner detail;
never offer the author a vote flow.

- **A (recommended):** resolve current viewer role on the server and show the existing neutral owner
  detail, including results/share management, with no vote controls. This is safe and useful, but
  needs a small trusted role/owner-resolution contract for the direct route.
- **B:** show the reader comparison with voting disabled and a link to My consultations. This keeps
  one direct-entry UI but duplicates an owner-only state and is less useful than the existing detail.
- **C:** show generic unavailable. This is simple but surprising: an author can manage the same open
  consultation elsewhere and the URL is otherwise valid.

#### Q6 - What generic experience should an unauthenticated valid link show?

**Confirmed: A.** Show a generic consultation authentication context with Sign in and Create
account, then resume the same validated destination after either succeeds.

- **A (recommended):** a generic `Sign in to view this consultation` entry context with both Sign in
  and Create account. It discloses no existence-sensitive content and clearly explains why auth is
  required; after either success, the same URL is resumed.
- **B:** reuse the ordinary generic NextPost sign-in screen without mentioning a consultation. This
  is slightly smaller but makes the return behavior less understandable.
- **C:** show a consultation-specific preview. This conflicts with the accepted generic external
  preview and would require deciding which protected fields may be anonymous.

#### Q7 - What should leaving a direct shared-link detail do?

**Confirmed: A.** Provide `Go to Home`; browser Back retains normal history behavior.

- **A (recommended):** provide `Go to Home`; browser Back keeps its normal history behavior. If the
  direct URL was the first entry, the explicit action is always usable. This avoids fabricating a
  feed position that never existed.
- **B:** label the action `Back to Home` and always replace the route with Home. Familiar wording, but
  “Back” is inaccurate for a person who arrived from WhatsApp/email and it ignores browser history.
- **C:** attempt to return to the external referring app/site. This is unreliable, may leak behavior
  across trust boundaries and is not required by ordinary platform link opening.

#### Q8 - Which origin should copied production links use?

**Confirmed: B.** Always use the strictly validated `window.location.origin`. This keeps
configuration simple and supports current LAN/device-review addresses. The accepted consequence is
that a wrong browser-visible production/proxy origin would be copied into shared links and must be
prevented through correct deployment configuration and validation evidence.

- **A (earlier recommendation, not selected):** require a configured canonical public application origin outside
  development; allow current validated localhost/private-LAN origin only in development/review.
  Links remain stable behind proxies and cannot accidentally publish an internal host, at the cost
  of one deployment setting and validation.
- **B (selected):** always use `window.location.origin`, as current Private controls do. This is simplest and
  useful for LAN review, but a misconfigured production/proxy origin becomes user-visible in every
  copied link.
- **C:** have the backend return full URLs. This centralizes origin but unnecessarily sends the
  fragment capability through a response URL constructor and couples web deployment details to the
  API; it is not recommended.

### Previously resolved constraints

- Public and Private both require a registered account before text/photos/voting; registration alone
  is sufficient. Private is forwardable and creates no recipient allowlist (DEC-011/022; reaffirmed
  by the product owner in the RF-26 request on 2026-10-19).
- The valid original destination must survive sign-in and registration and resume afterwards
  (phase-2 accepted sharing answer; reaffirmed on 2026-10-19).
- Copy and the device share menu when supported are required; Copy remains the fallback. Contacts and
  automatic social posting are not implied.
- Revoked, replaced and terminal links do not grant access; authenticated causes collapse to generic
  unavailable, with network/server failure distinct (DEC-028/029).
- Private link possession never bypasses account, current lifecycle, association or vote rules.
- Ordinary platform link opening remains sufficient; no custom universal/app-link promise
  (DEC-030).
- 2026-10-19: the complete material decision batch is `1A 2A 3A 4A 5A 6A 7A 8B`. DEC-040 records
  its durable cross-feature behavior.

## Proposed scope

### In scope

- Addressable same-origin Public and Private consultation entry using the existing strict UUID/
  fragment-token grammar.
- Safe same-tab preservation and resumption of that parsed destination through session restoration,
  sign-in, switching between sign-in/registration and successful registration.
- Generic unauthenticated link-entry context with no protected fetch/content/metadata.
- Real authenticated direct detail/photo/vote using current access checks, including current-link
  revocation/rotation and lifecycle denial.
- Server-resolved safe owner handling for an author opening their own shared address, using the
  existing neutral owner detail without vote controls.
- Author-only Copy for both audiences, manual-copy fallback and capability-detected Web Share with
  generic invitation text plus URL.
- Public stable URL and current Private fragment URL; existing Private disable/replace/create-new
  controls remain authoritative.
- Browser refresh/history/direct navigation through a narrow History API boundary,
  session-loss/account-switch cleanup, generic unavailable and retryable network/media states.
- Strictly validated `window.location.origin` link construction, including accepted localhost/LAN
  support and explicit production proxy/origin configuration risk.
- Generic external HTML/social preview with no consultation-derived content.
- Automated frontend/backend/integration tests and real iPhone/Safari or packaged-webview validation
  of sharing, cookie authentication and return when an appropriate environment is available.

### Out of scope

- Device contacts, invitation codes, per-recipient links/grants, invitee allowlists, closed lists,
  messaging, automatic social posting or NextPost-managed social-network integration.
- Anonymous question, nickname, photo or result previews; anonymous voting; email verification.
- Native universal links, custom URL schemes, automatic installed-app opening, an `Open app` banner,
  native project generation, signing, TestFlight distribution or Android packaging.
- Link expiry, password-protected links, audience changes, Public-link revocation, revocation polling,
  push/WebSocket invalidation or remote recall of loaded/downloaded images.
- Feed ranking/search, participant tracking, open/read receipts, analytics or notification delivery.
- Vote/result/finalization/deletion/removal/photo-purge implementation owned by other tickets. RF-26
  only consumes their current access result and cannot claim seeded terminal fixtures prove the real
  writer/deletion flows.
- A full rewrite of all primary navigation unless Q4B is explicitly selected.

## Privacy, security and error outline

- Parse only exact local consultation paths. Never accept arbitrary redirects or an origin from user
  input. UUID/token grammar is bounded before any protected request.
- Keep the Private capability in the URL fragment and transient component/App memory only. Never put
  it in query/path/body, server redirect parameters, logs, analytics, persistent storage or cookies.
- Authentication callbacks receive only the account summary; App chooses the previously parsed
  internal destination. Auth endpoints need no return URL parameter.
- Do not fetch detail/photo/vote status before authentication. All protected data is cleared and
  object URLs revoked on 401, account change, token/path change, denial, navigation and unmount.
- Current server authorization remains authoritative for detail, each photo, own-vote and vote.
  Client routing, earlier successful access, browser history and possession of a photo ID are never
  grants.
- Invalid/unknown/revoked/replaced/finalized/deleted/removed collapse to the same authenticated
  unavailable state. Do not expose which check failed. Network/5xx/storage failure remains Retry.
- Private link rotation/disable uses the existing owner-only trusted-origin mutation endpoints and
  generation preconditions; sharing itself is a local user-initiated browser/device action.
- Static HTML/OpenGraph metadata stays generic. Use `Referrer-Policy: no-referrer` on protected
  responses/pages and avoid external resources from the sensitive detail surface.
- Do not log or report raw URLs containing the fragment token. Tests and operational diagnostics use
  synthetic/redacted capability values.

## Validation outline

### Automated

- URL entry: Public and Private direct load, case/UUID/token grammar, extra query, duplicate/unknown/
  oversized fragment, foreign origin and unsupported route; no protected fetch while anonymous.
- Authentication return: initial authenticated restoration, sign-in success, registration success,
  switch sign-in/register/back, failed/retried auth, page refresh during auth and ordinary `/`
  auth continuing to Home. Prove no arbitrary redirect and no token in storage/auth requests.
- Routing: direct first entry, internal open, refresh, Back/Forward/popstate, explicit Go to Home,
  primary navigation and dirty/pending composer regression. Late old-route responses cannot restore
  content.
- Access matrix: Public/Private owner/other account, valid/missing/wrong/stale/disabled capability,
  forwarded current Private link used by a second account, author self-vote denial, existing vote
  recovery and current lifecycle states. Public errors stay non-enumerating.
- Resource cleanup: partial/all photo blobs, vote/detail races, route/token/account changes, 401,
  generic denial and unmount revoke all URLs and discard sensitive state.
- Sharing: Public/Private current URL, Copy success/failure/manual fallback, Share supported/
  unsupported, resolved/cancelled/rejected share promise, pending duplicate prevention, current link
  after replace/create and disabled-link no-share state. Assert generic payload contains no protected
  text and accessible status feedback.
- Backend regression: detail/media/vote/link current authorization, private headers, link rotation
  and strict no-token-in-response behavior remain green. No schema/migration is expected unless a
  later confirmed choice demonstrates a need.
- Existing auth, navigation, composer, My consultations, Home, reader vote and owner detail suites
  remain green; strict types, lint, formatting, build, dependency audit and Compose configuration
  pass.

### Built-stack and manual

- Isolated PostgreSQL/backend/frontend two-or-more-account smoke: author publishes Public and
  Private with real photos; recipient opens both from fresh unauthenticated tabs, signs in or creates
  an account and returns; forwarded Private link works for another registered account; direct ID/
  missing/old token fails; vote and vote recovery work; ordinary restart preserves valid links.
- Disable and replace a Private link. New requests through the old URL become generic unavailable;
  current URL works; already-loaded screen behavior matches DEC-029 without polling.
- Seed terminal states only to validate RF-26 consumer denial and state clearly that this is not
  evidence of real finalization/deletion/removal/photo purge.
- Product owner validates presentation under DEC-034. Technical automated checks cover keyboard,
  focus, announcements, 320px wrapping, 44px targets, safe-area/navigation clearance and long URLs.
- On a real iPhone, verify Safari link opening, sign-in and registration return, cookie continuity,
  current Private header/photo/vote flow, Share-sheet success/cancel/failure, Copy/manual fallback,
  background/foreground, refresh and safe-area behavior. If a TestFlight client exists, test its
  actual webview behavior separately without claiming universal-link handoff.

## Readiness checklist

- [x] Desired outcome is captured from Trello and accepted repository decisions.
- [x] Scope and exclusions are confirmed.
- [x] Code impact was inspected.
- [x] Dependencies and conflicts are identified.
- [x] Technical approach is selected.
- [x] UX and failure states are confirmed where applicable.
- [x] Security, privacy, retention, and abuse implications are resolved where applicable.
- [x] No data migration is currently indicated; current-origin behavior and its operational risk
      are confirmed.
- [x] Test and manual validation expectations are agreed.
- [x] No material question remains.
- [x] Product owner explicitly approved plan finalisation.

