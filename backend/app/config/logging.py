import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any

from app.config.settings import settings

# Ensure log directory exists
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Logging configuration
LOGGING_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": settings.LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": settings.LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "stream": sys.stdout,
        },
        "file": {
            "level": settings.LOG_LEVEL,
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "app.log",
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "formatter": "standard",
            "encoding": "utf8",
        },
        "json_file": {
            "level": settings.LOG_LEVEL,
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "app.json.log",
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "formatter": "json",
            "encoding": "utf8",
        },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["console", "file", "json_file"],
            "level": settings.LOG_LEVEL,
            "propagate": False,
        },
        "app": {
            "handlers": ["console", "file", "json_file"],
            "level": settings.LOG_LEVEL,
            "propagate": False,
        },
        "sqlalchemy.engine": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

def setup_logging() -> None:
    """Configure logging for the application."""
    logging.config.dictConfig(LOGGING_CONFIG)

# Configure logging when module is imported
setup_logging()

# Create logger for this module
logger = logging.getLogger(__name__)
logger.info("Logging configured")
