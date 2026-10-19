# RF-18 - Consult results as author - Implementation Review

## Status

`Completed and validated`

Reviewed on 2026-10-18 against
`harness/features/RF-18-Implementation-plan.md`. This review covers the approved live Open,
count-only increment. It does not claim the broader Trello card's deferred percentages or finalized
snapshot/presentation.

## Delivered behavior

- The authenticated owner-only Open list returns and displays `total_votes` for every row.
- `GET /api/my-consultations/{consultation_id}/results` returns the exact allowlisted Open aggregate:
  consultation ID/state/total plus ordered photo ID, ordinal and count.
- The aggregate is derived from normalized RF-16 votes with a zero-preserving outer join. It exposes
  no identity, individual choice, timestamp, percentage, ranking or winner.
- Open owner detail displays the total and each photo's exact count in immutable order. Zero options
  remain visible and equal counts remain natural ties.
- Open list and detail load immediately and refresh every five seconds only while visible/current.
  Requests do not overlap, hidden/inactive scopes pause, visibility return refreshes immediately,
  stale successes survive network failure, and late item/account responses are ignored.
- Initial failure, stale refresh failure, generic unavailable and session loss are distinct. Generic
  denial removes counts and stops polling until the owner reconciles the consultation state.
- Finalized and participant/general surfaces remain aggregate-free.
- No migration, counter cache, worker, storage access or finalized snapshot was added.

## Harness evidence

The configured OpenCode harness used `opencode-go/deepseek-v4-pro` with variant `high` and exited
successfully. It reported:

- backend: 420 tests passed with zero skips against disposable PostgreSQL 18;
- frontend: 448 tests passed before coordinator review additions;
- Ruff check/format and strict mypy passed;
- Prettier, ESLint, strict TypeScript and the production build passed;
- `npm audit --audit-level=high`: zero vulnerabilities;
- `docker compose config --quiet` passed;
- rebuilt isolated-stack smoke passed initial zero counts, a tie with an untouched zero option, list
  total, anonymous/voter denial, aggregate-free participant surfaces and restart persistence;
- disposable containers and volumes were removed.

The reproducible smoke assets are `harness/validation/rf18-compose.override.yaml` and
`harness/validation/rf18_built_smoke.py`.

## Independent coordinator review

The coordinator compared the final tree to the retained prelaunch manifest and inspected the
authorization boundary, aggregate query, strict client guard, list/detail integration and polling
lifecycle. Four review gaps were corrected:

1. the exact `/api/my-consultations` 401 path now receives private no-store/nosniff/no-referrer
   headers as well as nested owner routes;
2. response schemas explicitly constrain totals, ordinals and counts to non-negative integers;
3. a result denial now renders a distinct unavailable state, removes old counts and stops polling;
4. automated coverage now proves hidden-document pause and immediate refresh on visibility return.

Post-correction evidence:

- 43 focused backend tests passed; Ruff, Ruff format and strict mypy passed;
- 149 focused frontend tests passed; ESLint and strict TypeScript passed;
- full local backend suite: 393 passed, 28 PostgreSQL-only tests skipped as expected;
- full frontend suite: 451 passed in 34 files;
- Prettier, production build and dependency audit passed; zero vulnerabilities;
- Compose configuration and `git diff --check` passed. Only existing line-ending conversion warnings
  were emitted; no whitespace error was found.

The coordinator did not repeat the already successful rebuilt PostgreSQL smoke after the four
corrections because none changed persistence or aggregate SQL; the focused backend coverage verifies
the header/schema changes and the full rebuilt-stack evidence remains applicable.

## Acceptance-criterion assessment

- [x] Owner Open list displays current total counts.
- [x] Open owner detail displays exact total and per-photo counts in immutable order.
- [x] Zero options and ties are preserved without ranking or hidden tie-breaking.
- [x] No percentage is returned or displayed.
- [x] Immediate and five-second visible-view refresh behavior is implemented and tested.
- [x] Initial/stale/unavailable/session failure behavior is explicit and safe.
- [x] Server-side owner authorization is non-enumerating; participants receive no aggregates.
- [x] Payloads and UI disclose no voter identity or individual choice.
- [x] Late responses and inactive scopes cannot repopulate protected result state.
- [x] Finalized and participant behavior remains compatible and aggregate-free.
- [x] Aggregates are set-wise and use existing RF-16 data without a migration or counter cache.
- [x] Automated, PostgreSQL and rebuilt-stack validation pass.
- [x] Product owner completed the DEC-034 visual acceptance check on 2026-10-19 using the
      disposable LAN instance, an actual three-photo consultation and nine votes from nine
      separate test accounts; the owner explicitly requested closure.

## Remaining boundary

Percentages and durable finalized/photo-free results remain deliberately deferred. RF-19/RF-20 must
define and atomically write terminal aggregates/outcomes before RF-37 removes photos. No commit,
push, deployment or Trello mutation occurred.

The temporary LAN services were stopped cleanly after acceptance. Their isolated volumes were
retained so the review consultation and votes remain recoverable; no ordinary project data or
services were touched.
