"""
Logging Configuration and Utilities
Centralized logging system for the compiler server
"""

import logging
import logging.handlers
import os
from datetime import datetime
from flask import request, g
import json

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        
        return json.dumps(log_entry)

def setup_logging(app):
    """Setup logging configuration for the Flask app"""
    
    # Create formatters
    json_formatter = JSONFormatter()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup file handlers
    
    # General application log
    app_log_file = os.path.join(LOGS_DIR, 'app.log')
    app_handler = logging.handlers.RotatingFileHandler(
        app_log_file, maxBytes=10*1024*1024, backupCount=5
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(json_formatter)
    
    # Error log
    error_log_file = os.path.join(LOGS_DIR, 'error.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file, maxBytes=10*1024*1024, backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    
    # Security log
    security_log_file = os.path.join(LOGS_DIR, 'security.log')
    security_handler = logging.handlers.RotatingFileHandler(
        security_log_file, maxBytes=10*1024*1024, backupCount=5
    )
    security_handler.setLevel(logging.INFO)
    security_handler.setFormatter(json_formatter)
    
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)
    
    # Configure Flask app logger
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(app_handler)
    app.logger.addHandler(error_handler)
    
    # Configure security logger
    security_logger = logging.getLogger('security')
    security_logger.addHandler(security_handler)
    
    # Configure specific module loggers
    loggers = [
        'src.routes.auth',
        'src.routes.projects',
        'src.routes.execution',
        'src.routes.containers',
        'src.routes.github',
        'src.routes.terminal',
        'src.models.container_manager'
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.addHandler(app_handler)
        logger.addHandler(error_handler)

def log_request_info():
    """Log request information"""
    logger = logging.getLogger('request')
    
    # Get request info
    method = request.method
    endpoint = request.endpoint
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', 
                                   request.environ.get('REMOTE_ADDR', 'unknown'))
    user_agent = request.headers.get('User-Agent', 'unknown')
    
    # Create log record with extra fields
    extra = {
        'method': method,
        'endpoint': endpoint,
        'ip_address': ip_address,
        'user_agent': user_agent
    }
    
    # Add user ID if available
    if hasattr(g, 'current_user_id'):
        extra['user_id'] = g.current_user_id
    
    # Add request ID if available
    if hasattr(g, 'request_id'):
        extra['request_id'] = g.request_id
    
    logger.info(f"{method} {request.url}", extra=extra)

def log_security_event(event_type, details, user_id=None, ip_address=None):
    """Log security-related events"""
    security_logger = logging.getLogger('security')
    
    extra = {
        'event_type': event_type,
        'details': details
    }
    
    if user_id:
        extra['user_id'] = user_id
    
    if ip_address:
        extra['ip_address'] = ip_address
    elif request:
        extra['ip_address'] = request.environ.get('HTTP_X_FORWARDED_FOR', 
                                                request.environ.get('REMOTE_ADDR', 'unknown'))
    
    security_logger.warning(f"Security event: {event_type}", extra=extra)

def log_container_operation(operation, container_id, project_id=None, user_id=None, success=True, error=None):
    """Log container operations"""
    logger = logging.getLogger('container')
    
    extra = {
        'operation': operation,
        'container_id': container_id,
        'success': success
    }
    
    if project_id:
        extra['project_id'] = project_id
    
    if user_id:
        extra['user_id'] = user_id
    
    if error:
        extra['error'] = str(error)
    
    level = logging.INFO if success else logging.ERROR
    message = f"Container {operation}: {container_id}"
    
    logger.log(level, message, extra=extra)

def log_code_execution(execution_id, project_id, command, success=True, exit_code=None, user_id=None):
    """Log code execution events"""
    logger = logging.getLogger('execution')
    
    extra = {
        'execution_id': execution_id,
        'project_id': project_id,
        'command': command,
        'success': success
    }
    
    if exit_code is not None:
        extra['exit_code'] = exit_code
    
    if user_id:
        extra['user_id'] = user_id
    
    level = logging.INFO if success else logging.WARNING
    message = f"Code execution: {execution_id}"
    
    logger.log(level, message, extra=extra)

def log_github_operation(operation, repository_url, user_id=None, success=True, error=None):
    """Log GitHub operations"""
    logger = logging.getLogger('github')
    
    extra = {
        'operation': operation,
        'repository_url': repository_url,
        'success': success
    }
    
    if user_id:
        extra['user_id'] = user_id
    
    if error:
        extra['error'] = str(error)
    
    level = logging.INFO if success else logging.ERROR
    message = f"GitHub {operation}: {repository_url}"
    
    logger.log(level, message, extra=extra)

class RequestIDMiddleware:
    """Middleware to add request ID to each request"""
    
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        import uuid
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Add to WSGI environ
        environ['REQUEST_ID'] = request_id
        
        return self.app(environ, start_response)

def setup_request_logging(app):
    """Setup request logging middleware"""
    
    @app.before_request
    def before_request():
        import uuid
        
        # Generate request ID if not present
        if not hasattr(g, 'request_id'):
            g.request_id = str(uuid.uuid4())
        
        # Log request info
        log_request_info()
    
    @app.after_request
    def after_request(response):
        # Log response info
        logger = logging.getLogger('response')
        
        extra = {
            'status_code': response.status_code,
            'content_length': response.content_length
        }
        
        if hasattr(g, 'request_id'):
            extra['request_id'] = g.request_id
        
        if hasattr(g, 'current_user_id'):
            extra['user_id'] = g.current_user_id
        
        logger.info(f"Response: {response.status_code}", extra=extra)
        
        return response
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Log unhandled exceptions
        logger = logging.getLogger('error')
        
        extra = {}
        
        if hasattr(g, 'request_id'):
            extra['request_id'] = g.request_id
        
        if hasattr(g, 'current_user_id'):
            extra['user_id'] = g.current_user_id
        
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True, extra=extra)
        
        # Return error response
        return {
            'error': 'Internal server error',
            'request_id': getattr(g, 'request_id', 'unknown')
        }, 500

# Audit logging functions
def log_user_action(action, user_id, details=None):
    """Log user actions for audit purposes"""
    audit_logger = logging.getLogger('audit')
    
    extra = {
        'action': action,
        'user_id': user_id
    }
    
    if details:
        extra['details'] = details
    
    if request:
        extra['ip_address'] = request.environ.get('HTTP_X_FORWARDED_FOR', 
                                                request.environ.get('REMOTE_ADDR', 'unknown'))
        extra['user_agent'] = request.headers.get('User-Agent', 'unknown')
    
    audit_logger.info(f"User action: {action}", extra=extra)

def log_admin_action(action, admin_user_id, target_user_id=None, details=None):
    """Log administrative actions"""
    admin_logger = logging.getLogger('admin')
    
    extra = {
        'action': action,
        'admin_user_id': admin_user_id
    }
    
    if target_user_id:
        extra['target_user_id'] = target_user_id
    
    if details:
        extra['details'] = details
    
    admin_logger.warning(f"Admin action: {action}", extra=extra)

