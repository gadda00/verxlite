"""
Pydantic Schemas for Request/Response Validation
"""

from verxlite_api.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse
from verxlite_api.schemas.user import UserCreate, UserUpdate, UserResponse
from verxlite_api.schemas.connection import ConnectionResponse, ConnectionListResponse
from verxlite_api.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowListResponse,
)
from verxlite_api.schemas.workflow_run import (
    WorkflowRunCreate,
    WorkflowRunResponse,
    WorkflowRunListResponse,
    WorkflowRunDetailResponse,
)
from verxlite_api.schemas.artifact import ArtifactResponse, ArtifactListResponse
from verxlite_api.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from verxlite_api.schemas.error import ErrorResponse

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
