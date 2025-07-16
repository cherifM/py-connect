from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional, Dict, Any, Union
import uuid

from . import models, schemas

def get_content_by_name(db: Session, name: str) -> Optional[models.Content]:
    """Get a content item by name."""
    return db.query(models.Content).filter(models.Content.name == name).first()

def get_content(db: Session, content_id: int) -> Optional[models.Content]:
    """Get a content item by ID."""
    return db.query(models.Content).filter(models.Content.id == content_id).first()

def get_all_content(db: Session, skip: int = 0, limit: int = 100) -> List[models.Content]:
    """Get all content items with pagination."""
    return db.query(models.Content).offset(skip).limit(limit).all()

def create_content(db: Session, content: schemas.ContentCreate) -> models.Content:
    """Create a new content item.
    
    Args:
        db: Database session
        content: Content data to create
        
    Returns:
        The created content item
    """
    # Generate a unique image name based on the content name
    image_name = f"pyconnect-{content.name.lower().replace(' ', '-')}:{uuid.uuid4().hex[:8]}"
    
    db_content = models.Content(
        name=content.name,
        description=content.description,
        image_name=image_name,
        status="creating"
    )
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    return db_content

def update_content_status(
    db: Session, 
    content_id: int, 
    status: str, 
    container_id: Optional[str] = None, 
    internal_port: Optional[int] = None
) -> Optional[models.Content]:
    """Update a content item's status and related fields.
    
    Args:
        db: Database session
        content_id: ID of the content to update
        status: New status value
        container_id: Optional container ID
        internal_port: Optional internal port
        
    Returns:
        The updated content item or None if not found
    """
    db_content = db.query(models.Content).filter(models.Content.id == content_id).first()
    if db_content:
        db_content.status = status
        if container_id is not None:
            db_content.container_id = container_id
        if internal_port is not None:
            db_content.internal_port = internal_port
        db_content.updated_at = func.now()
        db.commit()
        db.refresh(db_content)
    return db_content

def delete_content(db: Session, content_id: int) -> Optional[models.Content]:
    """Delete a content item by ID.
    
    Args:
        db: Database session
        content_id: ID of the content to delete
        
    Returns:
        The deleted content item or None if not found
    """
    db_content = db.query(models.Content).filter(models.Content.id == content_id).first()
    if db_content:
        db.delete(db_content)
        db.commit()
    return db_content
