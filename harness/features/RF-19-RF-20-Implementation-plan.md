# RF-19/RF-20 - Finalize a consultation and declare the final choice - Implementation Plan

## Status

`Ready for implementation`

The product owner confirmed every coordinated grooming recommendation (`Q1A` through `Q14A`) and
explicitly approved plan finalisation and harness launch on 2026-10-20. RF-19 and RF-20 retain
independent ticket traceability but form one indivisible product operation, transaction,
implementation and validation contract.

## Source tickets

- Trello title: `RF-19 · Finalizar una consulta`
- Trello URL: https://trello.com/c/cPkS0GiV/20-rf-19-finalizar-una-consulta
- Trello list at intake: `Próximo · completar el MVP`
- Snapshot captured on: 2026-10-20
- Grooming notes: `harness/grooming/RF-19-grooming.md`
- Trello title: `RF-20 · Declarar la elección final`
- Trello URL: https://trello.com/c/iud9aWtV/21-rf-20-declarar-la-elecci%C3%B3n-final
- Trello list at intake: `Próximo · completar el MVP`
- Snapshot captured on: 2026-10-20
- Grooming notes: `harness/grooming/RF-20-grooming.md`

## Objective

Allow the authenticated author to end an open consultation by declaring one, several or no photo
in one accessible confirmation and one atomic database operation. The winning commit must freeze
the valid votes, create definitive photo-free aggregate results and minimal private participant
outcomes, revoke every content/link/photo read, sanitize prohibited data and schedule RF-37 durable
physical erasure.

The declaration is the author's decision, not an objective assessment, majority requirement or
proof that a photo was published elsewhere. Finalization is terminal and irreversible.

## Context and current behaviour

- `ConsultationLifecycle` defines `open`, `finalized`, `deleted` and `removed`. RF-11 requires every
  terminal consumer to lock and re-read the consultation, write all database side effects and
  commit once. First terminal commit wins without priority among finalization, deletion and removal.
- `Vote` stores one immutable stable `ConsultationPhoto` choice per account and consultation.
  `vote_service.submit_vote` locks the same consultation row before re-authorizing and inserting.
- `ConsultationPhoto.id` and `ordinal` already survive RF-37 erasure. After verified absence,
  `image_id` is detached and `media_deleted_at` remains as the non-visual completion marker.
- RF-18 calculates open counts live from raw votes. No final snapshot, declaration or participant
  outcome currently exists.
- `mark_media_for_erasure` marks every object in the unique consumed source session while the caller
  owns the terminal transaction. `sanitize_terminal_content` removes question, context, audience,
  link capability and publication fingerprint after permitted replacements exist. Physical deletion
  is startup/hourly/manual, durable, retryable and post-commit.
- RF-12 provides Open/Finalized author lists and owner detail. Open detail shows photos and live
  counts. Finalized detail currently shows only reference, state and publication date.
- RF-13 open deletion discards votes without outcomes. Later deletion of a finalized consultation
  preserves `state=finalized` and future DEC-023 outcome data while hiding it from author lists.
- Protected detail, media, vote and link reads reload current state. Terminal states are generic
  unavailable. Private reads use `Cache-Control: private, no-store`; bytes already delivered before
  terminal commit cannot be remotely recalled.
- Current migration head is `20261020_0007_author_deletion.py`. Existing seeded terminal rows may
  predate the outcome contract and must not receive fabricated declarations or results.

Binding decisions include DEC-017–023, DEC-028–033 and DEC-035–044. User-facing copy remains English.

## Scope

### In scope

- One author-only atomic finalization/declaration service and HTTP operation.
- Explicit tagged one/several/none declaration with stable option identifiers.
- One immutable finalization header, declared-option relation, definitive count for every stable
  option, total denominator and one minimal outcome per valid voter.
- `Matched`, `Not matched` and `No choice` semantics exactly as defined below.
- Raw-vote replacement and deletion in the winning transaction.
- Immediate database revocation, link deactivation, terminal sanitization and RF-37 scheduling.
- Exact retry identity, expected-state validation and safe conflict/unavailable handling.
- Accessible author confirmation, error recovery and photo-free finalized list/detail results.
- Additive migration, honest compatibility for pre-contract finalized rows, sanitized observability
  and the complete validation matrix.

### Out of scope

- Automatic/time-based finalization, duration, vote threshold or scheduled closure.
- Reopening, editing or replacing a finalized declaration.
- Separate close and declaration actions, vote changes or vote explanations/comments.
- Participant aggregates, public results or the RF-21 participant-history screen.
- Percentages, winners, ranking, reputation, expertise or predictive metrics.
- Notifications, social-network publication or proof of external publication.
- Public reporting/moderation/admin UI or implementation of RF-32 administrator authority.
- Image/text archive, thumbnails, trash, recovery, deletion buffer or model-training retention.
- Account deletion/anonymization implementation, broad routing changes, native project generation,
  deployment or Trello changes.

## User experience

### Entry and selection

- Show `Finalize consultation` only on the authenticated author's open consultation detail, where
  the real ordered photographs and live counts are already visible. Do not put a destructive
  finalization shortcut on My consultations list rows.
- Open one accessible modal/dialog. Let the author select multiple photos with labelled checkboxes
  and choose an explicit mutually exclusive `Choose none` option. Switching to none clears selected
  photos; selecting a photo clears none.
- The dialog must state that finalization is permanent, immediately stops new votes and access,
  removes all photographs including for the author, and cannot be undone. Counts may change until
  the final commit; there is no minimum vote requirement.
- A review step in the same dialog summarizes `Photo N`, multiple selected photo numbers, or
  `No choice`. It must never describe majority agreement, winner or objective correctness.
- Provide explicit Cancel and Finalize actions, safe initial focus, focus trap and restoration,
  Escape support before submission, labelled/described semantics, keyboard operation, screen-reader
  announcements, duplicate-submit protection and responsive mobile/zoom/safe-area layout.

### Pending, failure and recovery

- Preserve the current selection and operation ID after every known pre-commit/retryable failure.
- A failed request with a known non-commit response remains retryable. For an ambiguous network
  outcome, retry the identical operation ID/payload and/or fetch authoritative owner detail.
- On conflict, close or reset the stale confirmation as appropriate, reload authoritative state and
  explain that the consultation changed. Never silently reinterpret a deletion/removal/finalization.
- Session loss returns through the existing authentication handling without exposing data.
- A PostgreSQL failure before commit leaves the consultation open and all previous votes/content
  intact. A storage failure after commit does not change success and exposes no cleanup progress.

### Success and finalized presentation

- After commit, immediately unmount the photo-bearing view, revoke client object URLs, switch to the
  Finalized tab/detail, refetch authoritatively and announce a transient success.
- Finalized list row shows `Finalized`, publication and finalization dates, total votes and either
  `Selected Photo N[, ...]` or `No choice`.
- Finalized detail shows those values and every stable `Photo N` with its definitive count and
  selected marker. It shows no thumbnail, question, context, audience, percentage or link.
- Keep the existing finalized `Delete consultation` action and its RF-13 warning. A later author
  deletion hides the row but may preserve DEC-023 private records.
- A legacy finalized row without the new finalization record shows an honest
  `Final result unavailable` summary, never fabricated zero counts or `No choice`.

## Functional requirements

### FR-1 - Explicit declaration

Use a strict tagged request union:

- `kind: selected` requires 1..N unique stable consultation option IDs;
- `kind: none` permits and stores no option IDs.

The declaration field is required. Reject missing, extra, duplicate, malformed, foreign or detached
from-the-consultation option references. The author may select every option. Do not require the
majority option or any votes.

### FR-2 - Definitive snapshot

At the locked transaction boundary, store one immutable vote count for every stable option in
ordinal order, including zeroes, plus a total denominator equal to the sum of all option counts.
Ties and selection contrary to the majority are ordinary valid cases. Do not add percentages.

### FR-3 - Participant outcomes

Create exactly one account-linked private outcome for every valid committed raw vote:

- `Matched`: the voted option belongs to the declared selected set;
- `Not matched`: at least one option was declared and the voted option is outside that set;
- `No choice`: the author explicitly declared none.

Create no row for an account that did not vote. Outcome rows must not retain the raw selected option.
Use a constrained enum/check and a unique consultation/participant key. Design the account FK so
future RF-34 can remove or anonymize it, but do not implement account deletion here.

### FR-4 - Atomic transformation and minimization

Within one transaction and under the consultation row lock:

1. authenticate and prove owner authority;
2. validate `expected_state=open`, operation identity and declaration against latest stable options;
3. aggregate all committed votes into the definitive snapshot;
4. write the finalization header, declared selections, all option counts and participant outcomes;
5. prove count, option and participant invariants;
6. delete all raw `Vote` rows for the consultation;
7. call RF-37 transaction-local media marking;
8. sanitize terminal content/link capability;
9. write `state=finalized` and commit once.

If any vote cannot map exactly to a valid stable option/account or the snapshot/outcome counts do not
reconcile, roll back everything, leave the consultation open and surface a sanitized operational
error for restricted repair. Never skip an anomalous vote or retain raw choices as fallback.

### FR-5 - Retry identity

Require a client-generated UUID `operation_id`, `expected_state: open` and the declaration. Persist
the operation ID and a canonical payload fingerprint with the finalization header.

- Same operation ID and canonical payload against the committed finalization is idempotent success.
- Same operation ID with another payload is conflict.
- A new operation ID against any terminal state is conflict or generic unavailable according to the
  safe target rules; matching selection alone is not retry proof.
- Do not introduce a generic request ledger or general idempotency framework.

### FR-6 - First commit wins

Use the same consultation `FOR UPDATE` lock as vote and RF-13:

- vote commits first: include it;
- finalization commits first: later vote re-authorizes and fails;
- two finalizations: only the winning operation may write; exact replay rules apply afterward;
- open deletion/removal commits first: finalization changes nothing and fails safely;
- finalization commits first: an open-deletion confirmation conflicts and requires the author to
  reload and confirm RF-13's finalized-deletion warning;
- no operation receives priority and opening a dialog never freezes voting.

### FR-7 - Surviving allowlist

After commit and RF-37 convergence, retain only:

- consultation and owner identifiers, canonical state, publication/finalization dates and possible
  later author-deletion marker;
- stable option identifiers/order and media-deletion completion marker;
- finalization operation identity/fingerprint, declaration, per-option counts and denominator;
- participant account plus `Matched|Not matched|No choice` outcome;
- only RF-37 retry metadata while work is pending/failed.

Do not retain question/context, audience/link generation/activity, publication fingerprint,
source-session/upload/image/storage metadata or raw per-voter photo choice. Do not log them.

### FR-8 - Revocation and storage failure

The database commit is product success and immediately denies all new recipient/author photo,
detail, vote, link and feed reads. An authorization begun before commit may finish; downloaded bytes
cannot be recalled. Physical deletion remains post-commit RF-37 maintenance. Total or partial storage
failure remains observable/retryable to operators, never reopens access and never changes the
successful API/UI result.

### FR-9 - Owner API and safe responses

Add `POST /api/my-consultations/{consultation_id}/finalize` with signed-session authentication,
server-derived ownership, trusted-Origin enforcement, strict extra-field rejection and private
no-store response headers.

- unknown, foreign, removed or author-deleted target: generic `404 consultation_unavailable`;
- stale expected state, another terminal action or mismatched replay: `409 consultation_conflict`;
- semantically invalid declared option for an authorized open consultation: field-safe `422`;
- pre-commit infrastructure failure: sanitized 5xx and rollback;
- first success and exact replay: the same minimal finalized summary, with no removed content,
  participant identities, cleanup internals or link/storage data.

Do not accept owner IDs, Private-link capabilities or client lifecycle labels as authority.

### FR-10 - Author projections

Extend the separate owner-only finalized list/detail variants with finalization date, total count,
declaration by stable ordinal and all per-option final counts. Preserve stable pagination and
`author_deleted_at IS NULL` filtering. Never reuse the photo-bearing open detail or expose these
fields on feed, reader, direct-link, media or vote responses.

### FR-11 - Compatibility

Use an additive Alembic migration. Preserve all open/voted data. Do not backfill or infer outcomes
for existing finalized/deleted/removed rows. New service finalizations must always create the full
record atomically. Legacy finalized rows remain readable as result-unavailable and removable through
RF-13. Add explicit downgrade refusal after any irreversible finalization/outcome/minimization use.

### FR-12 - Observability

Emit sanitized structured events/counters for `first`, `replay`, `conflict` and `error`, total votes,
selected-option count, counts per outcome category and RF-37 images marked. Never log question,
context, Private token, storage key, image data, declared option IDs, operation payload or individual
voter/choice. Existing RF-37 pending/failed/overdue observability remains authoritative for storage.

## Technical approach

Create a focused service such as `backend/app/consultation_finalization_service.py`; keep the FastAPI
handler thin. Use normalized tables/models for the finalization header, declared selections,
per-option snapshots and participant outcomes. Prefer database uniqueness, composite foreign keys
and checks that prove every referenced option belongs to the consultation. Do not store JSON as the
primary integrity boundary.

The service owns the transaction and commit, as RF-13 does. Reuse `mark_media_for_erasure` and
`sanitize_terminal_content`; do not duplicate filesystem logic. Ensure RF-13 finalized deletion
removes no new DEC-023 rows. Extend owner projections rather than weakening open-only protected
reads.

### Affected areas

- Frontend: `OwnerConsultationDetail.tsx`, `MyConsultations.tsx`, `consultationApi.ts`, focused hooks,
  new accessible finalization dialog/components, CSS and tests.
- Backend/API: `api/consultations.py`, `schemas.py`, focused finalization service, owner result/list
  projections and sanitized errors/logging.
- Domain/data model: `models.py`, one new Alembic revision, stable options, finalization/snapshot/
  outcome constraints and RF-13 preservation.
- Storage/background: existing `photo_erasure_service.py`, startup/hourly/manual cleanup; no worker.
- Security: signed session, Origin check, request-time state authorization, no-store responses and
  generic unavailable semantics.
- Documentation: grooming status, project state and implementation review after execution.

### Data and migration requirements

- One-to-one finalization header keyed by consultation with operation UUID, canonical payload hash,
  finalization timestamp and non-negative total count.
- Declared-option join constrained to options from the same consultation; zero rows means only the
  explicit `none` declaration, never missing data.
- One count row per stable option, unique per consultation/option, non-negative.
- One participant outcome per consultation/voter, constrained enum and no raw option field.
- Cross-table/service invariants must prevent partially populated new finalizations. Use deferred
  PostgreSQL constraints/triggers only when ordinary keys/checks plus atomic service code cannot
  express an important invariant; keep SQLite-independent unit seams where useful but validate real
  PostgreSQL behavior.
- Preserve legacy terminal rows without a header. Downgrade must detect populated new records or
  irreversible sanitization and refuse rather than pretend to restore raw votes/images/text.

### Security and privacy

- Author identity comes only from the signed cookie and locked `owner_id` comparison.
- Validate syntax before service entry, then validate semantic option membership only after safe
  authorization. Do not reveal consultation existence through foreign option IDs.
- Every terminal read remains denied outside the separate owner projection. Participants receive no
  new surface in this increment.
- Keep every media object private. No public URL, CDN, service worker cache or thumbnail archive.
- Minimize logs and retained data exactly to FR-7/FR-12.

## Implementation sequence

1. Add domain enums/value objects and the additive migration/models with constraints and legacy
   compatibility/downgrade guards.
2. Implement canonical request fingerprinting and the finalization service with lock, authorization,
   snapshot/outcome transformation, invariants, vote removal, RF-37 marking, sanitization and commit.
3. Add unit and real-PostgreSQL service/concurrency/storage-fault tests before exposing HTTP.
4. Add strict schemas and the owner-only finalization route/error/Origin/no-store contract.
5. Extend owner finalized list/detail projections, preserving legacy-result-unavailable and RF-13
   author-deletion filtering.
6. Add the frontend API contract and accessible selection/review dialog with stable operation ID,
   duplicate prevention and failure reconciliation.
7. Integrate success/conflict/session-loss navigation and photo-free final list/detail rendering.
8. Add frontend accessibility/responsive/regression tests and sanitized observability assertions.
9. Run the full local, PostgreSQL, migration, Docker, restart/storage/recovery validation matrix and
   record evidence without claiming product-owner visual validation.

## Validation strategy

### Automated tests

- Declaration: one, several, all and none; duplicates, empty selected, IDs from another consultation,
  malformed IDs and extra fields.
- Snapshot/outcomes: zero votes, zero-vote options, ties, majority disagreement, all three outcome
  meanings, denominator and category reconciliation, non-voter absence and raw-vote removal.
- Atomic rollback for invalid/anomalous vote, failed invariant, PostgreSQL failure and RF-37 marking
  failure; no partial finalization, sanitized content or outcome.
- Idempotency: first, exact replay, same ID/different payload, different ID/same selection and stale
  state. Prove canonical ordering of a selected set.
- API/session/Origin/ownership/generic denial, strict validation, response minimization and no-store.
- Owner list/detail new and legacy projections; no exposure through reader/feed/link/vote/media APIs.
- Frontend select/multi/none transitions, review/cancel, pending/double click, known/ambiguous failure,
  retry, conflict reload, session loss, success navigation and object-URL cleanup.
- Accessibility: dialog name/description, focus entry/trap/restore, Escape, keyboard checkboxes,
  live-region announcements and responsive CSS regression.
- Real PostgreSQL: vote/finalize both orders, two finalizers, open delete/finalize both orders,
  seeded restricted removal/finalize both orders, RF-37 maintenance concurrency and constraint proof.
- Migration with open/voted/legacy finalized/deleted/removed rows; no fabricated backfill and
  downgrade refusal after irreversible use.
- RF-37 total/partial storage failures, restart/hourly/manual retry, verified absence, option survival,
  finalized RF-13 deletion and supported non-resurrecting recovery.

### Manual validation

- Use an isolated Compose project/database/photo volume. Do not modify retained RF-13/RF-37 manual
  stacks or ordinary data.
- Exercise author finalization with one, multiple and none using a separate voter account; verify
  immediate voter/link/media denial and correct photo-free author summaries.
- Verify narrow/mobile layout, keyboard and screen-reader flow. Subjective visual approval remains
  the product owner's gate under DEC-034.
- Simulate backend restart and storage failure/recovery; confirm finalization stays successful and
  cleanup converges without byte resurrection.

### Commands

From repository root:

```powershell
.\.venv\Scripts\python -m pytest backend\tests
.\.venv\Scripts\python -m ruff check backend
.\.venv\Scripts\python -m ruff format --check backend
.\.venv\Scripts\python -m mypy backend\app
```

Run every PostgreSQL-dependent test against an isolated Alembic-upgraded database using
`TEST_DATABASE_URL`; never point it at ordinary project data.

From `frontend`:

```powershell
npm test
npm run format:check
npm run lint
npm run typecheck
npm run build
npm audit --audit-level=high
```

From repository root:

```powershell
docker compose config --quiet
docker compose build backend frontend
```

Use a unique Compose project and volumes for migration/startup/restart/storage/recovery proof.

## Acceptance criteria

- [ ] Only the authenticated author can finalize an open consultation.
- [ ] One, several, all or explicitly none can be declared; no vote threshold or majority rule exists.
- [ ] Declaration, definitive snapshot, participant outcomes, raw-vote removal, logical revocation,
      sanitization and `finalized` commit atomically once.
- [ ] `Matched`, `Not matched` and `No choice` follow FR-3; non-voters receive no outcome.
- [ ] Every option has a final count including zeroes, and the denominator reconciles exactly.
- [ ] First lock/commit wins for voting/finalization/deletion/removal; losers cannot reinterpret state.
- [ ] Exact retries are successful only with matching operation identity and canonical payload.
- [ ] The commit immediately denies every new recipient/author content, media, link and vote read.
- [ ] Storage failure after commit is durable/retryable and never reopens access or changes success.
- [ ] After convergence no image, text, link/storage/upload metadata or raw vote choice remains beyond
      the explicit DEC-023/RF-37 allowlist.
- [ ] The accessible UI provides one irreversible selection/review confirmation, safe pending/error/
      conflict/recovery behavior and authoritative navigation.
- [ ] Finalized owner views show the minimum photo-free declared result and counts; legacy rows are
      honestly result-unavailable and no other audience receives aggregates.
- [ ] RF-13 later finalized deletion preserves the permitted outcomes while hiding author content.
- [ ] Logs contain only sanitized classifications and aggregate counters.
- [ ] Unit, API, frontend, migration, real-PostgreSQL race, storage, Docker, restart and recovery
      evidence pass; remaining product-owner visual validation is reported honestly.
- [ ] No RF-21 screen, RF-32 authority, account deletion, notification, reputation, archive,
      deployment, commit, push or Trello mutation is included.

## Dependencies and ordering

- Depends on RF-11 lifecycle/locking, RF-12 author recovery, RF-13 later finalized deletion, RF-16
  votes, RF-18 open counts, RF-26 link revocation and RF-37 erasure/minimization.
- RF-21 later consumes only the participant outcome rows created here.
- Restricted RF-32 removal must later preserve or remove finalized outcomes according to DEC-023 and
  use the same RF-37 boundary before beta.
- RF-34 later owns participant account-link removal/anonymization.

## Risks and mitigations

- **Partial terminal result:** one service-owned transaction and invariant checks before one commit.
- **Late vote:** common consultation row lock and real PostgreSQL race tests.
- **False retry success:** operation UUID plus canonical payload fingerprint.
- **Over-retention:** explicit allowlist, normalized replacement records and raw-vote deletion.
- **Fabricated legacy history:** no backfill; honest unavailable result.
- **Photo resurrection/storage failure:** database-first denial plus existing RF-37 retry/recovery.
- **Information leak:** owner-only projections, generic foreign/terminal denial and no-store headers.
- **UI accidental finalization:** explicit selection/review, accessible destructive dialog and duplicate
  protection.
- **Plan split drift:** one coordinated RF-19/RF-20 implementation contract with both traces.

## Harness handoff notes

- Read `AGENTS.md`, every `harness/context` document, this complete plan and every dependency plan
  before editing. Repository state, not Trello or conversation history, is authority.
- The coordinator-created grooming files, this plan and project/decision updates are intentional
  uncommitted worktree changes. Preserve and update them; do not overwrite or revert them.
- Implement only this contract. If current code or constraints conflict materially, stop and report
  rather than retaining forbidden data or weakening concurrency/privacy.
- Do not commit, push, deploy, mutate Trello, operate on ordinary volumes, generate native projects
  or launch other agents. Keep code/tests/docs/final report in English.
- Do not claim subjective visual approval; DEC-034 leaves it to the product owner.

## Resolved grooming decisions

- `Q1A`: explicit tagged selected/none declaration and mutually exclusive accessible UI.
- `Q2A`: normalized finalization, declaration, per-option snapshot and denominator.
- `Q3A`: voter-only `Matched|Not matched|No choice`; non-voters have no row.
- `Q4A`: replace/delete raw votes only after invariant proof; anomalies roll back.
- `Q5A`: exact DEC-023 allowlist plus dedicated finalization date.
- `Q6A`: ordered one-transaction transformation; database commit is success.
- `Q7A`: operation UUID, expected open state and canonical payload proof.
- `Q8A`: shared lock and first-commit-wins; no count freeze or terminal priority.
- `Q9A`: narrow owner endpoint, Origin protection and safe errors.
- `Q10A`: open-owner-detail accessible confirmation and authoritative recovery/navigation.
- `Q11A`: minimum photo-free finalized result with count-only aggregates.
- `Q12A`: honest legacy compatibility and future RF-34 account-link boundary.
- `Q13A`: request-time/no-store revocation and RF-37 post-commit failure convergence.
- `Q14A`: sanitized observability, full proof matrix and one coordinated plan.
- Product owner confirmed all choices and authorized plan finalisation/harness launch on 2026-10-20.

## Remaining questions

None
