"""
Code Execution API Routes
Handles code execution in containers
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.project import Project, ExecutionResult, db
from src.models.container_manager import ContainerManager
import time
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
execution_bp = Blueprint('execution', __name__)

# Initialize container manager
container_manager = ContainerManager()

# Store running executions
running_executions = {}

def execute_code_async(execution_id, project_id, command, working_dir="/workspace"):
    """Execute code asynchronously"""
    try:
        execution = ExecutionResult.get_by_id(execution_id)
        project = Project.get_by_id(project_id)
        
        if not execution or not project:
            logger.error(f"Execution {execution_id} or project {project_id} not found")
            return
        
        # Update status to running
        execution.set_status('running')
        execution.save()
        
        # Start container if not running
        if project.container_id:
            container_manager.start_container(project.container_id)
        
        # Execute command
        start_time = time.time()
        stdout, stderr, exit_code = container_manager.execute_command(
            project.container_id, command, working_dir
        )
        execution_time = time.time() - start_time
        
        # Update execution result
        execution.set_result(stdout, stderr, exit_code, execution_time)
        execution.save()
        
        # Update project execution time
        project.update_execution_time()
        project.save()
        
        # Remove from running executions
        if execution_id in running_executions:
            del running_executions[execution_id]
        
        logger.info(f"Completed execution {execution_id} for project {project_id}")
        
    except Exception as e:
        logger.error(f"Error in async execution {execution_id}: {e}")
        if execution_id in running_executions:
            del running_executions[execution_id]

@execution_bp.route('/execute', methods=['POST'])
@jwt_required(optional=True)
def execute_code():
    """Execute code in a project container"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'project_id' not in data or 'command' not in data:
            return jsonify({'error': 'project_id and command are required'}), 400
        
        project_id = data['project_id']
        command = data['command']
        working_dir = data.get('working_dir', '/workspace')
        
        # Get project
        project = Project.get_by_id(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Check if project has a container
        if not project.container_id:
            return jsonify({'error': 'Project container not found'}), 400
        
        # Create execution record
        execution = ExecutionResult(project_id=project_id, command=command)
        execution.save()
        
        # Add to running executions
        running_executions[execution.id] = {
            'project_id': project_id,
            'command': command,
            'started_at': time.time()
        }
        
        # Start async execution
        thread = threading.Thread(
            target=execute_code_async,
            args=(execution.id, project_id, command, working_dir)
        )
        thread.daemon = True
        thread.start()
        
        logger.info(f"Started execution {execution.id} for project {project_id}")
        return jsonify({
            'execution_id': execution.id,
            'status': 'started',
            'message': 'Code execution started'
        }), 202
        
    except Exception as e:
        logger.error(f"Error starting code execution: {e}")
        return jsonify({'error': str(e)}), 500

@execution_bp.route('/execute/<execution_id>/output', methods=['GET'])
@jwt_required(optional=True)
def get_execution_output(execution_id):
    """Get execution output"""
    try:
        execution = ExecutionResult.get_by_id(execution_id)
        
        if not execution:
            return jsonify({'error': 'Execution not found'}), 404
        
        return jsonify(execution.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error getting execution output {execution_id}: {e}")
        return jsonify({'error': str(e)}), 500

@execution_bp.route('/execute/<execution_id>/stop', methods=['POST'])
@jwt_required(optional=True)
def stop_execution(execution_id):
    """Stop a running execution"""
    try:
        execution = ExecutionResult.get_by_id(execution_id)
        
        if not execution:
            return jsonify({'error': 'Execution not found'}), 404
        
        if execution.status not in ['pending', 'running']:
            return jsonify({'error': 'Execution is not running'}), 400
        
        # Remove from running executions
        if execution_id in running_executions:
            del running_executions[execution_id]
        
        # Update execution status
        execution.set_status('stopped')
        execution.save()
        
        logger.info(f"Stopped execution {execution_id}")
        return jsonify({'message': 'Execution stopped successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error stopping execution {execution_id}: {e}")
        return jsonify({'error': str(e)}), 500

@execution_bp.route('/execute/running', methods=['GET'])
@jwt_required(optional=True)
def get_running_executions():
    """Get all currently running executions"""
    try:
        return jsonify({
            'running_executions': running_executions,
            'count': len(running_executions)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting running executions: {e}")
        return jsonify({'error': str(e)}), 500

@execution_bp.route('/execute/quick', methods=['POST'])
@jwt_required(optional=True)
def quick_execute():
    """Quick code execution without project (temporary container)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'language' not in data or 'code' not in data:
            return jsonify({'error': 'language and code are required'}), 400
        
        language = data['language']
        code = data['code']
        
        # Create temporary container
        container_id, success = container_manager.create_container(
            language=language,
            project_id=f"temp-{int(time.time())}",
            cpu_limit="0.5",
            memory_limit="256m"
        )
        
        if not success or not container_id:
            return jsonify({'error': 'Failed to create container'}), 500
        
        try:
            # Start container
            container_manager.start_container(container_id)
            
            # Write code to file and execute based on language
            if language == 'python':
                # Write Python code to file
                write_cmd = f'echo "{code}" > /workspace/main.py'
                container_manager.execute_command(container_id, write_cmd)
                
                # Execute Python code
                stdout, stderr, exit_code = container_manager.execute_command(
                    container_id, 'python /workspace/main.py'
                )
            
            elif language == 'nodejs':
                # Write Node.js code to file
                write_cmd = f'echo "{code}" > /workspace/main.js'
                container_manager.execute_command(container_id, write_cmd)
                
                # Execute Node.js code
                stdout, stderr, exit_code = container_manager.execute_command(
                    container_id, 'node /workspace/main.js'
                )
            
            elif language == 'java':
                # Write Java code to file (assuming class name is Main)
                write_cmd = f'echo "{code}" > /workspace/Main.java'
                container_manager.execute_command(container_id, write_cmd)
                
                # Compile and execute Java code
                compile_stdout, compile_stderr, compile_exit = container_manager.execute_command(
                    container_id, 'javac /workspace/Main.java'
                )
                
                if compile_exit == 0:
                    stdout, stderr, exit_code = container_manager.execute_command(
                        container_id, 'java -cp /workspace Main'
                    )
                else:
                    stdout, stderr, exit_code = compile_stdout, compile_stderr, compile_exit
            
            elif language == 'cpp':
                # Write C++ code to file
                write_cmd = f'echo "{code}" > /workspace/main.cpp'
                container_manager.execute_command(container_id, write_cmd)
                
                # Compile and execute C++ code
                compile_stdout, compile_stderr, compile_exit = container_manager.execute_command(
                    container_id, 'g++ -o /workspace/main /workspace/main.cpp'
                )
                
                if compile_exit == 0:
                    stdout, stderr, exit_code = container_manager.execute_command(
                        container_id, '/workspace/main'
                    )
                else:
                    stdout, stderr, exit_code = compile_stdout, compile_stderr, compile_exit
            
            elif language == 'go':
                # Write Go code to file
                write_cmd = f'echo "{code}" > /workspace/main.go'
                container_manager.execute_command(container_id, write_cmd)
                
                # Execute Go code
                stdout, stderr, exit_code = container_manager.execute_command(
                    container_id, 'go run /workspace/main.go'
                )
            
            elif language == 'rust':
                # Write Rust code to file
                write_cmd = f'echo "{code}" > /workspace/main.rs'
                container_manager.execute_command(container_id, write_cmd)
                
                # Compile and execute Rust code
                compile_stdout, compile_stderr, compile_exit = container_manager.execute_command(
                    container_id, 'rustc -o /workspace/main /workspace/main.rs'
                )
                
                if compile_exit == 0:
                    stdout, stderr, exit_code = container_manager.execute_command(
                        container_id, '/workspace/main'
                    )
                else:
                    stdout, stderr, exit_code = compile_stdout, compile_stderr, compile_exit
            
            elif language == 'php':
                # Write PHP code to file
                write_cmd = f'echo "{code}" > /workspace/main.php'
                container_manager.execute_command(container_id, write_cmd)
                
                # Execute PHP code
                stdout, stderr, exit_code = container_manager.execute_command(
                    container_id, 'php /workspace/main.php'
                )
            
            else:
                return jsonify({'error': f'Language {language} not supported'}), 400
            
            result = {
                'stdout': stdout,
                'stderr': stderr,
                'exit_code': exit_code,
                'language': language
            }
            
            logger.info(f"Quick execution completed for language {language}")
            return jsonify(result), 200
            
        finally:
            # Clean up temporary container
            container_manager.stop_container(container_id)
            container_manager.remove_container(container_id)
        
    except Exception as e:
        logger.error(f"Error in quick execution: {e}")
        return jsonify({'error': str(e)}), 500

