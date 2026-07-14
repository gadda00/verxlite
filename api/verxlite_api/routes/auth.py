"""
Auth Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timezone
import jwt

from verxlite_api.config import settings
from verxlite_api.db.session import get_db
from verxlite_api.models.user import User
from verxlite_api.models.tenant import Tenant
from verxlite_api.utils.logger import get_logger
from verxlite_api.deps import (
    create_access_token,
    verify_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(tags=["auth"])
logger = get_logger("auth")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tenant_name: Optional[str] = None


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: UserCreateRequest,
    db=Depends(get_db),
):
    """Register a new user with email + password."""
    logger.info(f"Registering new user: {request.email}")

    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )

    # Create or get tenant
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

    # First user in this tenant becomes admin
    users_in_tenant = db.query(User).filter(User.tenant_id == tenant.id).count()
    role = "admin" if users_in_tenant == 0 else "member"

    user = User(
        tenant_id=tenant.id,
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        role=role,
        is_active=True,
        password_hash=hash_password(request.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "tenant_id": tenant.id, "role": user.role}
    )

    logger.info(f"User registered: {user.id}")

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
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
    """Login a user with email + password (verifies password hash)."""
    logger.info(f"Login attempt for: {request.email}")

    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        # Constant-time-ish response: don't leak whether the email exists.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "tenant_id": user.tenant_id, "role": user.role}
    )

    logger.info(f"User logged in: {user.id}")

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
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
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "tenant_id": current_user.tenant_id,
    }


def _verify_clerk_webhook(request: Request, body: bytes) -> bool:
    """
    Verify the Clerk webhook signature using svix.

    Returns True if valid or if CLERK_WEBHOOK_SECRET is unset (dev mode).
    """
    if not settings.CLERK_WEBHOOK_SECRET:
        logger.warning("CLERK_WEBHOOK_SECRET not set — webhook signature verification skipped (dev only)")
        return True

    from svix import Webhook, WebhookVerificationError

    wh = Webhook(settings.CLERK_WEBHOOK_SECRET)
    svix_id = request.headers.get("svix-id")
    svix_timestamp = request.headers.get("svix-timestamp")
    svix_signature = request.headers.get("svix-signature")
    if not (svix_id and svix_timestamp and svix_signature):
        return False
    try:
        wh.verify(body, {
            "svix-id": svix_id,
            "svix-timestamp": svix_timestamp,
            "svix-signature": svix_signature,
        })
        return True
    except WebhookVerificationError:
        return False


@router.post("/clerk-webhook")
async def clerk_webhook(
    request: Request,
    db=Depends(get_db),
):
    """Handle Clerk webhook events for user synchronization."""
    body = await request.body()
    if not _verify_clerk_webhook(request, body):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    import json
    payload = json.loads(body)
    event_type = payload.get("type")
    data = payload.get("data", {})

    logger.info(f"Clerk webhook received: {event_type}")

    if event_type == "user.created":
        clerk_id = data.get("id")
        email = (data.get("email_addresses") or [{}])[0].get("email_address")
        first_name = data.get("first_name")
        last_name = data.get("last_name")

        existing = db.query(User).filter(User.clerk_id == clerk_id).first()
        if existing:
            return {"status": "ok"}

        tenant = db.query(Tenant).first()
        if not tenant:
            tenant = Tenant(name="Default Tenant", description="Default workspace", is_active=True)
            db.add(tenant)
            db.commit()
            db.refresh(tenant)

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
        logger.info(f"User created from Clerk: {user.id}")

    elif event_type == "user.updated":
        clerk_id = data.get("id")
        user = db.query(User).filter(User.clerk_id == clerk_id).first()
        if user:
            user.email = (data.get("email_addresses") or [{}])[0].get("email_address", user.email)
            user.first_name = data.get("first_name", user.first_name)
            user.last_name = data.get("last_name", user.last_name)
            db.commit()

    elif event_type == "user.deleted":
        clerk_id = data.get("id")
        user = db.query(User).filter(User.clerk_id == clerk_id).first()
        if user:
            # Soft delete: deactivate instead of hard delete.
            user.is_active = False
            db.commit()
            logger.info(f"User deactivated from Clerk: {user.id}")

    return {"status": "ok"}
