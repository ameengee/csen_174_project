# Backend

FastAPI service for the CSEN 174 project.

## Quick Start

### Docker (recommended)

```bash
cd backend
cp docker/env/.env.example docker/env/.env.local   # already done once; edit as needed
docker compose -f docker/compose/docker-compose.local.yml up --build
curl http://localhost:8000/healthz
```

This starts the API on `:8000` (with hot reload from `src/`) and Postgres on `:5432`.

### Without Docker

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements/local.txt
PYTHONPATH=src uvicorn backend.main:app --reload --port 8000
```

Settings come from environment variables (see `src/backend/configs/settings.py`); every field
has a local default, so the app boots without an env file. Without Postgres running,
`/healthz/ready` reports `503`.

## Checks

```bash
./scripts/ci/format.sh   # black
./scripts/ci/lint.sh     # ruff
./scripts/ci/type.sh     # mypy
./scripts/ci/unit.sh     # pytest + coverage
./scripts/run_all_checks.sh   # all of the above inside the test Docker image
```

## Project Structure

```
backend/
├── src/backend/
│   ├── clients/          # External service clients (Postgres pool) + init/close manager
│   ├── configs/          # Settings, constants, logging, exceptions, shared types
│   ├── database/         # SQL query functions
│   ├── managers/         # RuntimeManager: self-restarting background workers
│   ├── services/         # Business logic; routes call these
│   ├── server/
│   │   ├── middleware/   # Request logging
│   │   ├── routes/       # One module per domain; assembled in router.py
│   │   ├── rate_limit.py # slowapi limiter + per-endpoint limits
│   │   └── router.py
│   ├── utils.py          # async_with_retries, fire_and_forget
│   └── main.py           # App, lifespan, middleware, exception handlers
├── tests/
├── docker/               # Dockerfiles, compose files, env files, entrypoint
├── requirements/         # prod.txt, local.txt (prod + dev tools)
└── scripts/ci/           # format / lint / type / unit
```

## Adding a route

1. Create `src/backend/server/routes/<domain>.py` with `router = APIRouter(prefix="/api/<domain>")`.
2. Put logic in `src/backend/services/<domain>_service.py` and queries in `src/backend/database/`.
3. Register it in `src/backend/server/router.py`.
