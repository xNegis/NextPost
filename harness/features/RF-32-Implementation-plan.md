# RF-32 - Restricted administrator consultation removal - Implementation Plan

## Status

`Ready for implementation`

The product owner accepted grooming choices `Q1A` through `Q8A` and explicitly approved plan
finalisation on 2026-10-23. This plan implements only the DEC-022 MVP exception, not the broad
RF-32 card.

## Source ticket

- Trello title: `RF-32 · Retirar contenido y suspender cuentas`
- Trello URL: https://trello.com/c/jQPe9AZ6/33-rf-32-retirar-contenido-y-suspender-cuentas
- Trello list at intake: `Después · cuentas y administración`
- Snapshot captured on: `2026-10-23T13:49:14.2309810+02:00`
- Grooming notes: `harness/grooming/RF-32-grooming.md`

## Objective

Give one designated operator a deliberately narrow, irreversible way to remove one open
consultation from NextPost when rights/privacy, safety/abuse or integrity concerns require manual
intervention. The operation must immediately revoke every product access path, discard open votes,
schedule all associated photographs for RF-37 erasure and leave only a minimal immutable audit and
idempotency record.

The capability is a restricted backend command operated through controlled deployment access. It
must not create an administrator web/API surface, expose an administrative credential to ordinary
clients or expand into suspension, reports, case management, result adjudication or a general
moderation system.

## Context and current behaviour

- `ConsultationLifecycle` and `ConsultationState` already define `open`, `finalized`, `deleted` and
  `removed`. DEC-033 requires voting and all terminal writers to lock the consultation row; the
  first terminal transaction to commit wins without priority.
- Existing feed, detail, photograph, Private-link and vote authorization admits only `open` rows.
  A committed `removed` state is therefore immediate logical revocation and generic
  unavailability; no new read-path condition or tombstone is required.
- `app.photo_erasure_service.mark_media_for_erasure` is the RF-37 transaction-local seam. It
  requires the locked consultation to be open and backed by its unique consumed upload session. It
  deactivates Private-link access and marks the complete session without committing or touching the
  filesystem.
- `sanitize_terminal_content` applies DEC-023 terminal minimization. RF-37's
  `reconcile_terminal_media` already discovers `removed` rows and owns exact deletion, absence
  verification, partial-failure retry and visual-ledger removal. Startup/hourly maintenance and
  `python -m app.cleanup` already invoke that reconciliation.
- `app.consultation_deletion_service` and `app.consultation_finalization_service` demonstrate the
  required lock, transaction, vote and terminal-consumer patterns. They do not authorize or perform
  administrative removal.
- RF-21 derives participation history from current open votes or finalized semantic outcomes.
  Removing an open consultation deletes its raw votes and creates no outcome or tombstone, so its
  history rows disappear. Finalized consultations and their outcomes are not targets of this plan.
- There is no production removal service, operational command, administrator authority, audit row
  or removal configuration. A `_remove` helper in PostgreSQL concurrency tests is only a fixture and
  must not be reused as production behaviour.
- `app.config.Settings` loads deployment environment values. `.env.example` and
  `docker-compose.yml` document/pass backend configuration. Normal product authentication has no
  administrator role and the reserved alias `admin` conveys no authority.
- Alembic head is `20261021_0009_participation_history.py`. The next migration must be additive and
  must preserve historical rows, including any pre-existing `removed` fixture/data without
  inventing an actor, reason or timestamp.

Binding decisions are DEC-020, DEC-022, DEC-023, DEC-033, DEC-041, DEC-042, DEC-044, DEC-045 and
DEC-046.

## Scope

### In scope

- A backend-only command that removes exactly one open consultation.
- Authority through controlled deployment/host/container access, separate from application users.
- A required bounded server-side `REMOVAL_OPERATOR_ID` attribution label, unavailable as a command
  argument and never treated as a product credential.
- Explicit inputs: canonical target UUID, the same UUID repeated as confirmation,
  `expected_state=open`, caller-created operation UUID and one controlled reason code.
- One immutable, one-to-one removal record holding target, globally unique operation identity, UTC
  timestamp, operator label, controlled reason and previous state `open`.
- Exact idempotent replay and rejection of mismatched target, payload or operation reuse.
- Row-lock serialization with voting, finalization, author deletion and another removal.
- Atomic vote deletion, RF-37 marking, Private-link revocation, terminal sanitization, audit insert
  and lifecycle transition to `removed`.
- Sanitized structured command output, stable exit meanings and restricted observability.
- Additive migration and safe historical compatibility.
- Unit, SQLite, real-PostgreSQL concurrency, migration, command, RF-37 failure/recovery and isolated
  built-stack validation.
- Operator documentation for exact targeting, operation-ID preservation, exit interpretation and
  separate RF-37 cleanup/status follow-up.

### Out of scope

- Suspending, limiting, deleting or invalidating sessions for accounts.
- User reports, reporter identity, report review, moderation cases, queues or inboxes.
- A moderation console, general administration UI, FastAPI operational route or remote admin API.
- Administrator roles, permissions or credentials managed through NextPost accounts.
- Visual evidence archives, copied content, allegation notes or free-text removal reasons.
- Removing finalized consultations, invalidating/recalculating final results, or changing retained
  RF-21 outcomes.
- Restoring, undoing, republishing or reopening removed content.
- User-facing reason disclosure, notification, appeal or review workflow.
- RF-30 reputation/scoring, RF-31 report handling or RF-42 notifications.
- Synchronous physical deletion as part of removal success.
- Trello changes, deployment and production data operations.

## Operator and product experience

The operator works only from an approved backend runtime with database access and a configured
`REMOVAL_OPERATOR_ID`. Before invoking the command, the operator obtains the exact consultation UUID
through an authorized operational process, generates and preserves a fresh operation UUID, chooses
one allowed reason and supplies the consultation UUID twice. The command is non-interactive so its
input and retry contract are deterministic.

The command rejects malformed or non-canonical UUIDs, unequal target/confirmation UUIDs, any
expected state other than literal `open`, an unsupported reason, or missing/invalid operator
configuration before starting the destructive transaction. It must not offer `--yes`, fuzzy lookup,
question-text lookup, author lookup, bulk selection or implicit “latest” targeting.

On first success it emits one sanitized structured result identifying only the classification,
consultation UUID, operation UUID, previous state and safe aggregate counts such as votes removed
and images marked. An exact retry emits the same stable identity with classification `replay`; it
does not repeat destructive work. Product users immediately observe the existing generic
unavailability on feeds, detail, photographs, Private links and vote attempts. RF-21 open history
rows disappear because the votes no longer exist.

The command does not run filesystem cleanup. Documentation tells the operator how to inspect/run
the existing restricted RF-37 maintenance command separately and how to escalate overdue or
anomalous work. A cleanup failure cannot change command success or restore access.

No visual UI is introduced, so frontend accessibility, responsive layout and browser interaction
requirements do not apply. Terminal output must remain readable machine-oriented JSON and stable
exit codes must also make the result unambiguous to a human operator.

## Functional requirements

### FR-1 - Restricted command surface and authority

Provide a dedicated backend module runnable as `python -m app.remove_consultation`. It must not be
mounted from `app.main`, imported as a FastAPI router or represented in frontend code.

Deployment/host access is the authorization boundary. The command obtains
`REMOVAL_OPERATOR_ID` only from backend environment configuration. Validate after trimming with an
explicit conservative character/length policy suitable for an opaque operational label; reject
empty, malformed or oversized values. Do not accept the label as a positional/optional command
argument and do not require it for ordinary API startup or frontend configuration.

### FR-2 - Exact target and irreversible confirmation

Require all of the following non-interactive inputs:

- target consultation UUID in canonical textual form;
- a separate confirmation value equal to that canonical UUID;
- exact expected state `open`;
- caller-generated canonical operation UUID;
- reason `rights_or_privacy`, `safety_or_abuse`, `vote_integrity` or `other`.

Reject invalid input before opening the removal transaction. The command must never accept a URL,
Private-link token, question text, alias, owner identity or list/bulk expression as the target.

### FR-3 - Minimal immutable removal record

Add a one-to-one `consultation_removals` record with:

- `consultation_id` as primary key and restrictive foreign key to `consultations.id`;
- globally unique, non-null `operation_id`;
- timezone-aware, non-null `removed_at` supplied by the service clock;
- bounded, non-null `operator_id` copied from validated server configuration;
- bounded, non-null `reason_code` constrained to the four accepted values;
- non-null `previous_state` constrained to literal `open`.

The application must expose no update/delete path for this row. It stores no copied question,
context, account alias, photograph information, vote choice, Private-link capability, storage key,
free-text note or credential.

### FR-4 - Atomic removal transaction

The application service must:

1. begin a transaction and fetch the exact consultation row with `FOR UPDATE`;
2. classify missing, terminal and possible replay states under the lock;
3. ensure a first execution is a coherent open consultation, with no finalization header/outcome
   data that would require result adjudication;
4. call `mark_media_for_erasure` while the row is still locked and open;
5. delete every raw `Vote` for the consultation without creating an outcome or history tombstone;
6. call `sanitize_terminal_content`;
7. insert the immutable removal record;
8. set the canonical lifecycle to `removed`; and
9. commit once.

The RF-37 marker must not commit or touch storage, and the command/service must not attempt physical
file deletion. Any pre-commit failure rolls the entire unit back, leaving state, link access, votes,
audit and media markers unchanged.

### FR-5 - Idempotency and replay

Only a persisted removal record matching the same consultation UUID, operation UUID,
`expected_state=open`, operator label and reason is an exact replay and returns exit success. Replay
does not call the RF-37 marker, delete votes, sanitize or rewrite timestamps.

The following are conflicts with no mutation:

- the target is already `removed` but has no matching audit row;
- the target has an audit row but any replay field differs;
- the operation UUID already belongs to another consultation;
- the target is `finalized` or `deleted`;
- the target changed away from `open` while this operation waited for its lock.

An unknown consultation is unavailable rather than proof of existence through extra detail.

### FR-6 - Concurrency and terminal precedence

Removal must participate in the existing consultation-row lock protocol. Voting, finalization,
author deletion and removal have no priority; the first transaction to commit wins. A losing vote
must re-read the terminal state and fail. A losing removal must return conflict without overwriting
the winner, creating an audit row, changing outcomes or touching RF-37 data. Two identical removal
attempts converge to first success plus exact replay; different operation/payload attempts converge
to one success plus conflict.

### FR-7 - Immediate access revocation and history semantics

After commit, existing authorization must exclude the removed consultation from public/private
feeds, owner views, ordinary detail, photographs and votes. Current and stale Private-link tokens
must fail generically. No endpoint may reveal the audit record, operator or reason.

All open raw votes are deleted atomically. RF-21 therefore has no open history row and no new
unavailable/tombstone row. Because finalized consultations are rejected, this increment never
preserves, deletes, replaces or reinterprets finalized semantic outcomes.

### FR-8 - RF-37 physical erasure and recovery

Database commit is removal success. The complete consumed photo session is marked by the existing
RF-37 seam in that transaction. Existing startup/hourly/manual reconciliation later deletes each
exact object, verifies absence, retries partial failures and removes visual metadata only after
convergence.

A storage failure, process crash after commit, restart or repeated cleanup must leave product access
denied and must not modify the immutable removal record. The command may point the operator to the
separate cleanup/status procedure but must not invoke it implicitly.

### FR-9 - Stable output, errors and observability

Emit exactly one structured, sanitized JSON result to the appropriate stream and use stable process
exit meanings:

- `0`: first success or proven exact replay;
- `2`: invalid arguments, confirmation, reason or operator configuration;
- `3`: target unavailable/not found;
- `4`: lifecycle, operation-identity or replay-payload conflict;
- `5`: unexpected database/application failure before a confirmed commit.

Do not report physical cleanup as part of this exit contract. Logs/output may include
classification, consultation/operation UUID, previous lifecycle, controlled reason and aggregate
counts. They must exclude questions, context, aliases, session cookies, secrets, database URLs,
Private-link tokens, storage keys, image data, vote choices, stack traces in normal structured
output and raw exception/database payloads. Detailed restricted diagnostics may use existing server
logging without weakening these exclusions.

### FR-10 - Configuration and non-exposure

Document `REMOVAL_OPERATOR_ID` in `.env.example` and pass it only to the backend service in
`docker-compose.yml`. No value belongs in frontend build args, Vite variables, browser storage,
URLs, HTTP headers, source maps or product API responses. It is an attribution label rather than a
secret; actual authority remains deployment access. Existing database/session/private-link secrets
must not be accepted as removal arguments or printed by the command.

### FR-11 - Migration and historical compatibility

Add a new Alembic revision after `20261021_0009` with the removal table, foreign key, unique
operation constraint and value constraints. Upgrade does not change consultation state and does not
backfill records for historical `removed` rows because actor, reason and time are unknowable.

Downgrade is safe only while no removal record exists. Once the new operation has been used,
downgrade must refuse rather than erase the immutable audit/idempotency record. Fresh install,
upgrade from populated head, empty-table downgrade/upgrade and used-table refusal require tests on
SQLite where supported and real PostgreSQL.

### FR-12 - Documentation and operational safety

Add a restricted runbook covering prerequisites, exact UUID acquisition, generation and durable
preservation of the operation UUID, allowed reasons, double-target confirmation, examples that do
not place credentials in command lines, all exits, exact-retry procedure, conflict escalation and
separate RF-37 cleanup/status follow-up. State explicitly that the operation is irreversible and
supports only open consultations.

The runbook must not document direct database updates as a supported removal method and must not
present the test-only `_remove` helper as operational functionality.

## Technical approach

Create a domain/application service, expected at `backend/app/consultation_removal_service.py`, that
owns locking, classification, exact replay, atomic side effects and sanitized outcomes. Keep CLI
parsing/configuration/process exits in a thin intended entry point at
`backend/app/remove_consultation.py`. The service accepts already validated typed values and remains
independently testable; the command creates a session, calls it and maps domain results/errors to
the stable JSON/exit contract.

Reuse `_remove_votes` only after moving it to an appropriately shared private helper or implement
the same small explicit delete/count operation without importing an author-specific service. Do not
introduce a generic moderation framework. Reuse `ConsultationLifecycle`/`ConsultationState`,
`decide_transition`, `mark_media_for_erasure`, `sanitize_terminal_content`, the session factory and
the existing UTC clock seam.

For exact replay, lock the consultation first and query the one-to-one audit identity within the
same transaction. Also check the globally unique operation UUID so cross-target reuse is a defined
conflict rather than an unhandled integrity error. Database constraints remain the final defense
against races. Treat an open row carrying finalization/outcome records as an internal consistency
failure and roll back; do not silently erase or preserve adjudicated data through the open-only
path.

### Affected areas

- Frontend: none; add regression evidence that no route, client, environment value or bundle
  reference is introduced.
- Backend/application: new removal service and command; existing lifecycle, access, vote,
  finalization, deletion and RF-37 services are integration boundaries, not new admin surfaces.
- Domain/data model: new immutable removal model/reason representation and relationship only where
  useful; no account role or consultation content column.
- Storage/background work: unchanged RF-37 marker/reconciler and `app.cleanup`; only a new real
  terminal consumer.
- Configuration/deployment: command-only `REMOVAL_OPERATOR_ID` validation, `.env.example`, backend
  Compose environment and restricted runbook.
- Migration: new additive Alembic revision after `20261021_0009`.
- Tests: new removal service/command/migration/PostgreSQL suites plus access, participation, RF-37
  and terminal-race regressions.
- Documentation: operator runbook and any concise backend operational reference needed to discover
  the command safely.

### Data and migration requirements

Use portable SQLAlchemy/Alembic types consistent with current models: `Uuid`, timezone-aware
`DateTime`, bounded `String` columns and explicit check constraints. Prefer a string/check
representation for controlled reasons so SQLite and PostgreSQL validate the same domain without a
new native database enum. Use `ondelete=RESTRICT` for the audit-to-consultation relationship and a
unique constraint for `operation_id`.

The table is append-only at the application layer. It is retained with the consultation because it
is the proof for exact retry and minimal administrative accountability. There is no independent
analytics/export requirement and no free text. Existing backup/restore procedures include the row
as ordinary database state. A restored database plus empty photo volume follows RF-37's existing
pre-traffic reconciliation rule and never resurrects access or photographs.

### API and integration requirements

There is no HTTP API. Do not add schemas, routes, OpenAPI entries, CORS changes or frontend calls.
The command is the sole entry point and its JSON plus process exit code is its operational
interface.

The service must not trust the command for concurrency correctness: it validates expected state and
replay payload under the database lock. The command validates representation and confirmation early
for operator feedback. RF-37 remains the exclusive physical-erasure integration; RF-21 observes the
ordinary disappearance of deleted open votes.

### Security and privacy

- Deployment access, not an application-provided credential, authorizes execution.
- The configured operator label is bounded and persisted only for accountability. It must never be
  sourced from normal users or used as proof of authentication.
- No secret or authority value is sent to or bundled in the frontend. No administrative value is
  placed in URLs or browser history because there is no browser/API flow.
- Command examples must avoid inline environment-secret assignment. Existing database credentials
  remain server runtime configuration and are never printed.
- Double UUID confirmation, explicit expected state and caller-owned operation identity protect
  against wrong-target execution and ambiguous lost responses.
- Generic unavailable/conflict output avoids disclosing content or owner information.
- Logs and audit store only the accepted allowlist; no unnecessary user content or visual evidence
  survives.
- The operation is irreversible and has no hidden restoration path.

## Implementation sequence

1. Add the removal reason/model and additive Alembic revision with constraints, no backfill and
   downgrade refusal after use; cover fresh/upgrade/downgrade behavior.
2. Add command-only operator-label parsing/validation without making ordinary API startup depend on
   the variable; document/pass the backend environment value without frontend exposure.
3. Implement the removal service with row lock, consistency checks, global operation collision
   detection, exact replay and typed sanitized outcome/errors.
4. Integrate RF-37 marking, vote deletion, terminal sanitization, immutable audit insert and
   `removed` transition into one commit. Prove rollback on every injected pre-commit failure.
5. Implement the thin non-interactive command, canonical input/confirmation validation, JSON output
   and exit codes 0/2/3/4/5.
6. Add SQLite/service/command/access/history/RF-37 tests, including historical removed rows and
   inconsistent open-result data.
7. Add disposable PostgreSQL races for vote, finalization, author deletion and same/different
   removal operations, plus transaction failure/retry evidence.
8. Add the restricted operator runbook and verify no credential, route, frontend environment or
   browser-visible surface was introduced.
9. Run migration matrices, complete backend/frontend quality suites, Compose build and isolated
   built-stack removal/storage-failure/restart/reconciliation smoke.
10. Review the final diff against every exclusion and record completion evidence without changing
    Trello, deploying or operating on production data.

## Validation strategy

### Automated tests

- CLI/config: canonical and malformed UUIDs, mismatched confirmation, fixed expected state,
  supported/unsupported reasons, missing/blank/oversized/malformed operator label, JSON schema and
  every exit code. Assert ordinary API settings/startup do not require the operator label.
- Service happy path on Public and Private open consultations with minimum and maximum options:
  audit fields, one timestamp, all votes deleted, no outcomes created, link deactivated, all
  source-session images marked, content sanitized and state `removed` in one commit.
- Replay: identical target/operation/operator/reason returns `replay` without changing timestamp,
  counts or RF-37 records; changed reason/operator/operation/target conflicts; global operation UUID
  reuse on another target conflicts cleanly.
- Terminal/historical handling: missing is unavailable; finalized, author-deleted and mismatched
  removed are conflicts; historical removed without audit is not synthesized or replayed; open row
  carrying finalization/outcome evidence fails and rolls back.
- Rollback/faults: RF-37 precondition failure, audit insert/flush failure, commit failure and command
  exception leave state, votes, content, link and media markers unchanged and produce exit 5 without
  sensitive output.
- Access/history: owner, public reader, valid/stale Private link, photo and vote all fail immediately
  after commit; feed/owner lists omit the row; affected open RF-21 rows disappear; unrelated votes,
  consultations and histories remain.
- RF-37: total and partial storage failures after removal keep access denied and audit immutable;
  repeated/startup/manual reconciliation verifies absence and clears only the intended visual
  ledger.
- PostgreSQL concurrency: removal versus vote, finalization and open author deletion in both winner
  orders; identical double removal; differing operation/reason removal; lock wait and connection
  failure. Assert first-commit-wins and no orphan audit/outcome/vote/media state.
- Migration: fresh head, populated 0009 to head, historical removed preservation without backfill,
  constraints on reason/previous state/operator/operation, empty downgrade/upgrade and refusal after
  a persisted removal.
- Regression: complete backend/frontend suites, access policy, cleanup, finalization, deletion,
  participation and existing PostgreSQL tests remain green. Assert no FastAPI/OpenAPI or frontend
  admin surface/config reference exists.

### Manual and built-stack validation

- Use a uniquely named disposable Compose project and disposable database/photo volumes only.
- Configure a harmless test operator label in backend environment. Create two accounts and real
  Public and Private open consultations with photographs and votes.
- Invoke the built backend command with exact double confirmation and a preserved operation UUID.
  Verify exit 0 and sanitized JSON, then verify feed/detail/photo/link/vote denial and RF-21 row
  disappearance through normal product clients.
- Repeat exactly and verify replay exit 0. Change one payload field and verify exit 4 without state
  change. Exercise malformed confirmation/config and verify exit 2; unknown target exit 3.
- Race removal against a vote and terminal operation using disposable PostgreSQL and prove the two
  valid winner orders rather than relying on SQLite scheduling.
- Inject physical deletion failure, prove removal remains successful and inaccessible, run the
  existing cleanup command separately, restart and prove convergence/verified absence without
  touching unrelated open media.
- Inspect OpenAPI, frontend source/build output, browser-visible configuration and logs to prove no
  admin route or credential was exposed. Inspect structured output for forbidden content/secrets.
- Stop and remove only the disposable project's services, networks and volumes after recording
  evidence. Never run removal, cleanup, downgrade or volume deletion against ordinary/production
  data during validation.

### Commands

Use the repository's existing environments and exact quality commands:

```powershell
Set-Location backend
..\.venv\Scripts\python -m ruff check app tests
..\.venv\Scripts\python -m ruff format --check app tests
..\.venv\Scripts\python -m mypy app
..\.venv\Scripts\python -m pytest

Set-Location ..\frontend
npm test -- --run
npm run format:check
npm run lint
npm run typecheck
npm run build
npm audit --audit-level=high

Set-Location ..
docker compose config --quiet
docker compose build backend frontend
```

Run live PostgreSQL migration and concurrency suites with a disposable `TEST_DATABASE_URL`. Use a
unique disposable Compose project/override for built-stack smoke. The implementation must document
the exact final removal invocation after defining its parser; use `python -m app.cleanup` only as a
separate follow-up inside that disposable backend. Do not invent or exercise a public endpoint.

## Acceptance criteria

- [ ] A deployment-authorized operator can remove one open consultation only through the backend
      command using exact double UUID confirmation, `expected_state=open`, a caller operation UUID
      and an allowed controlled reason.
- [ ] Missing/invalid operator configuration or command input fails before mutation with exit 2,
      and no ordinary API/frontend startup depends on that operational label.
- [ ] First success atomically persists the minimal immutable audit row, deletes raw votes, creates
      no outcome/tombstone, marks the complete RF-37 session, sanitizes content, revokes Private
      access and commits `removed` once.
- [ ] The terminal commit immediately removes every feed/detail/photo/link/vote access path and the
      corresponding open RF-21 participation row, even while physical deletion is pending/failing.
- [ ] Exact replay succeeds without repeated side effects; mismatched replay, cross-target operation
      reuse and all other terminal targets conflict without mutation.
- [ ] Voting, finalization, author deletion and competing removals obey consultation-row locking and
      first-commit-wins on real PostgreSQL with no priority or mixed terminal state.
- [ ] RF-37 separately retries partial physical failures, verifies exact absence and removes the
      visual ledger without changing successful removal or unrelated media.
- [ ] Historical `removed` rows receive no fabricated audit data; finalized outcomes are never
      targeted, preserved, deleted or reinterpreted by this operation.
- [ ] Structured output and logs have stable exits and reveal no content, credentials, tokens,
      database URL, storage keys, image data or vote choices.
- [ ] No FastAPI route, OpenAPI operation, frontend code, browser value, administrator role,
      suspension/report/case/notification/restoration functionality or general admin abstraction is
      introduced.
- [ ] Additive migration, downgrade refusal after use, full local suites, disposable PostgreSQL
      tests, Compose build and isolated failure/restart smoke all pass.
- [ ] Restricted documentation explains irreversible use, safe retry, cleanup separation and
      escalation without recommending direct database edits.

## Dependencies and ordering

- RF-13 author deletion is complete and supplies one competing terminal writer.
- RF-19/RF-20 finalization is complete and supplies the outcome boundary and another competing
  terminal writer.
- RF-21 participation history is complete; its open-vote disappearance contract must be preserved.
- RF-37 media protection/erasure is complete and is a mandatory reused seam, not duplicated work.
- DEC-033 and DEC-041 define locking, terminal precedence and database-first erasure.
- DEC-046 defines every RF-32 choice in this plan.
- RF-30, RF-31 and RF-42 are not prerequisites and must not be pulled into implementation. Future
  work may consume the bounded audit reason but cannot change this plan's scope implicitly.

## Risks and mitigations

- **Wrong consultation removed:** exact canonical UUID entered twice, explicit `open` expectation,
  caller-preserved operation identity and no fuzzy/bulk lookup.
- **Operational access is shared or misattributed:** per-operator deployment configuration and host
  access governance are deployment responsibilities; the bounded label records attribution without
  pretending to be authentication.
- **Lost response after commit:** caller-owned operation UUID and exact replay recover the result
  without rerunning side effects.
- **Race produces mixed state:** consultation `FOR UPDATE`, under-lock revalidation, database
  constraints and real-PostgreSQL race tests.
- **Audit collision or tampering:** one-to-one target key, globally unique operation ID, immutable
  application surface, controlled reason and downgrade refusal after use.
- **Finalized outcomes accidentally erased:** open-only under-lock check and explicit consistency
  failure if result records exist.
- **Filesystem failure mistaken for product failure:** commit is success; RF-37 cleanup has a
  separate command, reports and retry lifecycle.
- **Sensitive data retained or logged:** controlled reason only, no free text/content copies,
  allowlisted JSON/log fields and negative-output tests.
- **Admin capability leaks publicly:** no HTTP/frontend surface; backend-only environment and bundle,
  OpenAPI and log inspection.
- **Historical removed rows imply false provenance:** no migration backfill and no replay without an
  exact new audit row.

## Harness handoff notes

- Begin from `main` only after confirming the worktree contains the approved documentation changes
  expected by the coordinator and no unrelated user modifications. Do not discard those documents.
- Read `AGENTS.md`, all mandatory context, this plan, RF-32 grooming and the approved RF-13,
  RF-19/RF-20, RF-21 and RF-37 plans/reviews before editing.
- The existing test helper that writes `removed` is not production code. Replace/extend fixtures as
  necessary to exercise the real service, but preserve explicit historical-row coverage.
- Do not launch another agent or read the Codex-only harness runbook.
- Use only disposable PostgreSQL/Compose resources for destructive validation. Never target
  production/ordinary data or delete broad/local volumes.
- Do not commit, push, deploy or mutate Trello unless the product owner separately requests it.
- If the plan conflicts with current code/decisions or a material new policy choice appears, stop
  and report it rather than expanding scope.

## Resolved grooming decisions

- Q1A: deployment/host access is authority; server-side `REMOVAL_OPERATOR_ID` is attribution only.
- Q2A: restricted backend command only; no API or frontend.
- Q3A: open consultations only; finalized/deleted/nonmatching removed targets conflict.
- Q4A: one immutable minimal removal/audit row with global operation identity.
- Q5A: controlled reason code only; no free text.
- Q6A: double target UUID, explicit open state, caller operation UUID and exact replay.
- Q7A: database commit is success; RF-37 cleanup remains separate and retryable.
- Q8A: sanitized structured output/stable exits; product users receive generic unavailability only.

## Remaining questions

None
