# RF-21 - Consult my participation history - Implementation Plan

## Status

`Ready for implementation`

The product owner accepted every grooming recommendation (`Q1A` through `Q7A`) and explicitly
approved implementation-plan finalisation and harness launch on 2026-10-21.

## Source ticket

- Trello title: `RF-21 · Consultar mi historial de participación`
- Trello URL: https://trello.com/c/J1t1OjVt/22-rf-21-consultar-mi-historial-de-participaci%C3%B3n
- Trello list at intake: `Próximo · completar el MVP`
- Snapshot captured on: 2026-10-21
- Grooming notes: `harness/grooming/RF-21-grooming.md`

## Objective

Give an authenticated participant a private, photo-free history that confirms where the current
account has an open vote and returns the semantic result of completed participation as `Matched`,
`Not matched` or `No choice`. Complete the MVP feedback loop without revealing the participant's
raw selected option, images, author aggregates, other participants, Private-link capabilities or
reputation-style metrics.

The history is evidence of participation, not an access-control grant. Matching means agreement
with the author's declared final choice, not objective correctness or proof of external publication.

## Context and current behaviour

- RF-16 stores one immutable `Vote` per account and consultation while the consultation is open.
  `Vote.created_at` is the truthful open-participation event time. The current `votes` indexes are
  consultation-first and do not efficiently serve a voter-first chronological history.
- RF-19/RF-20 atomically replace every valid raw vote with exactly one `ConsultationOutcome` at
  finalisation. Values are `matched`, `not_matched` and `no_choice`; no raw option choice survives.
  `ConsultationFinalization.finalized_at` is the truthful terminal event time.
- `ConsultationOutcome` has a voter index, but not the composite order needed by the planned
  account/date/id page. The current Alembic head is `20261020_0008_finalization.py`.
- RF-37 removes images and terminal free text/access metadata. Final history cannot safely depend on
  question, author nickname, image or former audience data.
- RF-13 deletes open votes without producing outcomes or tombstones. If an author later deletes a
  finalised consultation, it remains `finalized` with `author_deleted_at` and its DEC-023 outcome may
  survive.
- RF-26 defines Private access as a bearer-link capability. Account participation is not an access
  entitlement and cannot recover, persist or replace that capability.
- `/api/my-consultations` and `MyConsultations.tsx` are author-only. They must remain separate from
  the participant projection and authority model.
- The frontend currently exposes Home, Create, My consultations and Profile through
  `Navigation.tsx` and destination state in `App.tsx`. RF-21 adds a fifth primary destination.
- Existing API pagination uses opaque validated cursors and `limit + 1` reads. RF-21 should follow
  those repository conventions while using its own mixed-event cursor contract.
- Pre-RF-19/RF-20 finalised rows may have no individual outcomes. Aggregates and declarations cannot
  reconstruct which option an account selected, so no personal outcome may be fabricated.

Binding decisions include DEC-019, DEC-021, DEC-023, DEC-029, DEC-036, DEC-038, DEC-041–045.
User-facing copy remains English.

## Scope

### In scope

- A fifth primary navigation destination labelled `History`, with screen heading
  `My participation`.
- One authenticated participant-history read endpoint, schemas and service/query boundary.
- One row per current-account participation drawn from:
  - a real vote on a currently open consultation;
  - a real retained `ConsultationOutcome`; or
  - an exceptional surviving account-linked terminal vote that proves participation but cannot
    safely yield a semantic result, represented as `Unavailable` and treated as an anomaly.
- Neutral textual states: `Open`, `Matched`, `Not matched`, `No choice`, and narrowly constrained
  `Unavailable`.
- Truthful event labels and dates: `Voted` for vote-derived rows and `Finalized` for outcome-derived
  rows.
- Stable descending keyset pagination, loading/empty/error/retry/load-more behaviour and responsive,
  accessible presentation.
- Strict participant isolation, response minimisation, Private-capability non-escalation and
  cache/session safety.
- Additive voter-first indexes required by the approved query, migration tests and regression
  coverage.

### Out of scope

- Images, thumbnails, question/context, author nickname or any other content recognition in history.
- Returning the participant's raw selected option or durable choice recovery.
- Aggregate counts, final declaration details, other voter data, percentages, scores, reputation,
  expertise, streaks, comments or notifications.
- Persisting or returning Private-link tokens, treating participation as Private access, or changing
  RF-26 direct-entry rules.
- A durable tombstone for an open consultation deleted or removed before finalisation.
- Fabricated legacy outcomes or data repair inferred from aggregates/declarations.
- RF-32 administrative removal, suspension, inbox, audit, appeal, invalidation or recalculation.
- RF-34 account deletion/anonymisation implementation or a new independent retention period.
- RF-42 deployment, HTTPS, native project generation, TestFlight/App Store work or invited testing.
- Changes to author results, voting/finalisation semantics, Trello, deployment, commit or push.

## User experience

### Navigation and initial load

- Add `History` as the fifth primary destination. Selecting it renders a screen headed
  `My participation`; do not rename, merge or otherwise change `My consultations`.
- Navigation must remain usable at 320px width, with device safe-area insets, at 200% zoom and with
  keyboard/screen-reader navigation. Labels may wrap or the layout may adapt, but destinations must
  not overlap, clip or become ambiguous.
- Show a labelled loading state on the first request. Do not briefly present the empty state while a
  request is pending.
- On first-load failure, show a generic recoverable message and Retry. Do not expose SQL, cursor,
  identifiers beyond the row's permitted reference, or internal lifecycle/storage details.

### History rows

- Render a semantic list with one row per returned consultation reference. The row contains only:
  - the opaque consultation reference in the existing safe display convention;
  - one neutral textual state;
  - one accurately labelled event timestamp; and
  - a View consultation action only when the server says the currently open consultation is Public.
- `Open` uses `Voted <date/time>` and never shows the chosen option. A Public open row may navigate
  through the existing direct consultation flow, where current server authorization determines
  access and existing RF-16/RF-18 behaviour may show live content/own choice. The history payload
  itself remains photo-free.
- A Private open row has no View action. The user must retain and use the original Private link; the
  history must not store, reconstruct or solicit its capability.
- `Matched`, `Not matched` and `No choice` use `Finalized <date/time>` and never link to terminal
  content. `No choice` must be explained as the author having declared no selected photo, not as the
  participant having failed to vote.
- `Unavailable` may appear only when a surviving account-linked record proves participation but the
  system cannot safely produce a semantic outcome. It must not be synthesized for an absent legacy
  row or for an open vote deleted normally before finalisation.
- Include short adjacent/help copy explaining that matching compares the vote with the author's
  declared choice and is not a correctness score. Do not use win/loss, correct/wrong, expertise or
  celebratory language. Status meaning must not depend on colour or icon alone.

### Empty, pagination and refresh behaviour

- The empty state explains that consultations the account votes in will appear here and provides a
  Home action. It must not imply that omitted pre-contract history never existed.
- Fetch the first page when History becomes active for the current authenticated account. A later
  explicit revisit may refresh the first page; do not poll.
- Show Load more only when `next_cursor` is present. Prevent duplicate submissions. A load-more
  failure keeps all successful rows visible and offers a retry of that page.
- Merge pages by consultation ID defensively and keep server ordering. An open row can become a
  final row between visits; a fresh first-page load is authoritative. Do not attempt live client
  reconciliation or retain a cross-session snapshot.
- On sign-out, session expiry or account change, immediately clear history rows, cursors and pending
  responses. A stale response from the prior account must not populate the new session.

### Accessibility

- Use a real page heading, semantic list, status text, labelled dates and buttons/links with visible
  focus. Announce initial errors, retries and newly appended results appropriately without noisy
  per-row live regions.
- Touch targets are at least 44px; layout supports keyboard-only use, screen readers, reduced motion,
  mobile safe areas and text expansion. Existing navigation destinations remain reachable.

## Functional requirements

### FR-1 - Dedicated private projection

Add `GET /api/my-participation?limit=<n>&cursor=<opaque>` under signed-session authentication. Derive
the participant account only from the authenticated session. Do not accept account, voter, owner,
audience, state or capability parameters.

Use a strict response allowlist:

- `items`: ordered history rows;
- `next_cursor`: an opaque string or null.

Each row contains exactly:

- `consultation_id`: opaque stable reference;
- `status`: `open | matched | not_matched | no_choice | unavailable`;
- `event_kind`: `voted | finalized`;
- `event_at`: UTC timestamp in the repository's established serialized form;
- `can_view`: boolean, true only for a currently open Public consultation.

Reject/ignore no unknown response data: define explicit typed backend and frontend decoders. Do not
include question, context, nickname, audience, photo/option IDs, photo metadata/URLs, raw vote,
final declaration, counts, percentages, author controls, participant IDs, capability/link state,
author-deletion marker, moderation state or cleanup internals.

### FR-2 - Row derivation and precedence

For the authenticated account:

1. A `Vote` joined to a consultation currently in canonical `open` state produces `open`,
   `event_kind=voted`, `event_at=Vote.created_at`; `can_view` is true only when the current audience
   is Public.
2. A `ConsultationOutcome` joined to its `ConsultationFinalization` produces the corresponding
   semantic status, `event_kind=finalized`, `event_at=finalized_at`, and `can_view=false`, including
   when the finalised consultation has a later `author_deleted_at` marker.
3. A surviving `Vote` for a non-open consultation with no outcome may prove a pre-contract or
   inconsistent participation and produces `unavailable`, `event_kind=voted`, its real vote time and
   `can_view=false`. Never return its selected option. Emit only a sanitized anomaly counter/event so
   restricted maintenance can investigate the forbidden terminal residue.
4. A finalised consultation with no outcome and no surviving account-linked participation record
   produces no row for that account. Do not infer participation or outcome from author aggregates,
   declarations or consultation ownership.
5. Normal deletion/removal before finalisation creates no history tombstone. Once its vote is gone,
   it disappears from history.

Enforce one row per consultation. A semantic outcome has precedence over any anomalous residual
vote. Do not treat authorship alone as participation.

### FR-3 - Stable pagination

- Default `limit=20`; accept `1..50`; reject invalid values using the established validation style.
- Order by `event_at DESC, consultation_id DESC` across the mixed projection.
- Fetch `limit + 1` to determine `next_cursor`.
- The cursor encodes and strictly validates the keyset boundary plus an initial server snapshot
  timestamp. Subsequent pages retain the snapshot and exclude events newer than it. The cursor is
  pagination state only and never authority.
- Reject malformed, unsupported-version or impossible cursors with a stable, generic client error.
  Do not log cursor contents unnecessarily.
- A consultation that finalises during an older snapshot may disappear from a later open-vote page
  while its new final event is newer than that snapshot. This is acceptable; a fresh first-page load
  is authoritative. Never duplicate or fabricate it to force snapshot history.
- Use one database-level union/query plan or an equivalently bounded merge that applies account,
  snapshot and keyset filters before limiting. Do not fetch all history into application memory.

### FR-4 - Authorization and privacy

- Every branch is constrained by the session account in SQL; filtering after an unscoped read is
  insufficient.
- An empty account history and an account with no permission to view former content have the same
  non-revealing shape. History does not expose whether another account participated.
- `can_view` is current convenience only. The destination request must re-authorize from current
  database state and may still return generic unavailability after a race.
- Never accept, persist, serialize, place in a cursor, log or browser-store a Private capability.
- Apply authenticated private/no-store security headers consistently with the existing API. Preserve
  trusted-Origin/session protections where applicable; this GET introduces no mutation or CSRF
  exception.
- Clear client state on authentication loss and guard asynchronous responses by current session or
  request generation.

### FR-5 - Neutral product semantics

- `Matched` means the participant's former raw choice belonged to the author's declared set.
- `Not matched` means at least one option was declared and the participant's choice was not in it.
- `No choice` means the author explicitly declared none.
- `Unavailable` is not a mismatch and conveys no reason beyond the result being unavailable.
- Do not calculate or expose a personal/global percentage, success rate, rank or derived profile
  attribute.

### FR-6 - Error and state handling

- Unauthenticated/session-expired requests use the existing authentication response and frontend
  return flow.
- Invalid query/cursor requests receive the repository's stable field-safe 4xx response.
- Database failures return sanitized 5xx responses and a generic retryable UI state. Existing items
  remain visible for load-more failures.
- The endpoint is read-only and idempotent. It creates no history rows, tombstones, access grants,
  cleanup jobs or last-viewed state.
- Sanitized observability may include request outcome, item/status counts, pagination presence,
  latency and terminal-vote anomaly count. It must exclude consultation IDs, participant IDs,
  questions, capabilities, raw choices and cursor payloads.

### FR-7 - Compatibility and retention

- Do not backfill outcomes, infer participation or add a history ledger.
- Preserve all existing votes and outcomes. Add indexes only; no data rewrite is required.
- Keep account-linked outcomes only under the current DEC-023 contract while the account exists.
  RF-34 remains responsible for deletion/anonymisation and restrictive foreign-key handling.
- Future RF-32 may preserve, replace or remove semantic outcomes in its approved transaction. RF-21
  renders the stored result and does not infer administrative policy from consultation state.

## Technical approach

Create a narrow participant-history service rather than expanding author-focused
`consultation_service.py` projections. The service should construct a database-bounded mixed
projection from voter-scoped `Vote` and `ConsultationOutcome` sources, apply deterministic keyset
pagination, map only to internal read DTOs and let the API map those DTOs to strict Pydantic schemas.

Add the endpoint to the existing consultation API router or a focused participant router consistent
with current application composition. Reuse authentication dependencies, datetime normalization,
safe error conventions and response security middleware. Use a versioned cursor codec specific to
this projection; reuse low-level safe serialization helpers only when their format matches.

On the frontend, add a dedicated API decoder, hook and `MyParticipation` component. Extend
`Destination` and Navigation with `history`, keeping direct consultation routing and author screens
independent. Use request generation/abort logic so stale page results cannot cross sign-out or
account changes.

### Affected areas

- Frontend:
  - `frontend/src/Navigation.tsx`
  - `frontend/src/App.tsx`
  - `frontend/src/consultationApi.ts` or a focused participant-history API module
  - new participant-history hook/component and focused tests
  - `frontend/src/styles.css`
- Backend/application:
  - `backend/app/api/consultations.py` or a focused participant-history router
  - `backend/app/schemas.py`
  - a new focused participant-history service/cursor module
  - `backend/app/main.py` response-header routing if the exact endpoint is not already covered
- Domain/data model:
  - existing `Vote`, `ConsultationOutcome`, `ConsultationFinalization`, `Consultation` and
    `ConsultationAudience`; no new product entity
  - model index declarations kept consistent with the migration if this repository mirrors indexes
- Database:
  - one additive Alembic revision after `20261020_0008` for voter-first chronological indexes
- Storage/background work: none; RF-21 never touches images or RF-37 jobs
- Configuration/deployment: none
- Documentation:
  - `harness/context/04_PROJECT_STATE.md` only when supported by implementation evidence

### Data and migration requirements

- Add a composite index supporting open-vote lookup and ordering, expected shape
  `votes(voter_id, created_at, consultation_id)`.
- Add a composite index supporting outcome lookup/tie-breaking, expected shape
  `consultation_outcomes(voter_id, created_at, consultation_id)`, unless the final query plan proves
  a better equivalent using the joined finalisation timestamp. Because displayed terminal ordering
  uses `ConsultationFinalization.finalized_at`, inspect PostgreSQL `EXPLAIN` or actual query shape and
  add the minimum justified finalisation/join index rather than mechanically adding redundant ones.
- Migration is additive and contains no backfill, new row or retention field. Downgrade may drop only
  the new indexes and must leave all participation data untouched.
- Keep model metadata and migration constraints/index names aligned. Validate upgrade/downgrade on
  real PostgreSQL and through the full current migration chain.

### API and integration requirements

- Endpoint: `GET /api/my-participation`.
- Query: optional `limit` and `cursor`; no body and no participant selector.
- Success: strict `200` page payload defined by FR-1, including an empty array and null cursor.
- Authentication: existing signed session only.
- Pagination cursor: versioned, opaque, bounded and validated; never accepted as authorization.
- Public open View uses the existing direct consultation route. The target endpoint performs its own
  current authorization; do not pass history-derived authority.
- Runtime-decode the API response before storing/rendering it. Malformed status, timestamps,
  booleans, arrays or cursors fail safely into the recoverable error path.

### Security and privacy

- Perform account scoping in every union branch before joining/projecting.
- Return only the exact allowlist and add tests that assert forbidden keys are absent recursively.
- Never select raw option IDs into application DTOs when only status derivation is needed. For the
  exceptional terminal-vote branch, project existence/time only and discard the choice in SQL.
- Do not let consultation IDs act as authorization. All navigation rechecks current state.
- Do not cache history in localStorage/sessionStorage, service-worker persistence or cross-account
  global state. Clear in-memory results on session loss.
- Preserve no-store/nosniff/referrer protections and avoid identifiers/content in logs and metrics.
- Treat cursor and server response data as untrusted; enforce length, version, type and date bounds.

## Implementation sequence

1. Add focused backend read DTOs, strict response schemas, cursor codec and voter-scoped mixed query.
2. Add `GET /api/my-participation` with session authentication, safe query validation, headers and
   sanitized errors/observability.
3. Add only the voter-first indexes justified by the real query, with additive Alembic and
   PostgreSQL migration coverage.
4. Add backend service/API tests for all statuses, strict isolation, author deletion, open deletion,
   legacy compatibility, cursor boundaries and forbidden-field absence.
5. Add the frontend runtime decoder/API client and a hook with initial, refresh, pagination,
   retry, stale-request and session-clear handling.
6. Add `MyParticipation`, neutral explanatory copy, semantic rows, empty/loading/error states and
   Public-only View navigation.
7. Add History to the primary navigation and adapt responsive/safe-area styles without regressing
   the four existing destinations or direct-entry routes.
8. Add focused component/hook/API/accessibility tests, then run the complete validation matrix.
9. Update project state with exact evidence and remaining DEC-034 manual visual checks; do not claim
   completed/validated before product-owner visual acceptance.

## Validation strategy

### Automated tests

- Backend service tests:
  - only current-account rows across two participants and an author;
  - open/Public and open/Private states with correct `can_view` and no capability leakage;
  - `matched`, `not_matched`, `no_choice` mapping and finalisation date;
  - author-deleted final consultation remains in participant history;
  - normally deleted/removed open participation leaves no row;
  - terminal residual-vote anomaly maps only to `unavailable` and exposes no choice;
  - legacy finalised row without account-linked proof is omitted;
  - outcome precedence prevents duplicates;
  - default/min/max/invalid limit and malformed/version-invalid cursor;
  - deterministic ordering and multiple pages with tied timestamps;
  - snapshot/new-finalisation behaviour and bounded queries;
  - database error rollback/read-only safety and sanitized failure.
- API/security tests:
  - unauthenticated request rejected;
  - client cannot choose another account or expand scope through query/cursor tampering;
  - exact payload allowlist and recursive absence of images, options, counts, author data, voters,
    audience/link state and moderation/cleanup internals;
  - correct private/no-store headers on success, empty and error responses.
- PostgreSQL/migration tests:
  - full upgrade to new head and downgrade of the index-only revision without data loss;
  - expected indexes exist and the history query behaves with real timestamp/UUID ordering;
  - representative query-plan evidence that voter lookup does not require an unbounded table scan;
  - existing finalisation/deletion constraints remain intact.
- Frontend tests:
  - fifth navigation destination and accessible selection state;
  - loading versus empty, empty Home action, first-load retry and load-more retry preserving rows;
  - all five status labels, correct date labels and explanatory copy;
  - no selected-option/photo/aggregate rendering;
  - View only for a server-authorised Public open row and no link for Private/terminal rows;
  - runtime rejection of malformed payloads;
  - pagination deduplication, duplicate-load prevention and stable append order;
  - sign-out/account change/stale-response state clearing;
  - keyboard/focus/semantic-list/accessibility behaviour and responsive navigation classes.
- Regression tests for Home, direct Public/Private entry, voting/own-choice recovery,
  My consultations, finalisation, author deletion and Profile navigation.

### Manual validation

- Exercise empty, one-page and multi-page history with two participant accounts and one author.
- Confirm open Public navigation works and open Private rows disclose nothing beyond the minimum and
  cannot reopen without the original link.
- Finalise examples producing each semantic outcome; confirm images, raw choices and aggregates are
  absent and the neutral explanation is understandable.
- Delete one open and one finalised consultation as author; verify disappearance versus retained
  private outcome.
- Verify keyboard and screen-reader flow, visible focus, 320px layout, representative phone safe
  areas, 200% zoom and all five navigation destinations.
- Complete the DEC-034 product-owner visual/interaction acceptance after independent review.

### Commands

From the repository root unless a command changes directory:

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
git diff --check
```

Run PostgreSQL-only history/migration tests with a disposable database and `TEST_DATABASE_URL`,
following the established repository test pattern. Do not reuse or remove ordinary development
volumes. Record the exact command, disposable resource name and cleanup evidence in project state.

## Acceptance criteria

- [ ] Authenticated users can open a distinct primary History destination headed My participation.
- [ ] The current account sees one ordered row for each representable open vote or retained semantic
      outcome and never sees another account's participation.
- [ ] Open rows show only minimum reference/state/date data; Public rows may navigate through the
      existing independently authorised route and Private rows grant no access.
- [ ] Final rows display exactly `Matched`, `Not matched` or `No choice` from stored outcomes, with a
      neutral explanation and no fabricated result.
- [ ] Open deletion/removal produces no tombstone; author deletion after finalisation leaves the
      existing private outcome visible.
- [ ] `Unavailable` appears only from surviving account-linked proof without a safe result and never
      reveals the raw option.
- [ ] No history response or UI exposes photos, raw choices, declaration/aggregates, other voters,
      Private capabilities, scores, comments or administrative internals.
- [ ] Default 20/max 50 keyset pagination is deterministic, bounded and recoverable on error.
- [ ] Empty, loading, initial error, retry and load-more failure states leave the user in a usable
      state; session/account changes cannot retain or receive stale prior-account history.
- [ ] The five-destination navigation and history screen are usable by keyboard/screen reader and at
      320px, safe-area mobile layouts and 200% zoom without status relying on colour.
- [ ] Additive migration/indexes are validated on real PostgreSQL with no backfill or data loss.
- [ ] Existing feed, direct access, voting, finalisation, author deletion and My consultations flows
      pass regression checks.
- [ ] Automated suites, static checks, production build, dependency audit, Compose validation/build
      and diff check pass, with any environmental limitation recorded accurately.
- [ ] Independent implementation review finds no unresolved acceptance or privacy defect, followed
      by DEC-034 product-owner visual/interaction acceptance before completion is claimed.

## Dependencies and ordering

- RF-16 vote persistence, RF-19/RF-20 finalisation/outcomes and RF-37 minimisation are implemented
  prerequisites and are present at the approved baseline.
- RF-13 supplies deletion semantics; RF-26 supplies the Private capability boundary; RF-12 supplies
  author-navigation conventions but remains a separate screen.
- RF-32 is not an implementation dependency for this reader. Before real-user beta, its restricted
  removal path must define any outcome invalidation/recalculation and use the RF-37 boundary.
- RF-34 later owns deletion/anonymisation of account-linked outcomes.
- RF-42 consumes RF-21 during delivery and invited-beta validation; it is not part of this scope.

## Risks and mitigations

- **Cross-account data leak:** scope every SQL branch by the signed-session account and prove with
  two-account/cursor-tampering tests.
- **Private access escalation:** return/store no capability or content; Public-only `can_view` is a
  hint and destination access is re-authorised.
- **Accidental raw-choice retention/exposure:** select only existence/time for anomaly rows and use
  exact response/runtime allowlists with forbidden-key tests.
- **False historical result:** use only real outcomes; omit unprovable rows and constrain
  `Unavailable` to surviving proof.
- **Misleading chronology:** label vote and finalisation timestamps differently and sort by the
  truthful effective event.
- **Mixed-query performance:** apply voter/snapshot/keyset filters in the database, add minimal
  composite indexes and inspect the PostgreSQL query plan.
- **Pagination races:** snapshot the event upper bound, accept that a transition may appear on fresh
  reload, and never fabricate consistency.
- **Mobile navigation crowding:** test all five destinations at 320px, safe areas and text zoom;
  adapt CSS without renaming or hiding destinations.
- **Future RF-32 conflict:** RF-21 consumes stored outcomes only; administrative mutations remain an
  explicit later producer contract.
- **Premature completion:** record automated/review evidence separately and retain DEC-034 manual
  product-owner acceptance as the final gate.

## Harness handoff notes

- The worktree contains the newly approved RF-21 grooming, DEC-045, project-state entries and this
  implementation plan. These are intentional coordinator changes and must be preserved.
- Start from `main` commit `b4c8232fe71225444287863c001c31bdf53d37dd`, which matched
  `origin/main` before grooming documents were added.
- Inspect the complete current worktree before editing. Do not revert or rewrite the coordinator's
  documentation changes.
- Implement the approved plan, not the Trello card or conversation history. Do not open the
  Codex-only OpenCode runbook or launch agents.
- Do not commit, push, deploy, modify Trello or use ordinary development data/volumes.
- If the approved contract conflicts with current code or an accepted decision, stop and report the
  conflict rather than choosing a new product rule.
- Product code, tests and reports remain English. Update project state only with evidence.

## Resolved grooming decisions

- `Q1A`: fifth primary History destination; My participation screen; My consultations unchanged.
- `Q2A`: minimal open rows; participation grants no Private access; View needs current independent
  authority.
- `Q3A`: truthful Voted/Finalized event dates and descending mixed ordering.
- `Q4A`: no tombstone after pre-finalisation deletion/removal; narrow evidence-based Unavailable.
- `Q5A`: consume stored final outcome; RF-32 owns future administrative outcome mutation.
- `Q6A`: no fabricated historical backfill; omit unprovable legacy participation.
- `Q7A`: neutral status language and explicit non-correctness explanation.

## Remaining questions

None
