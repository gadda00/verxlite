"""
Authentication Schemas
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserLoginRequest(BaseModel):
    """User login request."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password", min_length=8)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class UserRegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password", min_length=8)
    first_name: Optional[str] = Field(None, description="User's first name", max_length=100)
    last_name: Optional[str] = Field(None, description="User's last name", max_length=100)
    tenant_name: Optional[str] = Field(None, description="Tenant name", max_length=255)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "first_name": "John",
                "last_name": "Doe",
                "tenant_name": "Acme Corp"
            }
        }


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    role: str
    is_active: bool
    avatar_url: Optional[str] = None
    timezone: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "user_abc123",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe",
                "role": "admin",
                "is_active": True,
                "avatar_url": "https://example.com/avatar.jpg",
                "timezone": "UTC",
                "tenant_id": "tenant_abc123",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z"
            }
        }


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    user: UserResponse

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "refresh_token": "refresh_token_value",
                "user": {
                    "id": "user_abc123",
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "role": "admin",
                    "is_active": True,
                    "tenant_id": "tenant_abc123"
                }
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str = Field(..., description="Refresh token")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "refresh_token_value"
            }
        }
