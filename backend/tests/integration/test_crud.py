import pytest
from app import crud, schemas

def test_create_content(db_session):
    """Test creating a content item"""
    # Test data
    content_data = {
        "name": "test_app",
        "description": "A test app",
        "image_name": "test_app:latest"
    }
    
    # Create content
    content = crud.create_content(db_session, schemas.ContentCreate(**content_data))
    
    # Assertions
    assert content.id is not None
    assert content.name == "test_app"
    assert content.description == "A test app"
    assert content.status == "creating"

def test_get_content(db_session):
    """Test retrieving a content item"""
    # First create a content item
    content_data = {
        "name": "test_app",
        "description": "A test app",
        "image_name": "test_app:latest"
    }
    created_content = crud.create_content(db_session, schemas.ContentCreate(**content_data))
    
    # Now retrieve it
    retrieved_content = crud.get_content(db_session, created_content.id)
    
    # Assertions
    assert retrieved_content is not None
    assert retrieved_content.id == created_content.id
    assert retrieved_content.name == "test_app"

def test_update_content_status(db_session):
    """Test updating content status"""
    # First create a content item
    content_data = {
        "name": "test_app",
        "description": "A test app",
        "image_name": "test_app:latest"
    }
    created_content = crud.create_content(db_session, schemas.ContentCreate(**content_data))
    
    # Update status
    updated_content = crud.update_content_status(
        db_session, 
        created_content.id, 
        status="running", 
        container_id="test_container_id", 
        internal_port=8080
    )
    
    # Assertions
    assert updated_content is not None
    assert updated_content.status == "running"
    assert updated_content.container_id == "test_container_id"
    assert updated_content.internal_port == 8080
