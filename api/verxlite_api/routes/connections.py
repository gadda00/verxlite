"""
Connections Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import httpx
import json
import secrets

from verxlite_api.config import settings
from verxlite_api.db.session import get_db
from verxlite_api.models.connection import Connection
from verxlite_api.models.user import User
from verxlite_api.models.tenant import Tenant
from verxlite_api.utils.logger import get_logger
from verxlite_api.utils.encryption import encrypt_data, decrypt_data

router = APIRouter(prefix="/connections", tags=["connections"])
logger = get_logger("connections")


class ConnectionResponse(BaseModel):
    id: str
    provider: str
    is_active: bool
    created_at: datetime
    provider_user_id: Optional[str] = None
    scope: Optional[str] = None


class ConnectionListResponse(BaseModel):
    connections: List[ConnectionResponse]


class OAuthState(BaseModel):
    state: str
    provider: str
    user_id: str
    tenant_id: str


# In-memory store for OAuth states (in production, use Redis)
oauth_states = {}


@router.get("/", response_model=ConnectionListResponse)
async def list_connections(
    request: Request,
    db=Depends(get_db),
):
    """
    List all connections for the current user.
    """
    # Get current user from JWT
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    # For now, we'll use a simple approach - in production, use Clerk
    user_id = "test-user-id"
    
    connections = db.query(Connection).filter(Connection.user_id == user_id).all()
    
    return ConnectionListResponse(
        connections=[
            ConnectionResponse(
                id=conn.id,
                provider=conn.provider,
                is_active=conn.is_active,
                created_at=conn.created_at,
                provider_user_id=conn.provider_user_id,
                scope=conn.scope,
            )
            for conn in connections
        ]
    )


@router.get("/google/authorize")
async def google_authorize(
    request: Request,
    db=Depends(get_db),
):
    """
    Start Google OAuth flow.
    """
    # Get current user from JWT
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    # For now, we'll use a simple approach - in production, use Clerk
    user_id = "test-user-id"
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Generate state token
    state = secrets.token_urlsafe(32)
    oauth_states[state] = OAuthState(
        state=state,
        provider="google",
        user_id=user.id,
        tenant_id=user.tenant_id,
    )
    
    # Build Google OAuth URL
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile%20https://www.googleapis.com/auth/gmail.readonly%20https://www.googleapis.com/auth/calendar.readonly"
        f"&access_type=offline"
        f"&prompt=consent"
        f"&state={state}"
    )
    
    logger.info(f"Starting Google OAuth for user: {user.id}")
    
    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str,
    state: str,
    db=Depends(get_db),
):
    """
    Handle Google OAuth callback.
    """
    # Verify state
    if state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state",
        )
    
    oauth_state = oauth_states.pop(state)
    
    # Exchange code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for tokens",
            )
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in")
        scope = token_data.get("scope")
    
    # Get user info
    user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(user_info_url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info",
            )
        
        user_info = response.json()
        provider_user_id = user_info.get("id")
    
    # Save connection
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
    
    connection = Connection(
        tenant_id=oauth_state.tenant_id,
        user_id=oauth_state.user_id,
        provider="google",
        provider_user_id=provider_user_id,
        access_token=encrypt_data(access_token, settings.ENCRYPTION_KEY),
        refresh_token=encrypt_data(refresh_token, settings.ENCRYPTION_KEY),
        token_type="Bearer",
        expires_at=expires_at,
        scope=scope,
        is_active=True,
        metadata={"user_info": user_info},
    )
    
    db.add(connection)
    db.commit()
    db.refresh(connection)
    
    logger.info(f"Google connection created: {connection.id}")
    
    # Redirect to frontend with success
    return RedirectResponse(
        url=f"http://localhost:3000/connections/success?provider=google&connection_id={connection.id}"
    )


@router.get("/hubspot/authorize")
async def hubspot_authorize(
    request: Request,
    db=Depends(get_db),
):
    """
    Start HubSpot OAuth flow.
    """
    # Get current user from JWT
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    # For now, we'll use a simple approach - in production, use Clerk
    user_id = "test-user-id"
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Generate state token
    state = secrets.token_urlsafe(32)
    oauth_states[state] = OAuthState(
        state=state,
        provider="hubspot",
        user_id=user.id,
        tenant_id=user.tenant_id,
    )
    
    # Build HubSpot OAuth URL
    hubspot_auth_url = (
        "https://app.hubspot.com/oauth/authorize"
        f"?client_id={settings.HUBSPOT_CLIENT_ID}"
        f"&redirect_uri={settings.HUBSPOT_REDIRECT_URI}"
        f"&scope=contacts%20content%20automation"
        f"&state={state}"
    )
    
    logger.info(f"Starting HubSpot OAuth for user: {user.id}")
    
    return RedirectResponse(url=hubspot_auth_url)


@router.get("/hubspot/callback")
async def hubspot_callback(
    request: Request,
    code: str,
    state: str,
    db=Depends(get_db),
):
    """
    Handle HubSpot OAuth callback.
    """
    # Verify state
    if state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state",
        )
    
    oauth_state = oauth_states.pop(state)
    
    # Exchange code for tokens
    token_url = "https://api.hubapi.com/oauth/v1/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": settings.HUBSPOT_CLIENT_ID,
        "client_secret": settings.HUBSPOT_CLIENT_SECRET,
        "redirect_uri": settings.HUBSPOT_REDIRECT_URI,
        "code": code,
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for tokens",
            )
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in")
        scope = token_data.get("scope")
    
    # Get user info (HubSpot doesn't have a standard userinfo endpoint)
    # We'll use the access token to make a test API call
    test_url = "https://api.hubapi.com/crm/v3/objects/contacts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(test_url, headers=headers)
        if response.status_code != 200:
            logger.warning(f"Failed to get HubSpot user info: {response.status_code}")
    
    # Save connection
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
    
    connection = Connection(
        tenant_id=oauth_state.tenant_id,
        user_id=oauth_state.user_id,
        provider="hubspot",
        provider_user_id=None,  # HubSpot doesn't provide a user ID in the same way
        access_token=encrypt_data(access_token, settings.ENCRYPTION_KEY),
        refresh_token=encrypt_data(refresh_token, settings.ENCRYPTION_KEY),
        token_type="Bearer",
        expires_at=expires_at,
        scope=scope,
        is_active=True,
        metadata={},
    )
    
    db.add(connection)
    db.commit()
    db.refresh(connection)
    
    logger.info(f"HubSpot connection created: {connection.id}")
    
    # Redirect to frontend with success
    return RedirectResponse(
        url=f"http://localhost:3000/connections/success?provider=hubspot&connection_id={connection.id}"
    )


@router.delete("/{connection_id}")
async def delete_connection(
    connection_id: str,
    request: Request,
    db=Depends(get_db),
):
    """
    Delete a connection.
    """
    # Get current user from JWT
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    # For now, we'll use a simple approach - in production, use Clerk
    user_id = "test-user-id"
    
    connection = db.query(Connection).filter(
        Connection.id == connection_id,
        Connection.user_id == user_id,
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found",
        )
    
    db.delete(connection)
    db.commit()
    
    logger.info(f"Connection deleted: {connection_id}")
    
    return {"status": "ok", "message": "Connection deleted"}
