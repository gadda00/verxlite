"""
Tenant Schemas
"""

from datetime import datetime

from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    """Tenant creation request."""

    name: str = Field(..., description="Tenant name", min_length=1, max_length=255)
    description: str | None = Field(None, description="Tenant description", max_length=5000)
    domain: str | None = Field(None, description="Tenant domain", max_length=255)
    custom_domain: str | None = Field(None, description="Custom domain", max_length=255)
    subscription_plan: str | None = Field("free", description="Subscription plan")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Acme Corp",
                "description": "A great company",
                "domain": "acme.com",
                "subscription_plan": "pro",
            }
        }


class TenantUpdate(BaseModel):
    """Tenant update request."""

    name: str | None = Field(None, description="Tenant name", min_length=1, max_length=255)
    description: str | None = Field(None, description="Tenant description", max_length=5000)
    domain: str | None = Field(None, description="Tenant domain", max_length=255)
    custom_domain: str | None = Field(None, description="Custom domain", max_length=255)
    subscription_plan: str | None = Field(None, description="Subscription plan")
    is_active: bool | None = Field(None, description="Whether tenant is active")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Acme Corp Updated",
                "description": "An even greater company",
                "is_active": True,
            }
        }


class TenantResponse(BaseModel):
    """Tenant response model."""

    id: str
    name: str
    description: str | None = None
    domain: str | None = None
    is_active: bool
    custom_domain: str | None = None
    subscription_plan: str
    subscription_status: str
    trial_ends_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "tenant_abc123",
                "name": "Acme Corp",
                "description": "A great company",
                "domain": "acme.com",
                "is_active": True,
                "subscription_plan": "pro",
                "subscription_status": "active",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        }


class TenantListResponse(BaseModel):
    """List of tenants response."""

    tenants: list[TenantResponse]
    total: int
    page: int = 1
    page_size: int = 100

    class Config:
        json_schema_extra = {
            "example": {
                "tenants": [{"id": "tenant_abc123", "name": "Acme Corp", "is_active": True}],
                "total": 1,
                "page": 1,
                "page_size": 100,
            }
        }
