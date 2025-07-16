"""
Py-Connect Backend Application

This package contains the FastAPI application and its components.
"""

from .database import Base, init_db, get_db
from . import schemas, crud, services, database
from .models import Content, Base
from .schemas import ContentBase, ContentCreate, ContentUpdate, ContentInDB, ContentInDBBase, Content

# Re-export for easier imports
__all__ = [
    'Content',
    'ContentBase',
    'ContentCreate',
    'ContentUpdate',
    'ContentInDB',
    'ContentInDBBase',
    'init_db',
    'get_db',
    'get_content',
    'get_content_by_name',
    'get_all_content',
    'create_content',
    'update_content_status',
    'delete_content',
    'services',
    "Content",  # For backward compatibility
    "Base", 
    "schemas", 
    "crud", 
    "services", 
    "database"
]

# Import models to ensure they're registered with SQLAlchemy
from . import models  # noqa