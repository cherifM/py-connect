import pytest
import tempfile
import os
import zipfile
from datetime import datetime
from fastapi import status
from app import schemas, models

def test_create_content(client, tmp_path):
    """Test creating content via API endpoint"""
    # Create a temporary directory for our test app
    app_dir = tmp_path / "test_app"
    app_dir.mkdir()
    
    # Create a simple Dockerfile
    dockerfile = app_dir / "Dockerfile"
    dockerfile.write_text("""
    FROM python:3.9-slim
    WORKDIR /app
    COPY . .
    CMD ["python", "-m", "http.server", "80"]
    """)
    
    # Create a ZIP file with the Dockerfile
    zip_path = tmp_path / "test_app.zip"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.write(dockerfile, arcname="Dockerfile")
    
    # Prepare test data
    data = {
        "name": "test_app",
        "description": "A test app"
    }
    
    # Make the request
    with open(zip_path, "rb") as f:
        files = {"app_bundle": ("test_app.zip", f, "application/zip")}
        response = client.post("/api/publish", data=data, files=files)
    
    # Assertions
    assert response.status_code == status.HTTP_202_ACCEPTED
    response_data = response.json()
    assert "id" in response_data
    assert "name" in response_data
    assert response_data["name"] == "test_app"

def test_get_content(client, db_session):
    """Test retrieving content via API endpoint"""
    # First create a content item directly in the database
    content = models.Content(
        name="test_app",
        description="A test app",
        image_name="test_app:latest",
        status="running",
        created_at=datetime.utcnow()
    )
    db_session.add(content)
    db_session.commit()
    db_session.refresh(content)
    
    # Now retrieve it via the API
    response = client.get(f"/api/content/{content.id}")
    
    # Assertions
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == content.id
    assert response_data["name"] == "test_app"

def test_list_content(client, db_session):
    """Test listing all content via API endpoint"""
    # First create some test data
    for i in range(3):
        content = models.Content(
            name=f"test_app_{i}",
            description=f"Test app {i}",
            image_name=f"test_app_{i}:latest",
            status="running",
            created_at=datetime.utcnow()
        )
        db_session.add(content)
    db_session.commit()
    
    # Now retrieve the list via the API
    response = client.get("/api/content")
    
    # Assertions
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data) >= 3  # Should have at least the 3 we just created
