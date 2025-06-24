"""
Project Model
Handles project data and database operations
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import json

db = SQLAlchemy()

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    language = db.Column(db.String(50), nullable=False)
    framework = db.Column(db.String(100))
    
    # GitHub integration
    github_url = db.Column(db.String(500))
    github_branch = db.Column(db.String(100), default='main')
    
    # Container information
    container_id = db.Column(db.String(100))
    container_status = db.Column(db.String(50), default='stopped')
    
    # Project files and structure
    files = db.Column(db.Text)  # JSON string of file structure
    main_file = db.Column(db.String(255))  # Entry point file
    
    # Resource limits
    cpu_limit = db.Column(db.String(10), default='1')
    memory_limit = db.Column(db.String(10), default='512m')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_executed = db.Column(db.DateTime)
    
    # User association (for future multi-user support)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    
    def __init__(self, name, language, description=None, framework=None, 
                 github_url=None, user_id=None):
        self.name = name
        self.language = language
        self.description = description
        self.framework = framework
        self.github_url = github_url
        self.user_id = user_id
        self.files = json.dumps({})  # Initialize empty file structure
    
    def to_dict(self):
        """Convert project to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'language': self.language,
            'framework': self.framework,
            'github_url': self.github_url,
            'github_branch': self.github_branch,
            'container_id': self.container_id,
            'container_status': self.container_status,
            'files': json.loads(self.files) if self.files else {},
            'main_file': self.main_file,
            'cpu_limit': self.cpu_limit,
            'memory_limit': self.memory_limit,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_executed': self.last_executed.isoformat() if self.last_executed else None,
            'user_id': self.user_id
        }
    
    def update_files(self, files_dict):
        """Update project files structure"""
        self.files = json.dumps(files_dict)
        self.updated_at = datetime.utcnow()
    
    def get_files(self):
        """Get project files as dictionary"""
        return json.loads(self.files) if self.files else {}
    
    def set_container(self, container_id, status='created'):
        """Set container information"""
        self.container_id = container_id
        self.container_status = status
        self.updated_at = datetime.utcnow()
    
    def update_execution_time(self):
        """Update last execution timestamp"""
        self.last_executed = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    @staticmethod
    def get_by_id(project_id):
        """Get project by ID"""
        return Project.query.filter_by(id=project_id).first()
    
    @staticmethod
    def get_by_user(user_id):
        """Get all projects for a user"""
        return Project.query.filter_by(user_id=user_id).all()
    
    @staticmethod
    def get_all():
        """Get all projects"""
        return Project.query.all()
    
    def save(self):
        """Save project to database"""
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        """Delete project from database"""
        db.session.delete(self)
        db.session.commit()


class ExecutionResult(db.Model):
    __tablename__ = 'execution_results'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    
    # Execution details
    command = db.Column(db.Text, nullable=False)
    stdout = db.Column(db.Text)
    stderr = db.Column(db.Text)
    exit_code = db.Column(db.Integer)
    execution_time = db.Column(db.Float)  # in seconds
    
    # Status
    status = db.Column(db.String(50), default='pending')  # pending, running, completed, failed
    
    # Timestamps
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationship
    project = db.relationship('Project', backref=db.backref('executions', lazy=True))
    
    def __init__(self, project_id, command):
        self.project_id = project_id
        self.command = command
    
    def to_dict(self):
        """Convert execution result to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'command': self.command,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'exit_code': self.exit_code,
            'execution_time': self.execution_time,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def set_result(self, stdout, stderr, exit_code, execution_time):
        """Set execution result"""
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.execution_time = execution_time
        self.completed_at = datetime.utcnow()
        self.status = 'completed' if exit_code == 0 else 'failed'
    
    def set_status(self, status):
        """Update execution status"""
        self.status = status
        if status == 'completed' or status == 'failed':
            self.completed_at = datetime.utcnow()
    
    def save(self):
        """Save execution result to database"""
        db.session.add(self)
        db.session.commit()
    
    @staticmethod
    def get_by_id(execution_id):
        """Get execution result by ID"""
        return ExecutionResult.query.filter_by(id=execution_id).first()
    
    @staticmethod
    def get_by_project(project_id, limit=10):
        """Get execution results for a project"""
        return ExecutionResult.query.filter_by(project_id=project_id)\
                                  .order_by(ExecutionResult.started_at.desc())\
                                  .limit(limit).all()

