# Project State

## Current phase

RF-03 implementation is in progress; RF-07 is in implementation review and unblocks RF-06's
real-photo path.

## Current status

- `RF-07 · Subir y comparar varias fotografías` was selected, groomed and approved as the real-photo
  prerequisite for RF-06. The approved OpenCode `opencode-go/deepseek-v4-pro` harness implemented
  its private upload sessions, bounded normalization, owner-only media reads, renewable leases,
  durable deletion and reusable React photo component on 2026-09-22. Independent review corrected
  client limit/session cleanup and superseded-retry behavior, RF-10 byte-presence validation,
  color-profile conversion, cleanup transaction ordering, concurrent cleanup locking and the race
  between orphan sweeping and an uncommitted upload. Automated evidence is green: 110 backend tests
  including three PostgreSQL concurrency tests, 88 frontend tests, formatting, lint, strict typing,
  production build, dependency audit, fresh migration upgrade/downgrade/upgrade, Docker builds and a
  live private-volume/API smoke for JPEG, PNG, WebP and HEIF/HEIC decoding. Container restart also
  proved startup abandonment and physical deletion of an expired session. The restricted cleanup
  command reports no overdue deletions. RF-07 remains in implementation review because the approved
  plan records real-iPhone/TestFlight behavior and final integrated composer layout as manual gates;
  those require the future signed iOS environment and RF-06 integration. Published-photo backup
  policy remains full RF-37 scope.
- `RF-06 · Preparar una consulta` was consumed read-only from the configured Trello board on
  2026-09-22 into `harness/grooming/RF-06-grooming.md`. Repository inspection found no consultation,
  upload, image storage, or publication implementation. The RF-06 boundary and dependency order
  are confirmed. RF-07 plus the minimum RF-37 protection now has an approved implementation plan;
  RF-08/RF-09/RF-10 integration contracts remain open, and no RF-06 implementation plan is
  approved. The product
  owner confirmed an integrated complete-flow phase-2 finish line through final choice and private
  voter feedback (DEC-010). `harness/grooming/PHASE-2-scope.md` inventories all 40 open board cards
  and records the agreed high-level grouping. Registered accounts may vote without email verification
  in phase 2 (DEC-011); invitation-only rollout is possible but not a feature-scope gate. Per-ticket
  specifications and safety scope remain open. Preparation is temporary and non-recoverable
  (DEC-012); publishable photo count starts at configurable minimum 2 and maximum 10 (DEC-013).
  The first delivery targets web and invited iOS TestFlight (DEC-014); permanent app ID/signing and
  real-device validation remain to be planned. Direct iPhone gallery selection without conversion is
  accepted, including HEIC/HEIF input support (DEC-015). FormCadence has code and automated tests for
  those formats, but physical-iPhone proof is not recorded in its project state. The owner chose to
  retain only normalized consultation images, not original uploads (DEC-016); HEIC/HEIF remains a
  bounded decoder requirement pending build/device validation. Consultations have no automatic
  expiry in phase 2; only the author voluntarily closes an open consultation (DEC-017). RF-11's
  expiry criteria are deferred, while abandonment and post-closure cleanup still need a policy.
  Published content is immutable and at most three consultations may be open per author from the
  shared restricted configuration source (DEC-018). The community feed is chronological; voting is
  optional and final after confirmation, and aggregate results belong to the author only (DEC-019).
  Public profile pages, user-facing block/report/moderation, broad abuse controls, and versioned
  service-rule acceptance were deferred from the first MVP (DEC-020). The owner then clarified that
  finalization atomically declares one, several, or no photos, closes the consultation, and removes
  stored images without a 30-day buffer; open consultations remain open until action (DEC-017/021).
  Public images require an account, Private images require account plus link; a restricted
  administrator can manually remove a consultation, and the composer reminds authors to have photo
  rights (DEC-022). Explicit Skip, voter comments, overall coincidence metrics, and varied photo
  ordering are deferred (DEC-019). Finalized consultations retain only minimum non-image outcome
  records for private history/statistics while the relevant participant accounts exist; deleting an
  unfinalized consultation produces no coincidence outcome (DEC-023). Image-deletion failure
  handling and operational storage/backup design still require plan-level resolution.
- The monorepo foundation contains a React/TypeScript/Vite frontend, FastAPI backend, Alembic
  baseline, PostgreSQL Compose service, and production container definitions.
- RF-01 now provides responsive account registration, validation, Argon2id password storage, safe
  case-insensitive uniqueness, automatic signed-cookie authentication, session restoration, and a
  minimal welcome state.
- Combined RF-01/RF-02 frontend validation passes: 48 tests across 5 files, formatting, linting, type
  checking, production build, and dependency audit.
- Combined RF-01/RF-02 backend validation passes: 34 tests, formatting, linting, and strict type
  checking.
- Docker Compose configuration and the full PostgreSQL-backed container smoke test pass. Offline
  Alembic SQL generation for PostgreSQL also passes.
- The `APP - NextPost` Trello board is connected and available as the product backlog.
- At the owner's explicit request on 2026-09-22, Trello's `Fase 2` list was organised into the 16
  agreed core cards, ordered from RF-06 preparation through RF-37 image deletion. Their descriptions
  were aligned with DEC-011–023; RF-11/18/19/20/37 titles were clarified. RF-17/32/36/40 remain
  in `Funcionalidades` with notes identifying deferred full scope and narrow MVP dependencies.
  Verified board totals are 3 `Fase 1`, 16 `Fase 2`, 19 `Funcionalidades`, and 2 `Descartadas del MVP`.
  No card completion flags were changed; Trello organisation does not change implementation status.
- The persistent Trello -> grooming -> implementation plan -> harness workflow is configured.
- `RF-03 · Crear y editar el perfil` has been consumed read-only from Trello into
  `harness/grooming/RF-03-grooming.md`. The accepted direction is an owner-only, read-only profile
  showing email and nickname plus the first shared authenticated navigation component, responsive
  across mobile and desktop. The accepted navigation has `Home` and `Profile`, adapts from a desktop
  top bar to a mobile bottom bar, uses local state, and places sign-out in the profile. Remaining
  presentation, privacy, error, and validation details are confirmed. The product owner approved
  finalisation and implementation on 2026-09-16.
- `harness/features/RF-03-Implementation-plan.md` is the approved self-contained implementation
  contract and is marked `Ready for implementation`.
- `RF-01 · Crear una cuenta` has been consumed into repository-owned grooming notes from the
  configured Trello board.
- `harness/features/RF-01-Implementation-plan.md` was implemented by the explicitly authorised
  OpenCode `opencode-go/deepseek-v4-pro` harness using variant `high`.
- Independent review corrected service-level email canonicalisation, expanded session/UI restoration
  tests, and fixed a narrow-layout grid constraint. No commit, push, deploy, or Trello mutation was
  performed.
- Product-owner review rejected RF-01's registration-first entry and dark, visually heavy styling.
  RF-02 retains its backend/account foundation while superseding that presentation with the accepted
  sign-in-first flow and light visual base.
- `RF-02 · Iniciar y cerrar sesión` has been consumed from Trello into
  `harness/grooming/RF-02-grooming.md` to introduce login-first navigation, logout, and the shared
  minimal visual foundation.
- The product owner approved RF-02 finalisation on 2026-09-16. Its self-contained implementation
  contract is `harness/features/RF-02-Implementation-plan.md`, marked `Ready for implementation`.
- RF-02 was implemented by the explicitly authorised OpenCode `opencode-go/deepseek-v4-pro` harness:
  email/password sign-in and sign-out over the existing signed `HttpOnly` cookie session, sign-in as
  the default unauthenticated view, registration reached through a visible secondary action, and a
  light neutral shared visual foundation with English product copy.
- Independent review found and corrected one session-safety edge case: malformed sign-in requests now
  clear any pre-existing authenticated session. A focused regression test raises the backend total to
  34 tests.
- Independent visual review of real desktop and narrow captures confirms the light neutral login,
  restrained typography, single accent, modest border/shadow, and absence of decorative excess.
- The full Docker Compose/PostgreSQL smoke test passes: the stack builds and becomes healthy, and a
  live flow verifies registration, restoration, malformed-login session clearing, case-insensitive
  sign-in, sign-out, final unauthenticated state, and frontend serving.

## Next gate

The RF-06 Trello description was rechecked on 2026-09-22 after its alignment with accepted phase-2
decisions. The grooming file preserves the original and current snapshots. The product owner has
confirmed the RF-06 composer boundary and the order of defining upload and cleanup contracts first.
No RF-06 implementation plan is approved.

RF-07's automatable implementation and independent review are complete. Keep its external
real-iPhone/TestFlight and RF-06 integrated-composer checks visible during phase-2 validation. Settle
the RF-08/RF-09/RF-10 integration contracts before finalising RF-06. The owner confirmed that the composer initially has no
audience selected and requires an explicit Public/Private choice (DEC-024). A concrete F06
implementation sequence and validation design were added to its grooming notes at the owner's
request. Separately, review the
RF-03 implementation against its approved acceptance
criteria and validation requirements before claiming RF-03 complete.

## Ticket lifecycle values

Use one of these values when tracking an active ticket:

- `Not consumed`
- `Grooming - questions open`
- `Grooming - awaiting product-owner confirmation`
- `Ready for implementation`
- `Implementation in progress`
- `Implementation review`
- `Completed and validated`
- `Blocked`
- `Deferred`

## Active ticket

- Ticket: `RF-07 · Subir y comparar varias fotografías`
- Trello: https://trello.com/c/x8VPrsF9/3-rf-07-subir-y-comparar-varias-fotograf%C3%ADas
- Lifecycle: `Implementation review`
- Grooming notes: `harness/grooming/RF-07-grooming.md`
- Approved plan: `harness/features/RF-07-Implementation-plan.md`

## Related ticket in grooming

- Ticket: `RF-06 · Preparar una consulta`
- Trello: https://trello.com/c/kLphAXQ1/10-rf-06-preparar-una-consulta
- Lifecycle: `Grooming - questions open`
- Grooming notes: `harness/grooming/RF-06-grooming.md`
- Approved plan: None

## Other in-progress ticket

- Ticket: `RF-03 · Crear y editar el perfil`
- Trello: https://trello.com/c/WAVz9fNb/9-rf-03-crear-y-editar-el-perfil
- Lifecycle: `Implementation in progress`
- Grooming notes: `harness/grooming/RF-03-grooming.md`
- Approved plan: `harness/features/RF-03-Implementation-plan.md`

## Related completed implementation

- Ticket: `RF-02 · Iniciar y cerrar sesión`
- Lifecycle: `Completed and validated`
- Approved plan: `harness/features/RF-02-Implementation-plan.md`
- RF-02 provides the authenticated entry point and shared light visual foundation RF-03 will reuse.

- Ticket: `RF-01 · Crear una cuenta`
- Lifecycle: `Completed and validated`
- Approved plan: `harness/features/RF-01-Implementation-plan.md`
- The previously pending full Docker Compose/PostgreSQL smoke test now passes.
