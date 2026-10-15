# RF-14 - Discover open Public consultations - Implementation Plan

## Status

`Ready for implementation`

On 2026-10-15 the owner selected Q1B/Q2B, then explicitly approved the settled scope
and English plan finalization with `lom apruebo - dale caña` in response to the
finalization approval question. No material question remains. This authorizes this
contract, not a harness launch. Launch requires a subsequent independent owner request.

## Source ticket

- Trello title: RF-14 · Descubrir consultas que necesitan votos
- Trello URL: https://trello.com/c/WVW0cmEp/5-rf-14-descubrir-consultas-que-necesitan-votos
- Stable short URL: https://trello.com/c/WVW0cmEp
- Board: APP - NextPost, https://trello.com/b/CgBkRg78/app-nextpost
- Trello list at intake: Próximo · completar el MVP
- Snapshot captured on: 2026-10-15, live reads completed before 15:38:06 UTC /
  17:38:06 Europe/Madrid; no exact read timestamp supplied by the connector.
- Last activity at intake: 2026-10-12T11:26:36.593Z
- Grooming notes: harness/grooming/RF-14-grooming.md

The card asks registered users to browse accessible open Public consultations newest
first, pass by without voting or Skip, prevent new votes on own/already-voted items,
hide totals/percentages/leaders and show a real empty state. Personalization, interest
ranking, weighting and following are deferred. This approved increment supplies real
discovery and opening; RF-16 owns actual voting and one-vote/self-vote enforcement.
No card completion or full phase-2 completion follows merely from this plan's readiness.

## Objective

A registered person opens Home, discovers real open Public consultations, reads the
purpose, opens a consultation and inspects its complete ordered comparison, then returns
to browsing. Home also shows the person's own open Public consultations in normal
chronology, clearly marked, with access to their authorized owner detail.

Each feed card displays its first published photo as Photo 1. All photo bytes remain
behind current account/audience/lifecycle authorization. Browsing has no participation
side effect and requires neither voting nor publication.

## Context and current behaviour

- React/TypeScript/Vite and Capacitor share the client; FastAPI/SQLAlchemy/Alembic and
  PostgreSQL supply the API/persistence. Signed HttpOnly cookie authentication exists.
- App.tsx/Navigation.tsx have Home, Create, My consultations, Profile. Home is still a
  welcome card and the initial destination after ordinary sign-in, registration and
  restoration. Destinations use local state; there is no URL router/recipient entry.
- RF-12's approved author-recovery increment is Completed and validated with recorded
  owner acceptance on 2026-10-15. MyConsultations.tsx, OwnerConsultationDetail.tsx and
  useOwnerConsultationDetail.ts implement list/tabs, owner recovery, minimal finalized
  summary, protected photos and current Private-link management.
- Owner detail currently chooses Back wording from success/returning variants. It must
  gain a narrow Home return context without showing publication success or changing
  My consultations/PublishedSuccess defaults. Its owner-read API remains authoritative.
- ConsultationComposer.tsx implements real publication and dirty/pending navigation
  protection. Preserve the upload-session relinquish-before-unmount and Retry behavior.
- Consultation/ConsultationPhoto persist owner, question/context, immutable audience,
  lifecycle, publication date and ordered processed-photo associations. No vote,
  aggregate, declaration or participant-outcome model or terminal transition date exists.
- consultation_service.py and api/consultations.py provide publication, capacity, owner
  list/detail, general open detail/photo and owner Private-link operations. No feed,
  real finalization/deletion/removal operation or published-photo purge exists.
- General detail/photo already authorize registered non-owner Public access via
  consultation_access.py. Private readers need the current link. The owner management
  API independently checks ownership, including for a Public reader or valid token holder.
- consultationApi.ts has general reader clients, but their detail guard is looser than
  RF-12's owner guard. Tighten the consumed general contract without narrowing valid
  Private API authorization. General detail needs consistent protected JSON headers;
  existing photo responses already disable caching and referrers.
- Existing owner-list keyset code/tests supply patterns, not a community feed. Current
  index is owner_id/state/created_at; existing data supports a bounded POC read query.
- The worktree contains extensive uncommitted tracked/untracked user and dependency
  implementation. Preserve it. Historical observations in earlier plans predate this code.

Binding decisions include DEC-004–009 (stack/session/copy), DEC-016–024 (photos, no expiry,
immutable publication, chronology, identity, retention and registered audiences),
DEC-027–033 (complete detail text, generic denial, request-time access, persistence and
lifecycle), DEC-034 (owner visual validation), DEC-035–037 (community/Home/own previews).

## Scope

### In scope

- Home chronological feed of only open Public consultations, including own items.
- Full question, author nickname, short context excerpt, actual publication date,
  Public/Open labels, own marker and one real first-photo preview per card.
- Bounded keyset pagination, Load more, Refresh, truthful empty/loading/error states.
- Other-author read-only detail with full question/context, ordered protected photos,
  accessible enlargement, Refresh and Back to Home.
- Own-card entry to existing authorized owner detail with neutral wording and Home return.
- In-memory feed range/anchor/focus recovery with current-state revalidation on Back.
- Robust preview/detail request and object-URL ownership, session cleanup and late-response
  protection, current authorization and protected-response/runtime validation.
- Focused tests, full relevant quality checks and isolated PostgreSQL/built-stack evidence.

### Out of scope

- Votes, selecting a vote, participation/voted status, vote counts (including fake zero),
  percentages, results, leader/winner, final declaration or participant history.
- Real finalization/deletion/removal, state setter, published-photo erasure or retention changes.
- Private discovery, external recipient routes, Public share/Copy URL controls, private-token
  entry, post-authentication destination return, router or native deep links (RF-26).
- Search, filters/categories, ranking, following, Skip, forced reciprocity, comments,
  public profiles, user-facing moderation or administration.
- Editing published content, drafts, expiry/duration/countdown/reopening or lifecycle dates.
- New business persistence, migration/backfill, stored thumbnail/derivative/original,
  photo backup/versioning, CDN, worker, queue, polling, push or offline cache.
- New package, secret, deployment service, native project/signing or TestFlight distribution.

## User experience

### Home feed and navigation

Replace the welcome-only Home body with heading Home and concise truthful copy about
open Public consultations. Preserve Home/Create/My consultations/Profile order and
Home default. Do not promise voting is available in this increment. Existing composer
dirty exits still confirm Keep editing/Discard; pending publication cannot be interrupted.

Every card shows the complete question, author nickname, Public, Open, Published date
and optional context excerpt. Excerpt is the first 160 Unicode code points of normalized
stored context, followed by an ellipsis only when shortened; absent context is omitted.
Do not reapply today's publication text limits to stored immutable text. Render inert
text with long-word wrapping, paragraph handling and direction support. Nicknames do
not link to public profiles. Dates use English/browser-local formatting with a time element.

Show first immutable published photo, with visible Photo 1 label and accessible alternative
text. Preserve proportions with no forced crop. Never imply this photo is a winner or
that the author chose it after publication. Load preview bytes when the card is visible;
show a local loading state until ready. A retryable media failure has a local Retry photo
action; View consultation remains available for a fresh authorized complete read.

Mark own cards Your consultation without reordering them. View consultation on an own
card opens real owner detail with heading Your consultation and Back to Home. Others
open the reader view with heading Consultation. Do not trust a client marker as management
authority. Own Private consultations remain accessible solely through existing management
or future authorized link entry, never through Home.

Initial entry loads 20 cards. Load more appends older cards; hide it when next_cursor is
null. Refresh restarts from page one and resets the loaded range. Disable repeated pending
actions and prevent refresh/append overlap. Scrolling requires no vote or Skip. New
publications appear on refresh/reentry, with no background refresh or synthetic activity.

On opening detail, retain only the feed's in-memory metadata/range/anchor; cancel or
invalidate list/preview work and revoke preview URLs. On Back, re-fetch from page one
using fresh cursors for at most the previously loaded number of pages, stopping on
exhaustion. Replace the range, never merge stale pages into it. Restore the selected
card's scroll anchor and focus to its View action; if absent, use the feed heading.
Retained rows during a retryable revalidation failure must be identified as not refreshed
and cannot authorize photo/detail access. Reload/sign-in starts Home fresh; leaving Home
for another primary destination may reset its range/detail. No history/storage framework.

### Reader detail and photographs

Fetch general protected detail by ID, then its actual ordered photo bytes. Show nickname,
Public/Open, actual publication date and complete question then optional complete context
above photos using ConsultationTextDisplay. Do not truncate/collapse detail context.
Do not show author management controls or publication-success messages for another author.

Install only a completely loaded comparison. Do not render a partial comparison after a
failed photo request or substitute a preview/upload/cached photo. Show usable error and
Retry/Back, revoking all partial URLs. Ready/unavailable/error views offer Back and Refresh;
loading offers Back so the user can leave without waiting.

Photos preserve their stored order and proportions and can be enlarged using already
loaded normalized bytes in a contained accessible dialog. Support Escape/Close, focus
containment and return, inert background interaction and readable labels. No vote selection
or original-download action. Reuse a small image presenter/enlargement helper where useful;
do not mount the uploader or introduce another image lifecycle. Own open detail reached
from Home must support equivalent inspection without regressing its other entry contexts.

### Loading, empty, errors and sessions

- Initial feed loading communicates status and keeps primary navigation usable.
- Empty success: No open public consultations yet. Offer Refresh. Own eligible Public
  rows make the feed nonempty. No sample cards, fake activity or empty-on-error rendering.
- Initial network/5xx/invalid-2xx failure: Could not load consultations, with Retry.
- Failed Load more retains successful cards and retries the same next page. Failed Refresh/
  Back revalidation may retain prior cards with explicit not-refreshed feedback and Retry.
- A denied preview clears that card's protected text/image, revokes its URL and leaves a
  generic unavailable placeholder with Refresh feed; it is not a successful-empty feed.
- Missing authorized photo bytes/503/network stays retryable; never describe it as deletion.
- Any current feed/preview/detail/owner request's 401 invalidates account-bound state,
  revokes all URLs and invokes the existing Sign in transition. Old requests cannot restore
  content or log out a later account after navigation/unmount/account change.
- Unknown/unauthorized/finalized/deleted/removed third-party detail/media receives the
  same generic This consultation is unavailable, with no text/photos/terminal cause.
  Clear current protected content before showing unavailable. Do not call an owner terminal
  projection to find a reason. Own entry retains the existing minimal finalized projection
  if the owner API now reports finalized; Back revalidation removes that item from Home.
- Each refresh/reopen/photo request checks current server state. Already-loaded bytes may
  remain on an idle screen under DEC-029. No timer/push or promise to recall downloaded bytes.

## Functional requirements

### FR-1 - Server-scoped discovery

Authenticate every page with the verified cookie account. Apply audience=public AND
state=open in SQL before pagination; include current-owner rows with no special ranking.
Never list Private, terminal or temporary upload-session rows, even for an owner/current
Private-token holder. These are discovery rules, not a change to existing read authorization.
Keep their equivalence to current shared read policy tested and explicit.

### FR-2 - Stable bounded pagination

Order published_at DESC, id DESC; query limit+1 to derive next_cursor. Default limit 20,
minimum 1, maximum 50. Subsequent page keys are strictly below the cursor tuple. Cursor
uses URL-safe unpadded base64 JSON with exactly version `feed-v1`, UTC publication-time
value and canonical UUID, maximum 512 characters. Require valid alphabet, tuple shape,
version, actual timestamp/calendar and UUID; reject owner-list cursors, malformed/oversized
input with safe 422 validation_error. Cursor contains no token/content/account or access grant.
No snapshot table/signature is required. Concurrent additions can await Refresh; terminal
changes remove rows. Client appends deduplicate within/across pages and reject nonprogressing
cursors safely rather than loop. Refresh/Back collection is replaced using fresh cursors.

### FR-3 - Accurate card projection

Return only the explicit feed fields defined below. Compute is_owner from the verified
account and selected owner_id internally; do not return owner ID. first_photo identifies
the lowest stored ordinal association, not the temporary image ID, arbitrary association,
client photo order or inferred leader. Obtain nickname and first-photo metadata set-wise
without one general-detail/storage query per row. No file reads during feed JSON projection.
Corrupt/missing first-photo association/metadata fails safely as retryable feed failure;
do not silently pick another photo, shorten the page as though exhausted or expose bad IDs.

### FR-4 - Separate reader and owner authority

Use general protected detail/media for other authors. A focused reader view/controller owns
its requests and never loads owner links or management summaries. Own-card navigation uses
the existing owner API, which must check current ownership regardless of is_owner. Add a
narrow explicit Home back label/context to owner presentation while preserving existing
PublishedSuccess and My consultations wording and callbacks. No new mutation is introduced.

### FR-5 - Preview resource ownership

Fetch visible-card previews with at most four active preview requests per feed instance,
deduplicated by consultation/photo/request generation. Use IntersectionObserver or a small
equivalent visibility boundary with a safe fallback; no unbounded eager page/photo preload.
Release preview URLs when cards leave visibility, are replaced/removed or feed becomes hidden;
newly visible cards may refetch. Opening detail cancels/invalidates preview work. Late returned
URLs are revoked even if never installed in state. No global/persistent image cache.

### FR-6 - Current access, strict payloads and cleanup

Detail/photo authorizations use current persisted state and exact photo association on
every request. Protected errors do not disclose cause or content. Validate every client
response at runtime, require requested-ID match and exact state/audience/fields/metadata.
All-or-error comparison, distinct denial versus storage/network error and explicit URL
ownership apply to partial failure, Retry, denied access, item/account change and unmount.
All GET behavior is read only, with no viewed/participation record or resource mutation.

### FR-7 - Accessible truthful product

Use English copy, existing light styling, semantic list/headings/time/status/alerts,
44px controls, keyboard/focus/return semantics, safe-area and fixed-navigation clearance,
long Unicode/RTL wrapping and contained image proportions. No fake votes/results or
disabled future-action scaffolding. DEC-034 reserves visual acceptance for the owner.

## Technical approach

Extend existing consultation query/API/schema boundaries and compose a focused Home
feed and reader detail within the local destination model. Reuse real protected photo
clients, shared text/date presentation and narrowly useful detail-photo presentation.
Keep list/preview/detail request generations distinct so one lifecycle cannot revive or
cancel another accidentally. Avoid broad owner/composer/auth refactors.

### Affected areas

- Backend: backend/app/consultation_service.py, backend/app/api/consultations.py and
  backend/app/schemas.py; related access/API/query tests under backend/tests.
- Frontend: frontend/src/App.tsx, consultationApi.ts, OwnerConsultationDetail.tsx,
  styles.css and their tests. Add focused feed/reader/controller/preview components
  under frontend/src; they do not yet exist and names may follow local conventions.
- Reuse ConsultationTextDisplay.tsx, consultationDate.ts, ConsultationUnavailable.tsx,
  owner detail/controller, API cookie conventions and small existing enlargement patterns.
  Preserve MyConsultations.tsx, PublishedSuccess.tsx, PrivateLinkControls.tsx and composer.
- Domain/data: current models, canonical lifecycle and access policy; no new persisted data.
- Storage/background: unchanged private normalized files; client URL ownership only.
- Configuration/deployment: no package, setting, service, volume or native project change.
- Documentation: README implemented-flow/boundary guidance and evidence-based project state.

### Data and migration requirements

No migration, backfill, new column or speculative feed index is part of this POC increment.
Do not edit migration 20260928_0004 or reinterpret published_at as another lifecycle date.
Inspect the bounded query with representative isolated PostgreSQL data; report concrete
performance problems rather than silently expanding schema scope. A demonstrated need
for indexing or another data change returns to the coordinator before changing this contract.

Preserve account/consultation/photo associations, immutable content, current link state,
source-session deduplication and promoted-photo cleanup protection. No derivative or copied
text is persisted for discovery/history. UTC timestamps must serialize unambiguously once,
never by appending Z to an already offset-bearing value.

### API and integration requirements

Add GET /api/consultations/feed?limit=20&cursor=... before the dynamic UUID detail route.
Authentication uses get_current_account, with no target account/owner/state/audience filter
parameter. A Private token cannot broaden the feed. 200 contains exactly items and next_cursor.
Each item contains exactly:

```text
id: canonical UUID string
owner_nickname: string
question: string
context_excerpt: string|null (up to 160 code points, plus ellipsis only if shortened)
audience: "public"
state: "open"
published_at: valid UTC ISO timestamp string
is_owner: boolean
first_photo: { id: canonical consultation-photo UUID, width: positive integer, height: positive integer }
```

Empty collection: items=[] and next_cursor=null. No total count, vote state/count, email,
owner account ID, original context, token/generation, storage key, source session or filename.
Malformed first-photo metadata is a safe retryable 503 unavailable, not an empty success.
Missing/invalid/stale session uses existing 401 unauthenticated. Invalid query/cursor uses
422 validation_error without echoing payload/parser internals.

Reuse GET /api/consultations/{id} with exactly id, owner_nickname, question, context,
audience, state, published_at, photos; each photo exactly id/width/height. General API
continues to allow authorized Public/Private reads; Home reader accepts Public/open only.
Validate UUIDs, date, literal open, canonical audience, nullable context, unique photo IDs,
positive dimensions and response-ID match. Do not impose today's authoring maxima on
stored valid publications. Nominal success with unknown/extra/invalid content is retryable
failure and cannot be rendered. Preserve existing valid owner/publication/API clients.

Photos still use GET /api/consultations/{id}/photos/{photo_id}/content with credentials.
No token is needed for Home Public photos; never expose a storage URL or temporary upload
endpoint. Retain 401/404 consultation_unavailable/503 unavailable distinctions. For own
cards consume GET /api/my-consultations/{id}; server ownership remains mandatory.

Feed, consumed general detail and photo responses must consistently carry Cache-Control:
private, no-store; Referrer-Policy: no-referrer; X-Content-Type-Options: nosniff. Apply these
also to their protected 401/422/404/503/error paths, using a scoped existing handler or small
consistent boundary rather than unintentionally changing unrelated public endpoints.

### Security and privacy

- SQL eligibility precedes projection; every subsequent request reauthorizes current state.
- is_owner is a hint only; management read still verifies verified-account ownership.
- Private never leaks via feed fields, preview requests, counts or a supplied capability.
- Images stay outside static roots; browser holds only credential-fetched normalized blobs.
- Render user text inertly; no HTML/Markdown execution, automatic links or public profile route.
- No content/token/cookie/storage/byte logging, persistent browser content or offline access.
- No anonymous/SEO/OpenGraph protected text or image preview; no new external share destination.
- Denied new requests clear protected view content; physical deletion is never inferred from denial.
- Preserve current token header/fragment and owner link operations; do not mint links on reads.

## Implementation sequence

1. Inspect dirty baseline/dependencies; add strict feed projection/cursor schemas and query tests.
2. Implement Public/open SQL page with set-based nickname/first ordinal photo metadata and
   server-derived ownership. Register static route before UUID route and safe headers/errors.
3. Tighten consumed general detail runtime validation and exact-ID handling; add strict
   credentialed feed client without changing Private authorization semantics.
4. Build Home list/pagination/refresh state and bounded visible-card preview ownership.
5. Add focused reader detail/all-photo controller and accessible no-crop enlargement.
6. Add own-card owner detail Home return context; preserve other owner/success contexts.
7. Integrate Home replacement, Back range/anchor/focus revalidation, session-loss and
   supersession protection while retaining composer dirty/pending behavior.
8. Complete failure/privacy/resource/accessibility regressions and existing-suite checks.
9. Run isolated PostgreSQL query and built two-account read/preview/restart smoke.
   Report exact evidence, remaining owner visual/device gates and limited increment status.

## Validation strategy

### Automated tests

- Feed/API: two accounts plus anonymous/invalid/stale sessions; both audiences/all four
  lifecycle states; own Public included; own Private excluded; current/revoked tokens never
  add a row; temporary preparation excluded; exact fields/headers and static route dispatch.
- Query/cursor: >20 rows across authors, tied publication times/native UUID ordering,
  exhaustion, insertion/removal between pages, strict bounds/oversize/alphabet/tuple/version/
  timestamp/UUID, owner cursor rejection, tampered cursor never grants access. Assert set-based
  projection/no storage access, first published ordinal rather than arbitrary photo.
- Corrupt first-photo metadata produces retryable failure without substitute/leaked key.
  Use actual isolated PostgreSQL with current Alembic head, not SQLite-only query evidence.
- General detail/media: Public non-owner works, Private without capability denied, valid
  Private API contract remains, cross-consultation photo IDs denied before storage, every
  terminal state generically denies for owner and others on protected content routes.
- Client guards reject wrong/extra/missing fields, response ID mismatch, unknown state,
  invalid audience/date/UUID/photo IDs/dimensions/cursor and malformed nominal successes.
- Home: default after ordinary auth, loading/empty/errors, own marker/chronology, Load more
  within/across-page deduplication, pending duplication, refresh/append race, nonprogressing
  cursor, fresh range collection/anchor/focus on Back and retryable revalidation failures.
- Preview: visibility/bounded concurrency, Photo 1/contain rendering, local failure/retry,
  denied card clearing, no all-photo preload, and every URL revoked on invisible/hidden/
  superseded/unmount/401 paths including a late URL not installed in state.
- Detail: full question/context before ordered photos, all-or-error media, no crop,
  enlargement keyboard/focus, loading Back, Retry/Refresh, generic denied text clearing,
  missing-bytes retry, no management call from reader, no data revived after account/item exit.
- Own detail: server ownership checked despite forged is_owner, Home return context and
  existing minimum finalized reconciliation preserved. Published/My defaults remain unchanged.
- No vote/result/counter/Skip/terminal/share scaffolding, persistence or activity invention.
- Regression: publication Retry/pending/relinquish, composer dirty Home exits, temporary
  cleanup/promoted persistence, owner management/Private links, My consultations, auth/profile.
- Full format/lint/types/tests/build and meaningful accessibility/layout regressions.

### Manual validation

- Use isolated built frontend/backend/PostgreSQL, two accounts and actual processed photos.
  A publishes Public and Private; B discovers/open reads only Public. A sees own Public marker
  and authorized detail with Home return, never own Private in Home. Both still recover own
  collections. Initial empty and missing-media retry are truthful.
- Exercise real protected preview/detail reads and no anonymous/static access; exact photo
  order, no management grant for B, credentials and private headers. Reload/sign-out/sign-in
  returns Home with current data; ordinary disposable-service restart preserves discovery/media.
- Use isolated seeded terminal fixtures for list removal and denied next reads, not a
  production state setter. These fixtures do not prove real finalization, outcomes or erasure.
- Owner performs visual acceptance at 320px/desktop/200% zoom, safe-area/navigation clearance,
  long Unicode/RTL and keyboard/focus/enlargement under DEC-034. Codex/harness must not perform
  browser visual inspection/screenshots/zoom unless specifically requested by the owner.
- Nonvisual DOM/HTTP checks may supplement technical evidence. Actual iPhone/TestFlight and
  other tickets' independent gates remain explicit; do not infer device proof from web tests.

### Commands

From repository root with the existing environment:

```powershell
.\.venv\Scripts\python -m pytest backend\tests
.\.venv\Scripts\python -m ruff check backend
.\.venv\Scripts\python -m ruff format --check backend
.\.venv\Scripts\python -m mypy backend\app
Push-Location frontend
npm test
npm run format:check
npm run lint
npm run typecheck
npm run build
npm audit --audit-level=high
Pop-Location
docker compose config --quiet
docker compose build backend frontend
```

Set TEST_DATABASE_URL only to a disposable isolated PostgreSQL database. Apply existing
head using the configured isolated database URL and:

```powershell
.\.venv\Scripts\python -m alembic -c backend\alembic.ini upgrade head
```

Use a separate Compose project/override and disposable DB/private-photo volumes for smoke,
following existing harness/validation patterns without resetting active data. Existing
Compose lifecycle commands include up --build -d and restart. No migration downgrade,
active-storage cleanup or Docker repair is needed. Report skipped/unavailable tests as
unverified, never passed. New checks are run only after authorized implementation.

## Acceptance criteria

- [ ] Home remains default and shows only real Public/open rows in newest-publication/UUID order.
- [ ] Own eligible rows appear in normal chronology, marked Your consultation; own/others'
      Private and all terminal/temporary rows never appear, even with a current Private token.
- [ ] Every card shows full question/nickname/date/Public/Open/optional bounded excerpt and
      the actual first immutable photo as Photo 1 without implying a result.
- [ ] Protected visible-card previews have bounded concurrent reads, no crop, local loading/
      Retry and denied-content cleanup; all object URLs are released on every exit/stale path.
- [ ] Bounded Load more/Refresh and Back range revalidation avoid duplicate cards/races and
      recover anchor/focus without persistent navigation/content or polling.
- [ ] Another author's card opens current authorized read-only detail with complete text
      above all ordered photos, accessible enlargement and usable Back/Refresh/Retry.
- [ ] Own card opens independently authorized owner detail with Home return; existing
      My consultations, PublishedSuccess and Private-link behavior is preserved.
- [ ] Loading/real empty/initial and later-page failures/media failure/denial/401 are distinct;
      no partial comparison, cached fallback, fake empty/success or terminal-cause disclosure.
- [ ] Feed/general-detail/photo payload/header/runtime validation is strict, account access
      is enforced server-side and no unauthorized photo request touches storage.
- [ ] Session loss and account/item/unmount supersession clear protected state and cannot
      revive content or transfer management authority through is_owner/cursors.
- [ ] No vote/count/result/status/leader/Skip/terminal action, Private discovery, recipient
      routing, new persistence/migration/package/derivative/infrastructure is introduced.
- [ ] Composer Home dirty/pending guards, publication handoff, owner recovery and auth
      regressions pass; immutable content and no-expiry behavior remain unchanged.
- [ ] Full quality checks, isolated PostgreSQL query and built two-account/restart smoke
      have recorded evidence; owner visual and actual device gates remain separate.
- [ ] Documentation states completion only for this increment; full-card consumers and
      required real-user-exposure safeguards remain explicit. No unauthorized external mutation.

## Dependencies and ordering

Read complete approved RF-03/RF-06/RF-07/RF-08/RF-09/RF-10/RF-11/RF-12 plans and inspect
their current code. RF-01/02 supply cookie accounts; RF-03 navigation; RF-06 composer;
RF-07 private normalized bytes; RF-08 full-text presentation; RF-09 access/link policy;
RF-10 persistence/protected detail/media; RF-11 lifecycle; RF-12 owner recovery.
Historical missing-code/environment observations are not current implementation evidence.

RF-14 -> RF-16 -> RF-18 remains the discovery/vote/author-results sequence. RF-16 later
owns independent confirmed voting, self-vote/one-vote rules and already-voted rendering;
RF-18 owns author-only aggregates. RF-26 owns recipient routing and post-auth return.
RF-13/19/20/37 and restricted RF-32 removal own terminal mutations/erasure; tests here
must not claim them implemented. RF-21 owns participant history; RF-42 owns integrated
web/iOS delivery. RF-03/06/07/09/11 retain independently recorded review/device gates.
Published-photo cleanup and restricted removal remain required before real-user exposure;
this development increment does not approve deployment or waive the full phase-2 finish line.

## Risks and mitigations

- Private leak through common list/preview: Public/open SQL projection before pagination,
  exact fields, no capability-based discovery and per-photo current authorization.
- Owner hint becomes privilege: server owner API check, forged-flag and two-account tests.
- First-photo bias/mislabel: stored ordinal, Photo 1 label, no winner/count/selection implication.
- Automatic image reads grow memory/transfer: visible-card four-request bound, URL cleanup,
  no all-photo eager preload/cache or new derivative.
- Stale/late requests restore denied content: separate generations/owned URLs, denied clears,
  explicit session/item/unmount and partial-failure coverage.
- Back/refresh page races: fresh-cursor bounded replacement, dedupe and anchor/focus fallback.
- General-reader integration weakens Private/owner rules: preserve authorization, tighten
  only response handling/headers and run existing access/link/publication regressions.
- Overclaiming lifecycle or device proof: isolated fixture labels and explicit consumer/owner
  visual/real-device gates; no real terminal write or deployment in this increment.

## Harness handoff notes

- Read AGENTS.md, all seven source-of-truth context documents, product reorganization,
  RF-14 grooming, this plan and the complete named approved dependencies before editing.
- Preserve extensive tracked/untracked work. No reset, broad refactor, historical migration
  edit, new dependency or unrelated cleanup. Stop/report any conflict with accepted code/contracts.
- Implement only the approved discovery increment in English, with exact validation evidence.
  The harness needs no conversation history or Trello access; this plan is self-contained.
- Do not commit, push, deploy, mutate Trello, send invitations, generate native projects,
  operate destructively on active data or launch other agents. External agents must not open
  the Codex-only orchestration runbook. Coordinator launch requires a subsequent owner request.
- Owner performs visual validation under DEC-034; automate technical/accessibility checks
  and report remaining visual/device gates honestly without taking screenshots or inspecting zoom.
- Update project state only from supported implementation/review evidence. Ready is not completed.

## Resolved grooming decisions

- Q1B accepted on 2026-10-15: own Public/open items remain in normal Home chronology,
  identified as own and opening authorized owner detail with Home return.
- Q2B accepted on 2026-10-15: one real first-photo preview per card, Photo 1 in immutable
  order, with protected access and real load/retry/denial handling. Recorded in DEC-037.
- Registered audiences, Private unlisted, immutable publication, no expiry, nickname-only
  identity, full detail text, generic denial, request-time revocation and owner visual gates remain.
- Coordinator resolves routine API/query/cursor/components/URL ownership and keeps the local
  navigation model. No vote/result/terminal/recipient-flow scaffolding or new business persistence.
- After the settled scope and explicit finalization question, the owner replied
  `lom apruebo - dale caña`, approving scope and plan finalization. This does not launch the harness.

## Remaining questions

None
