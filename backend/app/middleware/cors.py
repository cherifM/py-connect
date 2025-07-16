from typing import List, Optional, Callable, Awaitable

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class CORSMiddleware(FastAPICORSMiddleware):
    """
    Extended CORS middleware with additional security headers.
    """
    
    def __init__(
        self,
        app,
        allow_origins: List[str] = None,
        allow_origin_regex: str = None,
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
        allow_credentials: bool = False,
        allow_private_network: bool = False,
        expose_headers: List[str] = None,
        max_age: int = 600,
    ):
        """
        Initialize the CORS middleware.
        
        Args:
            app: The FastAPI application
            allow_origins: List of allowed origins (e.g., ["https://example.com"])
            allow_origin_regex: Regex pattern for allowed origins
            allow_methods: List of allowed HTTP methods
            allow_headers: List of allowed HTTP headers
            allow_credentials: Whether to allow credentials
            allow_private_network: Whether to allow private network access
            expose_headers: List of headers to expose to the browser
            max_age: Maximum age for CORS preflight requests
        """
        if allow_origins is None:
            allow_origins = []
        
        if allow_methods is None:
            allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
        
        if allow_headers is None:
            allow_headers = ["*"]
        
        if expose_headers is None:
            expose_headers = ["X-Request-ID"]
        
        super().__init__(
            app=app,
            allow_origins=allow_origins,
            allow_origin_regex=allow_origin_regex,
            allow_methods=allow_methods,
            allow_headers=allow_headers,
            allow_credentials=allow_credentials,
            expose_headers=expose_headers,
            max_age=max_age,
        )
        
        self.allow_private_network = allow_private_network
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and add CORS headers.
        """
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = await super().dispatch(request, call_next)
        else:
            response = await call_next(request)
        
        # Add security headers
        self._add_security_headers(response)
        
        # Handle private network access
        if self.allow_private_network:
            self._handle_private_network(request, response)
        
        return response
    
    def _add_security_headers(self, response: Response) -> None:
        """Add security-related headers to the response."""
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "base-uri 'self'; "
            "object-src 'none'"
        )
        response.headers["Content-Security-Policy"] = csp
    
    def _handle_private_network(self, request: Request, response: Response) -> None:
        """Handle private network access headers."""
        if request.method == "OPTIONS" and "Access-Control-Request-Private-Network" in request.headers:
            response.headers["Access-Control-Allow-Private-Network"] = "true"
