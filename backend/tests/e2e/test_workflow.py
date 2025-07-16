import pytest
import tempfile
import os
import time
from fastapi import status

# This is an end-to-end test that verifies the complete workflow
# from content creation to deployment and cleanup

@pytest.mark.e2e
def test_complete_workflow(client, db_session):
    """Test the complete workflow from content creation to deployment"""
    # Skip if Docker is not available
    try:
        import docker
        docker_client = docker.from_env()
        docker_client.ping()
    except Exception as e:
        pytest.skip(f"Docker is not available: {e}")
    
    # Create a simple zip file for testing
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
        # Create a simple Dockerfile in the zip
        import zipfile
        with zipfile.ZipFile(tmp_file, 'w') as zipf:
            zipf.writestr('Dockerfile', 'FROM nginx:alpine\nCOPY . /usr/share/nginx/html\n')
            zipf.writestr('index.html', '<html><body>Test App</body></html>')
        tmp_file_path = tmp_file.name
    
    try:
        # Step 1: Publish content
        with open(tmp_file_path, "rb") as f:
            response = client.post(
                "/api/publish",
                data={"name": "e2e_test_app", "description": "End-to-end test app"},
                files={"app_bundle": ("test_app.zip", f, "application/zip")}
            )
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        content_id = response_data["content_id"]
        
        # Step 2: Verify content was created
        response = client.get(f"/api/content/{content_id}")
        assert response.status_code == status.HTTP_200_OK
        content = response.json()
        assert content["name"] == "e2e_test_app"
        
        # Give some time for the background task to complete
        max_attempts = 10
        for _ in range(max_attempts):
            response = client.get(f"/api/content/{content_id}")
            content = response.json()
            if content.get("status") == "running":
                break
            time.sleep(1)
        
        # Step 3: Verify the container is running
        assert content["status"] == "running"
        assert content["container_id"] is not None
        
        # Verify the container exists
        container = docker_client.containers.get(content["container_id"])
        assert container.status == "running"
        
        # Step 4: Clean up
        response = client.delete(f"/api/content/{content_id}")
        assert response.status_code == status.HTTP_200_OK
        
        # Verify container is removed
        with pytest.raises(docker.errors.NotFound):
            docker_client.containers.get(content["container_id"])
        
        # Verify content is deleted
        response = client.get(f"/api/content/{content_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    finally:
        # Clean up test file
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
