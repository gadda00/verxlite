"""
User Model
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import relationship

from verxlite_api.db.base import BaseModel


class User(BaseModel):
    """
    Represents a user in the system.

    Attributes:
        tenant_id: Tenant this user belongs to
        email: User's email address (unique)
        first_name: User's first name
        last_name: User's last name
        role: User's role (admin, member, viewer)
        is_active: Whether the user is active
        clerk_id: Clerk user ID
        avatar_url: URL to user's avatar
        last_login_at: When user last logged in
        email_verified: Whether email is verified
        phone: User's phone number
        timezone: User's timezone
        preferences: JSON field for user preferences
    """

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_user_email", "email", unique=True),
        Index("ix_user_tenant", "tenant_id"),
        Index(
            "ix_user_clerk", "clerk_id", unique=True, postgresql_where=text("clerk_id IS NOT NULL")
        ),
        Index("ix_user_active", "is_active"),
    )

    tenant_id = Column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email = Column(String(255), nullable=False, unique=True, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    role = Column(String(20), default="member", nullable=False)  # admin, member, viewer
    is_active = Column(Boolean, default=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # For email/password auth (dev fallback)
    clerk_id = Column(String(255), nullable=True, unique=True)
    avatar_url = Column(String(500), nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    phone = Column(String(50), nullable=True)
    timezone = Column(String(50), default="UTC", nullable=False)
    preferences = Column(Text, nullable=True)  # JSON string for user preferences

    # Relationships
    tenant = relationship("Tenant", backref="users")
    connections = relationship("Connection", backref="user", cascade="all, delete-orphan")
    workflow_runs = relationship("WorkflowRun", backref="user", cascade="all, delete-orphan")
    created_workflows = relationship(
        "Workflow", backref="creator", foreign_keys="Workflow.created_by"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role}, tenant_id={self.tenant_id})>"

    @property
    def full_name(self) -> str:
        """Get user's full name (empty string if both parts are None)."""
        parts = [p for p in (self.first_name, self.last_name) if p]
        return " ".join(parts)

    def to_dict(self):
        """Convert user to dictionary (sanitized)."""
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "role": self.role,
            "is_active": self.is_active,
            "avatar_url": self.avatar_url,
            "timezone": self.timezone,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
