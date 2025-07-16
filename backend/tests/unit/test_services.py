import pytest
import zipfile
import tempfile
import shutil
from unittest.mock import Mock, patch, ANY, MagicMock
from pathlib import Path
import docker
from app import services, schemas

def create_test_zip(tmp_path):
    """Helper function to create a test zip file with a simple Dockerfile"""
    zip_path = tmp_path / "test_app.zip"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        # Create a simple Dockerfile
        dockerfile = temp_dir / "Dockerfile"
        dockerfile.write_text("""
        FROM python:3.9-slim
        WORKDIR /app
        COPY . .
        CMD ["python", "-m", "http.server", "8000"]
        """)
        
        # Create a simple app file
        app_file = temp_dir / "app.py"
        app_file.write_text("print('Hello, World!')")
        
        # Create the zip file
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in temp_dir.glob('*'):
                zipf.write(file, file.name)
    
    return zip_path

def test_build_and_run_app(tmp_path):
    """Test building and running a Docker container with the service"""
    # Create a test zip file
    zip_path = create_test_zip(tmp_path)
    
    # Create a mock content item
    content_item = MagicMock()
    content_item.image_name = "test_app:latest"
    
    # Mock Docker client and its methods
    mock_client = MagicMock()
    mock_client.images.build.return_value = (MagicMock(id="test_image_id"), [])
    
    # Mock container object with ports attribute
    mock_container = MagicMock()
    mock_container.id = "test_container_id"
    mock_container.ports = {"8000/tcp": [{"HostPort": "32768"}]}
    mock_client.containers.run.return_value = mock_container
    
    # Patch the docker.from_env() call
    with patch('docker.from_env', return_value=mock_client):
        # Call the function
        container_id, port = services.build_and_run_app(content_item, zip_path)
        
        # Assertions
        assert container_id == "test_container_id"
        assert isinstance(port, int)
        
        # Verify Docker API calls
        mock_client.images.build.assert_called_once()
        build_args = mock_client.images.build.call_args[1]
        assert build_args['tag'] == "test_app:latest"
        assert build_args['rm'] is True
        assert build_args['pull'] is True
        
        mock_client.containers.run.assert_called_once()
        run_args = mock_client.containers.run.call_args[1]
        assert run_args['image'] == "test_app:latest"
        assert run_args['detach'] is True
        assert '80/tcp' in run_args['ports']
        assert isinstance(run_args['ports']['80/tcp'], int)

def test_stop_and_remove_container():
    """Test stopping and removing a Docker container"""
    # Setup mock container
    mock_container = MagicMock()
    mock_client = MagicMock()
    mock_client.containers.get.return_value = mock_container
    
    # Test successful container stop and remove
    with patch('docker.from_env', return_value=mock_client):
        services.stop_and_remove_container("test_container_id")
        
        # Assertions
        mock_client.containers.get.assert_called_once_with("test_container_id")
        mock_container.stop.assert_called_once()
        mock_container.remove.assert_called_once()
    
    # Test container not found
    mock_client.reset_mock()
    mock_container.reset_mock()
    mock_client.containers.get.side_effect = docker.errors.NotFound("Container not found")
    
    with patch('docker.from_env', return_value=mock_client):
        # Should not raise an exception
        services.stop_and_remove_container("nonexistent_container")
        
        # Assertions
        mock_client.containers.get.assert_called_once_with("nonexistent_container")
        mock_container.stop.assert_not_called()
        mock_container.remove.assert_not_called()
