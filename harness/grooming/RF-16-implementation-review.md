# RF-16 - Cast an independent vote - Implementation Review

## Review status

`Completed and validated`

Reviewed on 2026-10-16 against
`harness/features/RF-16-Implementation-plan.md`. The OpenCode final report was treated as
evidence to verify, not proof of completion. The worktree, implementation, migration, tests and
documented commands were inspected independently. No commit, push, deployment, browser visual
inspection or Trello mutation was performed.

On 2026-10-16 the product owner completed the real-iPhone review, confirmed the final Home behavior
works after the reported corrections, and explicitly requested closure. This satisfies the retained
DEC-034 visual/UI gate. No commit, push, deployment or Trello mutation was performed.

## Delivered scope

- Additive immutable Vote persistence with one vote per consultation/account, restrictive account
  and consultation foreign keys, composite same-consultation photo integrity and the RF-18 index.
- Transactional `FOR UPDATE` submission using current `AccessOperation.vote` authorization,
  exact replay success and immutable different-selection conflict behavior.
- Viewer-scoped `my-vote` and vote submission APIs with strict request/response shapes, trusted-
  origin protection, current Private capability support and protected response headers.
- Set-wise current-account `has_voted` feed projection and `Voted` card marker without aggregates.
- Reader selection, chosen-photo review, cancel/back, confirm, ambiguous-response reconciliation,
  definitive `Your vote` recovery and optional current Private-token reuse.
- Bounded RF-14 prerequisite repairs for stale preview ownership, hidden feed/Back revalidation,
  enlargement focus containment and protected success/error privacy headers.
- Reproducible migration/concurrency tests and isolated built-stack smoke artifacts.

## Coordinator corrections after harness handoff

Independent inspection found and corrected four gaps before acceptance:

1. The inline review named the selected photo but did not display it. It now includes the chosen
   image with an explicit accessible label.
2. Refresh from a vote-authorization unavailable state retried detail only, leaving vote state
   permanently unavailable. It now refreshes both protected resources.
3. Changing a Private token on an existing reader instance did not automatically reauthorize
   detail/vote state. Both controllers now reload when the token changes.
4. Home could restore focus before Back revalidation completed. Focus now waits for reconciliation
   and falls back to the Home heading when the selected card disappears.

The owner-device session also exposed and corrected three integration defects: iPhone still photos
arriving as HEIF/MPO containers were normalized to JPEG, LAN HTTP origins no longer crash Private
owner detail while constructing its share link, and Home preview cards now reserve a stable frame
through idle/loading/ready/error states to prevent scroll drift. The owner confirmed the corrected
Private detail and Home scrolling before closing RF-16.

Focused regression tests cover each correction. A final Python formatting failure in the late-added
migration test was also normalized and all quality checks were rerun.

## Acceptance review

| Approved acceptance area | Evidence and result |
| --- | --- |
| Compare, enlarge, select, review, cancel and confirm | Implemented with semantic radio controls, separate enlargement, chosen-photo inline review and confirm-only write. Automated tests pass. |
| One immutable vote under retries/concurrency/direct SQL | Unique key, consultation lock and exact replay/conflict behavior verified by API, migration and PostgreSQL race tests. |
| Owner/access/revocation/terminal/late denial | Canonical vote access policy is rechecked under lock; unit, PostgreSQL terminal-writer and built smoke evidence pass. |
| Ambiguous response and different winner | One authoritative `my-vote` reconciliation; retryable/unknown states never claim success or silently resubmit. Hook tests pass. |
| Reload/sign-in/current-account recovery | Viewer-scoped status API and built-stack relogin/restart smoke pass. |
| Home chronology and `Voted`; `Your vote` detail | Set-wise boolean keeps feed ordering; UI and API tests pass. Private remains undiscoverable. |
| No aggregate/other-voter exposure | Exact API projections, strict client guards and built smoke contain no result fields. |
| Protected headers and server authority | Middleware covers consultation success/error/auth/validation paths; vote/feed/detail/photo tests and smoke verify required headers. |
| Stale requests, Back revalidation and URL cleanup | Permanent Home/preview/detail tests cover stale 401/success, URL revocation, page-range reconciliation and focus fallback. |
| Keyboard/focus behavior | Automated dialog containment, Escape, radio/review and focus-return/fallback tests pass. Product-owner real-iPhone interaction was accepted on 2026-10-16. |
| Migration/build/full regression evidence | Recorded below. No destructive active-data operation occurred. |
| Explicit future/debt boundaries | RF-14 F3/F5/F6 and RF-18/19/20/26/37 remain outside this implementation. |

## Validation evidence

### Harness evidence

- Disposable PostgreSQL 18 full backend suite: 398 passed, 0 skipped, including Alembic fresh and
  `0004 -> head` upgrades, data preservation, direct-SQL constraints, empty downgrade, populated
  downgrade refusal, concurrent same/different choices, many voters and terminal-writer locking.
- Frontend at harness handoff: 405 passed with format, lint, strict typecheck and production build.
- Isolated Compose build and two-account smoke passed: Public and current-Private vote/replay/
  conflict, self-vote denial, revoked capability, own-vote recovery, Home marker, restart
  persistence and no aggregate exposure. Disposable services and volumes were removed.

### Independent coordinator evidence after corrections

- Focused backend API/feed suite: 45 passed.
- Final full frontend suite after owner-device corrections: 33 files, 419 passed, including direct
  strict vote API payload/error guards and stable Home preview-frame coverage.
- Backend Ruff check and format check: passed.
- Backend strict mypy: passed.
- Frontend Prettier, ESLint and strict TypeScript: passed.
- Frontend production build: passed.
- Frontend dependency audit at high severity: 0 vulnerabilities.
- Compose configuration and `git diff --check`: passed.

The coordinator did not repeat the already-passing disposable PostgreSQL/Compose smoke after the
four corrections because they affect only client review/refresh/token/focus behavior; full client
tests and production build were rerun after those changes.

## Product-owner visual/UI checklist

- At mobile width, compare at least two photos, enlarge and close with both Close and Escape.
- Select a photo, enter review and verify the chosen image/number and finality warning are clear.
- Use Cancel and Back to photos; confirm that no vote is sent until Confirm vote.
- Confirm once and verify `Your vote`, `Votes cannot be changed` and continued enlargement.
- Return Home and verify the consultation keeps its chronological position with `Voted`.
- Check keyboard Tab/Shift+Tab containment in enlargement and sensible focus after closing/Back.
- Check long text, RTL content, 200% zoom, 320px width and safe-area/navigation clearance.

## Closure and later boundaries

- Real Private-link entry/authentication return remains RF-26; RF-16 proves only the reusable
  current-token contract.
- Deployment and real-device/TestFlight validation are not authorized or claimed.

