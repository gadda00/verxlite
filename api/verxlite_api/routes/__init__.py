"""
Routes Module
"""

from verxlite_api.routes.artifacts import router as artifacts_router
from verxlite_api.routes.auth import router as auth_router
from verxlite_api.routes.connections import router as connections_router
from verxlite_api.routes.workflows import router as workflows_router

__all__ = ["auth_router", "connections_router", "workflows_router", "artifacts_router"]
