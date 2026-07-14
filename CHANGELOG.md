# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive code review document (`download/COMPREHENSIVE_CODE_REVIEW.md`).
- Real authentication system with JWT + bcrypt password hashing.
- `get_current_user` / `get_current_admin` FastAPI dependencies with per-tenant isolation.
- Alembic initial migration (`api/migrations/versions/0001_initial.py`).
- `/metrics` endpoint serving Prometheus-format metrics.
- `/metrics/json` endpoint for in-memory workflow metrics.
- Clerk webhook signature verification via `svix`.
- `middleware.ts` for the Next.js app (Clerk v4 `withClerkMiddleware`).
- `app/error.tsx`, `app/not-found.tsx`, `app/loading.tsx`.
- `@radix-ui/react-switch` dependency and a proper `Switch` UI primitive.
- `.gitignore`, `.dockerignore` (root + per-service), `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`.
- `.env.example` for backend and frontend.
- Tests for: encryption round-trip, JWT auth, password hashing, workflow engine with real DB.
- `hash_password` / `verify_password` using `bcrypt` directly (avoids passlib/bcrypt-4.x incompatibility).
- Redis-backed OAuth state store (with in-memory fallback for tests).
- Workflow engine now chains step outputs into next step's inputs via `save_as` + `input_from`.
- Workflow engine now tries real Anthropic / OpenAI before falling back to mock.
- Worker now uses the API's `run_id` (no longer generates a phantom one).
- Worker now uses `autoretry_for` + `retry_backoff` + `retry_jitter`.
- Worker now closes its DB session in a `finally` block.

### Changed
- Replaced hardcoded `tenant_id="test-tenant-id"` / `user_id="test-user-id"` with real auth.
- Renamed reserved `metadata` column to `extra_metadata` on `Connection`, `WorkflowRun`, `WorkflowStep`, `Artifact`.
- Replaced `DateTime.utcnow()` with `datetime.now(timezone.utc)`.
- Replaced `.from_orm()` with `.model_validate()` (Pydantic v2).
- Replaced `class Config:` with `model_config = ConfigDict(...)` on Pydantic models.
- Replaced in-memory `oauth_states` dict with Redis-backed store.
- Dropped `prefix="/..."` from each router (now only added in `main.include_router`).
- Reordered `routes/workflows.py` so `/templates`, `/stats`, `/runs` come before `/{workflow_id}`.
- `Settings.DEBUG` now defaults to `False` (was `True`).
- `Settings.ENCRYPTION_KEY` is now optional in dev (auto-derived from `JWT_SECRET`) and required in production.
- `Settings.DATABASE_URL` now defaults to `sqlite:///./verxlite.db` (was a required field that crashed startup).
- `Settings` now uses `SettingsConfigDict` with `extra="ignore"`.
- `connection.is_expired` now compares timezone-aware datetimes correctly.
- `User.full_name` returns `""` (not `"None None"`) when both parts are None.
- `WorkflowEngine.__init__` now accepts an optional `db` parameter for testability.
- `WorkflowEngine.execute_workflow` now accepts an optional `run_id` to update an existing run.
- `models/workflow.py` now imports `Integer`.
- `models/tenant.py` & `models/user.py` use `text()` for partial-index `postgresql_where` (was a `NameError`).
- `models/artifact.py` now imports `Integer`.
- SQLAlchemy `Enum` columns now use `values_callable` so they store enum VALUES, not NAMES.
- `tests/conftest.py` now uses `StaticPool` for the in-memory SQLite engine (tables were being dropped between connections).
- `tests/conftest.py` now overrides `get_db` so route tests use the test session.
- `web/app/layout.tsx` now puts `ClerkProvider` inside `<body>` and adds SEO metadata.
- `web/app/login/page.tsx` and `web/app/sign-up/[[...sign-up]]/page.tsx` fixed the `appearance={{ ... }}` JSX syntax error.
- `web/app/workflows/page.tsx` fixed the broken template-literal className and the JSX-comment-in-ternary syntax error.
- `web/app/{dashboard,workflows,connections,settings}/page.tsx` now gate auth redirects on `isLoaded && !isSignedIn`.
- `web/Dockerfile` now uses multi-stage build, non-root user, `HEALTHCHECK`, and tolerates a missing `package-lock.json`.
- `api/Dockerfile` multi-stage with non-root user and `HEALTHCHECK`.
- `docker-compose.yml` no longer reinstalls deps at every `up`.
- `docker-compose.yml` `NEXT_PUBLIC_API_URL` now points at `http://localhost:8000` (browser-reachable).
- `api/pyproject.toml` added `alembic`, `pyjwt`, `email-validator`, `prometheus-client`, `slowapi`, `greenlet`, `svix`, `python-multipart`; removed dead `langgraph`.
- CI/CD now runs `pytest` from the repo root (was `cd api` → 0 tests collected).

### Removed
- Dead `langgraph ^0.0.10` dependency.
- Dead `@radix-ui/react` meta-package.
- Broken `services/__init__.py` imports of non-existent `google_connector.py` / `hubspot_connector.py`.
- Three binary PDFs from the repo root (now in `.gitignore`).
- Hardcoded `postgresql://postgres:postgres@localhost` URL from `alembic.ini`.

### Fixed
- 20 CRITICAL backend bugs (see `download/COMPREHENSIVE_CODE_REVIEW.md` for the full list).
- 7 CRITICAL frontend bugs (appearance syntax error, Switch primitive, template literal, auth redirect, middleware, Dockerfile, layout).
- 4 CRITICAL worker bugs (disconnected from API, phantom run_id, broken package layout, broken `__init__.py`).
- 6 CRITICAL infra bugs (no `.gitignore`, committed PDFs, broken Dockerfile, broken worker package, missing LICENSE, broken CI test job).

## [0.1.0] — initial commit

- Basic backend structure with mocked workflow engine.
- Basic frontend structure with mocked data.
- Basic worker (disconnected).
- Docker configuration.
- CI/CD pipeline (misconfigured).

[Unreleased]: https://github.com/gadda00/verxlite/compare/HEAD
[0.1.0]: https://github.com/gadda00/verxlite/releases/tag/v0.1.0
