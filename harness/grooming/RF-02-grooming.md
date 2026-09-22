# RF-02 - Iniciar y cerrar sesión - Grooming

## Status

`Ready for implementation`

## Trello snapshot

- Title: `RF-02 · Iniciar y cerrar sesión`
- URL: https://trello.com/c/MdV631iO/6-rf-02-iniciar-y-cerrar-sesi%C3%B3n
- Board: `APP - NextPost`
- List: `Fase 1`
- Labels: None
- Members: None
- Due date: None
- Checklists: None
- Comments: None
- Captured on: `2026-09-16T14:13:20+02:00`
- Last Trello activity at intake: `2026-09-15T09:27:49.395Z`

### Description and acceptance criteria at intake

**Historia de usuario**

Como usuario registrado, quiero entrar y salir de mi cuenta.

**Comportamiento y criterios de aceptación**

- El inicio de sesión permite usar las credenciales del registro y muestra errores comprensibles sin
  exponer información de otras cuentas.
- Cerrar sesión significa volver a la pantalla de inicio.

The punctuation and accent in the final bullet were normalised in this readable snapshot without
changing its meaning.

## Intended outcome

Make login the default unauthenticated entry to NextPost. The login page offers a secondary, clearly
visible action to create an account. Registration becomes a separate view rather than the product's
landing screen. Authenticated users can log out and return to login.

The same increment establishes a restrained visual foundation suitable for a social product: clear,
friendly, reusable, and deliberately light on decoration.

## Current code findings

- RF-01 implemented account persistence, Argon2id password hashes, a signed `HttpOnly` cookie,
  `POST /api/accounts`, and `GET /api/session`.
- `frontend/src/App.tsx` currently sends unauthenticated visitors directly to
  `RegistrationForm`. There is no login screen, logout action, or routing/view navigation.
- `frontend/src/styles.css` uses a dark purple background, gradient, oversized heading, large card,
  heavy spacing, rounded corners, and shadow. The product owner explicitly rejected this as too
  visually loaded.
- The registration form itself is functional and tested. Its fields and API behaviour should be
  preserved while its placement and presentation are revised.
- `backend/app/security.py` hashes passwords but does not yet expose password verification.
- `backend/app/api/accounts.py` can restore an authenticated session but cannot create a session from
  existing credentials or clear one.
- DEC-008 already fixes the MVP session mechanism: RF-02 must reuse the signed cookie and must not add
  a session table or token subsystem.

## Dependencies and conflicts

- RF-02 depends on RF-01's account, password-hash, and cookie contracts.
- The RF-01 implementation remains in review. Its backend/account work is retained, but its
  registration-first unauthenticated presentation is rejected and will be replaced by RF-02.
- Email verification and password recovery remain outside the MVP.
- A broad application shell, feed, or social navigation does not yet exist. Login success therefore
  needs a minimal authenticated destination without inventing later product features.

## Candidate approach

### Accepted small vertical increment

1. Show login as the default unauthenticated view.
2. Provide a secondary “Crear cuenta” action that opens the existing registration flow.
3. Provide a “Volver a iniciar sesión” action from registration.
4. Add one login endpoint that verifies the canonical email and Argon2id password, then writes the
   existing cookie session.
5. Add one logout endpoint that clears the cookie, then return to login.
6. Keep the current minimal authenticated welcome state until a later ticket provides the actual
   social application home.
7. Replace the current styling with a small reusable visual base rather than another bespoke screen.

### Proposed visual foundation

- Light neutral page background and white surfaces.
- Dark, highly readable text and one restrained accent colour.
- Normal heading sizes; no gradients, glow effects, oversized display typography, or dramatic
  shadows.
- Modest spacing, borders, and corner radii.
- Shared tokens for colours, typography, spacing, radii, borders, focus, errors, and buttons.
- One consistent form, primary button, secondary link/button, and feedback treatment reused by login
  and registration.
- Responsive by default, with the same understated presentation on desktop and mobile.

## Questions

### Open

- None.

### Resolved

- 2026-09-16: The product owner explicitly requested login as the default unauthenticated page.
- 2026-09-16: Login must offer a visible option to create an account.
- 2026-09-16: Registration must no longer be shown directly as the initial unauthenticated page.
- 2026-09-16: The current styling was rejected as too visually loaded. The replacement must be
  simple, attractive, and suitable as a durable base for a social network rather than a showcase
  design.
- 2026-09-16: Login uses email and password only. Alias remains the public identity and is not a login
  credential in the MVP.
- 2026-09-16: Successful login keeps the existing minimal authenticated welcome destination until a
  later feature introduces the actual product home/feed.
- 2026-09-16: Login and registration use a light neutral visual foundation with white surfaces, dark
  text, one restrained accent colour, normal typography, modest borders/radii, and no gradients or
  dramatic shadows.
- 2026-09-16: All user-facing product copy is English. The MVP does not add a translation framework,
  but new UI and API messages must avoid embedding Spanish as the product language and should remain
  easy to centralise for future localisation.

## Proposed scope

### In scope

- Default login view and navigation between login and registration.
- Email/password authentication using the existing account records and cookie session.
- Logout from the temporary authenticated view and return to login.
- Generic invalid-credentials errors that do not reveal whether an email exists.
- A small shared visual-token and component-style foundation applied to both auth views.
- Replace existing Spanish authentication, validation, error, loading, welcome, and action copy with
  English.
- Focused frontend/backend tests and responsive/keyboard validation.

### Out of scope

- Password recovery/change, email verification, social login, MFA, remember-me, or server-side
  session storage.
- Feed, profiles, consultations, full application navigation, or a broader social-network shell.
- Illustration systems, complex branding, animation systems, themes, or decorative landing-page
  sections.
- A runtime internationalisation framework, language selector, or translated locale catalogue.

## Validation outline

- Backend tests for valid login, wrong password, unknown email, generic failure response, canonical
  email matching, cookie creation, logout, and cleared-session behaviour.
- Frontend tests for login as the initial view, navigation to/from registration, pending/errors,
  login success, session restoration, and logout.
- Visual/manual checks at mobile and desktop widths for simplicity, hierarchy, focus, readable
  errors, and lack of horizontal overflow.
- Run all existing backend/frontend format, lint, type, test, build, audit, migration, and Compose
  configuration checks.

## Readiness checklist

- [x] Desired outcome is unambiguous.
- [x] Scope and exclusions are confirmed.
- [x] Code impact was inspected.
- [x] Dependencies and conflicts are identified.
- [x] Technical approach is selected.
- [x] UX and failure states are confirmed where applicable.
- [x] Security and privacy implications are resolved where applicable.
- [x] No data migration is expected.
- [x] Test and manual validation expectations are agreed.
- [x] No material question remains.
- [x] Product owner explicitly approved plan finalisation.
