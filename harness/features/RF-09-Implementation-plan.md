# RF-09 - Choose audience and control the private link - Implementation Plan

## Status

`Ready for implementation`

The product owner explicitly requested this implementation plan on 2026-09-28 after resolving the
RF-09 grooming questions. This authorizes plan finalisation. Launching the external harness still
requires a separate explicit request under AGENTS.md and DEC-002. The plan delivers a reusable
foundation because no published Consultation exists yet. RF-09's full card completion requires the
later integrated gates listed below; readiness of this plan is not that completion claim.

## Source ticket

- Trello title: `RF-09 · Elegir audiencia y controlar el enlace`
- Trello URL: https://trello.com/c/vt8seQzA/12-rf-09-elegir-audiencia-y-controlar-el-enlace
- Trello list at intake: `Fase 2`, on the configured `APP - NextPost` board.
- Snapshot captured on: 2026-09-28, before the `08:01:14Z` coordinator checkpoint; Trello did not
  supply an exact read timestamp. See the full card/metadata snapshot in grooming.
- Grooming notes: `harness/grooming/RF-09-grooming.md`

The card asks authors to choose Public or Private before publication, with clear reach, and to
revoke or regenerate a Private link. Public is discoverable by registered accounts. Private is
unlisted, forwardable to another registered account and requires possession of the current link.
No unauthenticated person can see photos. Old links stop working after revocation/replacement,
finalization, deletion or administrator removal. Published audience cannot be edited.

## Objective

Define and implement the audience, private-link and access rules that the consultation composer,
publication transaction, detail/image readers, sharing and voting will consume. The author can
choose an audience deliberately; the server has one authoritative way to decide whether a current
account may read protected content or vote through a link. A Private consultation automatically
has one shareable link when it is published. Link state is checked on actual requests, with no
periodic polling. Deliver these contracts as tested reusable code now, then enforce them on real
published consultations when RF-10 and subsequent consumers exist.

## Context and current behaviour

- The stack is React/TypeScript/Vite with Capacitor, FastAPI/SQLAlchemy/Alembic and PostgreSQL.
  Authentication uses the signed HttpOnly account cookie (DEC-008). Product copy is English
  (DEC-009). Public/Private registered access, explicit no-default choice and immutable audience
  are accepted in DEC-018/022/024.
- `backend/app/models.py` has Account, PhotoUploadSession and PhotoUploadImage, with no Consultation,
  audience, published-media, vote or link row. Alembic currently ends at
  `20260922_0003_photo_uploads.py`. `backend/app/photo_service.py::validate_publication_images`
  checks an owner-bound ready image set but does not publish or promote it. Temporary reads in
  `backend/app/api/photos.py` remain owner-only and must stay so.
- RF-08 supplies normalized question/context schemas and a shared inert text presenter. RF-09's
  future access decision covers this text and photographs equally. There is no published-detail,
  voter-image or voting endpoint today.
- `frontend/src/App.tsx` and `Navigation.tsx` have local Home/Profile navigation and Home as the
  default after authentication. There is no router or shareable consultation destination.
  `frontend/nginx.conf` falls back to index.html; that alone does not handle consultation links.
- RF-07 implemented private temporary storage/cleanup; it is in implementation review pending
  integrated RF-06 and real-iPhone checks. RF-08 is completed and validated. RF-03 still requires
  acceptance review according to project state. Existing RF-08 and documentation edits in the
  worktree are uncommitted; preserve them.
- DEC-028 requires a generic unavailable response for denied/terminal links. DEC-029 settles
  automatic issuance and request-time database checks with no polling; already-loaded content may
  remain on an idle screen. DEC-030 chooses ordinary platform URL opening without new native link
  infrastructure. The owner reconfirmed RF-09 -> RF-10 -> RF-06 ordering.

## Scope

### In scope for this RF-09 implementation increment

- A controlled, accessible Public/Private selector with no preselection, accurate reach copy and
  a typed validation result for RF-06 and RF-10.
- Pure backend audience/access policy over a supplied consultation access snapshot and current
  account, including owner, audience, lifecycle and current Private capability checks. This is the
  single rule set future detail/text/image/vote services must call.
- Reusable backend Private-link creation, current-link verification, revocation and replacement
  transitions, with deterministic owner re-copy, strict token handling and testable concurrency
  preconditions. No actual Consultation table or public API endpoint is introduced in RF-09.
- Focused frontend URL construction/parsing, protected-request credential preparation, generic
  unavailable/error presentation and controlled owner link actions that consuming screens can
  connect to real endpoints. A pure navigation target helper may represent a pending same-origin
  consultation destination without changing the current product shell or RF-03 Home default.
- Matching security/privacy, component and contract tests plus documentation of the exact RF-10,
  RF-06, RF-26, RF-14, RF-16 and RF-37 integration obligations.

### Out of scope for this increment

- Consultation persistence/migration, publication endpoint or idempotency, photo promotion,
  published detail/media/vote endpoints, feed, author list, full composer and a product share
  destination. These later endpoints must use this contract; isolated RF-09 tests cannot establish
  published-access security or complete the Trello card.
- Public-link revocation, audience changes after publication, per-recipient links/grants, invitee
  allowlists, passwords, link expiry, tracking/analytics, contact import, social publishing,
  personalized feeds, new background infrastructure and broad moderation UI.
- Native universal/app links, custom iOS URL handlers, native project generation, TestFlight
  distribution and Android packaging. Ordinary platform link handling remains the phase-2 choice.

## User experience

1. RF-06 will initialize audience as unselected. The reusable control presents `Public` and
   `Private` with clear English explanations: Public is discoverable and viewable by registered
   accounts; Private is unlisted and viewable by registered accounts with a forwarded link. Neither
   permits anonymous photo viewing. Selection is explicit and remains editable until publication.
2. Attempting preview/publication with no valid selection exposes a concise field error and focuses
   the selector. The control preserves choice through preview/edit and retry. RF-10 must reject an
   omitted or invalid audience independently; there is no server default.
3. A future successful Private publication automatically makes one current link available to its
   author. Re-copying returns the same link. Public sharing uses a normal destination without a
   Private capability. The published audience never changes. RF-10 owns the atomic publication
   and initial link-state persistence; RF-26 owns copy/device-share integration and the full
   authentication return journey.
4. Owner link controls will show one of `Current link` or `Link disabled`. `Disable link` asks for
   confirmation; cancelling changes nothing. `Replace link` also confirms that the old link will
   stop working. After disable, `Create new link` may re-enable access with a fresh link. A pending
   request prevents duplicate activation. A network/lost-response error must reconcile current
   server state before claiming success or offering a supposedly current link. Use the existing
   visual language, keyboard/focus conventions and 44 px touch target baseline.
5. On opening a Private destination, an unauthenticated recipient reaches generic sign-in/register
   without protected content. A signed-in recipient with the current link sees the consultation
   when future detail readers are implemented. An invalid, revoked, replaced, finalized, deleted
   or removed target yields one generic `This consultation is unavailable.` state with a way back.
   A network/server failure has `Retry` and is not described as a revoked consultation.
6. There is no polling or timer to observe revocation. Already-loaded photos can remain on an idle
   screen. Each new protected image/text/detail fetch and vote checks current server access; a
   denied request clears content held by the requesting view. The UI must not imply it can recall
   an already-downloaded image or screenshot.
7. For an external link, use ordinary platform opening. This plan creates no `Open app` action and
   promises no automatic native-app handoff. On web, the future destination may survive the
   current tab's sign-in/register transition; an ordinary session entry still starts Home.

## Functional requirements

### FR-1 - Required audience value

Define exactly `public` and `private` as canonical lower-case API/domain values. The frontend may
use an empty value only during preparation. A shared strict backend validation function/schema
rejects missing, null, case variants, booleans, arrays, objects and unknown strings with a safe
`audience` field error. No published consultation is created with an implicit audience. RF-10
reuses the canonical value and includes it in the immutable publication/idempotency contract.

### FR-2 - Authoritative access policy

Provide a pure, independently testable decision function taking a minimal typed snapshot:
consultation ID, owner ID, audience, lifecycle/access state, Private-link active flag and generation,
requesting account ID or absent account, presented token or absent token, and intended operation.
The snapshot is supplied by a later database-owning service; RF-09 does not read incomplete models.
The result is allow/deny with a stable internal reason, but public errors collapse to the generic
unavailable response. Rule order:

- No verified account means no protected content.
- Deleted/removed/finalized/unavailable consultation means no published photos or voter detail for
  anyone, including the owner. Authorized owner outcome/history views are separate data contracts.
- For an open item, the owner can read/manage it by account ownership without a Private token;
  owner cannot vote. Ownership is never inferred from a link.
- Any other registered account can read an open Public item without a token. Any other registered
  account can read an open Private item only with its current active link. Knowing UUIDs, earlier
  visits, earlier votes or stale tokens never creates enduring access.
- Voting requires the same audience access plus RF-16's independent account/one-vote/state rules;
  this policy must not attempt to implement vote persistence or return author-only aggregates.

Every future published detail, question/context read, individual media response and vote must
invoke the policy with current database state. RF-14 applies the same audience/state constraints
server-side to feed queries. Direct IDs, copied Private image URLs or guessed endpoints cannot
bypass it. No single UI-side check counts as authorization.

### FR-3 - Single current Private link

Specify a capability that is unguessable, stable while current, reproducible for the owner after
reload, and invalidated when the stored generation/active state changes. Implement the reusable
service with these precise inputs and rules:

- Represent Private link state as `(consultation_id, generation, active)`, with generation a positive
  integer. Publication initializes generation 1 and active true. Public has no active Private link.
- Derive a 256-bit token as HMAC-SHA-256 under a dedicated `PRIVATE_LINK_SECRET`, domain-separated
  using the exact byte sequence ASCII `nextpost-private-link-v1`, one zero separator byte, the
  consultation UUID's 16 network-order bytes and an unsigned 64-bit big-endian generation. Encode
  URL-safe base64 without padding, prefixed `v1.` (exactly 43 encoded digest characters).
  Use constant-time comparison after strict syntax/length checking. A given ID/generation/key
  yields the same token for owner re-copy; another consultation or generation yields a different
  capability. Never use `SESSION_SECRET` or a bare consultation UUID as the capability.
- Keep the dedicated secret server-only. Add startup validation in `backend/app/config.py` and
  `.env.example`/Compose wiring. Permit a clearly local-development default only when
  `APP_ENV=development`; production startup must fail when the secret is absent, too short or
  equal to the documented local-development sentinel. Require at least 32 UTF-8 bytes for a
  supplied secret. In Compose, forward `${PRIVATE_LINK_SECRET:-}` as empty when unset so an
  `APP_ENV=production` deployment cannot silently inherit a local default. Do not expose it through
  `/api/application-config`, API errors or logs. Document that changing it invalidates all
  existing Private links; preserve it across ordinary deployment restarts.
- `disable`: require owner and expected current generation, set active false without changing the
  generation. `replace` while active: require owner and expected generation, increment generation
  atomically and leave active true. `create new` while disabled: require owner and expected
  generation, increment generation and set active true. Repeated/stale commands conflict and must
  not rotate again. Generation overflow fails safely. No operation revives an old token.
- Successful publication creates link state in the same transaction as the consultation. Link
  mutation uses a row lock or compare-and-swap condition in RF-10's persisted model. Reads/votes
  evaluate the state after committed mutation; concurrent operations have a serializable outcome.
  The reusable RF-09 service must accept explicit current state and expected generation now, with
  no DB commit, fake endpoint or side effects.
- Disabling/replacing is distinct from finalizing/deleting. Existing confirmed votes remain,
  open-consultation limits still apply and the owner retains management access. A newly shared link
  does not allow an account to vote twice. Terminal actions override even a valid current token.

### FR-4 - Safe link and destination transport

Use the same-origin HTTPS product destination `/consultations/{uuid}#access={token}` for Private
and `/consultations/{uuid}` for Public. In local development, allow the configured HTTP origin.
The fragment keeps the capability out of the HTTP path/query and ordinary server access logs.
Strictly parse one UUID and one exact `access` parameter; reject malformed, duplicate, oversized
or unknown fragment data. Do not interpret a supplied URL as an arbitrary post-auth redirect.
Build copyable links from a trusted application origin, never user-submitted host text.

For protected API requests, the client sends the token in `X-NextPost-Private-Link` on credentialed
requests to the configured trusted API origin over HTTPS in production. The current development
frontend/API use separate localhost origins; this remains supported through the explicit CORS
allowlist. The token is never a replacement for the signed account cookie. Future
published image loading uses authenticated fetch-to-blob as RF-07 already does, so the custom
header can be supplied; no public `<img src>` URL is issued. Cross-origin production deployment
must configure a narrow allowed origin/header without wildcard credential access. No token in
query parameters, request bodies, logs, analytics, local/session storage, cookies, external
referrers or public metadata. Avoid referrer-bearing external links from a sensitive page; future
published responses use `Referrer-Policy: no-referrer`, `Cache-Control: private, no-store` and
`X-Content-Type-Options: nosniff`.

The frontend link parser/helper may retain a pending same-tab destination and token in memory
across existing sign-in/register state transitions. RF-26/RF-10 will connect it to real routing
and session restoration; no storage-backed draft, permanent grant or open redirect is introduced.
Keep the original fragment URL during this journey so a same-tab refresh can reparse it. The
fragment belongs in the browser's address/history because it is the shareable link; do not copy it
into local/session storage. Clear the in-memory token on sign-out or account switch. A new account
opening the same still-current forwarded link must pass normal authorization checks. The link
stops working once its database state is revoked, regardless of retained browser history.

### FR-5 - Generic failures and no polling

Anonymous users see no protected text/photos before authentication. After authentication, invalid,
revoked, replaced, finalized, deleted, removed or unknown link targets return the same
non-enumerating unavailable code/message (`DEC-028`), without a target-specific reason, nickname,
question, media or aggregate results. A missing/unusable session remains the established 401
`unauthenticated` state, not an unavailable consultation. Network/server failures are retryable.
Do not add timers, polling, WebSocket or push invalidation. Every actual protected API read or vote
re-evaluates current authorization. React views must not falsely claim already loaded bytes were
removed; a denied new request clears locally retained content for that view.

## Technical approach

Build small typed policy and link-lifecycle modules without pretending a published consultation
exists. Keep the active/revoked state model explicit so RF-10 can persist it with the Consultation
in its own migration. Use an HMAC capability plus a stored generation because it gives the author
a stable, reproducible current link without storing bearer token plaintext or silently replacing
the link on each copy. The key is a deployment secret, not an account/session mechanism. No new
dependency or background service is needed; Python's standard crypto primitives suffice.

### Affected areas

- Frontend: add focused `audience` validation/control and `consultationLink` helpers/components in
  `frontend/src/` with tests. Match established styling in `frontend/src/styles.css` and reuse the
  `ApiError`/credential conventions from `frontend/src/api.ts`/`photoApi.ts`. Avoid changing the
  production `App.tsx`/`Navigation.tsx` to show a destination that has no consultation yet.
- Backend/application: add focused audience/access and private-link domain modules; extend
  `backend/app/config.py` for a dedicated key. Add a reusable strict audience schema in
  `backend/app/schemas.py` or a focused schema module. Do not register speculative consultation
  routes in `backend/app/main.py`.
- Domain/data model: typed in-memory access and link-state snapshots, no database model in this
  increment. RF-10 will add audience, link generation and active state to Consultation.
- Storage/background: RF-07 temporary images and cleanup unchanged; no new worker or file storage.
- Configuration/deployment: `.env.example`, `docker-compose.yml` backend environment and README
  document the secret/startup/restore implications. No secret in frontend build configuration.
- Documentation: this plan and `04_PROJECT_STATE.md` after actual validation. Add a compact
  consumer contract in a code-adjacent module docstring or README if needed so future harnesses
  can use the service without relying on conversation history.

### Data and migration requirements

RF-09 has no Consultation persistence and **no Alembic migration**. Do not attach audience/link
columns to upload sessions or invent a separate link table that RF-10 would need to undo. RF-10's
Consultation migration must have immutable audience and a Private-link generation/active flag,
with a check that Public rows do not expose an active Private capability. The Private generation
starts at 1 on publication; successful revoke/replace/create-new operations update that row
transactionally. IDs remain opaque UUIDs. If RF-10 chooses separate link rows for a demonstrated
reason, it must preserve this one-current-link behavior and record the reason before changing the
contract. Do not persist raw tokens.

Revocation must survive normal restarts and backups. Database restore could resurrect an earlier
active generation if paired with the same secret. RF-37's restore runbook must invalidate/rotate
the Private-link secret before restored traffic is served, or otherwise prove that no previously
revoked URL works. This can invalidate still-current links and requires author re-sharing; document
the operational consequence explicitly. A testable restore scenario is a later integrated gate,
not a reason to create a premature RF-09 database.

### API and integration requirements

No consultation API exists to extend in RF-09. Publish reusable signatures and typed results
matching this intent, rather than test-only routes:

- `validate_audience(raw) -> public | private | field error` for RF-06/RF-10.
- `can_access(snapshot, account_id, token, operation, verifier) -> decision` for RF-10 detail/media and
  RF-14/RF-16 consumers. The operation distinguishes owner management, protected read and vote.
- `current_link_token(state, secret)` and `verify_current_link(state, presented, secret)`; strict
  token syntax and constant-time comparison.
- `disable_link(state, expected_generation)`, `replace_link(...)`,
  `create_new_link(...)` return a new state or stable conflict/forbidden result without committing.
- Frontend selector returns `public | private | null` and a validation/focus contract; URL helper
  returns a canonical same-origin destination plus optional validated token.

RF-10 must create a real publication route and, later, owner-only link read/mutation and published
detail/media routes. Those routes authenticate through `get_current_account`, acquire current
database state and call these policies on every protected operation. Failed and successful
responses must not reveal the bearer capability except to the owner requesting their current link.
The future owner action API must include expected generation (and idempotency/reconciliation for
lost responses), reject cross-account mutation with non-enumerating errors, reject terminal-state
changes, and not change the audience. RF-26 will provide copy/device share and direct-link
post-authentication return; RF-14 and RF-16 apply the same access check to discovery/votes.

### Security and privacy

- The Private token is a bearer capability **plus** required account authentication. Anyone with
  a forwarded current link and registered account may access while the consultation is open.
- Use strict ID/token parsing, constant-time verification, dedicated startup-validated secret,
  generic denial and no raw token logging. Test wrong account, wrong consultation, old generation,
  disabled state and terminal lifecycle separately even though public errors collapse.
- The current account is derived from the verified cookie. Link-management writes require owner
  proof and CSRF/origin protection appropriate to the cookie-based API; do not trust an account ID
  supplied by the client. Do not mutate state on GET. RF-10 must lock/compare generations under
  concurrency and recheck lifecycle before returning content or accepting a vote.
- Generic external previews have no photos, question, context or recipient identity. The page
  must not embed protected consultation text in SEO/OpenGraph metadata or HTML before access checks.
- Never use temporary upload endpoints as published-media endpoints. Private files stay outside
  web roots. Future media responses use private/no-store and database authorization on every read.
- No per-recipient access record is created; history/outcome retention remains DEC-023, and link
  revocation alone does not rewrite previous votes or retain image copies.

## Implementation sequence

1. Add the dedicated Private-link secret setting with validation and `.env.example`/Compose/README
   wiring. Prove local default and production missing/weak-secret startup failure.
2. Implement canonical audience validation and pure access policy with typed snapshots/operations.
   Test the full account/audience/state matrix independently of HTTP.
3. Implement deterministic current-link derivation, strict verification and pure disable/replace/
   create-new transitions with generation preconditions. Test replay, stale generation, token
   rejection and restoration/key-change behavior without a database stub.
4. Add frontend audience selector and pure link URL/target helpers, plus controlled owner link
   actions/error state for future consultation detail. Reuse existing visual primitives and avoid
   adding a premature product route.
5. Write concise consumer contracts for RF-10/RF-06/RF-26/RF-14/RF-16/RF-37 covering database
   columns, atomic publication, guarded reads, vote rechecks, sharing/auth return and restore.
6. Run backend/frontend validation and configuration/container smoke. Record exactly which
   component/service contracts passed and which published/iPhone integration gates remain pending.

## Validation strategy

### Automated tests

- Audience: missing/null/invalid values and correct canonical values; explicit selector choice,
  correction, focus and persistence across test-parent preview/edit/retry; clear explanations for
  registered-only Public/Private reach, 320 px and keyboard semantics.
- Access matrix: anonymous/owner/other registered account; Public/Private; valid/current/wrong/
  missing/disabled/stale capability; open/finalized/deleted/removed state; owner management versus
  voter read and vote eligibility. No photo/text exposure when a policy denies.
- Token: deterministic re-copy, cross-consultation and generation separation, key separation,
  version/syntax/length rejection, constant-time compare path, duplicate/stale transition conflict,
  no old-token revival, no token in public error/log output. A changed key invalidates prior links.
- Client URL: canonical same-origin URLs, fragment-only Private capability, strict parse, malformed
  and duplicate rejection, no arbitrary external return URL, no accidental token in API path/query
  or public link. Protected request helper includes cookie credentials and the token header only
  when valid; 401 and generic unavailable differ from network retry.
- Controls: confirm/cancel Disable/Replace, pending duplicate prevention, Create new after disable,
  safe re-copy, stale response reconciliation, keyboard/focus/error feedback, no timer/polling.
- Existing account/profile/photo/text suites remain green; settings and config response never
  expose the key. No migration or PostgreSQL concurrency test is claimed for the RF-09 foundation.

### Manual validation and later integrated gates

- Inspect controlled components in a temporary development/test mount only: desktop/narrow/320 px,
  200% zoom, keyboard and focus, copy/confirm/error states, English reach explanations. Do not ship
  a fake consultation route or link-management screen.
- Verify local/dev secret behavior and production configuration validation. Check the built
  backend does not return the secret through `/api/application-config` or error responses. Docker
  Compose configuration must be valid. No real link endpoint can be smoke-tested yet.
- RF-10 integrated gate: with PostgreSQL, two accounts and real promoted images, publish Public
  and Private, confirm automatic Private link, owner re-copy, other-account current-link access,
  direct-ID/media denial without link, disable/replace/re-enable and unchanged votes/count limits.
  Race link replacement against image reads/votes and finalization; old links lose access on the
  next request. Use a transactionally consistent lifecycle check.
- RF-06/RF-26 gate: no preset audience; faithful preview/confirmation; same-tab link destination
  through sign-in/register; generic external preview; ordinary platform URL opening. No polling;
  already-loaded content behavior and subsequent denied requests must match DEC-029.
- RF-37 gate: finalization/deletion/admin removal immediately revoke detail/media reads and start
  no-buffer deletion. Restore cannot revive a revoked link or withdrawn image. Native iPhone and
  TestFlight shared-link/session behavior needs real-device evidence when packaging exists; it is
  not passed by this isolated increment.

### Commands

From the repository root, using the repository's existing environment:

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
docker compose build backend
```

Use `docker compose up --build -d` for a built-stack configuration/authentication smoke when the
harness is explicitly authorized to implement. Do not create or roll back an Alembic migration for
this schema-free foundation. The later RF-10 plan must add PostgreSQL migration and concurrency
commands for the persisted integration.

## Acceptance criteria for this implementation increment

- [ ] Controlled audience input begins unselected, clearly explains Public and Private reach and
      rejects absent/invalid selection without losing the form; backend rules agree with the UI.
- [ ] Reusable server policy independently distinguishes owner, registered Public reader,
      registered Private reader with current link, anonymous and denied terminal state; it has no
      path that gives an old voter/guessed ID a standing Private grant.
- [ ] Automatic Private-link issuance is specified as publication's initial state; stable re-copy,
      disable, replace and create-new transitions produce no surviving old token. No automatic
      expiry or periodic access check is introduced.
- [ ] A dedicated server-only secret, strict URL/token grammar, fragment transport and protected
      request header are implemented/tested without exposing capability or key through config,
      logs, public errors or metadata.
- [ ] Generic unavailable and distinct retryable network/session states are available to consuming
      views. A denied subsequent request clears locally held content; an idle already-loaded screen
      is not polled.
- [ ] No Consultation table, premature public route, published media endpoint, vote endpoint,
      unrelated navigation or native link infrastructure is added in this increment.
- [ ] Tests and container/config checks pass; existing account/photo/text behavior remains green.
      Pending full RF-09 Trello criteria are explicitly handed to RF-10/RF-06/RF-26/RF-37 rather
      than claimed complete on pure-policy tests.

## Dependencies and ordering

- Depends on RF-01/RF-02 signed-cookie accounts, RF-03's navigation conventions, RF-07 temporary
  photo storage and RF-08 question/context contracts. Read the complete approved RF-07 and RF-08
  plans and inspect current implementations before editing; RF-03 plan is relevant to shell UI.
- RF-10 next owns Consultation migration, publication/first-link transaction, real link-management
  and published-detail/media routes. Its plan must consume and test this policy; if its schema
  genuinely requires a different representation, return to grooming before silently changing
  semantics. RF-06 consumes selector and preview. RF-26 consumes share/return behavior. RF-14,
  RF-16 and RF-37 enforce the same access/lifecycle rule on their surfaces.
- Existing requested order is RF-09 -> RF-10 -> finalise/implement RF-06. RF-09's reusable
  increment may be independently validated, but the Trello ticket cannot be called completed
  until all directly required access, link lifecycle and device/integration checks have evidence.
- Permanent app ID/signing/Xcode/TestFlight remain the external delivery gate accepted in DEC-014.

## Risks and mitigations

- **False security from isolated policy tests:** deliver no public photo route now, preserve the
  owner-only RF-07 path, and make later real-endpoint access matrix an explicit completion gate.
- **Bearer-token leakage:** fragment-based URL, separate header, dedicated secret, no token logs,
  no external referrer and private/no-store responses. Review network traces and HTML metadata.
- **Key loss or database restore:** ordinary restart keeps the same secret; a changed key invalidates
  links. RF-37 must ensure restore never reactivates old links/media before accepting traffic.
- **Rotation/read race:** expected generation and row locking/CAS when RF-10 persists state;
  authorize each real read/vote from current state. Do not claim already-loaded bytes are revoked.
- **Auth destination loss:** explicit app-origin target helper and RF-26 integration tests; preserve
  the fragment across same-tab authentication and refresh, with no arbitrary redirect or permanent
  account grant.
- **Native scope growth:** use ordinary platform URL opening and keep signed-device validation as
  a later gate; do not add an unapproved universal-link project now.

## Harness handoff notes

- Before implementation, inspect this entire plan, AGENTS.md, all seven context files, its RF-07/
  RF-08/RF-03 dependencies and the current worktree. Preserve existing user and RF-08 changes.
- Implement exactly this reusable RF-09 increment. Do not synthesize a Consultation model or API
  solely to make a premature end-to-end demonstration. Do not modify temporary-photo authorization
  or add a product route exposing placeholder consultations.
- Use English identifiers, copy, tests and comments. Read all external responses as untrusted
  runtime input; enforce account and access rules on the server. Report exact validation evidence
  and deferred real-publication/device gates. Update project state only to the status supported by
  that evidence; do not mark the full RF-09 card completed on foundation-only evidence.
- This plan is the implementation contract. The external harness needs no Trello or conversation
  access. It must not open the Codex-only orchestration runbook or launch other agents. No commit,
  push, deployment, Trello mutation, signed native project or TestFlight invitation is authorized.

## Resolved grooming decisions

- The author chooses Public or Private explicitly; neither is preselected. Public is feed-visible
  to registered accounts; Private is unlisted, forwardable and requires account plus current link.
  Publication fixes the audience (DEC-018/022/024).
- A Private link is generated automatically at publication, ready for copying. Link state is
  checked against the database on actual entry and later protected requests. No periodic polling;
  already-loaded photos may remain visible until the user leaves or makes a new request (DEC-029).
- Invalid/revoked/replaced/terminal links give the same generic unavailable message (DEC-028).
  Revocation/rotation do not themselves finalize, delete photos or erase confirmed votes.
- Ordinary platform URL opening is sufficient for this proof of concept; no custom native app-link
  flow is requested (DEC-030). Web and invited iOS TestFlight remain phase-2 targets (DEC-014).
- The owner reconfirmed RF-09 -> RF-10 -> RF-06. RF-09 supplies reusable rules; RF-10 adds real
  consultation persistence and endpoint enforcement. The full ticket awaits integrated validation.
- The technical package selects a versioned HMAC capability, dedicated key, one current generation,
  fragment URL and request header to meet stable owner re-copy and minimize server/URL leakage.
  These are explicit implementation choices in the approved plan, not earlier product choices.
- The owner explicitly requested plan drafting on 2026-09-28. Harness launch remains separate.

## Remaining questions

None
