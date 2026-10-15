# RF-14 - Independent implementation review

## Product-owner closure - 2026-10-15

After receiving this review and validating the displayed UI, the owner explicitly instructed
Codex to treat RF-14 as closed in its current state: `que des por cerrada RF-14 y ya`.
The repository lifecycle is therefore `Completed and validated` by product-owner decision.
The findings and failed probes below remain accurate known technical debt; this closure does not
claim that they were corrected or that the failing evidence passed.

Codex briefly started a correction run after misinterpreting the preceding instruction. It was
stopped immediately when the owner clarified the request, exited with code 1, and changed no
implementation, test or documentation file. No commit, push, deployment or Trello mutation occurred.

## Owner UI feedback - 2026-10-15

The owner opened the isolated RF-14 UI and reported `Se ve del carajo. Que va siguiente ?`.
This records positive acceptance of the displayed presentation only, with no inferred
viewport/zoom/keyboard/device coverage. Required technical corrections below remain open;
this feedback does not certify the full increment or authorize a correction-harness launch.

## Outcome - 2026-10-15

Superseded by the explicit product-owner closure above. At the time of this review, corrections
were required before independent technical acceptance. The authorized OpenCode Go deepseek-v4-pro/high run
(execution handle 66045) exited with code 0. Its completion message is a report, not
acceptance. This review supersedes claims of full scope, strict cursor validation,
complete preview cleanup and accessible modal behavior in that report/project-state entry.

No correction run has been launched by this review. No application fix, commit, push,
deployment or Trello mutation was performed by the coordinator. The product owner
retains visual acceptance under DEC-034; no visual inspection/screenshots/zoom occurred.

## Preservation and evidence

Compared all 174 prelaunch source files with SHA-256 manifest at
`C:/Users/anton/AppData/Local/Temp/nextpost-rf14-20261015-183337-rgwwgy2n`.
No file is missing. Changed baseline files are exactly:

- backend/app/api/consultations.py, consultation_service.py, main.py, schemas.py.
- frontend/src/App.tsx, App.test.tsx, OwnerConsultationDetail.tsx,
  consultationApi.ts, consultationApi.test.ts, styles.css.
- harness/context/04_PROJECT_STATE.md (coordinator launch and harness report entries).

These changes correspond to the feature boundaries; unrelated baseline files, including
the existing lockfile, migrations, environment/configuration and prior feature plans,
remain byte-identical. New feed/reader/preview components/tests and isolated validation
helpers are present. The approved RF-14 plan and prior decisions are unchanged.

Independently rerun after harness exit:

- Existing frontend suite: 30 files, 384 passed.
- Existing backend suite: 353 passed, 13 skipped without TEST_DATABASE_URL; these skipped
  PostgreSQL tests are not independently claimed passed by this run.
- Six additional targeted frontend review probes: all six fail as detailed below.
  Source is preserved in harness/validation/rf14_review_reproductions.tsx. It was
  temporarily run as frontend/src/RF14IndependentReview.test.tsx, then moved out of the
  ordinary suite to preserve the evidence without silently changing existing green tests.
- Direct backend probes: an invalid-alphabet cursor and noncanonical UUID cursor are
  accepted; anonymous feed returns 401 without any of the three required private headers.

Observed harness validation, distinguished from independent reruns:

- 366 backend tests passed with no skips on disposable PostgreSQL 18.
- 384 frontend tests; format/lint/types/build and dependency audit passed (0 vulnerabilities).
- Backend Ruff/format/mypy, Compose config/build passed.
- Built two-account HTTP smoke passed: Public-only chronology, own flag, first-photo order,
  Private exclusion, successful protected-read headers, seeded terminal denial and restart.
  This serves the frontend but does not exercise its actual Home DOM/preview/detail navigation.
- Disposable RF-14 Compose services/volumes and test PostgreSQL container were removed.
  The pre-existing RF-12 and ordinary project containers were left intact.

## Required corrections

### F1 [P1] Preview requests survive their scope and can replace newer content

frontend/src/useFeedPreviews.ts:56-88 has no request-generation/mounted check in the
error path; success checks only current active/visible flags, not the originating request.
Clearing inflight/requested sets is not cancellation and does not invalidate a promise.

Reproduced: start a photo read, unmount, then reject with unauthenticated. The old view
still calls onSessionLost (expected 0 calls, actual 1), which can dismiss a later account.
Also reproduced: deactivate/reactivate the same card, resolve new request first then old.
The old blob replaces the new blob, and the overwritten new URL loses its cleanup owner.
Visibility/ref removal also drops inflight accounting while actual requests are pending,
so request concurrency can exceed four during churn even though the static bound test passes.

Give each actual request an immutable scope/generation and explicit URL ownership. Ignore
all late success/error/401 paths, revoke uninstalled late URLs, preserve accounting for
uncancelled requests and prevent old finalizers deleting a newer request's bookkeeping.
Add unmount/account-change, off/on/Back, response-order, partial-failure and churn tests.

### F2 [P2] List navigation, Refresh and Back do not implement the agreed contract

frontend/src/useHomeFeed.ts:90 always refreshes the previous loaded page count; the
same function is used for explicit Refresh and Back. After two pages, Refresh performs
two page reads (four total including initial/load-more), rather than one newest-page read
(three total). Reproduced by a targeted hook test.

HomeFeed.tsx:33 only sets selected; useHomeFeed remains mounted and does not invalidate
pending list reads. Reproduced: pending Load more, open reader, reject the hidden page
with 401; onSessionLost still fires. Hidden success can likewise replace retained range.

There is no nonprogressing/repeated-cursor check. No scroll anchor/offset is captured.
Back focus is attempted immediately after async state replacement without ensuring commit;
if the card disappears, the optional element lookup does not fall back to the heading.
refreshFailed is rendered only in the nonempty branch, so a failed empty-feed refresh
has no failure feedback. Denied-preview placeholder offers no Refresh feed action there.

Separate explicit one-page Refresh from bounded Back reconciliation, suspend/invalidate
list scope on detail entry, guard cursor progress, restore anchor/focus after commit with
heading fallback, and cover retryable refresh failures in empty/nonempty/denied states.

### F3 [P2] Missing visibility-observer fallback leaves every preview unloaded

frontend/src/useFeedPreviews.ts:102 returns null without IntersectionObserver; observe
neither marks the card visible nor schedules another visibility mechanism. Reproduced:
an observed card makes zero photo reads when the observer is unavailable. The plan
explicitly requires a safe fallback. Implement a bounded fallback with the same cleanup
and authorization rules; keep it covered without enabling unbounded eager preload.

### F4 [P2] Photo dialog lacks keyboard containment and background isolation

frontend/src/PhotoEnlargement.tsx:13 focuses Close and handles Escape, but does not trap
Tab/Shift+Tab or isolate background actions. aria-modal alone does not implement either.
Reproduced: Tab from Close moves focus to body (and a subsequent tab can reach background)
instead of keeping focus inside. Add real containment/inert background and verify focus
return, Escape, Close, keyboard navigation and account/detail changes without visual inspection.

### F5 [P2] Own Home detail misses equivalent photo inspection and loading Back

frontend/src/OwnerConsultationDetail.tsx only adds the home label variant. Its photos at
line 189 remain plain img elements, with no enlargement action. The loading branch has
no Back button. The approved plan explicitly requires own Home detail to support equivalent
inspection and loading exit while preserving existing success/My contexts. Reuse the
corrected small image dialog/presenter, add the Home loading Back path, and test all entry
contexts plus finalized reconciliation. Do not weaken owner authorization or add future actions.

### F6 [P2] Feed cursor parsing accepts invalid grammar and noncanonical IDs

backend/app/consultation_service.py:263 uses permissive urlsafe_b64decode and uuid.UUID
without an alphabet/canonical-form check. Independent probes confirm `!!!` prepended to
a valid cursor is accepted, and a cursor containing a UUID's 32-character hex form is
accepted. datetime.fromisoformat also accepts forms beyond the stated timestamp grammar.
The harness's strict-alphabet claim is incorrect. Enforce the approved grammar/tuple/version/
actual UTC calendar/canonical UUID/length, preserve safe 422 and test each invalid form.

### F7 [P2] Protected errors do not carry the approved privacy headers

Only successful feed/detail/photo responses and ConsultationError use the private header
helper. HTTPException from authentication/denied reads, request validation and PhotoError
do not use it. Independently observed anonymous GET /api/consultations/feed: 401 with
Cache-Control, Referrer-Policy and X-Content-Type-Options all absent. Cover the exact
feed/general-detail/photo boundaries consistently for success and 401/422/404/503/5xx.
Do not broaden unrelated public endpoints or change error content/cause disclosure.

## Validation and documentation gaps

- The new PostgreSQL fixture drops/recreates ORM metadata for every feed test. Its tests
  prove PostgreSQL query behavior, not the planned query suite against an Alembic-upgraded
  schema. Keep test isolation but install existing Alembic head in a disposable dedicated
  test database/schema; do not turn a global feed test into an active-data cleanup operation.
- The built smoke covers HTTP only; serving the JS bundle does not prove actual Home
  preview/detail/Back behavior. Add focused nonvisual built-client interaction evidence
  after the corrections, distinct from owner visual acceptance.
- README has no RF-14 update (byte-identical to prelaunch), despite the approved affected
  documentation boundary. Document implemented discovery and remaining vote/share/terminal limits.
- Promote the targeted repros to meaningful permanent regression tests when fixing their
  behaviors. Do not weaken/remove assertions merely to preserve the existing pass count.

## Acceptance audit

Numbers refer to the ordered acceptance criteria in RF-14-Implementation-plan.md.

| Criteria | Review result |
| --- | --- |
| 1-3: eligible chronological Home, own marker, card content/Photo 1 | Implemented in code and covered by service/component tests and observed HTTP smoke; actual built Home interaction remains unverified |
| 4: bounded previews, retry, denial, complete cleanup | Not accepted: F1/F3; denied refresh path in F2 |
| 5: pagination/Refresh/Back range/anchor/focus | Not accepted: F2 |
| 6: other-author complete read/enlargement | Core read/media implemented; modal accessibility not accepted (F4) |
| 7: authorized own Home detail and existing entries | Core owner routing implemented; own inspection/loading exit gap F5 |
| 8: distinct loading/error/denial/401 and no stale content | Partially covered; F1/F2 and empty refresh error gap remain |
| 9: strict payload/header/current server authorization | Eligibility/association rules present; F6/F7 remain |
| 10: session/scope supersession | Not accepted: F1/F2, independently reproduced |
| 11: no voting/results/terminal/Private discovery/new infrastructure | No prohibited feature found; prior model/migration/package files preserved |
| 12: composer/publication/owner/auth regression | Existing suites pass; F1's late callback can invalidate a later account |
| 13: full checks/PG/built evidence and separate manual gates | Existing suites pass; additional probes fail; migrated-query/nonvisual built-client gaps above; visual/device still external |
| 14: limited completion documentation and preserved authority | State corrected to Implementation review; README update pending; no external mutation |

## Reproduction notes

The coordinator's six frontend probes can be rerun by copying
harness/validation/rf14_review_reproductions.tsx to the unused temporary path
frontend/src/RF14IndependentReview.test.tsx, running
`npx vitest run src/RF14IndependentReview.test.tsx` from frontend, then removing only
that temporary copy. Its relative imports intentionally resolve from frontend/src.
Keep the preserved source as review evidence until corrections incorporate the tests.
Existing baseline suites run through the exact commands in the approved plan.

No acceptance of physical photo deletion, actual terminal operations, vote/results,
owner visual review or real iPhone/TestFlight is inferred from these checks.
