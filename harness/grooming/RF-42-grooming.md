# RF-42 - Prepare web and iOS delivery and the invited test - Grooming

## Status

`Completed - implementation plan ready`

The product owner explicitly selected RF-42 on 2026-10-23 and confirmed the intended delivery
surfaces as the production web application and iOS through TestFlight. The owner wants to reuse the
proven FormCadence/FlexGym delivery shape: a push-driven GitHub web deployment and a separately
invoked iOS distribution path. This is accepted product intent, not yet an approved implementation
plan or authorization to deploy, upload a build, invite testers, create credentials or mutate
Trello.

## Trello snapshot

- Title: `RF-42 · Preparar la entrega web e iOS y la prueba invitada`
- URL: https://trello.com/c/T2TyOtlh/43-rf-42-preparar-la-entrega-web-e-ios-y-la-prueba-invitada
- Stable short URL: https://trello.com/c/T2TyOtlh
- Card ARI:
  `ari:cloud:trello::card/workspace/6aa9032829f8b45ead46cfdd/6accc3be4ed82d519e23eb27`
- Board: `APP - NextPost`
- List at the preserved intake snapshot: `Beta · entrega y aprendizaje`
- State: open and incomplete (`closed: false`, `complete: false`).
- Position: `16384`
- Start date / due date: None / None.
- Labels: None.
- Members: None.
- Checklists: None.
- Comments: None in the preserved snapshot.
- Last Trello activity in the preserved snapshot: `2026-10-12T11:30:39.553Z`.
- Preserved snapshot source:
  `harness/grooming/TRELLO-2026-10-12-after-reorganization.json`.
- Grooming intake started: `2026-10-23T19:37:30.3670911+02:00`.
- Live refresh note: the exact card URL was opened read-only on 2026-10-23, but the available
  browser reached Trello's sign-in wall. Trello's public page was also unavailable to the read-only
  web fetcher. The owner accepted the readable 2026-10-12 repository snapshot for plan finalisation.
  No Trello mutation was performed.

### Description and acceptance criteria at intake (preserved verbatim)

**Estado: trabajo de entrega pendiente de grooming; sin autorización de despliegue o distribución.**

**Origen**
DEC-014 establece web e iOS TestFlight como primeros destinos. La entrevista del propietario
(2026-10-12) confirma primeros participantes invitados personalmente.

**Objetivo**
Hacer visible el trabajo pendiente para una prueba real del recorrido completo: crear, compartir o
descubrir, votar, revisar resultados, finalizar/eliminar y recibir devolución privada.

**Dependencias y evidencias a planificar**
- Identificador definitivo, equipo/firma Apple, entorno Xcode, proyecto nativo y distribución
  TestFlight.
- Prueba en iPhone real: galería y HEIC/HEIF, sesión, navegación, enlaces, subida y ciclo completo;
  cierre de las evidencias pendientes de RF-06/RF-07/RF-09.
- Entorno web/API HTTPS y acceso privado a fotos, operación de borrado y retirada manual restringida
  RF-32/RF-37 antes de exposición real.
- Revisión explícita de preparación de cuentas/datos (RF-34/RF-35), información/contacto y feedback
  RF-38; no asumir que quedan dispensados por la invitación.
- Observar si los primeros usuarios reciben ayuda y vuelven, coordinado con RF-39, sin objetivos
  numéricos inventados.

Las invitaciones pueden ser personales. No se aprueba un sistema de códigos de invitación, lista de
acceso, categorías, cambio de autenticación, despliegue, envío de mensajes ni subida de builds con
esta tarjeta. Cada acción conserva sus gates y requiere un plan aprobado y la petición
correspondiente.

Referencia: harness/grooming/PRODUCT-2026-10-12-reorganization.md.

## Intended outcome

Deliver the complete accepted NextPost MVP through two real surfaces:

1. A production HTTPS web application and API that update automatically only after the main-branch
   validation gate succeeds.
2. A signed iOS application built from the same React/Vite source, distributed to personally
   invited testers through TestFlight and connected to the same production API.

The increment must make delivery reproducible and operationally safe. It must not equate a green
build with a successful beta: the real author/voter/finalization/history journey, private photo
boundaries, terminal erasure, restricted removal, support/contact and required data-subject
processes need explicit evidence before invited use.

## Baseline and inspection record

- Baseline: clean `main` at `862a661d9cff7958aab24bfebb6ae0f027285f21`, matching
  `origin/main`, remote `https://github.com/xNegis/NextPost.git`.
- Current NextPost has no `.github` workflow, production reverse proxy, deployment script,
  `codemagic.yaml`, generated `ios/` project or production/mobile environment file.
- The current Capacitor ID is explicitly provisional: `com.nextpost.app`.
- Current Compose starts PostgreSQL 18, applies Alembic before Uvicorn, exposes backend on 8000 and
  frontend on 4173, and owns named PostgreSQL and private-photo volumes. It is a development stack,
  not a hardened internet-facing topology.
- Production sessions already become `Secure`, `HttpOnly`, `SameSite=Lax` when `APP_ENV` is not
  `development`. Browser requests use credentialed fetches. State-changing consultation routes
  enforce configured trusted origins while allowing the missing Origin expected from a native
  client.
- The frontend currently makes browser `fetch` requests. A bundled Capacitor application with a
  local WebView origin needs an explicit, validated native HTTP/cookie design before iOS can claim
  authenticated relaunch and protected photo access.
- RF-37's accepted restore contract permits PostgreSQL-only restoration into an empty or current
  photo volume after pre-traffic reconciliation. Historical photo-volume snapshots are forbidden
  because they could resurrect revoked photos. Open-consultation photos can be lost in this POC.
- The owner has now proposed moving normalized NextPost photographs from the local Compose volume
  to an existing private AWS S3 bucket used by FormCadence. This is technically viable and likely
  better aligned with NextPost's photo-heavy use, but it changes the accepted RF-37 storage,
  inventory, verified-deletion and restore implementation and therefore requires an explicit
  architecture decision rather than a deployment-only file copy.
- RF-37 cleanup exposes sanitized counters and non-zero overdue/anomaly status, but no deployment
  scheduler or operator alert channel currently consumes it.
- RF-32's restricted removal is implemented as a backend command authorized by deployment/host
  access. The production deployment must preserve that boundary and its server-only
  `REMOVAL_OPERATOR_ID`.
- The current dependency audit has one pre-existing high Vite advisory plus two moderate Vitest
  advisories recorded by the latest review. A release gate must resolve or explicitly accept any
  then-current production-relevant advisory; RF-42 must not silently claim a clean audit.

## FormCadence/FlexGym reference inspection

The neighbouring `C:/Users/anton/Desktop/FlexGym` repository is the FormCadence implementation.
The useful delivery pattern is real and repository-owned:

### Web chain that exists today

`push to main` -> GitHub Actions `Validate` -> backend and frontend checks -> `Deploy to Lightsail`
using GitHub production-environment SSH secrets -> `/opt/flexgym` fetch/reset to `origin/main` ->
`scripts/deploy.sh` -> Compose validation/build/up -> migration on backend startup -> health wait ->
HTTPS frontend/API probes.

FormCadence uses Caddy for public TLS and same-origin `/api/*` routing. Its workflow has one
non-cancelling production concurrency group and also supports manual dispatch.

### iOS chain that is present but not completed

FormCadence commits its Capacitor iOS/Android projects and has `codemagic.yaml` for hosted macOS:
locked npm install -> frontend validation -> Capacitor iOS sync -> build-number update -> App Store
signing -> IPA build -> App Store Connect upload. Signing material remains in Codemagic/Apple secure
interfaces.

However, FormCadence's own project state says the hosted signed build, App Store Connect upload,
TestFlight installation and focused physical-iPhone validation are still pending. This repository is
therefore a strong implementation pattern, not proof that its iOS delivery is operational.

FormCadence also provides a small Boto3 `ObjectStore` abstraction for exact-key S3 `put`, `get` and
`delete`, with a deterministic in-memory fake for tests. It uses the standard AWS credential chain
and keeps object access behind the backend. That is a useful starting boundary. It is not sufficient
unchanged for NextPost: it does not expose `HEAD`/absence verification, object versions, inventory,
unexpected-object reporting or the durable deletion evidence required by RF-37.

### Differences that prevent a blind file copy

- FormCadence currently owns public ports 80/443 through its Compose Caddy service. A second literal
  copy on the same Lightsail host would conflict. Same-host deployment needs one shared host proxy
  (or distinct bound loopback ports); otherwise NextPost needs a separate instance.
- NextPost uses PostgreSQL plus a private local photo volume, not FormCadence's SQLite/S3 shape.
  Migration, backup, restore and filesystem-erasure behavior must follow NextPost's accepted
  contracts.
- FormCadence's current Codemagic export is marked internal-TestFlight-only. Apple documents that
  internal testers must be App Store Connect team users and that an internal-only build cannot be
  used for external testing. Personally invited people outside that team are external testers; the
  first external build requires TestFlight Beta App Review and beta metadata.
- A local ignored FormCadence `.env` contains credentials that appear to be real long-lived AWS
  credentials. They were not found as a tracked file, but they must not be copied or reused. Rotate
  them before relying on that account and keep NextPost production credentials in managed secret
  stores/server-owned configuration only.
- Read-only probes on 2026-10-23 confirmed that AWS CLI is installed and that the saved default
  owner/root login session is expired. The existing FormCadence runtime identity can authenticate,
  but AWS returns `AccessDenied` for bucket versioning, public-access blocking, default encryption,
  Object Lock and lifecycle configuration. No AWS state was changed and no credential value was
  printed. Those least-privilege runtime credentials cannot establish bucket compatibility; an
  authenticated bucket-owner/IAM configuration review remains required before NextPost uploads any
  photograph.
- FormCadence's SSH action is version-tag pinned rather than immutable-commit pinned. The NextPost
  workflow should retain the same observable chain while pinning third-party actions to reviewed
  immutable commits where practical.

## External platform and privacy facts checked during grooming

- Apple allows up to 100 internal testers who are App Store Connect users. Internal-only builds
  cannot later be submitted for external testing.
- External testers can be invited by email or public link; the first build added to an external
  group requires TestFlight Beta App Review. Beta description, review information and a feedback
  email are required for external sharing. TestFlight builds expire after 90 days.
- Apple's review guidance expects a functional backend and review credentials or an approved demo
  alternative for a login-gated app.
- The AEPD treats a person's photograph as personal data and says mobile apps must give concrete
  information on purposes, retention and rights, and provide effective procedures to exercise
  those rights. The EDPB identifies access, erasure and portability among data-subject rights.
- AWS documents strong read-after-write consistency for S3 object `PUT`, `DELETE`, `GET` and
  metadata/`HEAD`, so RF-37 can retain its explicit delete-then-verify contract against S3.
- AWS also documents that deleting a key without a version ID in a versioned bucket only creates a
  delete marker while prior bytes remain retrievable. In a non-versioned bucket deletion is
  permanent. S3 Object Lock can prevent permanent deletion until its retention/hold expires.

These facts do not select NextPost's legal basis or replace legal advice. They do mean that an
invitation-only label does not make RF-34/RF-35, privacy information, a contact channel or an
operational rights-request process disappear.

## Dependencies and conflicts

- DEC-004/014 require one React/Vite application for web and invited iOS TestFlight, with Android
  later.
- RF-06/RF-07/RF-09 retain integrated and physical-iPhone evidence that RF-42 should close rather
  than duplicate or waive.
- RF-26 provides real shared-link entry and return after authentication; production origin and
  native shared-link handling must be validated against it.
- RF-37 defines private-photo erasure, cleanup status, alerting handoff and the non-resurrecting
  restore boundary.
- RF-13, RF-19/RF-20 and RF-21 provide deletion, finalization and private feedback that must be part
  of the end-to-end invited test.
- The restricted RF-32 subset is implemented and technically validated; its operator command and
  cleanup follow-up must be usable in production before real-user exposure.
- RF-34 account deletion and RF-35 data copy/export are not groomed or implemented. RF-42 must
  decide whether beta is blocked until their product surfaces exist or whether a documented manual
  request process is an explicitly accepted temporary beta control.
- RF-38 owns support/feedback preparation and RF-39 owns learning. TestFlight already supplies a
  feedback channel, but web participants and privacy/right requests still need a clearly owned
  contact route.
- Deployment changes are not the place to add invitation codes, an allowlist, email verification,
  categories, notifications, analytics, crash SDKs or a broad admin console.

## Candidate approach

The following reflects the accepted product and operational choices. Bucket compatibility, the
final validation boundary and explicit plan-finalisation approval remain gated below.

### A. Web delivery

1. Add a GitHub Actions workflow on pushes to `main` plus manual dispatch. CI runs locked backend
   install, Ruff, formatting, strict MyPy, complete tests (including a disposable PostgreSQL job for
   migration/concurrency release gates), locked frontend install, tests, formatting, ESLint,
   typecheck, production build and a then-current dependency audit.
2. A non-cancelling `production` deployment job receives only Lightsail SSH host/user/key from a
   protected GitHub environment and runs after CI. Application/database secrets remain only in a
   root/operator-owned environment file on the server.
3. Deploy to a dedicated `/opt/nextpost` checkout. A repository-owned idempotent deploy script
   validates production configuration, obtains the intended `main` revision, builds/starts services,
   applies Alembic, waits for `/api/ready`, verifies the public same-origin frontend/API and reports
   the deployed revision. It creates no database backup and must report migration failure honestly.
4. Put NextPost behind HTTPS with one public origin and route `/api/*` to the backend. PostgreSQL
   stays private; only the backend can access the dedicated S3 namespace through its restricted IAM
   identity. Do not expose backend docs publicly in production unless explicitly selected.
5. Schedule the existing RF-37 cleanup/status command and route exit 1/anomaly/overdue output to an
   operator channel. Treat exit 2 as another maintenance leader, not a privacy incident.
6. Document the accepted no-backup posture and a controlled empty restart: if PostgreSQL becomes
   unusable without an ad hoc valid copy, keep traffic off, purge only the exact `nextpost/` S3
   namespace through a restricted verified procedure, recreate the database and start empty. Never
   imply that application state can be reconstructed from object keys.

### B. iOS delivery

1. Select and register one permanent bundle identifier and App Store Connect record before
   generating the native project.
2. Generate and commit the conventional Capacitor iOS project, build bundled local Vite assets and
   point the native build at the production HTTPS API. Do not use a remote `server.url` WebView.
3. Adopt and test a bounded Capacitor native HTTP/cookie path modelled on FormCadence so the signed
   `HttpOnly` cookie remains outside JavaScript while login, relaunch, logout, photos and Private
   links work. Do not weaken TLS, CORS or cookie flags.
4. Add a Codemagic hosted-macOS workflow using an App Store Connect integration, automatic signing,
   locked dependencies, frontend validation, iOS sync, monotonically increasing build number,
   signed IPA build and upload. Secrets remain only in Codemagic/Apple.
5. Keep iOS promotion manual (the owner's “optionally distribute later” behavior): a normal push
   deploys web after CI; the owner explicitly starts a chosen commit's TestFlight build. For invited
   people outside the App Store Connect team, build for ordinary App Store Connect/TestFlight
   distribution rather than `Internal Testing Only`, supply beta/review metadata and pass the first
   external beta review.

### C. Release evidence

Use a release checklist tied to one Git commit. Prove public TLS, current revision, database
readiness, private photo isolation, the accepted no-backup/empty-restart posture, cleanup alerting
and restricted removal.
On a physical iPhone installed from TestFlight, exercise registration/sign-in/relaunch/logout,
gallery selection including HEIC/HEIF, upload retry, Create/review/publish, Public feed, shared
Public and Private links with auth return, voting, owner counts, finalization/deletion, participant
history, background/foreground, safe areas, keyboard/zoom and an unavailable API recovery. Capture
results without user photo bytes, credentials or link capabilities.

## Questions

### Resolved questions

#### Q1 - Where should the production web stack run?

- **A (accepted 2026-10-23):** reuse the existing
  instance, deploy under `/opt/nextpost`, and replace the per-project public-port ownership with one
  shared host reverse proxy routing the FormCadence and NextPost domains to separate loopback-bound
  Compose ports. Lower cost and matches the owner's stated server; a shared host increases coupled
  outage/maintenance risk and requires careful preservation of FormCadence.
- **B:** use a separate Lightsail instance for NextPost. Cleaner isolation and simpler per-project
  Caddy ownership; higher cost and another host to patch, back up and monitor.

The owner confirmed that current traffic does not justify a second server and that separation can
be reconsidered if traffic grows. The server must be inspected read-only for capacity, OS/proxy
layout and existing backups before finalising the implementation plan; no production mutation is
authorized by grooming. “Same server” does not mean one shared application API or data store:
FormCadence and NextPost remain separate services, databases/configurations and storage boundaries,
with only the host and public reverse proxy shared.

#### Q2 - What exact public web origin should be permanent?

**Accepted 2026-10-23:** the owner does not want to purchase another domain and selected
`https://nextpost.formcadence.app` as the initial production origin. It serves the NextPost web
client and its API under same-origin `/api`; the iOS package uses the same HTTPS API.
This requires only a DNS subdomain and a proxy route, does not interfere with the existing
`https://formcadence.app` product, and preserves RF-26's origin-derived shared links.

The iOS UI need not display the host as product chrome, but the domain is still operationally and
externally visible in network traffic, shared links, Apple review/support information, TLS
certificates and privacy documentation. It therefore remains a real production identity rather
than a hidden implementation detail. The owner accepts that it can be changed later if necessary;
such a change requires coordinated DNS/proxy/CORS/link configuration and a new iOS build, and old
shared links are not silently rewritten.

#### Q3 - Where should normalized NextPost photographs be stored?

- **A (recommended): a dedicated private, non-versioned NextPost S3 bucket in the existing AWS
  account.** PostgreSQL retains only metadata/state/exact opaque keys; originals still disappear
  after normalization; the backend is the only reader/writer and continues to authorize every
  content request. Use a dedicated least-privilege IAM identity, Block Public Access, default
  encryption and no Object Lock/replication/versioning. Advantages: clean isolation, S3 durability
  and independent server replacement/scaling without creating recoverable old photo versions.
  Risks: one new bucket/policy/credential boundary and S3 request/storage/transfer costs.
- **B (accepted 2026-10-23): reuse the existing FormCadence bucket under a dedicated `nextpost/`
  prefix.** Advantages: no new bucket and the account already uses S3. Risks: versioning, Object
  Lock, encryption and public
  access are bucket-wide; a prefix cannot opt out of unsafe version retention. At minimum use a new
  IAM identity restricted to the prefix, never the existing FormCadence key. The owner selected this
  option to keep the operational footprint together and avoid perceived additional cost.
- **C: keep the current private local Compose photo volume.** Advantages: already implemented and
  fully validated by RF-37; no network dependency or S3 changes. Risks: photos are tied to one host
  and accepted disaster recovery may lose every still-open consultation image.

For the accepted B, the backend continues to proxy bytes after authorization for the MVP; no public
object URLs or long-lived presigned URLs are introduced. Implement an object-store boundary with exact
`put/get/head/delete/list-safe-prefix` behavior, delete then strongly consistent absence
verification, retry/anomaly reporting and disposable S3-compatible tests. S3 durability is not an
application backup: no retained retrievable version history or replication may allow revoked photos
to be restored. Before the first NextPost production photo upload, a bucket-owner configuration
review must prove Block Public Access, encryption, versioning, Object Lock, lifecycle and
bucket-policy behavior. If
historical/versioned objects can exist, the implementation must persist/delete the exact version
identity and verify that no retrievable version remains; a current-key 404/delete marker is not
sufficient. This choice updates/supersedes only the local-volume mechanism in DEC-032/041 while
preserving their privacy, minimization and no-historical-photo-restore outcomes.

#### Q4 - What backup and recovery service should hold PostgreSQL backups?

- **A (recommended):** encrypted private object storage in the owner's AWS account, automated daily
  PostgreSQL dumps with a short explicit retention plus a pre-deploy dump; no photo-volume backup.
  Rehearse restore into an empty photo volume before beta.
- **B:** Lightsail database-only snapshots/export if they can be proven not to capture/restore the
  photo volume and can meet the same retention/rehearsal contract.
- **C (accepted 2026-10-23): no durable database backup for the invited beta.** Lowest effort but
  account, consultation, vote, outcome, removal audit and S3-object ownership data can be lost. The
  owner explicitly accepts that a lost/corrupt PostgreSQL volume may require purging the isolated
  NextPost S3 prefix and restarting the product from empty; no recovery or continuity is promised.

No scheduled/pre-deploy dump, snapshot, restore service, retention or backup alert is included.
Ordinary PostgreSQL volume persistence across container restart remains, but it is not a backup.
The existing RF-37 database-only restore procedure remains valid only if an ad hoc valid database
copy happens to exist; RF-42 creates and promises none.

#### Q5 - How automatic should each distribution path be?

- **A (accepted 2026-10-23):** every push to `main` runs CI and automatically deploys web on success;
  TestFlight is manually started for a selected `main` commit. This matches the stated FormCadence
  behavior and avoids sending every commit to Apple.
- **B:** web and TestFlight both run on every successful main push. Fast but expensive/noisy and can
  consume build minutes and create excessive beta builds.
- **C:** web is automatic; TestFlight starts only from an explicit version tag. Stronger release
  identity, with a little more ceremony than manual selection.

#### Q6 - Who are the first iOS testers?

- **A:** only the product owner or existing App Store Connect team members. Internal TestFlight is
  sufficient for the first device proof but does not distribute to ordinary invited users.
- **B (accepted 2026-10-23):** a mixture that may include both App Store Connect team members and
  people outside the team.
  Prepare external TestFlight, required beta/review/contact metadata, review credentials and the
  first TestFlight Beta App Review. Do not grant product testers App Store Connect roles merely to
  avoid review. The same eligible build may be assigned to separate internal and external groups;
  it must not use the irreversible `TestFlight Internal Only` export option.

#### Q7 - What permanent Apple identity and account assets already exist?

**Accepted 2026-10-23:** use the same Apple Developer account/team and Codemagic account/integration
infrastructure as FormCadence, but create a completely separate NextPost App ID and App Store
Connect application record. The preferred permanent bundle identifier is `app.nextpost`, replacing
the repository's provisional `com.nextpost.app`. The visible app name is `NextPost`.

The existing FormCadence App ID, record, bundle, builds, tester groups and metadata must not be
reused or modified for NextPost. `app.nextpost` must be checked for availability in the selected
Apple team before native generation. If Apple rejects or reserves it, stop and return to the owner
with the exact conflict and a small set of neutral alternatives; do not silently fall back to the
rejected `app.formcadence.nextpost` naming. Creating the identifier, App Store Connect record,
Codemagic application/integration binding or signing material is a later authorized external action,
not part of grooming.

#### Q8 - May RF-42 adopt the FormCadence native HTTP/cookie architecture?

- **A (accepted 2026-10-23):** bundled local assets plus Capacitor's native HTTP bridge for the
  production API, preserving the `HttpOnly` cookie outside JavaScript and validating it on the real
  device.
- **B:** use WebView/browser fetch directly. Simpler code, but cross-origin cookie behavior is a
  known delivery risk and cannot be approved without a successful focused prototype proving every
  auth/photo/link flow.
- **C:** redesign authentication for native tokens. This is a substantial security/product change
  and not recommended inside RF-42.

#### Q9 - What minimum privacy/account readiness blocks invited beta?

- **A (accepted 2026-10-23):** before inviting external users, publish a plain-language privacy
  notice and use `xnegis@gmail.com` as the monitored support, feedback and privacy contact.
  The notice identifies controller, purpose, retention and processors. Authenticated access/export
  and account/data erasure requests use an executable manual, audit-safe operator process. Groom
  RF-34/RF-35 immediately if that process cannot satisfy the accepted product/data contracts. No
  full self-service UI is implied by this option.
- **B:** require implemented self-service RF-34 account deletion and RF-35 export before beta.
  Stronger user control and less operator work, but delays delivery and expands the prerequisite
  implementation set.
- **C:** invite users without those processes because the beta is personal/invitation-only. This is
  not recommended; invitation does not remove privacy and rights obligations.

#### Q10 - Which operator channels own failures and tester feedback?

- **Accepted 2026-10-23:** `xnegis@gmail.com` is the single beta destination for (a) web deploy
  failure, (b) backend/readiness failure, (c) RF-37 overdue deletion/anomaly status, (d) S3/storage
  failure, and (e) user/TestFlight feedback and privacy requests. RF-42 must prove the chosen
  automated delivery mechanism reaches that inbox, but does not require operating a custom mail
  server or adding an in-product chat/notification system.

#### Q11 - What is the release/rollback rule for `main`?

- **A (accepted 2026-10-23):** protect `main`, require the complete CI gate, allow one production deploy at
  a time, record the deployed SHA, and roll forward from a corrective commit. If a migration is
  involved, do not pretend a code rollback reverses it. With no valid ad hoc database copy, the
  accepted disaster path is traffic-off purge of the exact NextPost S3 namespace and an empty
  database restart; never restore old photo bytes.
- **B:** permit server-side rollback to a previous Git commit. Faster for code-only failures, but
  unsafe once migrations or irreversible terminal cleanup have executed unless every release proves
  compatibility. This cannot be a blanket rule.

### Resolved

- 2026-10-23: RF-42 is the selected ticket.
- 2026-10-23: the delivery targets are both web and iOS; Android remains out of scope.
- 2026-10-23: the desired model is the FormCadence/FlexGym chain: GitHub-based push delivery for the
  web application and an optional separately invoked iOS/TestFlight distribution path.
- 2026-10-23 (`Q1A`): FormCadence and NextPost will run on the same existing Amazon/Lightsail
  instance while traffic remains modest. They keep separate APIs, processes, configuration,
  databases and storage; one shared HTTPS reverse proxy routes each permanent domain to its own
  loopback-bound stack. A separate host can be reconsidered if measured traffic or operational risk
  later justifies it.
- 2026-10-23 (`Q2`): no separate domain will be purchased. The initial canonical NextPost web/API
  origin is `https://nextpost.formcadence.app`, with same-origin `/api`. A later change is allowed
  through an explicit coordinated deployment and new iOS build; compatibility of old shared links
  is not assumed.
- 2026-10-23 (`Q3B`): normalized NextPost photos move from the server-local private volume to the
  existing FormCadence S3 bucket under a dedicated `nextpost/` namespace. NextPost receives a new
  least-privilege IAM identity restricted to that prefix; it does not reuse FormCadence's access
  key. Backend-only authorization, no public object URL, permanent verified deletion and no
  historical-photo restore remain binding. Final design depends on a bucket-owner review of
  versioning/Object Lock/lifecycle; every retrievable version must be deleted if versions exist.
- 2026-10-23 (`Q4C`): the invited beta has no PostgreSQL backup automation or recovery promise. A
  lost/corrupt database may require purging the NextPost S3 prefix and restarting accounts and all
  product state from empty. Container-volume persistence is not presented as a backup.
- 2026-10-23 (`Q5A`): every successful `main` push deploys the web stack after its complete CI gate;
  an iOS/TestFlight build is started manually for a selected `main` commit.
- 2026-10-23 (`Q6B`): iOS testing may include both internal App Store Connect team members and
  ordinary external invitees. Builds must remain eligible for external TestFlight, with beta/review
  metadata, review credentials/contact and the first external TestFlight Beta App Review; do not
  export them as internal-only.
- 2026-10-23 (`Q7`): reuse the existing Apple Developer team and Codemagic account/integration
  infrastructure, but create a new independent NextPost App ID and App Store Connect app. Preferred
  permanent bundle ID: `app.nextpost`; visible name: `NextPost`. FormCadence's app record and builds
  remain untouched. If `app.nextpost` is unavailable, return to the owner rather than silently
  selecting another identity.
- 2026-10-23 (`Q8A`): the iOS app packages local versioned Vite assets and uses Capacitor's native
  HTTP bridge for `https://nextpost.formcadence.app/api`, preserving the signed `HttpOnly` session
  cookie outside JavaScript. Browser delivery keeps normal same-origin fetch. No token redesign,
  remote production WebView, TLS weakening, permissive CORS or `SameSite=None` shortcut is accepted.
- 2026-10-23 (`Q9A`): external invitations require a published plain-language privacy notice and an
  executable manual process for authenticated access/export and account/data erasure requests.
  `xnegis@gmail.com` is the monitored human contact for support, tester feedback and privacy,
  and is also used for TestFlight contact metadata. RF-42 does not add self-service RF-34/RF-35 UI.
- 2026-10-23 (`Q10`): `xnegis@gmail.com` is also the single private beta destination for automated
  deploy, readiness, RF-37 overdue/anomaly and S3/storage failure alerts. Delivery to that inbox must
  be validated; RF-42 adds neither a custom mail server nor an in-product notification system.
- 2026-10-23 (`Q11A`): `main` is protected by the complete CI gate, production deploys are
  serialized and the deployed SHA is recorded. Failures roll forward through a corrective commit;
  code rollback is not treated as migration rollback. Without a valid ad hoc database copy, the
  accepted disaster procedure is traffic-off verified purge of the exact NextPost S3 namespace and
  an empty database restart, never restoration of old photo bytes.
- 2026-10-23: the owner accepted the unavailable authenticated S3 inspection as a hard pre-upload
  activation gate and explicitly asked Codex to complete all other work. This accepts the preserved
  Trello snapshot, settled scope, exclusions and validation matrix, authorizes plan finalisation and
  authorizes autonomous harness implementation. It does not authorize external deployment or
  account/service mutations.
- 2026-09-22 (DEC-014): iOS delivery is invited TestFlight, not public App Store release.

## Proposed scope

### In scope

- Production-ready GitHub CI and automated web deployment for the selected topology/domain.
- HTTPS reverse proxy, server-owned production configuration and secret boundaries.
- Explicit no-backup/no-recovery production posture, safe empty restart/purge procedure and no
  photo backup/history that can resurrect revoked content.
- RF-37 scheduled status/alert integration and RF-32 production runbook verification.
- Permanent iOS identity, generated committed Capacitor iOS project and production mobile config.
- Hosted signed build/upload workflow and the selected internal/external TestFlight path.
- Physical-iPhone and complete two-account invited-journey validation tied to one release SHA.
- Minimal release, recovery, operations, privacy/support and tester instructions.

### Out of scope

- Android project generation/distribution unless Capacitor tooling requires harmless shared config;
  no Android store release or device gate.
- Public App Store release, paid apps, subscriptions or marketing launch.
- Invitation codes, technical allowlist, forced email verification or automated invitation sending.
- New product analytics/dashboard, push notifications, crash/analytics SDKs or user tracking.
- Broad moderation/admin UI, account roles, reports/cases or account suspension.
- Silent implementation of RF-34/RF-35 product scope beyond an explicitly approved minimum manual
  beta process.
- Photo-volume backup, historical photo restore or any storage path that can resurrect revoked
  photos.
- Deployment, build upload, tester invitation, credential creation, DNS mutation, commit, push or
  Trello mutation during grooming.

## Validation outline

### Repository and CI

- Workflow syntax and least-privilege permissions; immutable action pins; concurrency and failure
  behavior; no secret values in logs/artifacts.
- Complete backend/frontend checks plus disposable PostgreSQL migration/concurrency release tests.
- Production and mobile builds contain only the intended public API origin and no credentials,
  localhost/LAN fallback or private capabilities.

### Web deployment

- Fresh and incremental deploy, idempotent rerun, unhealthy backend failure, migration failure and
  public probe failure all leave an observable, recoverable state.
- TLS, canonical redirect, same-origin API, SPA deep-link fallback, Secure cookie, trusted Origin,
  private PostgreSQL and backend-only photo volume are verified from outside and inside the stack.
- The no-backup posture and controlled exact-prefix empty restart, RF-37 scheduled run/exit handling
  and RF-32 command are exercised on disposable data before ordinary production use.

### iOS

- Clean Codemagic build on hosted macOS, signing identity/provisioning inspection, App Store Connect
  upload and selected TestFlight group availability.
- Real TestFlight installation and the complete device matrix listed in Candidate approach C,
  including authenticated relaunch, HEIC/HEIF and shared Private links.
- External beta review and metadata/contact evidence for the accepted mixed internal/external
  tester model.

### Invited end-to-end proof

- At least two non-production test accounts execute author and voter roles through web and iPhone;
  evidence covers publication, discovery/share, immutable vote, counts, finalization or deletion,
  participant history, access revocation and physical-erasure convergence.
- Validate failure and recovery without recording real user photos, credentials, cookies, private
  capabilities or personal tester feedback in repository artifacts.

## Readiness checklist

- [x] Desired outcome and requested reference implementation identified.
- [x] Current repository and FormCadence delivery code inspected.
- [x] Relevant delivery, media-erasure, removal and native dependencies identified.
- [x] Material topology, iOS, data, privacy, operations and rollback questions consolidated.
- [x] Owner accepted the preserved 2026-10-12 Trello snapshot while authenticated refresh remains
      unavailable.
- [x] Production host topology confirmed: existing shared Lightsail host with isolated stacks and a
      shared reverse proxy.
- [x] Initial canonical origin confirmed as `https://nextpost.formcadence.app`.
- [x] Production photograph storage selected: existing private S3 bucket, isolated `nextpost/`
      prefix and dedicated least-privilege IAM identity.
- [x] Bucket compatibility contract resolved: owner-authenticated verification is an explicit hard
      gate before the first production upload; implementation must fail closed until it passes.
- [x] No PostgreSQL backup/recovery service selected; accepted beta data-loss/empty-restart posture
      recorded.
- [x] Web/iOS trigger policy confirmed: web on successful `main`, TestFlight manual.
- [x] Tester class confirmed: mixed internal and external TestFlight groups.
- [x] Apple team/Codemagic reuse and separate NextPost app identity confirmed; preferred permanent
      bundle ID is `app.nextpost`, subject to Apple availability check.
- [x] Native HTTP/authentication approach confirmed: packaged assets plus Capacitor native HTTP and
      server-owned `HttpOnly` cookie.
- [x] Minimum privacy/account-readiness gate confirmed: published notice, manual rights process and
      `xnegis@gmail.com` contact.
- [x] Operator/support channels confirmed: `xnegis@gmail.com` for human contact and automated beta
      operational alerts, with delivery validation required.
- [x] Release/rollback policy confirmed: serialized SHA-recorded deploy and corrective roll-forward;
      migrations are not reversed by code rollback.
- [x] Scope, exclusions and complete validation matrix confirmed.
- [x] No material question remains.
- [x] Product owner explicitly approved plan finalisation and autonomous harness implementation.
