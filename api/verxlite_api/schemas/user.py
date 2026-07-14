"""
User Schemas
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """User creation request."""

    email: EmailStr = Field(..., description="User's email address")
    first_name: str | None = Field(None, description="User's first name", max_length=100)
    last_name: str | None = Field(None, description="User's last name", max_length=100)
    role: str | None = Field("member", description="User role")
    phone: str | None = Field(None, description="User's phone number", max_length=50)
    timezone: str | None = Field("UTC", description="User's timezone")
    preferences: dict | None = Field(None, description="User preferences")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "member",
                "timezone": "America/New_York",
            }
        }


class UserUpdate(BaseModel):
    """User update request."""

    email: EmailStr | None = Field(None, description="User's email address")
    first_name: str | None = Field(None, description="User's first name", max_length=100)
    last_name: str | None = Field(None, description="User's last name", max_length=100)
    role: str | None = Field(None, description="User role")
    is_active: bool | None = Field(None, description="Whether user is active")
    phone: str | None = Field(None, description="User's phone number", max_length=50)
    timezone: str | None = Field(None, description="User's timezone")
    preferences: dict | None = Field(None, description="User preferences")

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Smith",
                "role": "admin",
                "is_active": True,
            }
        }


class UserResponse(BaseModel):
    """User response model."""

    id: str
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    role: str
    is_active: bool
    avatar_url: str | None = None
    timezone: str
    tenant_id: str
    last_login_at: datetime | None = None
    email_verified: bool
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
                "email_verified": True,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        }


class UserListResponse(BaseModel):
    """List of users response."""

    users: list[UserResponse]
    total: int
    page: int = 1
    page_size: int = 100

    class Config:
        json_schema_extra = {
            "example": {
                "users": [
                    {
                        "id": "user_abc123",
                        "email": "user@example.com",
                        "full_name": "John Doe",
                        "role": "admin",
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 100,
            }
        }
