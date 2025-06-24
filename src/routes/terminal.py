"""
Terminal API Routes and WebSocket Handlers
Handles terminal access to containers
"""

from flask import Blueprint, request, jsonify
from flask_socketio import emit, join_room, leave_room
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.project import Project
from src.models.container_manager import ContainerManager
import uuid
import logging
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
terminal_bp = Blueprint('terminal', __name__)

# Initialize container manager
container_manager = ContainerManager()

# Store active terminal sessions
terminal_sessions = {}

class TerminalSession:
    def __init__(self, session_id, container_id, project_id=None):
        self.session_id = session_id
        self.container_id = container_id
        self.project_id = project_id
        self.created_at = time.time()
        self.last_activity = time.time()
        self.is_active = True
    
    def update_activity(self):
        self.last_activity = time.time()
    
    def close(self):
        self.is_active = False

@terminal_bp.route('/terminal/create', methods=['POST'])
@jwt_required(optional=True)
def create_terminal_session():
    """Create a new terminal session for a container"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        container_id = data.get('container_id')
        project_id = data.get('project_id')
        
        # If project_id is provided, get container from project
        if project_id and not container_id:
            project = Project.get_by_id(project_id)
            if not project:
                return jsonify({'error': 'Project not found'}), 404
            
            if not project.container_id:
                return jsonify({'error': 'Project has no associated container'}), 400
            
            container_id = project.container_id
        
        if not container_id:
            return jsonify({'error': 'container_id or project_id is required'}), 400
        
        # Check if container exists and is accessible
        container_status = container_manager.get_container_status(container_id)
        if 'error' in container_status:
            return jsonify({'error': 'Container not found or not accessible'}), 404
        
        # Start container if not running
        if container_status.get('status') != 'running':
            success = container_manager.start_container(container_id)
            if not success:
                return jsonify({'error': 'Failed to start container'}), 500
        
        # Create terminal session
        session_id = str(uuid.uuid4())
        terminal_session = TerminalSession(session_id, container_id, project_id)
        terminal_sessions[session_id] = terminal_session
        
        logger.info(f"Created terminal session {session_id} for container {container_id}")
        return jsonify({
            'session_id': session_id,
            'container_id': container_id,
            'project_id': project_id,
            'websocket_url': f'/api/terminal/connect/{session_id}',
            'status': 'created'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating terminal session: {e}")
        return jsonify({'error': str(e)}), 500

@terminal_bp.route('/terminal/<session_id>/status', methods=['GET'])
@jwt_required(optional=True)
def get_terminal_session_status(session_id):
    """Get terminal session status"""
    try:
        if session_id not in terminal_sessions:
            return jsonify({'error': 'Terminal session not found'}), 404
        
        session = terminal_sessions[session_id]
        
        return jsonify({
            'session_id': session.session_id,
            'container_id': session.container_id,
            'project_id': session.project_id,
            'created_at': session.created_at,
            'last_activity': session.last_activity,
            'is_active': session.is_active
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting terminal session status: {e}")
        return jsonify({'error': str(e)}), 500

@terminal_bp.route('/terminal/<session_id>', methods=['DELETE'])
@jwt_required(optional=True)
def close_terminal_session(session_id):
    """Close a terminal session"""
    try:
        if session_id not in terminal_sessions:
            return jsonify({'error': 'Terminal session not found'}), 404
        
        session = terminal_sessions[session_id]
        session.close()
        del terminal_sessions[session_id]
        
        logger.info(f"Closed terminal session {session_id}")
        return jsonify({'message': 'Terminal session closed successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error closing terminal session: {e}")
        return jsonify({'error': str(e)}), 500

@terminal_bp.route('/terminal/sessions', methods=['GET'])
@jwt_required(optional=True)
def list_terminal_sessions():
    """List all active terminal sessions"""
    try:
        sessions = []
        for session_id, session in terminal_sessions.items():
            sessions.append({
                'session_id': session.session_id,
                'container_id': session.container_id,
                'project_id': session.project_id,
                'created_at': session.created_at,
                'last_activity': session.last_activity,
                'is_active': session.is_active
            })
        
        return jsonify({
            'sessions': sessions,
            'count': len(sessions)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing terminal sessions: {e}")
        return jsonify({'error': str(e)}), 500

# WebSocket event handlers (to be registered with SocketIO)
def register_terminal_events(socketio):
    """Register terminal WebSocket events"""
    
    @socketio.on('connect', namespace='/terminal')
    def handle_terminal_connect(auth):
        """Handle terminal WebSocket connection"""
        try:
            logger.info(f"Terminal WebSocket connection established")
            emit('connected', {'message': 'Terminal connection established'})
        except Exception as e:
            logger.error(f"Error in terminal connect: {e}")
            emit('error', {'error': str(e)})
    
    @socketio.on('disconnect', namespace='/terminal')
    def handle_terminal_disconnect():
        """Handle terminal WebSocket disconnection"""
        try:
            logger.info(f"Terminal WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error in terminal disconnect: {e}")
    
    @socketio.on('join_session', namespace='/terminal')
    def handle_join_session(data):
        """Join a terminal session"""
        try:
            session_id = data.get('session_id')
            
            if not session_id or session_id not in terminal_sessions:
                emit('error', {'error': 'Invalid session ID'})
                return
            
            session = terminal_sessions[session_id]
            
            if not session.is_active:
                emit('error', {'error': 'Session is not active'})
                return
            
            # Join the session room
            join_room(session_id)
            session.update_activity()
            
            # Send welcome message
            emit('output', {
                'data': f'Connected to terminal session {session_id}\n',
                'type': 'system'
            })
            
            # Send current working directory
            stdout, stderr, exit_code = container_manager.execute_command(
                session.container_id, 'pwd'
            )
            
            if exit_code == 0:
                emit('output', {
                    'data': f'Current directory: {stdout.strip()}\n',
                    'type': 'system'
                })
            
            logger.info(f"Client joined terminal session {session_id}")
            
        except Exception as e:
            logger.error(f"Error joining terminal session: {e}")
            emit('error', {'error': str(e)})
    
    @socketio.on('leave_session', namespace='/terminal')
    def handle_leave_session(data):
        """Leave a terminal session"""
        try:
            session_id = data.get('session_id')
            
            if session_id:
                leave_room(session_id)
                logger.info(f"Client left terminal session {session_id}")
            
        except Exception as e:
            logger.error(f"Error leaving terminal session: {e}")
    
    @socketio.on('execute_command', namespace='/terminal')
    def handle_execute_command(data):
        """Execute a command in the terminal"""
        try:
            session_id = data.get('session_id')
            command = data.get('command', '').strip()
            
            if not session_id or session_id not in terminal_sessions:
                emit('error', {'error': 'Invalid session ID'})
                return
            
            session = terminal_sessions[session_id]
            
            if not session.is_active:
                emit('error', {'error': 'Session is not active'})
                return
            
            session.update_activity()
            
            if not command:
                return
            
            # Echo the command
            emit('output', {
                'data': f'$ {command}\n',
                'type': 'command'
            }, room=session_id)
            
            # Execute command in container
            stdout, stderr, exit_code = container_manager.execute_command(
                session.container_id, command
            )
            
            # Send stdout
            if stdout:
                emit('output', {
                    'data': stdout,
                    'type': 'stdout'
                }, room=session_id)
            
            # Send stderr
            if stderr:
                emit('output', {
                    'data': stderr,
                    'type': 'stderr'
                }, room=session_id)
            
            # Send exit code if non-zero
            if exit_code != 0:
                emit('output', {
                    'data': f'Command exited with code {exit_code}\n',
                    'type': 'system'
                }, room=session_id)
            
            logger.info(f"Executed command in session {session_id}: {command}")
            
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            emit('error', {'error': str(e)})
    
    @socketio.on('get_directory_listing', namespace='/terminal')
    def handle_get_directory_listing(data):
        """Get directory listing"""
        try:
            session_id = data.get('session_id')
            path = data.get('path', '/workspace')
            
            if not session_id or session_id not in terminal_sessions:
                emit('error', {'error': 'Invalid session ID'})
                return
            
            session = terminal_sessions[session_id]
            session.update_activity()
            
            # Execute ls command
            stdout, stderr, exit_code = container_manager.execute_command(
                session.container_id, f'ls -la {path}'
            )
            
            if exit_code == 0:
                emit('directory_listing', {
                    'path': path,
                    'listing': stdout,
                    'success': True
                })
            else:
                emit('directory_listing', {
                    'path': path,
                    'error': stderr,
                    'success': False
                })
            
        except Exception as e:
            logger.error(f"Error getting directory listing: {e}")
            emit('error', {'error': str(e)})

def cleanup_inactive_sessions():
    """Clean up inactive terminal sessions"""
    try:
        current_time = time.time()
        inactive_sessions = []
        
        for session_id, session in terminal_sessions.items():
            # Close sessions inactive for more than 1 hour
            if current_time - session.last_activity > 3600:
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            if session_id in terminal_sessions:
                terminal_sessions[session_id].close()
                del terminal_sessions[session_id]
                logger.info(f"Cleaned up inactive terminal session {session_id}")
        
        return len(inactive_sessions)
        
    except Exception as e:
        logger.error(f"Error cleaning up terminal sessions: {e}")
        return 0

# Start cleanup thread
def start_cleanup_thread():
    """Start background thread for session cleanup"""
    def cleanup_loop():
        while True:
            time.sleep(300)  # Run every 5 minutes
            cleanup_inactive_sessions()
    
    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()
    logger.info("Started terminal session cleanup thread")

