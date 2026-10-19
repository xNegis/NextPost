# NextPost

NextPost is a web-first application packaged for iOS and Android with Capacitor. Product work is
driven by Trello tickets and the repository-owned grooming and implementation workflow documented
in `AGENTS.md` and `harness/context`.

## Stack

- React, TypeScript, and Vite frontend.
- Capacitor configuration for future iOS and Android projects.
- FastAPI backend with SQLAlchemy and Alembic.
- PostgreSQL database.
- Docker Compose development stack.

## Run the complete stack

Copy `.env.example` to `.env` if you want to override the safe local defaults, then run:

```powershell
docker compose up --build
```

`SESSION_SECRET` signs the `HttpOnly` session cookie. The checked-in default is for local
development only; provide a strong secret in any shared or production environment.

`PRIVATE_LINK_SECRET` is a server-only secret that derives private consultation links. It is never
exposed through the configuration API, logs or error responses. Provide a strong value (at least
32 bytes) in production; the checked-in local-development default is accepted only when
`APP_ENV=development`, and changing the secret invalidates every existing private link. Compose
forwards the variable empty when unset so a production deployment cannot silently inherit the
local default.

Open:

- Frontend: http://localhost:4173
- API documentation: http://localhost:8000/docs
- Liveness: http://localhost:8000/api/health
- Database readiness: http://localhost:8000/api/ready

Stop the stack with:

```powershell
docker compose down
```

The PostgreSQL and private normalized-photo volumes are retained. Use
`docker compose down --volumes` only when deliberately discarding both local data stores.

Run the restricted photo cleanup and status command inside the backend container with:

```powershell
docker compose exec backend python -m app.cleanup
```

It retries queued deletions and exits unsuccessfully when a deletion has remained pending beyond
the configured alert age. Before downgrading past the RF-07 migration, run this command and make an
explicit operator decision about any remaining files in the private photo volume; a database
downgrade does not make that volume public or silently remove it.

## Consultation text limits

`CONSULTATION_QUESTION_MAX_LENGTH` (default `120`) and `CONSULTATION_CONTEXT_MAX_LENGTH` (default
`500`) bound consultation question and context text. Both are startup-validated positive integers;
the question maximum must accommodate the accepted default question (27 code points). A restart
applies changes, and the effective values are exposed through the authenticated
`GET /api/application-config` response. The reusable question/context validation lives in
`backend/app/consultation_text.py` (server) and `frontend/src/consultationText.ts` (client), which
share the same normalization rules and Unicode code-point counting.

RF-06 should initialize its own question/context state once with `initialConsultationText()`, keep
the raw values while editing and previewing, and use `ConsultationTextFields` with
`validateAndFocus()` before progression. The parent owns server field errors and clears each one
through `onServerErrorClear` when that field changes. `useConsultationConfig` exposes limits only
while its status is `ready`; a failed fetch can be retried without resetting the parent's text.
Render validated normalized values with `ConsultationTextDisplay` above the photos. RF-10 must run
the backend text validation under current server limits before atomic publication. These helpers
do not create a draft, publication endpoint or consultation read route.

## Audience and private links

RF-09 defines the reusable audience, access and private-link contracts. RF-10 now persists
consultations and enforces those rules on real publication, detail, media and link endpoints; the
contracts remain the single policy every protected request must call with current database state.

`backend/app/audience.py` (and `frontend/src/audience.ts`) define the canonical lower-case
`public`/`private` values. The composer starts unselected; `validate_audience` rejects missing,
case variants and non-string values with a safe `audience` field error. `public` is feed-visible to
registered accounts; `private` is unlisted and requires a registered account plus the current link.
Neither audience allows anonymous photo viewing, and publication fixes the audience.

`backend/app/consultation_access.py` provides the single `can_access` decision function. RF-10,
RF-14 and RF-16 must call it with current database state on every protected detail, text, image and
vote request; the decision reason is internal and denied reads collapse to a generic unavailable
response (`DEC-028`), while a missing session remains the 401 `unauthenticated` state.

`backend/app/private_link.py` derives the single current private-link capability as a versioned
HMAC-SHA-256 token (`v1.` + 43 URL-safe base64 characters) from the consultation UUID, a positive
generation and `PRIVATE_LINK_SECRET`. It exposes `current_link_token`, `verify_current_link` and
pure `disable_link`/`replace_link`/`create_new_link` transitions. RF-10 persists
`(consultation_id, generation, active)` with the Consultation, initializes generation 1 on
publication, and applies transitions under a row lock. `frontend/src/consultationLink.ts` builds and
strictly parses same-origin `/consultations/{uuid}` destinations (the Private capability travels in
the `#access={token}` fragment) and prepares credentialed requests with the
`X-NextPost-Private-Link` header only for a valid capability.
`AudienceSelector`, `PrivateLinkControls` and `ConsultationUnavailable` are controlled components
for RF-06/RF-26 to wire to real endpoints; none of these helpers exposes a consultation route
or drafts any data.

## Consultations and publication

`backend/app/consultation_service.py` owns the durable consultation lifecycle and exposes an
authenticated API through `backend/app/api/consultations.py`:

- `GET /api/consultation-capacity` — the current owner's open count, limit and `can_start`. Advisory
  only; it reserves no slot.
- `POST /api/consultations` — atomically publish one consultation from an owned active upload
  session. One transaction validates text/audience, locks and verifies ordered ready photos,
  enforces the configured open cap, creates the consultation and ordered photos, consumes the
  upload session and revokes unselected temporary photos. The upload-session UUID is the operation
  identity: retrying the same normalized payload returns the same consultation, and a changed
  payload conflicts without editing or duplicating.
- `GET /api/consultations/{id}` and `GET /api/consultations/{id}/photos/{photo_id}/content` —
  protected detail and media reads that build one `AccessSnapshot` and call `can_access` on every
  request. Private consultations require the current link (the `X-NextPost-Private-Link` header).
  Media responses are `private, no-store`, `nosniff` and `no-referrer`.
- `GET /api/consultations/{id}/private-link` plus `POST .../private-link/{disable|replace|create}`
  (owner-only) — persisted link read and generation-transition mutations with expected-generation
  preconditions.

State-changing consultation routes reject requests whose `Origin` header is not a configured trusted
origin (a missing `Origin`, as from a native client, is allowed). Publication keeps
`PhotoUploadImage` as the single private-file ledger; promotion reuses the existing normalized bytes
and never copies or reprocesses them. Published content is immutable and does not expire.

Alembic revision `20260928_0004` adds `consultations`, `consultation_photos` and the terminal
`consumed` upload-session state. Downgrading below that revision with published rows is unsafe (the
old cleanup cannot protect promoted files), so the migration refuses downgrade while any consultation
or consumed upload session exists. A later explicit withdrawal/purge operation must remove that
durable state before an operator can downgrade.

## Consultation lifecycle

`backend/app/consultation_lifecycle.py` is the single source of truth for the persisted consultation
lifecycle: `open`, `finalized`, `deleted` and `removed`. Publication creates only `open`; `finalized`
(RF-19/RF-20), `deleted` (RF-13) and `removed` (restricted administrator removal / RF-37) are
terminal states owned by those consumers. There is no automatic expiry, duration, reopening or
lifecycle-transition date; `published_at` remains the only product event date. Temporary preparation
stays on `PhotoUploadSessionState`, not on a consultation row.

`decide_transition(current, target)` is a pure policy that classifies a requested terminal transition
as `apply` (open -> terminal), `same_target` (already that terminal state) or `conflict` (reopening,
different terminal state or unsupported input). It performs no persistence, storage or authorization
side effect. Consumers must:

1. authenticate and authorize the actor;
2. lock the consultation row with PostgreSQL `FOR UPDATE` and re-read the current lifecycle;
3. evaluate `decide_transition`;
4. on `apply`, perform every database side effect and write the terminal state in the same
   transaction, committing once before any RF-37 physical deletion;
5. on `same_target`, return the existing result only after proving the operation and payload are
   identical;
6. on `conflict`, change nothing and return a safe, owner-appropriate conflict.

The first terminal commit wins; finalization, author deletion and administrator removal have no
priority ordering, and no later operation may overwrite, reinterpret or reopen the result. Every
protected detail, text, photo, private-link and future vote request still authorizes against the
latest committed lifecycle, and non-open consultations return the generic unavailable response
(`DEC-028`) without leaking which terminal cause applied.

## Manage my consultations

`My consultations` is a fourth authenticated primary navigation destination (Home, Create, My
consultations, Profile). It lets an author recover a published consultation after leaving Create,
reloading the app, signing in again or an ordinary service restart.

- `GET /api/my-consultations?state=open|finalized&limit=&cursor=` — the current account's
  consultations in one canonical lifecycle, ordered newest first (`published_at DESC, id DESC`),
  with bounded keyset pagination. Open rows expose only `id`, `state`, `question`, `audience` and
  `published_at`; finalized rows expose only `id`, `state` and `published_at`. The cursor encodes
  only version, state, publication time and UUID, and carries no owner, token or content field.
- `GET /api/my-consultations/{id}` — owner-only projection. `open` returns the full stored text,
  audience and ordered photo metadata; `finalized` returns only `id`, `state` and `published_at`
  with no question/context/audience, photo, storage or link work. Unknown, non-owner, deleted and
  removed targets return the generic `consultation_unavailable` response.

Both reads require the signed cookie session, are private and `no-store`, and derive ownership
solely from the current account; a Public reader or valid Private-link holder cannot reach another
author's management view. The frontend reuses one shared owner-detail controller for the
publication-success screen and the returning detail, so ordered photos and the existing
Private-link controls (copy/disable/replace/create, with confirmation and expected-generation
checks) behave identically, with full object-URL cleanup on partial failure, superseded responses
and unmount.

This increment recovers existing consultations and their Private links only. Votes, results,
finalization, deletion and the public share journey remain owned by their later tickets and are not
fabricated by this list or detail. Finalized rows therefore show the minimum permitted
identifier/date/state summary without original free text, photos, link tokens or invented outcome
data.

## Voting

`backend/app/vote_service.py` owns the immutable single-vote boundary and is exposed through two
focused routes in `backend/app/api/consultations.py`:

- `GET /api/consultations/{id}/my-vote` — the current account's own vote, returning exactly
  `{status: "not_voted"}` or `{status: "voted", photo_id}`. It never returns a count, percentage,
  leader, winner, timestamp, voter identity or any result derived from other votes.
- `POST /api/consultations/{id}/votes` — accepts exactly `{photo_id}` and records one final vote.
  The first insert returns 201, an exact replay returns 200, and a different already-recorded option
  returns a safe `vote_already_recorded` conflict without being overwritten.

Both routes require the signed cookie and, for Private consultations, the current capability in the
`X-NextPost-Private-Link` header. Submission locks the consultation row `FOR UPDATE`, re-authorizes
the current account/audience/link/lifecycle state inside the same transaction, and commits once, so
a late vote cannot land on the far side of a terminal transition (DEC-033). Owners cannot vote, and
unknown, unauthorized, terminal, revoked-link and self-vote cases share the generic
`consultation_unavailable` result. An authorized option from a different consultation is a safe
`invalid_selection` failure.

Alembic revision `20261016_0005` adds the `votes` table with a `(consultation_id, voter_id)` unique
constraint and a composite `(consultation_id, consultation_photo_id)` foreign key (backed by a new
`(consultation_id, id)` candidate key on `consultation_photos`) proving the selected option belongs
to that consultation. Foreign keys are restrictive so a future account/terminal workflow cannot
silently erase participation; downgrade is refused while votes exist.

The chronological Home feed adds a server-derived `has_voted` boolean (computed set-wise for the
authenticated account, never a count). An already-voted Public card keeps its position and gains a
`Voted` marker; opening it shows only that account's recorded photo as `Your vote` with
`Votes cannot be changed`, and never exposes aggregate or other-voter information. Private
consultations never appear in Home.




## Local backend development

Start PostgreSQL with `docker compose up -d db`, then:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -e "backend[dev]"
$env:DATABASE_URL = "postgresql+psycopg://nextpost:nextpost-local-only@localhost:5432/nextpost"
.\.venv\Scripts\python -m alembic -c backend\alembic.ini upgrade head
.\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --reload
```

Backend validation:

```powershell
.\.venv\Scripts\python -m pytest backend\tests
.\.venv\Scripts\python -m ruff check backend
.\.venv\Scripts\python -m ruff format --check backend
.\.venv\Scripts\python -m mypy backend\app
```

## Local frontend development

```powershell
cd frontend
npm ci
npm run dev
```

Frontend validation:

```powershell
npm test
npm run format:check
npm run lint
npm run typecheck
npm run build
```

The Capacitor configuration is present, but native projects are intentionally not generated yet.
Choose the permanent application ID and signing identities before running `npm run mobile:add:ios`
or `npm run mobile:add:android`.
