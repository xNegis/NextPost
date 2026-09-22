# RF-01 - Crear una cuenta - Grooming

## Status

`Ready for implementation`

## Trello snapshot

- Title: `RF-01 · Crear una cuenta`
- URL: https://trello.com/c/SGj0fby6/2-rf-01-crear-una-cuenta
- Board: `APP - NextPost`
- List: `Fase 1`
- Labels: None
- Members: None
- Due date: None
- Checklists: None
- Comments: None
- Captured on: `2026-09-15T18:02:58+02:00`
- Last Trello activity at intake: `2026-09-15T09:25:25.945Z`

### Description and acceptance criteria at intake

**Historia de usuario**

Como visitante, quiero crear una cuenta para pedir opiniones y participar en las consultas de otras
personas.

**Comportamiento y criterios de aceptación**

- El registro solicita correo, contraseña y alias; no exige nombre legal, teléfono ni acceso a
  contactos.
- Los campos obligatorios y sus errores se identifican antes de enviar el formulario. Los errores no
  eliminan los datos ya introducidos que puedan conservarse de forma segura.
- La cuenta no puede duplicar un correo o alias existente. La interfaz evita revelar innecesariamente
  si un correo pertenece a otra persona.
- El usuario deberá introducir la misma contraseña dos veces para confirmar que no se ha equivocado.

Intake note: the final bullet has only been normalised for spelling in this readable snapshot; its
meaning has not been changed.

## Intended outcome

Allow a visitor to create the minimum NextPost identity needed for later authentication and product
participation, using an email address, a unique public alias, and a password confirmed in the client.
The flow must be understandable and usable on the shared responsive web/mobile frontend, reject
invalid or duplicate identities safely, and avoid collecting unrelated personal data.

## Current code findings

- The frontend is a single React 19 and TypeScript application. `frontend/src/App.tsx` currently
  contains only a foundation/readiness screen; there is no router, form library, authentication
  state, design system, or account UI.
- `frontend/src/api.ts` only implements the readiness request and runtime response guard. There is no
  account API client or shared error contract.
- The current CSS already provides responsive safe-area padding, but the registration layout,
  validation, pending/success/error states, password controls, and accessibility behaviour all need
  to be introduced.
- The FastAPI backend exposes only `/api/health` and `/api/ready`. There are no account endpoints,
  authentication dependencies, application services, or domain models.
- SQLAlchemy session management and Alembic are configured, but the baseline migration intentionally
  contains no product tables. RF-01 will introduce the first product schema and migration.
- PostgreSQL 18 is the accepted relational system of record. Database constraints can enforce email
  and alias uniqueness under concurrent registration attempts.
- No mail service, background worker, queue, rate-limiter, or external identity provider exists.
- Production frontend Nginx currently serves only static files and does not proxy `/api`; local and
  Compose frontend builds call the API through `VITE_API_BASE_URL`. Any cookie/session choice must be
  compatible with the eventual web and Capacitor clients.
- The repository is currently entirely untracked in Git. These appear to be the user's bootstrap
  files and must be preserved; RF-01 work must not assume a clean committed baseline.

## Dependencies and conflicts

- `RF-02 · Iniciar y cerrar sesión` is the next `Fase 1` ticket and owns explicit sign-in/sign-out
  behaviour. Grooming must decide whether RF-01 creates a session immediately or stops at account
  creation, without silently absorbing all of RF-02.
- `RF-03 · Crear y editar el perfil` owns the broader profile. RF-01 should create only the public
  alias/identity fields essential to registration unless an explicit dependency is accepted.
- `RF-XX · Verificar el correo` is labelled `Fuera del MVP`. RF-01 therefore cannot depend on email
  verification unless the product owner changes that backlog decision.
- `RF-XX · Cambiar la contraseña`, including forgotten-password recovery, is also `Fuera del MVP`.
  This makes password guidance and the consequences of a mistyped/unreachable email especially
  important.
- DEC-004, DEC-005, and DEC-006 fix the shared React client, FastAPI/SQLAlchemy/Alembic backend, and
  PostgreSQL boundaries. Introducing a hosted identity provider would change the accepted technical
  direction and require a durable decision.
- Later access-control tickets refer to active, suspended, and blocked accounts. RF-01 should leave a
  clean account-status boundary without implementing moderation or blocking behaviour now.

## Candidate approach

### Selected approach

Build the smallest first-party registration slice that fits the accepted stack:

1. One responsive form in the existing React application.
2. One FastAPI registration endpoint.
3. One account table with email, alias, password hash, and creation timestamp.
4. Database uniqueness for canonical email and alias.
5. A minimal authenticated session after creation and the already accepted welcome state.

Do not introduce a hosted identity provider, CAPTCHA, custom rate-limiting infrastructure, separate
role/status machinery, password-reputation services, or native-only behaviour in RF-01. These can be
added by later tickets if real requirements justify them.

Passwords are stored with Argon2id. Successful registration establishes a signed `HttpOnly` cookie
containing only the account identifier; the MVP does not add a server-side session table.

## Questions

### Open

#### Product flow and lifecycle

- None.

#### Email and alias rules

- None.

#### Password policy and usability

- None.

#### Abuse, errors, and operational constraints

- None.

#### Scope and validation

- None.

### Resolved

- 2026-09-15: RF-01 was explicitly selected by the product owner for grooming.
- 2026-09-15: The Trello card specifies email, password, password confirmation, and alias as the only
  registration data; legal name, telephone, and contact access are not required.
- 2026-09-15: Email and alias duplicates must be rejected, and the UI must avoid unnecessary email
  account disclosure.
- 2026-09-15: Email verification and password recovery/change are currently outside the MVP backlog.
- 2026-09-15: Successful registration creates an authenticated session automatically; manual login
  and logout remain owned by RF-02.
- 2026-09-15: A successfully registered account becomes active immediately. RF-01 has no dormant or
  pending-verification state.
- 2026-09-15: Registration success leads to a minimal authenticated welcome/home state and does not
  invent feed or consultation behaviour.
- 2026-09-15: RF-01 will not require terms/privacy acceptance without approved legal copy and URLs.
  It may show only factual privacy guidance supported by accepted product behaviour.
- 2026-09-15: Email input is trimmed at its boundaries and compared case-insensitively. The canonical
  value is retained for authentication, without provider-specific transformations such as removing
  dots or `+tags`.
- 2026-09-15: Aliases contain 3-30 letters, numbers, underscores, or dots, with no whitespace. Alias
  uniqueness is case-insensitive, while the user's chosen casing is preserved for display. Alias
  editing remains owned by RF-03.
- 2026-09-15: RF-01 reserves system/confusing aliases including `admin`, `support`, and `nextpost`.
  General profanity, impersonation, and alias moderation are deferred to an explicit later feature.
- 2026-09-15: An unavailable alias receives a specific field error. A duplicate email receives the
  non-enumerating message: “No se ha podido crear la cuenta con esos datos. Revísalos o inicia sesión
  si ya tienes una cuenta”, without confirming that the address is registered.
- 2026-09-15: Passwords contain 15-128 Unicode code points, may include spaces and Unicode, are not
  trimmed or truncated, and have no character-class composition rules.
- 2026-09-15: Checking proposed passwords against a common/expected/compromised-password blocklist is
  explicitly outside the MVP. This can be reconsidered as a later security increment.
- 2026-09-15: Both password inputs allow paste, password-manager/autofill use, and accessible
  show/hide controls. Registration fields use the appropriate `new-password` autocomplete semantics.
- 2026-09-15: Email and alias survive correctable validation/server errors. Password values survive
  only in transient component memory, are cleared on successful registration or leaving the view,
  and are never stored in browser persistence or logs.
- 2026-09-15: Password confirmation is a client-side entry check and is neither sent nor persisted.
  The server receives and authoritatively validates only the definitive password.
- 2026-09-15: The product owner directed RF-01 grooming toward the simplest useful MVP increment and
  away from speculative or disproportionately complex mechanisms.
- 2026-09-15: RF-01 is limited to the registration form, one registration endpoint, the minimum
  account persistence, automatic session creation, and a welcome state. CAPTCHA, custom throttling,
  explicit idempotency, hosted identity providers, separate role/status machinery, and other
  speculative mechanisms remain outside this ticket.
- 2026-09-15: Ordinary client/server validation, database uniqueness, disabling submission while the
  request is pending, and a retryable generic unexpected-error state are sufficient for RF-01.
- 2026-09-15: Passwords are hashed with Argon2id. Automatic authentication uses a signed `HttpOnly`
  cookie containing only the account identifier, with no server-side session table in the MVP. RF-02
  will reuse this session mechanism for manual login and clear the cookie on logout.
- 2026-09-15: RF-01 is validated in the shared responsive web application without generating native
  projects. Validation covers successful registration, required fields, mismatched passwords,
  duplicate identities, unexpected failure, programmatic form labels, and basic keyboard operation.

## Proposed scope

### In scope

- Responsive, accessible registration UI for email, alias, password, and password confirmation.
- Client-side required-field, format, policy, and password-match feedback before submission.
- Authoritative server-side validation and a stable safe error contract.
- First account table/model and Alembic migration with concurrency-safe canonical email and alias
  uniqueness.
- Secure password hashing and exclusion of credentials from logs and responses.
- A transactional registration endpoint and a confirmed minimal success transition.
- Minimal session creation after successful registration.
- Automated frontend/backend tests plus manual responsive and accessibility validation.

### Out of scope

- Email verification and outbound email infrastructure.
- Forgotten-password recovery or authenticated password change.
- Manual login and logout screens beyond any minimal post-registration session transition explicitly
  accepted for RF-01.
- Profile biography, photo, social links, alias editing, or public profile pages owned by RF-03.
- Native iOS/Android project generation, signing, or store distribution.
- Social login, contact import, telephone collection, legal-name collection, CAPTCHA, custom
  throttling/rate-limiting infrastructure, explicit registration idempotency keys, hosted identity
  providers, separate account role/status machinery, and broad moderation tooling.
- Common, expected, or compromised-password blocklist checks and third-party password reputation
  services.
- Account deletion and full retention-policy implementation; the schema must not prevent those later
  decisions.

## Validation outline

- Frontend tests for required fields, email/alias/password policy feedback, mismatched confirmation,
  pending state, safe input retention, duplicate handling, network failure, success transition, and
  prevention of repeated submission.
- Backend service/API tests for valid creation, canonicalisation, malformed runtime payloads,
  password length/encoding policy violations, duplicate email/alias, generic email-conflict
  disclosure, rollback on failure, and omission of secret values from responses.
- Persistence tests against PostgreSQL semantics for case-insensitive uniqueness and concurrent
  attempts; migration upgrade/downgrade or rollback validation as appropriate.
- Security checks that stored values are password hashes, plaintext/confirmation values are never
  persisted or logged, and any session cookie/token follows the confirmed transport rules.
- Manual checks on narrow and wide viewports, keyboard-only flow, password manager/autocomplete,
  focus/error announcement, loading/retry behaviour, and refresh/navigation after success.
- Run the repository's established frontend and backend format, lint, type-check, test, build, and
  migration validation commands once the plan is approved and implemented.

## Readiness checklist

- [x] Desired outcome is unambiguous.
- [x] Scope and exclusions are confirmed.
- [x] Code impact was inspected.
- [x] Dependencies and conflicts are resolved.
- [x] Technical approach is selected.
- [x] UX and failure states are confirmed where applicable.
- [x] Security, privacy, retention, and abuse implications are resolved where applicable.
- [x] Data migration and operational implications are resolved where applicable.
- [x] Test and manual validation expectations are agreed.
- [x] No material question remains.
- [x] Product owner explicitly approved plan finalisation.

## Post-implementation product review

- 2026-09-16: The product owner rejected the registration-first unauthenticated entry and the current
  dark, visually heavy styling.
- RF-01's account API, persistence, validation, password hashing, and session foundation remain valid.
- RF-02 will make login the default entry, expose registration as a secondary action, and replace the
  auth presentation with the approved shared visual foundation.
