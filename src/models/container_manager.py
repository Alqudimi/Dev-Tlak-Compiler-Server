"""
Container Management Module
Handles Docker container operations for code execution
"""

import docker
import os
import uuid
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContainerManager:
    def __init__(self):
        """Initialize Docker client"""
        try:
            self.client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise

    def build_images(self) -> Dict[str, bool]:
        """Build all language-specific Docker images"""
        results = {}
        dockerfiles_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'dockerfiles')
        
        languages = {
            'python': 'Dockerfile.python',
            'nodejs': 'Dockerfile.nodejs', 
            'java': 'Dockerfile.java',
            'go': 'Dockerfile.go',
            'rust': 'Dockerfile.rust',
            'php': 'Dockerfile.php',
            'cpp': 'Dockerfile.cpp'
        }
        
        for lang, dockerfile in languages.items():
            try:
                dockerfile_path = os.path.join(dockerfiles_dir, dockerfile)
                if os.path.exists(dockerfile_path):
                    logger.info(f"Building image for {lang}...")
                    image, logs = self.client.images.build(
                        path=dockerfiles_dir,
                        dockerfile=dockerfile,
                        tag=f"compiler-server-{lang}:latest",
                        rm=True
                    )
                    results[lang] = True
                    logger.info(f"Successfully built image for {lang}")
                else:
                    logger.warning(f"Dockerfile not found for {lang}: {dockerfile_path}")
                    results[lang] = False
            except Exception as e:
                logger.error(f"Failed to build image for {lang}: {e}")
                results[lang] = False
        
        return results

    def create_container(self, language: str, project_id: str = None, 
                        cpu_limit: str = "1", memory_limit: str = "512m") -> Tuple[str, bool]:
        """Create a new container for the specified language"""
        try:
            if not project_id:
                project_id = str(uuid.uuid4())
            
            container_name = f"compiler-{language}-{project_id}"
            image_name = f"compiler-server-{language}:latest"
            
            # Check if image exists
            try:
                self.client.images.get(image_name)
            except docker.errors.ImageNotFound:
                logger.error(f"Image {image_name} not found. Please build images first.")
                return None, False
            
            # Create container with resource limits
            container = self.client.containers.create(
                image=image_name,
                name=container_name,
                detach=True,
                tty=True,
                stdin_open=True,
                working_dir="/workspace",
                mem_limit=memory_limit,
                cpu_quota=int(float(cpu_limit) * 100000),  # Convert to microseconds
                cpu_period=100000,
                network_disabled=False,  # Allow network access
                volumes={
                    f"/tmp/compiler-workspace-{project_id}": {
                        'bind': '/workspace',
                        'mode': 'rw'
                    }
                }
            )
            
            logger.info(f"Created container {container_name} for language {language}")
            return container.id, True
            
        except Exception as e:
            logger.error(f"Failed to create container for {language}: {e}")
            return None, False

    def start_container(self, container_id: str) -> bool:
        """Start a container"""
        try:
            container = self.client.containers.get(container_id)
            container.start()
            logger.info(f"Started container {container_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to start container {container_id}: {e}")
            return False

    def stop_container(self, container_id: str) -> bool:
        """Stop a container"""
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=10)
            logger.info(f"Stopped container {container_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop container {container_id}: {e}")
            return False

    def remove_container(self, container_id: str) -> bool:
        """Remove a container"""
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=True)
            logger.info(f"Removed container {container_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove container {container_id}: {e}")
            return False

    def execute_command(self, container_id: str, command: str, 
                       working_dir: str = "/workspace") -> Tuple[str, str, int]:
        """Execute a command in a container"""
        try:
            container = self.client.containers.get(container_id)
            
            # Ensure container is running
            if container.status != 'running':
                container.start()
            
            # Execute command
            exec_result = container.exec_run(
                command,
                workdir=working_dir,
                demux=True,
                tty=False
            )
            
            stdout = exec_result.output[0].decode('utf-8') if exec_result.output[0] else ""
            stderr = exec_result.output[1].decode('utf-8') if exec_result.output[1] else ""
            exit_code = exec_result.exit_code
            
            logger.info(f"Executed command in container {container_id}: {command}")
            return stdout, stderr, exit_code
            
        except Exception as e:
            logger.error(f"Failed to execute command in container {container_id}: {e}")
            return "", str(e), 1

    def get_container_status(self, container_id: str) -> Dict:
        """Get container status and information"""
        try:
            container = self.client.containers.get(container_id)
            container.reload()
            
            return {
                'id': container.id,
                'name': container.name,
                'status': container.status,
                'created': container.attrs['Created'],
                'image': container.image.tags[0] if container.image.tags else 'unknown',
                'ports': container.ports,
                'labels': container.labels
            }
        except Exception as e:
            logger.error(f"Failed to get status for container {container_id}: {e}")
            return {'error': str(e)}

    def list_containers(self, all_containers: bool = False) -> List[Dict]:
        """List all containers"""
        try:
            containers = self.client.containers.list(all=all_containers)
            result = []
            
            for container in containers:
                result.append({
                    'id': container.id,
                    'name': container.name,
                    'status': container.status,
                    'image': container.image.tags[0] if container.image.tags else 'unknown',
                    'created': container.attrs['Created']
                })
            
            return result
        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
            return []

    def cleanup_old_containers(self, max_age_hours: int = 24) -> int:
        """Clean up containers older than specified hours"""
        try:
            containers = self.client.containers.list(all=True)
            cleaned = 0
            
            for container in containers:
                # Check if container is from our compiler server
                if 'compiler-' in container.name:
                    created_time = datetime.fromisoformat(
                        container.attrs['Created'].replace('Z', '+00:00')
                    )
                    age_hours = (datetime.now().astimezone() - created_time).total_seconds() / 3600
                    
                    if age_hours > max_age_hours:
                        try:
                            container.remove(force=True)
                            cleaned += 1
                            logger.info(f"Cleaned up old container: {container.name}")
                        except Exception as e:
                            logger.error(f"Failed to clean up container {container.name}: {e}")
            
            logger.info(f"Cleaned up {cleaned} old containers")
            return cleaned
            
        except Exception as e:
            logger.error(f"Failed to cleanup old containers: {e}")
            return 0

    def get_system_info(self) -> Dict:
        """Get Docker system information"""
        try:
            info = self.client.info()
            return {
                'containers': info.get('Containers', 0),
                'containers_running': info.get('ContainersRunning', 0),
                'containers_paused': info.get('ContainersPaused', 0),
                'containers_stopped': info.get('ContainersStopped', 0),
                'images': info.get('Images', 0),
                'server_version': info.get('ServerVersion', 'unknown'),
                'memory_total': info.get('MemTotal', 0),
                'cpus': info.get('NCPU', 0)
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {'error': str(e)}

