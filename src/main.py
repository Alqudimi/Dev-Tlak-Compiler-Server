import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from src.models.user import db
from src.models.project import Project, ExecutionResult
from src.routes.user import user_bp
from src.routes.projects import projects_bp
from src.routes.execution import execution_bp
from src.routes.containers import containers_bp
from src.routes.github import github_bp
from src.routes.terminal import terminal_bp, register_terminal_events, start_cleanup_thread
from src.routes.auth import auth_bp, check_if_token_revoked
from src.routes.health import health_bp
from src.utils.logging_config import setup_logging, setup_request_logging

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-string'  # Change this in production

# Enable CORS for all routes
CORS(app)

# Initialize JWT
jwt = JWTManager(app)

# Configure JWT
jwt.token_in_blocklist_loader(check_if_token_revoked)

# Setup logging
setup_logging(app)
setup_request_logging(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(projects_bp, url_prefix='/api')
app.register_blueprint(execution_bp, url_prefix='/api')
app.register_blueprint(containers_bp, url_prefix='/api')
app.register_blueprint(github_bp, url_prefix='/api')
app.register_blueprint(terminal_bp, url_prefix='/api')
app.register_blueprint(health_bp)

# uncomment if you need to use database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

# Register terminal WebSocket events
register_terminal_events(socketio)

# Start terminal session cleanup thread
start_cleanup_thread()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

# Health check endpoint
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'message': 'Compiler Server is running'}, 200

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
