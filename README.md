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
