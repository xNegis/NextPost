# RF-16 - Cast an independent vote - Implementation Plan

## Status

`Ready for implementation`

On 2026-10-16 the product owner selected `1A 2A`, then explicitly approved the settled
scope, plan finalization and harness launch. No material question remains. This does not
authorize commits, pushes, deployment or Trello changes.

## Source ticket

- Trello title: RF-16 · Emitir un voto independiente
- Trello URL: https://trello.com/c/rzoUcPdL/17-rf-16-emitir-un-voto-independiente
- Stable URL: https://trello.com/c/rzoUcPdL
- Board: APP - NextPost, https://trello.com/b/CgBkRg78/app-nextpost
- Trello list at intake: Próximo · completar el MVP
- Snapshot captured on: 2026-10-15
- Grooming notes: `harness/grooming/RF-16-grooming.md`

## Objective

Let a registered non-owner compare an accessible open consultation's photos, select one,
review it and confirm exactly one immutable vote. Reload, later sign-in and an ambiguous
response recover only that account's recorded selection. Voters never see aggregate results.

An already-voted Public consultation remains in normal Home chronology with `Voted`.
Opening it highlights only the current account's photo as `Your vote` and states that votes
cannot be changed. The same contract accepts a current Private token, while RF-26 owns the
actual Private-link entry and post-authentication return.

## Context and current behaviour

- React/TypeScript/Vite/Capacitor forms the client; FastAPI/SQLAlchemy/Alembic/PostgreSQL
  forms the API and persistence layer. Authentication uses a signed HttpOnly cookie.
- RF-14 implemented `HomeFeed.tsx`, `FeedCard.tsx`, `useHomeFeed.ts`,
  `ReaderConsultationDetail.tsx`, `useReaderConsultationDetail.ts`, protected previews and
  `PhotoEnlargement.tsx`. Local React state owns navigation; there is no URL router.
- Reader detail shows complete immutable text and ordered protected photos, but has no vote
  selection, review, status read or mutation. Own cards use owner detail.
- `consultation_access.py` already defines `AccessOperation.vote`, denying the owner and
  applying current lifecycle/audience/Private-token rules. No route consumes it yet.
- `models.py` has Account, Consultation and ordered ConsultationPhoto records. The stable
  option identifier is `ConsultationPhoto.id`. There is no Vote/aggregate model. Current
  migration head is `20260928_0004_consultations.py`.
- DEC-033 requires terminal state-dependent writers to lock and reread Consultation.
- RF-14 is owner-closed, but F1 stale previews, the relevant F2 hidden-feed/Back behavior,
  F4 dialog focus and F7 privacy headers block this journey. F3/F5/F6 remain separate debt.
- DEC-011, DEC-019-024, DEC-027-034 and DEC-038 bind this work. Publication is immutable,
  has no expiry, access is request-time, denial is non-enumerating and the owner performs
  visual acceptance.
- The plan-time dirty worktree contains only RF-16 grooming/context/plan documentation.
  Preserve it and all later unrelated changes.

## Scope

### In scope

- Additive Vote migration/model with database uniqueness and same-consultation photo integrity.
- Viewer-scoped vote-status read and one definitive submission with retry reconciliation.
- Consultation row locking, current access recheck and real PostgreSQL race evidence.
- Public Home `Voted` marker and reader selection/review/cancel/confirm/final-own-vote flow.
- Reusable optional current Private-token support for detail/media/status/submission.
- Strict payloads, protected headers, session/denial cleanup and keyboard/focus behavior.
- Only RF-14 F1, the required F2 subset, F4 and F7 prerequisite repairs.

### Out of scope

- Counts, percentages, leaders, winners or any aggregate/other-voter information (RF-18).
- Vote changes/withdrawal, comments (RF-41), random order, Skip, reciprocity or moderation.
- Private discovery, routing, invitations and authentication return (RF-26).
- Finalization/declaration, deletion/removal, participant outcomes/history, photo purge or
  account-deletion behavior (RF-13/19/20, restricted RF-32, RF-21/37/34).
- Search, ranking, profiles, notifications, expiry, workers, analytics or deployment.
- RF-14 F3 IntersectionObserver fallback, F5 owner-detail parity and F6 cursor grammar.

## User experience

Load immutable detail/photos and current-account vote status as separately owned requests.
Submission stays unavailable until status is known. `not_voted` enables an explicit semantic
single-choice control beside every photo; enlargement remains separate. Selection may change
locally without a request.

`Review vote` enters an inline review with the selected photo/number and a finality warning.
`Back to photos` permits another selection. `Cancel` sends nothing and returns to comparison.
`Confirm vote` is the only write and is disabled while pending. Photo activation never confirms.

After success, keep comparison/enlargement usable, highlight the authoritative photo as
`Your vote`, show `Votes cannot be changed`, and remove mutation controls. Own consultations
never gain vote controls. Feed items keep their order and add `Voted`; Private stays out of Home.

On network/5xx/lost POST response, perform one `my-vote` reconciliation. If a vote exists,
show it. If none exists, retain the reviewed choice and permit explicit retry. If reconciliation
also fails, say the outcome is unknown and offer `Check vote status`; never claim success or
silently resubmit. Exact replay succeeds. If another choice won a race, show that immutable
authoritative choice. A current 401 clears account-bound state/URLs and signs in; denial or a
terminal state clears protected content and shows generic unavailable. Missing bytes are retryable.

Back performs RF-14's bounded current-state Home revalidation and restores selected-card focus
when possible. There is no auto-advance or local/browser vote persistence.

## Functional requirements

### FR-1 - Durable immutable vote

Persist opaque Vote UUID, consultation ID, verified voter account ID, selected
ConsultationPhoto ID and server timestamp. Enforce uniqueness on `(consultation_id, voter_id)`.
Add a unique candidate key on ConsultationPhoto `(consultation_id, id)` and a composite Vote
foreign key proving the option belongs to that consultation. Add
`(consultation_id, consultation_photo_id)` for future RF-18 aggregation. Use restrictive foreign
keys so future terminal/account workflows cannot silently erase participation.

### FR-2 - Atomic authorization and concurrency

Submission authenticates, parses bounded untrusted input, begins a transaction, locks the
current Consultation row with PostgreSQL `FOR UPDATE`, rebuilds its access snapshot and calls
`can_access(..., AccessOperation.vote)` with the current Private token where supplied. Within
that boundary, read any existing account vote, validate the option, insert once and commit once.

This lock is the shared protocol for future terminal writers; a late vote cannot cross a terminal
transition. The unique constraint remains a backstop. Same-photo replay returns the existing
vote. If a different photo already won, return `vote_already_recorded` without changing it and
let the client recover the authoritative own selection. Add no idempotency table or background job.

### FR-3 - Viewer-scoped API

Add focused routes:

- `GET /api/consultations/{consultation_id}/my-vote`
- `POST /api/consultations/{consultation_id}/votes`

GET returns exactly `{status: "not_voted"}` or
`{status: "voted", photo_id: <canonical UUID>}`. POST accepts exactly
`{photo_id: <canonical UUID>}` and returns the recorded projection; first creation may be 201
and exact replay 200. Use existing trusted-origin protection for the cookie-authenticated POST.

Both routes require current cookie and current Private token where relevant. A past visit/vote is
not a standing Private grant. Unknown, unauthorized, terminal, revoked-link and self-vote cases
share generic non-enumerating failure. Malformed/extra input is 422; an authorized cross-
consultation option is a safe invalid-selection failure. No response exposes totals, timestamp,
voter identity, leader or derived result.

### FR-4 - Privacy and strict state

Vote routes and consumed protected detail/photo/feed/auth-validation success and error paths carry
`Cache-Control: private, no-store`, `Referrer-Policy: no-referrer` and
`X-Content-Type-Options: nosniff`. Never log choices, tokens, cookies, text, bytes or storage keys.
Every protected media request remains currently authorized before storage access.

Frontend runtime guards accept only exact vote payloads and matching IDs. Detail, media, vote
status and submission have separate request generations bound to account/consultation. Stale
success/error/401 cannot restore content or sign out a later account. Revoke all object URLs on
stale, denied, navigation, replacement and unmount paths.

### FR-5 - Accessible reader flow

Extend the focused reader/controller and `consultationApi.ts`, not owner management/uploader.
Use semantic radio behavior, labelled controls, statuses/alerts and existing touch targets. Inline
review is keyboard usable. `PhotoEnlargement` traps Tab/Shift+Tab, closes on Escape, isolates
background interaction and safely returns focus across detail/account changes.

### FR-6 - Home integration and RF-14 repairs

Extend the strict feed projection with exactly server-derived `has_voted: boolean`, computed
set-wise for the verified account with no voter ID/count. Preserve Public/open eligibility,
chronology, pagination and own-card behavior. Invalidate hidden feed/preview work on detail entry.
Separate one-page Refresh from bounded Back reconciliation, require cursor progress/deduplication,
accurate in-flight accounting and card-action/feed-heading focus fallback. Do not absorb F3/F5/F6.

## Technical approach

Add a focused Vote model/service and thin routes while reusing canonical access policy. The
service owns locking/idempotency and returns only viewer-scoped state. Keep general detail immutable
and use a dedicated status read. Use inline review rather than another dialog lifecycle.

### Affected areas

- Backend: `backend/app/models.py`, `schemas.py`, `consultation_service.py` or a focused vote
  service, `api/consultations.py`, and tests under `backend/tests`.
- Migration: one new revision after `backend/alembic/versions/20260928_0004_consultations.py`.
- Frontend: `consultationApi.ts`, `FeedCard.tsx`, `HomeFeed.tsx`, `useHomeFeed.ts`,
  `ReaderConsultationDetail.tsx`, `useReaderConsultationDetail.ts`, `PhotoEnlargement.tsx`,
  `useFeedPreviews.ts`, `styles.css` and focused tests.
- Storage/background/configuration: no image mutation, service, package, secret or worker.
- Documentation: README where behavior changes and evidence-based project state.

### Data and migration requirements

The additive migration has no backfill; existing consultations start with zero votes. ORM and
Alembic constraints must match. Downgrade may remove the schema only while Vote is empty; refuse
a populated downgrade without data loss. Test fresh upgrade, `0004 -> head`, existing-data
preservation, empty downgrade/upgrade and populated refusal on isolated Alembic PostgreSQL.

### API and integration requirements

Preserve cookie credentials and existing Private capability transport; never accept voter/owner
identity from the client or store the token. Feed computes `has_voted` set-wise, never per card.
Use stable safe errors inside existing envelopes. A different recorded vote is reconciliation,
not update. Vote status/submission perform no file operation.

### Security and privacy

- Derive voter from session and authorize current state inside the write transaction.
- Never trust feed flags, ordinals or client lifecycle/audience/owner claims.
- Render user content inertly; keep images behind protected endpoints.
- Clear protected state before denial/session changes and never infer physical deletion.
- Return/log no aggregate, other choice, voter list, timestamp or reusable capability.

## Implementation sequence

1. Inspect baseline/dependencies; add Vote migration/model and isolated migration/constraint tests.
2. Implement locked service, replay/conflict semantics and PostgreSQL race/terminal-writer tests.
3. Add strict schemas/routes with trusted-origin and private headers.
4. Extend feed query/schema/client with set-wise `has_voted`.
5. Add strict vote clients and reader status/reconciliation state machine.
6. Implement selection, inline review/cancel/confirm and final `Your vote` state.
7. Complete bounded RF-14 F1/F2/F4/F7 repairs and permanent regression tests.
8. Run focused/full checks, isolated migration/races and built two-account smoke.
9. Update documentation/state only from evidence and report owner visual/future-ticket gates.

## Validation strategy

### Automated tests

- Migration/direct SQL proves upgrades, preservation, rollback refusal, one-vote uniqueness and
  composite same-consultation integrity.
- API matrix covers anonymous/stale, owner, Public non-owner, Private correct/missing/wrong/
  replaced/disabled token, every lifecycle, unknown/wrong photo, malformed/extra fields,
  trusted-origin failure, exact payloads and headers.
- Real PostgreSQL races cover same account/same and different options, double click, many accounts,
  delayed retry, and vote versus seeded terminal writer using the shared lock. Assert one final
  state, rollback on injected failure and no storage access for invalid/unauthorized options.
- Frontend guards reject malformed successes. Tests distinguish loading, success, known failure,
  ambiguous response, failed reconciliation, 401, denial and missing media.
- Selection changes locally; Back/Cancel POST nothing; pending confirm cannot duplicate; exact
  retry/different winner/reload/sign-in all reconcile correctly.
- Home preserves order and shows `Voted`; own cards never vote. Reusable tests forward a current
  Private token to detail/media/status/submit but Home never discovers Private.
- No aggregate/result/social-proof fields or copy. RF-14 F1/F2/F4/F7 pass permanently; F3/F5/F6
  remain excluded. Existing feed, owner, publication, links and auth regressions pass.
- Keyboard/focus and nonvisual long-text/RTL/320px/safe-area/200%-zoom coverage; owner handles visuals.

### Manual validation

Use isolated built frontend/backend/PostgreSQL/storage with two accounts and processed photos.
Verify Public and direct current-Private selection/review/cancel, confirm, replay, self-vote denial,
relogin recovery, Home `Voted`, revoked capability and zero result exposure. Use an isolated seeded
terminal writer sharing the lock; add no production terminal endpoint. Restart disposable services
and verify persistence. Owner performs visual acceptance under DEC-034; the harness does not take
screenshots or visually inspect browser/zoom unless separately requested.

### Commands

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

Set `TEST_DATABASE_URL` only to disposable isolated PostgreSQL and migrate with:

```powershell
.\.venv\Scripts\python -m alembic -c backend\alembic.ini upgrade head
```

Use a separate Compose project/override and disposable database/photo volumes for smoke. Never
reset active data. Report skipped/unavailable checks as unverified, not passed.

## Acceptance criteria

- [ ] A registered non-owner can compare/enlarge, select, review, cancel or confirm; only confirm
      writes and pending activation cannot duplicate it.
- [ ] Exactly one immutable vote exists per consultation/account under retries/concurrency/direct
      SQL, and the selected photo must belong to that consultation.
- [ ] Owner, current-access denial/revocation, unknown/terminal consultation and late vote are
      rejected generically without a Vote row or storage access.
- [ ] Exact replay succeeds; a different winner is never overwritten and reconciles to the
      authoritative current-account selection.
- [ ] Reload/sign-in/ambiguous POST recovers only the own photo; unresolved state is honest and
      never silently resubmits.
- [ ] Public cards retain chronology and show `Voted`; detail shows `Your vote` and finality;
      Private remains absent from Home.
- [ ] No voter API/UI/log exposes aggregate/result/other-voter/timestamp/capability data.
- [ ] Protected success/errors have required private headers, strict payloads and server authority.
- [ ] Stale requests cannot revive content or sign out another account; Back revalidates and URLs
      are cleaned up.
- [ ] Enlargement/radio/review/recovery keyboard and focus behavior is tested.
- [ ] Migration, PostgreSQL races, full checks, Compose build/config and isolated smoke have evidence.
- [ ] Existing feed/owner/publication/links/auth pass; F3/F5/F6, RF-26/RF-18 and terminal flows
      remain explicitly unimplemented. Documentation makes no deployment/device/visual overclaim.

## Dependencies and ordering

Read the complete approved RF-07/RF-08/RF-09/RF-10/RF-11/RF-12/RF-14 plans and inspect current
code. RF-14 is the direct dependency. RF-18 consumes Vote rows; RF-19/RF-20 later share the lock
and create outcomes; RF-26 supplies Private entry; RF-13/restricted RF-32/RF-37 own removal/bytes;
RF-21 owns participant history and RF-34 owns account-deletion effects.

## Risks and mitigations

- Duplicate/change race: row lock, natural unique key and immutable service path.
- Late terminal race: current-state authorization under the shared Consultation lock.
- Wrong-consultation option: composite foreign key plus service validation.
- Privacy leak: dedicated exact viewer projection, no aggregates and private headers.
- Lost response: one status reconciliation, explicit unknown and no silent retry.
- Stale state: independent generations, bound ownership and URL cleanup.
- Destructive rollback: refuse populated downgrade.
- Scope growth/overclaim: named debt boundary and explicit owner/device/future-ticket gates.

## Harness handoff notes

- Read `AGENTS.md`, all context, this plan and named dependencies completely before editing.
- Preserve existing RF-16 documentation and unrelated changes. Do not reset, commit, push,
  deploy, mutate Trello/active data or launch other agents.
- Implement this contract rather than another plan. Stop on conflicts with code/accepted decisions.
- Use isolated Alembic PostgreSQL for migration/race evidence; metadata-only tests are insufficient.
- Add no production terminal endpoint for tests. Owner retains visual acceptance.
- Update project state only from evidence. Ready is not completed.

## Resolved grooming decisions

- Q1A: voted Public consultations retain chronology and show current-account `Voted`.
- Q2A: detail identifies only the own recorded photo as `Your vote` and states finality.
- One confirmed vote is immutable; pre-confirmation selection is local. Registration suffices;
  owners cannot vote and no aggregate/other-voter information is exposed.
- Public/Private share the current-access contract; RF-26 owns Private entry/auth return.
- Photo order stays immutable; no Skip, comments, reciprocity, expiry or terminal action is added.
- On 2026-10-16 the owner approved the scope, finalized plan and harness launch.

## Remaining questions

None
