from fastapi import status
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional


class ErrorResponse(BaseModel):
    """Standard error response model."""
    detail: str
    code: str
    meta: Optional[Dict[str, Any]] = None


class BaseAPIException(HTTPException):
    """Base exception for API errors."""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "internal_server_error"
    message: str = "An unexpected error occurred"
    
    def __init__(
        self,
        message: Optional[str] = None,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.status_code = status_code or self.status_code
        self.code = code or self.code
        self.message = message or self.message
        self.meta = meta or {}
        
        super().__init__(
            status_code=self.status_code,
            detail=self.message,
            headers=headers
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to a dictionary."""
        return {
            "detail": self.message,
            "code": self.code,
            "meta": self.meta
        }


class BadRequestException(BaseAPIException):
    """400 Bad Request."""
    status_code = status.HTTP_400_BAD_REQUEST
    code = "bad_request"
    message = "Invalid request"


class UnauthorizedException(BaseAPIException):
    """401 Unauthorized."""
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"
    message = "Not authenticated"


class ForbiddenException(BaseAPIException):
    """403 Forbidden."""
    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"
    message = "Not enough permissions"


class NotFoundException(BaseAPIException):
    """404 Not Found."""
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"
    message = "Resource not found"


class ConflictException(BaseAPIException):
    """409 Conflict."""
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"
    message = "Resource already exists"


class UnprocessableEntityException(BaseAPIException):
    """422 Unprocessable Entity."""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    code = "unprocessable_entity"
    message = "Validation error"


class RateLimitExceededException(BaseAPIException):
    """429 Too Many Requests."""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "rate_limit_exceeded"
    message = "Rate limit exceeded"


class ServiceUnavailableException(BaseAPIException):
    """503 Service Unavailable."""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "service_unavailable"
    message = "Service temporarily unavailable"


# Custom application exceptions
class InvalidFileTypeException(BadRequestException):
    """Invalid file type."""
    code = "invalid_file_type"
    message = "Invalid file type"


class FileTooLargeException(BadRequestException):
    """File too large."""
    code = "file_too_large"
    message = "File size exceeds the maximum allowed limit"


class DockerOperationException(ServiceUnavailableException):
    """Docker operation failed."""
    code = "docker_operation_failed"
    message = "Docker operation failed"


def handle_http_exception(request, exc: HTTPException):
    """Handle HTTP exceptions and return a standardized error response."""
    from fastapi.responses import JSONResponse
    
    status_code = exc.status_code
    detail = exc.detail
    
    if isinstance(detail, dict):
        error_code = detail.get("code", "unknown_error")
        error_message = detail.get("detail", str(detail))
        error_meta = detail.get("meta", {})
    else:
        error_code = "unknown_error"
        error_message = str(detail)
        error_meta = {}
    
    error_response = ErrorResponse(
        detail=error_message,
        code=error_code,
        meta=error_meta
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.dict()
    )
