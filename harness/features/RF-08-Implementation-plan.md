# RF-08 - Explain the consultation objective - Implementation Plan

## Status

`Ready for implementation`

The product owner explicitly approved finalisation on 2026-09-23 after confirming options 1A/2A
and reviewing the closed contract. This approval authorizes this plan, not harness launch.

## Source ticket

- Trello title: `RF-08 · Explicar el objetivo de la consulta`
- Trello URL: https://trello.com/c/lcZAWVWd/11-rf-08-explicar-el-objetivo-de-la-consulta
- Trello list at intake: `Fase 2`, on the configured `APP - NextPost` board.
- Snapshot captured on: 2026-09-22 UTC, before the 21:08:23 UTC research checkpoint; the connector
  did not return the exact read timestamp. Recorded in the repository on 2026-09-23.
- Grooming notes: `harness/grooming/RF-08-grooming.md`

The source story asks authors to explain their decision so votes have context. Its criteria require
an editable preloaded question, optional guided context, plain text alongside photos, visible limits
and validation before publication. Categories, tags and social-account connections are excluded.

## Objective

Provide reusable question/context editing, validation and presentation so authors can explain a
comparison and voters can read exactly the text reviewed before publication. Deliver tested frontend
components and a backend validation contract for RF-06/RF-10, without adding a temporary product
destination. RF-06 later integrates the real composer; RF-10 persists and publishes its content.

## Context and current behaviour

- The existing stack is React/TypeScript/Vite with Capacitor, FastAPI/SQLAlchemy/Alembic and
  PostgreSQL. Authentication uses the existing signed HttpOnly account cookie.
- `frontend/src/App.tsx` provides Home/Profile navigation. No consultation composer, preview,
  published detail or publication route exists. Account validation is in `frontend/src/validation.ts`
  and `backend/app/validation.py`; consultation text rules do not exist yet.
- RF-07 is implemented and in implementation review. Its private upload sessions, image processing,
  owner-only reads, lease and cleanup have recorded automated validation. Real-iPhone/TestFlight
  and final composer checks remain external integration gates.
- `backend/app/config.py` owns validated settings applied at startup. The authenticated
  `GET /api/application-config` in `backend/app/api/photos.py` returns photo and open-consultation
  limits using `ApplicationConfigResponse` in `backend/app/schemas.py`. The client lives in
  `frontend/src/photoApi.ts` and is consumed by `usePhotoUploader.ts`.
- `backend/app/models.py` contains accounts, upload sessions and images, but no Consultation entity
  or text columns. The latest migration is `20260922_0003_photo_uploads.py`.
- `backend/app/main.py` already exposes safe 422 field errors through
  `{"detail":{"code":"validation_error","field_errors":{...}}}`.
- DEC-009 requires English product copy. DEC-012 requires transient preparation without recoverable
  drafts. DEC-018 makes publication immutable. DEC-022/024 define registered Public/Private access
  and explicit audience choice. DEC-027 requires correction of cleared questions and complete context
  above photos. RF-06's accepted boundary requires shared faithful preview and preserved editor state.

## Scope

### In scope

- Reusable controlled question/context fields, initialization helper, matching frontend/backend
  normalization and validation, safe field errors and accessible counters.
- A shared read-only text component displaying question and optional context in full.
- Additive server-owned text limits in the existing authenticated application-config contract,
  startup validation, environment/Compose wiring and operator documentation.
- Unit/component/config-API tests and documented contracts for RF-06, RF-09 and RF-10.

### Out of scope

- Complete composer/navigation, product preview route, consultation database model/migration,
  publication endpoint, photo promotion, audience/link enforcement, feed, voting, results or history.
- Text in upload-session records, saved drafts, autosave, browser persistence, rich text, clickable
  URL detection, mentions, categories, tags, social imports, translation or AI suggestions.
- New moderation systems, queues, storage services, dependencies, native project generation,
  TestFlight distribution or changes to RF-07 image processing/cleanup.

## User experience

1. A new composer initializes `Question` to the editable value `Which photos should I post?` and
   `Context (optional)` to empty. Initialization happens once in the owning state, never on remount,
   blur, configuration refresh or ordinary rerender of a controlled field.
2. The question is single-line. Context is multiline and offers placeholder guidance:
   `For example, where will you post these photos, and what would you like people to compare?`
   Placeholder content is never submitted. User text can contain other languages and emoji.
3. Display each normalized current length and effective maximum. The default maxima are 120 and 500.
   Counters describe normalized content, so surrounding whitespace does not consume the limit.
4. Deleting the question leaves it empty. Show `Enter a question.` on blur or attempted progression;
   require correction before preview/publication. Provide no automatic restoration or restore button.
5. Allow editing/pasting beyond the configured limit so the user can correct it. Show an error and
   block progression; do not silently truncate. Preserve input during IME composition and avoid
   replacing the controlled raw value on every keystroke. Normalize a derived value for validation,
   preview and eventual submission.
6. Validate on blur and progression attempts. Once a field error is visible, update it during
   correction. On a progression attempt, focus the first invalid field. Do not announce every
   character/count change through a live region.
7. A missing/loading/invalid configuration keeps progression blocked. Show loading or a retryable
   configuration error while preserving text. Do not substitute independent client limits.
8. Preview and voter detail share the same display component: complete question, then complete
   nonempty context, above photos supplied by the consumer. No truncation, collapse or expansion
   control. Preserve context paragraph breaks and omit the empty context block.
9. A consumer's validation/network/server failure preserves text. RF-06 owns edit/preview transitions,
   discard confirmation and session loss; controlled components preserve what the parent supplies.
   Confirmed discard/sign-out/session loss clears the owning composer. Reload has no recovery promise.

## Functional requirements

### FR-1 - Effective limits

Add `CONSULTATION_QUESTION_MAX_LENGTH=120` and `CONSULTATION_CONTEXT_MAX_LENGTH=500` to server settings.
Require positive integers; question maximum must accommodate the exact default question (27 code
points). Invalid supplied values fail startup. Configuration changes apply after service restart.

Expose `consultation_question_max_length` and `consultation_context_max_length` in the existing
authenticated configuration response. Preserve the existing four fields and their semantics.
Validate received text maxima as finite safe positive integers, with the question maximum at least
27. Missing/malformed text limits are unavailable configuration for text editing/progression.
Update configuration fixtures and consumers coherently without weakening existing photo checks.

### FR-2 - Deterministic text normalization and validation

Implement equivalent pure rules in TypeScript and Python, separate from UI/HTTP handlers. Validate
runtime types before normalization; never coerce numbers, arrays, objects or booleans to strings.
Question is a required string. Context may be omitted or null; those mean absent context.

For each string, apply these rules in order:

1. Reject unpaired UTF-16 surrogates / surrogate code points. Valid astral characters are allowed.
2. Convert CRLF and lone CR to LF; normalize Unicode to NFC.
3. For question, replace LF and TAB with ordinary spaces. For context, preserve LF and replace TAB
   with an ordinary space. Reject remaining U+0000–U+001F controls except context LF, and reject
   U+007F–U+009F. Do this before trimming so prohibited controls cannot disappear unnoticed.
4. Trim both ends using the same explicit whitespace set in both languages: U+0009–U+000D, U+0020,
   U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029, U+202F, U+205F and U+3000. Earlier control
   rejection still applies. Do not rely on different platform `strip`/`trim` definitions.
5. Count Unicode code points of the result. Require 1 through the configured question maximum;
   context allows 0 through its maximum. Empty context becomes null. Preserve internal spaces and
   context line breaks. No word minimum, question-mark requirement or semantic classifier applies.

Preserve legitimate script/emoji joining characters, variation selectors, case and punctuation.
Composite emoji can count as multiple code points. Browser HTML `maxlength` must not define these
limits because it counts UTF-16 units and can prevent the accepted correction behavior.

Return normalized `{question, context}` only for valid values; otherwise return field-specific safe
errors. Collect both field errors where possible. Revalidating normalized valid output is idempotent.
Use the current server limits when RF-10 later invokes validation, regardless of client guidance.

Required messages:

- Empty/missing question: `Enter a question.`
- Question overflow: `Use {maximum} characters or fewer for the question.`
- Context overflow: `Use {maximum} characters or fewer for the context.`
- Invalid field type/characters: `Enter valid text for the question.` or
  `Enter valid text for the context.`

Do not include submitted content in errors. A backend schema or value object must make this
validation reusable by a future publication service; no standalone validation endpoint is required.

### FR-3 - Controlled editing contract

Provide an initialization helper and controlled field component that receive raw question/context,
effective limits/configuration state, and a change callback. Publish a typed normalized validation
result and a supported way for the parent to request validation/focus after attempted progression.
Accept server field errors without wiping input; clear stale field errors when that field changes.
Keep authentication/config fetching outside the pure fields so RF-06 can share one config request.

Provide a testable configuration-loading boundary or helper using the existing authenticated client:
loading, success, retryable failure and 401/session-loss callback. Consumers can retry without
remounting or reinitializing their text. A 401 delegates to the existing session-loss flow.

Text validity is not consultation publishability. RF-06 combines it with ready photos, count,
session, configuration and audience; RF-10 independently enforces the complete publication rules.

### FR-4 - Shared display and accessibility

Render normalized values with React text nodes. Do not use HTML injection, Markdown parsing or
automatic anchors. Display markup and URL strings literally. Use wrapping that handles long
unbroken text, context whitespace preservation and `dir="auto"` or equivalent direction handling.
Keep question/context ordering stable. The caller supplies heading level and surrounding photo
composition without duplicating text markup or adding voting behavior to this component.

Use visible labels, associated help/counters/errors, `aria-invalid`, logical keyboard order,
visible focus and restrained status announcements. Any action must meet the established 44 by 44
CSS pixel touch-target baseline. Support 320 px width and 200% zoom without horizontal overflow.

### FR-5 - Privacy and lifecycle boundaries

Unpublished text remains in owning React memory only. No text requests on each keystroke, no upload
session text fields, and no text in logs, URLs, telemetry, localStorage or sessionStorage.
RF-06 preserves the live editor through preview and clears it on confirmed discard/session loss.
RF-10 will persist only validated normalized text as immutable consultation content.

Published text must follow the consultation's audience/lifecycle authorization. Public requires a
registered account; Private also requires the link. External previews remain generic. RF-08 creates
no content read endpoint or independent retention path. Do not copy text to retained outcome data;
DEC-023 permits only minimum outcome records, not additional free-text analytics retention.

## Technical approach

Deliver small pure validators, controlled editor fields and one read-only presenter. Extend the
existing configuration API rather than adding a service. Share behavior through explicit contracts
and matching test vectors across languages; no new library or code-generation pipeline is needed.

### Affected areas

- Frontend: `frontend/src/photoApi.ts` configuration type/runtime guard; new focused text validation,
  field/presentation components and tests; relevant additions in `frontend/src/styles.css`.
  New module filenames may follow local conventions; these modules do not exist yet.
- Backend: `backend/app/config.py`, `backend/app/schemas.py`, `backend/app/api/photos.py`, plus a new
  focused text-validation module/schema. Reuse the error shape in `backend/app/main.py` without
  changing unrelated account handling.
- Domain/data model: an in-memory text value/schema only. `backend/app/models.py` and migrations
  need no changes for this increment.
- Storage/background work: none.
- Configuration/deployment: `.env.example`, `docker-compose.yml` backend environment entries.
- Documentation: README configuration/integration guidance and evidence-based project state.
- Existing tests: configuration/photo API fixtures and uploader tests must include the new fields
  where they construct full configuration responses. Keep account validation behavior unchanged.

### Data and migration requirements

No new persisted data and no migration. Do not add text to PhotoUploadSession or create Consultation
early. RF-10 owns the future question/context columns and atomic persistence. Future published reads
must not reject stored content solely because deployment later lowers a text limit; current limits
govern new publications. RF-08 configuration rollback has no database transformation.

### API and integration requirements

`GET /api/application-config` remains authenticated and additive. Its new numeric fields are
`consultation_question_max_length` and `consultation_context_max_length`. It must expose no secret
settings. Existing photo limits remain present. Test the actual route and runtime client guards.

RF-10's future request includes required `question` and optional nullable `context` alongside its
own publication fields. RF-08 supplies normalization/validation, not that endpoint. Future text
errors use HTTP 422 and the existing envelope, for example:

```json
{"detail":{"code":"validation_error","field_errors":{"question":"Enter a question."}}}
```

RF-10 must validate text before committing publication, persist normalized values atomically and
include normalized text in its retry/idempotency contract. Invalid text cannot consume or promote
uploaded photos. The server never inserts a default for a missing/empty submitted question.

Preserve these discovered RF-07 constraints in consumer documentation:

- `PhotoUploader` exposes ready IDs and a blocked flag, but not the upload-session ID. The hook
  discards uploads on unmount. RF-06/RF-10 must extend their integration boundary and keep the live
  uploader mounted through preview, then safely relinquish it after confirmed publication.
- The blocked flag alone does not enforce the minimum photo count. RF-06 must compose all checks.
- `validate_publication_images(db, storage, account_id, session_id, ordered_ids, now)` locks the
  session and returns ordered rows after checking owner, active lease, uniqueness, count, ready
  state and byte presence. It does not commit or publish. RF-10 owns atomic promotion and preventing
  later composer discard/abandonment cleanup from deleting promoted files.

These are consuming-ticket tasks, not permission to change RF-07 lifecycle code during RF-08.

### Security and privacy

Use strict types, deterministic normalization and server validation. Render text inertly; test
script-like input and malicious URL text. Never log raw validation payloads or expose them in
exception responses. Configuration reads reuse signed-cookie authentication. No new credentials,
authorization bypass, anonymous preview, persisted draft or background task is introduced.

## Implementation sequence

1. Add the two validated settings, environment/Compose wiring and additive configuration response.
2. Implement the pure backend text validator/value schema and representative normalization fixtures.
3. Extend client configuration validation and implement matching TypeScript rules using the same
   input/output fixtures. Keep defaults centralized per runtime and assert their equality in tests.
4. Add controlled editor fields and retryable configuration-loading integration, preserving raw text
   and exposing normalized validity and progression-error focus to the future composer.
5. Add the shared full-text display component and scoped responsive/accessibility styles.
6. Exercise editor/preview behavior in tests and a temporary development mount; add no product route.
7. Run repository checks and focused built-stack config smoke; document consumer contracts, manual
   evidence and deferred RF-06/iPhone gates. Update project state only with actual evidence.

## Validation strategy

### Automated tests

- Configuration defaults, overrides, zero/negative/noninteger inputs, maximum below default-question
  length, additive authenticated response, 401, missing/malformed/nonfinite/unsafe client values,
  retry and preservation of input through config changes/failures.
- Matching text vectors: default; empty/spaces; absent/null context; invalid runtime types; exact
  120/500 boundaries and overflow; altered limits; CRLF/CR/TAB; prohibited controls before trimming;
  explicit whitespace edges; NFC composed/decomposed accents; astral emoji and joined emoji;
  Arabic/RTL; lone surrogates; preserved internal spaces/paragraphs; idempotent normalized output.
- Components: initialize once; clearing question never restores it; optional context omitted;
  counters use normalized code points; no silent truncation; blur/progression errors and focus;
  correction clears errors; server errors preserve input; IME composition does not lose characters;
  preview/edit state retained by a test parent; config retry and session-loss callback.
- Presenter: full question/context in order, no collapse/truncation, paragraph breaks, literal
  HTML/Markdown/URLs without executable elements or links, direction/wrapping and accessible markup.
- Existing frontend/backend suites, including configuration-consuming upload tests, remain green.
  Use the real config route for HTTP tests; a test-only route may exercise future 422 mapping if
  needed, but must not be registered in the production application.

### Manual validation

- Mount the components in a temporary development/test harness and verify keyboard focus, field
  labels/error announcements, config retry, default clearing, maximum-length text, paragraphs,
  emoji/RTL and literal markup. Do not commit a temporary product route.
- Inspect rendered mobile/desktop layouts at 320 px and 200% zoom; long words must wrap and complete
  context must stay readable above representative photo content.
- Smoke the built API with authenticated config reads using default and overridden values, and
  unauthenticated rejection. Verify deployment actually forwards the new settings.
- RF-06 later proves real edit/preview/edit, uploader lifetime, discard/session loss and publication
  retry. RF-09 proves text access restrictions; RF-10 proves transactional validation/persistence.
- Physical-iPhone/TestFlight keyboard, selection, IME and integrated safe-area checks require the
  signed iOS environment and RF-06 integration. Record them as pending external integration gates,
  not passed component tests or blockers to delivering this reusable increment.

### Commands

From the repository root, using the existing environment:

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

For built-stack configuration smoke when implementation is authorized:

```powershell
docker compose up --build -d
```

Do not run migration downgrade or delete volumes for this schema-free feature. Do not claim skipped
PostgreSQL tests or unavailable device checks passed; report relevant environment limits explicitly.

## Acceptance criteria

- [ ] New preparation initializes the exact editable default question once and empty optional context.
- [ ] Clearing the question keeps it empty and requires correction; no restoration action exists.
- [ ] Configurable 120/500 defaults reach the authenticated client from the server; invalid settings
      fail startup and malformed/unavailable client config blocks progression with retry.
- [ ] Client/server normalization, code-point counting, type/control validation and limits agree on
      shared fixtures; normalized absent context is null and question cannot be empty.
- [ ] Counters and field errors are accessible, excess text is never silently truncated, IME input
      is preserved, and attempted progression focuses the first invalid field.
- [ ] Loading, errors, retry and ordinary rerender preserve entered raw text; 401 delegates session loss.
- [ ] One display component shows the complete question and nonempty context above photos without
      collapse/truncation, preserves paragraph breaks and omits empty context.
- [ ] Text is rendered inertly and no unpublished text enters persistence, URLs, logs or telemetry.
- [ ] Backend validation and typed frontend contracts are reusable by RF-06/RF-10 without adding
      a consultation model, migration, save endpoint, product route or photo-lifecycle changes.
- [ ] Automated validation and component-level responsive/accessibility checks have evidence;
      the built config API smoke proves defaults, override forwarding and authentication.
- [ ] Existing authentication/profile/photo behavior remains green; integrated RF-06/RF-09/RF-10
      and physical-iPhone gates are explicitly handed off without false completion claims.

## Dependencies and ordering

- Reuse RF-01/RF-02 cookie/account foundation and RF-03's visual/accessibility conventions.
- Read the complete `harness/features/RF-07-Implementation-plan.md` dependency and inspect its actual
  code. It supplies configuration/upload boundaries, not a complete composer or publication.
- Grooming order remains RF-08 -> RF-09 -> RF-10 -> finalise and implement RF-06. RF-08's reusable
  implementation does not require the future publication endpoint or complete voter screen.
- RF-06 owns integration; RF-09 owns links/access; RF-10 owns persistence/publication. RF-14 can
  define compact feed cards separately without changing the full preview/detail requirement.
- Native app ID, signing, Xcode and TestFlight remain future delivery prerequisites (DEC-014).

## Risks and mitigations

- Cross-language length drift: explicit code-point/whitespace rules and matching Unicode fixtures.
- User text lost during normalization/config retry: retain controlled raw values; derive normalized
  preview/submission values and initialize only in the parent once.
- Text changes vote meaning: RF-10 persists normalized values immutably with the publication.
- Content execution or leakage: inert rendering, strict types, no raw text logs/persistence and
  consultation-wide authorization in future consumers.
- Scope expansion or premature completion: keep reusable components independent of missing product
  flows and document exact consumer/device gates.
- Image loss during future preview/publication: carry RF-07's unmount/ID/promotion constraints into
  RF-06/RF-10 documentation; do not attempt an incomplete promotion fix in RF-08.

## Harness handoff notes

- At finalisation the working tree contains uncommitted grooming, decisions and state documentation
  for this task. Preserve unrelated work; inspect the current tree before implementation.
- This English plan is self-contained. The harness needs neither Trello access nor conversation
  history. Historical intake findings in older plans may predate RF-07; inspect actual code.
- Implement only the approved reusable text/configuration increment. No commit, push, deployment,
  Trello mutation, native generation or launching other agents is authorized by this plan.
- Do not open the coordinator's OpenCode orchestration runbook or launch the harness from this plan.
- Use English identifiers/comments/copy; preserve accepted stack and session behavior. Stop and
  report any material conflict with accepted decisions instead of silently expanding scope.
- Record actual validation evidence and remaining integrated/device checks separately. Readiness
  of this plan is not an implementation-completion claim.

## Resolved grooming decisions

- The owner selected 1A: a cleared question stays empty and requires correction.
- The owner selected 2A: complete question and optional context appear above the photos in shared
  preview/voter detail; empty context is omitted (DEC-027).
- Editable default, optional guidance, plain text, transient preparation and immutable publication
  are inherited accepted requirements.
- The reviewed contract uses configurable 120/500 limits, accessible counters/errors, preserved
  input and equivalent server/client validation. Routine normalization/API details are resolved here
  under the owner's explicit technical delegation.
- RF-08 supplies reusable components/validators; RF-06 integrates and RF-10 persists/publishes.
- On 2026-09-23 the owner explicitly requested finalisation and notification when this plan is ready.
  Harness launch remains a separate request.

## Remaining questions

None
