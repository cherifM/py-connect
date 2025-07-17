"""Custom middleware for the FastAPI application."""
import time
import uuid
import logging
from typing import Callable, Awaitable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and adding request ID to each request."""
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request
        start_time = time.time()
        
        # Log request details
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client": f"{request.client.host}:{request.client.port}" if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            },
        )
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate request duration
            process_time = (time.time() - start_time) * 1000
            process_time = round(process_time, 2)
            
            # Log response
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration_ms": process_time,
                },
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time}ms"
            
            return response
            
        except Exception as e:
            # Log any exceptions that occur during request processing
            process_time = (time.time() - start_time) * 1000
            process_time = round(process_time, 2)
            
            logger.error(
                "Request failed",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "duration_ms": process_time,
                    "error": str(e),
                    "error_type": e.__class__.__name__,
                },
            )
            raise


class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive information from logs."""
    
    SENSITIVE_KEYS = {
        'password', 'token', 'secret', 'api_key', 'apikey', 'authorization',
        'access_token', 'refresh_token', 'credit_card', 'ssn', 'social_security',
        'auth', 'credentials', 'pwd', 'passwd', 'pass', 'pword', 'passphrase',
        'private_key', 'privatekey', 'secret_key', 'secretkey'
    }
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records to redact sensitive information."""
        # Redact sensitive data in record attributes
        for attr, value in record.__dict__.items():
            if isinstance(value, dict):
                record.__dict__[attr] = self._redact_dict(value)
            elif isinstance(value, str) and any(key in attr.lower() for key in self.SENSITIVE_KEYS):
                record.__dict__[attr] = "[REDACTED]"
        
        # Also redact in the message
        if hasattr(record, 'msg') and isinstance(record.msg, dict):
            record.msg = self._redact_dict(record.msg)
            
        return True
    
    def _redact_dict(self, data: dict) -> dict:
        """Recursively redact sensitive keys in a dictionary."""
        result = {}
        for key, value in data.items():
            if isinstance(value, dict):
                result[key] = self._redact_dict(value)
            elif isinstance(value, str) and any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                result[key] = "[REDACTED]"
            else:
                result[key] = value
        return result


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Middleware for audit logging of sensitive operations."""
    
    AUDIT_LOGGER = logging.getLogger("audit")
    
    def __init__(
        self,
        app: ASGIApp,
        sensitive_paths: list[str] = None,
        sensitive_methods: list[str] = None,
    ) -> None:
        super().__init__(app)
        self.sensitive_paths = set(sensitive_paths or [
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/change-password",
            "/api/users",
        ])
        self.sensitive_methods = set(sensitive_methods or ["POST", "PUT", "PATCH", "DELETE"])
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip if not a sensitive operation
        if not self._is_sensitive_operation(request):
            return await call_next(request)
        
        # Get user info if available
        user_info = {
            "user_id": getattr(request.state, "user_id", None),
            "username": getattr(request.state, "username", None),
            "ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
        
        # Log the operation start
        self.AUDIT_LOGGER.info(
            "Sensitive operation started",
            extra={
                "operation": f"{request.method} {request.url.path}",
                "stage": "start",
                **user_info,
            },
        )
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Log the operation completion
            self.AUDIT_LOGGER.info(
                "Sensitive operation completed",
                extra={
                    "operation": f"{request.method} {request.url.path}",
                    "stage": "complete",
                    "status_code": response.status_code,
                    **user_info,
                },
            )
            
            return response
            
        except Exception as e:
            # Log the operation failure
            self.AUDIT_LOGGER.error(
                "Sensitive operation failed",
                exc_info=True,
                extra={
                    "operation": f"{request.method} {request.url.path}",
                    "stage": "error",
                    "error": str(e),
                    "error_type": e.__class__.__name__,
                    **user_info,
                },
            )
            raise
    
    def _is_sensitive_operation(self, request: Request) -> bool:
        """Check if the request is for a sensitive operation."""
        # Check if the path contains any sensitive segments
        path_sensitive = any(
            sensitive_path in request.url.path
            for sensitive_path in self.sensitive_paths
        )
        
        # Check if the method is in the sensitive methods
        method_sensitive = request.method in self.sensitive_methods
        
        return path_sensitive or method_sensitive
