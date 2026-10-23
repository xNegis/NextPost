# RF-21 - Implementation Review

## Status

`Corrective implementation technically validated; DEC-034 product-owner acceptance pending`

This review began with the coordinator's independent assessment of the first external harness pass
against `harness/features/RF-21-Implementation-plan.md`. The four original findings below have now
been corrected and revalidated by the coordinator; the remaining gate is the product owner's
DEC-034 visual/interaction acceptance.

## Evidence reviewed

- Complete worktree diff and every new RF-21 backend/frontend/migration/test file.
- Harness evidence: 540 local backend tests, 68 PostgreSQL/migration tests, 587 frontend tests,
  MyPy, frontend format/lint/type/build, Compose config/build and clean diff check.
- Independent rerun: 30 RF-21 backend tests, 34 focused frontend tests, strict MyPy and
  `git diff --check` all passed.
- The disposable PostgreSQL container used by the harness was removed.

## Original findings

### F1 - The five-destination mobile navigation has no 320px fit adaptation

**Severity:** High relative to the approved acceptance contract.

`frontend/src/styles.css` retains the four-destination mobile flex rules: fixed horizontal gaps,
button horizontal padding and intrinsic label minimum widths. Adding `History` in
`frontend/src/Navigation.tsx` without allowing items/buttons/labels to shrink or wrap within an
allocated fifth share cannot guarantee that all five visible labels fit at 320px. The longest
unbreakable word (`consultations`) plus the other four label widths, padding, gaps and safe-area
padding exceed the viewport's available width.

Required correction:

- adapt the mobile navigation so all five destinations fit without horizontal overflow, clipping
  or overlap at 320px and 200% text zoom;
- preserve visible labels, at least 44px touch targets, safe-area padding and keyboard focus;
- add focused structural/regression coverage and record manual/browser evidence if available.

### F2 - The frontend decoder accepts impossible cross-field authority combinations

**Severity:** Medium.

`frontend/src/consultationApi.ts:isParticipationItem` validates each field independently but accepts,
for example, `status=matched`, `event_kind=finalized`, `can_view=true`, or `status=open` with
`event_kind=finalized`. `MyParticipation` renders the View action solely from `can_view`, so a
malformed server payload can render a terminal View action instead of failing safely. The approved
contract requires Public-only open navigation and runtime rejection of malformed payloads.

Required correction:

- enforce the semantic union in the runtime decoder:
  - `open` requires `voted`; `can_view` may be true or false;
  - `matched|not_matched|no_choice` require `finalized` and `can_view=false`;
  - `unavailable` requires `voted` and `can_view=false`;
- add decoder/component tests for rejected impossible combinations.

### F3 - Outcome precedence is not complete for an anomalous open-state residual vote

**Severity:** Medium.

`backend/app/participation_service.py:_terminal_vote_select` excludes a residual vote when an
outcome exists, but `_open_vote_select` does not. The ordinary service lifecycle cannot create an
outcome while a consultation remains open, but RF-21 explicitly handles inconsistent terminal
residue and requires one row per consultation with semantic outcome precedence. If an inconsistent
row has both an outcome and an open-state residual vote, the union returns duplicate history rows.

Required correction:

- exclude any vote-derived branch when a same-account outcome exists, or deduplicate in the bounded
  SQL projection with outcome precedence;
- add a focused inconsistent-state test that proves exactly one semantic-outcome row survives.

### F4 - Validation reporting overstates the Ruff result

**Severity:** Low documentation/evidence accuracy.

The first-pass project-state entry says “Ruff check and format pass” while also recording the
pre-existing RF-37 `E501`. The full `ruff check backend` command therefore did not pass. New/changed
RF-21 files do pass Ruff, and the inherited finding remains untouched, but the evidence must say so
precisely. The pre-existing Vite high-severity audit advisory is already described accurately and
must remain visible; do not apply a forced dependency upgrade as part of RF-21.

Required correction:

- amend the project-state evidence to distinguish clean RF-21 files from the failing full-tree Ruff
  check;
- preserve the Vite advisory as an explicit pre-existing limitation.

## Acceptance trace after first pass

- Backend projection, authentication, private headers, status derivation, open/final deletion
  behaviour, pagination and additive migration: implemented and passing focused tests.
- Frontend loading/empty/error/pagination/status presentation and fifth destination: implemented and
  passing functional tests.
- Private capability non-escalation and strict field allowlist: implemented.
- 320px/200% five-destination layout: not yet demonstrated and structurally at risk (F1).
- Fail-safe semantic runtime decoding: incomplete (F2).
- One-row/outcome-precedence anomaly invariant: incomplete (F3).
- Evidence wording: correction required (F4).
- DEC-034 product-owner visual/interaction acceptance: not started.

## Corrective validation required

- Focused backend duplicate/precedence test and complete RF-21 backend tests.
- Focused frontend decoder, My participation and navigation tests.
- Prettier, ESLint, TypeScript, production build, MyPy, changed-file Ruff/format and diff check.
- Real PostgreSQL RF-21/migration tests if backend query structure changes materially.
- Responsive evidence for five destinations at 320px and 200% zoom before requesting DEC-034 owner
  acceptance.

No commit, push, deployment or Trello mutation is authorised.

## Corrective harness attempt

On 2026-10-21 the coordinator launched a new corrective OpenCode conversation with the required
`opencode-go/deepseek-v4-pro` model and `high` variant. It read the mandatory context, approved plan,
grooming, this review and the relevant implementation files, but the provider then returned
`Go usage limit exceeded`. The process produced no edits and was terminated after the provider
failure was verified. No fallback model or variant was selected.

On 2026-10-22 the product owner requested another launch. The coordinator created a fresh corrective
conversation with the same required model and `high` variant, but the provider returned the same
`Go usage limit exceeded` response on the first model call, before any repository read or edit. The
inert process was terminated after verification. Findings F1-F4 and the review status are unchanged,
and no fallback model or variant was selected.

## Coordinator corrective implementation - 2026-10-22

After the product owner explicitly asked the coordinator to perform the work directly because the
OpenCode Go subscription usage was exhausted, the coordinator corrected and independently reviewed
all four findings without launching another agent:

- **F1 resolved:** the mobile navigation now uses an equal-share responsive grid with 44px minimum
  tracks and targets, zero-gap allocation, shrink-safe items, wrapping visible labels and preserved
  safe-area/focus treatment. Below 240 CSS pixels it wraps into multiple rows and reserves matching
  content clearance. Five destinations were inspected in the built stack at a 320px viewport; all
  labels were visible without overlap, the keyboard focus ring was visible, and the History screen
  remained usable above the fixed navigation. A separate 160px viewport stress capture also retained
  every destination. The remaining DEC-034 owner pass must still confirm real-device 200% zoom.
- **F2 resolved:** `ParticipationItem` is now a discriminated semantic union and the runtime decoder
  accepts only `open/voted/(true|false)`, terminal outcome/`finalized`/`false`, and
  `unavailable/voted/false`. Seven impossible combinations fail closed in regression coverage.
- **F3 resolved:** the open-vote query now excludes an account outcome just like the terminal-vote
  query. SQLite and real-PostgreSQL regressions prove a deliberately inconsistent open consultation
  with both an outcome and residual vote returns exactly one authoritative finalized outcome row.
- **F4 resolved:** the project-state evidence now distinguishes clean RF-21 changed-file Ruff checks
  from the inherited full-tree RF-37 `E501` failure.

Corrective evidence:

- 31 focused participation backend tests and 43 focused frontend tests passed.
- The complete backend suite passed; 596 frontend tests passed across 45 files.
- Six real-PostgreSQL RF-21 query/migration tests passed against a disposable PostgreSQL 18
  container, including the new outcome-precedence regression; the container was removed.
- Changed-file Ruff/format, strict MyPy, Prettier, ESLint, strict TypeScript, production build,
  Compose config/build and `git diff --check` passed.
- The full backend Ruff check still reports only the pre-existing RF-37 `E501` at
  `20261019_0006_media_erasure.py:83`; it was not edited.
- `npm audit --audit-level=high` still reports the pinned Vite high advisory plus two moderate Vitest
  advisories. No forced dependency update was made because dependency remediation is outside RF-21.
- The disposable visual-validation Compose project and its volumes were removed.

RF-21 is technically ready for the product owner's DEC-034 visual/interaction acceptance. This
review does not record that acceptance or claim `Completed and validated`. No commit, push,
deployment or Trello mutation occurred.
