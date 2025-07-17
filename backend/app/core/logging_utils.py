"""Utility functions for logging and error handling."""
import logging
import functools
import inspect
import json
import traceback
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

from pydantic import BaseModel

from app.core.exception_handlers import AppError

logger = logging.getLogger(__name__)

T = TypeVar('T')

class LogContext:
    """Context manager for adding context to log messages."""
    
    def __init__(self, logger: logging.Logger, **context):
        """Initialize with logger and context."""
        self.logger = logger
        self.context = context
        self.old_context = {}
    
    def __enter__(self):
        """Add context to the logger."""
        # Save old context
        for key in self.context:
            if hasattr(self.logger, key):
                self.old_context[key] = getattr(self.logger, key, None)
            
            # Set new context
            setattr(self.logger, key, self.context[key])
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore old context."""
        # Restore old context
        for key, value in self.old_context.items():
            if value is not None:
                setattr(self.logger, key, value)
            else:
                try:
                    delattr(self.logger, key)
                except AttributeError:
                    pass
        
        # Clear old context
        self.old_context = {}


def log_execution(
    log_args: bool = True,
    log_result: bool = True,
    log_errors: bool = True,
    level: str = "debug",
    logger: Optional[logging.Logger] = None
):
    """Decorator to log function execution details.
    
    Args:
        log_args: Whether to log function arguments
        log_result: Whether to log function result
        log_errors: Whether to log errors
        level: Logging level (debug, info, warning, error, critical)
        logger: Logger to use (defaults to module logger)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        """Decorator implementation."""
        if logger is None:
            func_logger = logging.getLogger(func.__module__)
        else:
            func_logger = logger
        
        log_func = getattr(func_logger, level.lower())
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            """Wrapper function."""
            # Log function entry
            func_args = []
            
            if log_args:
                # Get parameter names and values
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                
                # Format arguments for logging
                for name, value in bound_args.arguments.items():
                    # Skip self parameter for instance methods
                    if name == 'self':
                        continue
                    
                    # Handle sensitive data
                    if any(sensitive in name.lower() for sensitive in ['password', 'token', 'secret']):
                        value = '***REDACTED***'
                    
                    func_args.append(f"{name}={value!r}")
            
            # Log function call
            func_args_str = ", ".join(func_args)
            log_func(f"Calling {func.__name__}({func_args_str})")
            
            # Call the function
            start_time = datetime.utcnow()
            try:
                result = func(*args, **kwargs)
                
                # Log function result
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                if log_result:
                    result_repr = (
                        '***REDACTED***' 
                        if any(sensitive in func.__name__.lower() 
                              for sensitive in ['password', 'token', 'secret'])
                        else repr(result)
                    )
                    log_func(
                        f"Function {func.__name__} returned {result_repr} "
                        f"(took {duration:.4f}s)"
                    )
                else:
                    log_func(
                        f"Function {func.__name__} completed successfully "
                        f"(took {duration:.4f}s)"
                    )
                
                return result
                
            except Exception as e:
                if log_errors:
                    # Log the error with traceback
                    func_logger.error(
                        f"Error in {func.__name__}: {str(e)}\n"
                        f"{traceback.format_exc()}",
                        extra={
                            "function": func.__name__,
                            "error": str(e),
                            "error_type": e.__class__.__name__,
                            "args": args if log_args else None,
                            "kwargs": kwargs if log_args else None,
                        }
                    )
                
                # Re-raise the exception
                raise
        
        return wrapper
    
    return decorator


def log_async_execution(
    log_args: bool = True,
    log_result: bool = True,
    log_errors: bool = True,
    level: str = "debug",
    logger: Optional[logging.Logger] = None
):
    """Decorator to log async function execution details."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        """Decorator implementation for async functions."""
        if logger is None:
            func_logger = logging.getLogger(func.__module__)
        else:
            func_logger = logger
        
        log_func = getattr(func_logger, level.lower())
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            """Async wrapper function."""
            # Log function entry
            func_args = []
            
            if log_args:
                # Get parameter names and values
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                
                # Format arguments for logging
                for name, value in bound_args.arguments.items():
                    # Skip self parameter for instance methods
                    if name == 'self':
                        continue
                    
                    # Handle sensitive data
                    if any(sensitive in name.lower() for sensitive in ['password', 'token', 'secret']):
                        value = '***REDACTED***'
                    
                    func_args.append(f"{name}={value!r}")
            
            # Log function call
            func_args_str = ", ".join(func_args)
            log_func(f"Calling async {func.__name__}({func_args_str})")
            
            # Call the async function
            start_time = datetime.utcnow()
            try:
                result = await func(*args, **kwargs)
                
                # Log function result
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                if log_result:
                    result_repr = (
                        '***REDACTED***' 
                        if any(sensitive in func.__name__.lower() 
                              for sensitive in ['password', 'token', 'secret'])
                        else repr(result)
                    )
                    log_func(
                        f"Async function {func.__name__} returned {result_repr} "
                        f"(took {duration:.4f}s)"
                    )
                else:
                    log_func(
                        f"Async function {func.__name__} completed successfully "
                        f"(took {duration:.4f}s)"
                    )
                
                return result
                
            except Exception as e:
                if log_errors:
                    # Log the error with traceback
                    func_logger.error(
                        f"Error in async {func.__name__}: {str(e)}\n"
                        f"{traceback.format_exc()}",
                        extra={
                            "function": func.__name__,
                            "error": str(e),
                            "error_type": e.__class__.__name__,
                            "args": args if log_args else None,
                            "kwargs": kwargs if log_args else None,
                        }
                    )
                
                # Re-raise the exception
                raise
        
        return wrapper
    
    return decorator


def log_deprecated(
    logger: Optional[logging.Logger] = None,
    message: Optional[str] = None,
    version: Optional[str] = None,
    alternative: Optional[str] = None
):
    """Decorator to mark functions as deprecated.
    
    Args:
        logger: Logger to use for deprecation warning
        message: Custom deprecation message
        version: Version in which the function was deprecated
        alternative: Suggested alternative to use instead
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        """Decorator implementation."""
        nonlocal message
        
        if message is None:
            message = f"Function {func.__name__} is deprecated"
            if version:
                message += f" since version {version}"
            if alternative:
                message += f". Use {alternative} instead."
        
        if logger is None:
            func_logger = logging.getLogger(func.__module__)
        else:
            func_logger = logger
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            """Wrapper function."""
            func_logger.warning(message)
            return func(*args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            """Async wrapper function."""
            func_logger.warning(message)
            return await func(*args, **kwargs)
        
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator


def log_elapsed_time(
    logger: Optional[logging.Logger] = None,
    level: str = "debug",
    message: str = "Operation completed in {elapsed:.2f} seconds"
):
    """Context manager to log the time taken by a block of code.
    
    Args:
        logger: Logger to use
        level: Logging level (debug, info, warning, error, critical)
        message: Log message with {elapsed} placeholder for the elapsed time
    """
    @contextmanager
    def elapsed_time_logger():
        """Context manager implementation."""
        start_time = datetime.utcnow()
        try:
            yield
        finally:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if logger is not None:
                log_func = getattr(logger, level.lower(), logger.debug)
                log_func(message.format(elapsed=elapsed))
    
    return elapsed_time_logger()


def log_exception(
    logger: Optional[logging.Logger] = None,
    level: str = "error",
    message: str = "An error occurred",
    reraise: bool = True,
    exception_types: tuple = (Exception,)
):
    """Decorator to log exceptions with configurable behavior.
    
    Args:
        logger: Logger to use
        level: Logging level (debug, info, warning, error, critical)
        message: Log message
        reraise: Whether to re-raise the exception after logging
        exception_types: Tuple of exception types to catch
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        """Decorator implementation."""
        if logger is None:
            func_logger = logging.getLogger(func.__module__)
        else:
            func_logger = logger
        
        log_func = getattr(func_logger, level.lower())
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            """Wrapper function."""
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                log_func(f"{message}: {str(e)}", exc_info=True)
                if reraise:
                    raise
                raise AppError(
                    status_code=500,
                    message="An unexpected error occurred",
                    error_type=e.__class__.__name__,
                    error_details={"details": str(e)}
                ) from e
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            """Async wrapper function."""
            try:
                return await func(*args, **kwargs)
            except exception_types as e:
                log_func(f"{message}: {str(e)}", exc_info=True)
                if reraise:
                    raise
                raise AppError(
                    status_code=500,
                    message="An unexpected error occurred",
                    error_type=e.__class__.__name__,
                    error_details={"details": str(e)}
                ) from e
        
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator
