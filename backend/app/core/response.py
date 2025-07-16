from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic.generics import GenericModel

from app.core.exceptions import ErrorResponse

# Type variable for generic response data
T = TypeVar("T")

class Pagination(BaseModel):
    """Pagination metadata for paginated responses."""
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_previous: bool

class BaseResponse(GenericModel, Generic[T]):
    """Base response model for all API responses."""
    success: bool = True
    data: Optional[T] = None
    error: Optional[ErrorResponse] = None
    meta: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            # Add custom JSON encoders here
        }

class SuccessResponse(JSONResponse):
    """Standard success response with a 200 status code."""
    
    def __init__(
        self,
        data: Any = None,
        status_code: int = status.HTTP_200_OK,
        headers: Optional[Dict[str, str]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a success response.
        
        Args:
            data: The response data
            status_code: HTTP status code (default: 200)
            headers: HTTP headers
            meta: Additional metadata
        """
        content = BaseResponse[Any](
            success=True,
            data=data,
            meta=meta or {},
        )
        
        super().__init__(
            content=jsonable_encoder(content, exclude_none=True),
            status_code=status_code,
            headers=headers,
        )

class CreatedResponse(SuccessResponse):
    """201 Created response with a location header."""
    
    def __init__(
        self,
        data: Any = None,
        location: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a created response.
        
        Args:
            data: The created resource
            location: URL of the created resource
            meta: Additional metadata
        """
        headers = {"Location": location} if location else None
        super().__init__(
            data=data,
            status_code=status.HTTP_201_CREATED,
            headers=headers,
            meta=meta,
        )

class PaginatedResponse(SuccessResponse):
    """Paginated response with metadata."""
    
    def __init__(
        self,
        data: List[Any],
        total: int,
        page: int,
        size: int,
        meta: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a paginated response.
        
        Args:
            data: List of items on the current page
            total: Total number of items
            page: Current page number (1-based)
            size: Number of items per page
            meta: Additional metadata
        """
        pages = (total + size - 1) // size if size > 0 else 1
        
        pagination_meta = {
            "pagination": {
                "total": total,
                "page": page,
                "size": size,
                "pages": pages,
                "has_next": page < pages,
                "has_previous": page > 1,
            }
        }
        
        if meta:
            pagination_meta.update(meta)
        
        super().__init__(data=data, meta=pagination_meta)

class ErrorResponse(JSONResponse):
    """Standard error response."""
    
    def __init__(
        self,
        message: str,
        code: str = "error",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        headers: Optional[Dict[str, str]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize an error response.
        
        Args:
            message: Error message
            code: Error code
            status_code: HTTP status code
            headers: HTTP headers
            meta: Additional metadata
        """
        error = ErrorResponse(
            detail=message,
            code=code,
            meta=meta or {},
        )
        
        content = BaseResponse[Any](
            success=False,
            error=error,
        )
        
        super().__init__(
            content=jsonable_encoder(content, exclude_none=True),
            status_code=status_code,
            headers=headers,
        )

class NotFoundResponse(ErrorResponse):
    """404 Not Found response."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        code: str = "not_found",
        headers: Optional[Dict[str, str]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a not found response.
        
        Args:
            message: Error message
            code: Error code
            headers: HTTP headers
            meta: Additional metadata
        """
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_404_NOT_FOUND,
            headers=headers,
            meta=meta,
        )

class UnauthorizedResponse(ErrorResponse):
    """401 Unauthorized response."""
    
    def __init__(
        self,
        message: str = "Not authenticated",
        code: str = "unauthorized",
        headers: Optional[Dict[str, str]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize an unauthorized response.
        
        Args:
            message: Error message
            code: Error code
            headers: HTTP headers
            meta: Additional metadata
        """
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers=headers,
            meta=meta,
        )

class ForbiddenResponse(ErrorResponse):
    """403 Forbidden response."""
    
    def __init__(
        self,
        message: str = "Insufficient permissions",
        code: str = "forbidden",
        headers: Optional[Dict[str, str]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a forbidden response.
        
        Args:
            message: Error message
            code: Error code
            headers: HTTP headers
            meta: Additional metadata
        """
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_403_FORBIDDEN,
            headers=headers,
            meta=meta,
        )

class ConflictResponse(ErrorResponse):
    """409 Conflict response."""
    
    def __init__(
        self,
        message: str = "Resource already exists",
        code: str = "conflict",
        headers: Optional[Dict[str, str]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a conflict response.
        
        Args:
            message: Error message
            code: Error code
            headers: HTTP headers
            meta: Additional metadata
        """
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_409_CONFLICT,
            headers=headers,
            meta=meta,
        )

class ValidationErrorResponse(ErrorResponse):
    """422 Unprocessable Entity response for validation errors."""
    
    def __init__(
        self,
        errors: List[Dict[str, Any]],
        message: str = "Validation error",
        code: str = "validation_error",
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize a validation error response.
        
        Args:
            errors: List of validation errors
            message: Error message
            code: Error code
            headers: HTTP headers
        """
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            headers=headers,
            meta={"errors": errors},
        )
