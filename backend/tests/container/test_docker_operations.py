import pytest
import docker
import time
from app import services

# This test requires Docker to be running
pytestmark = pytest.mark.integration

def test_stop_and_remove_container():
    """Test stopping and removing a container"""
    # Skip if not running in an environment with Docker
    try:
        client = docker.from_env()
        client.ping()
    except Exception as e:
        pytest.skip(f"Docker is not available: {e}")
    
    # Start a test container
    container = client.containers.run(
        "hello-world",
        detach=True,
        remove=True
    )
    
    try:
        # Give it a moment to start
        time.sleep(1)
        
        # Test our function
        services.stop_and_remove_container(container.id)
        
        # Verify the container is gone
        with pytest.raises(docker.errors.NotFound):
            client.containers.get(container.id)
            
    except Exception as e:
        # Clean up if the test fails
        try:
            container.remove(force=True)
        except:
            pass
        raise
