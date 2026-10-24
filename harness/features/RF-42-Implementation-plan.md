# RF-42 - Prepare web and iOS delivery and invited testing - Implementation Plan

## Status

`Ready for implementation`

The product owner approved the settled scope, the deferred authenticated S3 configuration gate,
plan finalisation and autonomous harness implementation on 2026-10-23 by asking Codex to complete
everything possible while leaving only the new `aws login`-dependent check for later. This approval
does not authorize commit, push, production deployment, DNS/IAM/Apple/App Store Connect/Codemagic
mutation, build upload, tester invitation or Trello mutation.

## Source ticket

- Trello title: `RF-42 · Preparar la entrega web e iOS y la prueba invitada`
- Trello URL: https://trello.com/c/T2TyOtlh/43-rf-42-preparar-la-entrega-web-e-ios-y-la-prueba-invitada
- Trello list at intake: `Beta · entrega y aprendizaje`
- Snapshot captured on: `2026-10-12T14:13:54.8916209+02:00`
- Grooming notes: `harness/grooming/RF-42-grooming.md`

The authenticated Trello card was unavailable during grooming. The owner accepted using the
repository-preserved snapshot and asked that all work except the authenticated AWS check proceed.

## Objective

Make the MVP reproducibly deliverable as a production web application and as a distinct invited
iOS TestFlight application. A successful protected `main` revision must pass complete CI and be
capable of serialized deployment to the existing Lightsail host at
`https://nextpost.formcadence.app`. A selected `main` revision must also be capable of a manually
started, signed Codemagic build for the separate NextPost App Store Connect record.

Prepare the code, automated checks, production configuration contracts, runbooks and iOS project
without performing external mutations. Production photo storage changes to the existing private
FormCadence S3 bucket under an isolated `nextpost/` namespace, but no NextPost photo may be uploaded
until an owner-authenticated preflight proves that bucket versioning, Object Lock, lifecycle,
encryption and public-access settings can satisfy permanent RF-37 deletion.

## Context and current behaviour

- NextPost is a React/Vite frontend, FastAPI/SQLAlchemy backend and PostgreSQL 18 database. Compose
  currently exposes development ports and stores normalized images in a backend-only named volume.
- `backend/app/storage.py` is a concrete filesystem `PhotoStorage`; upload, protected reads and
  RF-37 cleanup depend on it. Exact opaque 32-hex keys, delete-then-exists verification, anomaly
  inventory and safe temporary-file cleanup already form the privacy boundary.
- RF-37, RF-13, RF-19/RF-20 and RF-32 implement database-first terminal revocation and permanent
  image cleanup. Storage failure may delay physical erasure but never restore access.
- Production cookies become `Secure`, `HttpOnly`, `SameSite=Lax`. Browser calls use credentialed
  fetch and state-changing routes validate trusted origins.
- `frontend/capacitor.config.ts` has the provisional ID `com.nextpost.app`; no committed iOS project
  or NextPost Codemagic workflow exists.
- FormCadence provides the reference chain: GitHub CI, SSH to Lightsail, idempotent Compose deploy,
  HTTPS probes, Capacitor bundled assets, native HTTP patching and a Codemagic App Store build. It
  is a pattern, not proof of a completed iPhone/TestFlight release.
- The two products cannot each own public ports 80/443. One host-level reverse proxy must route to
  separate loopback-bound stacks without merging applications or data.
- The existing FormCadence runtime IAM identity is intentionally unable to read bucket-wide
  configuration. The saved owner/root AWS CLI login is expired. No bucket, object, permission or
  credential was changed during grooming.
- DEC-047 contains the durable production, storage, recovery, native and beta-contact decisions.

## Scope

### In scope

- Complete GitHub Actions CI and a production deployment workflow for protected `main`, with a
  manual dispatch option, protected environment, immutable action pins, concurrency control and
  deployed-SHA evidence.
- Production Compose/configuration that binds NextPost services only to loopback where host access
  is required and integrates with one documented host-owned reverse proxy.
- An idempotent deploy script and operator runbooks for fresh/incremental deployment, health,
  migration failure, corrective roll-forward, cleanup scheduling, alerts and empty restart.
- A storage abstraction with filesystem and S3 implementations; S3 exact-prefix/version-aware
  upload/read/head/delete/inventory behavior; RF-37 permanent-delete integration; deterministic
  fakes and disposable S3-compatible automated tests.
- A fail-closed bucket compatibility preflight and explicit activation gate. Code and local tests
  may be completed now; the real bucket check remains manual until a new `aws login` is available.
- A plain-language web privacy notice and documented authenticated manual access/export and
  account/data-erasure procedure using `xnegis@gmail.com`.
- Scheduled restricted RF-37 status and failure delivery to `xnegis@gmail.com`, with a testable
  provider-neutral command/interface. Do not invent or configure a paid vendor.
- Permanent iOS configuration for visible name `NextPost` and preferred ID `app.nextpost`, a
  conventional committed Capacitor iOS project, mobile build mode, native HTTP/cookie path and
  native deep-link handling for Public and Private consultation links.
- A manual Codemagic hosted-macOS workflow for locked validation, sync, signing, monotonic build
  number, ordinary App Store/TestFlight IPA and App Store Connect upload. It must not use
  `testFlightInternalTestingOnly`.
- Release, privacy, TestFlight and physical-device checklists tied to one Git SHA.

### Out of scope

- Android distribution, public App Store release, subscriptions, payment or marketing launch.
- A second domain, second production server or migration away from the existing Lightsail host.
- Executing deployment, changing DNS/reverse-proxy state, creating IAM credentials, changing the
  S3 bucket, registering Apple identifiers/apps, changing Codemagic, uploading builds or inviting
  testers.
- PostgreSQL backup, snapshot, retention, automated restore or continuity guarantees.
- Public/presigned object URLs, photo backups, retained versions, replicas or archives that can
  resurrect revoked content.
- Full self-service RF-34/RF-35 UI, invitation codes, tester allowlists, forced email verification,
  push notifications, analytics/crash SDKs or a broad administrator console.
- Product redesign, bearer-token authentication, a remote production WebView or relaxed transport,
  CORS, Origin or cookie security.
- Commit, push or Trello mutation.

## User and operator experience

The web product remains the current responsive application at one canonical HTTPS origin. Existing
deep links load through SPA fallback and `/api` remains same-origin. Unhealthy or partially migrated
releases fail deployment probes and are not reported successful. There is no user-visible backup or
recovery promise.

The installed iOS app uses bundled assets. Registration, sign-in, authenticated relaunch, logout,
photo selection/upload, consultation creation, Public/Private shared links, voting, owner actions
and participation history retain their current semantics through the native HTTP cookie jar. A
network outage produces the existing recoverable unavailable behavior rather than a blank remote
WebView or silent logout.

External testers see TestFlight beta metadata and use `xnegis@gmail.com` for feedback/support. A
published privacy page identifies the controller, purposes, data categories, processors, retention
and rights contact. The operator authenticates a requester before manually exporting or erasing
account data and records only the minimum audit-safe evidence.

Deployment and RF-37/S3 failures reach `xnegis@gmail.com`. A failed alert delivery is itself a
failing operational check. The app must not require a custom mail server; configuration chooses a
replaceable delivery mechanism later without embedding credentials in code.

## Functional requirements

### FR-1 - Complete CI gate

On pull requests and pushes to `main`, run locked backend installation, Ruff check and format check,
strict MyPy, the complete pytest suite, disposable PostgreSQL migration/concurrency tests, locked
frontend installation, Vitest, Prettier check, ESLint, TypeScript check, production/mobile builds,
Compose validation and then-current high-severity dependency audits. Cache only non-secret package
data. Use least-privilege workflow permissions and reviewed immutable action commit pins.

No deploy job may run after a skipped or failed required check. Add workflow/config tests where
practical so the gate cannot silently omit an established repository command.

### FR-2 - Serialized push-to-main web delivery

After the complete `main` CI gate, one non-cancelling protected `production` deployment may run at a
time. It receives only SSH connection material from GitHub environment secrets and calls a
repository-owned server deploy script for the intended SHA. Application, database, AWS and alert
secrets remain in a root/operator-owned server environment file.

The script validates configuration, fetches the exact approved revision, builds/starts the isolated
stack, applies Alembic through the backend startup contract, waits for readiness, checks the public
HTTPS frontend and `/api/ready`, verifies the running revision and records/reports the SHA. It is
idempotent and must never claim success after a migration, readiness, TLS or revision failure.

### FR-3 - Shared-host isolation and HTTPS contract

Document and supply an operator-reviewed reverse-proxy fragment for
`nextpost.formcadence.app`. Only the shared host proxy owns 80/443. NextPost frontend/API bind to
distinct loopback ports; PostgreSQL has no public host binding. FormCadence configuration, volumes,
containers and routes remain untouched. Backend documentation endpoints are not public in
production unless separately authorized.

Production validates canonical HTTPS, trusted Origin, secure cookie flags, same-origin browser
requests, SPA fallback and no localhost/LAN/private capability in built assets.

### FR-4 - Storage boundary and S3 namespace

Refactor the concrete filesystem implementation behind an explicit storage protocol used by
`photo_service`, protected media reads and cleanup. Preserve local filesystem behavior for
development/tests. Add an S3 implementation configured only outside code by region, bucket and the
fixed/bounded `nextpost/` prefix. The backend creates opaque keys and never accepts a caller key,
bucket or prefix.

S3 operations cover exact put, get, head/exists, permanent delete, safe namespace inventory and
unexpected-object reporting. No list or delete may escape the configured prefix. Reads remain
backend-authorized; do not return bucket keys or public/presigned URLs. Add a pinned compatible AWS
SDK dependency and sanitize all SDK errors/logs.

### FR-5 - Version-aware permanent erasure

The compatibility preflight reports only safe configuration facts, not secrets or object names. It
must verify Block Public Access, encryption, versioning, Object Lock/default retention, lifecycle,
replication implications and the dedicated identity's exact-prefix put/get/head/list-version/delete-
version abilities.

When versioning is disabled, RF-37 completion still requires delete followed by strong absence
verification. When versions/delete markers can exist, the durable storage/delete contract must
retain sufficient exact version identity, enumerate every version of the exact logical object,
delete each version and marker, and verify none remains retrievable before removing retry metadata.
Never treat a current-key 404/delete marker as completion. If Object Lock/default retention or a
policy prevents timely permanent deletion, preflight fails and production photo activation stops.

### FR-6 - Safe migration from local storage

RF-42 does not silently migrate ordinary production bytes. Provide a restricted, idempotent,
auditable migration/verification command or documented procedure for any legitimate current local
objects: keep traffic controlled, copy exact DB-referenced active objects to the isolated prefix,
verify byte identity/metadata through the backend boundary, switch only after complete proof and
leave no public copy. Revoked/terminal bytes must be deleted, not migrated. Do not remove the local
source until cutover is explicitly authorized and proven. Since this is a beta and no deployment is
authorized, automated tests use disposable data only.

### FR-7 - Cleanup scheduling and private alerts

Provide a host scheduling example/runbook for `python -m app.cleanup`. Exit 0 is healthy; RF-37
overdue/anomaly/failure exit 1 and deployment/readiness/S3 failures route to `xnegis@gmail.com`;
exit 2/busy means another maintenance leader and is not a privacy incident. Alert content is
sanitized and excludes photos, keys, paths, content, cookies, links and account data. Delivery is
testable through dependency injection or a dry-run sink and production configuration contains no
hard-coded mail secret.

### FR-8 - Deliberate no-backup and empty restart

Do not add PostgreSQL dumps, volume snapshots, pre-deploy backups or restore automation. Document
that volume persistence is not backup. If the database is unusable without a valid ad hoc copy,
traffic stays off; a restricted operator permanently deletes and verifies only the exact
`nextpost/` versions/objects, recreates the database, applies Alembic and starts with no accounts or
product state. Never reconstruct state from S3 keys or restore historical photos.

### FR-9 - Privacy and manual rights readiness

Serve a plain-language privacy notice reachable without authentication and linked from appropriate
web/iOS entry points. It identifies controller/contact, purposes, categories including photographs,
retention/deletion, processors/services, security boundary and applicable user rights without
claiming unsupported guarantees.

Document a restricted process for `xnegis@gmail.com` requests: authenticate the requester through a
separate safe exchange, locate only their account-scoped data, produce a minimal secure export or
execute the applicable RF-34/RF-35-compatible erasure steps, verify completion and keep minimal
audit-safe evidence. If current product contracts cannot satisfy a real request, stop and groom the
owning ticket rather than improvising database edits.

### FR-10 - Permanent iOS project and native HTTP

Set Capacitor `appId` to `app.nextpost`, `appName` to `NextPost`, use `dist`, enable the Capacitor
native HTTP bridge and do not configure a remote `server.url`. Add deterministic `build:mobile` and
`mobile:sync:ios` scripts using `https://nextpost.formcadence.app` as the mobile API origin while
the browser build remains same-origin.

Centralize the request boundary enough to prove every current fetch path, multipart photo upload and
protected binary photo response works with native HTTP/cookies. Session cookies remain server-
signed `HttpOnly`; JavaScript never receives a bearer/session token. Preserve trusted Origin
protection for browsers and fail closed for unexpected cross-origin callers.

Generate and commit the conventional Capacitor iOS project only after the identifier is represented
consistently. Do not create/register the external Apple identifier during implementation. If later
Apple validation finds `app.nextpost` unavailable, stop and return to the owner.

### FR-11 - Native links and real-device behavior

Configure the intended custom/universal-link boundary without claiming associated-domain readiness
before Apple/DNS setup. Public and Private NextPost consultation links opened on iOS must route into
the same application state, preserve the Private capability only for the immediate authorized flow,
return through authentication correctly and never log/persist the capability beyond existing
contracts. Unsupported links fail safely.

Document physical iPhone checks for install, cold/warm launch, registration/sign-in/relaunch/logout,
background/foreground, gallery HEIC/HEIF, upload/retry, create/publish, Public/Private links, voting,
owner results/deletion, participation history, unavailable API, safe areas, keyboard and zoom.

### FR-12 - Manual external-capable TestFlight workflow

Add `codemagic.yaml` using the existing account integration name as a configurable documented
prerequisite, hosted macOS, locked Node dependencies, shared frontend checks, mobile sync, monotonic
build number, automatic App Store signing for `app.nextpost`, IPA build with useful sanitized
diagnostics and App Store Connect publishing. The workflow is manual and tied to a selected `main`
SHA. Do not set the irreversible internal-only export option.

Document the separate App ID/App Store Connect record, internal/external groups, beta description,
privacy/support/review contact `xnegis@gmail.com`, review credentials, export-compliance answers and
first external TestFlight Beta App Review. Do not grant testers App Store Connect roles to avoid
external review.

### FR-13 - Release evidence and roll-forward

Maintain a checklist tied to one SHA covering CI, configuration preflight, deployed revision,
public TLS/readiness, storage privacy/permanent deletion, RF-37 alerting, RF-32 command availability,
privacy/support, Codemagic signing/upload and physical iPhone journeys. Production deployments are
serialized. Correct failures with a new commit and repeat the gate. Do not describe checkout of an
older application commit as safe database migration rollback.

## Technical approach

Introduce a narrow storage protocol/factory rather than spreading environment checks through
services. Keep local raw-upload temporary processing on private ephemeral/local backend storage;
only normalized durable bytes use S3 in production. Extend durable media metadata only if exact S3
version identity is required, through an additive Alembic migration compatible with existing rows.
All cleanup/minimization invariants remain owned by RF-37.

Use one centralized frontend runtime/API-origin boundary and Capacitor's built-in native HTTP patch
instead of duplicating every endpoint or exposing cookies. Add focused compatibility tests for
multipart requests, blobs and links because browser-only JSDOM tests cannot prove the native bridge.

### Affected areas

- Frontend: `frontend/capacitor.config.ts`, `frontend/package.json`, API-origin/request modules,
  routing/link handling, privacy link/page, tests and generated `frontend/ios/` project.
- Backend/application: `backend/app/storage.py`, configuration/factory wiring, photo services,
  cleanup/inventory, restricted preflight/migration commands, tests and AWS SDK dependency.
- Domain/data model: optional additive exact-version metadata only when required for retry-safe S3
  deletion; no new product entity or user-visible state.
- Storage/background work: private local temporary files, S3 normalized objects, RF-37 maintenance
  and host scheduler/alert adapter.
- Configuration/deployment: new `.github/workflows/`, production Compose/override, proxy example,
  deploy/preflight scripts, `codemagic.yaml` and environment examples.
- Documentation: privacy notice, web/iOS release checklist, server operations, no-backup recovery,
  S3 activation and manual rights/TestFlight runbooks.

### Data and migration requirements

- Preserve existing opaque storage keys and database ownership. Bucket/prefix never becomes client
  data or a derivation from account/consultation IDs.
- Any version field is nullable/additive for existing filesystem rows and populated only after a
  successful S3 write. Migration/downgrade must not discard a still-required deletion reference.
- Do not fabricate S3 state for current rows. Cutover must reconcile exact DB rows and bytes.
- PostgreSQL remains authoritative; S3 listings cannot rebuild accounts or consultations.
- Do not create backups. The empty-restart procedure is explicitly destructive and remains a later
  operator action requiring exact target verification; it is not executed by the harness.

### API and integration requirements

- Existing public API payloads and authorization semantics remain unchanged.
- Browser uses same-origin `/api`; mobile uses the canonical HTTPS origin through native HTTP.
- S3 inputs and SDK responses are untrusted. Bound pagination, validate exact prefix/key/version and
  reject unexpected inventory rather than broad deletion.
- GitHub, SSH, AWS, Apple and Codemagic secrets are referenced by names only and never copied from
  FormCadence, logged or committed.
- Alert and TestFlight contact is `xnegis@gmail.com`; implementation does not send real mail or
  mutate external metadata.

### Security and privacy

- Backend-only S3 access, Block Public Access, encryption and least-privilege exact-prefix policy are
  mandatory activation conditions.
- Rotate the apparently long-lived FormCadence key separately; never reuse it for NextPost.
- Preserve `Secure`, `HttpOnly`, signed cookie behavior and trusted browser Origin checks.
- No content/key/path/capability/cookie/account data in logs, CI artifacts, alerts or release proof.
- Never delete by an unresolved prefix, wildcard or inferred path. Production purge and migration
  remain operator-controlled exact-scope procedures.
- Never claim physical deletion until all retrievable S3 versions are absent.

## Implementation sequence

1. Add characterization tests around filesystem storage, factory wiring, RF-37 delete/verify and
   frontend API-origin/cookie behavior.
2. Introduce the storage protocol and preserve the filesystem implementation without regression.
3. Add pinned AWS SDK support, S3 implementation, safe prefix/version inventory, fakes and
   disposable S3-compatible tests; add an additive migration only if version retry data requires it.
4. Implement the read-only compatibility preflight and restricted local-to-S3 cutover/empty-purge
   runbooks or commands. Do not run them against the real bucket.
5. Integrate S3 production selection into configuration/Compose, RF-37 cleanup and sanitized
   observability while keeping local development functional.
6. Add privacy notice/manual-rights documentation and provider-neutral sanitized alert delivery,
   scheduling examples and dry-run tests.
7. Add hardened production Compose/proxy/deploy/revision contracts and complete GitHub CI/deploy
   workflows, with no external secrets or operations.
8. Centralize browser/mobile API origin behavior, enable native HTTP, implement native link routing
   and add focused tests.
9. Replace the provisional bundle ID, generate/commit the iOS project, and add the external-capable
   manual Codemagic workflow without registering or uploading anything.
10. Add release, TestFlight, physical-device, no-backup and roll-forward runbooks/checklists.
11. Run the complete automated, migration, disposable PostgreSQL/S3-compatible and Compose matrix;
    inspect generated/native and workflow configuration for secrets and scope.

## Validation strategy

### Automated tests

- Filesystem/S3 contract parity: exact write/read/head/delete, already absent, transient failures,
  partial retry, invalid key/prefix, pagination, unexpected inventory and sanitized errors.
- Versioned S3: current/noncurrent versions, delete markers, multiple versions, partial version
  deletion, retained/denied version and explicit all-version absence before RF-37 completion.
- Configuration/preflight: local versus production selection, missing/unsafe settings, Object Lock
  or retention rejection, permission rejection and no credential output.
- Existing upload, protected photo, temporary cleanup, whole-session RF-37 cleanup, terminal
  consumers and anomaly reporting remain green.
- Frontend: browser same-origin and mobile canonical origin, credentials, multipart upload, binary
  response, login/relaunch model, link parsing and privacy route.
- Workflow/script static tests: required checks, immutable actions, least permissions, concurrency,
  no internal-only TestFlight flag, exact SHA and failure propagation.
- Full backend/frontend suites plus disposable real PostgreSQL migration/concurrency tests.

### Manual validation

- Inspect the generated Xcode project and build it on hosted macOS; external signing/upload and real
  TestFlight/iPhone proof remain manual external gates.
- With a new authenticated owner session, run the real bucket preflight. Stop before upload on any
  incompatible or unavailable fact; do not change bucket settings implicitly.
- On disposable S3-compatible storage, rehearse cutover, RF-37 deletion and exact-prefix empty purge.
- On an isolated Compose project, prove fresh and incremental deploy, failed migration/readiness,
  restart, cleanup scheduling and sanitized alert dry run.
- Later production proof covers public DNS/TLS, SHA, S3, email delivery, Apple/Codemagic and the full
  two-account web/iPhone matrix. None is claimed by repository-only validation.

### Commands

```powershell
Set-Location backend
..\.venv\Scripts\python -m ruff check app tests
..\.venv\Scripts\python -m ruff format --check app tests
..\.venv\Scripts\python -m mypy app
..\.venv\Scripts\python -m pytest

Set-Location ..\frontend
npm ci
npm test
npm run format:check
npm run lint
npm run typecheck
npm run build
npm run build:mobile
npm audit --audit-level=high

Set-Location ..
docker compose config --quiet
docker compose build backend frontend
```

Run PostgreSQL tests with a disposable `TEST_DATABASE_URL`. Run S3 tests only against a deterministic
fake or uniquely named disposable S3-compatible service/prefix. Never run cleanup, purge, migration,
deployment or bucket changes against ordinary data.

## Acceptance criteria

- [ ] Complete locked backend/frontend/PostgreSQL/build/audit CI gates every deployable `main` SHA.
- [ ] A serialized deployment workflow and idempotent script deploy the exact SHA and fail honestly
      on migration, readiness, TLS, public probe or revision mismatch without embedding app secrets.
- [ ] One documented host proxy can route NextPost and FormCadence while their stacks, databases,
      storage identities and loopback services remain isolated.
- [ ] Local storage behavior remains green and production S3 uses only the private `nextpost/`
      namespace through a new least-privilege identity; clients receive no object URL/key.
- [ ] Version-aware RF-37 deletion removes and verifies every retrievable exact version/marker;
      partial or denied work retains retry evidence and never restores access.
- [ ] Real S3 activation is fail-closed until the deferred owner-authenticated preflight passes.
- [ ] No PostgreSQL backup is added; the exact-prefix verified empty-restart procedure is documented
      without pretending S3 can reconstruct database state.
- [ ] RF-37 scheduled status and deploy/readiness/S3 failures have sanitized, testable delivery to
      `xnegis@gmail.com`; busy maintenance is distinguished.
- [ ] A public plain-language privacy notice and executable manual authenticated rights process use
      `xnegis@gmail.com` without claiming completed RF-34/RF-35 self-service.
- [ ] Capacitor uses `app.nextpost`, bundled assets and native HTTP/cookies against the canonical API,
      with no remote production WebView, bearer token or weakened web security.
- [ ] The committed iOS project and manual Codemagic workflow can build an ordinary external-capable
      App Store/TestFlight IPA and contain no internal-only export flag or secret.
- [ ] Browser/mobile links, photo uploads/responses, session relaunch and failure behavior have
      focused tests; the physical iPhone matrix is documented and not falsely claimed automated.
- [ ] Release evidence is tied to one SHA and uses corrective roll-forward; code rollback is not
      presented as migration rollback.
- [ ] No deployment, AWS/DNS/Apple/Codemagic mutation, build upload, invitation, commit, push or
      Trello change occurs during harness implementation.

## Dependencies and ordering

- RF-07/RF-09/RF-10 define normalized uploads, protected reads and publication ownership.
- RF-37 defines the binding deletion, inventory, retry, anomaly and no-resurrection contract.
- RF-13, RF-19/RF-20 and RF-32 are terminal consumers that production cleanup must preserve.
- RF-21 provides participant history included in real-device invited-journey validation.
- External activation depends on owner-authenticated AWS bucket preflight, DNS/proxy control,
  GitHub environment secrets, Apple availability/registration, Codemagic integration/signing and
  first external TestFlight review. These are manual gates, not harness work.

## Risks and mitigations

- **Shared-host coupled outage:** isolate projects/ports/data and use one reviewed host proxy; verify
  FormCadence before and after a later deployment.
- **S3 retention violates erasure:** fail closed before first upload; delete/verify every version;
  return to the owner if Object Lock/policy is incompatible.
- **Credential exposure:** never copy FormCadence keys; names-only examples, protected secret stores,
  sanitized logs and a dedicated NextPost identity.
- **Lost deletion reference:** persist exact version identity where needed and remove it only after
  all-version absence proof.
- **Native cookie/blob mismatch:** one bounded native HTTP path plus focused multipart/binary/session
  tests and mandatory physical-device proof.
- **Unsafe migration rollback:** serialize deploys, record SHA, roll forward and treat migrations as
  one-way operational events unless independently proven reversible.
- **No database recovery:** state the accepted loss explicitly and provide a traffic-off exact-prefix
  purge/empty restart, not a misleading restore promise.
- **External review delay:** keep web delivery independent; prepare complete beta metadata and use an
  external-capable build from the start.

## Harness handoff notes

- Read `AGENTS.md`, every `harness/context` document, RF-42 grooming and this entire plan. Read the
  approved plans and reviews for RF-07, RF-09, RF-10, RF-13, RF-19/RF-20, RF-21, RF-32 and RF-37.
- The worktree already contains coordinator-owned RF-42 grooming, DEC-047, project-state and plan
  documentation. Preserve them; do not reset or overwrite unrelated changes.
- Implement repository code/tests/config/docs only. Do not run `aws login`, use the real bucket,
  reuse/rotate credentials, SSH, deploy, change DNS, create IAM/Apple/Codemagic resources, upload an
  IPA, invite testers, commit, push or modify Trello.
- Generated iOS files are authorized repository artifacts. External Apple registration/signing is
  not. If native generation requires unavailable macOS-only external state, prepare all portable
  configuration and report the exact remaining command instead of fabricating success.
- If satisfying S3 version deletion would conflict with RF-37 minimization or require retaining
  forbidden history, stop and report the conflict rather than weakening deletion.
- Keep implementation, tests, comments and documentation in English. Report every manual/external
  gate honestly.

## Resolved grooming decisions

- `Q1A`: existing Lightsail host, separate stacks and one shared reverse proxy.
- `Q2`: canonical origin `https://nextpost.formcadence.app`; later changes require coordinated
  deployment and a new iOS build.
- `Q3B`: existing private bucket, isolated `nextpost/` prefix, new least-privilege identity and
  permanent version-aware deletion. Owner-authenticated compatibility is deferred but blocks upload.
- `Q4C`: no PostgreSQL backup/recovery service; accepted exact-prefix purge and empty restart.
- `Q5A`: successful `main` auto-deploys web; selected iOS/TestFlight build is manual.
- `Q6B`: support both internal and external TestFlight testers and first external beta review.
- `Q7`: existing Apple/Codemagic accounts, separate app, preferred `app.nextpost`/`NextPost`.
- `Q8A`: bundled assets plus Capacitor native HTTP and server-owned `HttpOnly` cookie.
- `Q9A`: privacy notice and manual authenticated rights process; no full RF-34/RF-35 UI.
- `Q10`: `xnegis@gmail.com` for support/privacy/TestFlight and private automated beta alerts.
- `Q11A`: complete CI, serialized SHA-recorded deploy and corrective roll-forward.
- The owner accepted the stored Trello snapshot, complete scope/validation matrix and the S3
  pre-upload hard gate by authorizing all work except the unavailable authenticated check.

## Remaining questions

None
