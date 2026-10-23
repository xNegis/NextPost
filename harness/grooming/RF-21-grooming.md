# RF-21 - Consult my participation history - Grooming

## Status

`Material grooming complete - implementation plan ready and harness launch authorised`

This note records the read-only Trello intake, repository inspection, current constraints and the
resolved material product decisions. On 2026-10-21 the product owner accepted recommended options
`Q1A` through `Q7A` in one response. No implementation plan has been created or approved, and no
implementation or harness work is authorised by this document.

## Trello snapshot

- Title: `RF-21 · Consultar mi historial de participación`
- URL: https://trello.com/c/J1t1OjVt/22-rf-21-consultar-mi-historial-de-participaci%C3%B3n
- Short URL: https://trello.com/c/J1t1OjVt
- Board: `APP - NextPost`
- List: `Próximo · completar el MVP`
- List ARI: `ari:cloud:trello::list/workspace/6aa9032829f8b45ead46cfdd/6aa903892e7d7b54f23fae23`
- Card ARI: `ari:cloud:trello::card/workspace/6aa9032829f8b45ead46cfdd/6aa90bfa8a3b927014876935`
- Card state: open; not marked complete
- Labels: none
- Members: none
- Start date, due date and completion date: none
- Checklists: none
- Comments: none
- Attachments: none
- Custom fields: none
- Position: `163840`
- Captured read-only on: `2026-10-21T14:19:07.5724630+02:00`
- Last Trello activity at intake: `2026-10-12T11:30:34.555Z`
- Relevant card activity:
  - created in `Funcionalidades` by Negis on `2026-09-15T09:12:26.419Z`;
  - moved from `Funcionalidades` to `Fase 2` by Negis on
    `2026-09-22T14:33:34.941Z`.

### Description and acceptance criteria at intake (verbatim)

> **Reorganización del backlog · 2026-10-12**
>
> Historial privado y devolución al participante forman parte del MVP ya acordado. Depende de votos
> y finalización; conserva solo el resultado no visual permitido. No convierte la coincidencia en
> reputación pública ni en nivel de experto.
>
> Ubicación: Próximo · completar el MVP. El repositorio es la fuente de estado y especificaciones
> aceptadas. Esta organización no aprueba un plan ni lanza implementación.
>
> ---
>
> **Descripción conservada del ticket**
>
> **Historia de usuario**
> Como votante, quiero recordar dónde participé y saber si mi voto coincidió con la elección
> declarada.
>
> **Criterios de fase 2 acordados**
> - El historial es privado y muestra por consulta un estado textual: abierta, coincidió, no
>   coincidió, ninguna foto elegida o no disponible, según corresponda.
> - No revela fotos tras finalizar, eliminar o retirar; tampoco muestra resultados agregados de
>   otros votantes.
> - Una consulta abierta eliminada sin finalizar no produce coincidencia. Una finalizada conserva
>   solo el resultado privado mínimo incluso si después se elimina, mientras exista la cuenta
>   participante.
>
> **Aplazado:** porcentaje global de coincidencia, reputación y comentarios. Referencia:
> DEC-019/021/023.

## Repository and accepted-decision baseline

The intake was performed on clean `main` at
`b4c8232fe71225444287863c001c31bdf53d37dd`, exactly matching `origin/main`. RF-19/RF-20 are
recorded as completed and validated.

The mandatory context, the 2026-10-12 product reorganisation, and the grooming, plans and reviews
for RF-12, RF-16, RF-18, RF-19/RF-20, RF-26 and RF-37 were reviewed before this analysis.
The controlling accepted constraints are:

- DEC-019 makes the participant history private and explicitly excludes aggregate feedback,
  comments and global coincidence/reputation.
- DEC-021 defines `Matched`, `Not matched` and `No choice`. Deletion/removal before finalisation
  creates no outcome; finalisation and photo erasure form one winning transaction.
- DEC-023 permits only the minimum account-linked, photo-free semantic outcome while the
  participant account exists. It does not permit the retained raw option choice.
- DEC-029/RF-26 make Private access a bearer-link capability. Prior participation is not an
  account-level entitlement and must not restore access after the capability is lost or revoked.
- DEC-036 reserves `My consultations` as the fourth primary destination for author-owned content.
- DEC-038 allows an open participant to recover their own committed choice only inside an
  independently authorised open consultation detail, not in a durable history result.
- DEC-041 requires terminal retention to be allowlist-based. An open consultation deleted or
  removed before finalisation leaves no outcome.
- DEC-042/043 require an author-deleted open consultation and its votes to disappear, but preserve
  the minimum existing semantic outcomes after an author deletes a finalised consultation.
- DEC-044 establishes RF-19/RF-20 as the producer and RF-21 as the private consumer of one semantic
  outcome per voter. Historical finalised rows without those records must not be given fabricated
  results.

## Current implementation findings

### Data and lifecycle

- `backend/app/models.py` contains immutable `Vote` records for open consultations and
  `ConsultationOutcome` records with exactly `matched`, `not_matched` or `no_choice` for successful
  finalisation.
- The finalisation path in `backend/app/consultation_finalization_service.py` creates one outcome
  per voter, persists the final snapshot, removes every raw `Vote`, erases images and finalises in
  one transaction.
- `ConsultationOutcome` retains no photo, selected option or raw vote. Its voter index supports an
  account-filtered lookup, but the current indexes are not designed for a stable voter-first
  chronological page. `votes` has no voter-first index at all.
- `Vote.created_at` represents the open participation time. After finalisation that record is
  deleted; the retained outcome date is the transformation/finalisation time, not the original vote
  time. The current model therefore cannot honestly display one uniform “voted on” timestamp for
  every historical state.
- RF-13 author deletion removes open votes and creates no tombstone. A finalised consultation is
  retained with `author_deleted_at`, and its existing outcomes remain available.
- There is no production account-deletion flow and no restricted RF-32 administrative removal
  flow. The account foreign keys are restrictive, so RF-34 must later explicitly delete or
  anonymise account-linked outcomes before an account can be removed.
- The RF-19/RF-20 migration intentionally performs no outcome backfill. Pre-existing finalised
  consultations cannot be assigned an individual result safely from declarations or aggregate
  counts.

### API and presentation

- There is no participant-history endpoint, schema or screen.
- Existing `/api/my-consultations` endpoints and `MyConsultations.tsx` are author-only and must not
  be reused in a way that mixes author and participant authority.
- The frontend has four destinations: Home, Create, My consultations and Profile. Direct
  consultation entry is a separate route-aware flow.
- Existing API projections distinguish open and finalised consultation data and already demonstrate
  strict response allowlists. RF-21 needs a narrower participant-specific projection with no
  aggregate counts, declaration set, photo identifiers, raw chosen option, author controls or
  capability token.
- Public and Private access are evaluated for the current consultation request. A history row or
  cursor must never become an access credential.

## Provisional minimum coherent increment

Subject to the unresolved questions below, the smallest coherent MVP increment is a private,
authenticated participation-history screen backed by a dedicated read-only endpoint. It would
combine:

1. the current account's live `Vote` rows for consultations that are still open; and
2. the current account's retained `ConsultationOutcome` rows for completed finalisations.

Each consultation appears at most once. The history row itself is photo-free and contains only a
stable opaque consultation reference, a textual semantic state and an accurately labelled relevant
date. It contains no raw chosen option, photo or image metadata, aggregate count, declaration set,
other participant identity, public reputation or global percentage.

The following are proposed engineering defaults rather than product decisions:

- session-derived account scope on every query; a client-supplied account identifier is forbidden;
- descending keyset pagination with deterministic tie-breaking, provisionally `20` items per page
  and a server maximum of `50`;
- opaque cursors that are pagination state only, are validated and cannot expand authority;
- a distinct initial loading state, empty state, recoverable error with Retry, and load-more error
  that preserves already loaded rows;
- no polling and no retained participant-history cache across sign-out/account changes;
- privacy headers consistent with other authenticated responses and no logging of row contents;
- semantic list/headings, text labels independent of colour, visible keyboard focus, 44px touch
  targets, safe-area-aware mobile layout and correct behaviour at 320px and 200% zoom;
- only evidence-driven additive voter-first indexes if the approved query needs them; no data
  backfill or new retention table unless an accepted answer below explicitly requires one.

## Conflicts and dependencies outside RF-21

### RF-32 - removal and suspension

The broad RF-32 card includes administrative removal, suspension, reversals, audit/appeal and the
possible invalidation of manipulated votes. Those behaviours are not groomed and must not be
implemented implicitly here. The accepted MVP prerequisite is only a restricted manual consultation
removal path, which still needs its own grooming and validation with RF-37 before real-user exposure.

RF-21 can read an already retained final semantic outcome, but it cannot decide whether a future
RF-32 removal should preserve, suppress, recalculate or erase that outcome. Question Q5 sets the
safe interface boundary without adding RF-32 authority or workflows to this ticket.

### RF-42 - delivery and invited beta

RF-42 consumes the completed full loop, including RF-21, during web/iOS/TestFlight and invited-user
validation. RF-21 does not authorise HTTPS delivery, builds, deployment, TestFlight upload,
invitations or production data handling. RF-42 also remains dependent on the restricted RF-32/RF-37
path and the separate account/data review. None of those delivery activities belong in RF-21.

### RF-34 - account deletion

RF-21 must honour DEC-023's “while the participant account exists” boundary, but must not define or
implement account deletion. RF-34 must later specify deletion versus anonymisation and satisfy the
current restrictive foreign keys. RF-21 should add no independent retention period or archival
copy.

## Material questions and accepted answers

All questions were presented in one batch. On 2026-10-21 the product owner accepted every
recommended option: `Q1A`, `Q2A`, `Q3A`, `Q4A`, `Q5A`, `Q6A` and `Q7A`.

### Q1 - Where should a participant find the history?

**Why it matters:** the current mobile navigation already has four primary destinations, while
`My consultations` has an accepted author-only meaning.

- **A - Add a fifth primary destination**, with the short navigation label `History` and the screen
  title `My participation`. **Advantages:** visible to vote-first users and keeps author/participant
  concepts separate. **Risks:** tighter mobile navigation and another top-level destination.
- **B - Link it from Profile.** **Advantages:** smallest navigation change. **Risks:** materially less
  discoverable for an MVP feedback loop.
- **C - Replace My consultations with a broader My activity area and tabs.** **Advantages:** one home
  for authored and voted activity. **Risks:** changes DEC-036/RF-12 terminology and expands this
  ticket into an information-architecture redesign.

**Recommendation: A.** It completes the participant loop explicitly without changing the accepted
meaning or behaviour of `My consultations`.

### Q2 - What may an open-participation row reveal or reopen?

**Why it matters:** the card requires an `Open` state, but an earlier vote must not become standing
access to a Private consultation or leak its question/author after a link is lost or revoked.

- **A - Minimal photo-free row.** Show only `Open`, an opaque consultation reference and the relevant
  date. A View action may be offered only when the consultation is currently Public or another
  independently supplied request capability authorises it. The history never stores/returns a
  Private token and participation itself grants no access. **Advantages:** fulfils the open state
  while preserving DEC-029. **Risks:** a Private row can be hard to recognise without the original
  link.
- **B - Show the question/author and let every history row reopen the consultation.** **Advantages:**
  recognisable and convenient. **Risks:** turns account history into a new access channel and leaks
  Private metadata.
- **C - Exclude all open participations.** **Advantages:** simplest and safest. **Risks:** directly
  misses an agreed card state and delays useful confirmation that a vote was recorded.

**Recommendation: A.** A history is evidence of participation, not an access-control grant.

### Q3 - Which date and ordering semantics should the mixed history use?

**Why it matters:** an open `Vote` retains its vote time, but the raw vote is intentionally deleted
at finalisation. The durable outcome only has its finalisation/transformation time.

- **A - Use an accurately labelled effective event date:** `Voted …` for open rows and `Finalized …`
  for terminal outcomes; sort descending by that effective date plus a stable identifier.
  **Advantages:** truthful, needs no extra retained personal datum and works with current records.
  **Risks:** a row can move upward when the consultation is finalised, and the labels differ.
- **B - Add the original vote timestamp to every durable outcome.** **Advantages:** one consistent
  “participated on” meaning. **Risks:** expands retained account-linked data, needs a migration and
  cannot repair older outcomes honestly.
- **C - Sort by consultation publication date.** **Advantages:** already available. **Risks:** does
  not represent the participant's action or result event and can feel chronologically wrong.

**Recommendation: A.** It is the smallest truthful model and preserves the existing minimisation
boundary.

### Q4 - What should `Unavailable` mean when an open consultation disappears?

**Why it matters:** the Trello wording names `Unavailable`, but RF-13/RF-37 deliberately delete an
open vote and create no outcome when the consultation is deleted before finalisation. A durable
Unavailable row would require a new account-linked participation tombstone and a change to the
accepted terminal allowlist.

- **A - Do not create a tombstone.** An open participation disappears if its consultation is deleted
  or removed before finalisation. Reserve `Unavailable` for a provable historical/inconsistent case
  where an account-linked participation record still exists but no safe semantic outcome can be
  shown. **Advantages:** preserves DEC-041/043 and adds no new retained personal data. **Risks:** the
  user cannot later see that deleted open participation, so the card wording must be clarified.
- **B - Add a minimal Unavailable tombstone** for every open deletion/removal. **Advantages:** a
  complete durable activity ledger. **Risks:** expands retention, migrations and erasure logic;
  requires coordinated changes to RF-13 and future RF-32, not just an RF-21 reader.
- **C - Keep the raw vote to drive Unavailable.** **Advantages:** no new table. **Risks:** violates
  the accepted deletion and minimisation model and is not viable.

**Recommendation: A.** Treat a pre-finalisation deletion as no durable outcome, exactly as the
accepted lifecycle specifies; do not create a second hidden retention system in RF-21.

### Q5 - How should later deletion/removal affect an already finalised outcome?

**Why it matters:** author deletion is already defined, but future RF-32 removal may involve abuse or
vote manipulation and has not yet defined whether outcomes are preserved or invalidated.

- **A - Display the stored semantic outcome while it exists.** Author deletion does not change it.
  RF-21 does not infer an administrative state; future RF-32 must explicitly preserve, replace or
  delete outcomes in its own approved transaction, after which RF-21 renders the resulting stored
  state. **Advantages:** matches DEC-023/043 and creates a clean producer/consumer boundary.
  **Risks:** RF-32 must later handle manipulated outcomes deliberately.
- **B - Map every removed finalised consultation to Unavailable in RF-21.** **Advantages:** avoids
  presenting a potentially disputed result. **Risks:** requires RF-21 to know an as-yet undefined
  moderation state and contradicts preservation after ordinary author deletion.
- **C - Delete all outcomes whenever finalised content is removed.** **Advantages:** simplest visible
  moderation effect. **Risks:** discards the explicitly accepted private minimum and prematurely
  decides RF-32 policy.

**Recommendation: A.** RF-21 should remain a narrow consumer; RF-32 owns any future invalidation or
recalculation rule.

### Q6 - How should legacy finalised participation be represented?

**Why it matters:** rows finalised before RF-19/RF-20 may lack per-voter outcomes. Aggregate counts
and the author's selection cannot prove an individual's result.

- **A - No fabricated backfill.** Show current open votes and real semantic outcomes only. Show
  Unavailable only where an actual surviving account-linked participation record proves that the
  user participated but a safe result cannot be produced; otherwise omit the legacy row.
  **Advantages:** honest and consistent with DEC-044. **Risks:** old participation may be absent.
- **B - Infer an individual result from aggregates/declarations.** **Advantages:** fuller-looking
  history. **Risks:** mathematically incapable of identifying the user's vote and can display a
  false result.
- **C - Block RF-21 until legacy data is manually repaired.** **Advantages:** uniform UI.
  **Risks:** there is no reliable source for repair and it delays the MVP without improving truth.

**Recommendation: A.** Absence is preferable to an invented personal result.

### Q7 - What tone should the outcome use?

**Why it matters:** `Matched` means agreement with the author's declaration, not correctness,
expertise or external publication success.

- **A - Neutral text badges plus a short explanation.** Use `Open`, `Matched`, `Not matched`,
  `No choice` and, only under Q4/Q6's accepted conditions, `Unavailable`; explain that matching
  compares the vote with the author's declared choice. **Advantages:** accessible, precise and
  resistant to gamification. **Risks:** slightly more copy.
- **B - Success/failure language and celebratory styling.** **Advantages:** emotionally prominent.
  **Risks:** implies objective correctness and nudges RF-21 toward reputation mechanics.
- **C - Bare labels with no explanation.** **Advantages:** compact. **Risks:** `Matched` can be
  misunderstood and `No choice` can be confused with “you did not vote”.

**Recommendation: A.** It preserves the accepted meaning and does not turn feedback into a score.

## Accepted decision register

- **Q1A:** add a fifth primary `History` destination whose screen title is `My participation`;
  retain the author-only meaning of `My consultations`.
- **Q2A:** open rows are minimal and photo-free. Participation never grants Private access, stores a
  capability or restores a lost/revoked link. A View action requires current independent authority.
- **Q3A:** label the effective event date honestly as `Voted` for an open vote and `Finalized` for a
  terminal outcome; order descending by that event plus a deterministic identifier.
- **Q4A:** do not add an open-deletion participation tombstone. Deletion/removal before finalisation
  leaves no durable row. `Unavailable` is reserved for a proven account-linked legacy/inconsistent
  participation for which no safe semantic result exists.
- **Q5A:** display a stored final semantic outcome while it exists, including after ordinary author
  deletion. RF-32, not RF-21, must later decide any administrative preservation, invalidation,
  replacement or erasure transaction.
- **Q6A:** never fabricate historical outcomes. Include real current votes and semantic outcomes;
  show `Unavailable` only with surviving account-linked proof, otherwise omit the legacy row.
- **Q7A:** use neutral textual states and explain that matching is comparison with the author's
  declared choice, not objective correctness, reputation or expertise.

These decisions complete material grooming. On 2026-10-21 the product owner explicitly approved
creation/finalisation of `harness/features/RF-21-Implementation-plan.md` and launch of the external
implementation harness.

## Proposed observable behaviour if all recommendations are accepted

- An authenticated participant has a separate `My participation` history reachable from `History`.
- Rows are newest effective event first and paginated; the empty state explains that voted
  consultations will appear here and links back to Home.
- A still-open participation is represented without a photo or raw option. It creates no Private
  access grant.
- Finalised participation shows exactly one neutral outcome: `Matched`, `Not matched` or
  `No choice`.
- `No choice` means the author explicitly declared that no option was selected; it does not mean the
  participant failed to vote.
- Author deletion after finalisation does not remove the retained private outcome. Open deletion
  before finalisation leaves no durable row.
- Legacy participation is never assigned an inferred result.
- No aggregate, result snapshot, other voter, raw selection, photo, reputation, comment or global
  percentage appears in the participant payload or UI.

## Validation outline for a later approved plan

This is an analysis checklist, not an implementation authorisation.

- API authentication and strict account isolation across at least two participants and an author.
- Exact response allowlist tests proving absence of photos, URLs, option IDs, raw choices,
  declarations, counts and other-account data.
- Open plus all three terminal outcomes, author-deleted final outcome, open deletion behaviour and
  legacy/no-backfill behaviour.
- Stable keyset pagination across tied timestamps, empty pages, invalid cursors and concurrent state
  transitions without duplicate rows.
- Private-link tests proving that history neither retains nor recreates a capability and cannot
  bypass revocation.
- Sign-out/account-switch cache isolation; generic recoverable errors; retry and load-more failure
  without discarding successful rows.
- Keyboard, screen-reader, text-only status, focus, 320px, safe-area and 200% zoom coverage.
- PostgreSQL query/migration tests for any additive indexes, plus the full backend and frontend
  regression suites, formatting, lint, type checks and production build.
- Manual visual and interaction acceptance remains required by DEC-034 after implementation review.

## Explicitly out of scope

- global match percentage, streaks, reputation, expertise levels, comments or notifications;
- revealing the participant's durable raw choice, author aggregate results or other voters;
- adding account-level Private access, persisting/recovering share tokens or changing RF-26;
- RF-32 administration, suspension, moderation inbox, appeal, audit or vote-recalculation workflows;
- RF-34 account deletion/anonymisation implementation;
- RF-42 deployment, HTTPS, App Store/TestFlight work or invited-user operations;
- edits to Trello, implementation-plan finalisation, harness launch or product-code implementation.
