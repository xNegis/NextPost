# RF-18 - Consult results as author - Implementation Plan

## Status

`Ready for implementation`

The product owner explicitly approved the settled RF-18 scope, this plan's finalisation and the
external implementation-harness launch on 2026-10-18.

## Source ticket

- Trello title: RF-18 · Consultar resultados como autor
- Trello URL: https://trello.com/c/GBfvkzU8/19-rf-18-consultar-resultados-como-autor
- Trello list at intake: Próximo · completar el MVP
- Snapshot captured on: 2026-10-16
- Grooming notes: `harness/grooming/RF-18-grooming.md`

## Objective

Give an authenticated consultation author a private, current view of how many valid votes each
published photograph has received while the consultation is open. Show the current total in each
Open row of My consultations and the exact count for every photograph in owner detail. Results are
participant opinions that help the author decide; they are not a prediction, guarantee, objective
quality judgment or obligation to follow the majority.

This increment intentionally exposes counts only. It must not expose percentages, voter identities,
individual voter choices, rankings or aggregates to participants.

## Context and current behaviour

- RF-10/RF-11 supply immutable published options, protected media and the open/finalized lifecycle.
- RF-12 supplies the authenticated, owner-scoped `My consultations` list and detail. Open detail
  includes photos in immutable ordinal order; finalized detail is deliberately photo-free. It
  deferred vote counts until RF-16/RF-18.
- RF-16 is implemented and validated. `Vote` stores one immutable choice per
  `(consultation_id, voter_id)`, enforces that the selected `ConsultationPhoto` belongs to that
  consultation, and has `ix_votes_consultation_photo` on
  `(consultation_id, consultation_photo_id)`. Its participant endpoints reveal only the current
  participant's own choice and reject the author as a voter.
- The current owner list/detail authority is derived from the signed account session. Public access
  and a valid Private capability do not confer owner authority.
- No aggregate service, result endpoint, denormalized counter, result snapshot, percentage or
  author-result UI currently exists.
- DEC-039 fixes this increment as live Open counts only, refreshed immediately and every five
  seconds while the relevant view is visible. Finalized snapshots and photo-free finalized result
  presentation remain consumers of RF-19/RF-20/RF-37.
- The worktree already contains substantial accepted RF-16 and device-correction work. It is the
  implementation baseline and must be preserved; the harness must not reset, revert or overwrite
  unrelated changes.

## Scope

### In scope

- Add the total valid vote count to every Open item returned by the owner-only My consultations list.
- Add a focused owner-only live-results read for an Open consultation.
- Return every immutable photo option in ordinal order with its exact integer vote count, including
  options with zero votes; equal counts remain equal without a hidden tie-break.
- Display total votes in each Open list row and total plus per-photo counts in Open owner detail.
- Load results immediately, refresh them every five seconds only while the relevant Open list/detail
  view is visible, and retain the existing manual Refresh route for immediate recovery.
- Make loading, successful zero, stale-after-refresh-failure, session loss, denial and unavailable
  states observable and distinct.
- Add strict response validation and comprehensive backend, frontend and PostgreSQL coverage.
- Document that durable finalized aggregates/display remain gated on RF-19/RF-20/RF-37.

### Out of scope

- Percentages or any percentage response field, calculation or presentation.
- Aggregate access for voters, participants, Home/feed, general consultation detail, public readers
  or Private-link holders.
- Voter identities, aliases, emails, timestamps, per-account choices, comments or any inference that
  lets the author reconstruct an individual's vote.
- Leader/winner badges, ranking, confidence, prediction, recommendation, automatic selection or
  reordering by count.
- Vote editing, withdrawal, invalidation, weighting or moderation.
- Finalization, declared author selections, participant outcomes/history, durable result snapshots,
  finalized-result presentation, consultation deletion/removal or physical image purge.
- Account deletion/anonymisation behavior, notifications, push, hidden/background polling,
  analytics, workers/queues, denormalized counters or unrelated cleanup.

## User experience

### My consultations - Open list

- On entry to the visible Open tab, request the first page immediately. Each row shows its current
  total using correct copy (`1 vote`, otherwise `<n> votes`). A confirmed zero displays `0 votes`.
- Continue the existing pagination behavior. Any newly fetched Open page must include totals; a
  refresh of the current list must coherently replace the loaded list rather than merge counts from
  different request generations or accounts.
- While this Open list panel and the browser document are visible, start the next refresh five
  seconds after the previous request settles. Never issue two list requests concurrently and never
  queue missed ticks. Pause when the document is hidden, the user selects Finalized or detail,
  navigation changes, the component unmounts or the account changes. On becoming current and
  visible again, refresh immediately before resuming the interval.
- The existing manual Refresh remains available. It follows the same one-request-per-scope rule.
- A failed first request shows the existing usable error/retry state and no invented zero. If a
  later refresh fails, preserve the last successful rows and counts, mark them as not refreshed,
  expose Retry/Refresh, and allow a later scheduled refresh to recover.

### Open owner detail

- Load detail/photos and its result aggregate as distinct resources. Align each count using the
  stable photo ID and ordinal, never array position alone.
- Show the total once and the exact count with each photo in immutable publication order. All photos
  remain present at zero. Equal counts are shown as equal numbers only; do not add a tie, leader or
  winner treatment.
- Use correct singular/plural copy. Include restrained copy that these are participant opinions and
  may change while the consultation remains open.
- Refresh the live aggregate immediately and every five seconds only while this Open detail and the
  document are visible, with no overlap. Detail/photo loading must not be repeatedly restarted just
  because counts refresh.
- Manual Refresh may refresh the full owner view, but result state must have an independent request
  generation/current-consultation guard so late responses cannot appear under another item/account.
- A first result-load failure must not display zero counts. A later failure preserves the visibly
  identified last-known aggregate while photos/detail remain usable. A successful aggregate with a
  zero total is not an error.
- A 401 clears all owner data, stops polling and invokes the existing session-loss behavior. A
  generic unavailable/denied result clears protected result state without exposing whether another
  owner's consultation exists. Unmount/navigation/item/account changes invalidate late responses
  and cancel or ignore outstanding work.

### Finalized and participant experiences

- Finalized My consultations rows/detail do not gain live counts or result polling in this increment.
- Home, participant reader, `my-vote`, Public and Private general detail remain aggregate-free.
- No broken thumbnail or fabricated finalized result is introduced.

## Functional requirements

### FR-1 - Owner-only live aggregate

Only the authenticated author may read an Open consultation aggregate. Server-side authorization
must derive the account from the signed session and verify ownership before aggregate or storage
work. Anonymous/stale sessions return the established authentication failure. Another account,
including one holding a valid Private capability, receives the repository's generic non-enumerating
unavailable response.

### FR-2 - Exact count semantics

The total is the number of current valid `Vote` rows for the consultation. Each option count is the
number whose `consultation_photo_id` is that option. Every row counts once and equally. Counts are
non-negative integers, the sum of option counts equals `total_votes`, and the server performs no
percentage calculation.

### FR-3 - Complete stable option set

Return all immutable `ConsultationPhoto` options, including zero-vote options, ordered by ordinal.
An outer join from options to votes is required; querying only `Vote` is not acceptable. Ties do not
change order and do not select a leader.

### FR-4 - Open-list summary

The owner-only Open list response adds `total_votes` to each Open item. The Finalized item shape is
unchanged. Totals must be computed set-wise for the page, not with one query per consultation.
Pagination ordering/cursors and ownership filtering remain unchanged.

### FR-5 - Visible-view refresh

The relevant Open list and Open detail result scopes refresh immediately and then at five-second
intervals while current and visible. There is at most one in-flight request per scope. Hidden,
unmounted, inactive-tab/item/destination and account-transition scopes do not poll. Visibility
return triggers an immediate refresh. A refresh failure preserves last-known success and labels it;
an initial failure never masquerades as zero.

### FR-6 - Privacy-preserving payload

No author-result payload or log contains voter ID, alias, email, vote timestamp, individual choice,
Private token, question/context text, storage key, image bytes, percentage, ranking or winner. The
frontend rejects unexpected response keys instead of silently accepting identity/per-voter fields.

### FR-7 - Participant non-disclosure

Participant/feed/general-detail APIs and UI continue to expose no aggregate field or copy. Casting
or recovering a vote does not grant result visibility.

### FR-8 - Safe failure and concurrency

Each result response represents one coherent database statement. Reads do not lock out voting or
cache counts server-side. Stale frontend responses cannot overwrite a newer generation, account,
consultation or navigation state. Existing private response headers apply to success and error
paths.

## Technical approach

Implement live aggregates directly over normalized RF-16 rows. Add a small result projection and
service operation using one set-wise `LEFT OUTER JOIN`/grouped query from all consultation photos to
votes, ordered by stable ordinal. Do not add a counter column, snapshot table, migration, cache,
worker or storage dependency.

Expose the full aggregate through a dedicated owner route:

`GET /api/my-consultations/{consultation_id}/results`

Recommended exact success shape:

```json
{
  "consultation_id": "uuid",
  "state": "open",
  "total_votes": 3,
  "options": [
    { "photo_id": "uuid", "ordinal": 0, "vote_count": 2 },
    { "photo_id": "uuid", "ordinal": 1, "vote_count": 1 },
    { "photo_id": "uuid", "ordinal": 2, "vote_count": 0 }
  ]
}
```

The harness may choose equivalent internal dataclass/function names, but must keep this observable
route and allowlisted wire contract unless current framework constraints make it impossible; any
such conflict must be reported rather than silently redesigning the contract.

Extend only the owner Open-list item with `total_votes`. Use a set-wise subquery/join for the page so
query count does not grow with row count. A dedicated frontend fetcher and exact runtime guard own
the results payload. Integrate polling with existing My consultations/detail state using independent
request generations, cleanup and `document.visibilityState` handling.

### Affected areas

- Frontend: `frontend/src/consultationApi.ts`, `frontend/src/MyConsultations.tsx`,
  `frontend/src/OwnerConsultationDetail.tsx`, `frontend/src/useOwnerConsultationDetail.ts`, relevant
  styles and their existing test files. A focused result hook is acceptable if it reduces lifecycle
  coupling without adding a premature abstraction.
- Backend/application: `backend/app/api/consultations.py`, `backend/app/consultation_service.py`,
  `backend/app/schemas.py`, and focused owner-result/list tests.
- Domain/data model: read the existing `Consultation`, `ConsultationPhoto` and `Vote` models; no model
  schema change is expected.
- Storage/background work: none. Aggregates must not read image storage or add background work.
- Configuration/deployment: none expected.
- Documentation: this plan, implementation review/evidence, and project-state transition after
  independently supported completion.

### Data and migration requirements

- No database migration.
- Source of truth remains valid normalized `Vote` rows and immutable `ConsultationPhoto` rows.
- Preserve RF-16 uniqueness and composite option-integrity constraints. Do not weaken foreign keys.
- Do not persist totals or percentages. Each read derives current Open counts transactionally in one
  statement; no reconciliation process or rollback data work is required.
- Do not create a finalized snapshot. RF-19/RF-20 must write any durable terminal aggregate
  atomically with finalization before RF-37 removes photo data.

### API and integration requirements

- Add the exact owner-result GET route above, authenticated by the existing signed cookie. It accepts
  no capability token or voter identifier.
- Success is permitted only for a current Open consultation owned by the session account. Unknown,
  non-owner, removed/deleted and terminal targets use established generic unavailable behavior; no
  count, state or existence detail leaks.
- Apply `Cache-Control: private, no-store`, `Referrer-Policy: no-referrer` and
  `X-Content-Type-Options: nosniff` consistently to relevant success/error responses.
- Schema validation must reject extra fields. UUIDs, ordinals and counts are validated strictly;
  counts are integer and non-negative, ordinals are non-negative and unique, photo IDs are unique,
  and the aggregate sum equals the total.
- Add `total_votes` only to Open items from `GET /api/my-consultations?state=open`; preserve the
  finalized shape, cursor contract and limit behavior.
- The polling client uses same-origin credentials and does not persist results to local/session
  storage. It may cancel requests with `AbortController`; generation checks remain mandatory even if
  cancellation is used.

### Security and privacy

- Perform authentication/ownership/state checks before aggregate execution and before any image
  storage access. The result service itself must not fetch image bytes.
- Keep denial non-enumerating. Do not distinguish unknown from another owner's ID through response
  bodies, status variants, timings intentionally added by this work or UI copy.
- Allowlist every returned field. Never serialize/join an account object or entire `Vote` model.
- Avoid logging raw result bodies or vote records. Existing request-level route/status logging is
  acceptable if it does not include capabilities or per-voter data.
- Do not add result fields to shared Public/Private detail schemas. Regression tests must prove
  participant surfaces remain aggregate-free.
- Five-second polling stops immediately on session loss and outside visible current scope to avoid
  unnecessary disclosure, account-crossing stale state and resource abuse.

## Implementation sequence

1. Re-read the approved plan and inspect the dirty worktree. Preserve all RF-16/device changes and
   identify overlaps before editing; stop and report any real conflict with accepted decisions.
2. Add backend result projection/query/service with owner/Open authorization, full zero-preserving
   option aggregation and invariant checks. Keep it independent from image storage.
3. Add strict result response schemas and the dedicated owner result route with private headers and
   generic denial behavior.
4. Extend the owner Open-list projection/query/schema with set-wise `total_votes` while preserving
   Finalized shape and cursor semantics.
5. Add frontend result/list types, fetch functions and exact runtime guards that reject malformed or
   extra data, including forbidden percentage/identity fields.
6. Integrate Open-list totals and immediate/non-overlapping five-second visible polling, preserving
   pagination, manual Refresh, stale-data labeling and session-loss handling.
7. Integrate result state into Open owner detail without restarting photo loads on each tick. Align
   by stable photo ID/ordinal; render total, exact per-photo counts and opinion copy with accessible
   loading/error/stale states.
8. Add focused backend, PostgreSQL and frontend tests, including privacy regressions and fake-timer/
   visibility/request-generation scenarios.
9. Run the complete repository validation commands and an isolated built-stack PostgreSQL smoke.
   Record evidence and any environmental limitation without weakening assertions.
10. Update implementation evidence/project state only when supported. Do not mark visually accepted
    or completed; the product owner retains the DEC-034 visual gate.

## Validation strategy

### Automated tests

- Backend access matrix: owner Public/Private success; anonymous/stale 401; another account and
  Private-capability holder generic denial; unknown/removed/terminal generic unavailable.
- Aggregate cases: zero total, one vote, uneven counts, exact ties and ten options. Assert immutable
  ordinal order, zero preservation, non-negative integers and `sum(options) == total_votes`.
- Assert no percentage, voter ID, alias/email, per-voter choice, timestamp, token, text, storage or
  media fields in owner results or Open-list totals.
- PostgreSQL test of the actual outer join and RF-16 constraints/index path. Prove page totals are
  set-wise and avoid N+1 behavior with query-shape/count evidence appropriate to the stack.
- Existing RF-16 exact replay, concurrency, cross-option and late-terminal tests remain green.
- Frontend exact guards reject missing, extra, malformed, duplicate/inconsistent option data and
  total/count invariant failures.
- UI tests cover zero, ties, singular/plural, immutable order, list totals, detail alignment by ID,
  initial failure, stale refresh failure/recovery, manual Retry and session loss.
- Fake-timer/visibility tests prove immediate fetch, five-second cadence after settlement, no
  overlap/queued ticks, pause when hidden/inactive/unmounted, immediate visibility-return refresh,
  and stale-response rejection after item/account/navigation changes.
- Regression tests prove voter reader, `my-vote`, feed and general detail expose no aggregates.
- Accessibility/semantic tests cover status announcements, keyboard/focus behavior, 320px layout and
  200% zoom assumptions. Visual acceptance itself remains with the owner.

### Manual validation

- In an isolated built environment, create an owner and at least two voter accounts, publish a
  consultation with at least three photos, and confirm initial zeros in owner list/detail.
- Cast votes that produce both a tie and an untouched zero option. Confirm the visible owner view
  updates within the approved five-second cadence without manual navigation.
- Confirm participant/general surfaces and direct calls as voters cannot read aggregates.
- Simulate a refresh/network failure after success: last-known counts remain identified as stale and
  later recovery replaces them coherently. Confirm hidden browser state stops requests.
- Restart services and confirm the same counts are derived from persisted votes.
- Do not fabricate finalization. Do not perform browser/device visual inspection unless separately
  requested; prepare the build for the product owner's DEC-034 review.

### Commands

From the repository root:

```powershell
.\.venv\Scripts\python -m pytest backend\tests
.\.venv\Scripts\python -m ruff check backend
.\.venv\Scripts\python -m ruff format --check backend
.\.venv\Scripts\python -m mypy backend

Set-Location frontend
npm test
npm run format:check
npm run lint
npm run typecheck
npm run build
npm audit --audit-level=high
Set-Location ..

docker compose config --quiet
docker compose build backend frontend
```

Use the repository's isolated Compose smoke conventions for PostgreSQL and rebuilt images. Do not
reuse or mutate the developer's normal services/data merely to obtain evidence.

## Acceptance criteria

- [ ] An authenticated author sees the current total vote count on every Open My consultations row.
- [ ] Opening an owned Open consultation shows the exact vote count for every photo in immutable
      order and shows the total once.
- [ ] Options with zero votes remain present; equal counts remain equal without ranking, winner or
      hidden tie-breaking.
- [ ] No percentage field, value or copy is returned or displayed.
- [ ] Results load immediately and refresh every five seconds only while the relevant Open view is
      visible, with one in-flight request per scope and immediate refresh on visibility return.
- [ ] Initial failure never appears as zero; refresh failure preserves and identifies last-known
      counts, manual recovery remains available, and later success recovers coherently.
- [ ] Only the signed-in author can access aggregates. Anonymous users, other accounts, voters and
      Private-link holders receive no aggregate or existence detail.
- [ ] No response, UI state or log introduced by RF-18 reveals voter identity, per-voter selection,
      vote timestamp or another forbidden field.
- [ ] Session loss, denial, navigation, account/item changes and unmount stop polling, clear protected
      state as appropriate and prevent late-response restoration.
- [ ] Open-list pagination and Finalized list/detail remain compatible; participant/feed/general
      detail behavior is unchanged and aggregate-free.
- [ ] Live counts are derived set-wise from RF-16 data without a migration, denormalized counter,
      N+1 page query, image-storage access or background worker.
- [ ] Focused, full and PostgreSQL tests plus format/lint/type/build/dependency/Compose checks pass,
      and isolated built smoke proves zeros, ties, privacy, refresh and restart persistence.
- [ ] Documentation records finalized-result delivery as an RF-19/RF-20/RF-37 gate and does not
      claim the broader Trello card fully complete.
- [ ] Representative failures leave the author view safe and usable, and important RF-12/RF-16
      behavior remains green.

## Dependencies and ordering

- Direct prerequisites already implemented: RF-10/RF-11 publication/lifecycle, RF-12 owner list and
  detail, RF-16 immutable voting.
- DEC-019/DEC-021/DEC-023 preserve author-only aggregate privacy and minimum terminal data;
  DEC-034 leaves visual acceptance to the product owner; DEC-035 constrains claims; DEC-039 defines
  this increment's count-only visible-polling boundary.
- RF-19/RF-20 must define and atomically write final aggregates/outcomes. RF-37 later purges photos;
  together they gate photo-free finalized result presentation.
- RF-21 may consume participant outcomes only after finalization and must not receive author
  aggregates. RF-34 later resolves account deletion/anonymisation without being guessed here.

## Risks and mitigations

- **Privacy leak through shared schemas:** keep a dedicated owner result schema/route and exact
  frontend guards; add negative tests for every participant surface.
- **Zero options omitted:** aggregate from photos with an outer join and test all-zero/mixed cases.
- **N+1/list load:** compute totals set-wise for the current page and verify query behavior.
- **Polling overlap/resource pressure:** schedule after settlement, skip/avoid concurrent work, stop
  outside visible scope and keep the five-second interval fixed.
- **Stale cross-account/item data:** independent generations plus cleanup/cancellation; clear on
  session/authority changes and test delayed responses.
- **Failures misrepresented as zero:** model initial, success and stale/error states separately.
- **Counts overinterpreted:** no percentages/ranking/winner; include modest opinion/may-change copy.
- **Future finalization conflict:** add no speculative snapshot or terminal payload; document the
  explicit consumer gate.
- **Dirty-worktree loss:** preserve current files, make narrow changes and never reset/revert.

## Harness handoff notes

- Work directly in the current dirty worktree. Existing tracked and untracked RF-16, iPhone imaging,
  LAN detail and feed-scroll corrections belong to the project. Preserve them exactly except where
  RF-18 necessarily integrates with the same files.
- Before editing an overlapping file, inspect its current content and diff. Never use destructive Git
  commands. Do not commit, push, deploy or modify Trello.
- This plan authorizes only RF-18's approved live Open count increment. Do not implement percentages,
  finalized snapshots/results or unrelated cleanup.
- External implementation agents must not open `.codex/runbooks/opencode_implementation.md`, launch
  other agents or perform product-owner visual acceptance.
- Run validation proportionate to risk and leave reproducible evidence. Environmental failures must
  be reported accurately; do not silently weaken or skip assertions.

## Resolved grooming decisions

- Q1A: show a total on each Open My consultations row and full per-photo counts in owner detail.
- Q2B: refresh immediately and every five seconds while the relevant view is visible, with no
  overlap, no hidden polling, immediate visibility-return refresh and last-known preservation.
- Q3 custom: counts only for now; no percentages. Preserve fixed order, zero options, natural ties
  and singular/plural copy; add no leader/winner treatment.
- Q4A: deliver complete live Open results now. Finalized snapshot/photo-free presentation remains
  an RF-19/RF-20/RF-37 consumer gate and is not a claimed RF-18 capability.
- Only the author sees aggregates. Participants never do, and no voter identity or individual
  selection is exposed.
- The product owner explicitly approved all settled decisions, plan finalisation and harness launch
  on 2026-10-18.

## Remaining questions

None
