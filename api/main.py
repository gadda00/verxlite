"""
Verxlite API - FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from verxlite_api.routes import auth, connections, workflows, artifacts
from verxlite_api.config import settings

# Create FastAPI app
app = FastAPI(
    title="Verxlite API",
    description="Universal AI Workflow Agent for Email + CRM + Documents",
    version="0.1.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://verxlite.web.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(connections.router, prefix="/connections", tags=["connections"])
app.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
app.include_router(artifacts.router, prefix="/artifacts", tags=["artifacts"])


@app.get("/")
async def root():
    return {
        "name": "Verxlite API",
        "version": "0.1.0",
        "description": "Universal AI Workflow Agent",
        "docs": "/docs" if settings.ENVIRONMENT == "development" else None,
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
