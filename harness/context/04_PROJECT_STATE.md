# Project State

## RF-26 completed and validated - 2026-10-19

The product owner completed the private-LAN mobile review and explicitly reported `VALIDADO`.
Together with the approved plan, successful harness run, independent review, 486 passing frontend
tests, 405 passing local backend tests plus expected skips, clean quality/build/audit checks and the
rebuilt multi-account PostgreSQL smoke, this closes RF-26 as `Completed and validated`.

The temporary `nextpost-rf26-lan-20261019` services are stopped. Its isolated database and photo
volumes remain recoverable; ordinary project services and data were not touched. No commit, push,
deployment or Trello mutation occurred.

The recommended next grooming ticket is RF-37, `Proteger y borrar fotografías`. The accepted backlog
ordering requires its published-photo revocation, physical-deletion and retry contract before the
terminal mutations in RF-13 and the coordinated RF-19/RF-20 finalization flow.

## RF-26 disposable LAN review instance running - 2026-10-19

At the product owner's request, RF-26 is exposed to the current private Wi-Fi network through
an isolated Compose project, `nextpost-rf26-lan-20261019`. The recorded host address is
`192.168.1.130`, with frontend port `14177`, API port `18004`, and PostgreSQL remaining localhost
only on `15436`. `harness/validation/rf26-lan.override.yaml` records the LAN binding. This is a
temporary review environment with dedicated database/photo volumes, not a deployment.

The rebuilt frontend and API both respond through the LAN address: `/` and a direct consultation
path returned HTTP 200, `/api/ready` returned `ok`, and the backend/database health checks are green.
The instance starts empty so the owner can register fresh review accounts and consultations.

The browser origin is plain private-LAN HTTP. It supports the RF-26 web/auth/link flow, but mobile
browsers may withhold `navigator.share` because Web Share is normally restricted to secure HTTPS
contexts. No commit, push or Trello mutation is authorized by this launch.

## RF-26 implemented and independently reviewed; visual acceptance pending - 2026-10-19

The approved RF-26 implementation is present and the autonomous OpenCode harness completed
successfully. The coordinator independently reviewed the route/auth return, server-derived
owner/reader boundary, Public/Private sharing, revocation behavior, privacy headers and mobile Share
state machine. One uncovered synchronous `navigator.share()` failure path was corrected and new
registration, Private-fragment, history, session-loss and Share concurrency tests were added.

Final evidence is 486 passing frontend tests; 405 passing backend tests with 28 expected local
PostgreSQL-only skips; clean Ruff/format/mypy/Prettier/ESLint/typecheck; successful production and
Compose builds; zero npm audit vulnerabilities; and a passing isolated rebuilt multi-account smoke
covering direct SPA fallback, anonymous denial, Public roles, forwarded Private access and
missing/wrong/replaced/disabled token denial. The disposable containers and volumes were removed.
Full evidence is in `harness/grooming/RF-26-implementation-review.md`.

RF-26 is `Implementation review`. The sole remaining gate is the product owner's visual and actual
iPhone Share-sheet validation under DEC-034, which the owner explicitly reserved. No commit, push,
deployment or Trello mutation occurred.

## RF-26 implementation launched - 2026-10-19

The product owner explicitly authorized autonomous harness launch after approving the settled
scope and plan finalisation. Preflight confirmed
`harness/features/RF-26-Implementation-plan.md` is `Ready for implementation` with
`Remaining questions: None`, project state names the same active ticket, OpenCode Go is
authenticated, and `opencode-go/deepseek-v4-pro` remains active with the required `high`
variant. RF-26 is `Implementation in progress`.

The 62 prelaunch dirty tracked/untracked files were copied to the recoverable snapshot
`C:\Users\anton\AppData\Local\Temp\NextPost-RF26-prelaunch-20261019-144701`.
They include the accepted RF-14/RF-16/RF-18 and real-device correction baseline plus RF-26
planning documentation and must be preserved. The harness is instructed to implement only
RF-26, run executable technical validation and leave subjective UI/visual review to the product
owner under DEC-034. Commit, push, deployment, Trello mutation and native distribution remain
unauthorized.

## RF-26 plan ready; autonomous implementation harness authorized - 2026-10-19

The product owner explicitly approved the settled RF-26 scope, finalisation of the English
implementation plan and autonomous launch of the external implementation harness. The owner
selected `1A 2A 3A 4A 5A 6A 7A 8B`; DEC-040 records the durable behavior.

`harness/features/RF-26-Implementation-plan.md` is `Ready for implementation` with
`Remaining questions: None`. It defines author-only Public/Private Copy and capability-detected
device Share, generic payload/manual fallback, one narrow consultation History API entry,
safe destination return after session restoration/sign-in/registration, server-derived owner
versus reader routing, current-token voting and generic revocation/terminal denial. Shared links
use the strictly validated current `window.location.origin`; no schema migration, app-wide router,
contact/invitation/messaging/social-posting or native deep-link infrastructure is planned.

The external harness launch is authorized. It must preserve the substantial existing dirty
worktree, implement only RF-26, run technical validation and leave subjective browser/UI review
for the product owner under DEC-034. Commit, push, deployment, Trello mutation and native
distribution are not authorized.

## RF-26 material choices confirmed - 2026-10-19

The product owner selected `1A 2A 3A 4A 5A 6A 7A 8B`. Sharing is author-only on every
open Public or Private owner detail, with Copy always present, capability-detected device
Share and a manual-copy fallback. The share payload is generic NextPost invitation text
plus the URL. RF-26 will add only a narrow consultation URL/history boundary; generic
authentication preserves and resumes the validated destination after sign-in or registration.
An author opening their own shared URL receives neutral owner detail, while a non-owner uses
the existing reader/vote flow. Direct entry offers Go to Home and leaves browser Back intact.

Shared URLs will continue to use the strictly validated current `window.location.origin`,
not a new canonical-origin setting. This preserves simple LAN/device-review behavior and
accepts that deployment must expose the intended production origin or a wrong proxy/host
will appear in copied links. DEC-040 records the durable behavior.

RF-26 is now `Grooming - awaiting product-owner confirmation`. No material question remains
identified. The settled scope, exclusions, security/privacy contract, failure behavior,
dependencies and validation direction are recorded in `harness/grooming/RF-26-grooming.md`.
No implementation plan has been created: explicit approval of the settled scope and plan
finalisation is still required, and a harness launch would require a later independent request.
No implementation, test run, visual inspection, commit, push, deployment, service operation
or Trello mutation occurred.

## RF-26 grooming started - 2026-10-19

The product owner explicitly selected `RF-26 · Compartir una consulta e invitar a votar`.
The current card was consumed read-only from the configured APP - NextPost board:
https://trello.com/c/47FD3mrW/28-rf-26-compartir-una-consulta-e-invitar-a-votar.
It is open and incomplete in `Próximo · completar el MVP`, with no labels, members,
dates, checklists, comments, attachments or custom-field values. Its complete current
description, criteria, metadata and available activity are captured in
`harness/grooming/RF-26-grooming.md`. RF-26 is `Grooming - questions open`.

Repository-first inspection confirms that RF-09/RF-10 already provide strict same-origin
Public/Private URL helpers, versioned fragment capabilities, current database link
revocation/rotation and protected detail/media endpoints; RF-12 recovers real owner detail
and Private controls; RF-14/RF-16 provide real reader comparison and current-token voting.
Copy exists for Private owners, but Public has no copy/share action, no device Share API is
used, direct `/consultations/{uuid}` URLs are not routed, and App currently forces Home
after restoration, sign-in and registration. The accepted recipient journey therefore
does not work yet.

The grooming recommends a narrow History-API consultation route using the existing strict
parser, with the original path/fragment as the reload-safe source of truth and no arbitrary
redirect or persistent token storage. It recommends author-only Copy plus capability-detected
device Share for both audiences, generic share/auth copy, direct return after either auth
flow, a neutral owner detail when the author opens their own link, generic unavailable for
revoked/terminal targets and a configured production public origin. Eight material choices
cover share placement/actor, fallback presentation, share payload, routing scope, author
self-entry, unauthenticated entry copy, leaving direct detail and production origin. These
are proposals only; no answer is inferred.

No RF-26 implementation plan has been created. Product-owner answers and later explicit
plan-finalization approval are required; any harness launch requires a subsequent independent
request. Existing tracked/untracked implementation and documentation work is preserved. No
implementation, test run, visual inspection, commit, push, deployment, service operation or
Trello mutation occurred.

## RF-18 completed and validated - 2026-10-19

The product owner reviewed RF-18 on the real mobile/LAN flow with an actual three-photo Public
consultation. Nine distinct disposable voter accounts cast immutable votes, producing verified
author aggregates of 4, 3 and 2 votes (9 total). The owner then explicitly requested closure,
satisfying the DEC-034 visual-acceptance gate.

RF-18 is now `Completed and validated`. The accepted increment provides author-only live Open
counts in My consultations and owner detail, including zero options and natural ties, with
non-overlapping five-second visible-view refresh and no voter identities or participant aggregate
access. Percentages and durable finalized/photo-free results remain explicitly deferred to their
documented RF-19/RF-20/RF-37 boundary and are not part of this completion claim.

The disposable `nextpost-rf18-lan-20261019` frontend, backend and database containers were stopped
cleanly after review. Their isolated volumes were retained for recoverability; ordinary services
and data were not touched. No commit, push, deployment or Trello mutation occurred.

## RF-18 disposable LAN review instance launched - 2026-10-19

At the product owner's request, a rebuilt disposable RF-18 review instance is running under the
isolated Compose project `nextpost-rf18-lan-20261019`. The mobile URL is
`http://192.168.1.130:14176`; its browser bundle targets the LAN API at
`http://192.168.1.130:18003`. Host checks returned HTTP 200 for the frontend and API readiness, the
backend/database report healthy, and PostgreSQL remains bound only to localhost on port 15435.

The instance uses new isolated database/photo volumes and contains no seeded accounts or
consultations. `harness/validation/rf18-lan.override.yaml` records the current LAN binding. This is
a temporary owner-review environment, not a deployment. It was launched for DEC-034 visual and
real-device acceptance; the later closure entry records its clean stop. No commit, push or Trello
mutation occurred.

## RF-18 implemented and independently reviewed; visual acceptance pending - 2026-10-18

The external OpenCode harness implemented the approved RF-18 live Open, count-only increment and
completed executable validation. The coordinator independently reviewed the work against every
acceptance criterion and recorded the evidence in
`harness/grooming/RF-18-implementation-review.md`.

Delivered behavior includes author-only total counts in Open My consultations rows, exact per-photo
counts in owner detail, zero-vote options and natural ties, immediate plus non-overlapping five-second
visible-view refresh, honest stale/error/unavailable handling and strict aggregate payload guards.
Participants and general consultation surfaces remain aggregate-free; no identity, individual choice,
percentage, ranking or winner is exposed. No migration, counter cache or finalized snapshot was added.

Harness evidence is 420 passing PostgreSQL tests, 448 passing frontend tests before review additions,
clean quality/build/audit checks and a passing rebuilt-stack smoke covering zeros, ties, privacy and
restart persistence. Coordinator review corrected exact-list 401 private headers, explicit nonnegative
response constraints, unavailable-result presentation/poll stop and missing visibility-transition
coverage. Final evidence includes 451 passing frontend tests, 393 passing local backend tests with the
28 PostgreSQL-only cases skipped locally, 43 focused backend tests, 149 focused frontend tests and
clean Ruff/format/mypy/Prettier/ESLint/types/build/audit/Compose/diff checks.

RF-18 is `Implemented and independently reviewed - awaiting product-owner visual acceptance` under
DEC-034. Percentages and durable finalized/photo-free results remain the documented RF-19/RF-20/RF-37
gate, so the broader Trello card is not complete. No commit, push, deployment or Trello mutation
occurred.

## RF-18 harness launch blocked by expired OpenCode Go API key - 2026-10-18

The coordinator completed the RF-18 preflight, recorded the existing dirty worktree in the
recoverable snapshot `C:\Users\anton\AppData\Local\Temp\NextPost-RF18-prelaunch-20261018`, and
verified that `opencode-go/deepseek-v4-pro` with the `high` variant remains active in the installed
model catalog. A new OpenCode implementation conversation was then launched with the approved
plan and exact configured model, but it exited before performing any task work because the OpenCode
Go API key has expired. The CLI requires a new key from OpenCode Console to replace the local
credential and explicitly says signing in again will not renew it.

No alternate provider/model was selected and no implementation or validation ran. RF-18 remains
`Ready for implementation`; the approved launch should be retried only after the product owner has
replaced the expired OpenCode Go API key. No commit, push, deployment or Trello mutation occurred.

## RF-18 plan ready; implementation harness authorized - 2026-10-18

The product owner explicitly approved all settled RF-18 decisions, finalisation of the plan and
launch of the external implementation harness. `harness/features/RF-18-Implementation-plan.md` is
`Ready for implementation` with `Remaining questions: None`. The approved increment adds
author-only live counts to Open My consultations: total votes in list rows and exact per-photo
counts in owner detail, including zero options and natural ties, refreshed immediately and every
five seconds only while the relevant view is visible.

Percentages, voter aggregate access, voter identities and individual choices remain prohibited.
No migration or denormalized counter is planned. Finalized aggregate snapshots/presentation remain
an explicit RF-19/RF-20/RF-37 gate, so the broader Trello card must not be claimed complete by this
increment. Existing dirty RF-16/device-correction work is the baseline and must be preserved. The
harness launch is authorized; commit, push, deployment, visual acceptance and Trello mutation are
not.

## RF-18 material choices confirmed - 2026-10-18

The product owner selected `1A`, `2B` with a five-second automatic refresh, a custom count-only
answer to Q3, and `4A`. My consultations Open rows will show total votes; open owner detail will
show exact per-photo counts in immutable order, including zeros and natural ties. Percentages,
leader/winner presentation and all voter aggregate access are excluded from this first increment.

The relevant Open list/detail scope refreshes immediately and every five seconds while visible,
without overlapping requests or hidden/unmounted polling. Failed refresh preserves identified
last-known counts and manual Refresh remains available. RF-18 derives current counts from Vote
rows without denormalized counters or a migration. Finalized photo-free snapshots/display remain
an explicit RF-19/RF-20/RF-37 consumer gate. DEC-039 records the accepted cross-feature behavior.

RF-18 is now `Grooming - awaiting product-owner confirmation`. No material question remains
identified. The settled scope, privacy boundary, failure behavior, dependencies and validation
direction are recorded in `harness/grooming/RF-18-grooming.md`. No implementation plan has been
created: explicit approval of the settled scope and plan finalization is still required, and a
harness launch would require a later independent request. No implementation, test run, visual
inspection, commit, push, deployment, service operation or Trello mutation occurred.

## RF-18 grooming started - 2026-10-16

The product owner explicitly selected `RF-18 · Consultar resultados como autor`. The current
card was consumed read-only from the configured APP - NextPost board:
https://trello.com/c/GBfvkzU8/19-rf-18-consultar-resultados-como-autor.
It is open and incomplete in `Próximo · completar el MVP`, with no labels, members, dates,
comments, checklists, attachments or custom field values. Its complete current description,
criteria, metadata and available activity are captured in `harness/grooming/RF-18-grooming.md`.
RF-18 is `Grooming - questions open`.

Repository-first inspection confirms RF-12's private My consultations list/owner detail and
RF-16's immutable Vote model, composite option integrity and aggregate-supporting index are
present. No aggregate result service, schema, endpoint, persisted snapshot or author result UI
exists. A set-wise owner-scoped outer join can derive current open counts while preserving
zero-vote options and immutable photo order; voters/general readers must remain aggregate-free.

Four material choices remain: whether the private list also shows total votes; explicit refresh
versus polling; percentage/tie/leader presentation; and whether this increment delivers the
safe open result slice now or waits/adds speculative persistence for the currently unavailable
finalization/photo-deletion consumers. The grooming recommends a private list total plus full
owner-detail results, explicit Refresh, one-decimal non-ranked presentation, and a coherent live
Open increment with finalized snapshot/display retained as an explicit RF-19/RF-20/RF-37 gate.
No recommendation is accepted yet.

No RF-18 implementation plan has been created. Product-owner answers and later explicit plan-
finalization approval are required; any harness launch requires a subsequent independent request.
Existing tracked/untracked RF-16 and device-correction work is preserved. No implementation,
test run, visual inspection, commit, push, deployment, service operation or Trello mutation occurred.

## RF-07 real-iPhone photo compatibility confirmed; LAN Private-detail crash corrected - 2026-10-16

The product owner successfully created a Private consultation from an iPhone after the upload
pipeline correction. Safari supplied the selected still photos as two-frame MPO JPEG containers;
the backend now extracts and normalizes the primary image instead of rejecting the companion frame.
This confirms the real-device upload path that had previously failed.

Opening that Private consultation then produced a blank page even though the owner detail, both
photo bodies and the Private-link request all returned HTTP 200. The cause was client-side origin
validation: rendering the share control synchronously rejected the disposable LAN origin
`http://192.168.1.130:14175`. Private/link-local IP origins are now accepted for HTTP device review,
public HTTP origins remain rejected, and link construction is guarded so an invalid deployment
origin cannot crash the entire detail view. The focused regression tests and the complete 419-test
frontend suite pass, as do ESLint, strict typecheck, formatting and the production build. The fixed
frontend image is live in the disposable LAN review instance. The product owner subsequently
confirmed the corrected Private detail on the real iPhone and accepted it for closure.

During the same owner-device review, Home exhibited vertical scroll drift while preview requests
crossed the viewport. The preview slot changed from a 140px idle placeholder to a much shorter
loading status and then to the photo's rendered height; IntersectionObserver-driven unload/reload
made those layout shifts repeat around the viewport boundary. Feed cards now reserve one stable,
metadata-derived and bounded photo frame across idle, loading, ready and error states. The complete
419-test frontend suite and all frontend quality/build checks pass. The product owner confirmed the
corrected Home scrolling on the real iPhone and explicitly requested closure.

During the RF-16 owner UI session, a real iPhone selected six gallery photos: two normalized
successfully while four HEIF uploads repeatedly returned HTTP 422. Inspection found that the
processor treated every multi-image HEIF container as animation, despite the approved RF-07
contract requiring the primary still to be accepted when companion or auxiliary images exist.

`backend/app/imaging.py` now distinguishes HEIF still-image brands from HEIF sequence brands. It
normalizes the declared primary still from a multi-image HEIF container while continuing to reject
actual HEIF image sequences and animated non-HEIF inputs. Regression tests cover both cases. The
focused imaging/photo suite, Ruff checks and the full backend suite pass; the rebuilt disposable
container also normalized a multi-image HEIF primary to JPEG and retained the LAN CORS contract.

The correction is live in the disposable review instance. The later owner-device retry successfully
created a Private consultation from the iPhone photos. No commit, push, deployment or Trello
mutation occurred.

The owner's attempt to attach one rejected photo for diagnosis arrived as a JPEG and passed the
same live API, confirming that the iPhone/attachment path can provide a compatible representation.
The RF-07 picker now requests JPEG first and no longer explicitly requests HEIC/HEIF, allowing
WebKit's platform picker to transcode iPhone HEIF photos before upload. The backend retains actual
HEIC/HEIF decoding as defense in depth. All 418 frontend tests plus format, lint, strict typecheck
and production build pass, and the rebuilt LAN review bundle was verified to contain the new picker
contract. The later owner-device publication satisfied this acceptance gate.

## RF-16 completed and validated - 2026-10-16

The coordinator independently reviewed the RF-16 worktree against the approved plan and recorded
the result in `harness/grooming/RF-16-implementation-review.md`. Four client gaps found after the
harness handoff were corrected: chosen-photo review rendering, combined detail/vote Refresh,
Private-token change reauthorization and post-reconciliation Home focus. Focused tests cover them.

Current evidence includes the harness's 398-pass PostgreSQL suite and isolated built-stack smoke,
plus the coordinator's 45-pass focused backend suite and final 418-pass frontend suite. Backend
Ruff/format/mypy, frontend format/lint/types/build, dependency audit (0 vulnerabilities), Compose
configuration and diff checks pass. No material automated failure remains.

During the real-iPhone review, the owner also exercised iPhone photo publication, Private owner
detail and Home scrolling. The discovered HEIF/MPO normalization, LAN Private-link render crash and
preview layout-shift defects were corrected; the final frontend suite has 419 passing tests. The
owner confirmed the corrected behavior and explicitly requested closure, so RF-16 is now
`Completed and validated` under DEC-034. RF-18 remains the agreed next grooming ticket. No commit,
push, deployment or Trello mutation occurred.

## RF-16 implementation evidence recorded - 2026-10-16

The external OpenCode harness implemented the approved RF-16 plan
(`harness/features/RF-16-Implementation-plan.md`). This entry records the harness's own
validation evidence only; it is not an independent acceptance or a `Completed and validated`
claim. The coordinator must still review the worktree against every acceptance criterion,
and the product owner retains visual acceptance under DEC-034.

Implemented:

- Backend `Vote` model plus Alembic revision `20261016_0005_votes.py` (one immutable vote per
  `(consultation_id, voter_id)`, composite `(consultation_id, consultation_photo_id)` foreign key
  backed by a new `(consultation_id, id)` candidate key on `consultation_photos`, aggregate-support
  index, restrictive foreign keys and populated-downgrade refusal).
- `backend/app/vote_service.py` (locked submission with `FOR UPDATE`, current-state
  `AccessOperation.vote` authorization, exact-replay and different-winner conflict semantics).
- `GET /api/consultations/{id}/my-vote` and `POST /api/consultations/{id}/votes` with trusted-origin
  protection and private `no-store`/`nosniff`/`no-referrer` headers. The feed now carries a
  server-derived set-wise `has_voted` boolean.
- A middleware applying the private headers to every `/api/consultations/` success and error path
  (F7), plus the bounded F1 preview scope/ownership, F2 one-page-Refresh/bounded-Back-reconcile/
  detail-entry-suspend, and F4 dialog focus-containment repairs.
- Frontend vote clients (`fetchMyVote`/`submitVote` + strict guards), `FeedCard` `Voted` marker,
  and the reader selection/review/cancel/confirm/`Your vote`/reconciliation state machine with
  optional Private-token support.

Harness validation evidence (this environment):

- Backend against a disposable PostgreSQL 18 (`TEST_DATABASE_URL`): 398 passed, 0 skipped,
  including new `test_votes.py`, `test_votes_postgres.py` (row-lock races and a seeded terminal
  writer) and `test_votes_migration.py` (fresh upgrade, `0004 -> head` preservation, direct-SQL
  uniqueness/same-consultation integrity, empty downgrade and populated-downgrade refusal).
  Ruff check/format and strict mypy are clean.
- Frontend at harness handoff: 405 passed. Prettier, ESLint, strict typecheck and production build
  passed.
- Isolated built-stack two-account smoke (`harness/validation/rf16_built_smoke.py` +
  `rf16-compose.override.yaml`, disposable volumes removed afterwards) passes: create/replay/
  conflict, self-vote denial, viewer-scoped recovery, Home `has_voted`, current-Private vote and
  revoked-link denial, sign-in recovery and restart persistence, with no aggregate exposure.

No commit, push, deployment, visual inspection or Trello mutation was performed. Owner visual
acceptance (DEC-034), independent review and the future RF-18/RF-19/RF-20/RF-26/RF-37 consumer
gates remain open.

## RF-16 plan ready and harness authorized - 2026-10-16

The product owner explicitly approved the settled RF-16 scope, finalized English plan and
harness launch. `harness/features/RF-16-Implementation-plan.md` is `Ready for implementation`
with `Remaining questions: None`. It preserves `1A 2A` in DEC-038 and defines the bounded
vote persistence, API, UI, concurrency, privacy and RF-14 prerequisite work.

Implementation has not yet been validated or declared complete. The pre-launch worktree includes
only RF-16 grooming/context/plan documentation changes. No commit, push, deployment, visual
acceptance, service mutation or Trello mutation has occurred.

## RF-16 material choices confirmed - 2026-10-16

The product owner answered `1A 2A`. An already-voted Public consultation remains in its
normal chronological Home position and gains a server-derived `Voted` marker for that
account. Opening it identifies only that account's recorded photo as `Your vote` and states
that the vote cannot be changed. No aggregate, other-voter or winner signal is authorized.
DEC-038 records the accepted cross-feature behavior.

At that transition RF-16 was `Grooming - awaiting product-owner confirmation`. No material question remained
identified. The settled scope, transaction/data/API approach, RF-14 prerequisite-debt split,
future-ticket boundaries and validation direction are recorded in RF-16-grooming.md. No
implementation plan has been created: the owner must still explicitly approve the settled
scope and finalization of the self-contained English plan. A harness launch would require a
later independent request. No implementation, test run, visual inspection, commit, push,
deployment, service operation or Trello mutation occurred.

## RF-16 grooming started - 2026-10-15

The product owner explicitly selected `RF-16 · Emitir un voto independiente`. The current
card was consumed read-only from the configured APP - NextPost board:
https://trello.com/c/rzoUcPdL/17-rf-16-emitir-un-voto-independiente.
It is open and incomplete in `Próximo · completar el MVP`, with no labels, members,
dates, checklists, comments, attachments or custom field values. Its complete current
description, acceptance criteria, metadata and available activity are captured in
`harness/grooming/RF-16-grooming.md`. RF-16 is `Grooming - questions open`.

Repository-first inspection confirms RF-14 discovery and protected reader detail are
present, but no Vote model, migration, service, API, aggregate or vote UI exists. The
recommended unaccepted increment adds one immutable vote per consultation/account, a
viewer-scoped vote-status read, transactional current-state/access checks under a
PostgreSQL consultation lock, database uniqueness and same-consultation option integrity,
plus single-selection/review/cancel/confirm and ambiguous-response recovery in the reader
detail. Public is reached from Home; the same contract accepts an authorized Private token,
while RF-26 retains actual Private link entry and post-authentication return.

RF-14's known debt was assessed rather than silently absorbed. F1 stale preview callbacks,
the F2 hidden-list/Back subset, F4 modal keyboard isolation and F7 protected-path headers
are necessary prerequisites for RF-16's session, navigation, accessibility and privacy
requirements. F3 observer fallback, F5 own-detail enlargement and F6 feed cursor grammar
can remain separately recorded debt. Two material product choices remain: whether already-
voted Public items remain in Home with a marker, and whether the recovered state identifies
the account's own selected photo. The grooming recommends keeping normal chronology with
`Voted` and showing only the account's own recorded choice. No proposal is accepted yet.

RF-14 -> RF-16 -> RF-18 remains the agreed order. RF-18 will consume aggregate-ready vote
rows; RF-19/RF-20 later transform valid votes into minimum outcomes under the shared terminal
lock; RF-21, RF-26 and RF-37 retain history, recipient-entry and photo-deletion boundaries.
No RF-16 implementation plan has been created. Owner answers and a subsequent explicit plan-
finalization approval are required; harness launch requires a later independent request.
Only RF-16 grooming and project state changed. Existing work is preserved; no tests, visual
inspection, commit, push, deployment, service operation or Trello mutation was performed.

## RF-14 closed by product-owner decision - 2026-10-15

The product owner explicitly clarified `que des por cerrada RF-14 y ya` after accepting the
displayed UI. RF-14 is therefore closed as `Completed and validated` by product-owner decision,
with the seven independent-review finding groups retained as known technical debt rather than
represented as fixed. This closure accepts the current increment as it stands; it does not erase,
contradict or convert the failed review probes into passing evidence. Votes, results and all other
future-ticket boundaries remain unimplemented.

Codex initially misinterpreted `cierrala, voy con RF-16` as authorization to run the documented
corrections. The new OpenCode correction process was interrupted immediately after the owner
clarified the request and exited with code 1. Hash comparison against the pre-run snapshot found
no implementation, test or documentation changes from that process; only this coordinator-owned
project-state update changed. The preserved snapshot is at
`C:/Users/anton/AppData/Local/Temp/nextpost-rf14-corrections-20261015-193700`.
No commit, push, deployment or Trello mutation occurred. RF-16 is the next proposed grooming ticket,
but this clarification authorizes only closing RF-14 and does not start RF-16 grooming.

## RF-14 owner UI feedback - 2026-10-15

After entering the isolated RF-14 UI review environment, the owner reported
`Se ve del carajo. Que va siguiente ?`. Record this as positive owner acceptance of
the displayed presentation. No particular viewport, zoom, safe-area, keyboard or real
device measurement is inferred. This does not resolve the independent technical findings.
RF-14 remains Implementation review; next is correction of the documented findings and
independent validation before closing the approved increment. No correction harness
launch is authorized by the question about next steps. After RF-14 closure, the proposed
next grooming ticket is RF-16 (independent voting), followed by RF-18 (author results).

## RF-14 UI review environment reopened - 2026-10-15

At the owner's request to enter and validate the UI, Codex rebuilt/started the isolated
nextpost-rf14-review-20261015 Compose project with rf14-compose.override.yaml.
Frontend: http://localhost:14174; API: http://localhost:18001. Health/frontend HTTP
checks pass. No browser visual inspection was performed. This environment is left running.

Created local demo accounts UIReview (ui-rf14@example.com) and OtherReview
(other-rf14@example.com), plus real persisted demo consultations through existing APIs.
UIReview's Home has three Public/open cards (one own, two from OtherReview); its own
Private consultation is available in My consultations and excluded from Home.
Photos are synthetic red/blue fixtures for navigation/UI inspection. No vote/result
or terminal operation was introduced. Ordinary user data and RF-12 environment are untouched.
RF-14 remains Implementation review with required technical corrections in the review report;
the reopened environment is for owner UI feedback, not technical acceptance or deployment.

## RF-14 independent review - 2026-10-15

The explicitly requested harness (66045) exited with code 0. RF-14 is now
`Implementation review`, with technical corrections required before acceptance.
`harness/grooming/RF-14-implementation-review.md` records seven finding groups and
an audit against all 14 approved acceptance criteria. No correction run has been launched.

Codex independently reran the baseline suites: 384 frontend tests pass; 353 backend tests
pass and 13 PostgreSQL tests are skipped without TEST_DATABASE_URL. Six additional
frontend review probes all fail: late preview 401 after unmount, old photo overwriting
a newer scope, missing observer fallback, Refresh reloading all previous pages, hidden
Load-more response during detail, and modal keyboard focus escaping. Direct backend
probes also show invalid cursor alphabet/noncanonical UUID accepted and no required
privacy headers on anonymous feed 401. Own Home detail lacks enlargement/loading Back;
Back anchor/focus/cursor progression and other documented error paths remain incomplete.

The harness's live PostgreSQL/built HTTP evidence below is retained as observed evidence,
not repeated as independently verified full scope. Nonvisual built-client interaction and
Alembic-backed query validation need strengthening. Owner visual acceptance (DEC-034),
real iPhone and future consumer/exposure gates remain separate. The full implementation
is not technically accepted or Completed and validated.

SHA-256 comparison found no missing prelaunch file and no unrelated baseline changes.
The six probe sources are preserved at harness/validation/rf14_review_reproductions.tsx
outside the ordinary suite; no coordinator production fix was made. No visual inspection,
commit, push, deployment or Trello mutation occurred.

## RF-14 harness completion report - 2026-10-15

The external harness reported implementation of `harness/features/RF-14-Implementation-plan.md`
(Discover open Public consultations) against the preserved prelaunch snapshot. The independent
review above supersedes full-scope/cleanup/accessibility claims below. RF-14 remains in
`Implementation review`, not `Completed and validated`. No commit, push, deployment or Trello
mutation was performed. Existing tracked/untracked work was preserved.

Added backend discovery: an authenticated `GET /api/consultations/feed` (registered before the
UUID detail route) with SQL-scoped `audience=public AND state=open` projection including the
current owner, `published_at DESC, id DESC` bounded keyset pagination using a versioned
`feed-v1` cursor, server-derived `is_owner`, set-based nickname and lowest-ordinal first-photo
metadata with a safe retryable 503 on corrupt/missing metadata, a 160-code-point context excerpt,
and private `no-store`/`nosniff`/`no-referrer` headers. General detail now carries the same
private headers. Affected files: `backend/app/consultation_service.py`,
`backend/app/api/consultations.py`, `backend/app/schemas.py`, `backend/app/main.py`.

Added frontend discovery: `fetchFeed` with strict runtime validation and a tightened general
detail guard (UUIDs, canonical audience, exact open state, exact keys, unique photo IDs, positive
dimensions, requested-ID match); `HomeFeed`, `FeedCard`, `useHomeFeed`, `useFeedPreviews`
(IntersectionObserver visible-card previews with a four-request bound and full object-URL
cleanup), `ReaderConsultationDetail`, `useReaderConsultationDetail` (all-or-error ordered photo
comparison), `PhotoEnlargement` (accessible dialog), and a `home` variant on
`OwnerConsultationDetail` with neutral wording and `Back to Home`. Home remains the default
destination and preserves composer dirty/pending navigation guards.

Validation evidence (this environment):

- Backend: 366 passed, 0 skipped, including the new `test_feed.py` (23) and `test_feed_postgres.py`
  (5) suites, run against an isolated disposable PostgreSQL 18 with a live `TEST_DATABASE_URL`.
  Ruff check/format and strict mypy are clean.
- Frontend: 384 passed, including `HomeFeed.test.tsx`, `ReaderConsultationDetail.test.tsx` and
  `useFeedPreviews.test.ts` (visibility/concurrency/cleanup). Prettier, ESLint, strict typecheck
  and production build pass; `npm audit --audit-level=high` reports 0 vulnerabilities.
- Isolated PostgreSQL query ordering/tie/insertion/removal tests pass (10 postgres tests total).
- `docker compose config --quiet` passes and the backend/frontend images build.
- Isolated built two-account smoke (`harness/validation/rf14_built_smoke.py` +
  `rf14-compose.override.yaml`, disposable volumes removed afterwards) passes: Public-only
  newest-first discovery, correct own/other `is_owner` flags, first-photo preview matching detail
  photo 0, Private exclusion even for owners, protected detail/photo reads with private headers,
  seeded finalized removal and restart persistence.

Remaining gates (reported, not passed): product-owner visual validation (DEC-034), independent
review, and the real iPhone/TestFlight delivery gate. Votes (RF-16), author results (RF-18),
recipient routing (RF-26) and terminal operations/photo purge (RF-13/19/20/37) remain with their
owning tickets; seeded terminal fixtures prove read/access behavior only, never real finalization
or erasure. The full-card "voting" criteria remain out of scope for this discovery increment.

## RF-14 implementation launched - 2026-10-15

The owner explicitly approved launch (`Apruebo , lanzalo`). Codex verified the ready
RF-14 plan, Remaining questions None, matching active ticket, no existing implementation
run, authenticated OpenCode Go and active opencode-go/deepseek-v4-pro with high variant.
One new conversation titled `RF-14 Discover Open Public Consultations Implementation`
was launched using the approved plan, without continuation/session/fork/auto flags.
Retained execution handle: `66045`. RF-14 is `Implementation in progress`.

Prelaunch source files, SHA-256 manifest, dirty status and tracked patch (174 files)
are preserved at `C:/Users/anton/AppData/Local/Temp/nextpost-rf14-20261015-183337-rgwwgy2n`.
Existing tracked/untracked work must remain intact. The harness is instructed to implement
only RF-14, validate it and report evidence; Codex still independently reviews output.
Owner visual acceptance under DEC-034 and other tickets' gates remain separate.
No commit, push, deployment or Trello mutation is authorized.

## RF-14 plan finalized - 2026-10-15

After selecting Q1B/Q2B and receiving the settled scope with an explicit plan-finalization
approval question, the owner replied `lom apruebo - dale caña`. This approves scope and
finalization. `harness/features/RF-14-Implementation-plan.md` is the self-contained
English implementation contract, marked `Ready for implementation` with
`Remaining questions: None`. The next gate is a subsequent independent owner request
to launch the harness. No launch or implementation occurred during plan finalization.

Approved scope: chronological Home feed of open Public consultations including own
cards in normal order, real first-photo previews, protected reader detail and authorized
owner detail with Home return, pagination/refresh/Back recovery and explicit media/session/
denial failures. Registered audiences, Private exclusion, immutability, no expiry and
owner visual validation remain binding. Votes/results/terminal operations/recipient
routing and existing independent review/device/exposure safeguards remain with their
owning tickets. Only RF-14 plan/grooming/project-state documentation changed; existing
work is preserved. No tests, visual inspection, commit, push, deployment or Trello mutation.

## RF-14 material choices confirmed - 2026-10-15

The owner answered `Yo elegiria 1B y 2B`. Q1B includes own open Public consultations
in normal Home chronology, marked Your consultation, opening real owner detail with
Back to Home. Q2B shows the first immutable published photo on each card, identified as
Photo 1 and loaded through the protected media API. Private remains excluded for every
viewer, including its owner. DEC-037 records the accepted cross-feature choices.

RF-14 is now `Grooming - awaiting product-owner confirmation`. No material question
remains identified. The settled discovery/feed/detail scope, exclusions, per-card image
failure/cleanup and validation direction are recorded in RF-14-grooming.md and presented
for confirmation and explicit English implementation-plan finalization approval.
No plan is created yet. The choice response does not authorize plan finalization or
the harness; launch still requires a subsequent independent request. Existing work is
preserved; this follow-up changes only grooming, accepted decisions and project state.
No implementation, tests, visual inspection, Trello mutation, commit, push or deployment.

## RF-14 grooming started - 2026-10-15

The product owner explicitly selected RF-14. The current card was consumed read-only
from the configured APP - NextPost board:
https://trello.com/c/WVW0cmEp/5-rf-14-descubrir-consultas-que-necesitan-votos.
It remains open and incomplete in `Próximo · completar el MVP`, with no labels,
members, dates, checklists, comments, attachments or custom field values. Its full
description, acceptance criteria and relevant metadata are captured in
`harness/grooming/RF-14-grooming.md`. RF-14 is `Grooming - questions open`.

Repository-first inspection confirms RF-12's approved increment is completed and
validated with owner acceptance below; persisted publication, My consultations,
returning owner detail and Private-link management are present. Home is still a welcome
card. The general protected API already permits another registered account to read an
open Public consultation and its photos, but there is no feed or reader UI. Votes,
results and real finalization/deletion/removal operations do not exist.

The recommended, unaccepted RF-14 increment is a chronological Home feed plus local
read-only detail with full text and authorized ordered photos. A single material batch
asks whether own Public items appear (recommend other authors only) and whether cards
show a photo (recommend text cards, photos in detail). Routine pagination, navigation,
error/session/resource/privacy and validation directions are recorded in grooming.
Private stays outside the feed; immutable publication, registered audiences, no expiry,
generic terminal denial and owner visual validation (DEC-034) remain binding.

RF-14 -> RF-16 -> RF-18 remains the proposed discovery/vote/author-results order,
verified against the product reorganization and current cards. RF-26 retains external
recipient/authentication return; RF-37 and restricted removal retain real-user-exposure
safeguards. Other tickets' independent review/device gates stay unchanged.
No RF-14 plan has been created or finalized. Owner answers and subsequent explicit plan
finalization approval are required; harness launch requires a later independent request.
Only RF-14 grooming and project state changed; existing tracked/untracked work is
preserved. No implementation, test run, visual inspection, service operation, commit,
push, deployment or Trello mutation was performed.

## RF-12 approved increment accepted - 2026-10-15

After testing the isolated built app with the supplied account, the product owner
confirmed `Ok funciona todo`. Together with the independent technical evidence below,
this accepts the approved author-recovery increment as `Completed and validated`.
Owner acceptance is recorded as supplied; no specific viewport, zoom, safe-area or
device measurements are inferred from that statement. No real iPhone/TestFlight
evidence was supplied, and that delivery gate remains external.

The accepted increment covers My consultations, owner-only Open/Finalized lists,
returning open detail with persisted photos, existing Private-link management and the
minimum finalized projection. The broad source card still has future vote/result,
sharing-entry, finalization/deletion and published-photo-cleanup consumers. No such
capability or full MVP completion is claimed. Trello remains unchanged.

## RF-12 technical acceptance verified - 2026-10-15

RF-12 is in `Implementation review`, awaiting product-owner visual acceptance (DEC-034).
The owner opened Docker and explicitly requested continuation. The correction harness
had already exited; Codex independently completed the review, corrected the remaining
partial-photo/unmount, item-switch, Back/list, duplicate-page and strict-response cases,
and verified all seven original finding groups. No new harness conversation was launched.
This entry supersedes the older in-progress status and environment blockers for RF-12.

- Full backend suite: 338 passed, none skipped, against an isolated PostgreSQL 18.6
  test database upgraded through the existing Alembic head. All eight previously
  skipped live tests ran. The strengthened 25-row/20-row-page UUID-tie pagination
  test and all four RF-12 PostgreSQL tests passed afterward.
- Full frontend suite: 347 passed, plus a subsequent duplicate-page regression
  (affected suite: 19 passed; 348 total tests now). Format/lint/types/build pass;
  affected-suite/types/lint rechecked after the final test-only addition.
- Backend Ruff/format/mypy pass; npm audit zero vulnerabilities after only the
  authorized source-map-js 1.2.1 -> 1.2.2 transitive lockfile patch.
- Isolated built-stack two-account HTTP smoke passes: real ordered photos, ownership
  and headers, Private disable/create/replace and old-link denial, disabled owner
  recovery, sign-out/in, service/database restart, persistent current link and temporary
  cleanup preserving promoted images. Seeded terminal fixtures prove privacy/access only.
- Latest built Chrome client passes nonvisual DOM/HTTP smoke: real composer publication
  for both audiences, explicit success-to-owner handoff, neutral detail/photos, Back,
  list recovery/reload/sign-in/Home default and empty Finalized tab. No screenshots or
  visual/zoom/device assertions were made.

Evidence, acceptance matrix, reproduction commands and remaining gates are recorded in
`harness/grooming/RF-12-implementation-review.md`. Validation helpers and a disposable
Compose override are under `harness/validation`; ordinary development data is untouched.
The isolated app remains available at http://localhost:14173 for owner visual review.
No commit, push, deployment or Trello mutation occurred; prior unrelated work is preserved.

Next: product owner validates 320px/desktop, zoom, safe areas/navigation clearance,
long text and keyboard/focus. RF-12 is not `Completed and validated` yet. Actual iPhone/
TestFlight remains an external delivery gate. The broad card still depends on votes,
results, recipient sharing, terminal operations and published-photo cleanup; this
technical acceptance covers only the approved author-recovery increment. Independent
RF-03/RF-06/RF-07/RF-09/RF-11 gates are not automatically closed by this evidence.

## RF-12 corrections launched - 2026-10-12

After reviewing the concrete closure steps, the owner replied `venga, vamos`, explicitly
authorizing RF-12 corrections and validation. Codex launched one new OpenCode Go
`opencode-go/deepseek-v4-pro` / `high` conversation titled
`RF-12 Review Corrections and Validation` against the approved plan and independent
review report. Execution handle: `81082`. RF-12 is `Implementation in progress`.
The previous RF-12 run had exited; no concurrent implementation was started.

The owner-authorized closure work includes the smallest compatible transitive patch/
lockfile remediation of the reported source-map-js advisory, preserving direct
dependency versions and adding no package or broader upgrade. Feature scope is unchanged.
Pre-correction dirty files are preserved at
`C:/Users/anton/AppData/Local/Temp/nextpost-rf12-corrections-20261012-232843`.
Docker Desktop startup was requested without resetting data or repairing installation;
availability and live integration evidence remain to be verified. Owner visual/device
gates, unrelated ticket state, and no-commit/push/deploy/Trello boundaries remain.

## RF-12 independent review - 2026-10-12

The explicitly requested OpenCode run exited with code 0. Codex independently reran the
local suites: 329 backend tests passed and 8 were skipped; 314 frontend tests passed;
backend/frontend format, lint, strict types and frontend production build pass.
Comparison with the prelaunch dirty-file snapshot found no missing baseline files and
no changes to unrelated baseline files. No commit, push, deploy or Trello mutation.

RF-12 remains `Implementation review`, not completed. The acceptance audit in
`harness/grooming/RF-12-implementation-review.md` records required corrections: pending
publication navigation/discard, late list responses after navigation/account change,
partial-photo URL cleanup on 401, immediate content clearing on denied reconciliation,
list refresh/load-more races, strict owner response guards/minimal terminal DB reads,
open-detail Refresh and tab keyboard semantics. Passing local tests do not cover all
these paths. Harness claims of full URL cleanup and complete approved scope below are
superseded by this independent review.

The dependency audit has one high source-map-js advisory with no package/lock changes;
it is not green. Live PostgreSQL and isolated built-stack two-account verification
remain unverified because Docker is unavailable. Owner visual and real-iPhone gates
remain separate. No further harness conversation or code correction was launched as
part of this launch-and-review record.

## RF-12 implementation launched - 2026-10-12

The owner explicitly requested launch (`lanzalo`). Codex completed the runbook preflight,
verified authenticated OpenCode Go and active `opencode-go/deepseek-v4-pro` with the
`high` variant, recorded the dirty worktree and preserved a prelaunch file snapshot at
`C:/Users/anton/AppData/Local/Temp/nextpost-rf12-20261012-222558`.
One new OpenCode conversation titled `RF-12 Manage My Consultations Implementation`
was launched against the approved plan, without continuation/session/fork/auto flags.
Its execution handle was `76345`; it has now exited with code 0. At launch RF-12 was
`Implementation in progress`; the independent review entry above gives the current state.
Existing RF-11 and other review/device gates remain unchanged. No commit, push,
deployment or Trello mutation is authorized.

## RF-12 harness completion report - 2026-10-12

The harness reported implementation of the owner-recovery increment against
`harness/features/RF-12-Implementation-plan.md`. All pre-existing tracked/untracked work was
preserved; no commit, push, deployment or Trello mutation was performed.

Added:

- Backend `GET /api/my-consultations` and `GET /api/my-consultations/{id}` with strict allowlisted
  discriminated schemas, bounded keyset pagination (version-validated cursor over
  `published_at`/`id`), SQL-scoped ownership, private `no-store`/`nosniff`/`no-referrer` headers,
  and a finalized projection that selects only the necessary columns and performs no storage,
  protected-detail or link work (`backend/app/consultation_service.py`,
  `backend/app/api/consultations.py`, `backend/app/schemas.py`).
- Frontend fourth primary destination, `MyConsultations` list/tabs/pagination/empty/error/refresh,
  a shared `useOwnerConsultationDetail` controller with full object-URL cleanup, denied-read
  reconciliation to the minimum finalized summary, and generation-aware Private-link handling;
  `OwnerConsultationDetail` is reused by `PublishedSuccess` (now with "View in My consultations")
  and the returning detail. Composer cap copy offers a real list destination without a nonexistent
  close action.

Automated validation evidence (this environment):

- Backend: 329 tests pass; 8 PostgreSQL tests are skipped because `TEST_DATABASE_URL` is not
  configured (no local PostgreSQL; Docker daemon not running). Ruff check/format and strict mypy
  are clean.
- Frontend: 314 tests pass; Prettier, ESLint, strict typecheck and production build pass.
- `docker compose config --quiet` passes. `npm audit --audit-level=high` reports one pre-existing
  high advisory in the transitive `source-map-js` dependency (not introduced here; left unfixed to
  avoid an out-of-scope dependency change).

Unverified gates (reported, not passed): the isolated PostgreSQL list/order tests, the isolated
built two-account author-recovery smoke, the product owner's visual validation (DEC-034) and the
real web/iPhone/TestFlight delivery gates. Votes/results/finalization/deletion/public share remain
with their owning tickets and are not fabricated by this increment.

## RF-12 grooming started - 2026-10-12

RF-12 grooming is finalized. The owner selected Q1A (`a`) and subsequently replied
"Vamos al lio" to the explicit proposed-scope and plan-finalization approval question.
`harness/features/RF-12-Implementation-plan.md` is the self-contained English contract,
marked `Ready for implementation`, with `Remaining questions: None`. The next gate is
the owner's subsequent explicit request to launch the harness. No implementation or
harness launch occurred during plan finalization.

The product owner explicitly selected `RF-12 · Gestionar mis consultas`. Its current card
was consumed read-only from the configured board after a temporary Trello rate limit:
https://trello.com/c/L2mZ6OFf/14-rf-12-gestionar-mis-consultas.
It is open and incomplete in `Próximo · completar el MVP`, with no labels, members,
dates, checklists, comments, attachments or custom field values. The complete current
description, criteria, metadata and intake checkpoint are preserved in
`harness/grooming/RF-12-grooming.md`.

At plan finalization RF-12 was `Ready for implementation`; the launch entry above
now advances the active ticket to `Implementation in progress`. Inspection of
current code and approved RF-03/RF-06/RF-07/RF-08/RF-09/RF-10/RF-11 contracts confirms
persisted publication, protected open detail/media and real owner Private-link controls,
but no own-consultation list, votes/results, terminal mutations or published-photo
terminal purge. The recommended increment is an owner-only list, returning open detail,
existing Private-link management and a separate minimum non-image finalized projection.
It omits unavailable vote/result/finalize/delete controls and counters; the full card's
consumer gates remain explicit. The owner answered `a` to the consolidated navigation
question on 2026-10-12: My consultations is a fourth primary destination, with Home
remaining default and the future community entry (DEC-036). No material question remains
identified. The proposed scope and explicit final plan approval are confirmed by the
subsequent response recorded above. The approved plan has been created; the harness has
not been launched. Readiness is not an implementation or full-card completion claim.

RF-11 remains independently in `Implementation review` awaiting owner visual validation;
RF-06/RF-03/RF-07/RF-09 keep their recorded review/integration/device gates. Existing
tracked and untracked changes were preserved. This grooming changed documentation only:
no implementation, test run, browser visual review, Docker repair, commit, push,
deployment or Trello mutation. Earlier evidence and blockers remain dated records.

## Backlog reconciliation - 2026-10-12

The owner requested inspection and reorganization of the existing Trello board against the
repository and their new product interview. DEC-035 records the clarified direction: a recurring
community for purpose-based photographic choices, with voting as the sufficient initial
contribution. Comments and a reputation incentive remain future ideas requiring grooming.

`harness/grooming/PRODUCT-2026-10-12-reorganization.md` records the interview, actual code
inspection, per-card placement and proposed continuation. The complete original 40-card Trello
snapshot is `harness/grooming/TRELLO-2026-10-12-before-reorganization.json`.
The board reorganization is applied and verified: 42 cards in seven ordered columns (4 validated
increments, 5 review items, 10 remaining-MVP items, 3 beta items, 8 later-community items,
9 account/administration items and 3 initial-MVP exclusions). All 40 original cards and completion
flags are preserved; the original descriptions remain below dated notes. RF-03 is now titled
`RF-03 · Consultar mi perfil`, preserving its card identity/short link and approved read-only scope.
The application record in that grooming document and the complete
`harness/grooming/TRELLO-2026-10-12-after-reorganization.json` snapshot provide verification.

RF-03/RF-07/RF-09 are marked complete in Trello but retain pending review/integration/device gates
in the repository. Those historical flags are preserved and explained on their cards; this
reorganization does not turn them into validated implementations or alter their lifecycle values.
RF-01/RF-02/RF-08/RF-10 have recorded completion evidence for their approved increments.

The proposed next grooming ticket is RF-12 (find/manage own consultations), followed by community
discovery, voting and author results. RF-37 must define published-photo cleanup before terminal
mutations; RF-19/RF-20 remain one observable declaration/finalization operation. RF-41 captures
optional explanations as a later idea; RF-42 makes web/iOS delivery and integrated invited testing
visible. Neither has an approved plan. At that reconciliation checkpoint RF-12 had not been
selected/consumed; the RF-12 grooming entry above supersedes that intake status. RF-11 retains
its independent review status and owner's visual gate below.

No implementation, harness launch, new test run, browser visual review, Docker repair, deployment,
commit or push was performed. Previously recorded validation and environmental blockers remain
dated evidence; the Docker startup issue has not been rechecked in this backlog task.

## Current phase

RF-14 is closed as `Completed and validated` by explicit product-owner decision, with known
technical debt preserved in RF-14-implementation-review.md. Q1B/Q2B are accepted:
own Public/open cards and first-photo previews (DEC-037). The owner subsequently
approved the settled scope and English plan finalization on 2026-10-15, then
independently requested launch. `harness/features/RF-14-Implementation-plan.md` is
the self-contained contract. Handle 66045 exited. Independent review found seven groups
of corrections; the owner later accepted the displayed UI and explicitly chose closure
without that correction round. Those findings remain recorded and unresolved. The mistakenly
started correction process was stopped before changing implementation files. RF-12 completion
and other-ticket gates remain.

RF-12's approved author-recovery increment is `Completed and validated`, following
technical verification and product-owner acceptance on 2026-10-15. Its approved contract is
`harness/features/RF-12-Implementation-plan.md`; its intake, analysis and resolved choices
are in `harness/grooming/RF-12-grooming.md`. Navigation Q1A is accepted (DEC-036) and
the owner explicitly approved scope/plan finalization and then requested harness launch.
The original findings have been corrected and independently checked, including live
PostgreSQL, built two-account HTTP verification and actual built-client browser recovery.
The current evidence and separate future consumer/device gates are recorded in
RF-12-implementation-review.md. Audit/integration technical gates pass; owner acceptance
is recorded above without inventing viewport/device measurements.

RF-11 remains in `Implementation review`. It was explicitly selected and consumed
read-only from the configured Trello board on 2026-09-29. The product owner rejected new lifecycle
dates, accepted the reusable-foundation boundary and terminal concurrency/retry rule, and explicitly
requested the detailed final plan. `harness/features/RF-11-Implementation-plan.md` is the approved
self-contained contract. It adds no migration or terminal operation. The product owner explicitly
launched the external OpenCode harness on 2026-10-02 with `opencode-go/deepseek-v4-pro` at the
`high` variant. The implementation and independent technical review are complete: 302 backend tests
and 274 frontend tests pass, the four live-PostgreSQL concurrency tests pass, backend/frontend
formatting, linting, strict type checks, production build and dependency audit are green, and the
Docker Compose backend/frontend images build and start healthy. Product-owner visual validation is
the remaining RF-11 review gate under DEC-034.

RF-06 remains in `Implementation review`. On 2026-09-29 Codex independently reran the complete local
automated suites: 265 backend tests passed with four live-PostgreSQL tests skipped in the ordinary
environment, 263 frontend tests passed, and backend/frontend formatting, linting, strict type checks,
production build and dependency audit were green. The isolated built-stack two-account smoke could
not be rerun because Docker Desktop 4.86 crashes during startup while initializing its
`dockerInference` runtime socket. A reversible rename attempt was denied by Windows and made no
filesystem change. RF-06 is not marked completed without that smoke evidence; its real
iPhone/TestFlight gate also remains external.

RF-10's approved increment is `Completed and validated`. The product owner explicitly launched the
OpenCode `opencode-go/deepseek-v4-pro` harness on 2026-09-28; Codex then independently reviewed the
implementation, corrected three contract gaps and validated the complete approved scope with unit,
PostgreSQL, migration and isolated built-stack evidence. The later RF-06/RF-26/RF-12/RF-18 consumer
and physical-device gates remain assigned to those tickets.

RF-09's reusable audience/link/access increment is implemented and independently reviewed with
green automated, container and visual evidence; RF-10 now supplies its integrated publication and
protected-read contracts, while RF-06/RF-26 retain the share journey and device gates. RF-08 is completed and validated for its reusable
text increment. RF-03 implementation is in progress; RF-07 is in implementation review and unblocks
RF-06's real-photo path.

## Current status

- `RF-11 · Estados de una consulta` was explicitly selected and consumed read-only from the
  configured board on 2026-09-29:
  https://trello.com/c/5bQ0jXnq/13-rf-11-estados-de-una-consulta. The card remains open and incomplete
  in `Fase 2`, with no labels, members, dates, checklists or comments. Its current criteria define
  temporary preparation, open, author-finalized and deletion/administrator-removal unavailability;
  finalization must stop new votes and photo access, while automatic expiry/duration remains
  deferred. `harness/grooming/RF-11-grooming.md` records the exact snapshot, current implementation
  findings, dependency boundaries and resolved decision batch. The owner rejected lifecycle dates,
  accepted first-terminal-commit-wins with exact-retry proof and approved RF-11 as a reusable
  foundation. DEC-033 records the cross-ticket rule. The approved implementation contract is
  `harness/features/RF-11-Implementation-plan.md`, marked `Ready for implementation`. No Trello
  mutation was performed. The external OpenCode harness was explicitly launched on 2026-10-02 and
  Codex independently reviewed its output. The review expanded terminal coverage across every
  published photo, all three owner Private-link mutations and every frontend terminal/unknown
  response value. All local, PostgreSQL and built-container technical checks are green. The ticket
  remains in `Implementation review` pending the product owner's visual validation.

- `RF-10 · Publicar una consulta` was explicitly selected and consumed from the configured board
  on 2026-09-28: https://trello.com/c/gMQwBaFB/4-rf-10-publicar-una-consulta.
  `harness/grooming/RF-10-grooming.md` preserves its full title/description/criteria and metadata,
  current code findings, links to RF-07/RF-08/RF-09 approved contracts and their recorded validation,
  and read-only RF-12/RF-13/RF-18/RF-26/RF-37 dependency checks. Inspection confirms there is still
  no persisted Consultation or publication endpoint. The candidate design covers one atomic
  database publication, in-place promotion of private processed bytes, one publication per upload
  session, normalized-payload reconciliation, serialized open-cap enforcement, automatic Private
  link creation, current detail/media authorization and owner link mutations. It identifies the
  existing discard-on-unmount, session/image-delete, orphan-sweep and cascade paths that must be
  adapted together, plus migrations, CSRF/origin handling and meaningful PostgreSQL race tests.
  One consolidated Q1–Q5 batch asks about final confirmation,
  an uncertain publication result, when to block preparation at the open cap, published-photo
  durability/loss handling, and increment versus full-card completion with later consumer and
  withdrawal/deletion gates. The owner accepted Q1A (single preview confirmation) and Q3A (early
  open-cap guidance), recorded in DEC-031. Q2 was considered excessive for the POC; the revised
  recommendation uses ordinary pending feedback and manual retry with server deduplication, without
  a separate recovery flow. Q4 was subsequently closed: ordinary published consultation/photo
  persistence across app closure/restart, with no added photo backups or special disaster recovery
  for the POC (DEC-032). Temporary unpublished preparation remains non-recoverable. Q5 still needs
  clarification of the existing ticket split. The subsequent owner follow-up rejects double-submit
  recovery complexity: Q2 is closed with ordinary pending/error/manual-retry UX and minimal server
  deduplication, without a separate recovery/status flow. Acceptance of Q5 is not inferred.
  At the subsequent readiness check, no material product question remains: Q5 is an unnecessary
  reconfirmation of the already accepted ticket split, which is retained without scope expansion.
  Grooming was settled, and the owner subsequently explicitly requested plan finalisation.
  `harness/features/RF-10-Implementation-plan.md` is the approved English contract, marked
  `Ready for implementation`. It requires atomic persistence, one-publication-per-session Retry,
  transactional cap enforcement, cleanup-safe photo promotion, real protected detail/media and
  persisted owner link transitions while excluding backup/recovery and later product screens.
  This does not launch the harness or mark the full card completed. Grooming did not rerun
  implementation tests or change
  application code, Trello, running services or storage. Existing worktree changes are preserved.

- RF-10 was implemented by the explicitly launched OpenCode `opencode-go/deepseek-v4-pro` harness on
  2026-09-28 against the approved plan. The increment added `Consultation` and `ConsultationPhoto`
  models plus Alembic revision `20260928_0004` (adds `consultations`, `consultation_photos`, the
  terminal `consumed` upload-session state and audience/link/state/ordinal constraints);
  `backend/app/consultation_service.py` (atomic publication with per-author cap locking,
  one-publication-per-session idempotency via a versioned fingerprint, cleanup-safe in-place
  promotion, protected detail/media reads through `can_access`, and persisted owner link
  read/disable/replace/create transitions); and `backend/app/api/consultations.py` with trusted-origin
  protection on state-changing routes. `photo_service.remove_image` now rejects consumed sessions so
  a delayed temporary DELETE cannot revoke a promoted photo. The frontend gained `consultationApi.ts`,
  `usePublishConsultation.ts`, `PublishSummary.tsx`, and uploader `sessionId`/`relinquish`/`freeze`
  handoff support. No backup, worker, recovery screen, complete composer, feed, vote, results,
  finalization/deletion or native-link work was introduced. Automated evidence is green: 265 backend
  tests passed (4 PostgreSQL concurrency tests skipped without a live test database; all 4 passed
  against an isolated disposable PostgreSQL, including the new two-session last-slot cap race),
  Ruff check/format and strict mypy clean; 241 frontend tests, Prettier, ESLint, strict typecheck and
  production build pass; `npm audit` reports 0 vulnerabilities; `docker compose config` is valid.
  Alembic fresh upgrade, downgrade/upgrade round trip and a populated RF-07 -> RF-10 upgrade were
  verified on a disposable PostgreSQL, including preserved existing sessions/images, the accepted
  `consumed` state and enforcement of the public/active-link constraint. Independent review found
  and corrected three gaps: publication now normalizes and validates text/audience inside the
  transactional service rather than trusting the HTTP schema; the retry fingerprint uses canonical
  JSON so field boundaries cannot collide; and the migration uses `RESTRICT` for published-owner
  references and refuses downgrade while consultations or consumed sessions exist. Focused tests
  cover normalization, invalid direct-service input and fingerprint boundaries. An independent
  disposable PostgreSQL run passed all four concurrency suites, empty downgrade/upgrade, owner-delete
  restriction and populated-downgrade refusal. An isolated built Compose stack then verified real
  image upload, atomic private publication from three images with one leftover revoked, idempotent
  Retry, protected detail/media, link disable/create, cleanup and persistence of consultation,
  selected media and current link across a backend restart. The disposable containers and volumes
  were removed. Final independent checks pass: 265 backend tests with 4 live-PostgreSQL tests skipped
  in the ordinary local suite and separately passed live, Ruff check/format, strict mypy, 241 frontend
  tests, Prettier, ESLint, strict typecheck, production build and Compose configuration. No commit,
  push, deployment or Trello mutation was made. RF-10's approved increment is completed and
  validated; later consumer and physical-device gates remain with RF-06/RF-26/RF-12/RF-18.

- `RF-09 · Elegir audiencia y controlar el enlace` was explicitly selected and consumed read-only
  from the configured board on 2026-09-28. `harness/grooming/RF-09-grooming.md` preserves the full
  current card, metadata, repository findings and RF-10/RF-12/RF-26/RF-37 dependency checks.
  The owner requested all questions together. One six-question batch covers first link issuance,
  revocation consequences, already-open screens, unavailable-link disclosure, iPhone external-link
  behavior and the RF-09/RF-10 implementation boundary. After clarification, the owner confirmed
  automatic link creation; current database authorization on entry/actual requests without polling,
  allowing already-loaded photos to remain on an open screen (DEC-029); generic unavailable copy
  (DEC-028); ordinary platform link opening without custom native work (DEC-030); and the existing
  RF-09 -> RF-10 -> RF-06 order. The owner explicitly requested plan drafting on 2026-09-28.
  `harness/features/RF-09-Implementation-plan.md` is the approved self-contained contract, marked
  `Ready for implementation`. It defines the reusable audience/link/access increment plus exact
  RF-10/RF-06/RF-26 integration gates. No published consultation behavior is claimed complete.
  On 2026-09-28 the owner explicitly requested the
  harness launch. Codex started a new OpenCode conversation with the approved
  `opencode-go/deepseek-v4-pro` model and `high` variant. The owner asked Codex not to monitor it
  continuously and will request the completion review later. The harness implemented the reusable
  increment: canonical `public`/`private` audience validation (`backend/app/audience.py` +
  `frontend/src/audience.ts`), the pure account/owner/audience/link/lifecycle access policy
  (`backend/app/consultation_access.py`), the versioned HMAC-SHA-256 private-link capability with
  disable/replace/create-new transitions (`backend/app/private_link.py`), a startup-validated
  server-only `PRIVATE_LINK_SECRET` wired through `.env.example`/Compose (forwarded empty when
  unset) without exposure through `/api/application-config`, and controlled frontend
  `AudienceSelector`, `PrivateLinkControls`, `ConsultationUnavailable` and `consultationLink`
  URL/token/header helpers. No Consultation table, public route, migration or photo-path change was
  introduced. The independent review corrected strict trusted-origin URL handling, authoritative
  snapshot-bound token verification, fail-closed operation/generation handling, inactive-state
  token derivation, the strict backend audience schema, credentialed protected-request options,
  link-control error reconciliation and confirmation focus, reusable selector IDs/radio groups,
  and a 320 px horizontal overflow. A temporary browser mount verified desktop and 320 px layouts,
  touch targets, confirmation focus, wrapping and retry/error presentation, then was removed.
  Final evidence is green: 227 backend tests passed and 3 unrelated PostgreSQL concurrency tests
  were skipped without a configured live test database; Ruff check/format and strict mypy pass;
  215 frontend tests, Prettier, ESLint, strict typecheck and production build pass; `npm audit`
  reports 0 vulnerabilities; Compose configuration, backend image build and production secret
  rejection/acceptance checks pass. Full RF-09 completion remains pending the RF-10/RF-06/RF-26
  integrated publication, share/auth-return and real-device gates.

- `RF-08 · Explicar el objetivo de la consulta` was consumed read-only from the configured board
  during 2026-09-22 research and recorded on 2026-09-23 in `harness/grooming/RF-08-grooming.md`.
  The snapshot, actual code findings, RF-07 handoff gaps for RF-06/RF-10, inherited decisions,
  candidate text/API/configuration contract and consolidated question batch are recorded there.
  On 2026-09-23 the owner answered `1A 2A`: a cleared question requires correction, and question/full
  optional context appear above photos in shared preview/voter detail (DEC-027). No material question
  remains. The owner explicitly approved finalisation on 2026-09-23; the English self-contained
  `harness/features/RF-08-Implementation-plan.md` is `Ready for implementation`. On 2026-09-23 the
  owner explicitly requested launch of the RF-08 implementation harness. The owner requests
  RF-08 -> RF-09 -> RF-10 -> finalise and implement RF-06. The RF-08 harness implemented the
  reusable text increment on 2026-09-23: startup-validated `CONSULTATION_QUESTION_MAX_LENGTH=120`
  and `CONSULTATION_CONTEXT_MAX_LENGTH=500` settings wired through `.env.example`/Compose and the
  additive authenticated `GET /api/application-config` response; a pure Python validator/value
  object (`backend/app/consultation_text.py`) with a reusable `ConsultationTextRequest` schema;
  matching TypeScript rules in `frontend/src/consultationText.ts`; a retryable
  `useConsultationConfig` boundary; controlled `ConsultationTextFields` and shared
  `ConsultationTextDisplay` components with scoped styles. Automated evidence is green: 136 backend
  tests passed in the harness run (3 PostgreSQL concurrency tests skipped, no live PostgreSQL daemon in this
  environment), Ruff check/format and strict mypy clean; 143 frontend tests passed, Prettier,
  ESLint, strict typecheck and production build clean; `npm audit` reports 0 vulnerabilities and
  `docker compose config` is valid. The built-stack Docker config smoke was unavailable at that
  checkpoint. RF-06 integration and the physical-iPhone/TestFlight gate remain deferred
  consuming-ticket checks. Independent review corrected server-field-error clearing, hid stale configuration limits
  during loading/failure, and made the missing-question schema error match the specified text.
  Six pre-existing RF-07 cleanup tests used a fixed session time with a real-time upload and
  became date-dependent; their uploads now use the same fixed test clock. Revalidation after these
  corrections: 137 backend tests passed, 3 PostgreSQL tests skipped, 144 frontend tests passed;
  Ruff, mypy, Prettier, ESLint, typecheck, production build, and `docker compose config --quiet`
  passed. Docker API/build smoke and physical/device layout checks were unavailable at that
  checkpoint because the Docker daemon and signed iOS environment were unavailable.
  On 2026-09-28 Docker became available. The built PostgreSQL/backend/frontend stack is running;
  authenticated and unauthenticated live configuration reads verified default 120/500 limits and
  401 protection. A separate ephemeral backend verified 60/200 environment overrides through the
  HTTP response, and its test account/container were removed. All three previously skipped
  PostgreSQL concurrency tests passed against an isolated temporary database that was removed.
  A temporary `rf08-preview.html` page served the real text components and API configuration
  alongside illustrative photo positions without uploading or publishing. The product owner reviewed
  it visually on 2026-09-28 and explicitly asked to close RF-08. The temporary page and its styles
  were removed; the final frontend passed 144 tests, Prettier, ESLint, typecheck and production build,
  then was rebuilt in Docker. RF-08's reusable increment is `Completed and validated`. Real
  photo/composer integration remains RF-06's gate; published access remains RF-09/RF-10's gate; and
  physical-iPhone/TestFlight checks remain external integrated-delivery gates. No claim is made that
  those later flows were validated by the isolated RF-08 review.
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
  2026-09-22 into `harness/grooming/RF-06-grooming.md`. The RF-06 boundary and dependency order are
  confirmed. On 2026-09-28 the owner reactivated grooming after RF-10 completed validation. Fresh
  inspection found the old RF-07/RF-08/RF-09/RF-10 blockers resolved: real temporary upload and
  cleanup, text/configuration, audience/access/link and atomic publication/detail contracts are now
  implemented and tested. RF-06 is a frontend integration increment with no expected migration.
  `App.tsx` and `Navigation.tsx` still expose only Home/Profile, and there is no composer, dirty-exit
  interception or post-publication destination. The owner resolved the single question batch on
  2026-09-28: third Create navigation item; a polished three-step Photos, Details, Review/publish
  wizard; fixed selection order; dirty-only discard warnings; and a narrow persisted success/detail
  view with current Private link controls. The available browser session reached Trello's sign-in wall during a
  recheck, so the preserved 2026-09-22 card snapshot remains the backlog input; Trello was not
  mutated. No material question remains. On 2026-09-28 the product owner explicitly approved
  `harness/features/RF-06-Implementation-plan.md`, now marked `Ready for implementation`. The product
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

RF-14: `Completed and validated` by explicit product-owner closure decision. The known
technical findings in RF-14-implementation-review.md remain unresolved and visible; closure
does not claim that their failing probes passed. No correction harness is running.

RF-12: the approved author-recovery increment is `Completed and validated` following
technical verification and the owner's `Ok funciona todo` on 2026-10-15. The broad
card's vote/result/sharing/terminal/photo-deletion consumer gates and actual iPhone
delivery evidence stay explicit. RF-14 is now separately selected for grooming; no
implementation or Trello mutation is implicitly authorized by this acceptance.

RF-11 implementation and independent technical review are complete. The next gate is the product
owner's visual validation under DEC-034; Codex must not repeat browser/viewport inspection unless
the owner explicitly requests a specific visual check. After owner approval, RF-11 can move to
`Completed and validated` without relaunching the implementation harness.

Separately, RF-06's local automated review is green. Its remaining closure evidence is the isolated
built-stack two-account smoke, currently blocked by the local Docker Desktop startup failure. RF-09's
reusable foundation has passed independent review; remaining share/authentication-return and
real-device evidence belongs to RF-26/RF-06. RF-12/RF-18 and the later
finalization/deletion/removal tickets retain their own consumer checks.

RF-08's reusable text/configuration increment is completed and validated, including built
configuration API, PostgreSQL checks and the owner's isolated visual review. RF-09's reusable
contract is approved and reviewed, and RF-10's publication contract is completed and validated.
RF-06 integration plus the physical-iPhone/TestFlight gate are the deferred consuming-ticket checks.

The RF-06 Trello description was rechecked on 2026-09-22 after its alignment with accepted phase-2
decisions. The grooming file preserves the original and current snapshots. The product owner has
confirmed the RF-06 composer boundary and the order of defining upload and cleanup contracts first.
The approved RF-06 implementation plan was handed to the harness on 2026-09-28 and its implementation
is present. The historical statement that it had not been handed off is superseded by the current
phase and validation record above.

RF-07's automatable implementation and independent review are complete. Keep its external
real-iPhone/TestFlight and RF-06 integrated-composer checks visible during phase-2 validation. Settle
RF-06 using the validated RF-08/RF-09/RF-10 integration contracts. The owner confirmed that the composer initially has no
audience selected and requires an explicit Public/Private choice (DEC-024). A concrete RF-06
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

## Most recently completed ticket

- Ticket: `RF-14 · Descubrir consultas que necesitan votos`
- Trello: https://trello.com/c/WVW0cmEp/5-rf-14-descubrir-consultas-que-necesitan-votos
- Lifecycle: `Completed and validated` by product-owner decision, with known technical debt
- Grooming notes: `harness/grooming/RF-14-grooming.md`
- Approved plan: `harness/features/RF-14-Implementation-plan.md`
- Review: `harness/grooming/RF-14-implementation-review.md`
- Closure: owner accepted the current UI and explicitly requested closure without the correction round.
- Next proposed ticket: RF-16; grooming has not started in this closure-only action.

## Related lifecycle ticket in implementation review

- Ticket: `RF-11 · Estados de una consulta`
- Trello: https://trello.com/c/5bQ0jXnq/13-rf-11-estados-de-una-consulta
- Lifecycle: `Implementation review`
- Grooming notes: `harness/grooming/RF-11-grooming.md`
- Approved plan: `harness/features/RF-11-Implementation-plan.md`

## Related composer ticket in implementation review

- Ticket: `RF-06 · Preparar una consulta`
- Trello: https://trello.com/c/kLphAXQ1/10-rf-06-preparar-una-consulta
- Lifecycle: `Implementation review`
- Grooming notes: `harness/grooming/RF-06-grooming.md`
- Approved plan: `harness/features/RF-06-Implementation-plan.md`

## Most recently completed ticket

- Ticket: `RF-12 · Gestionar mis consultas` (approved author-recovery increment)
- Trello: https://trello.com/c/L2mZ6OFf/14-rf-12-gestionar-mis-consultas
- Lifecycle: `Completed and validated`
- Grooming notes: `harness/grooming/RF-12-grooming.md`
- Approved plan: `harness/features/RF-12-Implementation-plan.md`
- Evidence: `harness/grooming/RF-12-implementation-review.md`; owner acceptance 2026-10-15.
- RF-10's approved publication increment remains completed and validated as recorded above.

## Related audience/link ticket in implementation review

- Ticket: `RF-09 · Elegir audiencia y controlar el enlace`
- Trello: https://trello.com/c/vt8seQzA/12-rf-09-elegir-audiencia-y-controlar-el-enlace
- Lifecycle: `Implementation review`
- Grooming notes: `harness/grooming/RF-09-grooming.md`
- Approved plan: `harness/features/RF-09-Implementation-plan.md`

## Previously completed ticket

- Ticket: `RF-08 · Explicar el objetivo de la consulta`
- Trello: https://trello.com/c/lcZAWVWd/11-rf-08-explicar-el-objetivo-de-la-consulta
- Lifecycle: `Completed and validated`
- Grooming notes: `harness/grooming/RF-08-grooming.md`
- Approved plan: `harness/features/RF-08-Implementation-plan.md`

## Related ticket in implementation review

- Ticket: `RF-07 · Subir y comparar varias fotografías`
- Trello: https://trello.com/c/x8VPrsF9/3-rf-07-subir-y-comparar-varias-fotograf%C3%ADas
- Lifecycle: `Implementation review`
- Grooming notes: `harness/grooming/RF-07-grooming.md`
- Approved plan: `harness/features/RF-07-Implementation-plan.md`

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
