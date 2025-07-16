"""
Middleware configuration for the FastAPI application.

This module sets up and configures all middleware used by the application.
"""
from typing import List, Optional

from fastapi import FastAPI

from .cors import CORSMiddleware
from .rate_limiter import RateLimiterMiddleware
from .request_id import RequestIDMiddleware
from .request_logging import RequestLoggingMiddleware
from app.config.settings import settings


def setup_middleware(app: FastAPI) -> None:
    """
    Set up all middleware for the FastAPI application.
    
    Args:
        app: The FastAPI application instance
    """
    # Add request ID middleware first to ensure request ID is available to other middleware
    app.add_middleware(RequestIDMiddleware)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    
    # Add rate limiting middleware
    app.add_middleware(
        RateLimiterMiddleware,
        limit=100,  # requests
        window=60,  # seconds
        block_duration=300,  # seconds
        excluded_paths={"/health", "/docs", "/openapi.json", "/redoc"},
    )
    
    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # Note: The order of middleware is important. The first middleware added is the last to run.
    # The execution order is:
    # 1. RequestIDMiddleware (last added, first to process the request)
    # 2. CORSMiddleware
    # 3. RateLimiterMiddleware
    # 4. RequestLoggingMiddleware (first added, last to process the request)
