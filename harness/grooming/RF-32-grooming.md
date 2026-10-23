# RF-32 - Restricted administrator consultation removal - Grooming

## Status

`Grooming complete - implementation plan approved`

This grooming covers only the minimum MVP exception accepted in DEC-022: a designated
administrator can irreversibly remove one consultation through a restricted operational surface.
It does not groom or implement the broad RF-32 card. On 2026-10-23 the product owner selected
option A for every question in the consolidated decision batch and explicitly requested the
implementation plan. Those choices are accepted in DEC-046.

## Trello snapshot

- Title: `RF-32 · Retirar contenido y suspender cuentas`
- URL: https://trello.com/c/jQPe9AZ6/33-rf-32-retirar-contenido-y-suspender-cuentas
- Stable short URL: https://trello.com/c/jQPe9AZ6
- Card ARI:
  `ari:cloud:trello::card/workspace/6aa9032829f8b45ead46cfdd/6aa90c099d9a3617adfc06ee`
- Board: `APP - NextPost`
- Board ARI:
  `ari:cloud:trello::board/workspace/6aa9032829f8b45ead46cfdd/6aa903892e7d7b54f23fae1b`
- List: `Después · cuentas y administración`
- List ARI:
  `ari:cloud:trello::list/workspace/6aa9032829f8b45ead46cfdd/6accc3a6392fdd58cdf0e7b8`
- State: open and not archived (`closed: false`); incomplete (`complete: false`,
  `dueComplete: false`).
- Position: `98304`
- Start date / due date: None / None
- Labels: None; no omitted labels reported.
- Members: None; the complete member read reported no next page.
- Checklists: None; the complete checklist read reported no next page.
- Comments: None; no omitted comments reported.
- Attachments: None; the complete attachment read reported no next page.
- Custom-field values: None; the complete custom-field read reported no next page.
- Last Trello activity at intake: `2026-10-12T11:35:06.159Z`.
- Available activity:
  - created by Negis on `2026-09-15T09:12:41.899Z`;
  - moved by Negis from `Después · comunidad y participación` to
    `Después · cuentas y administración` on `2026-10-12T11:35:06.112Z`;
  - the complete activity read reported no next page.
- Captured read-only on: `2026-10-23T13:49:14.2309810+02:00`.
- Intake consistency: identifier, title, configured board, current list and content agree. The broad
  card is intentionally in the later administration queue, while its DEC-022 restricted-removal
  subset remains an MVP prerequisite. No Trello mutation was performed.

### Description and acceptance criteria at intake (verbatim)

**Reorganización del backlog · 2026-10-12**

La tarjeta amplia continúa aplazada. EXCEPCIÓN de MVP ya aceptada (DEC-022): retirada manual
restringida de una consulta, sin suspensión de cuentas, bandeja ni consola. Esa parte mínima debe
groomarse y validarse con RF-37 antes de exponer fotos de usuarios reales; no queda aplazada por esta
lista.

Ubicación: Después · cuentas y administración. El repositorio es la fuente de estado y
especificaciones aceptadas. Esta organización no aprueba un plan ni lanza implementación.

---

**Descripción conservada del ticket**

**Estado:** la funcionalidad completa queda para después del primer MVP. En fase 2 solo existe una
retirada manual y restringida por el administrador, sin bandeja de denuncias, suspensión de cuentas
ni panel de moderación (DEC-020/022). Esta capacidad mínima se coordina con RF-37.

---

**Historia de usuario**

Como moderador, quiero retirar contenido y limitar cuentas abusivas para proteger a la comunidad y
la integridad de las votaciones.

**Comportamiento y criterios de aceptación**

- Puedo retirar una consulta, suspender una cuenta y revertir medidas equivocadas cuando el
  contenido todavía exista y la reversión esté permitida.
- Una consulta retirada desaparece de feeds y enlaces y deja de aceptar votos. No se puede recuperar
  contenido que ya se borró definitivamente.
- Una suspensión impide nuevas publicaciones e interacciones e invalida sesiones activas; no se
  utiliza para borrar sin revisión todo el historial de la cuenta.
- Si se confirma manipulación de votos, puedo invalidar las participaciones afectadas con motivo
  registrado, corrigiendo resultados e indicadores dependientes.
- El afectado recibe una explicación apropiada y una vía de revisión sin conocer la identidad del
  denunciante. Todas las acciones se registran y no requieren suplantar al usuario.

## Verified baseline and sources

The intake began after RF-21 was committed and pushed as `25f0826` on `main`, with
`HEAD == origin/main` and a clean worktree. RF-13, RF-19/RF-20 and RF-37 are recorded as completed
and validated. RF-21 is committed and technically validated, but the repository still accurately
records its DEC-034 product-owner visual/interaction acceptance as pending; the owner explicitly
directed this RF-32 grooming to continue after the RF-21 push.

Before analysis, the complete `AGENTS.md`, mandatory `harness/context` sequence, 2026-10-12 product
reorganization and relevant RF-13, RF-19/RF-20, RF-21 and RF-37 grooming/plans/reviews were read.
RF-30, RF-31 and RF-42 have no repository grooming or implementation plan; their exact reorganized
cards in the stored board snapshot were inspected. The live RF-32 card and all available metadata
were consumed read-only through the connected Trello source.

Current models, migrations, configuration, authentication, access policy, owner deletion,
finalization, participant history, RF-37 marking/reconciliation, startup/hourly/manual maintenance,
observability and SQLite/PostgreSQL concurrency tests were inspected. Historical plans were not
treated as substitutes for current code.

## Binding accepted decisions

- The broad moderation/administration feature is deferred. The MVP exception is manual restricted
  removal of one consultation only (DEC-020/022).
- The persisted lifecycle remains exactly `open`, `finalized`, `deleted`, `removed`; `Unavailable`
  is an external result, not another state (DEC-033).
- Votes and every terminal writer serialize by locking the same consultation row. There is no
  priority: first commit wins (DEC-033/041/044).
- Administrator removal must consume the exact RF-37 database-first revocation and verified
  physical-erasure path. It cannot create a parallel purge (DEC-041).
- A removal before finalization deletes raw votes and creates no declaration, aggregate or
  participant outcome (DEC-021/023/041/045).
- The terminal commit revokes every new detail, feed, link, photo, vote and result authorization.
  A read authorized before commit may finish; bytes already saved outside NextPost cannot be
  recalled (DEC-029/041).
- Fallible filesystem deletion occurs after commit and retries through startup, hourly and
  restricted manual maintenance. Failure never reopens access or reverses product success.
- After convergence, only the DEC-023/041 allowlist may remain. There is no retained moderation
  image/evidence copy.
- RF-21 is a narrow consumer. It shows a stored semantic outcome while it exists, but RF-32 must
  explicitly decide any administrative preservation/replacement/erasure rule rather than making
  RF-21 infer it (DEC-045).

## Current implementation findings

### Authentication, authorization and configuration

- Ordinary product authentication is a signed `HttpOnly` session cookie containing an account ID.
  `Account` has no role, administrator flag, suspension state or server-side session ledger.
- Reserved aliases such as `admin` are input validation only and confer no authority.
- Current mutations use signed-session ownership plus trusted-Origin protection. A Public audience,
  Private link, consultation UUID or former ownership does not grant another mutation.
- Configuration is startup-loaded from environment variables. Server-only secrets currently cover
  sessions and Private-link derivation; limits and cleanup intervals are also environment-driven.
- No administrator credential, operator identity, role management, operational API network, or
  audit sink exists. Adding a normal account role would cross into RF-40 and expose a new
  application authorization model.

### Lifecycle, deletion, finalization and removal

- RF-13 supplies real voluntary deletion in `consultation_deletion_service.py`. An open deletion
  locks the row, calls RF-37, deletes every vote, sanitizes content, writes `deleted` plus
  `author_deleted_at` and commits once. A finalized author withdrawal preserves `finalized` and its
  minimum outcome records.
- RF-19/RF-20 supplies real finalization in `consultation_finalization_service.py`. It locks the same
  row, writes the declaration/snapshot/outcomes, deletes raw votes, calls RF-37, sanitizes, writes
  `finalized` and commits once.
- There is no production administrator-removal service, schema, command or API. The only removal
  writer found is `_remove` inside `test_finalization_postgres.py`; it merely changes the lifecycle
  for a race fixture. It does not authorize an operator, delete votes, call RF-37, sanitize, record
  audit data or prove idempotency and cannot be reused as implementation evidence.
- `mark_media_for_erasure` deliberately accepts only a locked `open` consultation backed by its
  unique consumed source session. This strongly aligns the minimum new consumer with removal of an
  open consultation, while finalized content has already been sanitized and physically scheduled
  by finalization.

### Access revocation and physical deletion

- Feed, owner/reader/direct detail, media, Private link, vote read/write and live author results all
  reauthorize current database state and require `open`. A committed `removed` state therefore
  disappears or becomes the same generic unavailable response without frontend changes.
- RF-37 marks every object in the consultation's whole unique consumed source session, deactivates
  the Private capability and retains exact keys plus sanitized retry state only while pending.
- `reconcile_terminal_media` already discovers `removed` rows, verifies exact absence, detaches
  stable options and deletes the visual/upload ledger. Partial and total failures retain only the
  remaining work; malformed/anomalous state fails closed and is reported.
- Maintenance runs before API startup, hourly and through `python -m app.cleanup` under the narrow
  PostgreSQL advisory lock. Exit codes are currently `0` healthy, `1` overdue/anomalous and `2`
  busy. `/api/ready` intentionally remains independent.

### Final results and participant history

- Finalization replaces raw choices with a one-to-one header, declared stable options, count rows
  and one semantic outcome per voter. Author deletion after finalization preserves them.
- RF-21 combines current open votes and retained outcomes. If an open consultation is deleted or
  removed, deletion of its raw votes makes its history row disappear and creates no tombstone.
- An administratively removed finalized outcome is an unresolved broad-policy question. Mapping it
  to unavailable, recalculating it or deleting it would implement the deferred vote-manipulation /
  review part of RF-32. The narrowest coherent MVP avoids that product decision by accepting only an
  `open` target; if finalization wins first, removal conflicts and does nothing.

### Data, migrations and audit

- The current head is `20261021_0009_participation_history.py`. Existing schema has
  `author_deleted_at`, but no `removed_at`, operator, reason or removal operation identity.
- A lifecycle value alone cannot prove who removed a consultation, why, when, or whether a retry is
  the same operation. Application logs alone are neither transactional nor sufficient for exact
  idempotency and may have shorter retention.
- Existing historical/fixture `removed` rows have no attributable action. They must remain denied
  and recoverable by RF-37, but must not be fabricated into audited administrator actions.

## Contrast between the broad card and the accepted MVP subset

### Minimum coherent increment

- A designated operator identifies exactly one consultation by canonical UUID.
- A restricted backend operational action removes it only if the locked current state is `open`.
- The same transaction records the immutable operation identity/audit minimum, deletes every raw
  vote without outcomes, calls RF-37, sanitizes terminal content, writes `removed` and commits once.
- Commit is irreversible product success and immediately revokes access. RF-37 maintenance owns
  physical convergence.
- Exact replay is idempotent; a different operation, payload or terminal winner conflicts safely.
- The operational surface reports bounded, machine-stable results without content, capabilities,
  storage keys or secrets.

### Explicitly out of scope

- Account suspension, session invalidation or account-status changes.
- User reports, report submission, reporter identity or blocking.
- Moderation inbox, case queue, prioritization or review workflow.
- General administration console, frontend route or ordinary admin login.
- Application-managed administrator/moderator roles or role assignment.
- Visual evidence retention or any extra photo copy/archive.
- Restoring, undoing or republishing removed content.
- Removal of finalized consultations, invalidation/recalculation of final outcomes or manipulated
  vote adjudication unless the product owner explicitly chooses that expansion below.
- Notifications, appeal/review UI or disclosure of the operator identity to the author.
- Account deletion/export, general audit platform, worker/queue, deployment or Trello mutation.

## Proposed technical boundary

The recommended design is a command-only operational consumer, for example
`python -m app.remove_consultation`, available only inside the backend runtime. Access to the
deployment shell/container and its existing database configuration is the authority. A required
server-side `REMOVAL_OPERATOR_ID` supplies a bounded non-secret audit label; it is not an
authentication credential and must not be exposed through application configuration.

The command would require explicit arguments such as canonical consultation UUID, a client-created
operation UUID, `expected_state=open`, a controlled reason code, and a repeated confirmation UUID.
It would call a focused `consultation_removal_service` rather than an HTTP route or an existing
author service. It would never accept an account session, author ID, Private capability or raw
database query.

Recommended persistent data is a one-to-one immutable `consultation_removals` record:

- `consultation_id` primary/foreign key;
- globally unique `operation_id` for exact retry and cross-target reuse rejection;
- `removed_at` in UTC;
- bounded `operator_id` copied from server-side operational configuration;
- controlled `reason_code` only;
- `previous_state=open` as explicit invariant.

This table is narrower and clearer than adding general moderation/audit entities. It proves the
operation transactionally and avoids retaining free-form allegations or deleted content. The
consultation remains the natural durable target required by RF-37 and referential integrity.

Within the locked transaction the service would:

1. load the consultation with `FOR UPDATE`;
2. resolve exact replay by operation ID plus stored actor/reason/target/state;
3. require current `open`; otherwise return a bounded unavailable/conflict result;
4. insert the immutable removal record;
5. call `mark_media_for_erasure`;
6. delete all `Vote` rows and create no finalization/outcome;
7. call `sanitize_terminal_content`;
8. write `state=removed` and commit once.

No synchronous filesystem call belongs in that transaction or in the success boundary. The
existing cleanup path can be run separately when an operator needs immediate reconciliation/status.

## Security and credential-exposure verification

Under the recommended command-only design:

- no frontend component, bundle variable, browser route, cookie, local/session storage entry or
  service worker receives administrator authority;
- no HTTP operational endpoint exists to expose accidentally through Nginx, CORS, browser history,
  referrers or access logs;
- no credential appears in a URL, query string, command argument, audit row or structured log;
- the existing database connection remains server-side environment configuration;
- `REMOVAL_OPERATOR_ID` is an attribution label, not a secret and not an authorization bearer;
- operation/consultation UUIDs and controlled reason codes are non-secret bounded metadata;
- ordinary signed-session users, authors and Private-link holders have no code path into removal;
- logs exclude question/context, author email/alias, tokens, storage keys/paths, images and raw vote
  choices.

An operational API would require a separate credential lifecycle, network isolation, header-only
transport, rotation and proxy/log verification. Those controls add risk and no MVP user value while
a command is sufficient, so the API is not recommended.

## Failure, concurrency and precedence analysis

- **Vote commits first:** removal acquires the lock next, deletes that vote with every other raw
  vote and creates no outcome.
- **Removal commits first:** later vote authorization observes `removed` and fails generically.
- **Finalization commits first:** removal sees `finalized`, returns conflict and does not alter final
  records. This avoids silently implementing outcome invalidation.
- **Removal commits first:** finalization sees `removed` and is unavailable; no outcome exists.
- **Author open deletion commits first:** removal sees `deleted` and cannot reinterpret it.
- **Removal commits first:** later author deletion/finalization cannot overwrite it.
- **Two identical removals:** one first commit and one exact replay success.
- **Different operation/reason/actor after removal:** conflict; the audit record is immutable.
- **Failure before commit:** rollback leaves state, votes, media marker and audit unchanged.
- **Storage failure after commit:** access remains revoked; exact RF-37 retry data survives and the
  existing maintenance path converges later.
- **Command output lost after commit:** rerun with the same operation UUID and payload returns replay
  success without duplicate side effects.

## Migration and historical compatibility

- Add one revision after `0009`; never edit prior migrations.
- Existing open/finalized/deleted/removed rows receive no synthetic audit backfill.
- Existing `removed` rows remain terminal and RF-37-reconcilable, but are not an exact replay of a
  new command because no immutable removal record proves it.
- Add unique/check/foreign-key constraints for one removal per consultation, globally unique
  operation ID, bounded actor/reason and `previous_state=open`.
- Keep all current lifecycle, finalization, outcome, option and media constraints intact.
- Downgrade may remove the unused additive schema only. Once any removal record exists, refuse
  downgrade because neither deleted content/votes nor true attribution can be reconstructed.

## Observability and operational behavior

Recommended stdout is one sanitized structured result containing classification (`first` or
`replay`), consultation ID, operation ID, previous state, reason code, votes removed and images
marked. Stderr/logging contains bounded `conflict`, `unavailable`, `validation`, `configuration` or
`internal_error` classifications without sensitive exception text.

Recommended stable exit classes are:

- `0`: first success or exact replay;
- `2`: invalid arguments, confirmation mismatch or invalid/missing operator configuration;
- `3`: unknown/unavailable target;
- `4`: lifecycle or idempotency conflict;
- `5`: pre-commit database/internal failure.

RF-37 cleanup keeps its existing independent `0/1/2` status contract. Operator documentation must
distinguish product removal success from later cleanup health and show the supported follow-up
status command. Deployment must keep the command inside the backend operational boundary and route
existing overdue/anomaly signals to the operator alert channel before beta.

## Dependencies and conflicts

- **RF-30:** reporting remains fully deferred. No report ID, reporter, accusation text or user
  report UI is introduced. A controlled removal reason is operational audit metadata only.
- **RF-31:** inbox/review/case resolution remains deferred. The command targets an already selected
  UUID and does not provide discovery or evidence review.
- **RF-37:** mandatory implementation dependency and the only media marker/reconciliation path.
- **RF-13:** supplies the analogous consumer pattern but cannot authorize administrators or be
  called with a fake owner. Removal remains a distinct service and audit identity.
- **RF-19/RF-20:** shares lock/first-commit precedence. Finalized outcome invalidation is not
  inherited and remains outside the recommended open-only subset.
- **RF-21:** an open removed vote disappears with no tombstone. Stored finalized outcomes are not
  changed because finalized removal is outside the recommended subset.
- **RF-42:** invited beta must not begin until restricted removal is implemented, independently
  reviewed, operationally documented and validated with RF-37. This grooming does not deploy or
  distribute anything.

## Validation direction for a later approved plan

### Unit, service and SQLite/API regressions

- command parsing, exact UUID confirmation, required operator configuration and controlled reasons;
- owner/session/Private-link code cannot call the operational consumer;
- open first removal, exact replay, different operation/payload conflict and legacy removed target;
- vote deletion with no finalization/declaration/count/outcome/history tombstone;
- pre-commit rollback at each RF-37/audit/sanitization/database seam;
- generic denial/omission across feed, owner/reader/direct detail, media, link, results and votes;
- exact audit allowlist and log/output forbidden-field assertions;
- RF-37 full, partial and already-absent convergence without touching unrelated sessions.

### Real PostgreSQL and migration

- vote/removal both orders; finalization/removal both orders; author deletion/removal both orders;
- concurrent identical replay and differing operation/reason conflicts with no deadlock;
- cleanup overlap with terminal commit under existing advisory/row locks;
- fresh upgrade, `0009 -> head`, populated historical-state preservation, direct constraint checks,
  empty downgrade and downgrade refusal after first irreversible use.

### Recovery and deployment

- isolated built Compose command execution against disposable database/photo volumes;
- immediate HTTP denial after commit, injected total/partial storage failure, manual/startup/hourly
  retry, restart and verified exact absence;
- supported PostgreSQL restore with empty/current private-photo volume and pre-traffic reconciliation;
- prove the operational command is absent from frontend assets/routes and no credential is emitted in
  command lines, browser-visible config, URLs, logs or history;
- operator runbook for generating/preserving operation IDs, selecting the exact UUID, confirmation,
  exit codes, cleanup-status follow-up and escalation of anomalies.

No accessibility or visual validation is needed for the recommended command-only surface. If the
owner chooses any human web/API UI, keyboard, screen-reader, focus, zoom, mobile layout and secure
credential-entry requirements become material and must be groomed before plan finalization.

## Consolidated material decision batch

The product owner accepted `Q1A` through `Q8A` together on 2026-10-23. The alternatives remain below
to preserve the evaluated trade-offs; each recommendation is now an accepted decision.

### Q1 - What constitutes designated-administrator authority and attribution?

**Why it matters:** the product has no roles or admin sessions. Adding them would expand RF-40 and
could expose authority to ordinary application clients.

- **A (recommended): deployment/host operational access is the authority; a required server-side
  `REMOVAL_OPERATOR_ID` is copied as a non-secret audit label.** Advantages: no application role,
  login or bearer secret; clear separation from users; minimal MVP. Risks: database attribution is
  only as strong as deployment access governance, so host/container access and per-operator
  configuration must be controlled externally.
- **B: add a distinct administrator credential and authentication realm.** Advantages: stronger
  application-level attribution and possible remote operation. Risks: credential issuance,
  rotation, storage, network exposure and session revocation become new scope.
- **C: add an `admin` flag/role to normal accounts.** Advantages: reuses login. Risks: mixes product
  and operational authority, needs role-management UI/process and risks exposing admin capability
  to the frontend.

**Recommendation: A.** It is the narrowest meaning of “designated administrator” compatible with
DEC-022; the operator label is not a credential.

### Q2 - Which operational surface should exist?

**Why it matters:** an HTTP surface needs a secure network/authentication lifecycle; the accepted
scope requires an operation, not a console.

- **A (recommended): restricted backend command only.** Advantages: no public route, browser or
  frontend secret; easy to keep inside existing container/deployment access. Risks: requires shell
  access and an operator runbook.
- **B: private operational API only.** Advantages: remotely automatable. Risks: a new bearer/mTLS or
  gateway boundary, proxy/log review and accidental exposure risk.
- **C: command plus API.** Advantages: flexibility. Risks: doubles entry points and proof burden
  without an MVP need.

**Recommendation: A.** Do not mount an RF-32 route in FastAPI or add frontend code.

### Q3 - Which consultation lifecycles may this minimum operation remove?

**Why it matters:** open removal has explicit DEC-022/041 semantics. A finalized consultation has
already erased content and now owns private outcomes; changing those outcomes is the deferred
manipulation/review policy.

- **A (recommended): open consultations only.** If finalization, author deletion or a prior removal
  wins, return a safe conflict/unavailable result. Advantages: coherent vertical slice, exact RF-37
  consumer, no implicit outcome policy. Risks: an operator cannot suppress already-finalized
  outcome records through this MVP command.
- **B: open and finalized; finalized removal preserves every stored outcome.** Advantages: wider
  target coverage. Risks: needs a second removal marker/visibility contract like RF-13 and may leave
  allegedly abusive results in RF-21.
- **C: open and finalized; finalized removal deletes or replaces outcomes.** Advantages: handles
  disputed results. Risks: implements the deferred manipulation adjudication and participant-history
  policy without reports/review/appeal.

**Recommendation: A.** It removes accessible user content while avoiding the broad RF-32 feature.

### Q4 - What immutable audit/idempotency data should be retained?

**Why it matters:** state and logs alone cannot prove exact replay or answer who/when/why after
content minimization.

- **A (recommended): one immutable removal row with target, unique operation UUID, UTC time,
  configured operator label, controlled reason code and previous state.** Advantages: transactional
  exact replay, minimal durable audit and no free text. Risks: adds a table and retains bounded
  operational metadata with the consultation.
- **B: nullable removal columns directly on `consultations`.** Advantages: fewer joins. Risks: mixes
  product lifecycle with audit identity and makes uniqueness/cross-target operation reuse weaker.
- **C: logs only.** Advantages: no schema change. Risks: non-transactional, weaker retention and no
  reliable idempotency after lost output.

**Recommendation: A.** It is the minimum new persistent data genuinely needed.

### Q5 - How should “why” be represented?

**Why it matters:** free text may duplicate allegations or personal data after the content itself is
deleted, while no reason undermines accountability.

- **A (recommended): required controlled code only**, initially
  `rights_or_privacy`, `safety_or_abuse`, `vote_integrity`, or `other`; no free-text note.
  Advantages: minimal and safe to log/retain. Risks: less nuance; `other` needs external operational
  context if later review is required.
- **B: controlled code plus optional bounded free text.** Advantages: more context. Risks: sensitive
  or unnecessary content can enter database/log/export retention.
- **C: required free text only.** Advantages: flexible. Risks: inconsistent, hard to minimize and
  likely to retain copied user content/allegations.

**Recommendation: A.** A later RF-31 case system can own richer evidence under an explicit policy.

### Q6 - What confirmation and retry contract should the command enforce?

**Why it matters:** the action is irreversible and command output can be lost after commit.

- **A (recommended): require canonical target UUID, the same UUID again as confirmation,
  `expected_state=open`, a caller-created operation UUID and reason; exact stored replay succeeds.**
  Advantages: deliberate target confirmation and deterministic recovery. Risks: more operator steps
  and operation-ID discipline.
- **B: require only `--yes`; generate an operation UUID internally.** Advantages: shorter command.
  Risks: weaker wrong-target protection and an ambiguous lost response may not retain the generated
  identity.
- **C: interactive prompt with generated identity.** Advantages: friendly for a terminal. Risks:
  poor automation, redirection and retry behavior.

**Recommendation: A.** Documentation can provide a safe UUID-generation example without storing
the value in browser history.

### Q7 - What is the success/failure and physical-cleanup boundary?

**Why it matters:** filesystem work is fallible and cannot be made atomic with PostgreSQL.

- **A (recommended): removal succeeds at the database commit; cleanup remains the existing separate
  startup/hourly/manual RF-37 process.** Advantages: exact shared contract, bounded command and safe
  retry. Risks: bytes may remain privately stored until reconciliation and require operational
  monitoring.
- **B: command reports success only after synchronous verified file absence.** Advantages: immediate
  physical assurance. Risks: misleading failure after irreversible commit, timeout ambiguity and
  duplication of cleanup leadership.
- **C: commit, then automatically run best-effort cleanup inside the command.** Advantages: often
  faster convergence. Risks: conflates two exit contracts and can make product success look failed.

**Recommendation: A.** The runbook should offer a distinct follow-up cleanup/status command.

### Q8 - What operator output and affected-user experience belong in this subset?

**Why it matters:** the broad card mentions explanation and review, but those need moderation cases,
notifications and policy not present in the MVP.

- **A (recommended): sanitized structured command output with stable exit codes; product users only
  receive existing generic unavailability/disappearance.** Advantages: operational automation with
  no new UI or information leak. Risks: no in-product explanation or appeal in this increment.
- **B: additionally expose the controlled reason to the author.** Advantages: some transparency.
  Risks: requires a retained user-facing tombstone/notification and wording/review policy.
- **C: implement notification and appeal entry.** Advantages: fuller fairness flow. Risks: absorbs
  deferred RF-31/RF-32 administration and messaging scope.

**Recommendation: A.** External operator communication, if any, remains outside NextPost until its
own policy and delivery mechanism are approved.

## Readiness checklist

- [x] Exact Trello card and complete available metadata captured read-only.
- [x] Mandatory context, product reorganization and relevant groomings/plans/reviews read.
- [x] Current code, migrations, configuration, tests and operational boundaries inspected.
- [x] Broad card contrasted with the DEC-022 MVP exception.
- [x] Proposed minimum scope, exclusions, dependencies, security and validation recorded.
- [x] All identified material questions are consolidated in one batch.
- [x] Product owner accepted Q1A-Q8A together on 2026-10-23.
- [x] Confirmed cross-feature decisions are recorded in DEC-046.
- [x] Product owner explicitly requested implementation-plan finalization.
- [x] `harness/features/RF-32-Implementation-plan.md` is ready for implementation.
