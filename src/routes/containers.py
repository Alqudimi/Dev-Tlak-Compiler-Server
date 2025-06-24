"""
Container Management API Routes
Handles container operations
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.container_manager import ContainerManager
from src.models.project import Project
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
containers_bp = Blueprint('containers', __name__)

# Initialize container manager
container_manager = ContainerManager()

@containers_bp.route('/containers', methods=['POST'])
@jwt_required(optional=True)
def create_container():
    """Create a new container"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'language' not in data:
            return jsonify({'error': 'Language is required'}), 400
        
        language = data['language']
        project_id = data.get('project_id')
        cpu_limit = data.get('cpu_limit', '1')
        memory_limit = data.get('memory_limit', '512m')
        
        # Create container
        container_id, success = container_manager.create_container(
            language=language,
            project_id=project_id,
            cpu_limit=cpu_limit,
            memory_limit=memory_limit
        )
        
        if not success or not container_id:
            return jsonify({'error': 'Failed to create container'}), 500
        
        # Update project if project_id provided
        if project_id:
            project = Project.get_by_id(project_id)
            if project:
                project.set_container(container_id, 'created')
                project.save()
        
        logger.info(f"Created container {container_id} for language {language}")
        return jsonify({
            'container_id': container_id,
            'language': language,
            'status': 'created',
            'project_id': project_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating container: {e}")
        return jsonify({'error': str(e)}), 500

@containers_bp.route('/containers/<container_id>/status', methods=['GET'])
@jwt_required(optional=True)
def get_container_status(container_id):
    """Get container status"""
    try:
        status = container_manager.get_container_status(container_id)
        
        if 'error' in status:
            return jsonify({'error': 'Container not found'}), 404
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Error getting container status {container_id}: {e}")
        return jsonify({'error': str(e)}), 500

@containers_bp.route('/containers/<container_id>/start', methods=['POST'])
@jwt_required(optional=True)
def start_container(container_id):
    """Start a container"""
    try:
        success = container_manager.start_container(container_id)
        
        if not success:
            return jsonify({'error': 'Failed to start container'}), 500
        
        # Update project status if container belongs to a project
        project = Project.query.filter_by(container_id=container_id).first()
        if project:
            project.container_status = 'running'
            project.save()
        
        logger.info(f"Started container {container_id}")
        return jsonify({'message': 'Container started successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error starting container {container_id}: {e}")
        return jsonify({'error': str(e)}), 500

@containers_bp.route('/containers/<container_id>/stop', methods=['POST'])
@jwt_required(optional=True)
def stop_container(container_id):
    """Stop a container"""
    try:
        success = container_manager.stop_container(container_id)
        
        if not success:
            return jsonify({'error': 'Failed to stop container'}), 500
        
        # Update project status if container belongs to a project
        project = Project.query.filter_by(container_id=container_id).first()
        if project:
            project.container_status = 'stopped'
            project.save()
        
        logger.info(f"Stopped container {container_id}")
        return jsonify({'message': 'Container stopped successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error stopping container {container_id}: {e}")
        return jsonify({'error': str(e)}), 500

@containers_bp.route('/containers/<container_id>', methods=['DELETE'])
@jwt_required(optional=True)
def delete_container(container_id):
    """Delete a container"""
    try:
        # Stop container first
        container_manager.stop_container(container_id)
        
        # Remove container
        success = container_manager.remove_container(container_id)
        
        if not success:
            return jsonify({'error': 'Failed to delete container'}), 500
        
        # Update project if container belongs to a project
        project = Project.query.filter_by(container_id=container_id).first()
        if project:
            project.container_id = None
            project.container_status = 'deleted'
            project.save()
        
        logger.info(f"Deleted container {container_id}")
        return jsonify({'message': 'Container deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting container {container_id}: {e}")
        return jsonify({'error': str(e)}), 500

@containers_bp.route('/containers', methods=['GET'])
@jwt_required(optional=True)
def list_containers():
    """List all containers"""
    try:
        all_containers = request.args.get('all', 'false').lower() == 'true'
        containers = container_manager.list_containers(all_containers=all_containers)
        
        return jsonify({
            'containers': containers,
            'count': len(containers)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing containers: {e}")
        return jsonify({'error': str(e)}), 500

@containers_bp.route('/containers/<container_id>/execute', methods=['POST'])
@jwt_required(optional=True)
def execute_in_container(container_id):
    """Execute a command in a container"""
    try:
        data = request.get_json()
        
        if not data or 'command' not in data:
            return jsonify({'error': 'Command is required'}), 400
        
        command = data['command']
        working_dir = data.get('working_dir', '/workspace')
        
        stdout, stderr, exit_code = container_manager.execute_command(
            container_id, command, working_dir
        )
        
        result = {
            'stdout': stdout,
            'stderr': stderr,
            'exit_code': exit_code,
            'command': command
        }
        
        logger.info(f"Executed command in container {container_id}: {command}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error executing command in container {container_id}: {e}")
        return jsonify({'error': str(e)}), 500

@containers_bp.route('/containers/cleanup', methods=['POST'])
@jwt_required(optional=True)
def cleanup_containers():
    """Clean up old containers"""
    try:
        max_age_hours = request.args.get('max_age_hours', 24, type=int)
        cleaned_count = container_manager.cleanup_old_containers(max_age_hours)
        
        logger.info(f"Cleaned up {cleaned_count} old containers")
        return jsonify({
            'message': f'Cleaned up {cleaned_count} old containers',
            'cleaned_count': cleaned_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error cleaning up containers: {e}")
        return jsonify({'error': str(e)}), 500

@containers_bp.route('/containers/system-info', methods=['GET'])
@jwt_required(optional=True)
def get_system_info():
    """Get Docker system information"""
    try:
        system_info = container_manager.get_system_info()
        
        return jsonify(system_info), 200
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return jsonify({'error': str(e)}), 500

@containers_bp.route('/containers/build-images', methods=['POST'])
@jwt_required(optional=True)
def build_images():
    """Build all language-specific Docker images"""
    try:
        results = container_manager.build_images()
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        logger.info(f"Built {success_count}/{total_count} Docker images")
        return jsonify({
            'message': f'Built {success_count}/{total_count} Docker images',
            'results': results,
            'success_count': success_count,
            'total_count': total_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error building images: {e}")
        return jsonify({'error': str(e)}), 500

