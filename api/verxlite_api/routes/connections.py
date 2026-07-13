"""
Connections Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import httpx
import secrets
import json

from verxlite_api.config import settings
from verxlite_api.db.session import get_db
from verxlite_api.models.connection import Connection
from verxlite_api.models.user import User
from verxlite_api.models.tenant import Tenant
from verxlite_api.schemas.connection import (
    ConnectionResponse,
    ConnectionListResponse,
    ConnectionCreate,
    ConnectionUpdate,
    OAuthStateResponse,
)
from verxlite_api.schemas.error import NotFoundErrorResponse, AuthorizationErrorResponse
from verxlite_api.utils.logger import get_logger
from verxlite_api.utils.encryption import encrypt_data, decrypt_data
from verxlite_api.connectors.google import GoogleConnector
from verxlite_api.connectors.hubspot import HubSpotConnector

router = APIRouter(prefix="/connections", tags=["connections"])
logger = get_logger("connections")


# In-memory store for OAuth states (in production, use Redis)
oauth_states = {}


class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size


@router.get("/", response_model=ConnectionListResponse)
async def list_connections(
    request: Request,
    db=Depends(get_db),
    pagination: PaginationParams = Depends(),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_expired: Optional[bool] = Query(None, description="Filter by expired status"),
):
    """
    List all connections for the current user.
    
    Supports:
    - Pagination
    - Filtering by provider, active status, expired status
    """
    # Get current user from JWT (in production, use real auth)
    user_id = "test-user-id"
    tenant_id = "test-tenant-id"
    
    query = db.query(Connection).filter(
        Connection.user_id == user_id,
        Connection.tenant_id == tenant_id,
    )
    
    # Apply filters
    if provider:
        query = query.filter(Connection.provider == provider)
    
    if is_active is not None:
        query = query.filter(Connection.is_active == is_active)
    
    if is_expired is not None:
        if is_expired:
            query = query.filter(Connection.expires_at < datetime.utcnow())
        else:
            query = query.filter(
                (Connection.expires_at > datetime.utcnow()) |
                (Connection.expires_at.is_(None))
            )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    connections = query.order_by(
        Connection.created_at.desc()
    ).offset(pagination.offset).limit(pagination.page_size).all()
    
    return ConnectionListResponse(
        connections=[ConnectionResponse.from_orm(conn) for conn in connections],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(
    connection_id: str,
    request: Request,
    db=Depends(get_db),
):
    """
    Get a specific connection by ID.
    """
    user_id = "test-user-id"
    tenant_id = "test-tenant-id"
    
    connection = db.query(Connection).filter(
        Connection.id == connection_id,
        Connection.user_id == user_id,
        Connection.tenant_id == tenant_id,
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection not found: {connection_id}",
        )
    
    return ConnectionResponse.from_orm(connection)


@router.post("/{connection_id}/refresh", response_model=ConnectionResponse)
async def refresh_connection(
    connection_id: str,
    request: Request,
    db=Depends(get_db),
):
    """
    Refresh an OAuth connection's access token.
    """
    user_id = "test-user-id"
    tenant_id = "test-tenant-id"
    
    connection = db.query(Connection).filter(
        Connection.id == connection_id,
        Connection.user_id == user_id,
        Connection.tenant_id == tenant_id,
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection not found: {connection_id}",
        )
    
    if not connection.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No refresh token available",
        )
    
    try:
        if connection.provider == "google":
            # Refresh Google token
            refresh_token = decrypt_data(connection.refresh_token, settings.ENCRYPTION_KEY)
            
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to refresh Google token",
                    )
                
                token_data = response.json()
                new_access_token = token_data.get("access_token")
                new_expires_in = token_data.get("expires_in")
                new_refresh_token = token_data.get("refresh_token", refresh_token)
            
            # Update connection
            connection.access_token = encrypt_data(new_access_token, settings.ENCRYPTION_KEY)
            if new_refresh_token:
                connection.refresh_token = encrypt_data(new_refresh_token, settings.ENCRYPTION_KEY)
            connection.expires_at = datetime.utcnow() + timedelta(seconds=new_expires_in - 60)
            connection.is_active = True
            connection.updated_at = datetime.utcnow()
            
        elif connection.provider == "hubspot":
            # Refresh HubSpot token
            refresh_token = decrypt_data(connection.refresh_token, settings.ENCRYPTION_KEY)
            
            token_url = "https://api.hubapi.com/oauth/v1/token"
            data = {
                "grant_type": "refresh_token",
                "client_id": settings.HUBSPOT_CLIENT_ID,
                "client_secret": settings.HUBSPOT_CLIENT_SECRET,
                "refresh_token": refresh_token,
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
                        detail="Failed to refresh HubSpot token",
                    )
                
                token_data = response.json()
                new_access_token = token_data.get("access_token")
                new_expires_in = token_data.get("expires_in")
                new_refresh_token = token_data.get("refresh_token", refresh_token)
            
            # Update connection
            connection.access_token = encrypt_data(new_access_token, settings.ENCRYPTION_KEY)
            if new_refresh_token:
                connection.refresh_token = encrypt_data(new_refresh_token, settings.ENCRYPTION_KEY)
            connection.expires_at = datetime.utcnow() + timedelta(seconds=new_expires_in - 60)
            connection.is_active = True
            connection.updated_at = datetime.utcnow()
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {connection.provider}",
            )
        
        db.commit()
        db.refresh(connection)
        
        logger.info(f"Refreshed connection: {connection.id}")
        
        return ConnectionResponse.from_orm(connection)
        
    except Exception as e:
        logger.error(f"Failed to refresh connection: {connection.id}, error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh connection",
        )


@router.post("/{connection_id}/sync", response_model=ConnectionResponse)
async def sync_connection(
    connection_id: str,
    request: Request,
    db=Depends(get_db),
):
    """
    Sync data from a connection (e.g., fetch recent emails, contacts).
    """
    user_id = "test-user-id"
    tenant_id = "test-tenant-id"
    
    connection = db.query(Connection).filter(
        Connection.id == connection_id,
        Connection.user_id == user_id,
        Connection.tenant_id == tenant_id,
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection not found: {connection_id}",
        )
    
    if not connection.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot sync inactive connection",
        )
    
    try:
        # Mark sync as starting
        connection.sync_status = "pending"
        connection.sync_error = None
        connection.last_sync_at = datetime.utcnow()
        db.commit()
        
        # In production, this would trigger a background task
        # For now, we'll just mark it as completed
        connection.sync_status = "success"
        db.commit()
        db.refresh(connection)
        
        logger.info(f"Synced connection: {connection.id}")
        
        return ConnectionResponse.from_orm(connection)
        
    except Exception as e:
        connection.sync_status = "failed"
        connection.sync_error = str(e)
        db.commit()
        
        logger.error(f"Failed to sync connection: {connection.id}, error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync connection",
        )


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: str,
    request: Request,
    db=Depends(get_db),
):
    """
    Delete a connection.
    """
    user_id = "test-user-id"
    tenant_id = "test-tenant-id"
    
    connection = db.query(Connection).filter(
        Connection.id == connection_id,
        Connection.user_id == user_id,
        Connection.tenant_id == tenant_id,
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection not found: {connection_id}",
        )
    
    # Soft delete (set is_active to False)
    connection.is_active = False
    connection.updated_at = datetime.utcnow()
    
    db.commit()
    
    logger.info(f"Deleted connection: {connection_id}")
    
    return None


# Google OAuth endpoints
@router.get("/google/authorize")
async def google_authorize(
    request: Request,
    db=Depends(get_db),
):
    """
    Start Google OAuth flow.
    
    Returns:
        - OAuth state
        - Redirect URL to Google
    """
    user_id = "test-user-id"
    tenant_id = "test-tenant-id"
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Generate state token
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        "provider": "google",
        "user_id": user_id,
        "tenant_id": tenant_id,
        "created_at": datetime.utcnow().isoformat(),
    }
    
    # Build Google OAuth URL
    scopes = [
        "openid",
        "email",
        "profile",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={'%20'.join(scopes)}"
        f"&access_type=offline"
        f"&prompt=consent"
        f"&state={state}"
    )
    
    logger.info(f"Starting Google OAuth for user: {user_id}")
    
    return OAuthStateResponse(
        state=state,
        provider="google",
        redirect_url=google_auth_url,
    )


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="State token"),
    error: Optional[str] = Query(None, description="Error message"),
    db=Depends(get_db),
):
    """
    Handle Google OAuth callback.
    
    This endpoint:
    - Validates the state token
    - Exchanges the authorization code for tokens
    - Creates or updates the connection
    - Redirects to the frontend
    """
    # Check for errors
    if error:
        logger.error(f"Google OAuth error: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth error: {error}",
        )
    
    # Verify state
    if state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state token",
        )
    
    oauth_state = oauth_states.pop(state)
    user_id = oauth_state["user_id"]
    tenant_id = oauth_state["tenant_id"]
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Exchange code for tokens
    try:
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
        
        # Check if connection already exists
        existing_connection = db.query(Connection).filter(
            Connection.user_id == user_id,
            Connection.provider == "google",
        ).first()
        
        if existing_connection:
            # Update existing connection
            existing_connection.access_token = encrypt_data(access_token, settings.ENCRYPTION_KEY)
            existing_connection.refresh_token = encrypt_data(refresh_token, settings.ENCRYPTION_KEY)
            existing_connection.token_type = "Bearer"
            existing_connection.expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
            existing_connection.scope = scope
            existing_connection.is_active = True
            existing_connection.provider_user_id = provider_user_id
            existing_connection.metadata = {
                "user_info": user_info,
                "updated_at": datetime.utcnow().isoformat(),
            }
            existing_connection.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(existing_connection)
            
            logger.info(f"Updated Google connection: {existing_connection.id}")
            
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/connections/success?provider=google&connection_id={existing_connection.id}"
            )
        
        # Create new connection
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
        
        connection = Connection(
            tenant_id=tenant_id,
            user_id=user_id,
            provider="google",
            provider_user_id=provider_user_id,
            access_token=encrypt_data(access_token, settings.ENCRYPTION_KEY),
            refresh_token=encrypt_data(refresh_token, settings.ENCRYPTION_KEY),
            token_type="Bearer",
            expires_at=expires_at,
            scope=scope,
            is_active=True,
            metadata={
                "user_info": user_info,
                "created_at": datetime.utcnow().isoformat(),
            },
        )
        
        db.add(connection)
        db.commit()
        db.refresh(connection)
        
        logger.info(f"Created Google connection: {connection.id}")
        
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/connections/success?provider=google&connection_id={connection.id}"
        )
        
    except Exception as e:
        logger.error(f"Google OAuth callback failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth callback failed",
        )


# HubSpot OAuth endpoints
@router.get("/hubspot/authorize")
async def hubspot_authorize(
    request: Request,
    db=Depends(get_db),
):
    """
    Start HubSpot OAuth flow.
    """
    user_id = "test-user-id"
    tenant_id = "test-tenant-id"
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Generate state token
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        "provider": "hubspot",
        "user_id": user_id,
        "tenant_id": tenant_id,
        "created_at": datetime.utcnow().isoformat(),
    }
    
    # Build HubSpot OAuth URL
    scopes = [
        "contacts",
        "content",
        "automation",
        "crm.objects.owners.read",
        "crm.objects.contacts.read",
        "crm.objects.contacts.write",
        "crm.objects.deals.read",
        "crm.objects.deals.write",
        "crm.objects.tasks.read",
        "crm.objects.tasks.write",
    ]
    
    hubspot_auth_url = (
        "https://app.hubspot.com/oauth/authorize"
        f"?client_id={settings.HUBSPOT_CLIENT_ID}"
        f"&redirect_uri={settings.HUBSPOT_REDIRECT_URI}"
        f"&scope={'%20'.join(scopes)}"
        f"&state={state}"
    )
    
    logger.info(f"Starting HubSpot OAuth for user: {user_id}")
    
    return OAuthStateResponse(
        state=state,
        provider="hubspot",
        redirect_url=hubspot_auth_url,
    )


@router.get("/hubspot/callback")
async def hubspot_callback(
    request: Request,
    code: str = Query(..., description="Authorization code from HubSpot"),
    state: str = Query(..., description="State token"),
    error: Optional[str] = Query(None, description="Error message"),
    db=Depends(get_db),
):
    """
    Handle HubSpot OAuth callback.
    """
    # Check for errors
    if error:
        logger.error(f"HubSpot OAuth error: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"HubSpot OAuth error: {error}",
        )
    
    # Verify state
    if state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state token",
        )
    
    oauth_state = oauth_states.pop(state)
    user_id = oauth_state["user_id"]
    tenant_id = oauth_state["tenant_id"]
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Exchange code for tokens
    try:
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
        
        # Check if connection already exists
        existing_connection = db.query(Connection).filter(
            Connection.user_id == user_id,
            Connection.provider == "hubspot",
        ).first()
        
        if existing_connection:
            # Update existing connection
            existing_connection.access_token = encrypt_data(access_token, settings.ENCRYPTION_KEY)
            existing_connection.refresh_token = encrypt_data(refresh_token, settings.ENCRYPTION_KEY)
            existing_connection.token_type = "Bearer"
            existing_connection.expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
            existing_connection.scope = scope
            existing_connection.is_active = True
            existing_connection.metadata = {
                "updated_at": datetime.utcnow().isoformat(),
            }
            existing_connection.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(existing_connection)
            
            logger.info(f"Updated HubSpot connection: {existing_connection.id}")
            
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/connections/success?provider=hubspot&connection_id={existing_connection.id}"
            )
        
        # Create new connection
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
        
        connection = Connection(
            tenant_id=tenant_id,
            user_id=user_id,
            provider="hubspot",
            provider_user_id=None,  # HubSpot doesn't provide a user ID in the same way
            access_token=encrypt_data(access_token, settings.ENCRYPTION_KEY),
            refresh_token=encrypt_data(refresh_token, settings.ENCRYPTION_KEY),
            token_type="Bearer",
            expires_at=expires_at,
            scope=scope,
            is_active=True,
            metadata={
                "created_at": datetime.utcnow().isoformat(),
            },
        )
        
        db.add(connection)
        db.commit()
        db.refresh(connection)
        
        logger.info(f"Created HubSpot connection: {connection.id}")
        
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/connections/success?provider=hubspot&connection_id={connection.id}"
        )
        
    except Exception as e:
        logger.error(f"HubSpot OAuth callback failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="HubSpot OAuth callback failed",
        )
