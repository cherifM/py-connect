import time
import logging
from typing import Callable, Awaitable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    """
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Log request and response information.
        
        Args:
            request: The incoming request
            call_next: Function to process the request
            
        Returns:
            Response: The response to send back to the client
        """
        # Log request details
        request_id = request.headers.get("x-request-id", "")
        client_host = request.client.host if request.client else "unknown"
        
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {client_host} "
            f"[ID: {request_id}]"
        )
        
        # Log request headers (sensitive headers are redacted)
        sensitive_headers = {"authorization", "cookie", "set-cookie", "x-api-key"}
        headers = {
            k: ("[REDACTED]" if k.lower() in sensitive_headers else v)
            for k, v in request.headers.items()
        }
        logger.debug(f"Request headers: {headers}")
        
        # Process the request and measure response time
        start_time = time.time()
        
        try:
            response = await call_next(request)
        except Exception as e:
            # Log unhandled exceptions
            logger.error(
                f"Unhandled exception: {str(e)}",
                exc_info=True,
                extra={"request_id": request_id}
            )
            raise
        
        # Calculate response time
        process_time = (time.time() - start_time) * 1000
        process_time = round(process_time, 2)
        
        # Log response details
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"{response.status_code} in {process_time}ms "
            f"[ID: {request_id}]"
        )
        
        # Add response headers
        response.headers["X-Process-Time"] = str(process_time)
        if request_id:
            response.headers["X-Request-ID"] = request_id
        
        return response
