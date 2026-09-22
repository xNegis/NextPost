# RF-01 - Create an account - Implementation Plan

## Status

`Ready for implementation`

## Source ticket

- Trello title: `RF-01 · Crear una cuenta`
- Trello URL: https://trello.com/c/SGj0fby6/2-rf-01-crear-una-cuenta
- Trello list at intake: `Fase 1`
- Snapshot captured on: `2026-09-15T18:02:58+02:00`
- Grooming notes: `harness/grooming/RF-01-grooming.md`

## Objective

Let a visitor create the minimum NextPost account needed to participate in the product. Registration
collects only email, public alias, password, and password confirmation. A successful registration
immediately signs the new account in and shows a small authenticated welcome state.

## Context and current behaviour

- The frontend is one React 19 and TypeScript Vite application shared by the future web, iOS, and
  Android clients. It currently shows only stack readiness and has no router, form framework,
  authentication state, or component library.
- The backend is FastAPI with SQLAlchemy session management and Alembic. It currently exposes only
  health/readiness endpoints and has no product models.
- PostgreSQL 18 is the relational system of record. The initial Alembic revision intentionally has no
  tables, so this feature creates the first product table.
- DEC-008 selects first-party credentials: Argon2id password hashing and a signed `HttpOnly` browser
  cookie with no server-side session table.
- RF-02 will later add manual login/logout using the same cookie mechanism. RF-03 will own profile
  editing, including any future alias-change behaviour.
- Email verification and password recovery/change are explicitly outside the MVP.

## Scope

### In scope

- A responsive registration form with email, alias, password, and password-confirmation fields.
- Client validation before submission and authoritative server validation.
- One account persistence model and Alembic migration.
- Case-insensitive uniqueness for canonical email and alias, including concurrent requests.
- Argon2id password hashing; plaintext passwords are never persisted, returned, or logged.
- `POST /api/accounts` to create an account and establish the signed cookie session.
- `GET /api/session` as the minimum read endpoint needed to restore the authenticated welcome state
  after a page reload.
- A small welcome state for the authenticated account.
- Focused frontend and backend automated tests and responsive/manual checks.

### Out of scope

- Email verification, outbound email, password recovery, and password change.
- Manual login and logout UI, which belong to RF-02.
- Profile biography, photo, social links, alias editing, and public profile pages, which belong to
  RF-03.
- Social login, hosted identity providers, access/refresh token systems, and server-side session
  tables.
- CAPTCHA, custom rate-limiting infrastructure, explicit registration idempotency keys, and password
  reputation/blocklist services.
- Account roles/status machinery, moderation, account deletion, and broad retention policy.
- Native project generation, signing, native-specific authentication transport, or app-store work.

## User experience

1. On initial load, the client checks `GET /api/session`.
2. While that check is pending, show a neutral loading state rather than briefly flashing the
   registration form.
3. An unauthenticated visitor sees one registration form containing email, alias, password, confirm
   password, and a submit action.
4. Labels, requirements, and validation errors are programmatically associated with their fields.
   Required, email-format, alias-format, password-length, and password-match errors appear before a
   request is sent.
5. Password fields use `autocomplete="new-password"`, allow paste and password-manager autofill, and
   each has an accessible show/hide control.
6. Submission is disabled while the request is pending so an ordinary double click cannot send
   repeated requests.
7. Safe correctable failures preserve email and alias. Passwords remain only in transient React state
   for a correctable failure and are cleared on successful registration or when the registration view
   is left. No registration value is written to local storage or session storage.
8. An unavailable alias is identified beside the alias field. A duplicate email uses this exact
   non-enumerating form message: `No se ha podido crear la cuenta con esos datos. Revísalos o inicia
   sesión si ya tienes una cuenta`.
9. Network or unexpected server failure shows a generic retryable message, retains safe form state,
   and restores the submit action.
10. Success changes the current view to a minimal authenticated welcome state that identifies the
    chosen alias and states that the account is ready. It does not invent feed or consultation
    content.
11. Reloading the page with a valid cookie restores the welcome state. An absent, invalid, or
    unusable cookie returns the visitor to registration without exposing internal details.

## Functional requirements

### FR-1 - Registration data

Registration accepts only email, alias, and password at the API boundary. Password confirmation is a
client-side entry check and is neither transmitted nor persisted. The UI requests no legal name,
telephone number, contact access, or terms/privacy consent.

### FR-2 - Email rules

Trim surrounding whitespace and canonicalise the complete email case-insensitively. Do not apply
provider-specific transformations such as removing dots or `+tags`. Validate it as an email address
on both client and server. Persist the canonical value needed for later login and enforce a unique
database constraint on it.

### FR-3 - Alias rules

Trim surrounding whitespace. Accept 3-30 ASCII letters, digits, underscores, and dots, with at least
one letter or digit. Preserve the submitted casing for display, store a case-folded canonical value,
and enforce uniqueness on that canonical value. Reject `admin`, `support`, and `nextpost`
case-insensitively. Alias editing and general name moderation are not part of RF-01.

### FR-4 - Password rules

Accept 15-128 Unicode code points, including spaces and Unicode characters. Do not trim, truncate, or
impose uppercase/lowercase/digit/symbol composition rules. Hash the complete password with Argon2id
before persistence. Do not add common/compromised-password checks in this MVP increment.

### FR-5 - Safe uniqueness behaviour

Email and alias uniqueness are case-insensitive and protected by database constraints, not only
pre-flight queries. A duplicate alias may be disclosed as unavailable because it is a public
identifier. A duplicate email must use the generic registration-unavailable contract and must not
confirm that another account owns the address.

### FR-6 - Account creation transaction

Create exactly one account in one transaction. A validation, hashing, constraint, or persistence
failure must not leave a partial account. Database uniqueness is sufficient for repeated and
concurrent submissions; do not introduce an idempotency subsystem.

### FR-7 - Automatic session

After the transaction succeeds, put only the account identifier in a signed `HttpOnly` cookie. Use
`SameSite=Lax`; use a browser-session cookie rather than persistent remember-me behaviour; and set
the Secure attribute outside local development. The signing secret comes from configuration, has a
clearly local-only development default, and must not be exposed to frontend code or logs.

### FR-8 - Session restoration

`GET /api/session` validates the signed cookie and loads the referenced account. It returns only the
minimum welcome data (`id` and display alias). Missing/invalid cookies and missing accounts are
treated as unauthenticated without leaking signing or persistence details.

## Technical approach

Implement the feature inside the existing stack without adding application layers or infrastructure
that the current size does not need.

### Affected areas

- Frontend: replace the readiness-only screen in `frontend/src/App.tsx` with initial-session,
  registration, and welcome states; add typed API functions/runtime guards in `frontend/src/api.ts`;
  extend `frontend/src/styles.css`; add focused form/API tests and only the test dependencies needed
  to render and interact with React components.
- Backend/application: add a small accounts router, request/response schemas, registration function,
  password-hashing helper, and cookie-session configuration; wire the router and Starlette session
  middleware into `backend/app/main.py`.
- Domain/data model: add the SQLAlchemy account model and ensure metadata is imported by Alembic.
- Configuration/deployment: add a session signing secret setting and safe local Compose/example value;
  production must be able to provide a different secret. Frontend credentialed fetches must work with
  the existing explicit CORS origins.
- Documentation: update local configuration/run instructions only where the new secret or behaviour
  changes them.

### Data and migration requirements

Add one `accounts` table in a new Alembic revision after `20260915_0001` with a generated UUID primary
key, canonical unique email, display alias, canonical unique alias, Argon2id password hash, and
timezone-aware creation timestamp. Use explicit unique constraint names so violations can map safely
to duplicate-email or duplicate-alias behaviour. The downgrade removes only this new table. Do not
add profile, role, status, verification, recovery, or session tables.

### API and integration requirements

- `POST /api/accounts`
  - Body: `{ "email": string, "alias": string, "password": string }`.
  - Success: HTTP 201, set the session cookie, and return `{ "id": string, "alias": string }`.
  - Invalid input: HTTP 422 with stable field information safe for the UI.
  - Duplicate alias: HTTP 409 with a stable `alias_unavailable` code.
  - Duplicate email: HTTP 409 with a stable generic `registration_unavailable` code and no email
    ownership detail.
  - Unexpected failure: an ordinary generic server error with no internal details.
- `GET /api/session`
  - Authenticated: HTTP 200 with `{ "authenticated": true, "account": { "id", "alias" } }`.
  - Unauthenticated: HTTP 401 with a stable unauthenticated response.
- Frontend requests that need the cookie use `credentials: "include"`. CORS remains restricted to
  configured origins with credentials enabled.

### Security and privacy

- Use Argon2id through a maintained Python password-hashing package; never implement the algorithm.
- Never log request bodies, plaintext passwords, password confirmation, password hashes, the signing
  secret, or cookie contents.
- Cookie signing prevents client modification but does not encrypt data, so store only the account ID
  in it.
- Configure `HttpOnly`, `SameSite=Lax`, path `/`, and environment-appropriate Secure behaviour.
- Do not accept role, status, verification, or other privileged account attributes in the request.
- Reject malformed runtime input on the server even when the React client already validated it.

## Implementation sequence

1. Add backend dependencies and configuration for Argon2id and signed cookie sessions.
2. Add the account model, Alembic metadata import, and the new account-table migration.
3. Implement canonicalisation, validation, password hashing, transactional registration, and safe
   uniqueness-error mapping.
4. Add the accounts/session API contracts and wire the router and middleware into the application.
5. Add backend tests covering success, validation, password storage, uniqueness, privacy, session
   creation/restoration, and rollback behaviour.
6. Add typed frontend registration/session API calls and runtime response validation.
7. Implement the registration and welcome UI states, pending/error behaviour, password controls, and
   responsive/accessibility styling.
8. Add frontend tests for the approved user flows and failures.
9. Update example configuration and documentation, then run all applicable validation commands.

## Validation strategy

### Automated tests

- Backend: valid creation; canonical email/alias persistence; 15/128-character boundaries; Unicode
  password; reserved/invalid alias; duplicate alias; generic duplicate email; no plaintext password;
  successful cookie creation; missing/invalid session; database rollback; malformed payload.
- Frontend: unauthenticated initial state; required and malformed fields; mismatched passwords; no
  request on client validation failure; pending submission; alias/email conflict presentation;
  generic retryable failure; safe value retention; successful welcome; restored welcome session;
  password show/hide and form labelling.
- Existing health/readiness behaviour remains covered against regression.

### Manual validation

- Check the flow at narrow mobile and ordinary desktop widths in the web application.
- Complete registration with keyboard only and confirm labels, focus, visible errors, password
  visibility buttons, paste, and autofill semantics.
- Confirm a successful registration remains authenticated after browser reload.
- If Docker is available, apply the migration and exercise the complete frontend/API/PostgreSQL flow.
  If the engine remains unavailable, report this check as pending rather than claiming it.

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
Pop-Location
docker compose config
```

When Docker is available:

```powershell
docker compose up --build
```

## Acceptance criteria

- [ ] Valid inputs create exactly one account.
- [ ] Registration collects only email, alias, password, and client-only confirmation.
- [ ] Client and server enforce the approved validation rules.
- [ ] Confirmation mismatch prevents submission and confirmation is never transmitted.
- [ ] Passwords are stored only as Argon2id hashes.
- [ ] Email and alias uniqueness are case-insensitive and concurrency-safe.
- [ ] Alias conflict is actionable; email conflict does not disclose account ownership.
- [ ] Correctable errors preserve only approved transient values and leave the form usable.
- [ ] Success creates the signed `HttpOnly` cookie and shows the welcome state.
- [ ] Reloading with a valid cookie restores the authenticated welcome state.
- [ ] Unexpected failure is retryable and leaves no partial or duplicate account.
- [ ] The responsive web flow has programmatic labels and basic keyboard support.
- [ ] Existing behaviour and all applicable quality commands pass.

## Dependencies and ordering

- Depends on the implemented monorepo foundation and accepted DEC-004, DEC-005, DEC-006, and DEC-008.
- Establishes the credential/cookie contract RF-02 reuses and the alias identity RF-03 may later edit.
- Does not depend on email verification, password recovery, native projects, or later product features.

## Risks and mitigations

- Concurrent duplicates: named database uniqueness constraints are the final guarantee.
- Email enumeration: use only the generic approved error contract.
- Secret leakage: hash before persistence and exclude secrets/request bodies from logs and responses.
- Readable signed cookie: store only the account ID and apply the accepted cookie attributes.
- No per-session server revocation: accepted for this MVP; RF-02 clears the cookie on logout.
- Docker may remain unavailable: run all non-container checks and report the smoke test accurately.

## Harness handoff notes

- The whole repository currently appears as untracked bootstrap work. Preserve every existing file.
- Do not commit, push, deploy, modify Trello, generate native projects, or launch another agent.
- Keep the implementation deliberately small and do not add out-of-scope mechanisms.
- Update project state only when supported by validation evidence.

## Resolved grooming decisions

- Registration collects only email, alias, password, and client-side confirmation.
- Accounts are active immediately; success signs in and shows a minimal welcome state.
- Email is canonicalised case-insensitively without provider-specific transformations.
- Alias follows the approved 3-30 character, uniqueness, display-casing, and reserved-name rules.
- Duplicate alias is explicit; duplicate email uses the approved non-enumerating message.
- Passwords are 15-128 Unicode code points with no composition or blocklist rule.
- Password inputs support password managers, paste, and accessible show/hide controls.
- Argon2id and a minimal signed `HttpOnly` cookie are the credential/session mechanisms.
- Validation targets the responsive shared web app; speculative infrastructure is out of scope.

## Remaining questions

None
