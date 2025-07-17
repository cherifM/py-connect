"""Logging configuration for the application."""
import logging
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging.config

from pydantic import BaseModel, Field

class LogConfig(BaseModel):
    """Logging configuration to be set for the app."""
    
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[Path] = None
    
    # Logging config
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: Dict[str, Dict[str, str]] = {
        "json": {
            "()": "app.core.logging_config.JsonFormatter",
            "fmt": "%(message)s"
        },
        "console": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }
    handlers: Dict[str, Dict[str, Any]] = {
        "console": {
            "class": "logging.StreamHandler",
            "level": LOG_LEVEL,
            "formatter": "console",
            "stream": sys.stdout
        }
    }
    loggers: Dict[str, Dict[str, Any]] = {
        "app": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False
        },
        "uvicorn": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False
        },
        "sqlalchemy": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False
        },
        "aiosqlite": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False
        }
    }
    root: Dict[str, Any] = {
        "handlers": ["console"],
        "level": LOG_LEVEL
    }
    
    def __init__(self, **data):
        super().__init__(**data)
        self._configure_handlers()
    
    def _configure_handlers(self):
        """Configure file handler if LOG_FILE is set."""
        if self.LOG_FILE:
            self.handlers["file"] = {
                "class": "logging.handlers.RotatingFileHandler",
                "level": self.LOG_LEVEL,
                "formatter": "json",
                "filename": str(self.LOG_FILE),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            }
            
            # Add file handler to all loggers
            for logger in self.loggers.values():
                if "handlers" in logger:
                    logger["handlers"].append("file")
            
            if "handlers" in self.root:
                self.root["handlers"].append("file")


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread,
            "thread_name": record.threadName,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        # Add any extra attributes
        if hasattr(record, 'props') and isinstance(record.props, dict):
            log_record.update(record.props)
        
        return json.dumps(log_record, ensure_ascii=False)


def configure_logging(log_file: Optional[Path] = None, log_level: str = "INFO") -> None:
    """Configure logging for the application.
    
    Args:
        log_file: Optional path to log file. If None, logs only to console.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    config = LogConfig(
        LOG_LEVEL=log_level,
        LOG_FILE=log_file
    )
    
    logging.config.dictConfig(config.dict())
    
    # Set log level for all loggers
    for logger_name in config.loggers:
        logging.getLogger(logger_name).setLevel(log_level)
    
    # Set log level for root logger
    logging.getLogger().setLevel(log_level)
    
    # Configure uvicorn loggers
    logging.getLogger("uvicorn").handlers = []
    logging.getLogger("uvicorn.access").handlers = []
    
    # Configure SQLAlchemy loggers
    logging.getLogger("sqlalchemy.engine").setLevel("WARNING")
    logging.getLogger("sqlalchemy.pool").setLevel("WARNING")
    
    # Configure aiosqlite loggers
    logging.getLogger("aiosqlite").setLevel("WARNING")
