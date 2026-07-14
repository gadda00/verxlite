"""
Auth Dependencies

Provides `get_current_user` for FastAPI dependency injection. Supports two modes:
  1. Email/password (dev fallback) — JWT signed with settings.JWT_SECRET.
  2. Clerk JWT (production) — verified with settings.CLERK_SECRET_KEY when set.
"""

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta, timezone
import jwt

from verxlite_api.config import settings
from verxlite_api.db.session import get_db
from verxlite_api.models.user import User
from verxlite_api.models.tenant import Tenant


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token (email/password mode)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_access_token(token: str) -> dict:
    """Verify a JWT access token (email/password mode)."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
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


def _extract_bearer_token(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return auth.split(" ", 1)[1]


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    Resolve the authenticated user from the request.

    Supports two modes:
      1. If `settings.CLERK_SECRET_KEY` is set, treat the bearer token as a Clerk session JWT
         and look up the user by `clerk_id` (claim `sub`).
      2. Otherwise, treat it as a locally-signed JWT (email/password mode).
    """
    token = _extract_bearer_token(request)

    if settings.CLERK_SECRET_KEY:
        # Production mode: verify Clerk JWT.
        try:
            payload = jwt.decode(
                token,
                settings.CLERK_SECRET_KEY,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Clerk token",
            )
        clerk_id = payload.get("sub")
        user = db.query(User).filter(User.clerk_id == clerk_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return user

    # Dev mode: local JWT.
    payload = verify_access_token(token)
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """Require the authenticated user to be an admin."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user


def hash_password(password: str) -> str:
    """Hash a password using bcrypt directly (avoids passlib/bcrypt-4.x incompat)."""
    import bcrypt
    # bcrypt has a 72-byte limit; truncate to avoid ValueError.
    pw_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: Optional[str]) -> bool:
    """Verify a password against a bcrypt hash."""
    if not password_hash:
        return False
    import bcrypt
    try:
        pw_bytes = password.encode("utf-8")[:72]
        hash_bytes = password_hash.encode("ascii")
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except Exception:
        return False
