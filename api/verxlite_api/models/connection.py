"""
Connection Model
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from verxlite_api.db.base import BaseModel
from verxlite_api.utils.encryption import encrypt_data, decrypt_data
from verxlite_api.config import settings


class Connection(BaseModel):
    """
    Represents an OAuth connection to an external service (Google, HubSpot, etc.).
    """
    __tablename__ = "connections"

    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # google, hubspot, salesforce
    provider_user_id = Column(String(255), nullable=True)  # User ID from the provider
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_type = Column(String(50), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    scope = Column(Text, nullable=True)  # Comma-separated scopes
    is_active = Column(Boolean, default=True, nullable=False)
    metadata = Column(JSON, nullable=True)  # Additional provider-specific data

    # Relationships
    tenant = relationship("Tenant", backref="connections")

    @property
    def decrypted_access_token(self):
        """Decrypt the access token."""
        if self.access_token:
            return decrypt_data(self.access_token, settings.ENCRYPTION_KEY)
        return None

    @decrypted_access_token.setter
    def decrypted_access_token(self, value):
        """Encrypt and set the access token."""
        if value:
            self.access_token = encrypt_data(value, settings.ENCRYPTION_KEY)
        else:
            self.access_token = None

    @property
    def decrypted_refresh_token(self):
        """Decrypt the refresh token."""
        if self.refresh_token:
            return decrypt_data(self.refresh_token, settings.ENCRYPTION_KEY)
        return None

    @decrypted_refresh_token.setter
    def decrypted_refresh_token(self, value):
        """Encrypt and set the refresh token."""
        if value:
            self.refresh_token = encrypt_data(value, settings.ENCRYPTION_KEY)
        else:
            self.refresh_token = None

    def __repr__(self):
        return f"<Connection(id={self.id}, provider={self.provider}, user_id={self.user_id})>"
