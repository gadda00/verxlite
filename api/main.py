"""
Verxlite API - FastAPI Application
"""

import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import text

from verxlite_api.config import settings
from verxlite_api.db.session import session
from verxlite_api.routes import artifacts, auth, connections, workflows
from verxlite_api.schemas.error import (
    AuthenticationErrorResponse,
    AuthorizationErrorResponse,
    InternalErrorResponse,
    NotFoundErrorResponse,
    RateLimitErrorResponse,
    ValidationErrorResponse,
)
from verxlite_api.utils.logger import get_logger

logger = get_logger("verxlite_api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    logger.info("Starting Verxlite API...")
    yield
    logger.info("Shutting down Verxlite API...")
    session.remove()


app = FastAPI(
    title="Verxlite API",
    description="Universal AI Workflow Agent for Email + CRM + Documents",
    version="0.1.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)


# --------------------------------------------------------------------------- #
# Middleware
# --------------------------------------------------------------------------- #
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{(time.time() - start):.4f}s"
    return response


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        settings.FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Correlation-ID"],
    expose_headers=["X-Request-ID", "X-Correlation-ID", "X-Process-Time"],
    max_age=600,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Mount static files only if the directory exists.
_static_dir = Path(__file__).parent.parent / "static"
if _static_dir.exists() and _static_dir.is_dir():
    from fastapi.staticfiles import StaticFiles

    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")
else:
    logger.info(f"Static directory '{_static_dir}' not found; skipping StaticFiles mount")


# --------------------------------------------------------------------------- #
# Exception handlers
# --------------------------------------------------------------------------- #
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "code": error.get("type", "value_error"),
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ValidationErrorResponse(
            error="ValidationError",
            message="Validation failed",
            details=errors,
            request_id=request.headers.get("X-Request-ID"),
            status_code=422,
        ).model_dump(mode="json"),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        response = AuthenticationErrorResponse(
            error="AuthenticationError",
            message=exc.detail or "Authentication failed",
            request_id=request.headers.get("X-Request-ID"),
            status_code=401,
        )
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        response = AuthorizationErrorResponse(
            error="AuthorizationError",
            message=exc.detail or "Authorization failed",
            request_id=request.headers.get("X-Request-ID"),
            status_code=403,
        )
    elif exc.status_code == status.HTTP_404_NOT_FOUND:
        response = NotFoundErrorResponse(
            error="NotFoundError",
            message=exc.detail or "Resource not found",
            request_id=request.headers.get("X-Request-ID"),
            status_code=404,
        )
    elif exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        retry_after = exc.headers.get("Retry-After") if exc.headers else None
        response = RateLimitErrorResponse(
            error="RateLimitError",
            message=exc.detail or "Rate limit exceeded",
            request_id=request.headers.get("X-Request-ID"),
            status_code=429,
            retry_after=int(retry_after) if retry_after else None,
        )
    else:
        response = InternalErrorResponse(
            error="InternalServerError",
            message=exc.detail or "Internal server error",
            request_id=request.headers.get("X-Request-ID"),
            status_code=exc.status_code or 500,
        )
    return JSONResponse(status_code=exc.status_code, content=response.model_dump(mode="json"))


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=InternalErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            request_id=request.headers.get("X-Request-ID"),
            status_code=500,
        ).model_dump(mode="json"),
    )


# --------------------------------------------------------------------------- #
# Routers — note: prefixes are added here, NOT in the routers themselves.
# --------------------------------------------------------------------------- #
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(connections.router, prefix="/connections", tags=["connections"])
app.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
app.include_router(artifacts.router, prefix="/artifacts", tags=["artifacts"])


# --------------------------------------------------------------------------- #
# Root / health / metrics
# --------------------------------------------------------------------------- #
@app.get("/", tags=["root"])
async def root():
    return {
        "name": "Verxlite API",
        "version": "0.1.0",
        "description": "Universal AI Workflow Agent",
        "docs": "/docs" if settings.ENVIRONMENT != "production" else None,
        "health": "/health",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint — verifies DB and Redis connectivity."""
    from verxlite_api.db.session import engine

    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {
            "database": {"status": "unknown"},
            "redis": {"status": "unknown"},
        },
    }

    # DB
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"

    # Redis (with bounded client lifetime)
    try:
        import redis

        r = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        r.close()
        health_status["checks"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"

    if all(c["status"] == "healthy" for c in health_status["checks"].values()):
        health_status["status"] = "healthy"
    elif any(c["status"] == "unhealthy" for c in health_status["checks"].values()):
        # If both are unhealthy, mark unhealthy; if only one, degraded.
        unhealthy_count = sum(
            1 for c in health_status["checks"].values() if c["status"] == "unhealthy"
        )
        if unhealthy_count == len(health_status["checks"]):
            health_status["status"] = "unhealthy"

    return health_status


@app.get("/metrics", tags=["metrics"], response_class=PlainTextResponse)
async def metrics():
    """Prometheus-format metrics endpoint."""
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    # Also dump in-memory metrics into the registry is non-trivial; we serve
    # the standard process/HTTP metrics here, plus a JSON view from the
    # MetricsCollector via /metrics/json for the in-memory ones.
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/metrics/json", tags=["metrics"])
async def metrics_json():
    """In-memory workflow metrics (JSON, useful for debugging)."""
    from verxlite_api.observability.metrics import MetricsCollector

    return {"metrics": MetricsCollector().get_metrics()}


# OpenAPI schema customization
@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_schema():
    return app.openapi()
