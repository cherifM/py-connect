"""Custom exception handlers for the FastAPI application."""
import logging
import traceback
from typing import Any, Callable, Dict, Optional, Type, Union

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.schemas import ErrorResponse

logger = logging.getLogger(__name__)

class AppError(Exception):
    """Base exception class for application errors."""
    
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        message: str = "An unexpected error occurred",
        error_type: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.message = message
        self.error_type = error_type or self.__class__.__name__
        self.error_details = error_details or {}
        super().__init__(message)


class ValidationError(AppError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str = "Validation error", error_details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_type="ValidationError",
            error_details=error_details or {}
        )


class AuthenticationError(AppError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_type="AuthenticationError"
        )


class AuthorizationError(AppError):
    """Raised when a user is not authorized to perform an action."""
    
    def __init__(self, message: str = "Not authorized to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_type="AuthorizationError"
        )


class NotFoundError(AppError):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource: str = "resource", id: Optional[Union[str, int]] = None):
        message = f"{resource.capitalize()} not found"
        if id is not None:
            message += f" with id {id}"
        
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_type="NotFoundError"
        )


class ConflictError(AppError):
    """Raised when a resource conflict occurs."""
    
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            error_type="ConflictError"
        )


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup global exception handlers for the FastAPI application."""
    
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """Handle custom application errors."""
        logger.warning(
            "Application error",
            extra={
                "status_code": exc.status_code,
                "error_type": exc.error_type,
                "error_details": exc.error_details,
                "path": request.url.path,
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                success=False,
                error={
                    "type": exc.error_type,
                    "message": exc.message,
                    "details": exc.error_details
                }
            ).dict()
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle request validation errors."""
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"][1:])  # Skip 'body' in loc
            errors.append({
                "field": field or "request body",
                "message": error["msg"],
                "type": error["type"]
            })
        
        logger.warning(
            "Request validation error",
            extra={
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "error_type": "ValidationError",
                "validation_errors": errors,
                "path": request.url.path,
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                success=False,
                error={
                    "type": "ValidationError",
                    "message": "Invalid request data",
                    "details": {"fields": errors}
                }
            ).dict()
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions."""
        logger.warning(
            "HTTP exception",
            extra={
                "status_code": exc.status_code,
                "error_type": exc.__class__.__name__,
                "detail": exc.detail,
                "path": request.url.path,
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                success=False,
                error={
                    "type": exc.__class__.__name__,
                    "message": str(exc.detail),
                    "details": {}
                }
            ).dict()
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle all other exceptions."""
        error_id = f"err_{request.state.request_id}" if hasattr(request.state, 'request_id') else "unknown"
        
        logger.error(
            f"Unhandled exception: {str(exc)}",
            exc_info=True,
            extra={
                "error_id": error_id,
                "path": request.url.path,
                "method": request.method,
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error={
                    "type": "InternalServerError",
                    "message": "An unexpected error occurred",
                    "details": {
                        "error_id": error_id,
                        "message": "Please contact support with the error ID for assistance."
                    }
                }
            ).dict()
        )


def handle_async_exceptions(async_func: Callable):
    ""
    Decorator to handle exceptions in async functions.
    
    Example:
        @handle_async_exceptions
        async def my_async_function():
            # Your async code here
            pass
    """
    async def wrapper(*args, **kwargs):
        try:
            return await async_func(*args, **kwargs)
        except AppError as e:
            # Re-raise custom exceptions
            raise e
        except Exception as e:
            # Log and convert other exceptions to AppError
            logger.exception(f"Error in {async_func.__name__}")
            raise AppError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An unexpected error occurred",
                error_type=e.__class__.__name__,
                error_details={"details": str(e)}
            )
    
    # Preserve the original function's name and docstring
    wrapper.__name__ = async_func.__name__
    wrapper.__doc__ = async_func.__doc__
    return wrapper
