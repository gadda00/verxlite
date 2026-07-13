"""
User Model
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from verxlite_api.db.base import BaseModel


class User(BaseModel):
    """
    Represents a user in the system.
    """
    __tablename__ = "users"

    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    role = Column(String(20), default="member", nullable=False)  # admin, member
    is_active = Column(Boolean, default=True, nullable=False)
    clerk_id = Column(String(255), nullable=True, unique=True)

    # Relationships
    tenant = relationship("Tenant", backref="users")
    connections = relationship("Connection", backref="user", cascade="all, delete-orphan")
    workflow_runs = relationship("WorkflowRun", backref="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
