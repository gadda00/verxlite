"""
Auth Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import jwt
import os

from verxlite_api.config import settings
from verxlite_api.db.session import get_db
from verxlite_api.models.user import User
from verxlite_api.models.tenant import Tenant
from verxlite_api.utils.logger import get_logger

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger("auth")

# JWT Configuration
JWT_SECRET = settings.CLERK_SECRET_KEY or "verxlite-secret-key"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 30


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserCreateRequest(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tenant_name: Optional[str] = None


class UserLoginRequest(BaseModel):
    email: str
    password: str


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
    })
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str):
    """
    Verify a JWT access token.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


@router.post("/register", response_model=TokenResponse)
async def register_user(
    request: UserCreateRequest,
    db=Depends(get_db),
):
    """
    Register a new user.
    """
    logger.info(f"Registering new user: {request.email}")
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )
    
    # Create or get tenant
    tenant = None
    if request.tenant_name:
        tenant = Tenant(
            name=request.tenant_name,
            description=f"Tenant for {request.email}",
            is_active=True,
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    else:
        tenant = db.query(Tenant).first()
        if not tenant:
            tenant = Tenant(
                name="Default Tenant",
                description="Default workspace",
                is_active=True,
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
    
    # Create user
    user = User(
        tenant_id=tenant.id,
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        role="admin" if not db.query(User).count() else "member",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create access token
    access_token_expires = timedelta(minutes=JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "tenant_id": tenant.id},
        expires_delta=access_token_expires,
    )
    
    logger.info(f"User registered: {user.id}")
    
    return TokenResponse(
        access_token=access_token,
        expires_in=int(access_token_expires.total_seconds()),
        user={
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "tenant_id": tenant.id,
        },
    )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    request: UserLoginRequest,
    db=Depends(get_db),
):
    """
    Login a user.
    """
    logger.info(f"Login attempt for: {request.email}")
    
    # In a real implementation, verify password against hashed password
    # For now, we'll just check if the user exists
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "tenant_id": user.tenant_id},
        expires_delta=access_token_expires,
    )
    
    logger.info(f"User logged in: {user.id}")
    
    return TokenResponse(
        access_token=access_token,
        expires_in=int(access_token_expires.total_seconds()),
        user={
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "tenant_id": user.tenant_id,
        },
    )


@router.get("/me")
async def get_current_user(
    request: Request,
    db=Depends(get_db),
):
    """
    Get the current user from the JWT token.
    """
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    token = token.split(" ")[1]
    payload = verify_access_token(token)
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "tenant_id": user.tenant_id,
    }


# Clerk Webhook for production auth
@router.post("/clerk-webhook")
async def clerk_webhook(
    request: Request,
    db=Depends(get_db),
):
    """
    Handle Clerk webhook events for user synchronization.
    """
    # Verify webhook signature
    # In production, verify the signature using CLERK_SECRET_KEY
    
    body = await request.json()
    event_type = body.get("type")
    data = body.get("data")
    
    logger.info(f"Clerk webhook received: {event_type}")
    
    if event_type == "user.created":
        clerk_id = data.get("id")
        email = data.get("email_addresses", [{}])[0].get("email_address")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        
        # Check if user exists
        existing_user = db.query(User).filter(User.clerk_id == clerk_id).first()
        if existing_user:
            logger.info(f"User already exists: {clerk_id}")
            return {"status": "ok"}
        
        # Create or get tenant
        tenant = db.query(Tenant).first()
        if not tenant:
            tenant = Tenant(
                name="Default Tenant",
                description="Default workspace",
                is_active=True,
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
        
        # Create user
        user = User(
            tenant_id=tenant.id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role="member",
            is_active=True,
            clerk_id=clerk_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"User created from Clerk: {user.id}")
    
    elif event_type == "user.updated":
        clerk_id = data.get("id")
        user = db.query(User).filter(User.clerk_id == clerk_id).first()
        if user:
            user.email = data.get("email_addresses", [{}])[0].get("email_address")
            user.first_name = data.get("first_name")
            user.last_name = data.get("last_name")
            db.commit()
            logger.info(f"User updated from Clerk: {user.id}")
    
    elif event_type == "user.deleted":
        clerk_id = data.get("id")
        user = db.query(User).filter(User.clerk_id == clerk_id).first()
        if user:
            db.delete(user)
            db.commit()
            logger.info(f"User deleted from Clerk: {user.id}")
    
    return {"status": "ok"}
