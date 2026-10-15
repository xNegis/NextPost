# RF-12 - Independent implementation review

## Product-owner acceptance - 2026-10-15

The owner tested the isolated built app using the supplied account with two open
Public/Private consultations and confirmed `Ok funciona todo`. The approved
author-recovery increment is now `Completed and validated`; this supersedes the
pending-owner-acceptance status below. Record only that supplied acceptance: no
specific viewport/zoom/safe-area measurements or real-device checks were reported.
The external iPhone/TestFlight gate and broad-card future consumers remain unchanged.
No Trello mutation, commit, push or deployment accompanies this repository closure.

## Current outcome - 2026-10-15

`Implementation review` — technical acceptance of the approved author-recovery increment
is complete; product-owner visual acceptance is pending (DEC-034). This supersedes the
dated first-pass findings below. It does not close the broad Trello card or the MVP.

The second harness applied corrections to all seven finding groups and patched the
transitive source-map-js version from 1.2.1 to 1.2.2 (only three lockfile lines changed;
package.json/direct versions unchanged). That run exited while its own permission
controller rejected a Docker probe writing outside the repository. No user denial
occurred, and the coordinator completed independent validation after the owner opened
Docker and explicitly requested continuation on 2026-10-15.

Independent follow-up found and corrected remaining cases within the approved scope:
partial photo URLs now belong to cleanup immediately, including unmount before a later
photo resolves; superseded item reads cannot let an old Private-link effect cancel the
new detail; late clipboard results are ignored; Back recovers a list whose initial read
was invalidated by direct detail entry; duplicate IDs inside appended pages are removed.
Owner responses now require actual UTC calendar timestamps and exact UUID/photo metadata.
Regression tests prove these paths, including late 401/success after unmount.

### Final technical evidence

- Backend full suite: 338 tests passed with TEST_DATABASE_URL set to a dedicated
  rf12_tests database on isolated PostgreSQL 18.6, after Alembic upgrade to
  20260928_0004. None skipped. The eight formerly skipped integration tests ran.
  The owner pagination test was then strengthened to 25 tied rows across 20-row pages;
  all four RF-12 PostgreSQL tests passed again.
- Frontend full suite: 347 tests passed. One additional page-deduplication regression
  was subsequently added; the affected suite passed all 19 tests (348 total tests now).
- Backend Ruff check/format and strict mypy passed. Frontend Prettier, ESLint,
  TypeScript and production build passed; affected-suite/type/lint checks passed after
  the final test-only addition. npm audit reports zero vulnerabilities.
- Isolated Compose builds and healthy services succeeded on Docker Engine 29.7.2.
  Latest production frontend was rebuilt after coordinator corrections.
- Reusable nonvisual HTTP smoke in harness/validation/rf12_built_smoke.py passed:
  registered A/B plus anonymous client; real Public/Private publication and normalized
  photos in immutable order; exact owner headers; no cross-account management even
  with Public access/current Private token; disable/create/replace with old-token
  denial; disabled owner recovery and unchanged capacity; sign-out/sign-in recovery;
  database/backend/frontend restart and persistent current link; temporary cleanup
  preserves promoted bytes. Seeded terminal rows prove exact finalized projection and
  deleted/removed exclusion/protected-reader denial only, not real terminal operations
  or physical deletion.
- Headless Chrome DOM/HTTP smoke in harness/validation/rf12_browser_smoke.mjs passed
  against the latest built application: actual composer upload and publication for both
  audiences; Published -> View in My consultations -> neutral owner detail; two actual
  protected blob photos; Back/list recovery, page reload, Profile sign-out and sign-in,
  Home defaults and Finalized empty state. It took no screenshots and made no visual,
  zoom or device assertions.
- git diff --check passed. Existing unrelated tracked/untracked changes remain present.
  No commit, push, deployment, Trello change, Docker repair or production-data cleanup.

### Current acceptance audit

Criteria refer to the ordered acceptance list in the approved RF-12 plan.

| Criteria | Current evidence |
| --- | --- |
| 1–3: navigation, recovery, list/order/pagination | Component/API suites; live PostgreSQL including 25 tied rows; built Chrome publication/list/reload/login; isolated restart |
| 4–5: minimal finalized and neutral open/Back/Refresh | Exact server/client projection tests; minimal-column service; detail/component and actual built-client tests |
| 6–7: real Private controls and disabled-owner recovery | Real HTTP disable/create/replace, stale/conflict component regressions, honest recipient limitation |
| 8–12: failures, isolation, terminal boundary, resources, composer | Seven corrected review groups and additional late/partial/item/Back regressions; full suites and integrated smoke |
| 13–14: truthful capacity and bounded feature scope | Source review and cap tests; no fake results, terminal mutation, Public share journey, schema or infrastructure addition |
| 15: semantics/copy/layout | Automated technical coverage passes; product-owner visual acceptance pending |
| 16: checks/PostgreSQL/built evidence | Passed as recorded above; actual iPhone/TestFlight evidence remains an external delivery gate |
| 17: narrow claim and authority | Repository updated; broad card and future consumers remain open; no external mutation |

### Reproduction and next gate

From the repository root, using the installed Docker CLI (add its existing directory to
PATH if necessary), run:

```powershell
docker compose -p nextpost-rf12-review-20261015 -f docker-compose.yml -f harness/validation/rf12-compose.override.yaml up --build -d
.\.venv\Scripts\python harness/validation/rf12_built_smoke.py
node harness/validation/rf12_browser_smoke.mjs
```

The override uses only the named disposable project's volumes and loopback ports
15432/18000/14173, with explicitly disposable local credentials. The HTTP script seeds
terminal fixtures only in rf12_review; rf12_tests is a separate database created with
createdb -U rf12 rf12_tests in that project's db container. For live test reproduction,
set DATABASE_URL and TEST_DATABASE_URL to
postgresql+psycopg://rf12:rf12-disposable-local@127.0.0.1:15432/rf12_tests?connect_timeout=8,
upgrade using the existing backend/alembic.ini, then run backend/tests. Explicit IPv4
avoids the host's observed localhost connection stall.

The isolated app is available at http://localhost:14173 for owner validation. The owner
can register a disposable account and publish up to the configured three consultations.
Still awaiting: 320px/desktop, 200% zoom, safe-area/four-label navigation clearance,
long text, keyboard/focus and the owner's visual acceptance. Real iPhone/TestFlight
validation stays with the delivery gate; no native project/environment exists here.

Votes/results (RF-16/RF-18), recipient sharing (RF-26), published photo cleanup (RF-37),
deletion (RF-13), atomic finalization/choice (RF-19/RF-20), and restricted removal remain
future consumer contracts. Do not mark the increment Completed and validated until the
owner's acceptance; do not turn seeded rows into a claim that these features exist.

## Historical first pass - 2026-10-12

The following sections preserve the original findings and evidence. They describe the
first implementation only and are superseded by the dated current audit above.

## Outcome

`Implementation review` — acceptance is not complete.

The explicitly requested OpenCode Go / deepseek-v4-pro / high run finished with exit 0.
Codex independently inspected the resulting production code against the approved plan and
reran local checks. The useful owner-recovery implementation is present, but the findings
below prevent an unqualified completion claim. No second harness conversation was launched.

## Independent evidence

- Backend: 329 passed, 8 skipped; Ruff check/format and strict mypy pass.
- Frontend: 314 passed; Prettier, ESLint, strict TypeScript and production build pass.
- Harness evidence: Compose configuration valid; live Docker daemon unavailable.
  Isolated PostgreSQL and built two-account smoke remain unverified, not passed.
- Audit: npm audit reports one high source-map-js advisory,
  https://github.com/advisories/GHSA-68fv-2mgg-jv7q.
  package.json and package-lock.json have no task changes. This required audit gate is
  not green; dependency remediation was not part of this implementation.
- No browser visual inspection. Owner visual validation and real-device gates remain.
- Compared all prelaunch dirty-file copies in
  C:/Users/anton/AppData/Local/Temp/nextpost-rf12-20261012-222558/files against current files.
  No prior file is missing. Changed existing files are the intended RF-12 shared modules,
  tests, README and project state. Unrelated baseline files remain byte-identical.
  Existing plans/decisions/product reorganization notes remain unchanged.
- No commit, push, deployment or Trello mutation.

## Required corrections

These are concrete source findings in the final harness output, not hypothetical risks.
Local passing tests do not cover these exact paths.

1. **[P1] Prevent composer discard while publication is pending.**
   App.handleNavigation can set pendingNav during publication; the composer effect at
   frontend/src/ConsultationComposer.tsx:121 opens the exit dialog without checking
   publish.status. Its Discard handler at line 203 calls uploader.discard and navigates
   away; the dialog buttons do not block pending publication. Selecting My consultations
   while Publish is in flight can discard/unmount the preparation before the successful
   relinquish handoff. This violates FR-4 and the explicit pending navigation requirement.
   Ignore/block internal exits during pending publication and add a deferred-publication
   regression proving no discard/unmount and safe successful handoff.

2. **[P1] Suppress late list responses after navigation/account change.**
   frontend/src/MyConsultations.tsx uses generationRef for requests but has no unmount
   cleanup to invalidate it. A deferred list 401 after navigating away can still invoke
   onSessionLost against the current App session, including a newly signed-in account.
   Invalidate requests at unmount and when switching to detail; test delayed success/401
   after leaving and after account replacement.

3. **[P2] Revoke partially loaded photo URLs on 401.**
   frontend/src/useOwnerConsultationDetail.ts:153 calls onSessionLost and returns before
   revokeUrls(urls). Successfully created URLs from earlier photos are still local to
   load(), not photoUrlsRef, so unmount cleanup cannot release them. Revoke accumulated
   URLs before every session-loss return; test first photo success/second photo 401.

4. **[P2] Immediately clear protected presentation during denied-read reconciliation.**
   useOwnerConsultationDetail.ts:88 revokes URLs and clears link state but leaves phase
   as open until fetchMyConsultation resolves. A denied link request can leave the old
   question/context and image elements visible while reconciliation is pending or hung.
   Set a cleared loading/unavailable phase synchronously, then perform the bounded
   owner re-read. Add a deferred reconciliation test that asserts content is absent
   before that request resolves, as required by the accepted denied-request behavior.

5. **[P2] Serialize list refresh/load-more and reset pending flags on tab changes.**
   MyConsultations.refresh checks refreshing but not loadingMore; Load more checks its
   own flag but not refreshing. A Refresh during Load more increments the generation,
   causing the earlier finally to skip clearing loadingMore. A tab change during Refresh
   starts a new generation but loadInitial does not reset refreshing. The new tab can
   remain stuck with Refresh/Load more disabled. Use a coherent pending boundary/reset
   and test both overlaps, tab change during refresh, and retry from a failed later page.
   Refresh errors are rendered only when items.length > 0, so failed refresh of an empty
   list has no feedback. Move that feedback outside the nonempty branch.

6. **[P2] Enforce the approved strict owner response guards.**
   consultationApi.ts:174 onwards checks a blacklist of a few finalized keys, not an
   exact allowlist; dates are accepted as any string, cursors have no length/grammar bound,
   item counts/state do not match the requested page, and photo dimensions retain weak
   number-only checks. New clients also do not bind returned detail ID to requested ID.
   Reject forbidden/extra terminal keys, invalid dates/metadata, oversized cursors/pages
   and wrong-state/target responses; add focused runtime guard tests from the plan.
   The server owner-detail finalized branch in consultation_service.py still db.gets the
   complete ORM row, contrary to the minimal-column terminal projection requirement.
   Query only ownership/state/id/date first and load open content only for verified open.

7. **[P2] Supply real open-detail Refresh and complete tab keyboard semantics.**
   OwnerConsultationDetail renders Refresh for finalized/unavailable but not loaded open
   detail, despite the approved open Back/Refresh contract. Add the explicit refresh.
   MyConsultations declares tablist/tab roles without roving focus, arrow/Home/End
   handling or an associated tabpanel. Complete those keyboard/semantic contracts with
   automated tests; owner visual verification remains separate.

## Acceptance criterion audit

Numbers follow the ordered acceptance list in RF-12-Implementation-plan.md.

| Criteria | Inspection / current evidence |
| --- | --- |
| 1: fourth destination, Home default | Present; Navigation/App tests pass |
| 2: recover after exit/reload/login/restart | Entry/persistence boundaries present; built restart/two-account proof pending |
| 3: owner list/state/date/pagination | Present; local tests pass; PostgreSQL ordering pending |
| 4: finalized minimum fields | HTTP response tests pass; exact client/DB minimal-column requirement needs correction 6 |
| 5: neutral open detail/Back/Refresh | Neutral wording/Back present; open Refresh missing (7) |
| 6: real Private controls/reconciliation | Real reused mutations present; denied/stale request presentation needs correction 4 |
| 7: disabled owner access/copy limitation | Existing authorization preserved; honest limitation copy present |
| 8: truthful loading/empty/error/refresh | Basic tests pass; overlap/empty-refresh failure feedback needs correction 5 |
| 9: ownership/isolation/headers | Server queries/per-ID owner checks and local tests pass; strict client target binding needs correction 6 |
| 10: terminal no storage/detail/link | Branch calls no media/link; complete ORM selection needs correction 6 |
| 11: every URL/late-response path | Corrections 2–4 required; existing tests do not prove every path |
| 12: composer pending/dirty/relinquish | Basic dirty/handoff tests pass; pending navigation violates requirement (1) |
| 13: truthful cap/list entry | Present; updated cap test passes |
| 14: no unavailable feature/infra additions | No vote/result/terminal/Public share/draft/router/migration/package added |
| 15: English/accessibility/safe area | English/style base retained; keyboard tabs need correction 7; visual gate pending |
| 16: full checks/PostgreSQL/built proof | Local checks pass; audit fails; live PostgreSQL and built smoke unverified |
| 17: narrow completion/no unauthorized mutation | State corrected to review with findings; no external mutation |

## Next gate

Correct the findings within the approved scope and validate their exact regression paths,
then repeat only the checks warranted by those changes. Complete isolated PostgreSQL and
built-stack proof when that environment is available. Resolve the real dependency-audit
failure through an appropriate dependency change, preserving approved versions unless
explicitly authorized. Product-owner visual and iPhone/TestFlight checks remain distinct.
Do not mark RF-12 Completed and validated while these requirements remain unmet.
