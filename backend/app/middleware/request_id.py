import uuid
from typing import Callable, Awaitable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add a unique request ID to each request.
    
    This helps with tracing requests across services and in logs.
    """
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Add a unique request ID to the request and response.
        
        Args:
            request: The incoming request
            call_next: Function to process the request
            
        Returns:
            Response: The response with the X-Request-ID header
        """
        # Get request ID from header or generate a new one
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Process the request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
