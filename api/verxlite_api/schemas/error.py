"""
Error Response Schemas
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime, timezone


class ErrorDetail(BaseModel):
    """Error detail model."""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: Optional[str] = None
    status_code: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "ValidationError",
                "message": "Invalid request data",
                "details": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "code": "invalid_format"
                    }
                ],
                "timestamp": "2024-01-01T12:00:00Z",
                "request_id": "req_abc123",
                "status_code": 400
            }
        }
    )


class ValidationErrorResponse(ErrorResponse):
    """Validation error response."""
    error: str = "ValidationError"


class AuthenticationErrorResponse(ErrorResponse):
    """Authentication error response."""
    error: str = "AuthenticationError"


class AuthorizationErrorResponse(ErrorResponse):
    """Authorization error response."""
    error: str = "AuthorizationError"


class NotFoundErrorResponse(ErrorResponse):
    """Not found error response."""
    error: str = "NotFoundError"


class RateLimitErrorResponse(ErrorResponse):
    """Rate limit error response."""
    error: str = "RateLimitError"
    retry_after: Optional[int] = None  # Seconds to wait before retry


class InternalErrorResponse(ErrorResponse):
    """Internal server error response."""
    error: str = "InternalServerError"
