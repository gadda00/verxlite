"""
Configuration Settings for Verxlite API
"""

import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = Field(default="development", validation_alias="ENVIRONMENT")
    DEBUG: bool = Field(default=False, validation_alias="DEBUG")

    # Database
    DATABASE_URL: str = Field(default="sqlite:///./verxlite.db", validation_alias="DATABASE_URL")

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")

    # Frontend URL (for OAuth redirects, CORS, etc.)
    FRONTEND_URL: str = Field(
        default="http://localhost:3000",
        validation_alias="FRONTEND_URL",
    )

    # Auth (Clerk) — optional in dev
    CLERK_SECRET_KEY: str | None = Field(default=None, validation_alias="CLERK_SECRET_KEY")
    CLERK_PUBLISHABLE_KEY: str | None = Field(
        default=None, validation_alias="CLERK_PUBLISHABLE_KEY"
    )
    CLERK_WEBHOOK_SECRET: str | None = Field(default=None, validation_alias="CLERK_WEBHOOK_SECRET")

    # JWT (used when CLERK_SECRET_KEY is not configured)
    JWT_SECRET: str = Field(
        default=os.getenv("JWT_SECRET", "change-me-in-production-please-32-bytes-minimum"),
        validation_alias="JWT_SECRET",
    )
    JWT_ALGORITHM: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    JWT_EXPIRE_MINUTES: int = Field(default=60 * 24, validation_alias="JWT_EXPIRE_MINUTES")

    # OAuth - Google
    GOOGLE_CLIENT_ID: str | None = Field(default=None, validation_alias="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str | None = Field(default=None, validation_alias="GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = Field(
        default="http://localhost:8000/connections/google/callback",
        validation_alias="GOOGLE_REDIRECT_URI",
    )

    # OAuth - HubSpot
    HUBSPOT_CLIENT_ID: str | None = Field(default=None, validation_alias="HUBSPOT_CLIENT_ID")
    HUBSPOT_CLIENT_SECRET: str | None = Field(
        default=None, validation_alias="HUBSPOT_CLIENT_SECRET"
    )
    HUBSPOT_REDIRECT_URI: str = Field(
        default="http://localhost:8000/connections/hubspot/callback",
        validation_alias="HUBSPOT_REDIRECT_URI",
    )

    # LLM Providers
    ANTHROPIC_API_KEY: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    OPENAI_API_KEY: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")

    # Observability (Langfuse)
    LANGFUSE_SECRET_KEY: str | None = Field(default=None, validation_alias="LANGFUSE_SECRET_KEY")
    LANGFUSE_PUBLIC_KEY: str | None = Field(default=None, validation_alias="LANGFUSE_PUBLIC_KEY")
    LANGFUSE_HOST: str = Field(
        default="https://cloud.langfuse.com",
        validation_alias="LANGFUSE_HOST",
    )

    # Encryption — REQUIRED in production; in dev we auto-generate a stable key.
    ENCRYPTION_KEY: str | None = Field(default=None, validation_alias="ENCRYPTION_KEY")

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, validation_alias="RATE_LIMIT_ENABLED")
    RATE_LIMIT_DEFAULT: str = Field(default="100/minute", validation_alias="RATE_LIMIT_DEFAULT")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_encryption_key(self) -> str:
        """
        Return a valid Fernet key (32-byte url-safe base64).

        - If ENCRYPTION_KEY is set, it must be a valid Fernet key.
        - If unset and ENVIRONMENT != "production", we derive one from JWT_SECRET
          (deterministic across restarts, fine for dev).
        - If unset in production, raise.
        """
        import base64

        from cryptography.fernet import Fernet, InvalidToken
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        if self.ENCRYPTION_KEY:
            # Validate
            try:
                Fernet(self.ENCRYPTION_KEY.encode())
            except (ValueError, InvalidToken) as e:
                raise ValueError(
                    "ENCRYPTION_KEY must be a valid Fernet key "
                    "(32-byte url-safe base64). Generate one with: "
                    "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
                ) from e
            return self.ENCRYPTION_KEY

        if self.ENVIRONMENT == "production":
            raise RuntimeError(
                "ENCRYPTION_KEY must be set in production. "
                "Generate one with: "
                "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )

        # Dev fallback: derive deterministically from JWT_SECRET.
        # Stable across restarts so encrypted DB rows don't break.
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"verxlite-dev-salt",  # static salt — fine for dev only
            iterations=480_000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.JWT_SECRET.encode()))
        return key.decode()


# Initialize settings
settings = Settings()
