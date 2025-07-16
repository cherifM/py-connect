import logging
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import docker
from docker.models.containers import Container
from docker.errors import (
    DockerException,
    APIError,
    ImageNotFound,
    ContainerError,
    BuildError,
)

from app.config.settings import settings
from app.core.file_utils import cleanup_directory

logger = logging.getLogger(__name__)

class DockerManager:
    """
    A class to manage Docker operations for the application.
    """
    
    def __init__(self):
        """Initialize the Docker client."""
        try:
            self.client = docker.from_env()
            self.client.ping()  # Test connection
            logger.info("Docker daemon connection established")
        except DockerException as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            raise
    
    def build_image(
        self,
        build_path: Path,
        tag: str,
        dockerfile: str = "Dockerfile",
        build_args: Optional[Dict] = None,
    ) -> str:
        """
        Build a Docker image from a Dockerfile.
        
        Args:
            build_path: Path to the build context
            tag: Tag for the built image
            dockerfile: Path to Dockerfile relative to build_path
            build_args: Build arguments
            
        Returns:
            str: Image ID
            
        Raises:
            BuildError: If the build fails
        """
        try:
            logger.info(f"Building Docker image from {build_path} with tag {tag}")
            
            # Convert build_args to the format expected by Docker SDK
            build_kwargs = {
                "path": str(build_path),
                "tag": tag,
                "dockerfile": dockerfile,
                "rm": True,
                "forcerm": True,
                "pull": True,
            }
            
            if build_args:
                build_kwargs["buildargs"] = build_args
            
            # Build the image
            image, logs = self.client.images.build(**build_kwargs)
            
            # Log build output
            for log in logs:
                if "stream" in log:
                    logger.debug(log["stream"].strip())
                elif "error" in log:
                    error_msg = log["error"].strip()
                    logger.error(f"Build error: {error_msg}")
                    raise BuildError(error_msg, logs)
            
            logger.info(f"Successfully built image {image.id}")
            return image.id
            
        except Exception as e:
            logger.error(f"Failed to build Docker image: {e}")
            if isinstance(e, BuildError):
                raise
            raise BuildError(str(e), [])
    
    def run_container(
        self,
        image: str,
        name: Optional[str] = None,
        ports: Optional[Dict[str, int]] = None,
        environment: Optional[Dict[str, str]] = None,
        volumes: Optional[Dict[str, Dict[str, str]]] = None,
        network: Optional[str] = None,
        detach: bool = True,
        remove: bool = True,
        **kwargs,
    ) -> Container:
        """
        Run a Docker container.
        
        Args:
            image: Name or ID of the image to run
            name: Name for the container
            ports: Port mappings (container_port: host_port)
            environment: Environment variables
            volumes: Volume mappings
            network: Network to connect to
            detach: Whether to run in detached mode
            remove: Whether to remove the container when it exits
            **kwargs: Additional arguments to pass to container.run()
            
        Returns:
            Container: The container object
            
        Raises:
            ContainerError: If the container fails to start
        """
        try:
            logger.info(f"Starting container from image {image}")
            
            # Prepare container configuration
            container_config = {
                "image": image,
                "detach": detach,
                "remove": remove,
                "ports": ports or {},
                "environment": environment or {},
                "network": network,
                "name": name,
                **kwargs,
            }
            
            # Add volumes if specified
            if volumes:
                container_config["volumes"] = volumes
            
            # Run the container
            container = self.client.containers.run(**container_config)
            
            logger.info(f"Started container {container.id}")
            return container
            
        except Exception as e:
            logger.error(f"Failed to start container: {e}")
            if isinstance(e, (ContainerError, APIError)):
                raise
            raise ContainerError(container_id=None, exit_status=1, command="", image=image, stderr=str(e))
    
    def stop_container(self, container_id: str, timeout: int = 10) -> None:
        """
        Stop a running container.
        
        Args:
            container_id: ID of the container to stop
            timeout: Timeout in seconds to wait for the container to stop
            
        Raises:
            APIError: If the Docker API returns an error
        """
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=timeout)
            logger.info(f"Stopped container {container_id}")
        except Exception as e:
            logger.error(f"Failed to stop container {container_id}: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to stop container: {e}")
    
    def remove_container(self, container_id: str, force: bool = False) -> None:
        """
        Remove a container.
        
        Args:
            container_id: ID of the container to remove
            force: Force remove the container if it's running
            
        Raises:
            APIError: If the Docker API returns an error
        """
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
            logger.info(f"Removed container {container_id}")
        except Exception as e:
            logger.error(f"Failed to remove container {container_id}: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to remove container: {e}")
    
    def get_available_port(self) -> int:
        """
        Get an available port in the configured range.
        
        Returns:
            int: An available port number
            
        Raises:
            RuntimeError: If no ports are available in the range
        """
        min_port, max_port = settings.DOCKER_PORT_RANGE
        used_ports = self._get_used_ports()
        
        # Try to find an available port
        for port in range(min_port, max_port + 1):
            if port not in used_ports:
                return port
        
        raise RuntimeError(f"No available ports in range {min_port}-{max_port}")
    
    def _get_used_ports(self) -> set[int]:
        """
        Get a set of currently used ports.
        
        Returns:
            set[int]: Set of used port numbers
        """
        used_ports = set()
        
        # Get ports used by running containers
        for container in self.client.containers.list():
            for port_bindings in container.ports.values():
                if port_bindings:
                    for binding in port_bindings:
                        if binding and 'HostPort' in binding:
                            used_ports.add(int(binding['HostPort']))
        
        return used_ports
    
    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self.client.close()
        except Exception as e:
            logger.error(f"Error cleaning up Docker client: {e}")

# Create a singleton instance
docker_manager = DockerManager()
