"""
Verxlite API - FastAPI Application
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from verxlite_api.config import settings
from verxlite_api.db.session import session
from verxlite_api.routes import auth, connections, workflows, artifacts
from verxlite_api.schemas.error import (
    ValidationErrorResponse,
    AuthenticationErrorResponse,
    AuthorizationErrorResponse,
    NotFoundErrorResponse,
    RateLimitErrorResponse,
    InternalErrorResponse,
)
from verxlite_api.utils.logger import get_logger

# Configure logging
logger = get_logger("verxlite_api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    """
    # Startup
    logger.info("Starting Verxlite API...")
    
    # Initialize database connection pool
    # In production, you might want to test the database connection here
    
    yield
    
    # Shutdown
    logger.info("Shutting down Verxlite API...")
    # Close database connections
    session.remove()


# Create FastAPI app
app = FastAPI(
    title="Verxlite API",
    description="Universal AI Workflow Agent for Email + CRM + Documents",
    version="0.1.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan,
)

# Add request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to each request for tracing."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    # Add request ID to response headers
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response


# Add timing middleware
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    """Add timing header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


# Add correlation ID middleware
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID for distributed tracing."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Store correlation ID in request state
    request.state.correlation_id = correlation_id
    
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response


# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://verxlite.web.app",
        "https://verxlite.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Correlation-ID", "X-Process-Time"],
    max_age=600,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "code": error.get("type", "value_error"),
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ValidationErrorResponse(
            error="ValidationError",
            message="Validation failed",
            details=errors,
            request_id=request.headers.get("X-Request-ID"),
            status_code=422,
        ).model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
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
        response = RateLimitErrorResponse(
            error="RateLimitError",
            message=exc.detail or "Rate limit exceeded",
            request_id=request.headers.get("X-Request-ID"),
            status_code=429,
            retry_after=exc.headers.get("Retry-After") if hasattr(exc, "headers") else None,
        )
    else:
        response = InternalErrorResponse(
            error="InternalServerError",
            message=exc.detail or "Internal server error",
            request_id=request.headers.get("X-Request-ID"),
            status_code=exc.status_code or 500,
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=InternalErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            request_id=request.headers.get("X-Request-ID"),
            status_code=500,
        ).model_dump(),
    )


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(connections.router, prefix="/connections", tags=["connections"])
app.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
app.include_router(artifacts.router, prefix="/artifacts", tags=["artifacts"])


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    return {
        "name": "Verxlite API",
        "version": "0.1.0",
        "description": "Universal AI Workflow Agent",
        "docs": "/docs" if settings.ENVIRONMENT == "development" else None,
        "health": "/health",
    }


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        - Database connectivity status
        - Redis connectivity status
        - Overall system health
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {
            "database": {"status": "unknown"},
            "redis": {"status": "unknown"},
        },
    }
    
    # Check database
    try:
        from verxlite_api.db.session import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        health_status["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        import redis
        from verxlite_api.config import settings
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.ping()
        health_status["checks"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Determine overall status
    if all(check["status"] == "healthy" for check in health_status["checks"].values()):
        health_status["status"] = "healthy"
    elif any(check["status"] == "unhealthy" for check in health_status["checks"].values()):
        health_status["status"] = "unhealthy"
    
    return health_status


# Metrics endpoint
@app.get("/metrics", tags=["metrics"])
async def metrics():
    """
    Prometheus-compatible metrics endpoint.
    
    Returns:
        - Workflow run metrics
        - Step execution metrics
        - Token usage metrics
        - Error metrics
    """
    from verxlite_api.observability.metrics import MetricsCollector
    
    metrics_collector = MetricsCollector()
    metrics_data = metrics_collector.get_metrics()
    
    # Format metrics for Prometheus
    prometheus_metrics = []
    
    for key, values in metrics_data.items():
        for metric_name, metric_value in values.items():
            if isinstance(metric_value, (int, float)):
                prometheus_metrics.append(
                    f"verxlite_{key.replace('.', '_').replace('-', '_')}_{metric_name} {metric_value}"
                )
    
    return {
        "metrics": prometheus_metrics,
        "raw": metrics_data,
    }


# OpenAPI schema customization
@app.get("/openapi.json")
async def get_openapi_schema():
    """Get OpenAPI schema with customizations."""
    return app.openapi()
