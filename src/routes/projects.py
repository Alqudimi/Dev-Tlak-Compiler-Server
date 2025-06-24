"""
Project Management API Routes
Handles CRUD operations for projects
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.project import Project, ExecutionResult, db
from src.models.container_manager import ContainerManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
projects_bp = Blueprint('projects', __name__)

# Initialize container manager
container_manager = ContainerManager()

@projects_bp.route('/projects', methods=['POST'])
@jwt_required(optional=True)  # Make JWT optional for now
def create_project():
    """Create a new project"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'name' not in data or 'language' not in data:
            return jsonify({'error': 'Name and language are required'}), 400
        
        # Get user ID from JWT (optional for now)
        user_id = get_jwt_identity() if get_jwt_identity() else None
        
        # Create new project
        project = Project(
            name=data['name'],
            language=data['language'],
            description=data.get('description'),
            framework=data.get('framework'),
            github_url=data.get('github_url'),
            user_id=user_id
        )
        
        # Set resource limits if provided
        if 'cpu_limit' in data:
            project.cpu_limit = data['cpu_limit']
        if 'memory_limit' in data:
            project.memory_limit = data['memory_limit']
        
        # Save project
        project.save()
        
        # Create container for the project
        container_id, success = container_manager.create_container(
            language=project.language,
            project_id=project.id,
            cpu_limit=project.cpu_limit,
            memory_limit=project.memory_limit
        )
        
        if success and container_id:
            project.set_container(container_id, 'created')
            project.save()
        
        logger.info(f"Created project {project.id} with container {container_id}")
        return jsonify(project.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects', methods=['GET'])
@jwt_required(optional=True)
def get_projects():
    """Get all projects or projects for a specific user"""
    try:
        user_id = get_jwt_identity() if get_jwt_identity() else None
        
        if user_id:
            projects = Project.get_by_user(user_id)
        else:
            projects = Project.get_all()
        
        return jsonify([project.to_dict() for project in projects]), 200
        
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects/<project_id>', methods=['GET'])
@jwt_required(optional=True)
def get_project(project_id):
    """Get a specific project by ID"""
    try:
        project = Project.get_by_id(project_id)
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Get container status if container exists
        if project.container_id:
            container_status = container_manager.get_container_status(project.container_id)
            project_dict = project.to_dict()
            project_dict['container_info'] = container_status
            return jsonify(project_dict), 200
        
        return jsonify(project.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error getting project {project_id}: {e}")
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects/<project_id>', methods=['PUT'])
@jwt_required(optional=True)
def update_project(project_id):
    """Update a project"""
    try:
        project = Project.get_by_id(project_id)
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'name' in data:
            project.name = data['name']
        if 'description' in data:
            project.description = data['description']
        if 'framework' in data:
            project.framework = data['framework']
        if 'github_url' in data:
            project.github_url = data['github_url']
        if 'github_branch' in data:
            project.github_branch = data['github_branch']
        if 'main_file' in data:
            project.main_file = data['main_file']
        if 'cpu_limit' in data:
            project.cpu_limit = data['cpu_limit']
        if 'memory_limit' in data:
            project.memory_limit = data['memory_limit']
        if 'files' in data:
            project.update_files(data['files'])
        
        project.save()
        
        logger.info(f"Updated project {project_id}")
        return jsonify(project.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {e}")
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects/<project_id>', methods=['DELETE'])
@jwt_required(optional=True)
def delete_project(project_id):
    """Delete a project"""
    try:
        project = Project.get_by_id(project_id)
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Stop and remove container if exists
        if project.container_id:
            container_manager.stop_container(project.container_id)
            container_manager.remove_container(project.container_id)
        
        # Delete project from database
        project.delete()
        
        logger.info(f"Deleted project {project_id}")
        return jsonify({'message': 'Project deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}")
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects/<project_id>/files', methods=['POST'])
@jwt_required(optional=True)
def upload_files(project_id):
    """Upload files to a project"""
    try:
        project = Project.get_by_id(project_id)
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        data = request.get_json()
        
        if not data or 'files' not in data:
            return jsonify({'error': 'Files data is required'}), 400
        
        # Update project files
        project.update_files(data['files'])
        project.save()
        
        logger.info(f"Updated files for project {project_id}")
        return jsonify({'message': 'Files updated successfully', 'files': project.get_files()}), 200
        
    except Exception as e:
        logger.error(f"Error uploading files to project {project_id}: {e}")
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/projects/<project_id>/executions', methods=['GET'])
@jwt_required(optional=True)
def get_project_executions(project_id):
    """Get execution history for a project"""
    try:
        project = Project.get_by_id(project_id)
        
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        limit = request.args.get('limit', 10, type=int)
        executions = ExecutionResult.get_by_project(project_id, limit)
        
        return jsonify([execution.to_dict() for execution in executions]), 200
        
    except Exception as e:
        logger.error(f"Error getting executions for project {project_id}: {e}")
        return jsonify({'error': str(e)}), 500

