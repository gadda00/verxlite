"""
Tenant Model
"""

from sqlalchemy import Boolean, Column, DateTime, Index, String, Text, text

from verxlite_api.db.base import BaseModel


class Tenant(BaseModel):
    """
    Represents a company/workspace.

    Attributes:
        name: Name of the tenant/company
        description: Optional description
        domain: Optional domain for email verification
        is_active: Whether the tenant is active
        custom_domain: Custom domain for branding
        subscription_plan: Current subscription plan
        subscription_status: Status of subscription (active, trial, expired, etc.)
        trial_ends_at: When trial period ends
        settings: JSON field for tenant-specific settings
    """

    __tablename__ = "tenants"
    __table_args__ = (
        Index("ix_tenant_name", "name", unique=True, postgresql_where=text("name IS NOT NULL")),
        Index(
            "ix_tenant_domain", "domain", unique=True, postgresql_where=text("domain IS NOT NULL")
        ),
        Index("ix_tenant_active", "is_active"),
    )

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    domain = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    custom_domain = Column(String(255), nullable=True)
    subscription_plan = Column(String(50), default="free", nullable=False)
    subscription_status = Column(String(50), default="trial", nullable=False)
    trial_ends_at = Column(DateTime, nullable=True)
    settings = Column(Text, nullable=True)  # JSON string for tenant settings

    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name}, is_active={self.is_active})>"

    def to_dict(self):
        """Convert tenant to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "domain": self.domain,
            "is_active": self.is_active,
            "custom_domain": self.custom_domain,
            "subscription_plan": self.subscription_plan,
            "subscription_status": self.subscription_status,
            "trial_ends_at": self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
