# RF-26 - Share a consultation and invite people to vote - Implementation Plan

## Status

`Ready for implementation`

The product owner confirmed the complete material decision batch
`1A 2A 3A 4A 5A 6A 7A 8B` and explicitly authorized plan finalisation and autonomous launch of the
external implementation harness on 2026-10-19. This plan is the approved implementation contract.
It does not authorize commits, pushes, deployment or Trello mutation. Product-owner visual review
remains a separate gate under DEC-034 and was explicitly excluded from this autonomous technical run.

## Source ticket

- Trello title: `RF-26 · Compartir una consulta e invitar a votar`
- Trello URL: https://trello.com/c/47FD3mrW/28-rf-26-compartir-una-consulta-e-invitar-a-votar
- Trello list at intake: `Próximo · completar el MVP`, configured `APP - NextPost` board
- Snapshot captured on: `2026-10-19T14:34:51.8761378+02:00`
- Last Trello activity at intake: `2026-10-12T11:26:45.219Z`
- Grooming notes: `harness/grooming/RF-26-grooming.md`

The card requires authors to copy a Public or Private consultation address and use the device share
menu when available. Both audiences require a registered account before text, photos or voting are
available. Private is unlisted and any registered account possessing a forwarded current link may
use it. A recipient who signs in or registers must return to the original consultation. External
previews are generic. Revoked, replaced, finalized, deleted and removed destinations stop granting
access. Contacts, invitation codes, allowlists, messaging and automatic social posting are excluded.

## Objective

Complete the real author-to-recipient sharing journey over the already implemented publication,
access and voting contracts. An author can share any open Public or Private consultation from every
owner-detail context. A recipient can open the address directly, authenticate or create an account
without losing the validated destination, view the current authorized comparison and vote. The
journey remains safe under refresh, Back/Forward, account/session changes, Private-link rotation,
terminal lifecycle denial and retryable failures.

Introduce only one narrow addressable consultation-entry route. Keep the current local primary
destinations and composer navigation rather than rewriting the whole shell. Treat the URL as an
entry destination, never as a permanent account grant or arbitrary redirect.

## Context and current behaviour

- The shared client is React/TypeScript/Vite with Capacitor dependencies. `frontend/src/App.tsx`
  owns auth phases and local `home`, `create`, `my`, `profile` destinations. It currently forces
  Home after session restoration, sign-in and registration, never parses location/history and has
  no direct consultation route.
- `frontend/nginx.conf` already serves `index.html` for unknown paths, so a web request for
  `/consultations/{uuid}` can bootstrap the SPA. The client must now interpret that path.
- `frontend/src/consultationLink.ts` strictly builds/parses same-origin
  `/consultations/{uuid}` and optional `#access=v1...`, rejects query strings, malformed/duplicate
  fragment data, arbitrary origins and non-HTTPS public origins, and provides the protected token
  header. Private/local IPv4/IPv6 HTTP origins are deliberately accepted for development/device
  review. Do not weaken this grammar.
- RF-09/RF-10 implement canonical Public/Private access, versioned HMAC Private capabilities,
  persisted current-link generation/active state, protected detail/media and owner link mutations.
  Tokens live in fragments/client headers, not API paths or the database.
- RF-12 provides real neutral owner detail and current Private Copy/Disable/Replace/Create-new
  controls. `PrivateLinkControls` uses clipboard Copy only; Public has no share controls and the UI
  still says shared-link opening is unavailable.
- RF-14 provides the Public Home reader presentation. RF-16 provides current-token-aware vote-status
  recovery and immutable voting. `ReaderConsultationDetail` already accepts an optional Private token
  but is reachable only through an in-memory Home selection.
- General protected detail does not identify the current viewer as owner versus reader. A direct
  entry must resolve that role on the server so an author never receives a self-vote flow.
- Auth uses a signed `HttpOnly`, `SameSite=Lax` cookie. Sign-in and registration callbacks return
  only the account summary. There is no server session row, OAuth callback or safe reason to send an
  arbitrary return URL to the backend.
- Persisted lifecycle is `open`, `finalized`, `deleted`, `removed`; external reads/votes are
  strict-open. Real terminal writers and photo purge remain RF-13/RF-19/RF-20/restricted RF-32/RF-37
  work. RF-26 consumes generic denial and does not implement those operations.
- The worktree is substantially dirty with accepted RF-14/RF-16/RF-18 and real-device corrections.
  Preserve every unrelated tracked and untracked change. Historical absence statements in older
  plans do not describe current code.

Binding decisions include DEC-008/009/011/014/017–024/028–030/033/034/036–040 and the complete
approved RF-09/RF-10/RF-12/RF-14/RF-16 plans.

## Scope

### In scope

- One strict addressable `/consultations/{uuid}` client entry with an optional current Private
  fragment token, refresh-safe parsing and browser History API Back/Forward behavior.
- Generic unauthenticated consultation context with Sign in and Create account, without protected
  consultation requests or metadata.
- Safe same-tab destination preservation through session restoration, sign-in, switching between
  sign-in/registration and successful registration; ordinary `/` authentication still lands Home.
- Authenticated server-side direct-entry role resolution, returning only owner/reader and no
  protected content. Owner opens existing neutral owner detail; reader opens existing real
  reader/photo/vote flow with the current token.
- `Go to Home` from direct detail; normal browser Back remains normal. Primary navigation remains
  available and safely exits the direct route.
- Author-only sharing on every open Public/Private owner detail context, including publication
  success, returning My consultations and own Home detail.
- Copy always available, positive/failure feedback, selectable read-only full URL/manual fallback,
  and capability-detected Web Share with duplicate prevention, silent user cancellation and safe
  error handling.
- Generic share payload: `NextPost`, `Vote on a photo consultation in NextPost`, and current URL.
  No question, context, nickname, audience, photo or result in the share text.
- Public stable address and current active Private fragment address. Disabled Private link cannot
  be copied/shared until Create new succeeds. Replacement immediately changes the shareable address.
- Current `window.location.origin` as the link origin, passed through the existing strict validator.
- Generic invalid/revoked/replaced/terminal unavailable behavior; retryable network/server/storage
  behavior; all protected resource cleanup on route/token/account/session change.
- Automated functional, security, accessibility, history and integration tests; built-stack
  multi-account validation where the local environment permits it.

### Out of scope

- Recipient-side in-product re-share controls. A recipient can still forward the address externally;
  no technical claim is made that Private links cannot be forwarded.
- Contacts, address-book access, invite codes, per-recipient links/grants, allowlists, closed lists,
  messaging, notifications, automatic social posting or social-network integration.
- Anonymous consultation question, nickname, audience, photo, result or vote preview; anonymous
  voting; email verification.
- Native universal links, custom URL schemes, automatic installed-app opening, `Open app` banners,
  native project generation/signing, TestFlight distribution or Android packaging.
- Migrating Home/Create/My/Profile to a router, persistent feed scroll/pages, saved drafts or a
  general navigation framework.
- Query/path/body token transport, server redirect targets, cookie or browser-storage token
  persistence, link expiry/passwords, Public-link revocation, periodic revocation polling,
  WebSocket/push invalidation or remote recall of downloaded bytes.
- Vote/result/finalization/deletion/removal/photo-purge implementation, analytics, open/read receipts,
  recipient tracking, moderation UI or deployment.
- Browser screenshot, viewport or subjective visual inspection. The product owner explicitly retains
  this validation under DEC-034.

## User experience

### Author sharing

Every open owner detail displays one `Share consultation` section. This includes publication success,
returning My consultations and own Home detail. Public builds
`{window.location.origin}/consultations/{uuid}`. Private uses the existing current token and builds
the fragment address. All construction uses `buildConsultationUrl`; an invalid current origin leaves
detail/results usable and shows a safe share-unavailable error rather than crashing the page.

Show the full URL in a labelled, wrapping or horizontally usable read-only/selectable control.
`Copy link` is always present while an address is available. On success, announce `Link copied.`;
on clipboard absence/rejection, preserve the selectable URL and say `Could not copy the link. Select
and copy it manually.` Do not claim delivery or recipient activity.

Show `Share` only if `navigator.share` is callable and, when `navigator.canShare` exists, accepts the
exact payload. Invoke Share synchronously from the user gesture, disable duplicate activation while
its promise is pending, and use `{title: "NextPost", text: "Vote on a photo consultation in
NextPost", url}`. `AbortError` means the person cancelled and produces no error/success claim.
Other rejection shows a concise error while Copy remains usable. Share success announces only that
the share sheet completed; it does not claim the recipient received, opened or voted.

Private Disable/Replace confirmations and generation reconciliation remain unchanged. Disabled
Private state shows no Copy/Share URL. Create new restores sharing only after the authoritative
response. Replace makes the old URL stop working on the next protected request and updates the
displayed current address. Remove `Opening shared links is not available yet.` only when the real
recipient flow is wired and technically validated.

### Direct unauthenticated entry

On initial boot parse the exact current URL before selecting an auth/product destination. A valid
consultation path presents the existing auth card with generic contextual copy such as
`Sign in to view this consultation.` and the ordinary Sign in/Create account actions. Do not fetch
direct-entry role, detail, photos or vote status before authentication. Do not reveal whether the
UUID/token is current, Private/Public or exists.

Switching Sign in -> Create account -> Back retains the parsed internal destination because the URL
remains unchanged. Failed auth retains it. Successful sign-in/registration and valid session
restoration resume it. Refresh during the auth screen reparses the same address. An ordinary root
entry continues to use the current auth copy and goes Home after authentication.

A syntactically invalid consultation route shows the same generic unavailable presentation without
a protected server read and offers Go to Home/sign-in as appropriate. Other unsupported paths do not
become redirects or aliases.

### Authenticated direct entry

After authentication call a small protected direct-entry resolver with the consultation UUID and
optional Private header. It reads current database state and RF-09 authorization and returns exactly
`{role: "owner"}` or `{role: "reader"}`. It returns no question, nickname, audience, photo, vote,
token, owner ID or result. Unknown, revoked, replaced and terminal targets return the existing
generic consultation-unavailable response. 401 returns to the contextual sign-in state while
retaining the original URL; network/5xx remains retryable.

Owner renders `OwnerConsultationDetail` with a new neutral direct-entry context, current results and
share/link controls but no vote. Reader renders `ReaderConsultationDetail` with the parsed token and
the real immutable vote flow. Do not trust a client-supplied role or infer ownership from a URL.

The direct action label is `Go to Home`. It pushes/replaces the safe root application location and
clears the transient token/direct state before rendering Home. Browser Back/Forward uses actual
history via `popstate`; it reparses the new location and invalidates all old async requests/blob URLs.
Clicking any primary destination safely leaves the direct route and writes a root location without
bypassing the existing dirty-composer navigation contract. Do not fabricate a Home feed return
position for an external entrant.

### Failures, session and lifecycle

- Loading, generic unavailable and retryable error are distinct. Retry repeats current role/detail
  reads only; it never rotates a link or resubmits a vote automatically.
- Any 401 clears rendered protected data and blob URLs, enters contextual Sign in and keeps only the
  URL-derived destination. A different account may authenticate and use a still-current forwarded
  Private link under normal access/vote rules.
- Invalid/unknown/revoked/replaced/finalized/deleted/removed collapse to
  `This consultation is unavailable.` after authentication. No cause or existence detail leaks.
- Missing authorized photo bytes/network/5xx says the consultation could not be loaded and offers
  Retry; it is not described as revoked/deleted.
- No polling. Already rendered photos may remain while idle after a separate revocation, but Refresh,
  a new media/vote request, navigation return or reopening checks current state and clears on denial.
- Late resolver/detail/photo/vote responses from an old path, token, account, request generation or
  unmounted component must not restore protected content.

## Functional requirements

### FR-1 - Strict route classification

Classify the browser location as root/local-primary state, valid consultation destination or
unsupported/malformed. Reuse `parseConsultationUrl` and its exact UUID/query/fragment/origin limits.
Do not add permissive decoding, query token support, trailing-path aliases or external return URLs.
Keep one validated `ConsultationDestination` in transient React state only. The address bar is the
reload source of truth; no localStorage/sessionStorage/cookie/server storage.

Synchronize direct-entry opens/exits and primary navigation with `history.pushState`/`replaceState`
and one `popstate` listener. Do not intercept external browser history or create loops. A pop to the
same route/token may retain or safely reload; a changed route/token invalidates current requests and
resources. Preserve current composer dirty/pending confirmation before any internal route change.

### FR-2 - Authentication return without an open redirect

Parse and retain only the local typed destination. Sign-in/registration APIs remain unchanged and
receive no return URL. Refactor App's successful-auth/session-restoration behavior: if the current
location contains a valid consultation destination, enter that direct route; otherwise Home.
Contextual auth-to-registration transitions preserve it. Explicit route exit clears it.

Session loss from direct protected APIs returns to contextual Sign in, not Home. No protected fetch
occurs until a verified account summary exists. Sign-out elsewhere retains its existing semantics;
do not silently broaden logout behavior or server sessions.

### FR-3 - Server-derived viewer role

Add an authenticated read-only route equivalent to
`GET /api/consultations/{consultation_id}/entry`. Accept the optional current Private capability only
through `X-NextPost-Private-Link`. Load the current Consultation, use the same RF-09 snapshot/token
verification and strict-open authorization as detail/media/vote, and derive role by comparing the
verified cookie account with persisted owner ID.

Successful response has exactly one field, `role`, with canonical `owner|reader`. It must not touch
photo storage or vote/result queries. Unknown/wrong/missing/stale/disabled token and every terminal
state return the same existing `consultation_unavailable`; unauthenticated is the existing 401.
Malformed UUID uses the safe validation envelope. Apply the same private no-store, nosniff and
no-referrer headers to success and error paths. This endpoint is navigation metadata, not an access
grant: subsequent detail, every photo, vote status and vote submission still reauthorize current
state independently.

### FR-4 - Reuse real owner and reader surfaces

Add a direct-entry variant to owner detail with neutral wording and `Go to Home`. It retains real
author results, photos and current share/link management. It performs owner-authorized reads; the
resolver response alone cannot authorize management.

Add configurable exit wording/handler to reader detail so Home-feed selection keeps `Back to Home`
and direct entry uses `Go to Home`. Direct Private passes the parsed token to detail/media/own-vote/
vote. Public passes null. Do not duplicate photo/vote state machines or create a fake direct-detail
implementation.

### FR-5 - Stable Public and current Private share addresses

For Public open owner detail, build a token-free URL. Public has no disable/replace/create controls
and remains accessible through feed/direct address while open. For Private, request the current
owner link only after real owner detail, then build its fragment address. Re-copy is stable until
the generation changes. Never show a raw token separately from the complete share URL.

Always pass `window.location.origin` to the existing strict builder (Q8B/DEC-040). Do not add a
canonical-origin configuration setting. Preserve current localhost/private-LAN HTTP acceptance and
production HTTPS enforcement. Document/test the accepted operational requirement that the
browser-visible production origin must be the intended public origin.

### FR-6 - Copy and Web Share state machine

Extract a focused reusable share controller/component rather than duplicating behavior in Public
and Private branches. Inputs are the already validated full address and disabled/unavailable state.
It owns only local copy/share pending and feedback state.

Clipboard Copy uses the maintained browser API and handles absence, synchronous throw and rejected
promise. The full address remains selectable for manual copying. Web Share capability is determined
at render/current environment without user-agent sniffing. Handle synchronous throw, resolved,
`AbortError` and other rejection. Prevent overlapping Share activations; Copy may remain available
unless platform behavior requires only the Share button's pending state. Clear stale feedback when
the address/generation/consultation changes or the component unmounts.

### FR-7 - Generic previews and privacy

The static application title/description and any OpenGraph metadata remain generic NextPost data.
No consultation-derived server rendering or anonymous lookup is introduced. Ensure the sensitive
client document/page uses a no-referrer policy through existing response headers and, where needed,
generic static meta/config without embedding a token. Do not load third-party resources from the
direct detail surface.

Never log raw `window.location.href`, fragment token, share payload URL, header, cookies, user text or
photo identifiers in new diagnostics. Test fixtures use synthetic tokens and assertions must avoid
printing real capabilities.

### FR-8 - Accessibility and responsive technical contract

Use English copy, semantic headings/labels/status/alerts, visible focus, keyboard-operable controls,
44px targets and long-URL wrapping/selection without horizontal page overflow. Announce copy/share
success or failure without relying on color. Hidden unsupported Share is not focusable. Pending
state is conveyed and prevents duplicate activation. Automated component/accessibility/layout
regressions are required; subjective browser/viewport inspection is reserved for the owner.

## Technical approach

Keep handlers thin and reuse the current access service. Add one read-only role resolver and one
small direct-route state machine at App level. Do not introduce a router dependency or persistence.
Generalize existing owner copy behavior into a share primitive, then compose it into Public owner
detail and the current Private link controls. Reuse the existing reader/owner data controllers.

### Affected areas

- Frontend shell/routing: `frontend/src/App.tsx`, focused route/history helper/hook and tests;
  possibly widen `Navigation.tsx` active state without changing its destinations.
- Frontend auth presentation: contextual surrounding copy/callback coordination; SignInForm and
  RegistrationForm API contracts remain unchanged unless a narrowly typed display prop is useful.
- Frontend link/share: `consultationLink.ts`, a new reusable share controller/component,
  `PrivateLinkControls.tsx`, `OwnerConsultationDetail.tsx`, related styles/tests.
- Frontend direct detail: reuse `ReaderConsultationDetail`, `useReaderConsultationDetail`,
  `useReaderVote`, owner detail and API clients; add strict role-response guard.
- Backend: `backend/app/api/consultations.py`, `consultation_service.py`, `schemas.py` and focused
  tests for the role resolver/current access. No model or migration expected.
- Static/deployment documentation: generic preview/referrer/origin behavior and README notes only;
  no new environment setting/service/volume.
- Project documentation: grooming/decisions/state and implementation-review evidence.

### Data and migration requirements

No schema change, data migration, backfill or downgrade is expected. Existing opaque consultation
UUID, immutable audience, lifecycle and Private generation/active fields are sufficient. Do not add
redirect, invite, share-event, recipient or token rows. If implementation appears to require product
persistence, stop and report the conflict instead of inventing it.

### API and integration requirements

Add the exact-role endpoint described in FR-3 using existing error envelopes and authentication.
Add a strict frontend client/runtime guard accepting only exact `{role:"owner"}` or
`{role:"reader"}`. Unknown/extra/malformed nominal-success payload is a retryable safe client error,
never a role guess. Token remains only in `X-NextPost-Private-Link`; requests use credentials.

Do not change existing detail/media/vote/link method semantics. Ensure route registration order
cannot collide with `/consultations/feed`, capacity, photos, vote or private-link routes. No GET has
side effects. CORS remains the existing explicit credentialed origin/header contract.

### Security and privacy

- Verified cookie account and persisted Consultation determine role; client role is presentation
  only. Owner management endpoints independently prove owner again.
- A Private capability plus authentication grants current unlisted access, not ownership, recipient
  identity or future access. Forwarding to another registered account remains valid while current.
- The client accepts no external redirect target. UUID/token parser bounds work before API calls.
- Fragment never enters HTTP request URLs or auth payloads. Do not persist it beyond address bar and
  transient React state.
- All direct protected operations reauthorize. Old successful resolver state cannot survive current
  link/lifecycle denial.
- Generic errors prevent enumeration. Static previews expose no consultation data. Current private
  response headers and blob fetches remain mandatory.
- Route/account/token changes synchronously clear sensitive state and invalidate late work; blob URLs
  are revoked on every partial/superseded/denied/unmount path.

## Implementation sequence

1. Add strict direct-entry role schema/service/GET endpoint with current access policy, private
   headers and full backend access/privacy tests.
2. Add strict frontend resolver client and focused route classification/history helpers around the
   existing consultation-link parser.
3. Refactor App authentication/session restoration to preserve a typed URL-derived destination,
   render generic contextual auth, resume safely and handle popstate/Go Home/primary navigation.
4. Add direct owner/reader composition reusing existing detail/photo/vote controllers and safe
   route-specific exit wording; cover request/resource invalidation.
5. Extract reusable author share controls with full selectable URL, Copy feedback/manual fallback
   and capability-detected Web Share state machine.
6. Integrate sharing into every open owner-detail context for Public and Private; preserve current
   link transitions and remove the obsolete not-available note only after direct entry works.
7. Add styles and automated keyboard/status/long-URL/320px-layout regression coverage without
   subjective visual inspection.
8. Run focused then full backend/frontend quality suites, dependency audit, Compose config/build and
   an isolated multi-account built-stack smoke where available. Record exact evidence and owner
   visual/real-device gates honestly.

## Validation strategy

### Automated tests

- Backend resolver: owner/readers, both audiences, forwarded current Private token, missing/wrong/
  stale/disabled/cross-consultation token, anonymous/invalid session, unknown ID and every lifecycle;
  exact role-only payload, no storage/vote/results access and private headers on success/errors.
- Parser/history: root, valid Public/Private, malformed UUID/token, query, duplicate/unknown/oversized
  fragment, foreign origin, unsupported path, direct refresh, push/replace/pop, Back/Forward and
  no navigation loop.
- Auth return: authenticated initial session, unauthenticated -> sign-in, registration, switch/back,
  failures/retry, refresh during auth, session loss and different account; root auth still Home; no
  protected pre-auth fetch and no destination/token in auth payload/storage.
- Direct composition: owner neutral detail/no vote, reader Public and Private flows, forwarded link,
  existing vote recovery, generic denial, retryable errors, Go Home and primary-nav exit. Late old
  resolver/detail/photo/vote results fail closed.
- Resources: all partial/complete blob URLs released on route/token/account/session changes, denial,
  retry, popstate and unmount.
- Share: all owner contexts, Public token-free URL, current Private URL, disabled/replaced/new link,
  strict current origin, invalid origin safe failure, Copy resolved/rejected/absent/manual fallback,
  Share absent/canShare false/resolved/AbortError/rejected/synchronous throw and duplicate prevention.
  Assert exact generic payload and no protected text.
- Accessibility/layout regression: labels, selectable address, status/alert semantics, focusability,
  pending disabled state, keyboard activation, long URL/320px no horizontal page overflow using
  component/style assertions rather than browser screenshots.
- Existing auth, navigation, composer, My consultations, Home, owner detail/results, consultation
  link/access, reader photo/vote and Private mutation suites remain green.

### Integration and manual validation

- Isolated built PostgreSQL/backend/frontend with at least author and two recipient accounts. Publish
  real Public/Private comparisons. From fresh unauthenticated tabs, sign in or register and resume;
  a second account uses a forwarded Private link; missing/old tokens fail; vote/recovery work; author
  self-entry resolves owner; restart preserves current addresses.
- Disable/replace/create a Private link and prove old/current URL behavior on new requests. Confirm
  no polling and no false recall claim for an already-loaded idle view.
- Seed terminal states only for RF-26 denial tests and report that this does not prove real terminal
  writers or photo deletion.
- Exercise Web Share through mocked automated contracts. Real iPhone Safari/WKWebView share-sheet,
  cookie return, background/foreground and safe-area behavior remain product-owner/manual device
  validation unless an appropriate connected environment is explicitly available.
- Do not perform browser screenshot, viewport, zoom or subjective UI inspection in this run. Report
  product-owner visual acceptance as pending under DEC-034.

### Commands

From repository root:

```powershell
.\.venv\Scripts\python -m pytest backend\tests
.\.venv\Scripts\python -m ruff check backend
.\.venv\Scripts\python -m ruff format --check backend
.\.venv\Scripts\python -m mypy backend\app
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

Use an isolated `TEST_DATABASE_URL`/Compose project and disposable volumes for PostgreSQL and built
multi-account smoke. Never run cleanup, downgrade or volume removal against active user data. No
Alembic operation is expected because RF-26 adds no migration.

## Acceptance criteria

- [ ] Every open Public/Private owner detail context offers a real share section; Public uses a
      token-free address and Private uses only the authoritative current active fragment address.
- [ ] Copy is always usable when an address exists, has accessible success/failure feedback and a
      selectable manual fallback; disabled Private has no shareable address.
- [ ] Device Share appears only when supported, sends the exact generic payload, prevents duplicates,
      treats cancellation neutrally and preserves Copy on failure.
- [ ] No recipient re-share UI, contacts, invites/allowlists, messaging or automatic social posting
      is introduced.
- [ ] A valid direct consultation address survives initial session restoration, sign-in,
      registration, switching auth views and refresh, then resumes without an arbitrary redirect or
      persistent capability storage.
- [ ] No protected role/detail/photo/vote request or consultation-derived preview occurs before
      authentication.
- [ ] Server-derived role sends authors to neutral owner detail with no vote and non-owners to the
      existing real reader/vote flow; every later protected request independently reauthorizes.
- [ ] A forwarded current Private link works for another registered eligible account. Direct UUID,
      missing/wrong/old/disabled capability and terminal state do not.
- [ ] Invalid/revoked/replaced/finalized/deleted/removed/unknown targets share one authenticated
      unavailable result; network/server/storage failures remain retryable.
- [ ] Direct detail offers Go to Home; normal browser Back/Forward works; primary navigation and
      dirty/pending composer behavior do not regress.
- [ ] Route/token/account/session changes and late requests cannot retain or restore protected data;
      every owned object URL is revoked correctly.
- [ ] Shared URLs use strictly validated `window.location.origin`; no new canonical-origin setting,
      permissive public HTTP, query token or server-generated full URL is added.
- [ ] Static/external preview data remains generic; no user content, photo, result, audience or raw
      capability is logged, persisted or exposed in metadata.
- [ ] No schema/migration, router dependency, native deep-link infrastructure, polling, worker,
      terminal operation or unrelated product feature is introduced.
- [ ] Focused and full automated quality checks plus isolated built multi-account smoke have exact
      evidence. Seeded terminal checks and mocked Web Share are not overstated as real terminal or
      iPhone evidence.
- [ ] Product-owner visual and real-device Share validation remain clearly pending; no autonomous
      browser visual inspection is performed.
- [ ] Documentation reports only evidence-supported implementation state; no commit, push,
      deployment or Trello mutation occurs.

## Dependencies and ordering

- RF-01/RF-02: registration, sign-in, cookie restoration and callbacks.
- RF-03/RF-06/RF-12: current shell, dirty composer guards, publication success, owner recovery and
  Private controls.
- RF-09/RF-10: strict URL/token/access/link lifecycle and real publication/detail/media endpoints.
- RF-11: lifecycle policy. RF-14: Public reader presentation. RF-16: immutable voting and recovery.
- RF-18: owner results reused by direct owner detail, never exposed to readers.
- RF-13/RF-19/RF-20/restricted RF-32/RF-37 retain real terminal writes and physical-photo deletion.
  RF-26 proves only their generic consumer denial contract with current/seeded states.
- Native packaging/signing/TestFlight and subjective visual acceptance remain external manual gates.

## Risks and mitigations

- **Open redirect/token leak:** typed same-origin parser only; no return URL input, auth payload,
  query, cookie or storage persistence.
- **Stale route restores data:** request generations plus synchronous route/account/token cleanup and
  object-URL ownership tests.
- **Role mistaken for authorization:** resolver is minimal; owner/detail/media/vote endpoints each
  reauthorize independently.
- **Private link copied after rotation:** share address derives only from current authoritative owner
  link state; stale/conflict disables assumptions until refresh.
- **Share API inconsistency:** capability detection, exact user-gesture call, AbortError handling and
  permanent Copy/manual fallback.
- **Internal production host shared:** accepted Q8B simplicity; retain strict scheme/origin validation,
  document/test deployment responsibility and fail without crashing on invalid origin.
- **Routing rewrite regression:** one narrow History API boundary, no router dependency, preserve
  current primary destination and composer contracts.
- **Premature security/completion claim:** built multi-account access tests, generic errors, pending
  real terminal/device/visual gates and no deployment.

## Harness handoff notes

- Read AGENTS.md, all seven source-of-truth context documents, this entire plan and every named
  approved dependency before editing. Inspect current code/tests/worktree; older plans contain
  historical absence statements superseded by current implementation.
- Preserve all existing tracked/untracked user and RF-14/RF-16/RF-18/device-correction work. Never
  reset, overwrite, clean or broadly reformat unrelated files.
- Implement exactly this RF-26 increment autonomously through executable technical validation. Do
  not stop after producing another plan. Stop and report only for a concrete contract/code conflict
  or missing authority that materially changes scope.
- Do not perform subjective browser/viewport/screenshot/zoom inspection. Automated UI/component,
  accessibility and layout tests are required; product-owner visual review stays pending.
- Do not commit, push, deploy, mutate Trello, generate native projects, operate on active user data,
  use the Codex-only orchestration runbook or launch other agents.
- Use English code, tests, comments, product copy and final report. Update project state only from
  evidence. Report exact commands, pass/fail/skip counts, built-stack scope and remaining manual
  visual/iPhone/terminal-writer gates.

## Resolved grooming decisions

- `1A`: author-only share controls on every open owner detail, including success; no recipient share
  button.
- `2A`: Copy always; capability-detected Share; selectable manual-copy fallback; cancellation neutral.
- `3A`: generic English NextPost invitation text plus URL; no protected/user content in share text.
- `4A`: narrow consultation path/history boundary; no app-wide router migration.
- `5A`: server-derived author entry opens neutral owner detail, never self-vote.
- `6A`: generic consultation auth context and exact destination return after sign-in/registration.
- `7A`: direct entry offers Go to Home and preserves normal browser Back behavior.
- `8B`: use strictly validated `window.location.origin`; no canonical-origin setting, with accepted
  proxy/public-origin operational responsibility.
- Registered-only Public/Private access, forwardable current Private links, generic unavailable,
  request-time revocation and ordinary platform link opening remain DEC-011/022/028–030.
- No contacts, invitation system, closed lists, messaging or automatic social posting.
- The owner explicitly authorized plan finalisation and autonomous external-harness launch on
  2026-10-19. Visual validation remains with the owner.

## Remaining questions

None
