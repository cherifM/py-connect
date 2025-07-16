import time
from collections import defaultdict
from typing import Dict, Optional, Tuple, Callable, Awaitable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import RateLimitExceededException
from app.core.security import get_remote_address

class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for FastAPI applications.
    
    This middleware limits the number of requests a client can make within a given time window.
    """
    
    def __init__(
        self,
        app,
        limit: int = 100,
        window: int = 60,
        block_duration: int = 300,
        excluded_paths: Optional[set] = None
    ):
        """
        Initialize the rate limiter middleware.
        
        Args:
            app: The FastAPI application
            limit: Maximum number of requests allowed per window
            window: Time window in seconds
            block_duration: Duration in seconds to block the client after exceeding the limit
            excluded_paths: Set of paths to exclude from rate limiting
        """
        super().__init__(app)
        self.limit = limit
        self.window = window
        self.block_duration = block_duration
        self.excluded_paths = excluded_paths or set()
        
        # Store request counts and block timestamps
        self.request_counts: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, 0.0))
        self.blocked_ips: Dict[str, float] = {}
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Handle incoming requests and apply rate limiting.
        
        Args:
            request: The incoming request
            call_next: Function to process the request
            
        Returns:
            Response: The response to send back to the client
        """
        # Skip rate limiting for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Get client IP address
        client_ip = get_remote_address(request)
        
        # Check if IP is blocked
        current_time = time.time()
        if client_ip in self.blocked_ips:
            if current_time - self.blocked_ips[client_ip] < self.block_duration:
                # Still in block period
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Too many requests. Please try again later.",
                        "code": "rate_limit_exceeded",
                        "retry_after": int(self.blocked_ips[client_ip] + self.block_duration - current_time)
                    },
                    headers={"Retry-After": str(int(self.blocked_ips[client_ip] + self.block_duration - current_time))}
                )
            else:
                # Block period has ended, remove from blocked IPs
                del self.blocked_ips[client_ip]
        
        # Get or initialize request count and window start time
        count, window_start = self.request_counts[client_ip]
        
        # Reset counter if window has passed
        if current_time - window_start > self.window:
            count = 0
            window_start = current_time
        
        # Check if rate limit is exceeded
        if count >= self.limit:
            # Block the IP
            self.blocked_ips[client_ip] = current_time
            
            # Clean up old entries
            self._cleanup_old_entries(current_time)
            
            raise RateLimitExceededException(
                detail="Rate limit exceeded. Please try again later.",
                meta={
                    "limit": self.limit,
                    "window": self.window,
                    "retry_after": self.block_duration
                }
            )
        
        # Increment request count
        count += 1
        self.request_counts[client_ip] = (count, window_start)
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.limit - count))
        response.headers["X-RateLimit-Reset"] = str(int(window_start + self.window))
        
        return response
    
    def _cleanup_old_entries(self, current_time: float) -> None:
        """Clean up old entries from request_counts and blocked_ips."""
        # Clean up request counts
        to_remove = []
        for ip, (_, window_start) in self.request_counts.items():
            if current_time - window_start > self.window * 2:  # Keep some history
                to_remove.append(ip)
        
        for ip in to_remove:
            self.request_counts.pop(ip, None)
        
        # Clean up blocked IPs
        to_unblock = [
            ip for ip, block_time in self.blocked_ips.items()
            if current_time - block_time > self.block_duration
        ]
        
        for ip in to_unblock:
            self.blocked_ips.pop(ip, None)


def get_remote_address(request: Request) -> str:
    """
    Get the client's IP address from the request.
    
    This function checks common headers used by proxies to get the real client IP.
    """
    # Check for common proxy headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, the first one is the client
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to the connection's remote address
    if request.client and request.client.host:
        return request.client.host
    
    # Last resort
    return "unknown"
