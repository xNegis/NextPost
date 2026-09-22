# Architecture

## Status

The MVP foundation is accepted and implemented as a small monorepo. It follows the useful
frontend/backend/database separation from FlexGym while selecting technology for NextPost's web,
iOS, and Android delivery requirements.

## Implemented baseline

- `frontend/`: one React and TypeScript application built with Vite. Capacitor packages and
  configuration allow this same application to become the iOS and Android client later.
- `backend/`: a FastAPI HTTP API with SQLAlchemy session management and Alembic migrations.
- PostgreSQL 18 is the relational system of record for local development.
- `docker-compose.yml` starts PostgreSQL, applies migrations before API startup, and serves the
  production frontend through Nginx.
- `/api/health` is the process liveness probe. `/api/ready` also verifies database connectivity.

The provisional Capacitor application ID is `com.nextpost.app`. Native `ios/` and `android/`
projects remain deliberately ungenerated until the permanent application ID and signing setup are
chosen.

DEC-014 now sets the first usable phase-2 delivery targets as web and invited iOS TestFlight. The
permanent iOS application ID, signing setup, native project generation, device validation, and
distribution are therefore phase-2 planning dependencies. Android packaging remains later.

No worker, message broker, or asynchronous job system exists in the MVP baseline. Introduce one
only when an approved feature and measured workload require it; do not design current features
around a hypothetical future worker.

## Boundaries to consider during feature grooming

- Client application and user experience.
- Authentication, sessions, and account lifecycle.
- Application/domain services for consultations, audiences, voting, and results.
- Relational persistence and transactional invariants.
- Private temporary upload and normalized-image storage; uploaded originals are discarded after
  processing (DEC-016), and consultation images are removed on finalization/deletion (DEC-021).
- Image validation, orientation, metadata removal, and derivative generation.
- Background lifecycle work such as physical deletion of abandoned or withdrawn image data;
  automatic consultation expiry is deferred by DEC-017.
- Authorization, blocking, reporting, moderation, and audit boundaries.
- Configuration, observability, deployment, and backup/restore.

## Baseline engineering principles

- Keep product rules independent from HTTP handlers and UI components where practical.
- Enforce ownership and authorization on the server for every protected operation.
- Treat retries and concurrent submissions explicitly for publication, voting, and destructive actions.
- Store times in an unambiguous form and define the user-facing timezone behaviour.
- Keep private files outside public web roots and avoid exposing storage credentials or internal keys.
- Make retention and deletion behaviour testable and operationally recoverable.
- Prefer the simplest architecture that satisfies the currently approved plan.

Any change to the accepted stack or deployment boundaries must be recorded in `03_DECISIONS.md`
before its implementation plan is handed to the harness.
