import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from typing import Any, Callable, Coroutine, TypeVar, Union, cast

from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel

from app.core.exceptions import ServiceUnavailableException

logger = logging.getLogger(__name__)

# Type variables for type hints
T = TypeVar("T")
P = TypeVar("P")
R = TypeVar("R")

class TaskResult(BaseModel):
    """Result of a background task."""
    success: bool
    result: Any = None
    error: str = None

def run_in_threadpool(
    func: Callable[P, R],
) -> Callable[P, Coroutine[Any, Any, R]]:
    """
    Run a synchronous function in a thread pool.
    
    Args:
        func: The synchronous function to run in a thread pool
        
    Returns:
        An awaitable coroutine that will run the function in a thread pool
    """
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        loop = asyncio.get_event_loop()
        func_call = partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, func_call)
    return wrapper

class BackgroundTaskRunner:
    """
    A class to manage and run background tasks.
    
    This class provides a way to run functions in the background and track their status.
    """
    
    def __init__(self, app: FastAPI):
        """Initialize the background task runner."""
        self.app = app
        self.tasks: dict[str, asyncio.Task] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Register startup and shutdown events
        self.app.add_event_handler("startup", self.startup_event)
        self.app.add_event_handler("shutdown", self.shutdown_event)
    
    async def startup_event(self) -> None:
        """Initialize resources when the application starts."""
        logger.info("Background task runner started")
    
    async def shutdown_event(self) -> None:
        """Clean up resources when the application shuts down."""
        # Cancel all running tasks
        for task_id, task in self.tasks.items():
            if not task.done():
                task.cancel()
                logger.info(f"Cancelled background task: {task_id}")
        
        # Shutdown the thread pool executor
        self.executor.shutdown(wait=False)
        logger.info("Background task runner stopped")
    
    def run_task(
        self,
        task_id: str,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """
        Run a function as a background task.
        
        Args:
            task_id: A unique identifier for the task
            func: The function to run
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            str: The task ID
            
        Raises:
            ValueError: If a task with the same ID already exists
        """
        if task_id in self.tasks and not self.tasks[task_id].done():
            raise ValueError(f"Task with ID {task_id} already exists")
        
        async def wrapper() -> T:
            try:
                # Run the function in a thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.executor,
                    partial(func, *args, **kwargs)
                )
                return result
            except asyncio.CancelledError:
                logger.info(f"Task {task_id} was cancelled")
                raise
            except Exception as e:
                logger.error(f"Task {task_id} failed: {e}", exc_info=True)
                raise
            finally:
                # Clean up the task when it's done
                if task_id in self.tasks:
                    del self.tasks[task_id]
        
        # Create and store the task
        task = asyncio.create_task(wrapper())
        self.tasks[task_id] = task
        
        return task_id
    
    async def get_task_result(self, task_id: str) -> TaskResult:
        """
        Get the result of a background task.
        
        Args:
            task_id: The ID of the task
            
        Returns:
            TaskResult: The result of the task
            
        Raises:
            KeyError: If no task with the given ID exists
        """
        if task_id not in self.tasks:
            raise KeyError(f"No task with ID {task_id}")
        
        task = self.tasks[task_id]
        
        if task.done():
            try:
                result = task.result()
                return TaskResult(success=True, result=result)
            except Exception as e:
                return TaskResult(success=False, error=str(e))
        else:
            raise ValueError(f"Task {task_id} is still running")
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.
        
        Args:
            task_id: The ID of the task to cancel
            
        Returns:
            bool: True if the task was cancelled, False otherwise
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if not task.done():
                task.cancel()
                return True
        return False
    
    def get_task_status(self, task_id: str) -> dict:
        """
        Get the status of a task.
        
        Args:
            task_id: The ID of the task
            
        Returns:
            dict: A dictionary containing the task status
            
        Raises:
            KeyError: If no task with the given ID exists
        """
        if task_id not in self.tasks:
            raise KeyError(f"No task with ID {task_id}")
        
        task = self.tasks[task_id]
        
        return {
            "task_id": task_id,
            "done": task.done(),
            "cancelled": task.cancelled(),
            "running": not task.done() and not task.cancelled(),
            "exception": str(task.exception()) if task.exception() else None,
        }

def create_background_tasks(app: FastAPI) -> BackgroundTaskRunner:
    """
    Create and configure a background task runner for the application.
    
    Args:
        app: The FastAPI application
        
    Returns:
        BackgroundTaskRunner: The configured task runner
    """
    # Create a task runner instance
    task_runner = BackgroundTaskRunner(app)
    
    # Store the task runner in the app state
    app.state.task_runner = task_runner
    
    # Add a health check endpoint
    @app.get("/health/tasks")
    async def get_task_runner_status() -> dict:
        """Get the status of the background task runner."""
        task_runner = cast(BackgroundTaskRunner, app.state.task_runner)
        return {
            "status": "ok",
            "task_count": len(task_runner.tasks),
            "executor": {
                "max_workers": task_runner.executor._max_workers,
                "active_threads": task_runner.executor._work_queue.qsize(),
            },
        }
    
    return task_runner
