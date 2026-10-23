# RF-32 - Restricted administrator removal - Implementation Review

## Status

`Implemented and technically validated`

The product owner explicitly authorized direct coordinator implementation after repeated OpenCode Go
launches remained at zero tokens because the subscription quota was exhausted. This review covers
only the DEC-022/DEC-046 restricted open-consultation removal increment, not the broad RF-32 card.

## Scope and acceptance review

- The sole human surface is `python -m app.remove_consultation`; no FastAPI/OpenAPI route, frontend
  code, administrator role, application credential or general administration abstraction exists.
- Deployment access remains authority. `REMOVAL_OPERATOR_ID` is read only by the command from the
  backend environment, validated as a bounded attribution label and absent from frontend source,
  build configuration, URLs and product responses.
- The command requires canonical target UUID twice, literal `expected_state=open`, a caller-created
  canonical operation UUID and one controlled reason. It emits sanitized JSON and stable exits
  `0/2/3/4/5`.
- `consultation_removals` is a one-to-one immutable application record with a globally unique
  operation UUID, UTC timestamp, operator label, controlled reason and previous state `open`.
  Database constraints enforce the bounded/controlled fields. Migration 0010 performs no historical
  backfill and refuses downgrade after use.
- The service locks the consultation, detects global operation collisions, proves exact replay and
  atomically marks RF-37 media, deletes raw votes, sanitizes terminal content, inserts audit and
  commits `removed`. PostgreSQL constraint races become defined conflicts rather than internal
  errors.
- Finalized/deleted/historical removed targets conflict; unknown targets are unavailable. An open
  row with finalization/outcome evidence fails safely rather than adjudicating results.
- Existing state-based authorization immediately removes feed/detail/photo/link/vote access. Open
  RF-21 history disappears with the raw vote and no outcome/tombstone is created.
- RF-37 cleanup remains separate. Verified absence detaches the visual ledger while the immutable
  removal record and `removed` state survive.
- Account suspension, reports/cases, moderation UI, evidence archives, restoration, user-facing
  reasons, notifications, appeals and finalized-result changes remain absent.

## Validation evidence

- Focused SQLite/service/command/access/history/reconciliation tests: 28 passed.
- Complete backend suite: 569 passed, 77 skipped.
- Real PostgreSQL 18 migration and concurrency matrix: 14 passed. It covered fresh/0009 upgrade,
  no historical backfill, downgrade refusal, vote/finalization/author-delete races, identical and
  differing removals and concurrent cross-target operation reuse.
- Strict Ruff check and format: 77 backend files passed.
- Strict MyPy: 34 backend source files passed. Small missing annotations/import ownership in existing
  RF-21/consultation code were corrected without changing runtime behaviour so the mandated full
  check is green.
- Frontend regression: 45 files and 596 tests passed; Prettier, ESLint, TypeScript and production
  build passed. Static inspection found no removal command/configuration reference in frontend code.
- Compose configuration and final backend/frontend image builds passed.
- Fresh built-image smoke on disposable PostgreSQL 18 passed migration to 0010, first removal,
  exact replay and separate RF-37 cleanup. The observed first result marked two images and removed
  one vote; replay performed zero side effects; cleanup reported two already-absent objects, zero
  failures/anomalies and one completed terminal session. Database verification was
  `removed`, source session detached, content null, zero votes and exactly one audit row.
- Built-command failure checks returned exit `2` with only `invalid_input` when operator
  configuration was missing and exit `3` with sanitized identifiers for an unknown target.
- `git diff --check` and equivalent checks for every new untracked file passed. Both disposable
  PostgreSQL containers were removed; no implementation process remains active.

## Known repository-level limitation

`npm audit --audit-level=high` reports one high Vite advisory and two moderate Vitest advisories.
The suggested remediation requires forced upgrades outside the declared dependency ranges. These
are pre-existing development-tool dependencies and were not changed as part of the command-only
RF-32 increment; all frontend executable validation passed. Dependency remediation remains a
separate explicitly scoped task.

## Final assessment

Every RF-32 restricted-removal acceptance criterion is implemented and supported by executable
evidence. No visual/product-owner acceptance is required because there is no application UI. No
commit, push, deployment or Trello mutation was performed.
