"""
Connection Model
"""

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import relationship

from verxlite_api.db.base import BaseModel
from verxlite_api.utils.encryption import decrypt_data, encrypt_data


class Connection(BaseModel):
    """
    Represents an OAuth connection to an external service (Google, HubSpot, etc.).

    Attributes:
        tenant_id: Tenant this connection belongs to
        user_id: User who owns this connection
        provider: Service provider (google, hubspot, salesforce, etc.)
        provider_user_id: User ID from the provider
        access_token: Encrypted OAuth access token
        refresh_token: Encrypted OAuth refresh token
        token_type: Type of token (Bearer, etc.)
        expires_at: When the access token expires
        scope: Comma-separated list of scopes
        is_active: Whether the connection is active
        metadata: Additional provider-specific data
        last_sync_at: When data was last synced
        sync_status: Status of last sync (success, failed, pending)
        sync_error: Error message from last sync
    """

    __tablename__ = "connections"
    __table_args__ = (
        Index("ix_connection_tenant", "tenant_id"),
        Index("ix_connection_user", "user_id"),
        Index("ix_connection_provider", "provider"),
        Index("ix_connection_active", "is_active"),
        Index("ix_connection_expires", "expires_at"),
    )

    tenant_id = Column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider = Column(String(50), nullable=False)  # google, hubspot, salesforce, outlook, etc.
    provider_user_id = Column(String(255), nullable=True)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_type = Column(String(50), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    scope = Column(Text, nullable=True)  # Comma-separated scopes
    is_active = Column(Boolean, default=True, nullable=False)
    extra_metadata = Column(JSON, nullable=True, default=dict)  # Additional provider-specific data
    last_sync_at = Column(DateTime, nullable=True)
    sync_status = Column(String(20), nullable=True)  # success, failed, pending
    sync_error = Column(Text, nullable=True)

    # Relationships
    tenant = relationship("Tenant", backref="connections")
    # `user` is created automatically via the backref on User.connections.

    @property
    def decrypted_access_token(self):
        """Decrypt the access token."""
        if self.access_token:
            try:
                return decrypt_data(self.access_token)
            except Exception:
                return None
        return None

    @decrypted_access_token.setter
    def decrypted_access_token(self, value):
        """Encrypt and set the access token."""
        if value:
            self.access_token = encrypt_data(value)
        else:
            self.access_token = None

    @property
    def decrypted_refresh_token(self):
        """Decrypt the refresh token."""
        if self.refresh_token:
            try:
                return decrypt_data(self.refresh_token)
            except Exception:
                return None
        return None

    @decrypted_refresh_token.setter
    def decrypted_refresh_token(self, value):
        """Encrypt and set the refresh token."""
        if value:
            self.refresh_token = encrypt_data(value)
        else:
            self.refresh_token = None

    @property
    def is_expired(self):
        """Check if the access token is expired."""
        if not self.expires_at:
            return True
        from datetime import datetime, timezone

        # Make both sides timezone-aware before comparing.
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return expires < datetime.now(timezone.utc)

    @property
    def scopes_list(self):
        """Get scopes as a list."""
        if not self.scope:
            return []
        return self.scope.split(",") if isinstance(self.scope, str) else self.scope

    def has_scope(self, scope: str) -> bool:
        """Check if connection has a specific scope."""
        return scope in self.scopes_list

    def to_dict(self):
        """Convert connection to dictionary (sanitized - no tokens)."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "provider": self.provider,
            "provider_user_id": self.provider_user_id,
            "token_type": self.token_type,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "scope": self.scope,
            "is_active": self.is_active,
            "is_expired": self.is_expired,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "sync_status": self.sync_status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Connection(id={self.id}, provider={self.provider}, user_id={self.user_id}, is_active={self.is_active})>"
