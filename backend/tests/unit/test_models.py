import pytest
from sqlalchemy.orm import Session
from datetime import datetime
from app import schemas, models

def test_content_model(db_session: Session):
    """Test Content model creation and default values"""
    # Create test data using the ContentCreate schema
    content_data = {
        "name": "test_app",
        "description": "A test app"
    }
    
    # Create schema instance
    content_create = schemas.ContentCreate(**content_data)
    
    # Create DB model instance
    db_content = models.Content(
        **content_create.model_dump(),
        image_name="test_app:latest",
        status="creating"
    )
    
    # Add to session and commit
    db_session.add(db_content)
    db_session.commit()
    db_session.refresh(db_content)
    
    # Assertions
    assert db_content.id is not None
    assert db_content.name == "test_app"
    assert db_content.description == "A test app"
    assert db_content.image_name == "test_app:latest"
    assert db_content.status == "creating"
    assert db_content.container_id is None
    assert db_content.internal_port is None
    assert db_content.created_at is not None
    assert isinstance(db_content.created_at, datetime)
    
    # Test updating the model
    db_content.status = "running"
    db_content.container_id = "test_container_id"
    db_content.internal_port = 8000
    db_session.commit()
    db_session.refresh(db_content)
    
    assert db_content.status == "running"
    assert db_content.container_id == "test_container_id"
    assert db_content.internal_port == 8000
