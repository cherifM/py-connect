import os
import zipfile
import tempfile
import random
from pathlib import Path
from typing import Tuple, Optional

import docker
from docker.models.containers import Container
from docker.errors import DockerException, APIError, NotFound, ImageNotFound, BuildError

from . import models

# In a production environment, this should be a managed pool of ports
MIN_PORT = 10000
MAX_PORT = 20000
USED_PORTS = set()

def get_next_available_port() -> int:
    """Get the next available port for container mapping."""
    if len(USED_PORTS) >= (MAX_PORT - MIN_PORT):
        raise RuntimeError("No more ports available in the configured range")
    
    while True:
        port = random.randint(MIN_PORT, MAX_PORT)
        if port not in USED_PORTS:
            USED_PORTS.add(port)
            return port

def release_port(port: int) -> None:
    """Release a port back to the pool."""
    USED_PORTS.discard(port)

def build_and_run_app(content_item: models.Content, app_zip_path: Path) -> Tuple[str, int]:
    """
    Build a Docker image and run a container for the user's app.
    
    Args:
        content_item: The content item containing app metadata
        app_zip_path: Path to the zip file containing the app code
        
    Returns:
        Tuple containing (container_id, host_port)
    """
    client = docker.from_env()
    image_name = content_item.image_name
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Unzip the application code
            try:
                with zipfile.ZipFile(app_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            except zipfile.BadZipFile as e:
                raise ValueError(f"Invalid zip file: {e}")
            
            # 2. Check for Dockerfile in the extracted files
            dockerfile_path = os.path.join(temp_dir, 'Dockerfile')
            if not os.path.exists(dockerfile_path):
                raise FileNotFoundError(
                    "Dockerfile not found in the uploaded zip. "
                    "Please include a Dockerfile in the root of your application."
                )

            # 3. Build the Docker image
            print(f"Building image: {image_name} from path: {temp_dir}")
            try:
                image, build_logs = client.images.build(
                    path=temp_dir,
                    tag=image_name,
                    rm=True,
                    forcerm=True,
                    pull=True
                )
                
                # Log build output
                for log in build_logs:
                    if 'stream' in log:
                        print(log['stream'].strip())
                    elif 'error' in log:
                        error_msg = log['error'].strip()
                        print(f"Build error: {error_msg}")
                        raise BuildError(error_msg, build_logs)
                        
            except BuildError as e:
                print(f"Build failed for {image_name}")
                for log in e.build_log:
                    if 'stream' in log:
                        print(log['stream'].strip())
                raise

            # 4. Run the container
            internal_port = 80  # Default port, should be configurable
            host_port = get_next_available_port()
            
            print(f"Running container for {image_name}. Mapping {internal_port} -> {host_port}")
            
            try:
                container = client.containers.run(
                    image=image_name,
                    detach=True,
                    ports={f'{internal_port}/tcp': host_port},
                    name=f"pyconnect-{content_item.id}",
                    remove=True,  # Automatically remove the container when it exits
                    environment={
                        "PORT": str(internal_port),
                        "PYCONNECT_CONTENT_ID": str(content_item.id)
                    }
                )
                
                return container.id, host_port
                
            except APIError as e:
                release_port(host_port)  # Release the port if container creation fails
                print(f"Failed to start container: {e}")
                raise
    
    except Exception as e:
        # Clean up the image if it was created but container failed to start
        try:
            client.images.remove(image=image_name, force=True)
        except:
            pass
        raise

def stop_and_remove_container(container_id: str) -> None:
    """
    Stop and remove a Docker container by its ID.
    
    Args:
        container_id: The ID of the container to stop and remove
    """
    if not container_id:
        return
        
    client = docker.from_env()
    
    try:
        container = client.containers.get(container_id)
        print(f"Stopping container {container_id}...")
        
        try:
            container.stop(timeout=10)
            print(f"Container {container_id} stopped successfully.")
        except Exception as e:
            print(f"Warning: Could not stop container {container_id}: {e}")
        
        try:
            container.remove(force=True)
            print(f"Container {container_id} removed successfully.")
        except Exception as e:
            print(f"Warning: Could not remove container {container_id}: {e}")
        
        # Release the port if we can determine it from the container
        try:
            port_bindings = container.attrs['HostConfig']['PortBindings']
            if port_bindings:
                for container_port, host_ports in port_bindings.items():
                    if host_ports:
                        host_port = int(host_ports[0]['HostPort'])
                        release_port(host_port)
                        print(f"Released port {host_port} from container {container_id}")
        except Exception as e:
            print(f"Warning: Could not release ports for container {container_id}: {e}")
    
    except NotFound:
        print(f"Container {container_id} not found, nothing to clean up.")
    except DockerException as e:
        print(f"Error cleaning up container {container_id}: {e}")
        raise
