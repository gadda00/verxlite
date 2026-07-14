"""
Connection Schemas
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ConnectionCreate(BaseModel):
    """Connection creation request."""

    provider: str = Field(..., description="Service provider (google, hubspot, etc.)")
    provider_user_id: str | None = Field(None, description="User ID from provider")
    scope: str | None = Field(None, description="Comma-separated scopes")
    metadata: dict | None = Field(None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "google",
                "provider_user_id": "google_user_123",
                "scope": "email,profile,calendar.readonly",
                "metadata": {},
            }
        }


class ConnectionUpdate(BaseModel):
    """Connection update request."""

    is_active: bool | None = Field(None, description="Whether connection is active")
    scope: str | None = Field(None, description="Comma-separated scopes")
    metadata: dict | None = Field(None, description="Additional metadata")

    class Config:
        json_schema_extra = {"example": {"is_active": True, "metadata": {"updated": True}}}


class ConnectionResponse(BaseModel):
    """Connection response model."""

    id: str
    tenant_id: str
    user_id: str
    provider: str
    provider_user_id: str | None = None
    is_active: bool
    is_expired: bool
    scope: str | None = None
    last_sync_at: datetime | None = None
    sync_status: str | None = None
    extra_metadata: dict | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "conn_abc123",
                "tenant_id": "tenant_abc123",
                "user_id": "user_abc123",
                "provider": "google",
                "provider_user_id": "google_user_123",
                "is_active": True,
                "is_expired": False,
                "scope": "email,profile,calendar.readonly",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        }


class ConnectionListResponse(BaseModel):
    """List of connections response."""

    connections: list[ConnectionResponse]
    total: int
    page: int = 1
    page_size: int = 100

    class Config:
        json_schema_extra = {
            "example": {
                "connections": [{"id": "conn_abc123", "provider": "google", "is_active": True}],
                "total": 1,
                "page": 1,
                "page_size": 100,
            }
        }


class OAuthStateResponse(BaseModel):
    """OAuth state response."""

    state: str
    provider: str
    redirect_url: str

    class Config:
        json_schema_extra = {
            "example": {
                "state": "random_state_string",
                "provider": "google",
                "redirect_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
            }
        }
