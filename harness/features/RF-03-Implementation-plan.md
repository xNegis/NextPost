# RF-03 - Crear y editar el perfil - Implementation Plan

## Status

`Ready for implementation`

## Source ticket

- Trello title: `RF-03 · Crear y editar el perfil`
- Trello URL: https://trello.com/c/WAVz9fNb/9-rf-03-crear-y-editar-el-perfil
- Trello list at intake: `Fase 1`
- Snapshot captured on: `2026-09-16T15:53:29+02:00`
- Grooming notes: `harness/grooming/RF-03-grooming.md`

## Objective

Give a signed-in user a private, read-only `My profile` view showing their email and nickname, and
introduce the first small shared authenticated navigation component. The same navigation must be
usable and visually correct across narrow mobile, tablet, and desktop layouts: a compact top bar on
wider screens and a thumb-reachable bottom bar on narrow screens.

RF-03 does not expose profiles to other users and does not edit profile data despite the broader
source-card title. It establishes a deliberately small navigation and private-account-profile
foundation without inventing later social features.

## Context and current behaviour

- RF-01 implemented the `accounts` table with UUID `id`, canonical email, display `alias`, canonical
  alias, Argon2id password hash, and creation time. Email and alias already contain all data required
  by RF-03.
- RF-02 implemented registration, sign-in, signed-cookie session restoration, sign-out, English copy,
  and a light neutral visual base. After authentication, `frontend/src/App.tsx` currently renders a
  single welcome card containing `Sign out`.
- The authenticated `AccountSummary` contains only `id` and `alias`; email is not returned to general
  authentication flows. Preserve that narrow contract.
- The frontend currently has no router, application shell, or navigation component. `App.tsx` uses
  local state for its few authentication views.
- There is no profile entity, image/file storage, moderation pipeline, background worker, or need for
  a schema migration in this increment.
- DEC-004 through DEC-006 require the existing React/TypeScript, FastAPI/SQLAlchemy/Alembic, and
  PostgreSQL stack. DEC-008 requires the existing signed `HttpOnly` cookie session. DEC-009 requires
  English user-facing copy.

## Scope

### In scope

- One shared authenticated navigation component with `Home` and `Profile` destinations.
- A compact top-navigation presentation on wider screens and a fixed, safe-area-aware bottom
  presentation on narrow/mobile screens, using one semantic destination model.
- Inline/repository-owned Home and Profile SVG icons, visible English labels, active state, visible
  focus, semantic navigation, and touch targets of at least 44 by 44 CSS pixels.
- Local authenticated-view state; `Home` remains the default after registration, sign-in, and session
  restoration.
- A private `My profile` view that retrieves and displays the authenticated account's `Email` and
  `Nickname` as labelled read-only details.
- The text `Only you can see this email.` next to the email's privacy context.
- Profile loading, retryable unavailable, expired-session, and sign-out states.
- Moving `Sign out` from Home into My profile while preserving RF-02's behaviour.
- Automated and manual validation of privacy, accessibility, responsive layout, and auth regressions.

### Out of scope

- Editing email, nickname/alias, password, roles, account status, or session mechanics.
- Profiles of other users, profile search, public profile URLs, sharing, or deep links.
- Bio, display/legal name, location, join date, links, uploaded avatar, or other profile fields.
- Followers, following, counts, messages, badges, rankings, activity, consultation lists, or criterion
  metrics.
- Blocking, reporting, moderation administration, data export, and account deletion workflows.
- A router, native project generation, component library, icon library, broad application shell, or
  unrelated design-system expansion.
- Database schema changes, storage services, or background processing.

## User experience

1. Registration, successful sign-in, or restored authentication continues to open `Home`, which
   preserves the existing welcome heading and summary. `Sign out` is no longer shown on Home.
2. Authenticated views include the shared primary navigation. It contains Home and Profile; each has
   an icon and visible text label. The active destination is visually distinct and identified with
   `aria-current="page"`.
3. On wider screens the navigation is a restrained top bar integrated with the existing light visual
   foundation. On narrow/mobile screens it is fixed at the bottom, reachable by thumb, includes the
   bottom safe-area inset, and never covers page content.
4. Selecting Profile shows `My profile` and begins the private profile request. During the request,
   show an accessible loading/status state without stale or invented email data.
5. Success displays labelled read-only values for `Email` and `Nickname`. Use text/detail rows rather
   than disabled inputs so the interface does not imply temporary editability. Show `Only you can see
   this email.`
6. Long valid email or nickname values wrap safely and do not create horizontal overflow.
7. A network or unexpected server failure shows a profile-local, understandable English error and a
   `Retry` action. Navigation remains usable, and retry requests the profile again.
8. A profile HTTP 401 means the signed-in state is no longer valid. Clear private profile/account
   client state, hide authenticated navigation, and return to `Sign in`.
9. `Sign out` appears in My profile. While pending, prevent repeated activation and communicate the
   pending state. Success clears profile/account state and returns to Sign in. Failure leaves the user
   on My profile with their already loaded data and the existing retryable sign-out feedback.
10. Unauthenticated authentication, loading, and registration views do not show the authenticated
    navigation.

## Functional requirements

### FR-1 - Private profile retrieval

Expose `GET /api/profile` for the currently authenticated account. A successful response contains
exactly:

```json
{
  "email": "ana@example.com",
  "nickname": "Ana"
}
```

`nickname` maps from the existing `Account.alias`; do not rename or duplicate the persisted column.
Do not include account ID, canonical alias, password hash, creation time, session values, or any other
field in this response.

### FR-2 - Authentication and privacy

Resolve the account only from the existing signed-cookie session. If the cookie is missing, invalid,
or references a deleted account, return HTTP 401 with the existing stable
`{"detail":{"code":"unauthenticated"}}` contract. A requester cannot supply an account identifier
to read another account. Do not log or persist profile response data on the client.

### FR-3 - Narrow authentication contracts

Keep `AccountSummary`, registration, sign-in, and `GET /api/session` response shapes unchanged. Email
must not be added to the general account/session summary merely to serve My profile.

### FR-4 - Authenticated destinations

Model `Home` and `Profile` as local authenticated UI state. Home is always the initial destination
after registration, sign-in, or successful session restoration. Switching destinations does not
alter authentication and needs no URL router.

### FR-5 - Responsive shared navigation

Use one reusable semantic navigation component and a content/layout-based CSS media query. On wider
screens render a compact top bar; on narrow screens render a fixed bottom bar. Preserve safe-area
insets and sufficient page padding so the bar cannot obscure content. Both destinations require
visible English labels, repository-owned SVG icons, an active state that does not depend only on
colour, visible keyboard focus, and at least 44 by 44 CSS pixel interactive targets.

### FR-6 - Profile interaction states

Request private profile data when the Profile view mounts/opens. A valid response renders the two
read-only fields. A network, non-401 HTTP, or invalid success response yields a local retryable error.
A 401 leaves authenticated UI and returns to Sign in. Sensitive profile state must be cleared on
sign-out and must not survive in browser persistence.

### FR-7 - Sign-out placement

Remove the sign-out action from Home and place it in My profile. Reuse the existing `DELETE
/api/session` behaviour. Preserve duplicate-prevention, pending text, success transition, and the
retryable failure rule that does not falsely claim the session ended.

### FR-8 - English, accessibility, and restrained visuals

Use the exact profile title and labels `My profile`, `Email`, `Nickname`, and `Only you can see this
email.` Keep loading, errors, retry, navigation, and sign-out text in English. Reuse RF-02's light
neutral palette, spacing, control, focus, and feedback patterns. Do not add gradients, dramatic
shadows, oversized type, decorative panels, or image assets.

## Technical approach

Add a narrow authenticated read endpoint and compose the current authenticated frontend into Home
and Profile views around a shared responsive navigation. Keep product rules and privacy explicit,
reuse the existing cookie/account loading boundary, and avoid schema, routing, storage, or dependency
changes.

### Affected areas

- Frontend API: extend `frontend/src/api.ts` with a private-profile type, strict runtime guard, and
  `fetchProfile()` using `credentials: "include"`; distinguish unauthenticated from retryable errors.
- Frontend views/state: revise `frontend/src/App.tsx` so authenticated state owns a `Home`/`Profile`
  destination, renders shared navigation, keeps Home as default, and clears authenticated/profile
  state appropriately.
- Frontend components: add focused navigation and profile components (names may follow repository
  conventions) rather than enlarging `App.tsx` with all markup and request-state logic.
- Frontend styles: extend `frontend/src/styles.css` with responsive authenticated layout/navigation,
  safe-area spacing, active/focus states, read-only detail rows, wrapping, and narrow/wide behaviour.
- Frontend tests: extend API and App tests and add focused component tests where helpful.
- Backend schemas/API: add a private profile response schema in `backend/app/schemas.py` and the
  authenticated GET route in `backend/app/api/accounts.py`, reusing/refactoring the existing safe
  session-account lookup without broadening other responses.
- Backend tests: extend `backend/tests/test_accounts.py` for success, exact privacy shape, and all
  unauthenticated forms.
- Domain/data model, storage, background work, configuration, and deployment: unchanged.
- Documentation: update project state only after implementation and validation evidence support it.

### Data and migration requirements

No data or schema migration is required. `Account.email` and `Account.alias` are the sources of truth.
Do not create a profile table or duplicate either field. No rollback/data transformation is needed.

### API and integration requirements

- `GET /api/profile`
  - Authentication: existing signed cookie; no request account ID or body.
  - Success: HTTP 200 and exactly `{ "email": string, "nickname": string }`.
  - Missing/invalid/deleted-account session: HTTP 401 with the existing `unauthenticated` detail.
  - Unexpected failure: generic server failure without internal detail.
- Frontend sends credentials and treats all response bodies as untrusted runtime input.
- HTTP 401 is distinct from offline, server, or malformed-success failures because it exits the
  authenticated shell; other failures remain local and retryable.
- Registration, sign-in, session restoration, and sign-out API contracts remain compatible.

### Security and privacy

- Authorize by the account identifier obtained exclusively from the verified signed session.
- The endpoint exposes only the current account; there is no user-supplied target identifier.
- Keep email out of `AccountSummary`, URLs, logs, analytics, local storage, and session storage.
- Clear transient profile state on sign-out and on transition to unauthenticated state.
- Never return password hashes, canonical/internal identity fields, cookie contents, or signing
  details.
- Do not introduce editable/user-generated profile content, uploads, or new moderation and retention
  surfaces.

## Implementation sequence

1. Add the strict private-profile response schema and authenticated `GET /api/profile` route while
   preserving all existing auth response shapes.
2. Add backend tests for the exact successful payload and missing, invalid, and deleted-account
   sessions, then run focused backend checks.
3. Add the typed `fetchProfile()` client, strict success guard, and distinct unauthenticated/error
   mapping with API tests.
4. Create the semantic Home/Profile navigation component with inline SVG icons and active/focus
   semantics.
5. Create the My profile component with loading, read-only success, local retry, session-expired, and
   sign-out states.
6. Refactor `App.tsx` to render the authenticated destinations, default to Home, place sign-out only
   in Profile, and clear state on session loss/sign-out.
7. Extend the shared CSS for wide top and narrow bottom navigation, safe areas, content clearance,
   touch targets, wrapping, and the existing restrained visual language.
8. Add/adjust frontend tests and run the complete validation suite, followed by real responsive and
   Docker/PostgreSQL smoke validation.

## Validation strategy

### Automated tests

- Backend: valid authenticated profile; exact `email`/`nickname` keys and mapped values; no ID,
  canonical alias, hash, or timestamp; missing cookie; malformed cookie; deleted-account session;
  existing registration/sign-in/session/sign-out regressions.
- Frontend API: credentials and method; valid response; missing/wrong/extra success fields rejected;
  401 maps to unauthenticated; network and server failures remain retryable/unavailable.
- Navigation/UI: Home default after registration, sign-in, and restoration; navigation absent before
  authentication; Home/Profile switching; visible labels/icons; active semantics; profile loading;
  read-only email/nickname and privacy copy; retry; 401 transition to Sign in; sign-out success,
  pending duplicate prevention, and failure retention; no sign-out action on Home.
- Existing 48 frontend and 34 backend tests remain green alongside the new tests.

### Manual validation

- Verify real rendered layouts at 320 px and representative mobile, tablet, ordinary desktop, and
  wide desktop widths. Check practical portrait/landscape orientations and 200% browser zoom.
- Confirm desktop top navigation and mobile fixed bottom navigation, safe-area spacing, minimum touch
  targets, readable labels, non-colour active state, no covered content, and no horizontal overflow.
- Test long valid email/nickname wrapping and profile loading/error/retry without layout shifts that
  make controls unusable.
- Complete registration or sign-in, Home/Profile navigation, reload restoration, profile retrieval,
  failed/successful sign-out, and expired-session handling with keyboard only; confirm visible focus,
  semantic navigation, status/alert announcements, and logical order.
- Exercise the full frontend/API/PostgreSQL stack through Docker Compose and verify that private
  profile data belongs only to the signed-in account.

### Commands

From the repository root:

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
docker compose config
```

Full-stack smoke and responsive browser validation:

```powershell
docker compose up --build
```

## Acceptance criteria

- [ ] Authenticated users see a shared Home/Profile navigation; unauthenticated/auth-loading views do
      not.
- [ ] Home remains the initial authenticated destination and retains the current welcome content
      without a sign-out action.
- [ ] Profile navigation opens `My profile` and requests the current account's private profile.
- [ ] My profile displays the authenticated owner's email and nickname as labelled read-only details
      and states `Only you can see this email.`
- [ ] `GET /api/profile` accepts no target account identifier, returns exactly email/nickname for the
      signed-in account, and returns the stable unauthenticated 401 for missing, invalid, or stale
      sessions.
- [ ] Email is not added to the general session/account response, browser persistence, URLs, or logs,
      and private profile state is cleared on sign-out/session loss.
- [ ] Profile loading is communicated; retryable failures keep navigation usable and offer Retry;
      profile 401 returns to Sign in without showing stale private data.
- [ ] Sign out exists in My profile only and preserves pending, success, idempotent server, and
      retryable failure behaviour from RF-02.
- [ ] One semantic navigation component appears as a compact top bar on wider screens and a fixed,
      safe-area-aware bottom bar on narrow/mobile screens without obscuring content.
- [ ] Both destinations have visible English labels, repository-owned SVG icons, at least 44 by 44
      CSS pixel targets, visible focus, and an active state exposed with `aria-current="page"` and not
      dependent only on colour.
- [ ] At 320 px, representative mobile/tablet/desktop widths, practical landscape orientation, and
      200% zoom, content remains readable and operable with no navigation overlap or horizontal
      overflow; long email/nickname values wrap safely.
- [ ] The flow is keyboard operable with logical order and accessible loading/error announcements.
- [ ] No router, database migration, profile-edit endpoint, uploaded avatar, additional profile data,
      icon/component library, or later social feature is introduced.
- [ ] Existing registration, sign-in, restoration, sign-out, health/readiness, and all repository
      quality checks remain green.
- [ ] A live Docker/PostgreSQL smoke flow proves authentication, private profile retrieval,
      navigation, and sign-out against the built stack.

## Dependencies and ordering

- Depends on RF-01's account, email/alias persistence, and signed-session foundation.
- Depends on RF-02's login-first flow, restoration, sign-out, English copy, and light visual base.
- Public criterion metrics remain owned by RF-23; following by RF-24; blocking/reporting by RF-29 and
  RF-30; deletion/export by RF-34 and RF-35.
- No later ticket is required for this private read-only vertical increment.

## Risks and mitigations

- **Private email leakage:** isolate email in a dedicated current-user endpoint and strict client
  type; never broaden shared session/account summaries or accept a target account ID.
- **Responsive navigation covers content:** include safe-area-aware bottom padding and validate real
  narrow, landscape, zoomed, and long-content layouts.
- **Icon-only ambiguity:** pair icons with visible labels and semantic active state.
- **Authentication state drift:** treat profile 401 as session loss, clear transient private state,
  and converge on Sign in; keep other failures local and retryable.
- **Premature shell/routing complexity:** retain local state and exactly two real destinations; do not
  add placeholders for unimplemented features.
- **RF-02 regression:** preserve auth contracts and sign-out behaviour while moving only its UI
  location; rerun all existing tests and live smoke flow.

## Harness handoff notes

- The repository is entirely untracked and contains the user's bootstrap plus completed RF-01/RF-02
  work. Preserve every unrelated file and change only RF-03 scope.
- Implement in English, including identifiers, comments, tests, user-facing copy, and final report.
- Do not commit, push, deploy, mutate Trello, generate native projects, or launch another agent.
- Do not replace the accepted dependency versions, session mechanism, visual foundation, or
  architecture.
- Update project state only when implementation and independent validation evidence support it.

## Resolved grooming decisions

- RF-03 is an owner-only, read-only My profile increment.
- Registration already creates the minimum profile; there is no separate onboarding step.
- My profile displays existing email and nickname/alias only; neither is editable.
- Email is private to the owner and is served only through a dedicated authenticated profile read.
- The first authenticated navigation contains Home and Profile, defaults to Home, and uses no router.
- The same semantic component is a desktop/wide top bar and mobile/narrow safe-area bottom bar.
- Icons have visible labels; focus, active state, semantics, touch size, wrapping, and responsive
  behaviour are explicit acceptance requirements.
- Sign out moves into My profile and retains RF-02 behaviour.
- No schema change, uploaded avatar, additional field, edit API, public profile, or later social
  feature belongs to RF-03.

## Remaining questions

None
