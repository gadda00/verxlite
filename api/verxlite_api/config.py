"""
Configuration Settings for Verxlite API
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")

    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    # Redis
    REDIS_URL: str = Field(..., env="REDIS_URL")

    # Auth (Clerk)
    CLERK_SECRET_KEY: Optional[str] = Field(default=None, env="CLERK_SECRET_KEY")
    CLERK_PUBLISHABLE_KEY: Optional[str] = Field(default=None, env="CLERK_PUBLISHABLE_KEY")

    # OAuth - Google
    GOOGLE_CLIENT_ID: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = Field(
        default="http://localhost:8000/connections/google/callback",
        env="GOOGLE_REDIRECT_URI"
    )

    # OAuth - HubSpot
    HUBSPOT_CLIENT_ID: Optional[str] = Field(default=None, env="HUBSPOT_CLIENT_ID")
    HUBSPOT_CLIENT_SECRET: Optional[str] = Field(default=None, env="HUBSPOT_CLIENT_SECRET")
    HUBSPOT_REDIRECT_URI: str = Field(
        default="http://localhost:8000/connections/hubspot/callback",
        env="HUBSPOT_REDIRECT_URI"
    )

    # LLM Providers
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")

    # Observability (Langfuse)
    LANGFUSE_SECRET_KEY: Optional[str] = Field(default=None, env="LANGFUSE_SECRET_KEY")
    LANGFUSE_PUBLIC_KEY: Optional[str] = Field(default=None, env="LANGFUSE_PUBLIC_KEY")
    LANGFUSE_HOST: str = Field(
        default="https://cloud.langfuse.com",
        env="LANGFUSE_HOST"
    )

    # Encryption
    ENCRYPTION_KEY: str = Field(
        default=os.getenv("ENCRYPTION_KEY", "default-secret-key-change-in-production"),
        env="ENCRYPTION_KEY"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Initialize settings
settings = Settings()
