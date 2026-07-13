"""
Tenant Model
"""

from sqlalchemy import Column, String, Text, DateTime, func
from verxlite_api.db.base import BaseModel


class Tenant(BaseModel):
    """
    Represents a company/workspace.
    """
    __tablename__ = "tenants"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    domain = Column(String(255), nullable=True)
    is_active = Column(bool, default=True, nullable=False)

    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name})>"
