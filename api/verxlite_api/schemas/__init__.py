"""
Pydantic Schemas for Request/Response Validation
"""

from verxlite_api.schemas.artifact import ArtifactListResponse, ArtifactResponse
from verxlite_api.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from verxlite_api.schemas.connection import ConnectionListResponse, ConnectionResponse
from verxlite_api.schemas.error import ErrorResponse
from verxlite_api.schemas.tenant import TenantCreate, TenantResponse, TenantUpdate
from verxlite_api.schemas.user import UserCreate, UserResponse, UserUpdate
from verxlite_api.schemas.workflow import (
    WorkflowCreate,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowUpdate,
)
from verxlite_api.schemas.workflow_run import (
    WorkflowRunCreate,
    WorkflowRunDetailResponse,
    WorkflowRunListResponse,
    WorkflowRunResponse,
)

__all__ = [
    # Tenant
    "TenantCreate",
    "TenantUpdate",
    "TenantResponse",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    # Connection
    "ConnectionResponse",
    "ConnectionListResponse",
    # Workflow
    "WorkflowCreate",
    "WorkflowUpdate",
    "WorkflowResponse",
    "WorkflowListResponse",
    # Workflow Run
    "WorkflowRunCreate",
    "WorkflowRunResponse",
    "WorkflowRunListResponse",
    "WorkflowRunDetailResponse",
    # Artifact
    "ArtifactResponse",
    "ArtifactListResponse",
    # Auth
    "TokenResponse",
    "UserLoginRequest",
    "UserRegisterRequest",
    # Error
    "ErrorResponse",
]
