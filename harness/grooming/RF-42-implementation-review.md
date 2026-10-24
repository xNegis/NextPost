# RF-42 - Web and iOS delivery - Implementation Review

## Status

`Implementation review - production web/API deployed; iOS and invited-beta gates pending`

The product owner explicitly authorized direct coordinator implementation after two approved
OpenCode Go launches failed before inference because the provider quota was exhausted. This review
covers repository implementation, validation and the first production web/API deployment. It does
not claim Apple registration, signed upload, TestFlight invitation or physical-iPhone acceptance.

## Scope and acceptance review

- GitHub Actions now gates pull requests and `main` with backend, PostgreSQL, frontend, mobile,
  audit, Compose and image-build checks. Production deployment is protected, serialized,
  non-cancelling, exact-SHA SSH delivery with immutable action pins and failure notification.
- Production Compose isolates PostgreSQL on an internal network, exposes frontend/backend only on
  loopback and gives the backend a separate egress-capable application network for S3. The shared
  host Caddy fragment routes the canonical origin and the future Apple association file without
  competing for ports 80/443.
- The deploy script validates configuration, checks out the requested full SHA, migrates through
  startup, waits for health, verifies the revision label, probes public TLS endpoints and records
  the deployed SHA. Recovery is corrective roll-forward; no PostgreSQL backup was added.
- Production normalized-photo storage is selected through a factory and fixed to the private
  `nextpost/normalized/` namespace. S3 reads and writes remain backend-only. Permanent deletion
  inventories and deletes every exact version and delete marker and verifies both version absence
  and current-object absence before reporting success. Local filesystem behaviour remains the
  development/test default.
- S3 production configuration fails closed unless the owner preflight is explicitly approved. The
  read-only preflight checks public access, policy status, encryption, versioning, Object Lock
  default retention, lifecycle readability, replication and version-inventory permission without
  printing credentials, keys or content. The dedicated exact-prefix IAM policy and controlled
  canary procedure are documented but were not applied.
- RF-37 maintenance has a host scheduling wrapper with distinct healthy, busy and incident exits.
  A provider-neutral HTTPS alert command sends bounded, sanitized events to the configured delivery
  service for `xnegis@gmail.com`; no mail credential or vendor is embedded.
- A public privacy page and restricted manual rights procedure cover photographs, service
  processors, retention/deletion and authenticated access/export/erasure requests without claiming
  the deferred self-service tickets.
- Capacitor now consistently uses `app.nextpost` and `NextPost`, bundled mobile assets, the canonical
  HTTPS API origin and native HTTP. Universal-link routing accepts only the canonical privacy and
  consultation paths. The conventional iOS project, associated-domain entitlement, photo-library
  explanation and Apple association template are committed artifacts.
- Codemagic has a manual hosted-macOS workflow for a selected `main` SHA, locked frontend install,
  shared checks, iOS sync, monotonic build number, automatic App Store signing, ordinary
  external-capable IPA and App Store Connect publishing. It does not use the irreversible
  internal-only export option.
- Operations, privacy, TestFlight, physical-device, release-evidence, S3 cutover and accepted
  empty-restart procedures are documented. All external mutations remain explicit gates.

## Validation evidence

- Backend Ruff check/format and strict MyPy passed.
- Complete backend suite passed twice: 577 passed with PostgreSQL-only cases skipped locally, then
  654 passed against a disposable PostgreSQL 18 instance. A pre-existing Alembic in-process logging
  side effect exposed by the complete matrix was corrected so cleanup/security loggers remain
  observable.
- Frontend passed 47 test files / 602 tests, Prettier, ESLint, TypeScript, web build and canonical
  mobile build.
- `npm audit --audit-level=high` reports zero vulnerabilities after non-major Vite/Vitest updates.
- Capacitor iOS synchronization completed and discovered `@capacitor/app` with the generated
  bundle identifier and entitlements intact.
- Development and production Compose validation passed; both production images built.
- An isolated production-shaped Compose smoke passed PostgreSQL migration, backend health
  (`/api/ready` 200), frontend serving (200), loopback-only frontend/backend publication and no
  PostgreSQL host binding. Its containers, networks and volume were removed afterwards.
- Credential-pattern inspection found no committed private key or AWS access key. No real AWS
  credential was printed or committed.
- On 2026-10-24 the owner-authenticated real-bucket preflight passed every configuration check. A
  dedicated `nextpost-production` IAM user and exact-prefix inline policy were created. A CLI
  canary and the real `S3PhotoStorage` implementation both proved encrypted write/read and
  permanent all-version deletion; final inventories contained zero current objects, versions and
  delete markers. The dedicated credential is installed in the protected production host
  environment; no credential was printed or committed.
- Cloudflare publishes the DNS-only `nextpost.formcadence.app` A record. The shared FormCadence
  Caddy container joins a dedicated proxy network and routes only NextPost frontend/backend aliases;
  PostgreSQL remains on an internal-only network. FormCadence stayed healthy throughout.
- GitHub Actions run `40079783618` passed backend, frontend, Compose and production deployment for
  exact SHA `031827db83b3567db42bb97ebf62da7a56314342` after two evidence-producing correction runs.
  Production reports healthy database/backend containers, a running frontend, public TLS readiness
  with `{"status":"ok"}`, HTTP 200 web serving and the expected browser-rendered sign-in UI.

## External activation gates

1. Install the host cleanup schedule and a real alert delivery adapter; run a controlled failure and
   confirm sanitized delivery to `xnegis@gmail.com`.
2. Confirm `app.nextpost` availability, create the separate Apple/App Store Connect record, replace
   the Apple Team ID in the association file, configure Codemagic signing and run the manual build.
3. Complete external TestFlight review/invitations and the documented physical-iPhone matrix on the
   same recorded Git SHA.

## Final assessment

The approved repository scope, real S3 compatibility gate and first production web/API deployment
are implemented and validated. RF-42 remains in implementation review because iOS distribution,
invited TestFlight use and private alert delivery still depend on the external gates above. External
mutations performed were the scoped IAM identity/policy and erased canaries, protected host/GitHub
configuration, shared proxy integration, Cloudflare DNS record, commits/pushes and the recorded web
deployment. No Apple/Codemagic mutation, build upload, invitation, email delivery or Trello change
was performed.
