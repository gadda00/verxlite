"""
Connections Routes

Manages OAuth connections to external services (Google, HubSpot, etc.).
OAuth state is stored in Redis (with TTL) when available, falling back to an
in-memory dict for tests.
"""

import json
import secrets
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse

from verxlite_api.config import settings
from verxlite_api.db.session import get_db
from verxlite_api.deps import get_current_user
from verxlite_api.models.connection import Connection
from verxlite_api.models.user import User
from verxlite_api.schemas.connection import (
    ConnectionListResponse,
    ConnectionResponse,
    OAuthStateResponse,
)
from verxlite_api.utils.encryption import decrypt_data, encrypt_data
from verxlite_api.utils.logger import get_logger

router = APIRouter(tags=["connections"])
logger = get_logger("connections")


# --------------------------------------------------------------------------- #
# OAuth state store (Redis with in-memory fallback).
# --------------------------------------------------------------------------- #
class _OAuthStateStore:
    """Tiny abstraction over Redis w/ in-memory fallback for tests."""

    def __init__(self):
        self._in_memory: dict[str, dict] = {}
        self._redis = None
        try:
            import redis  # type: ignore

            self._redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
            self._redis.ping()
        except Exception:
            self._redis = None  # Fall back to in-memory.

    def set(self, state: str, data: dict, ttl_seconds: int = 600) -> None:
        payload = json.dumps(data)
        if self._redis:
            self._redis.setex(f"oauth:state:{state}", ttl_seconds, payload)
        else:
            self._in_memory[state] = data

    def pop(self, state: str) -> dict | None:
        if self._redis:
            payload = self._redis.get(f"oauth:state:{state}")
            if not payload:
                return None
            self._redis.delete(f"oauth:state:{state}")
            return json.loads(payload)
        return self._in_memory.pop(state, None)


_oauth_states = _OAuthStateStore()


class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        page_size: int = Query(100, ge=1, le=1000),
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size


# --------------------------------------------------------------------------- #
# CRUD
# --------------------------------------------------------------------------- #
@router.get("/", response_model=ConnectionListResponse)
async def list_connections(
    request: Request,
    pagination: PaginationParams = Depends(),
    provider: str | None = Query(None),
    is_active: bool | None = Query(None),
    is_expired: bool | None = Query(None),
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all connections for the current user (scoped to tenant)."""
    query = db.query(Connection).filter(
        Connection.user_id == current_user.id,
        Connection.tenant_id == current_user.tenant_id,
    )

    if provider:
        query = query.filter(Connection.provider == provider)
    if is_active is not None:
        query = query.filter(Connection.is_active == is_active)
    if is_expired is not None:
        now = datetime.now(timezone.utc)
        if is_expired:
            query = query.filter(Connection.expires_at < now)
        else:
            query = query.filter((Connection.expires_at > now) | (Connection.expires_at.is_(None)))

    total = query.count()
    connections = (
        query.order_by(Connection.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
        .all()
    )

    return ConnectionListResponse(
        connections=[ConnectionResponse.model_validate(c) for c in connections],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(
    connection_id: str,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific connection by ID."""
    connection = (
        db.query(Connection)
        .filter(
            Connection.id == connection_id,
            Connection.user_id == current_user.id,
            Connection.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Connection not found: {connection_id}"
        )
    return ConnectionResponse.model_validate(connection)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: str,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a connection: deactivate and clear tokens."""
    connection = (
        db.query(Connection)
        .filter(
            Connection.id == connection_id,
            Connection.user_id == current_user.id,
            Connection.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Connection not found: {connection_id}"
        )

    connection.is_active = False
    # Clear tokens so they cannot be reused if the row is reactivated.
    connection.access_token = None
    connection.refresh_token = None
    db.commit()
    return None


@router.post("/{connection_id}/refresh", response_model=ConnectionResponse)
async def refresh_connection(
    connection_id: str,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Refresh an OAuth connection's access token."""
    connection = (
        db.query(Connection)
        .filter(
            Connection.id == connection_id,
            Connection.user_id == current_user.id,
            Connection.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Connection not found: {connection_id}"
        )
    if not connection.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No refresh token available"
        )

    refresh_token = decrypt_data(connection.refresh_token)

    if connection.provider == "google":
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    elif connection.provider == "hubspot":
        token_url = "https://api.hubapi.com/oauth/v1/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": settings.HUBSPOT_CLIENT_ID,
            "client_secret": settings.HUBSPOT_CLIENT_SECRET,
            "refresh_token": refresh_token,
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {connection.provider}",
        )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if response.status_code != 200:
            logger.error(f"Token refresh failed for {connection.provider}: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to refresh {connection.provider} token",
            )
        token_data = response.json()

    connection.access_token = encrypt_data(token_data["access_token"])
    new_refresh = token_data.get("refresh_token")
    if new_refresh:
        connection.refresh_token = encrypt_data(new_refresh)
    expires_in = int(token_data.get("expires_in", 3600))
    connection.expires_at = datetime.now(timezone.utc) + timedelta(seconds=max(expires_in - 60, 60))
    connection.is_active = True
    db.commit()
    db.refresh(connection)
    return ConnectionResponse.model_validate(connection)


# --------------------------------------------------------------------------- #
# OAuth — Google
# --------------------------------------------------------------------------- #
GOOGLE_SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
]


@router.get("/google/authorize", response_model=OAuthStateResponse)
async def authorize_google(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Start the Google OAuth flow."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Google OAuth not configured"
        )

    state = secrets.token_urlsafe(32)
    _oauth_states.set(
        state,
        {"user_id": current_user.id, "tenant_id": current_user.tenant_id, "provider": "google"},
    )

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    from urllib.parse import urlencode

    redirect_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return OAuthStateResponse(state=state, provider="google", redirect_url=redirect_url)


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    request: Request,
    db=Depends(get_db),
):
    """Handle the Google OAuth callback."""
    state_data = _oauth_states.pop(state)
    if not state_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OAuth state"
        )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if response.status_code != 200:
            logger.error(f"Google token exchange failed: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange Google code"
            )
        token_data = response.json()

        # Fetch user info
        userinfo = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        user_info = userinfo.json() if userinfo.status_code == 200 else {}

    expires_in = int(token_data.get("expires_in", 3600))
    connection = Connection(
        tenant_id=state_data["tenant_id"],
        user_id=state_data["user_id"],
        provider="google",
        provider_user_id=user_info.get("id"),
        access_token=encrypt_data(token_data["access_token"]),
        refresh_token=encrypt_data(token_data["refresh_token"])
        if token_data.get("refresh_token")
        else None,
        token_type=token_data.get("token_type", "Bearer"),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=max(expires_in - 60, 60)),
        scope=",".join(GOOGLE_SCOPES),
        is_active=True,
        extra_metadata={"user_info": user_info},
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)

    return RedirectResponse(url=f"{settings.FRONTEND_URL}/connections?connected=google")


# --------------------------------------------------------------------------- #
# OAuth — HubSpot
# --------------------------------------------------------------------------- #
HUBSPOT_SCOPES = [
    "crm.objects.contacts.read",
    "crm.objects.contacts.write",
    "crm.objects.notes.read",
    "crm.objects.notes.write",
    "crm.objects.tasks.read",
    "crm.objects.tasks.write",
]


@router.get("/hubspot/authorize", response_model=OAuthStateResponse)
async def authorize_hubspot(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Start the HubSpot OAuth flow."""
    if not settings.HUBSPOT_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="HubSpot OAuth not configured"
        )

    state = secrets.token_urlsafe(32)
    _oauth_states.set(
        state,
        {"user_id": current_user.id, "tenant_id": current_user.tenant_id, "provider": "hubspot"},
    )

    from urllib.parse import urlencode

    params = {
        "client_id": settings.HUBSPOT_CLIENT_ID,
        "redirect_uri": settings.HUBSPOT_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(HUBSPOT_SCOPES),
        "state": state,
    }
    redirect_url = f"https://app.hubspot.com/oauth/authorize?{urlencode(params)}"
    return OAuthStateResponse(state=state, provider="hubspot", redirect_url=redirect_url)


@router.get("/hubspot/callback")
async def hubspot_callback(
    code: str,
    state: str,
    request: Request,
    db=Depends(get_db),
):
    """Handle the HubSpot OAuth callback."""
    state_data = _oauth_states.pop(state)
    if not state_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OAuth state"
        )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.hubapi.com/oauth/v1/token",
            data={
                "grant_type": "authorization_code",
                "client_id": settings.HUBSPOT_CLIENT_ID,
                "client_secret": settings.HUBSPOT_CLIENT_SECRET,
                "redirect_uri": settings.HUBSPOT_REDIRECT_URI,
                "code": code,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if response.status_code != 200:
            logger.error(f"HubSpot token exchange failed: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange HubSpot code"
            )
        token_data = response.json()

        # Fetch token info to get the HubSpot user ID
        info = await client.get(
            "https://api.hubapi.com/oauth/v1/access-tokens/" + token_data["access_token"],
        )
        token_info = info.json() if info.status_code == 200 else {}

    expires_in = int(token_data.get("expires_in", 21600))
    connection = Connection(
        tenant_id=state_data["tenant_id"],
        user_id=state_data["user_id"],
        provider="hubspot",
        provider_user_id=str(token_info.get("user_id", "")),
        access_token=encrypt_data(token_data["access_token"]),
        refresh_token=encrypt_data(token_data["refresh_token"]),
        token_type=token_data.get("token_type", "bearer"),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=max(expires_in - 60, 60)),
        scope=token_data.get("scope", " ".join(HUBSPOT_SCOPES)),
        is_active=True,
        extra_metadata={"hub_user": token_info.get("user")},
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)

    return RedirectResponse(url=f"{settings.FRONTEND_URL}/connections?connected=hubspot")
