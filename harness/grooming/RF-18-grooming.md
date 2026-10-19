# RF-18 - Consult results as author - Grooming

## Status

`Grooming complete - implementation plan approved`

Explicitly selected by the product owner on 2026-10-16. This document records the
read-only Trello intake, repository findings, alternatives and confirmed choices. On
2026-10-18 the owner selected `1A`, `2B` with a five-second automatic refresh, a custom
count-only answer to Q3, and `4A`. DEC-039 records the durable cross-feature behavior.
No material question remains identified. On 2026-10-18 the product owner explicitly approved
all settled decisions, finalisation of the self-contained implementation plan and launch of the
external implementation harness. `harness/features/RF-18-Implementation-plan.md` is therefore
`Ready for implementation`. No Trello mutation, commit, push or deployment is authorized.

## Trello snapshot

- Title: RF-18 · Consultar resultados como autor
- URL: https://trello.com/c/GBfvkzU8/19-rf-18-consultar-resultados-como-autor
- Stable short URL: https://trello.com/c/GBfvkzU8
- Card ARI: `ari:cloud:trello::card/workspace/6aa9032829f8b45ead46cfdd/6aa90bf5e444b636722d0975`
- Board: APP - NextPost; `ari:cloud:trello::board/workspace/6aa9032829f8b45ead46cfdd/6aa903892e7d7b54f23fae1b`; matches the configured board.
- Board URL: https://trello.com/b/CgBkRg78/app-nextpost
- List: Próximo · completar el MVP; `ari:cloud:trello::list/workspace/6aa9032829f8b45ead46cfdd/6aa903892e7d7b54f23fae23`
- Captured on: 2026-10-16; live reads completed before 19:04:51 UTC /
  21:04:51 Europe/Madrid. The connector supplies no exact read timestamp.
- Last activity at intake: `2026-10-12T11:26:42.514Z`.
- Position: 65536.
- Archived: false; complete: false; due complete: false.
- Started at / due date: none.
- Labels / members / comments / checklists: none. All returned truncation flags are false;
  the separate comments and checklist reads have no next page.
- Attachments / custom field values: none; separate reads have no next page.
- Available activity: card creation on 2026-09-15 and a move from `Funcionalidades` to
  the historical `Fase 2` list on 2026-09-22. The current card read is authoritative for
  the renamed `Próximo · completar el MVP` list and current description.
- Intake mismatch: none in identifier, title, board, current list or content.
- Read-only board/card inspection; no Trello mutation.

### Description and acceptance criteria at intake (verbatim)

**Reorganización del backlog · 2026-10-12**

El autor utiliza votos y porcentajes como opiniones de quienes participaron para decidir; conserva la libertad de discrepar. El autor determina cuándo la ayuda le resulta suficiente: no se fija aquí un mínimo obligatorio de votos, un plazo de respuesta ni una garantía. Los resultados agregados siguen siendo solo del autor.

Ubicación: Próximo · completar el MVP. El repositorio es la fuente de estado y especificaciones aceptadas. Esta organización no aprueba un plan ni lanza implementación.

---

**Descripción conservada del ticket**

**Historia de usuario**
Como autor, quiero ver cuántos votos recibe cada foto para decidir con información clara.

**Criterios de fase 2 acordados**
- Solo el autor ve totales y porcentajes agregados por foto, incluidos cero votos y empates, sin identidades ni elecciones individuales de los votantes.
- Mientras la consulta está abierta, los resultados pueden actualizarse con información de fallo/reintento si se pierde conexión.
- Tras finalizar y borrar las fotos se conservan únicamente los datos agregados y resultados privados mínimos de DEC-023; la presentación no muestra miniaturas rotas.
- Los porcentajes no se presentan como certeza o garantía.

**Aplazado:** mostrar resultados agregados al votante. Referencia: DEC-019/021/023.

## Sources and verified baseline

Read `AGENTS.md`, all seven `harness/context` documents, the product/backlog
reorganization and historical phase-2 scope, RF-12 grooming/approved plan, RF-16
grooming/approved plan, and the approved RF-10 publication and RF-11 lifecycle plans.
Inspected the current dirty worktree rather than treating dated missing-code statements
as current evidence. Existing RF-16 and real-iPhone corrections are user/project work
and must be preserved.

Binding decisions include DEC-017–023, DEC-028–035, DEC-036 and DEC-038:
publication is immutable; open consultations do not expire; only the author sees
aggregates; voters may recover only their own immutable choice; finalization later
declares one/several/none and removes photos; minimum non-image aggregates/outcomes may
remain; denial is non-enumerating; and the product owner owns visual acceptance.

## Intended outcome

An authenticated author sees the current total vote count on each Open row in My consultations
and opens one of their own consultations to see the exact vote count for every immutable photo
option. Zero-vote options remain present, equal counts are visibly tied without hidden
tie-breaking, and no identity or per-account choice is returned. This first increment does not
calculate, return or display percentages. The results help the author decide but do not label a
photo objectively best, predict external success or constrain the author's choice.

While the Open list or an open owner detail is visible, the relevant counts refresh automatically
every five seconds. Only one request per result scope may be in flight; hidden/unmounted views do
not poll, and returning to a visible view triggers an immediate refresh before the interval resumes.
The existing manual Refresh remains available for immediate recovery. Loading, refresh failure,
session loss and unavailable state remain distinct, and a failed refresh does not silently replace
known results with zero. Voter/general consultation surfaces stay aggregate-free.

The Trello card also requires a future post-finalization, photo-free aggregate. The current
repository has no finalization mutation, declared-choice/outcome model or published-photo
purge. The delivery boundary for that criterion is therefore a material open decision below;
grooming must not fabricate finalized data or pre-empt RF-19/RF-20/RF-37.

## Current code findings

### Vote and database model

- RF-16 is implemented and recorded as `Completed and validated`. Alembic revision
  `20261016_0005_votes.py` adds `Vote` with opaque UUID, consultation ID, voter ID,
  selected `ConsultationPhoto` ID and server timestamp.
- Database uniqueness on `(consultation_id, voter_id)` makes one immutable vote per account.
  A composite foreign key proves the selected option belongs to the same consultation.
- Index `ix_votes_consultation_photo` on `(consultation_id, consultation_photo_id)` is the
  direct aggregate path RF-18 can consume. No denormalized count or percentage exists.
- Restrictive foreign keys prevent a later account/terminal operation from silently removing
  participation. Future account deletion and terminal workflows must deliberately transform,
  remove or anonymize affected records under their own contracts.
- Every current Vote row is a valid confirmed choice under RF-16. There is no moderation/
  invalidation flag, weighting, comment or ranking. RF-18 must count rows once and equally.

### Backend and authorization

- `vote_service.py` deliberately returns only the current voter's own option and explicitly
  leaves aggregates to RF-18. `GET .../my-vote` and `POST .../votes` cannot be reused as an
  author result surface; the access policy rejects the author for voting.
- `consultation_service.py` has owner-scoped `list_my_consultations` and
  `read_my_consultation`. The current open owner projection returns text, audience,
  publication time and immutable ordered photo metadata; the finalized projection returns
  only ID/state/publication time.
- `/api/my-consultations` and `/api/my-consultations/{id}` derive the owner from the signed
  cookie and scope authorization server-side. A Public read or Private capability does not
  grant management authority. These are the correct authority boundaries for RF-18.
- No result service, aggregate schema or author-result route exists. No current response
  includes a total, per-photo count or percentage.
- A set-wise SQL aggregate can join every `ConsultationPhoto` to `Vote` with an outer join,
  group by stable option ID/ordinal and order by ordinal. The outer join is required to
  preserve options with zero votes; computing only from Vote would incorrectly omit them.
- A focused owner route such as `GET /api/my-consultations/{id}/results` is the recommended
  technical boundary. It independently refreshes results, avoids making the immutable general
  detail viewer-specific, and can return an exact allowlist. The server should return integer
  counts and the total as the arithmetic source of truth; presentation rounding is a product
  choice below.
- The owner check must happen before aggregate work and storage access. Unknown, non-owner,
  deleted and removed targets should remain generically unavailable. Open is readable now;
  finalized behavior depends on the delivery-boundary decision.
- Existing private response headers (`private, no-store`, `no-referrer`, `nosniff`) apply.
  No response or log should contain voter IDs, aliases, emails, individual choices, vote
  timestamps, Private tokens, question/context, file keys or bytes beyond fields explicitly
  needed by the owner view.

### Frontend and observable integration

- `My consultations` is the accepted fourth primary destination. It has Open/Finalized tabs,
  an owner-only paginated list, and a returning `OwnerConsultationDetail`.
- Open owner detail already loads the persisted comparison in immutable photo order and has a
  single Refresh action. This is the smallest coherent place to align per-photo results with
  the actual photos. It currently displays no counts or percentages.
- The list currently displays open question/audience/state/publication date and finalized
  ID/state/publication date. RF-12 deliberately omitted fake vote counts until RF-16/RF-18.
- Finalized owner detail explicitly says photos are unavailable and contains no stable option
  labels or aggregate fields. It does not touch storage. Any future results there must use
  stable text labels such as `Photo 1`, `Photo 2` in publication order, never broken images.
- `consultationApi.ts` strictly validates exact payload keys. RF-18 must add exact result
  guards and reject extra identity/per-voter fields rather than silently ignoring them.
- `useOwnerConsultationDetail` owns request generations, object-URL cleanup, session loss,
  lifecycle reconciliation and Private-link state. Results need their own generation/current-
  consultation ownership so a stale response cannot appear under another account or item.

## Dependencies and conflicts

| Dependency | RF-18 relationship |
| --- | --- |
| RF-10/RF-11 | Supplies immutable options, protected media and current lifecycle. Results must not relax open-only media access or invent lifecycle mutations. |
| RF-12 | Supplies My consultations and owner-only detail/list authority. RF-18 should extend this owner journey, not Home or voter detail. |
| RF-16 | Supplies valid immutable Vote rows and the aggregation index. Voter APIs/UI must remain aggregate-free. |
| RF-19/RF-20 | Later lock the consultation, snapshot final aggregates and declared selections, create participant outcomes and finalize atomically. They must define the durable post-finalization projection. |
| RF-37 | Later revokes/purges image bytes. Finalized results must use stable non-image labels and must not depend on photo reads or thumbnails. |
| RF-13/restricted RF-32 | Deleting/removing an open unfinalized consultation produces no retained outcome; generic unavailable behavior must not leak results. |
| RF-21 | Consumes participant outcomes only after finalization and never gains the author aggregate or identities. |
| RF-34 | Future account deletion must deliberately remove/anonymize account-linked data and reconcile retained aggregate policy; RF-18 must not guess it now. |

RF-18 can safely deliver live open aggregates without a new migration because current Vote
rows are already normalized and indexed. A durable finalized snapshot cannot be completed
honestly until its atomic writer and relationship to photo/file-row deletion are settled by
RF-19/RF-20/RF-37. This is not a reason to leak or retain per-voter choices indefinitely.

## Candidate approach and alternatives

### Aggregate query and API

Selected direction: a dedicated owner-only result read, with one set-wise outer-join aggregate
over all immutable options. Return exact consultation/state/total plus ordered option IDs,
ordinals and integer counts. Return no percentage, denominator-derived display value, leader,
winner, ranking or confidence. This avoids N+1 queries, includes zero-vote options and supports
ties naturally. The same owner-scoped aggregate supports the Open-list total without exposing
per-option results in the list payload.

Alternative: embed results in every owner detail response. This saves one request but couples
immutable detail/photo loading to a frequently refreshed aggregate and makes independent retry
less clear. Alternative: persist/update counters on every vote. That adds write contention,
reconciliation and drift risk without evidence that live aggregation is too expensive for the POC.

### Five-second refresh and stale-data behavior

Selected direction: fetch immediately when the My consultations Open list or open owner detail
becomes visible, then refresh every five seconds while that scope remains visible. Do not overlap
requests: if the previous request is still pending, skip that tick rather than queueing another.
Pause when the browser document is hidden, the user changes tab/destination/detail, the component
unmounts or the account changes; invalidate late responses and refresh immediately on return to a
visible current scope. Keep the existing manual Refresh for immediate recovery.

A failed refresh preserves the last successful counts, labels them as not refreshed and permits
manual Retry while the next five-second tick may try again. A first-load failure shows no invented
zero values. A successful zero-vote aggregate is distinct from failure. Session loss clears all
author data and stops polling; current denial clears protected content. This needs no push,
background worker or browser-persistent cache.

### Count-only presentation

Selected direction: the total is the number of current valid Vote rows for the consultation;
each option count is the number selecting that stable option. Never omit an option, divide by
eligible viewers, invent skipped users or treat absence as a vote. This increment performs no
percentage calculation and exposes no percentage field, so later percentage work cannot be
mistaken for already implemented behavior.

Keep immutable photo order, show the exact count beneath each photo and show the total once.
Use correct singular/plural copy (`1 vote`, `2 votes`). With zero total, every option displays
`0 votes`. Equal counts remain visibly equal without a tie badge, hidden tie-break or reordering.
There is no leading-photo badge, winner color, confidence meter or automatic selection.

## Questions - one consolidated material batch

### Open

None. The owner resolved Q1-Q4 on 2026-10-18. The settled scope and explicit plan-finalization
approval remain a separate gate.

### Resolved on 2026-10-18

#### Q1 - Where should the author see the results?

- **A (selected): total vote count in each Open row plus full per-photo results in owner detail.**
  This completes RF-12's deliberately deferred at-a-glance count while keeping per-photo counts
  aligned with the private detail photos. The list remains author-only and does not show a leader.
- **B: full results only in owner detail.** Smaller list/API change, but the author must open every
  consultation to see whether new help arrived and RF-12's deferred count remains pending.
- **C: a separate Results screen reached from owner detail.** Clear separation but adds another
  navigation/state layer for a small aggregate and separates counts from the photos they describe.

#### Q2 - How should open results update?

- **A: load on detail entry and explicit Refresh, with honest stale/error feedback.**
  No background requests; preserve the last successful result on refresh failure and never replace
  a failed first load with zeros.
- **B (selected, clarified): refresh automatically every five seconds while the current Open list
  or owner detail is visible.** One request per scope at a time, no hidden/unmounted polling,
  immediate refresh on visibility return, preserved last-known counts on failure and manual Refresh.
- **C: explicit Refresh plus slow polling.** More current than A, but still adds lifecycle and stale
  request complexity for little POC benefit.

#### Q3 - How should percentages, zero votes and ties be presented?

- **A: immutable photo order, exact count, one-decimal percentage, total votes once,
  no leader/winner styling.** Zero total shows every option as `0 votes · 0%`; ties naturally show
  equal values. Add restrained copy that these are participant opinions and may change while open.
- **B: whole-number percentages.** Visually simpler, but small samples lose useful precision and
  independently rounded values can sum to 99% or 101%.
- **C: rank/highlight the current leader.** Faster to scan, but overstates a moving opinion sample,
  makes ties/zero awkward and conflicts with the author's freedom to disagree.

- **Selected custom direction: no percentages for now; show only exact vote counts.** Preserve
  immutable order, show total once, use singular/plural copy, keep zero-vote options and represent
  ties through equal numbers only. Percentages remain an unimplemented part of the broader ticket.

#### Q4 - What delivery boundary should RF-18 use for finalized results?

- **A (selected): implement complete live Open results now and leave durable finalized snapshot/
  photo-free presentation as an explicit RF-19/RF-20/RF-37 consumer gate.** No speculative table
  or fake finalized fixture becomes a claimed product capability; the broad Trello card remains
  partially open until that integration has evidence.
- **B: add a finalized aggregate snapshot table/projection now, populated only by tests until the
  future finalization writer exists.** Prepares the shape but adds unused persistence and risks
  conflicting with the still-ungroomed atomic outcome/photo-row lifecycle.
- **C: defer all RF-18 implementation until finalization and photo deletion are ready, then deliver
  open and finalized results together.** Gives one complete card boundary but delays the central
  author feedback loop even though open aggregation is already safe and useful.

### Resolved / inherited

- Only the authenticated author may see aggregate results. This increment exposes counts only;
  percentages remain deferred. Voters/participants never receive aggregates, including after voting.
- No response reveals voter identity or an individual's selected option to the author.
- Every immutable photo option appears, including zero; equal results remain ties.
- Results are opinions, not certainty, objective quality, predicted success or an obligation for
  the author to follow the majority (DEC-035 and the Trello reorganization note).
- There is no minimum vote threshold, response deadline, automatic closure or result guarantee.
- Finalized presentation must be photo-free and retain only DEC-023's minimum non-image data.
- Owner visual acceptance remains DEC-034; implementation agents do not perform browser visual
  inspection unless the owner separately requests a specific check.

## Settled proposed scope

### In scope

- Owner-only aggregate route/service with strict allowlisted payload and private headers.
- One set-wise outer-join query returning all stable options in publication order, exact counts
  and total without voter identity fields or N+1 work.
- My consultations Open rows show current total votes; open owner detail aligns exact per-photo
  counts with the immutable photos.
- Count-only presentation, including zero-vote options, natural ties and singular/plural copy.
- Immediate load plus non-overlapping five-second automatic refresh while the relevant view is
  visible; pause/invalidate outside that scope and retain manual Refresh.
- Honest first-load, stale-refresh, offline/network, session-loss, denied and unavailable behavior.
- Strict frontend guards and independent request generation/cleanup.
- Automated privacy/access/query/math/concurrency-regression coverage and isolated built smoke.
- Exact documentation of the finalized-result RF-19/RF-20/RF-37 consumer gate.

### Out of scope

- Aggregate access for voters, participants, Home/feed, public pages or Private-link holders.
- Voter identities, aliases, emails, per-account choices, vote timestamps or comments.
- Winner/leader declaration, ranking, confidence, prediction, recommendation or automatic choice.
- Percentages and any percentage API field or UI. The broader Trello criterion remains pending.
- Vote editing/withdrawal/invalidation, weighting, moderation and account-deletion behavior.
- Finalization/declaration, author deletion, administrator removal, physical image purge or
  participant history/outcomes unless Q4 explicitly changes the dependency boundary.
- Notifications, push, background/hidden polling, analytics dashboard, reputation/coincidence
  score or model training. The selected visible-view five-second refresh is the only timer.
- New worker/queue/service, denormalized live counters or unrelated RF-14/RF-16 debt.

## Validation outline

### Backend and data

- Owner receives all options in ordinal order for Public and Private open consultations; link state
  is irrelevant to owner authority. Another account, a valid Private-token holder and anonymous/
  stale sessions receive no aggregate or existence detail.
- Zero total, one vote, uneven counts, exact ties and maximum ten options. Sum of option counts
  equals returned total; each Vote counts once. Assert that no percentage field is returned.
- Direct SQL/real PostgreSQL coverage proves the outer join retains zero-vote options and uses the
  current RF-16 integrity constraints/index. No storage access is needed for the aggregate query.
- Unknown, non-owner, deleted and removed are generically unavailable. Open/finalized behavior
  follows confirmed Q4 without weakening protected media rules.
- Exact response keys and private headers on success and error paths; assert absence of voter ID,
  nickname/email, individual choice, timestamp, token, text, storage or media data.
- Existing RF-16 replay/concurrency/late-terminal tests remain green. Aggregate reads neither lock
  out votes nor cache stale counts server-side; each request reads one consistent database statement.

### Frontend and integration

- Strict guards reject missing/extra/malformed IDs, ordinals, counts, totals and forbidden fields.
- Owner list/detail follows Q1A; open detail aligns results by stable photo ID/ordinal and
  never by array accident. Photo/result failures remain distinct and usable.
- Initial loading is not zero success. Five-second refresh success replaces one coherent aggregate;
  failure preserves and labels prior data; manual retry works. One slow request never overlaps or
  queues ticks. Hidden/unmounted/account-switched scopes stop and late responses are ignored.
- Late responses after account/item/navigation/refresh changes cannot restore or mix results.
- Voter reader, `my-vote`, feed and general detail tests assert zero aggregate fields/copy.
- Zero/ties/singular-plural/opinion copy, long counts, 320px/200%-zoom semantics and
  keyboard/focus receive automated coverage; owner performs visual validation.
- Isolated built PostgreSQL smoke with owner plus at least two voters: publish, inspect zeros,
  cast votes including a tie, refresh author results, deny voters/direct API, restart services and
  recover the same aggregate. Do not seed/claim real finalization unless its owning operation exists.

## Readiness checklist

- [x] Current selected card consumed and complete readable snapshot preserved without Trello mutation.
- [x] Existing implementation and relevant approved contracts inspected.
- [x] RF-12 owner boundary, RF-16 Vote model/index and terminal dependencies identified.
- [x] Privacy/security, zero/tie math, error and validation directions analysed.
- [x] Q1A result placement/list summary confirmed.
- [x] Q2B five-second visible-view refresh and stale-data behavior confirmed.
- [x] Q3 custom count-only presentation confirmed; percentages deferred.
- [x] Q4A Open-versus-finalized delivery boundary confirmed.
- [x] Resulting scope and exclusions contain no identified material ambiguity.
- [x] No material question remains.
- [x] Product owner explicitly approved finalizing a self-contained English plan and launching
      the external implementation harness on 2026-10-18.

No implementation, test run, service mutation, visual inspection, commit, push, deployment or
Trello mutation occurred during grooming. The approved plan was created only after the explicit
approval recorded above.
