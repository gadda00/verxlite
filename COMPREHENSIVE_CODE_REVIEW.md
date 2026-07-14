# Verxlite — Comprehensive Code Review (10-Person Team Dissection)

**Repository:** `github.com/gadda00/verxlite`
**Branch reviewed:** `main` @ `aad0ef7`
**Date:** 2026-07-14
**Reviewers:** 3 parallel sub-teams (Backend / Frontend / Infra+Worker+Docs) emulating a 10-person review squad.
**Verdict:** The project is at a "mock prototype" stage that **does not boot, does not build, and does not pass its own tests**. There are ~20 CRITICAL defects in the backend, 7 CRITICAL defects in the frontend, and the Celery worker is fully disconnected from the API. The audit checklist shipped with the repo (`AUDIT_CHECKLIST.md`) is honest about feature gaps but understates the number of build-breaking bugs.

This document is the dissection. Phase 2 (the "20-developer fix squad") work is committed to the same branch immediately after this review.

---

## 0. Executive Summary

| Area | Status | CRITICAL | HIGH | MEDIUM | LOW |
|------|--------|----------|------|--------|-----|
| Backend (FastAPI) | **Does not boot** | 20 | 36 | 40 | 43 |
| Frontend (Next.js) | **Does not build** | 7 | 16 | 27 | 30 |
| Worker (Celery) | **Disconnected** | 4 | 4 | 8 | 3 |
| Infra / Docker / CI | **Broken** | 6 | 12 | 7 | 6 |
| Docs | **Inaccurate** | 0 | 5 | 4 | 3 |
| **TOTAL** | — | **37** | **73** | **86** | **85** |

The single biggest issue: **the application cannot start.** `models/workflow.py` references `Integer` without importing it, `models/connection.py` and `models/artifact.py` declare a column literally named `metadata` (reserved on SQLAlchemy's `DeclarativeBase`), `connectors/google.py` and `connectors/hubspot.py` contain `async with` inside a synchronous function (a `SyntaxError` at parse time), and `main.py` mounts a `static/` directory that does not exist. Any one of these aborts startup; the project has all of them.

---

## 1. Backend (FastAPI) — 20 CRITICAL bugs

The backend review found 139 issues total. Highlights below; the full per-file list is in `/home/z/my-project/worklog.md`.

### 1.1 The app cannot start

**C1. `models/workflow.py:5,75` — `Integer` used but never imported**
```python
priority = Column(Integer, default=5, nullable=False)  # NameError at import
```
Imports at top: `Column, String, Text, Boolean, ForeignKey, JSON, DateTime, Index, Enum` — no `Integer`. The `workflow` module is imported transitively by `models/__init__.py`, which is imported by `services/workflow_engine.py`, which is imported by `routes/workflows.py`, which is imported by `main.py`. The entire app crashes on `uvicorn main:app`.

**C2. `models/connection.py:52` & `models/artifact.py:83` — column named `metadata`**
```python
metadata = Column(JSON, nullable=True)  # SQLAlchemy reserved attribute
```
`DeclarativeBase` already defines `metadata` as a class-level `MetaData` instance. Redeclaring it as a column raises `InvalidRequestError: Cannot place column 'metadata' on both …`.

**C3. `connectors/google.py:71-75` & `connectors/hubspot.py:67-72` — `async with` in sync function (SyntaxError)**
```python
def _refresh_access_token(self) -> str:
    ...
    async with httpx.AsyncClient() as client:
        response = client.post(...)   # also missing await
```
This is a hard `SyntaxError`. Python refuses to import the module. Both connector files are dead.

**C4. `services/__init__.py:6-7` — imports non-existent modules**
```python
from verxlite_api.services.google_connector import GoogleConnector
from verxlite_api.services.hubspot_connector import HubSpotConnector
```
Those files do not exist (the real connectors live in `connectors/`). Importing `verxlite_api.services` raises `ModuleNotFoundError`.

**C5. `routes/auth.py:10` — `import jwt` but `pyjwt` not in deps**
`pyproject.toml` declares `python-jose` (unmaintained) but not `pyjwt`. The auth route crashes at import.

**C6. `routes/auth.py:23` — hardcoded JWT secret fallback**
```python
JWT_SECRET = settings.CLERK_SECRET_KEY or "verxlite-secret-key"
```
If `CLERK_SECRET_KEY` is unset, the entire auth system signs tokens with a publicly-known secret.

**C7. `routes/auth.py:162-201` — login does not verify password**
The login endpoint looks up the user by email and returns a token. No password check. The comment even says so: `# In a real implementation, verify password against hashed password`.

**C8. `routes/auth.py:242-317` — Clerk webhook has no signature verification**
Anyone can POST `{"type": "user.deleted", "data": {"id": "<clerk_id>"}}` and delete any user.

**C9. Every router declares `prefix="/..."` AND `main.py:211-214` re-adds the same prefix → double-prefixed routes**
```python
# routes/auth.py
router = APIRouter(prefix="/auth", tags=["auth"])
# main.py
app.include_router(auth.router, prefix="/auth", tags=["auth"])
```
Result: `POST /auth/auth/register`, `GET /workflows/workflows/`, etc. Every test that hits `/auth/register` or `/workflows/` 404s.

**C10. Every route hardcodes `user_id="test-user-id"`, `tenant_id="test-tenant-id"`**
No `Depends(get_current_user)`, no JWT middleware, no tenant extraction. Every user sees every tenant's data. The audit checklist's "RBAC" line item is not just unimplemented — there is no hook to plug it into.

**C11. `routes/connections.py:531,561,739,768` — references `settings.FRONTEND_URL`**
`Settings` doesn't define `FRONTEND_URL`. Hitting `/connections/google/authorize` or `/connections/hubspot/authorize` raises `AttributeError`.

**C12. `main.py:121` — `StaticFiles(directory="static")` but `static/` does not exist**
`RuntimeError: Directory 'static' does not exist` at app startup.

**C13. `main.py:252-253` — `conn.execute("SELECT 1")` (removed in SQLAlchemy 2.0)**
The health endpoint always 500s.

**C14. `workflow_engine.py:99` — enum-vs-string comparison always False**
```python
if workflow.workflow_type == "post_meeting_followup":  # PyEnum vs str
```
`workflow.workflow_type` is a `WorkflowType` enum, comparing to the string literal `"post_meeting_followup"` returns False. Every workflow run falls into the `else` branch and raises `ValueError: Unknown workflow type`.

**C15. `workflow_engine.py:86` — `trigger_data.get('event_id', '')` crashes if `trigger_data=None`**
The function signature is `trigger_data: Optional[Dict[str, Any]] = None`. The line does `trigger_data.get(...)` unconditionally.

**C16. `routes/connections.py:251-256, 564-569` — broad `except Exception` swallows `HTTPException`**
Inner HTTP exceptions (intended 4xx) are caught and re-raised as 500.

**C17. `routes/workflows.py` — `GET /{workflow_id}` declared before `/runs`, `/stats`, `/templates`**
FastAPI matches routes in declaration order. `GET /workflows/runs`, `GET /workflows/stats`, `GET /workflows/templates` are all captured by `GET /workflows/{workflow_id}` and return 404 (or 422 — invalid UUID).

**C18. `utils/encryption.py:33` — `Fernet(key.encode())` with an invalid default key**
`ENCRYPTION_KEY` defaults to `"default-secret-key-change-in-production"`, which is not a 32-byte url-safe base64 string. The first call to `encrypt_data` raises `ValueError: Fernet key must be 32 url-safe base64-encoded bytes`.

**C19. No `migrations/versions/` directory**
`alembic.ini` and `migrations/env.py` exist but there are zero revision files. `alembic upgrade head` is a no-op. `migrations/env.py:53` reads the DB URL from `alembic.ini` (hardcoded `postgres:postgres@localhost`) instead of `settings.DATABASE_URL`, so it points at the wrong database even if migrations existed.

**C20. `pyproject.toml` missing critical dependencies**
Missing: `alembic`, `pyjwt`, `email-validator`, `prometheus-client`, `slowapi` (rate-limiting), `greenlet` (SQLAlchemy 2.0 async support), `types-redis`. Declared but unused: `langgraph ^0.0.10` (dead package, never imported). Declared and broken: `python-jose` (unmaintained — replaced by `pyjwt`).

### 1.2 Other backend highlights (HIGH)

- **H1.** Sync SQLAlchemy (`create_engine`, `scoped_session`) but every handler is `async def` → blocks the event loop on every DB call.
- **H2.** `oauth_states = {}` in-memory dict in `connections.py:37` — never persists across workers, no TTL, unbounded growth.
- **H3/H4.** Connection lookups in `GoogleConnector._get_connection` and `HubSpotConnector._get_connection` filter only on `provider`, not `tenant_id`. A user can use another tenant's OAuth token.
- **H5.** Soft-deleting a `Connection` (`is_active = False`) does not clear `access_token` / `refresh_token`. The tokens remain usable if anyone re-activates.
- **H6.** Auto-generated idempotency key uses `int(time.time())` — second-granularity collisions on the unique index crash the second request.
- **H7.** `get_workflow_stats` loads ALL runs into Python and computes aggregates in a loop. Should be SQL `GROUP BY`.
- **H9.** `routes/workflows.py:334-342` creates `WorkflowStep` with raw strings `"trigger"`, `"completed"` for `Enum` columns — works only because SQLAlchemy stringifies, but bypasses type safety and breaks if the enum values are renamed.
- **H10.** `routes/artifacts.py` `limit`/`offset` have no `ge`/`le` validation — caller can request `limit=-5`.
- **H11.** `routes/artifacts.py:20-28` redefines `ArtifactResponse` locally, shadowing `schemas/artifact.py:ArtifactResponse`. Two competing schemas for the same concept.
- **H12/H13.** `MetricsCollector` is instantiated per-request → metrics always empty. `track_workflow_run` / `track_workflow_step` are never called from the engine. `/metrics` returns JSON, not Prometheus text format.
- **H14.** `/health` Redis check creates a new `redis.Redis` client per request — connection leak.
- **H16.** First registered user becomes admin via `db.query(User).count()` — a global count, not a per-tenant count. In a multi-tenant system the 2nd tenant's first user is a "member".
- **H17.** Clerk webhook `user.created` assigns new users to `Tenant.first()` — every new user joins tenant #1.
- **H20.** `WorkflowResponse.from_orm(...)` used throughout — `.from_orm()` is deprecated in Pydantic v2 (should be `model_validate`).
- **H24.** `langfuse.py` calls `self.langfuse.observation(...)` and `self.langfuse.generation(...)` — Langfuse v2 API removed both. Should be `trace()` + `span()` / `generation()` chained.
- **H29.** `alembic.ini:5` — `postgresql://postgres:postgres@localhost:5432/verxlite` hardcoded in source control.
- **H30.** API Dockerfile: single-stage, runs as root, no `HEALTHCHECK`, `pip install poetry` unpinned, single uvicorn worker.
- **H32-H36.** Tests cannot run: `tests/test_routes.py:14` does `from main import app` but `main.py` is in `api/` (not on path); no `get_db` override → tests hit real DB; `test_models.py` expects `full_name == ""` but the property returns `"None None"`; `test_services.py` patches `WorkflowEngine.db` (a class attr) but the code reads `self.db` (instance attr) → mocks are no-ops; `test_workflow_engine.py:64` sets `workflow_type = "post_meeting_followup"` (string) which **encodes** the C14 bug rather than catching it.

---

## 2. Frontend (Next.js) — 7 CRITICAL bugs

The frontend review found 80 issues total. The app does not build.

### 2.1 Build-breaking

**C1. `app/login/page.tsx:50-67` & `app/sign-up/[[...sign-up]]/page.tsx:50-67` — JSX syntax error**
```tsx
appearance={
  elements: {            // ← parses as a label + block, not an object
    rootBox: "w-full",
    ...
  },
}
```
Should be `appearance={{ elements: { ... } }}`. `next build` aborts here.

**C2. `components/ui/switch.tsx` — broken primitive**
- `aria-checked="false"` is hardcoded → switch is always "off" to screen readers.
- Tailwind `data-[state=checked]:bg-primary` requires `data-state="checked"` on the element, which the component never sets → switch never visually toggles.
- Prop type is `ButtonHTMLAttributes` (no `checked` / `onCheckedChange`) but `workflows/page.tsx` and `settings/page.tsx` pass both → TS errors.

**C3. `app/workflows/page.tsx:331-336` — template literal never interpolates**
```tsx
className={`{
  selectedCategory === category
    ? "bg-verxlite-neon text-verxlite-dark"
    : ""
}`}
```
No `${...}`. The className becomes the literal string. Selected category never highlights.

**C4. `app/dashboard/page.tsx:80-84`, `workflows:111-120`, `connections:110-119`, `settings:60-64` — auth redirect fires during Clerk loading**
```tsx
if (!isSignedIn) { router.push("/login"); }
```
`isSignedIn` is `undefined` while Clerk is loading. Should be `if (isLoaded && !isSignedIn)`. Signed-in users get bounced to `/login` on every cold load.

**C5. No `middleware.ts` — routes are not server-protected**
`ClerkProvider` is the only auth wiring. Unauthenticated visitors render the full dashboard shell (with mock data) before the client-side redirect kicks in.

**C6. `web/Dockerfile` will not build**
- Line 9 `RUN npm ci` requires `package-lock.json` — **no lockfile exists**.
- Line 23 `COPY --from=builder /app/public ./public` — **no `public/` directory exists**.
- The Dockerfile has never built successfully.

**C7. `app/layout.tsx:18-26` — `ClerkProvider` wraps `<html>`**
App Router requires `<html>` and `<body>` as the outermost elements. Wrapping `<html>` in a client provider is undefined behavior and breaks SSR.

### 2.2 Other frontend highlights (HIGH)

- **H1.** Zero API integration. `NEXT_PUBLIC_API_URL` is declared but never referenced. No `lib/api.ts`. Every page renders hardcoded mock data.
- **H2.** `setWorkflowRuns`, `setConnections`, `setStats` declared in `dashboard/page.tsx:76-78` and never called.
- **H3.** Stale-closure state updates throughout — `setX(arr.map(...))` instead of `setX(prev => ...)`.
- **H4.** Multiple `<Link>` targets point to non-existent routes: `/workflows/runs/${run.id}`, `/workflows/${workflow.id}/edit`, `/connections/${provider}/authorize`, `/connections/${conn.id}/edit`. No dynamic `[id]` segments exist.
- **H5/H6.** Home page CTAs (`Get Started`, `Learn More`, `Get Started Free`) are dead buttons. Anchor links target IDs (`#features`, `#how-it-works`) that don't exist on the page.
- **H7.** No `app/error.tsx`, `app/not-found.tsx`, `app/loading.tsx`.
- **H8.** Settings page "Save Changes" buttons on Tenant, Notifications, and Billing tabs have no `onClick`. Only Profile is wired.
- **H9.** No `<UserButton />` anywhere. Signed-in users cannot sign out.
- **H14.** No SEO metadata beyond title/description. No `metadataBase`, no `openGraph`, no `twitter`, no `robots`, no `sitemap.ts`, no `icon.tsx`, no favicon.
- **H15.** Custom tabs in `workflows/page.tsx:296-318` and `settings/page.tsx:180-233` lack `role="tablist"/"tab"/"tabpanel"`, `aria-selected`, `aria-controls`, and arrow-key navigation.

---

## 3. Worker (Celery) — 4 CRITICAL bugs

### 3.1 The worker is dead code in production

**C1. `routes/workflows.py:346-358` — Celery task is never invoked**
```python
# In production, add to queue here
# from verxlite_api.tasks import execute_workflow_run
# execute_workflow_run.delay(...)
# For now, mark as queued
workflow_run.status = WorkflowRunStatus.QUEUED
db.commit()
```
The Celery task is commented out. Workflow runs sit in `QUEUED` forever. `IMPLEMENTATION_SUMMARY.md:155` claims "Worker: 100% complete" — false.

**C2. `worker/tasks.py:66` vs `workflow_engine.py:77` — two competing `run_id`s**
The worker generates a `run_id`, then the engine generates a *different* `run_id` and persists that one. The worker's `run_id` is never saved. On failure the worker does `db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()` — always `None`. The "update failed run" branch is dead. Langfuse traces use the bogus id.

**C3. `worker/pyproject.toml:7` — declares a package that doesn't exist**
```toml
packages = [{include = "verxlite_worker"}]
```
There is no `worker/verxlite_worker/` directory. `poetry install` installs nothing.

**C4. `worker/__init__.py:5` — `from verxlite_worker.tasks import ...`**
Imports the same non-existent module. The `__init__.py` is dead code that crashes if imported.

### 3.2 Other worker issues (HIGH)

- **H1.** `worker/tasks.py:141-142` only retries on `ConnectionError` — not on HTTP errors, 429s, 5xxs, DB errors. Fixed `countdown=60`, no exponential backoff (despite `IMPLEMENTATION_SUMMARY.md:124` claiming otherwise).
- **H2.** `db = session()` per task, never closed. Celery prefork reuses processes for up to 100 tasks → session accumulates state and leaks connections.
- **H3.** `WorkflowEngine.__init__` does `self.db = session()` — same leak.
- **H4.** Idempotency key auto-generated but never checked. The unique index would raise `IntegrityError` on a duplicate, crashing the task.
- **H5.** `workflow_engine.py` never calls `tracer.trace_workflow_step(...)` — `LangfuseTracer.trace_workflow_step` is dead code.
- **H6.** `MetricsCollector` is per-instance, in-memory only. `/metrics` returns empty metrics from a fresh instance. `ARCHITECTURE.md:49` lists Prometheus as a component — not implemented.

---

## 4. Infrastructure / Docker / CI/CD — 6 CRITICAL bugs

**C8. No `.gitignore` anywhere** — at root, in `api/`, `web/`, or `worker/`. High risk of committing `__pycache__/`, `.venv/`, `node_modules/`, `.env`, `.next/`.

**C9. Three binary PDFs committed to repo** — `Verxlite (1).pdf`, `_High‑level roadmap (2).pdf` (with non-ASCII U+2011 hyphen), `the idea.pdf`. PDFs don't belong in source control.

**C10. `web/Dockerfile` cannot build** (see §2.1 C6 above).

**C11. Worker package layout broken** (see §3.1 C3-C4 above).

**C12. No `LICENSE` file despite README's claim** (`README.md:353` links to `LICENSE` — broken link).

**C13. CI test job runs from the wrong directory**
`.github/workflows/ci-cd.yml:59-61`:
```yaml
- name: Run tests
  run: |
    cd api
    poetry run pytest tests/ -v
```
`tests/` lives at the repo root, not inside `api/`. After `cd api`, `pytest tests/` looks for `api/tests/` → 0 tests collected → false sense of safety.

**C14-C16.** No `poetry.lock` files (non-reproducible builds). `docker-compose.yml` reinstalls all deps at every `up`. `NEXT_PUBLIC_API_URL: http://api:8000` is Docker-internal DNS that the browser cannot resolve, and `NEXT_PUBLIC_*` vars are inlined at build time anyway.

**C17. Hardcoded secrets everywhere**
- `docker-compose.yml:9-11` — `POSTGRES_PASSWORD: postgres`
- `api/verxlite_api/config.py:55-58` — `ENCRYPTION_KEY` defaults to a publicly-known string
- `api/verxlite_api/utils/encryption.py:25` — KDF derives from `b"verxlite-secret"` (hardcoded)
- `api/alembic.ini:5` — `postgres:postgres@localhost` in source
- Git remote URL had an embedded GitHub PAT (redacted by git)

**C18. No authentication anywhere — hardcoded `tenant_id` and `user_id`** (also §1.1 C10).

---

## 5. Documentation — inaccurate

`IMPLEMENTATION_SUMMARY.md` claims "100% complete" for API and worker (false), "production-ready foundation" (false), "idempotency for all external operations" (false — idempotency key is set but never checked), "health checks implemented" (false — `/health` 500s, Dockerfiles have no HEALTHCHECK), "exponential backoff" (false — fixed `countdown=60`).

`ARCHITECTURE.md` claims "Row-level security in PostgreSQL" (no RLS policies), "100 req/min rate limiting" (no rate-limit code), "Async: All external API calls are async" (workflow engine uses sync `time.sleep()`).

`DEVELOPMENT_GUIDE.md:99-100` references `api/verxlite_api/agent/` — doesn't exist. `:150` references `web/public/` — doesn't exist. `:663` references `tests/test_integration.py` — doesn't exist.

`README.md:329` references `docker-compose.prod.yml` — doesn't exist.

`AUDIT_CHECKLIST.md:147` has a typo: `n- [ ] Workflow templates` (stray `n` from newline corruption).

---

## 6. Tests — cannot run

- **53 test functions** across 4 files + 11 fixtures.
- **Coverage:** models (good), routes (happy paths only), workflow engine (mock-based only).
- **Untested:** worker tasks, connectors, encryption, LangfuseTracer, MetricsCollector, config, error handlers, middleware, `/metrics` endpoint.
- **Test DB:** SQLite in-memory (production uses PostgreSQL — enum/JSON behavior differs).
- `tests/test_routes.py:14` does `from main import app` — `main.py` is in `api/` (not on path) → `ModuleNotFoundError`.
- No `get_db` override → tests hit the production database.
- `tests/conftest.py:213-221` — `mock_google_api` and `mock_hubspot_api` fixtures are empty `pass` stubs.
- No frontend tests, no integration tests, no load tests, no security tests.

---

## 7. Security summary

**CRITICAL:**
1. Hardcoded default `ENCRYPTION_KEY` (`config.py:55`) — all OAuth tokens trivially decryptable.
2. KDF derives from hardcoded password `b"verxlite-secret"` (`encryption.py:25`).
3. No authentication — hardcoded `tenant_id` and `user_id` everywhere.
4. Login does not verify password (`routes/auth.py:162-201`).
5. Clerk webhook has no signature verification (`routes/auth.py:242-317`).
6. `DEBUG=True` by default (`config.py:14`).
7. Hardcoded DB credentials in `docker-compose.yml`, `alembic.ini`, source code.
8. Cross-tenant token reuse (`connectors/google.py:_get_connection` filters only on `provider`).

**HIGH:**
- No `.gitignore` (risk of committing secrets).
- No `.dockerignore`.
- CORS `allow_methods=["*"]`, `allow_headers=["*"]`.
- SQL logging default-on (`session.py:15` `echo=settings.DEBUG`).
- No webhook signature verification.
- No rate limiting.
- No CSRF protection.
- No PKCE in OAuth.
- No audit logging (despite claims).
- Incomplete PII sanitization in `_sanitize_data` (O(n²) bug, depth-1 only).

---

## 8. Recommended P0 fix sequence (Phase 2 plan)

The "20-developer fix squad" work, executed immediately after this review, follows this sequence:

1. **Make the backend boot:** import `Integer`, rename `metadata` → `extra_metadata` on `Connection` and `Artifact`, make `_refresh_access_token` async + add `await`, delete broken `services/__init__.py` imports, add `pyjwt` to deps, add `FRONTEND_URL` to `Settings`, create `static/` or remove mount, fix `conn.execute("SELECT 1")` → `conn.execute(text("SELECT 1"))`, fix enum-vs-string comparison, fix `trigger_data` None check, drop double-prefixed routes, fix `routes/workflows.py` route ordering, require valid Fernet key, add missing deps (`alembic`, `pyjwt`, `prometheus-client`, `slowapi`, `greenlet`, `email-validator`).
2. **Real auth & tenant isolation:** add `get_current_user` dependency, replace every hardcoded `tenant_id` / `user_id`, add `User.password_hash` column, hash passwords with `passlib`, verify passwords in login, verify Clerk webhook signatures with `svix`.
3. **Fix workflow engine:** compare enum to enum, handle `trigger_data=None`, chain step outputs to next step's inputs, check idempotency key before insert, dispatch to real `GoogleConnector` / `HubSpotConnector` instead of mock `if tool_name ==` chain.
4. **Wire worker to API:** uncomment + fix `execute_workflow_run.delay(...)`, pass the existing `run_id`, make the engine UPDATE the existing run (not create a new one), add exponential backoff, add `autoretry_for`, close DB sessions.
5. **Fix encryption:** require `ENCRYPTION_KEY` (no default), derive Fernet key from it deterministically (or accept a Fernet key directly), persist IV alongside ciphertext.
6. **Add Alembic migration:** create `migrations/versions/0001_initial.py` with the full schema, fix `migrations/env.py` to read URL from `settings.DATABASE_URL`, fix `init_db.py` to import models BEFORE `create_all`.
7. **Fix frontend:** fix `appearance={{ ... }}` syntax, replace `Switch` with `@radix-ui/react-switch`, fix template literal, gate redirects on `isLoaded && !isSignedIn`, add `middleware.ts`, fix Dockerfile (create `public/`, generate `package-lock.json`), move `ClerkProvider` inside `<body>`.
8. **Repo hygiene:** `.gitignore`, `.dockerignore`, `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`, `.env.example` files, remove PDFs from git, add `.pre-commit-config.yaml`, add `Makefile`.
9. **Fix Docker:** multi-stage builds, non-root user, `HEALTHCHECK`, `.dockerignore`, fix `docker-compose.yml` (no runtime installs, restart policies, fix `NEXT_PUBLIC_API_URL`, drop `version`).
10. **Fix CI/CD:** run `pytest tests/` from repo root, add web lint, add worker lint, add security scan, add coverage, add `fly.toml` or remove deploy job.
11. **Tests:** add `get_db` override, add tests for auth, encryption, workflow, connectors, worker, routes. Verify all 53 existing tests + new tests pass.
12. **Docs:** update `IMPLEMENTATION_SUMMARY.md`, `ARCHITECTURE.md`, `DEVELOPMENT_GUIDE.md`, `README.md` to reflect actual state. Remove false "100% complete" / "production-ready" claims.

---

## 9. What "Done" looks like

After Phase 2, the following must be true with **zero errors**:

- `cd api && poetry install && poetry run pytest tests/ -v` — all tests pass.
- `cd web && npm install && npm run build` — builds clean.
- `cd api && poetry run uvicorn main:app` — boots without errors, `/health` returns 200, `/docs` renders.
- `cd worker && poetry run celery -A tasks worker --loglevel=info` — boots and connects to Redis.
- `docker-compose up` — all services healthy.
- CI pipeline passes on push to `main`.
- No hardcoded secrets, no mock data in production paths, no broken imports, no double-prefixed routes, no cross-tenant data access.

---

**End of Phase 1 dissection. Phase 2 implementation begins now.**
