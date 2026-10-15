# RF-14 - Discover open Public consultations - Grooming

## Status

`Ready for implementation`

Explicitly selected by the product owner on 2026-10-15. This document records read-only
Trello intake, repository findings, alternatives and confirmed Q1B/Q2B choices. It is not
implementation authority. The approved self-contained English contract is now
`harness/features/RF-14-Implementation-plan.md`, marked `Ready for implementation`.
On 2026-10-15 the owner answered `Yo elegiria 1B y 2B`, confirming own Public cards and
first-photo previews. No material question remains identified. The resulting scope is
confirmed by the owner on 2026-10-15 with `lom apruebo - dale caña` in response to the
explicit scope/finalization approval question. A subsequent independent request is
required to launch the harness; no implementation or launch occurred during finalization.

## Trello snapshot

- Title: RF-14 · Descubrir consultas que necesitan votos
- URL: https://trello.com/c/WVW0cmEp/5-rf-14-descubrir-consultas-que-necesitan-votos
- Stable short URL: https://trello.com/c/WVW0cmEp
- Card ARI: `ari:cloud:trello::card/workspace/6aa9032829f8b45ead46cfdd/6aa90520d962e3b8deef234a`
- Board: APP - NextPost; `ari:cloud:trello::board/workspace/6aa9032829f8b45ead46cfdd/6aa903892e7d7b54f23fae1b`; matches the configured NextPost board.
- Board URL: https://trello.com/b/CgBkRg78/app-nextpost
- List: Próximo · completar el MVP; `ari:cloud:trello::list/workspace/6aa9032829f8b45ead46cfdd/6aa903892e7d7b54f23fae23`
- Captured on: 2026-10-15; live reads completed before 15:38:06 UTC /
  17:38:06 Europe/Madrid. The connector supplies no exact read timestamp.
- Last activity at intake: `2026-10-12T11:26:36.593Z`
- Position: 32768
- Archived: false; complete: false; due complete: false.
- Started at / due date: none.
- Labels / members / comments / checklists: none. All returned truncation flags are false.
- Attachments / custom field values: none; separate live reads have no next page.
- Intake mismatch: none in identifier/title/board/list. The title mentions votes, but the
  accepted ticket sequence separates discovery (RF-14), voting (RF-16) and results (RF-18).
  This discovery increment cannot claim the full voting behavior from the card.
- Read-only board/card inspection; no Trello mutation.

### Description and acceptance criteria at intake (verbatim)

**Reorganización del backlog · 2026-10-12**

Núcleo de comunidad: recorrer consultas Públicas abiertas, leer el objetivo y ayudar libremente. Feed cronológico tipo Reddit; no se fuerza votar para poder publicar ni se añade clasificación personalizada.

Ubicación: Próximo · completar el MVP. El repositorio es la fuente de estado y especificaciones aceptadas. Esta organización no aprueba un plan ni lanza implementación.

---

**Descripción conservada del ticket**

**Historia de usuario**
Como usuario registrado, quiero recorrer las consultas Públicas abiertas y votar solo en las que me interesen.

**Criterios de fase 2 acordados**
- El feed es una lista vertical de consultas Públicas abiertas y accesibles, ordenadas de la más reciente a la más antigua.
- Puedo seguir haciendo scroll sin votar ni pulsar un botón «Saltar». Las consultas propias o ya votadas no permiten un nuevo voto.
- Antes de votar no veo totales, porcentajes ni foto líder. Si no hay consultas se muestra un estado vacío real, sin actividad inventada.

**Aplazado:** personalización, ranking por intereses, reparto ponderado, seguidos y botón explícito «Saltar». Referencia: DEC-019/020/022.

## Sources and verified baseline

Read AGENTS.md, all seven harness/context documents, the product reorganization notes,
RF-12 grooming/review and relevant existing grooming decisions. Reviewed approved
RF-03/RF-06/RF-07/RF-08/RF-09/RF-10/RF-11/RF-12 contracts against actual code.
Historical intake observations in those contracts do not describe today's implementation.

- RF-12's approved author-recovery increment is Completed and validated. Both project
  state and RF-12-implementation-review.md record owner acceptance on 2026-10-15:
  `Ok funciona todo`. The earlier technical review has isolated PostgreSQL, built HTTP
  and nonvisual client evidence. This grooming does not rerun or extend that evidence.
- Current App.tsx/Navigation.tsx have Home, Create, My consultations, Profile. Home is
  still a welcome card and the default after ordinary authentication/restoration.
  Destinations use local state, unmount on departure and have no URL routing.
- MyConsultations.tsx implements owner-only Open/Finalized tabs, bounded pagination,
  refresh and owner detail. OwnerConsultationDetail.tsx and useOwnerConsultationDetail.ts
  implement neutral returning detail, ordered stored photos and real Private-link controls.
  These are management components; mounting them for another author's item would fail
  ownership checks and misrepresent the user's authority.
- ConsultationComposer.tsx implements publication and dirty/pending navigation protection.
  PublishedSuccess reuses owner detail; publication success remains a separate journey.
- models.py persists Account, PhotoUploadSession, PhotoUploadImage, Consultation and
  ordered ConsultationPhoto associations. Publication text/audience/photos are immutable;
  published_at exists. There is no vote, aggregate, declaration or participant-outcome model.
- api/consultations.py has publication/capacity, owner list/detail, general protected
  open detail/photo and owner Private-link read/disable/replace/create endpoints. There is
  no feed or real finalization/deletion/removal endpoint.
- consultation_service.py read_consultation_detail and read_consultation_photo invoke
  the shared access policy using current persisted consultation state. Open Public detail
  and photos already allow another authenticated account without a token. Private readers
  require a current link; even its holder must never discover a Private item in the feed.
  Photo IDs are checked against their exact consultation before storage access.
- consultation_lifecycle.py is a pure state/transition policy, not a terminal operation.
  Promoted photos survive temporary cleanup; complete published-photo erasure remains RF-37.
- consultationApi.ts has credentialed reader/detail/photo clients, but its general detail
  runtime guard is looser than the RF-12 owner guard (IDs, dates, audience, extra fields).
  RF-14 should tighten its consumed reader contract and match response IDs; do not assume
  TypeScript types authorize or validate an untrusted nominal success.
- General detail currently lacks the private-read header helper used by the owner routes;
  photo responses already set private/no-store, no-referrer and nosniff. Consuming general
  detail requires consistent protected JSON headers as part of this read increment.
- Existing keyset/query/test patterns in list_my_consultations and
  test_my_consultations_postgres.py are reusable references, not a community feed.
  Current index is owner_id/state/created_at; there is no dedicated feed index.
- Extensive tracked/untracked implementation and documentation work exists. Preserve it
  all. This grooming changes only repository documentation.

No votes/results, real terminal transitions, published-photo purge, external recipient
entry/authentication-return or native iOS delivery are inferred from existing enum values,
API policy tests or RF-12 acceptance. Other tickets' recorded gates remain independent.

## Intended outcome and inherited constraints

A registered person opens Home, discovers real open Public consultations in chronological
order, reads their purpose, opens an authorized consultation and inspects all stored photos,
then returns to browsing. Browsing is sufficient; no obligation to vote or publish follows.

Binding: DEC-009/017/018/019/020/021/022/027/028/029/033/034/035/036. Keep English
product copy, registered-only audiences, Private entirely outside the feed, immutable
publication and no expiry. Show author nickname without public profile links. Full detail
shows the complete question and optional complete context above photos, in stored photo
order, without results or a highlighted leader. No personalization, reciprocity, Skip,
public profiles, fake counters or unavailable action buttons.

## Selected direction and historical alternatives

Selected after owner response: one vertical Home feed including own open Public items in
normal chronology (Q1B), with each card showing its first photo in immutable publication
order (Q2B). Own cards are marked Your consultation and open real owner detail with Back
to Home; others open read-only reader detail through general protected APIs. My consultations
remains the dedicated own-management destination. This prepares RF-16 without inventing it.
The coordinator originally recommended Q1A/Q2A; the owner's Q1B/Q2B choices supersede those
recommendations. Overall scope/plan-finalization approval was subsequently supplied on 2026-10-15.

- Feed only: cheaper, but fails the discover-and-open outcome and leaves photos inaccessible.
- Feed plus voting/results: bundles ungroomed RF-16/RF-18 contracts and violates the requested
  increment. No vote status or invented zero counts should be added as scaffolding.
- Addressable/shareable routes now: useful later, but absorbs RF-26's recipient/private-token
  and authentication-return flow. Local Home detail is sufficient for current discovery.
- Cards with one real first photo: more immediately visual, but automatically downloads photos
  during browsing and adds media loading, resource and failure handling. Viable Q2B below.
- Own Public cards: viable Q1B; makes the feed closer to a common community view, but requires
  clear own labeling and an owner-detail entry that preserves Back to Home.

## Questions - one consolidated material batch

### Open

None. The owner confirmed Q1B/Q2B and subsequently explicitly approved the settled scope
and plan finalization on 2026-10-15. The approved plan has been created; launch is separate.

### Historical batch and alternatives

Q1 - Should the Home discovery feed include the current author's Public consultations?

- A (recommended): other authors only; own consultations remain in My consultations.
  Home focuses on discovering people to help. If only own items exist, it is honestly empty.
  Exclusion is a discovery filter, not denial of the author's existing read access.
- B: include own open Public items in normal chronology, marked Your consultation.
  Own item opens existing owner detail with Back to Home; management still verifies ownership
  server-side. Own Private items never appear. The future self-vote prohibition remains RF-16.

Q2 - How visual should a feed card be in this first increment?

- A (recommended): complete question, author nickname, publication date, Public/Open and a
  short optional context excerpt; photos load only after View consultation. Smallest coherent
  increment, lower automatic exposure/transfer, and no photo chosen as the card's representative.
- B: same information plus the first photo in immutable publication order, identified as Photo 1,
  without implying a winner. More visual discovery, at the cost of automatic protected photo
  reads and individual loading/error/retry handling. No new derivative or retained thumbnail.

The recommendations above describe the original batch, not the selected scope. The owner
confirmed Q1B/Q2B on 2026-10-15. Answering them does not approve final plan creation.

### Resolved / inherited

- 2026-10-15: `Yo elegiria 1B y 2B` confirms Q1B and Q2B. Include own open Public
  consultations without chronology changes, label them, and open owner detail with Home
  return. Show Photo 1 on every card using the first published photo; never imply a winner.
  DEC-037 records these cross-feature choices. No material question remains identified.
- 2026-10-15: after the explicit scope/plan-finalization approval question, the owner
  replied `lom apruebo - dale caña`, approving the settled scope and English plan
  finalization. The self-contained RF-14-Implementation-plan.md is Ready for implementation.
  No harness launch is authorized by this finalization response.

The user explicitly selected RF-14, authorized repository-first grooming/read-only Trello
intake and project-state updates, and retained all accepted audience/publication/lifecycle
constraints. No need to reopen those constraints, choose API names or approve routine engineering.
The proposed order RF-14 -> RF-16 -> RF-18 is verified in the 2026-10-12 reorganization notes
and the current adjacent cards, not treated as approval of any individual implementation.

## Approved observable scope (2026-10-15)

### Feed and navigation

- Replace the Home welcome-only body with a feed headed Home and a truthful introduction
  to open Public consultations. Keep four primary destinations and Home as default.
- Entering Home loads current server data. Keep existing composer dirty exit/Keep editing/
  Discard and pending-publication guards intact when Home is selected.
- Cards show full question, nickname, actual Published date in English/browser-local time,
  Public and Open. Optional context excerpt is at most 160 Unicode code points plus an
  ellipsis when shortened; complete context is in detail. Text is inert and wraps/handles RTL.
  No profile link, result, number of votes, participation status or promise of voting now.
- View consultation opens a local detail within Home. It does not use the owner management
  endpoint for another account. No share/Copy URL button or external link entry is added.
- Back to Home retains loaded pages and the selected card/scroll anchor in memory, revalidates
  that range from page one with fresh cursors and replaces it. Restore focus to the card or
  feed heading if it vanished. No hidden stale list requests may complete during detail.
- Refresh explicitly restarts at the newest first page. Load more appends older pages with
  duplicate-ID suppression. Page size 20, server bounds 1..50. Prevent concurrent duplicate
  page actions and refresh/append races. A next-page failure retries that page without losing
  successful cards. New publications appear on refresh/reentry; no live stream or polling.
- This is a vertical scroll list with explicit Load more between bounded batches, not a forced
  vote/Skip step. No infinite-loading infrastructure, scroll-history framework or browser
  persistence. Leaving Home may reset list/detail; reload/sign-in starts Home with current data.
- Confirmed Q1B includes own Public/open items alongside other authors' eligible items,
  supplies an is_owner boolean (not email/owner account ID), marks them and connects the real
  owner-read view with Home return. Do not derive ownership from nickname or client flags.
- Confirmed Q2B adds only first associated photo ID/dimensions, fetched
  through protected content APIs for visible cards with bounded requests; never preloads all
  comparison photos or generates a thumbnail file. Revoke object URLs on removal/replacement/
  exit/401/supersession. A failed image has an explicit local retry, not a broken image or a
  substitute photo. A denied image clears/removes that card's protected content and permits
  feed refresh; it must not retain denied text beside the failed image.

### Reader detail and photos

- Read current protected detail, show neutral Consultation heading, nickname, Public/Open,
  actual publication date and complete question/context before every actual ordered photo.
  No author management controls or publication-success wording for another account.
- Use a focused reader controller/view rather than mounting useOwnerConsultationDetail for
  non-owners. Reuse ConsultationTextDisplay, date formatting, photo client, status/unavailable
  patterns and narrowly useful display/enlargement code; preserve owner recovery/link behavior.
- Photos display without crop and may be enlarged in a keyboard-accessible contained dialog
  with Escape, focus containment/return and no extra data request/cache. This is inspection,
  not selection or a voting control. Reuse normalized bytes; do not introduce original downloads.
- Install only a complete loaded comparison. Partial failure revokes every created URL and
  shows a retryable detail error with Back. No temporary-uploader or cached comparison fallback.
- Provide Back and Refresh during ready, unavailable and error states, and Back during loading.
  Every refresh/reopen reauthorizes; ordinary viewing performs no mutation or participation write.

### Loading, empty, failure, sessions and state changes

- Initial loading has an accessible status; it is never rendered as an empty successful feed.
  Empty: No open public consultations yet. Own eligible Public items count toward a nonempty
  feed. Offer Refresh; existing Create/My navigation remains usable.
- Initial network/5xx/invalid-success failure has Retry. Later-page failure retains successful
  cards with page retry. Refresh/Back revalidation failure may retain earlier cards with a clear
  not-refreshed message; those cards grant no authority to bypass fresh detail/photo reads.
- Any active request's 401 clears all account-bound feed/detail/URL state and returns to the
  existing Sign in flow. Late responses after unmount/account/item change are ignored and any
  created URLs revoked. Ordinary subsequent login returns Home, not the previous recipient target.
  RF-26 owns external-link authentication return; no new pending deep-link storage here.
- Nonexistent, unauthorized, finalized, deleted or removed reader target: identical generic
  This consultation is unavailable. Clear its protected text/photos and offer Back/Refresh.
  Do not invoke an owner finalized projection for a third party or reveal the terminal cause.
- If the item changes state after listing, detail and every photo use latest request-time server
  authorization. A denied request clears content immediately in the requesting view; returning
  to/revalidating the feed removes terminal rows. Already loaded content on an idle screen may
  remain per DEC-029; no timer, push invalidation or claim to recall downloaded bytes.
- Missing authorized bytes/storage failure stays retryable, distinct from generic denied access.
  Seeded terminal states prove read/access behavior only, never real finalization or physical purge.

## Routine technical direction selected by coordinator

These engineering selections implement the proposed behavior; they are not accepted new product
decisions. They follow confirmed Q1B/Q2B and the owner's subsequent scope/finalization
approval. The approved plan fixes exact contracts. No API or application code is changed in grooming.

- Extend backend/app/consultation_service.py, api/consultations.py and schemas.py with an
  authenticated GET /api/consultations/feed?limit=20&cursor=... collection. Register its static
  route before /consultations/{consultation_id} so feed is not parsed as a UUID.
- Scope the query to Public AND open, including the current author's items, in SQL before LIMIT/cursor.
  Match the shared can_access read policy's current audience/lifecycle constraints; do not
  query arbitrary rows then filter Private/terminal items in JavaScript. Keep policy
  equivalence tested so future access-policy changes cannot silently diverge.
- Order published_at DESC then UUID DESC; fetch limit+1. Use a bounded versioned URL-safe
  cursor identifying this feed and its publication-time/UUID tuple, max 512 characters.
  Validate version/grammar/timestamp/UUID before querying and reject owner-list/feed cursor
  confusion. Cursors provide position only, never access or a stable snapshot grant.
- Return exactly items and next_cursor. Item: id, owner_nickname, question,
  context_excerpt (nullable), audience='public', state='open', published_at, is_owner and
  first_photo containing exactly id/width/height of the first immutable photo association.
  is_owner is computed server-side from the authenticated account; it is a navigation hint,
  never management authorization. Invalid/missing first-photo metadata must fail safely
  as a retryable feed failure rather than a malformed card or substituted image.
  No total result count, votes, email, owner ID, link state/token or internal storage identifiers.
- Use narrow explicit SQL columns and a join for nickname; avoid per-card general detail,
  storage reads or N+1 photo loads. The first-photo projection must also be bounded/set based.
- Reuse GET /api/consultations/{id} and /photos/{photo_id}/content. Keep registered Public and
  token-gated Private API behavior compatible; Home discovery does not connect Private entry.
  Apply private/no-store, nosniff/no-referrer to feed/general-detail successes and protected
  error responses consistently; verify no anonymous text/photo leak.
- Tighten the general detail runtime allowlist, UUIDs, UTC timestamp, canonical audience,
  exact open state, unique photo IDs/positive dimensions and requested-ID match. Do not apply
  today's authoring limits to reject older valid immutable publications. Validate pagination
  bounds/cursors and handle malformed 2xx as retryable failure without displaying its content.
- frontend/src/App.tsx, consultationApi.ts, styles.css and relevant tests are real integration
  points. New focused feed/reader components and hooks should live under frontend/src; they
  do not exist yet. Preserve Navigation, MyConsultations, OwnerConsultationDetail, composer
  guards and existing PrivateLinkControls. No new router/global-state/package is needed.
- Existing data supports this read increment; no new business table, field, migration or
  backfill is recommended for the POC. No speculative index: evaluate the bounded query on
  isolated PostgreSQL with representative data. No migration is in the approved increment;
  report a demonstrated index requirement to the coordinator rather than silently expanding
  the contract. Never edit the old migration.
- No background service, derivative, CDN, new secret, deployment change or native project.
  No browser-persistent content/IDs/token cache, logs of text/media/credentials, external
  previews or analytics writes. Existing private storage and retention are unchanged.

## Dependencies, boundaries and criterion mapping

| Capability / source criterion | RF-14 proposal or owning dependency |
| --- | --- |
| Registered discovery of newest open Public consultations | Feed query/API and Home in RF-14; RF-09/10/11 access/persistence/lifecycle |
| Read purpose and open actual photos from another author | Reader detail using RF-08 text and RF-10 media; RF-14 UI integration |
| Browse freely / no Skip | Scroll plus Load more; no participation write |
| Own or already-voted cannot vote again | No vote control at all in RF-14; RF-16 owns self-vote/one-vote enforcement and actual voted state |
| No totals/percentages/leader | Omitted from feed/detail payload and UI; RF-18 author-only aggregates later |
| Private outside feeds | Server filter even for owner/current-link holders; RF-26 owns actual Private recipient entry |
| Terminal denial after discovery | Shared RF-11 access contract now; real terminal mutations/purge remain RF-13/19/20/37 and restricted RF-32 |
| Find own publications | RF-12 management remains; confirmed Q1B also lists own Public/open items in Home |
| Web/iPhone delivery | Shared app stays compatible; owner visual gate DEC-034; real native/TestFlight gate RF-42 remains external |

RF-14 -> RF-16 -> RF-18 is a coherent incremental order, not approval of later plans. RF-16 can
attach independent confirmed voting to reader detail later, including already-voted rendering;
do not add a voted flag/table now. RF-18 integrates real author results with own management.
RF-26 later supplies shareable browser entry and post-authentication return. RF-37 and the
restricted administrator-removal subset remain required before real-user exposure; this grooming
is no deployment/rollout approval and does not waive any retained safeguard or full phase-2 goal.
RF-03/RF-06/RF-07/RF-09/RF-11 review/device gates are not silently closed by RF-12 or RF-14.

## Validation outline (future implementation; not run during grooming)

- Backend query/API: anonymous/invalid/stale sessions; two accounts; Public/Private in all
  lifecycle states; current/revoked Private tokens never add a feed row; own Public/open included;
  temporary sessions excluded; unknown state fails closed; exact payload and privacy headers.
- Real isolated PostgreSQL: more than 20 entries across multiple authors, tied timestamps and
  UUID order, insertion between pages, removal between pages, exhaustion, malformed/oversized/
  wrong-version/wrong-feed cursors and limit bounds. Inspect bounded query behavior; no claim of
  a frozen snapshot, vote race or terminal side effect. Install existing Alembic head there.
- Reader/media matrix: other registered account opens Public; direct Private ID/photo fails
  without current capability; existing valid-token API remains compatible; owner management
  still rejects non-owner; terminal detail/every photo denies with no storage touch or cause leak.
- Frontend/API: exact guards, malformed state/audience/ID/date/photos/cursor, credentialed calls,
  no data installed from invalid payload; no synthetic result/count/status or future buttons.
- UI interaction: Home default/entry, empty distinct from loading/error, retry, Load more,
  deduplication, refresh/append concurrency, detail/Back range revalidation/anchor/focus,
  component exit/account/item changes and delayed responses. Test own marker, trusted ownership
  routing/owner authorization/Home return, and bounded visible-card preview fetches with per-card
  failures/URL cleanup. Prove Private never enters Home even for its owner or current-link holder.
- Photos: complete question/context then stored order, no crop, accessible enlargement/dismiss/
  focus return; partial network/401/denial/storage failure; every URL revoked on retry,
  supersession, partial load, navigation and session loss. No fallback/cached terminal images.
- Regression: existing publication, promoted-media persistence, Private-link owner operations,
  My consultations, Profile/sign-out, composer dirty exits/pending/relinquish and Home default.
- Full relevant pytest/Ruff/format/mypy and frontend tests/format/lint/types/build/audit, plus
  Compose configuration and isolated built PostgreSQL/backend/frontend two-account smoke.
  Use existing repository commands from approved RF-12; do not run against user data.
  Publish Public/Private as A; B discovers only eligible Public, opens real ordered photos,
  reloads/signs in and sees current data; restart ordinary disposable services and repeat.
- Terminal fixtures exist only in isolated tests and prove denial/removal from reads, not real
  finalization, result generation or physical erasure. No production state setter for testing.
- Owner validates visual layout at 320px/desktop/200% zoom, safe-area/navigation clearance,
  long Unicode/RTL text and keyboard/focus under DEC-034. Codex/harness does not perform browser
  visual inspection/screenshots/zoom without a specific request. Automated accessibility/layout
  regressions remain technical checks. Actual iPhone/TestFlight remains separately evidenced.

## Readiness checklist

- [x] Current selected card consumed and readable snapshot preserved without Trello mutation.
- [x] Existing implementation, accepted decisions and relevant approved plans inspected.
- [x] Dependencies and full-card consumer boundaries identified.
- [x] Routine technical direction selected for the recommended scope.
- [x] Q1B own Public-card inclusion confirmed on 2026-10-15.
- [x] Q2B first-photo preview confirmed on 2026-10-15.
- [x] Resulting scope, exclusions and observable/error/validation behavior confirmed.
- [x] No material question remains identified.
- [x] Product owner explicitly approved finalizing a self-contained English plan on 2026-10-15.

No implementation, harness launch, tests, service changes, visual inspection, commit, push,
deployment or Trello mutation occurred in this grooming intake. Existing work is preserved.
