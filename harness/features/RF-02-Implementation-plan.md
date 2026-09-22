# RF-02 - Sign in and sign out - Implementation Plan

## Status

`Ready for implementation`

## Source ticket

- Trello title: `RF-02 · Iniciar y cerrar sesión`
- Trello URL: https://trello.com/c/MdV631iO/6-rf-02-iniciar-y-cerrar-sesi%C3%B3n
- Trello list at intake: `Fase 1`
- Snapshot captured on: `2026-09-16T14:13:20+02:00`
- Grooming notes: `harness/grooming/RF-02-grooming.md`

## Objective

Make sign-in the default unauthenticated entry to NextPost. A registered user can sign in with email
and password, use the existing cookie-backed session, and sign out back to the sign-in screen. The
sign-in screen provides a clear secondary route to account creation.

This increment also replaces the rejected registration-first, visually heavy presentation with a
simple and durable visual foundation for the social product. All user-facing product copy is in
English.

## Context and current behaviour

- RF-01 implemented the `accounts` table, email canonicalisation, Argon2id password hashes,
  registration through `POST /api/accounts`, a signed `HttpOnly` session cookie, and session
  restoration through `GET /api/session`.
- `frontend/src/App.tsx` currently checks the session and sends an unauthenticated visitor directly to
  `RegistrationForm`. It has no sign-in state, sign-out action, or navigation between authentication
  views.
- `frontend/src/styles.css` currently uses a dark purple background, gradient, oversized heading,
  large rounded card, and strong shadow. The product owner rejected this presentation.
- Registration behaviour and its backend contract remain valid, but its visible copy is Spanish and
  must become English under DEC-009.
- `backend/app/security.py` can hash passwords but cannot verify them. The accounts API can restore a
  session but cannot authenticate existing credentials or clear a session.
- DEC-008 requires RF-02 to reuse the existing signed cookie. No session table, access/refresh token
  system, or identity provider is introduced.
- The application has no feed or product home yet. The existing minimal authenticated welcome state
  remains the destination after registration, sign-in, or session restoration.

## Scope

### In scope

- Sign-in as the default view after an unauthenticated session check.
- Email-and-password authentication against existing accounts.
- A visible `Create account` action from sign-in and a `Back to sign in` action from registration.
- Sign-out from the temporary authenticated welcome state and return to sign-in.
- Generic invalid-credentials handling that does not disclose whether an email is registered.
- A light, neutral, responsive visual foundation shared by sign-in, registration, session states, and
  the temporary welcome state.
- English user-facing copy throughout the current authentication experience and server validation
  messages that may reach it.
- Focused backend and frontend tests for the new behaviour and regressions in registration/session
  restoration.

### Out of scope

- Password recovery or change, email verification, social login, MFA, remember-me, or alias login.
- Server-side session persistence, token refresh, hosted identity providers, or native-specific
  authentication transport.
- Feed, profiles, consultations, broad social navigation, or a general application shell.
- A client router solely for switching between sign-in and registration.
- A component library, illustration or branding system, animation system, theme selector, complex
  landing page, or decorative visual effects.
- A runtime internationalisation framework, locale catalogue, language selector, or translated UI.
- Account schema changes or Alembic migrations.

## User experience

1. On application load, keep checking `GET /api/session` before choosing a view. Show a small neutral
   English loading state without flashing sign-in or registration.
2. A valid existing session restores the minimal welcome state. A normal 401 shows sign-in. A network
   or unexpected session-check failure shows an English retryable unavailable state.
3. Sign-in is the default unauthenticated view. It contains email, password, a primary `Sign in`
   action, and a clearly visible secondary `Create account` action.
4. Email and password have programmatic labels. Email uses email autocomplete semantics and password
   uses `current-password`. Password entry supports paste, password managers, and an accessible
   show/hide control.
5. Empty or malformed input is reported beside the relevant field before sending a request. While a
   valid request is pending, disable repeated submission and show a clear pending label.
6. Wrong password and unknown email produce the same form-level message: `Email or password is
   incorrect.` The screen must not indicate which credential failed.
7. A network or unexpected server failure shows a generic retryable message and leaves the form
   usable. Email may remain for correction. Password stays only in transient component state and is
   cleared when leaving the sign-in view or after successful authentication.
8. Successful sign-in immediately shows the same minimal authenticated welcome state used by RF-01.
   No feed or placeholder social activity is invented.
9. `Create account` replaces the sign-in view with the existing registration flow. Registration has
   a visible `Back to sign in` action. Leaving either form unmounts it so sensitive field state is not
   retained across view changes.
10. Successful registration still enters the welcome state. All registration labels, validation,
    errors, pending text, password controls, and surrounding copy are converted to English.
11. The welcome state includes a `Sign out` action. While it is pending, prevent repeated clicks. A
    successful sign-out clears local authenticated state and shows sign-in.
12. If sign-out cannot reach the server, keep the user in the welcome state and show a retryable
    English error; do not claim that the session ended. A successful idempotent server response is
    treated as signed out even if the cookie was already absent.

## Functional requirements

### FR-1 - Credential input

Sign-in accepts only email and password. Alias remains a public identity and is not a login
credential. Canonicalise email with the same trim and case-insensitive rules used by registration.
Do not trim, transform, log, persist separately, or return the password.

### FR-2 - Credential verification

Load the account by canonical email and verify the submitted password against its stored Argon2id
hash using the maintained Argon2 library. Authentication succeeds only when both belong to the same
account. Malformed input, unknown accounts, wrong passwords, and invalid stored hashes must not
create an authenticated session. Keep unknown-account and wrong-password handling sufficiently
uniform to avoid an obvious account-discovery branch.

### FR-3 - Non-enumerating failure

An unknown email and an incorrect password return the same HTTP status and stable
`invalid_credentials` code. The frontend shows the exact same message for both and exposes no
account, hash, or persistence detail. Validation may identify malformed email or a missing field
because that does not disclose stored-account ownership.

### FR-4 - Session creation and restoration

Successful sign-in places only the account identifier into the existing signed session. Retain the
accepted browser-session cookie name and attributes: `HttpOnly`, `SameSite=Lax`, path `/`, and
environment-appropriate `Secure`. Return only the existing account summary (`id` and display alias).
`GET /api/session` behaviour remains compatible.

### FR-5 - Sign-out

Sign-out clears the existing server-managed cookie session and returns success whether or not a valid
session was present. It must not delete or modify the account. After success, the client returns to
sign-in and no longer renders authenticated account data.

### FR-6 - Authentication navigation

After an unauthenticated session result, sign-in is the sole default view. Switching to registration
and back is local UI state and does not require a routing dependency. Registration success, sign-in
success, and restored sessions converge on the same welcome state.

### FR-7 - English product copy

All current user-visible authentication copy is English, including loading, unavailable, sign-in,
registration, welcome, validation, errors, pending actions, show/hide controls, retry, navigation,
and sign-out. Stable machine-readable API codes remain language-neutral. Do not add runtime i18n in
this increment, but keep copy organized so later centralisation is straightforward.

### FR-8 - Shared visual foundation

Use a light neutral page background, white surfaces, dark readable text, and one restrained accent
colour. Define a compact set of CSS custom properties for colour, typography, spacing, borders,
radii, focus, errors, and control states. Reuse consistent form, input, primary action, secondary
action, link, status, and feedback treatments across authentication views.

Typography uses ordinary product sizes and hierarchy. Spacing, borders, radii, and shadows are
modest. Do not use gradients, glow, oversized display type, dramatic shadows, decorative panels, or
illustrations. Preserve safe-area padding and responsive behaviour without horizontal overflow at a
320 px viewport.

### FR-9 - Accessibility and interaction states

Preserve semantic headings, labels, field-error associations, alerts/status announcements, keyboard
operation, visible focus, and sufficient contrast. Hover must not be the only indication of an
interactive element. Pending controls must clearly communicate and prevent duplicate actions.

## Technical approach

Extend the existing small auth flow rather than adding navigation or authentication infrastructure.
Keep HTTP handlers thin: place password verification/account lookup in the existing account-service
boundary, reuse the existing session middleware, and let `App` coordinate the few local views.

### Affected areas

- Frontend: extend `frontend/src/api.ts` with typed sign-in/sign-out requests and runtime response
  validation; add a focused sign-in form component; revise `frontend/src/App.tsx` state transitions;
  update `frontend/src/RegistrationForm.tsx` and `frontend/src/validation.ts` to English; rebuild the
  shared foundation in `frontend/src/styles.css`; update/add focused Vitest and Testing Library tests.
- Backend/application: extend `backend/app/security.py` with safe password verification;
  `backend/app/accounts_service.py` with credential authentication; `backend/app/schemas.py` with the
  sign-in request; and `backend/app/api/accounts.py` with session creation/deletion routes. Convert
  user-facing validation fallback text in `backend/app/main.py` and `backend/app/validation.py` to
  English. Extend `backend/tests/test_accounts.py`.
- Domain/data model: reuse the existing `Account`; no model or invariant changes.
- Storage/background work: none.
- Configuration/deployment: reuse the current signing secret, session middleware, credentialed CORS,
  and deployment configuration; no new service or setting.
- Documentation: update project state after implementation only when supported by validation.

### Data and migration requirements

No schema or data migration is required. Existing canonical email and password-hash columns are the
source of truth. Sign-in must remain compatible with every account created by RF-01. Sign-out changes
only the browser session cookie.

### API and integration requirements

- `POST /api/session`
  - Body: `{ "email": string, "password": string }`; reject extra fields.
  - Success: HTTP 200, set/update the existing session cookie, and return
    `{ "id": string, "alias": string }`.
  - Unknown email or wrong password: HTTP 401 with `{ "detail": { "code":
    "invalid_credentials" } }`.
  - Malformed payload: HTTP 422 using the existing stable validation envelope with English field
    messages.
  - Unexpected failure: ordinary generic server failure with no internal detail.
- `DELETE /api/session`
  - Clear the cookie-backed session whether it is valid, invalid, absent, or already cleared.
  - Success: HTTP 204 with no response body.
- `GET /api/session` remains unchanged and continues returning the existing authenticated account
  summary or the stable unauthenticated 401 response.
- Frontend requests use `credentials: "include"`; CORS remains restricted to configured origins.
- Treat all response bodies as untrusted runtime input. Do not transition to authenticated UI on an
  invalid success payload.

### Security and privacy

- Use Argon2's maintained verification API and handle verification mismatch/invalid-hash outcomes
  without exposing them. Never compare passwords or hashes manually.
- Avoid an obvious fast unknown-email path relative to password verification, while keeping the
  implementation small (for example, verify against a valid non-account fallback hash).
- Never log credential request bodies, plaintext passwords, password hashes, signing secrets, cookie
  contents, or failure details that identify registered emails.
- Set authenticated state only after successful password verification. Clear any pre-existing
  account identifier before or upon a failed sign-in so a failed attempt cannot inherit a session.
- Sign-out is idempotent and does not reveal whether a session or account existed.
- Retain the accepted cookie attributes and store only the account identifier in the signed cookie.

## Implementation sequence

1. Add safe password verification and account authentication to the backend service boundary.
2. Add the strict sign-in request schema and `POST`/`DELETE /api/session` handlers using the existing
   cookie session.
3. Convert current backend validation messages that can reach users to English and add backend tests
   for authentication, privacy, cookie/session behaviour, and logout.
4. Extend the typed frontend API with sign-in and sign-out calls plus focused response/error tests.
5. Add the accessible sign-in form and revise application state so sign-in is the unauthenticated
   default, registration is secondary, and sign-out returns to sign-in.
6. Convert all existing registration, loading, unavailable, and welcome copy and validation to
   English while preserving RF-01 behaviour.
7. Replace the current CSS with the approved shared neutral visual foundation and validate narrow and
   desktop layouts, focus, feedback, and control states.
8. Update frontend tests for the complete auth navigation and failure flows, then run every applicable
   repository validation command.

## Validation strategy

### Automated tests

- Backend: valid login; case/whitespace email canonicalisation; wrong password; unknown email; same
  non-enumerating response; malformed/extra input; invalid stored hash safety; cookie-backed session
  after login; failed login creates no session; logout with valid, missing, and invalid cookies;
  session unauthenticated after logout; existing registration and restoration regressions.
- Frontend API: sign-in payload/credentials, valid response, invalid response body, invalid credentials,
  validation errors, network/server errors, sign-out method/credentials, and successful 204.
- Frontend UI: sign-in after unauthenticated check; no registration flash; navigation to registration
  and back; client validation; password semantics/visibility; pending and generic credential errors;
  successful sign-in; registration success; restored session; successful logout; failed logout;
  retryable initial session check; English copy throughout.
- Existing health/readiness, registration, and validation tests remain green with expectations updated
  only for approved English copy and navigation.

### Manual validation

- At mobile (including 320 px) and ordinary desktop widths, verify the visual result is light,
  restrained, readable, and free of gradients, oversized typography, dramatic shadows, and horizontal
  overflow.
- Complete sign-in, registration navigation, registration, reload restoration, and sign-out with
  keyboard only. Confirm visible focus, labels, alerts/status announcements, password manager
  semantics, paste, and show/hide controls.
- Confirm unknown email and wrong password look identical to the user and neither exposes account
  existence.
- If Docker is available, exercise the complete frontend/API/PostgreSQL flow. If it remains
  unavailable, report the full container smoke test as pending rather than claiming it.

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

When Docker is available:

```powershell
docker compose up --build
```

## Acceptance criteria

- [ ] An unauthenticated visitor sees sign-in as the default page after the session check.
- [ ] Sign-in uses email and password only and accepts credentials created through RF-01.
- [ ] Valid credentials create the existing signed `HttpOnly` cookie session and show the welcome
      state.
- [ ] Unknown email and wrong password return and display the same comprehensible generic error.
- [ ] Malformed, failed, or unexpected requests do not create or inherit an authenticated session.
- [ ] Sign-in offers `Create account`, registration offers `Back to sign in`, and registration still
      succeeds into the welcome state.
- [ ] Sign-out clears the cookie session and returns to sign-in; repeated/unauthenticated sign-out is
      safe.
- [ ] A failed sign-out leaves the user in a usable authenticated state with retryable feedback.
- [ ] All current product-facing authentication and validation copy is English.
- [ ] Login, registration, status, and welcome views share the approved light, restrained visual
      foundation without decorative excess.
- [ ] The responsive flow supports keyboard use, visible focus, programmatic labels, accessible
      feedback, and a 320 px viewport without horizontal overflow.
- [ ] No account migration, router, i18n runtime, component library, token subsystem, or unrelated
      product shell is introduced.
- [ ] Existing registration, session restoration, health/readiness, and all applicable quality checks
      pass.

## Dependencies and ordering

- Depends on RF-01's implemented account, validation, Argon2id, cookie-session, and registration
  contracts.
- Follows accepted DEC-008 for the session mechanism and DEC-009 for English product copy.
- The RF-01 Docker/PostgreSQL container smoke test remains an environmental check; it does not change
  RF-02's approved behaviour.
- Does not depend on password recovery, email verification, profiles, feed, native projects, or later
  social features.

## Risks and mitigations

- Account enumeration: use one generic status/code/message for unknown email and wrong password and
  avoid an obvious verification-timing branch.
- Password/hash exposure: use the maintained Argon2 API and exclude credentials, hashes, and cookie
  contents from responses and logs.
- Authentication state drift: converge registration, sign-in, and restoration on one account-summary
  state; only leave it after confirmed sign-out success.
- Cookie deletion inconsistencies: clear the existing session through the same middleware and test
  valid, invalid, missing, and repeated cases.
- Visual scope creep: implement only the small token set and shared auth primitives described here;
  do not invent a broader design system or social shell.
- English conversion regression: update tests with the approved copy and search current frontend and
  server validation sources for remaining Spanish user-facing messages.
- Docker may remain unavailable: run every non-container check and report the smoke test accurately.

## Harness handoff notes

- The repository contains uncommitted/untracked bootstrap and RF-01 work. Preserve every existing file
  and make only changes required by this plan.
- The current RF-01 frontend presentation is intentionally superseded, but its backend account and
  session foundation must remain compatible.
- Keep implementation, code identifiers, comments, tests, documentation, and the final report in
  English.
- Do not commit, push, deploy, modify Trello, generate native projects, or launch another agent.
- Do not add speculative dependencies or infrastructure. Update project state only when validation
  evidence supports the new lifecycle.

## Resolved grooming decisions

- Sign-in is the default unauthenticated page; registration is reached through a visible secondary
  action and provides a way back.
- Sign-in uses email and password only. Alias is not a login credential.
- The existing minimal welcome view remains the authenticated destination until a later product-home
  feature.
- Sign-out returns the user to sign-in and reuses the existing cookie-session mechanism.
- Invalid credentials are understandable but do not reveal whether an account exists.
- The new visual base is light and neutral with one restrained accent, normal typography, modest
  spacing/borders/radii, shared styles, and no visually heavy effects.
- All user-facing copy is English. Runtime localisation remains deferred until multiple languages are
  actually required.
- The increment stays small: no router, broad application shell, component library, theme system, or
  new authentication infrastructure.

## Remaining questions

None
