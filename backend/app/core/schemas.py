"""Pydantic models for API responses and common data structures."""
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

# Type variable for generic response data
T = TypeVar('T')

class ErrorDetail(BaseModel):
    """Detailed error information."""
    type: str = Field(..., description="Error type/classification")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details or validation errors"
    )

class BaseResponse(BaseModel):
    """Base response model for all API responses."""
    success: bool = Field(..., description="Indicates if the request was successful")
    message: Optional[str] = Field(
        None,
        description="Optional success/status message"
    )
    error: Optional[ErrorDetail] = Field(
        None,
        description="Error details if the request failed"
    )

class SuccessResponse(GenericModel, Generic[T]):
    """Generic success response model with data."""
    success: bool = Field(True, description="Always true for successful responses")
    data: T = Field(..., description="Response data")
    meta: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata about the response"
    )

class ErrorResponse(BaseResponse):
    """Error response model."""
    success: bool = Field(False, description="Always false for error responses")
    error: ErrorDetail = Field(..., description="Error details")

class PaginatedResponse(GenericModel, Generic[T]):
    """Paginated response model for collections."""
    success: bool = Field(True, description="Always true for successful responses")
    data: List[T] = Field(..., description="List of items in the current page")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")

class ValidationErrorDetail(BaseModel):
    """Detailed validation error information."""
    field: str = Field(..., description="The field that failed validation")
    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type/classification")

class ValidationErrorResponse(ErrorResponse):
    """Response model for validation errors."""
    error: ErrorDetail = Field(
        ...,
        example={
            "type": "ValidationError",
            "message": "Invalid request data",
            "details": {
                "fields": [
                    {
                        "field": "email",
                        "message": "value is not a valid email address",
                        "type": "value_error.email"
                    }
                ]
            }
        }
    )

class NotFoundErrorResponse(ErrorResponse):
    """Response model for not found errors."""
    error: ErrorDetail = Field(
        ...,
        example={
            "type": "NotFoundError",
            "message": "Resource not found",
            "details": {
                "resource": "user",
                "id": "123"
            }
        }
    )

class UnauthorizedErrorResponse(ErrorResponse):
    """Response model for unauthorized errors."""
    error: ErrorDetail = Field(
        ...,
        example={
            "type": "AuthenticationError",
            "message": "Not authenticated",
            "details": {
                "required_scope": "read:users"
            }
        }
    )

class ForbiddenErrorResponse(ErrorResponse):
    """Response model for forbidden errors."""
    error: ErrorDetail = Field(
        ...,
        example={
            "type": "AuthorizationError",
            "message": "Insufficient permissions",
            "details": {
                "required_permission": "users:delete"
            }
        }
    )

class ConflictErrorResponse(ErrorResponse):
    """Response model for conflict errors."""
    error: ErrorDetail = Field(
        ...,
        example={
            "type": "ConflictError",
            "message": "Resource already exists",
            "details": {
                "resource": "email",
                "value": "user@example.com"
            }
        }
    )

class RateLimitErrorResponse(ErrorResponse):
    """Response model for rate limit errors."""
    error: ErrorDetail = Field(
        ...,
        example={
            "type": "RateLimitExceeded",
            "message": "Too many requests, please try again later",
            "details": {
                "retry_after": 60,
                "limit": 100,
                "window": "1m"
            }
        }
    )

class InternalServerErrorResponse(ErrorResponse):
    """Response model for internal server errors."""
    error: ErrorDetail = Field(
        ...,
        example={
            "type": "InternalServerError",
            "message": "An unexpected error occurred",
            "details": {
                "error_id": "err_550e8400-e29b-41d4-a716-446655440000"
            }
        }
    )

# Common response models for OpenAPI documentation
responses = {
    400: {"model": ErrorResponse, "description": "Bad Request"},
    401: {"model": UnauthorizedErrorResponse, "description": "Unauthorized"},
    403: {"model": ForbiddenErrorResponse, "description": "Forbidden"},
    404: {"model": NotFoundErrorResponse, "description": "Not Found"},
    409: {"model": ConflictErrorResponse, "description": "Conflict"},
    422: {"model": ValidationErrorResponse, "description": "Validation Error"},
    429: {"model": RateLimitErrorResponse, "description": "Too Many Requests"},
    500: {"model": InternalServerErrorResponse, "description": "Internal Server Error"},
}
