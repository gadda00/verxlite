# Verxlite API

The FastAPI backend for [Verxlite](https://github.com/gadda00/verxlite) —
the universal AI workflow agent for sales & ops.

## Stack

- **FastAPI** 0.109 — async API framework
- **SQLAlchemy** 2.x — ORM (PostgreSQL in prod, SQLite in dev)
- **Alembic** — migrations
- **Pydantic** v2 — schemas & validation
- **Celery** — background workers (via Redis broker)
- **bcrypt** + **PyJWT** — auth (with Clerk webhook support)
- **Langfuse** — LLM observability
- **prometheus-client** — metrics

## Layout

```
api/
├── main.py                       # FastAPI entrypoint
├── alembic.ini
├── migrations/                   # Alembic migrations
│   └── versions/0001_initial.py
├── verxlite_api/
│   ├── config.py                 # Pydantic Settings
│   ├── deps.py                   # get_current_user, get_current_admin, hashing
│   ├── db/                       # Base, session
│   ├── models/                   # SQLAlchemy models (7 tables)
│   ├── schemas/                  # Pydantic request/response schemas
│   ├── routes/                   # auth, connections, workflows, artifacts
│   ├── services/workflow_engine.py
│   ├── connectors/               # Google Workspace, HubSpot CRM
│   ├── observability/            # Langfuse, Prometheus metrics
│   └── utils/                    # encryption, logger
└── pyproject.toml
```

## Quick start

```bash
poetry install
cp .env.example .env  # then edit
poetry run alembic upgrade head
poetry run uvicorn main:app --reload
```

API docs at <http://localhost:8000/docs>.

## Tests

Tests live at the repo root (`tests/`). Run from the repo root:

```bash
PYTHONPATH=api:. poetry run pytest tests/ -v
```

## Environment

See [`.env.example`](.env.example) for all variables.
