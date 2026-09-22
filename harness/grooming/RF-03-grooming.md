# RF-03 - Crear y editar el perfil - Grooming

## Status

`Grooming - questions open`

## Trello snapshot

- Title: `RF-03 · Crear y editar el perfil`
- URL: https://trello.com/c/WAVz9fNb/9-rf-03-crear-y-editar-el-perfil
- Board: `APP - NextPost`
- List: `Fase 1`
- Labels: None
- Members: None
- Due date: None
- Card completion: Not complete
- Checklists: None
- Comments: None
- Captured on: `2026-09-16T15:53:29+02:00`
- Last Trello activity at intake: `2026-09-15T09:31:53.463Z`

### Description and acceptance criteria at intake

**Historia de usuario**

Como usuario, quiero disponer de un perfil reconocible para participar y que otras personas
identifiquen mi criterio.

**Comportamiento y criterios de aceptación**

- Puedo consultar mi perfil

Intake note: the card title says that the profile can be created and edited, and the story says that
other people should recognise the user, but the only explicit acceptance criterion covers viewing
one's own profile. The card does not define editable fields, visibility to other accounts, entry
points, or profile-image behaviour. Those are material grooming questions rather than accepted
requirements.

## Intended outcome

Give an authenticated NextPost account a private `My profile` view where its owner can see the
account email and nickname (the existing alias). Both fields are read-only in this increment. Add the
first small shared authenticated navigation component, including a profile action, and make its
layout deliberately adaptive and usable on mobile and desktop without creating public profiles or a
broad application shell prematurely.

## Current code findings

- RF-01 created an `accounts` table containing UUID `id`, canonical email, display `alias`, canonical
  alias, password hash, and creation timestamp. There is no separate profile entity and no optional
  profile metadata.
- Registration already creates the public alias. It is 3-30 characters, permits ASCII letters,
  numbers, periods, and underscores, requires at least one letter or number, reserves `admin`,
  `support`, and `nextpost`, preserves chosen casing, and enforces case-insensitive uniqueness in the
  database.
- RF-01 explicitly assigned alias editing to RF-03. No service or endpoint can currently update an
  account or alias.
- The authenticated API surface returns only an account summary with `id` and `alias`. It never
  returns email, password hashes, or other private account data.
- The frontend has no router, persistent application shell, profile component, settings view, or
  general navigation. `App.tsx` coordinates session checking, sign-in, registration, a minimal
  authenticated welcome card, and sign-out through local component state.
- The existing responsive CSS preserves safe-area padding and was manually validated at narrow and
  desktop widths, but it covers only the authentication cards. RF-03 is the first feature that must
  establish responsive authenticated navigation as a reusable product boundary.
- RF-02 established English product copy and a light, restrained visual foundation. RF-03 should
  reuse it rather than introduce a separate design language.
- No private file storage, image processing, image metadata removal, moderation pipeline,
  background worker, or deletion job exists. Adding a profile photograph now would create storage,
  privacy, retention, abuse, validation, and operational scope ahead of the planned consultation
  image work.
- The account UUID is the stable identity. The current alias is not used as a database key or route,
  so allowing an alias change need not change ownership or session identity.
- The repository remains entirely untracked in Git. Existing bootstrap, RF-01, and RF-02 files are
  user work and must be preserved.

## Dependencies and conflicts

- RF-03 depends on RF-01's account, alias validation, case-insensitive uniqueness, and signed-cookie
  session, and on RF-02's authenticated entry point and shared visual foundation.
- RF-23 later owns the public, evidence-based criterion-coincidence indicator. RF-03 must not invent
  a score, expertise level, rank, voting history, or fabricated social proof before the underlying
  consultation and voting data exists.
- RF-24 later owns following and follower relationships. RF-03 may leave an appropriate UI boundary
  but should not add follow counts or actions early.
- RF-09 states that link-only consultations must not appear on other people's profiles. RF-03 must
  not introduce a consultation list that bypasses future audience rules.
- RF-29 and RF-30 later make profiles boundaries for blocking and reporting. If RF-03 exposes other
  accounts' profiles now, access and abuse behaviour would need to be settled here rather than
  assumed.
- RF-34 will remove a deleted account's profile from public exposure, and RF-35 will include profile
  data in an account export. New profile fields must therefore have explicit ownership and deletion
  semantics even though those later workflows are outside this increment.
- DEC-004 through DEC-006 keep this work within the shared React client, FastAPI, SQLAlchemy,
  Alembic, and PostgreSQL. DEC-008 requires the existing account-ID cookie session. DEC-009 requires
  English user-facing copy.

## Candidate approach

### Accepted direction so far

Build a deliberately small, read-only owner-profile increment:

1. Registration already creates the minimum profile because every account has a required nickname;
   do not add a second onboarding or empty-profile lifecycle.
2. Add a shared authenticated navigation component that works across mobile and desktop and includes
   `Home` and `Profile` destinations. Present it as a compact top navigation on wider screens and a
   fixed, safe-area-aware bottom navigation on narrow/mobile screens.
3. Add an authenticated `My profile` view showing the owner's email and nickname.
4. Keep email and nickname read-only in RF-03. No edit request, save flow, alias mutation, or new
   profile field is needed despite the broader Trello title.
5. Keep the profile owner-only. Email is private account data and must never be exposed through a
   future public-profile response.
6. Read the private profile through an authenticated dedicated API response. Do not broaden the
   account summary returned throughout the session/authentication flow with email unnecessarily.
7. Reuse the existing account table and stable account UUID. No schema migration or separate profile
   entity is needed for these already persisted fields.
8. Defer uploaded avatars and all additional profile data. The profile icon is navigation chrome,
   not a user-uploaded avatar.
9. Keep authenticated navigation in local application state for now. The authenticated default is
   `Home`; the active destination remains visibly identified. Do not add a router for these two
   non-shareable private views.
10. Place `Sign out` in `My profile`, retaining RF-02's pending and retryable failure behaviour.
11. Load the private data through `GET /api/profile` when the user enters `Profile`. Return only
    `email` and `nickname` (mapped from the existing internal alias); do not add email to the general
    session/account summary or browser persistence.
12. Treat a profile `401` as an expired/invalid session and return to sign-in. Treat network or
    unexpected server failures as profile-local, retryable unavailability while keeping navigation
    usable. Clear private profile state on sign-out.

### Alternatives and trade-offs

- **Accepted for RF-03 — read-only email and nickname:** smallest coherent private account-profile
  view, uses existing data, and adds no migration or user-generated content boundary.
- **Editable alias or optional bio:** explicitly deferred. Either would add mutation, validation,
  conflict, moderation, and failure behaviour not required by the accepted first profile view.
- **Alias plus uploaded avatar:** visually strongest identity but disproportionately expands this
  early ticket into image security, privacy, storage, lifecycle, and abuse work. Not recommended
  before those policies and facilities exist.
- **Public profiles in RF-03:** aligns directly with “other people identify my criterion,” but there
  is not yet a discovery flow, consultation/voting data, block enforcement, report handling, or the
  RF-23 criterion metric. An owner-only vertical slice is safer unless public viewing is essential to
  the product owner's definition of done.

## Questions

### Open

#### Product boundary and visibility

- None.

#### Shared navigation

- None.

#### UX and failures

- None.

#### Security, privacy, lifecycle, and abuse

- None.

#### Validation expectations

- None.

### Resolved

- 2026-09-16: The product owner explicitly selected RF-03 for grooming.
- 2026-09-16: The complete Trello card was consumed read-only from the configured `APP - NextPost`
  board. No Trello mutation was performed.
- 2026-09-16: RF-01 already creates the minimum account identity and explicitly assigns alias editing
  to RF-03.
- 2026-09-16: Accepted project decisions require English product copy and reuse of the existing
  React/FastAPI/PostgreSQL and signed-cookie session foundation.
- 2026-09-16: RF-03 is an owner-only `My profile` increment; viewing other users' profiles is not part
  of this ticket.
- 2026-09-16: Registration already creates the minimum profile. RF-03 adds no separate profile setup
  or onboarding step.
- 2026-09-16: `My profile` displays the authenticated owner's email and nickname (the existing
  alias). Both are read-only in this increment.
- 2026-09-16: RF-03 adds the first small shared authenticated navigation component with a profile
  icon/action, designed and validated for both mobile and desktop.
- 2026-09-16: No additional profile field or uploaded profile image is included at this stage.
- 2026-09-16: The shared authenticated navigation initially contains `Home` and `Profile`. `Home`
  shows the existing welcome state and remains the default after registration, sign-in, or session
  restoration; no feed or consultation destination is invented.
- 2026-09-16: The same semantic navigation component is a compact top bar on wider screens and a
  fixed, thumb-reachable bottom bar on narrow/mobile screens. It respects safe-area insets, does not
  obstruct content, and gives both destinations an icon, visible text label, keyboard focus, and
  active state.
- 2026-09-16: Navigation uses local authenticated application state. RF-03 does not add a router or
  deep links for its two private views.
- 2026-09-16: `Sign out` moves from the temporary welcome card into `My profile` and preserves the
  existing pending, success, and retryable failure behaviour.
- 2026-09-16: `GET /api/profile` is the dedicated authenticated private-profile read. Its successful
  response contains only `email` and `nickname`, with nickname mapped from the existing internal
  alias. Email is not added to the general session/account summary.
- 2026-09-16: Email and nickname are presented as clearly labelled read-only details rather than
  disabled form controls. The profile states that only the owner can see the email.
- 2026-09-16: Private profile data remains only in transient application memory and is cleared on
  sign-out. It is not written to local/session storage, logs, URLs, or public-profile contracts.
- 2026-09-16: A profile `401` returns the application to sign-in because the session is no longer
  usable. Network and unexpected server failures stay local to the profile with a retry action and
  usable navigation; stale or invented email data is not shown.
- 2026-09-16: RF-03 adds no persistence, migration, uploaded content, editing endpoint, or new
  retention/moderation surface.
- 2026-09-16: The profile uses the English title `My profile`, labels `Email` and `Nickname`, and the
  privacy explanation `Only you can see this email.` The current welcome content remains `Home`.
- 2026-09-16: Navigation icons are repository-owned SVGs without a new icon dependency. Visible text
  labels, semantic navigation, `aria-current`, visible keyboard focus, and at least 44 by 44 CSS pixel
  touch targets are required.
- 2026-09-16: Responsive switching is based on layout/content rather than device detection.
  Validation covers 320 px, representative mobile, tablet, and desktop widths; practical landscape
  orientation; safe areas; 200% zoom; keyboard use; long values; and absence of obstruction or
  horizontal overflow.
- 2026-09-16: The product owner confirmed all remaining RF-03 decisions and explicitly approved plan
  finalisation and implementation.

## Proposed scope

### In scope

- A small shared authenticated navigation component containing the accepted destinations and profile
  icon/action, responsive across narrow mobile and desktop layouts.
- An authenticated owner-only `My profile` view reachable from that navigation.
- Read-only display of the account email and nickname/alias as labelled account details.
- Server-authoritative authentication/ownership and a strict private-profile response schema that
  excludes password hashes, canonical/internal fields, and session internals.
- Profile loading, unavailable, retry, navigation-active, and sign-out states as finally confirmed.
- Responsive, accessible UI in English using the RF-02 visual foundation.
- Automated backend/frontend tests and focused manual validation.

### Out of scope

- Editing email, nickname, password, roles, account status, or the session mechanism.
- Additional profile fields such as bio, display/legal name, location, links, or join date.
- Uploaded profile images unless the product owner explicitly expands the ticket and resolves their
  complete storage, privacy, moderation, retention, and deletion boundary.
- Followers/following, private messaging, contact import, social-account connections, badges,
  rankings, inferred expertise, or fabricated activity.
- Criterion coincidence metrics owned by RF-23.
- Consultation lists or photos on profiles before audience and lifecycle rules exist.
- Blocking, reporting, moderation administration, data export, and account deletion workflows owned
  by later tickets; RF-03 must remain compatible with them.
- Native project generation, router adoption, broad application navigation, component libraries, or
  unrelated design-system expansion unless an accepted scope decision makes one necessary.

## Validation outline

- Backend service/API tests for authentication, owner loading, strict private response fields,
  unauthenticated rejection, and representative unexpected failures. No migration test is needed.
- Frontend API tests for credential inclusion, runtime response validation, and network/server
  failures.
- Frontend UI tests for reaching the profile, viewing current read-only values, profile loading and
  retry, switching destinations, active navigation state, and sign-out regressions.
- Security/privacy checks that email, password hash, session contents, and internal canonical fields
  never appear in profile responses or UI, and that user text renders without HTML execution.
- Manual checks at 320 px and representative mobile, tablet, and desktop widths; portrait and
  landscape where practical; safe-area behaviour; touch target sizing; keyboard-only use; visible
  focus and active state; long email/nickname wrapping; no content obstruction or horizontal
  overflow.
- Run the repository's existing backend format/lint/type/test suite, frontend test/format/lint/type/
  build/audit suite, Compose configuration check, and the PostgreSQL-backed smoke flow when the final
  plan is approved and implemented.

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
