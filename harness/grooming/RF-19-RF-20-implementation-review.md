# RF-19/RF-20 implementation review

## Status

`Completed and validated`

Reviewed on 2026-10-20 against
`harness/features/RF-19-RF-20-Implementation-plan.md` after the implementation harness completed.
No product code was changed during this review.

## Findings

### P1 - The irreversible action has no separate review step

`frontend/src/FinalizeConsultationDialog.tsx` renders the option controls and the destructive
`Finalize consultation` button together. Selecting a checkbox enables that button and one click
submits immediately. The inline `Your choice` sentence is useful feedback, but it is not the
approved review step and does not create a second deliberate confirmation boundary.

This contradicts the approved UX requirement for a selection/review flow in the same dialog and
weakens the primary mitigation for accidental permanent finalization and photo erasure. Add an
explicit transition to a review state that summarizes the choice and offers Back/Cancel plus the
destructive final action. Keep the current focus, retry identity and duplicate-submit guarantees.

### P2 - Successful finalization discards the selected item instead of opening authoritative detail

`frontend/src/App.tsx` clears `selectedMyConsultationId` on success, and
`frontend/src/MyConsultations.tsx` does the same in its local success handler. The user therefore
lands on the Finalized list, not the newly finalized consultation detail. This also throws away the
operation's response and relies only on the list fetch.

The approved success contract requires the photo-bearing view to unmount, then the UI to switch to
the Finalized tab/detail and refetch the owner projection authoritatively. Preserve the finalized
consultation ID, select the Finalized tab, and let the detail perform its ordinary authoritative
read.

### P2 - Finalized list rows omit the finalization date

`frontend/src/MyConsultations.tsx` renders the publication date, declaration and total count, but
never renders `item.result.finalized_at`. The approved finalized-list contract explicitly requires
both publication and finalization dates. Render the finalization date for new-contract rows while
retaining the honest legacy `Final result unavailable` behavior.

### P2 - Downgrade can silently drop orphan selection/count records

The migration states that downgrade must refuse after any finalization, selection, count or outcome
has been persisted. Its guard checks only `consultation_finalizations` and
`consultation_outcomes`. Because the selection and count tables reference stable photos but do not
reference the finalization header, PostgreSQL permits either table to contain rows while both
guarded tables are empty. Downgrade then drops those records without refusal.

Make selection/count ownership by the header enforceable (or otherwise prevent orphan replacement
records), and make the downgrade guard check every irreversible table as documented. Add a real
PostgreSQL migration test for the selection-only/count-only cases.

## Independent evidence

- Focused backend suite: `85 passed`.
- Focused frontend suite: `81 passed` across five RF-19/RF-20 files.
- Frontend TypeScript project check: passed.
- `git diff --check`: passed before review.
- Harness-reported broader evidence remains useful: 510 local backend passes, 56 PostgreSQL passes,
  555 frontend passes, clean frontend lint/format/type/build/audit and successful Compose build.
- The harness-reported seven MyPy errors and one Ruff line-length error are pre-existing and outside
  the RF-19/RF-20 changes; they do not explain the findings above.

## Review conclusion

The four findings above were corrected in the harness corrective pass and independently re-reviewed
on 2026-10-20:

- The irreversible dialog now has separate selection and review states with Back, Cancel and the
  final destructive action; retry identity, selection, focus handling and duplicate protection are
  preserved.
- Successful finalization keeps the consultation selected, switches to Finalized and performs the
  authoritative owner-detail read after photo-bearing content is unmounted.
- New-contract finalized rows show both publication and finalization dates; legacy rows remain
  honestly result-unavailable.
- Selection and count rows now reference the finalization header, the service flushes that header
  before its children, and downgrade checks all four irreversible tables.

Independent correction evidence: 85 focused backend tests and 83 focused frontend tests passed,
and `git diff --check` remained clean. Harness evidence adds 557 passing frontend tests, clean
frontend lint/format/type/build, clean backend Ruff/format/MyPy, seven real-PostgreSQL migration
tests, six RF-19/RF-20 concurrency tests and 63 total PostgreSQL/migration tests. The disposable
PostgreSQL container was removed.

Running every backend file in one process with `TEST_DATABASE_URL` exposes a pre-existing test-only
logging isolation problem because Alembic reconfigures logging before later `caplog` assertions.
The PostgreSQL/migration files pass when run as the repository's validation matrix runs them by
file; this does not affect runtime behavior or the RF-19/RF-20 acceptance results.

No actionable code finding remains in the reviewed scope. On 2026-10-21, the product owner exercised
the supplied manual journey against the isolated LAN-accessible built stack and reported that it
worked perfectly. This satisfies the remaining subjective visual, responsive/mobile and interaction
gate under DEC-034, so RF-19/RF-20 are `Completed and validated`.

The isolated frontend, backend and database containers, Compose network and dedicated test-data
volumes were removed after acceptance at the product owner's previously stated request. No ordinary
development data was affected. No commit, push, deployment or Trello mutation was performed.
