"""
Authentication and Security Module
Handles user authentication, JWT tokens, and API security
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, 
    get_jwt_identity, get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash
from src.models.user import User, db
import logging
from datetime import timedelta
import secrets
import string

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Store revoked tokens (in production, use Redis or database)
revoked_tokens = set()

def generate_api_key():
    """Generate a secure API key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Username and password are required'}), 400
        
        username = data['username'].strip()
        password = data['password']
        email = data.get('email', '').strip()
        
        # Validate input
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters long'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({'error': 'Username already exists'}), 409
        
        if email:
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                return jsonify({'error': 'Email already exists'}), 409
        
        # Create new user
        password_hash = generate_password_hash(password)
        api_key = generate_api_key()
        
        user = User(
            username=username,
            email=email,
            password_hash=password_hash
        )
        user.api_key = api_key
        user.save()
        
        # Create access token
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=24)
        )
        refresh_token = create_refresh_token(identity=user.id)
        
        logger.info(f"New user registered: {username}")
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token,
            'api_key': api_key
        }), 201
        
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Username and password are required'}), 400
        
        username = data['username'].strip()
        password = data['password']
        
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Update last login
        user.update_last_login()
        user.save()
        
        # Create tokens
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=24)
        )
        refresh_token = create_refresh_token(identity=user.id)
        
        logger.info(f"User logged in: {username}")
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except Exception as e:
        logger.error(f"Error logging in user: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        
        # Create new access token
        access_token = create_access_token(
            identity=current_user_id,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'access_token': access_token
        }), 200
        
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (revoke token)"""
    try:
        jti = get_jwt()['jti']  # JWT ID
        revoked_tokens.add(jti)
        
        logger.info(f"User logged out, token revoked: {jti}")
        return jsonify({'message': 'Successfully logged out'}), 200
        
    except Exception as e:
        logger.error(f"Error logging out user: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'email' in data:
            email = data['email'].strip()
            if email and email != user.email:
                # Check if email already exists
                existing_email = User.query.filter_by(email=email).first()
                if existing_email and existing_email.id != user.id:
                    return jsonify({'error': 'Email already exists'}), 409
                user.email = email
        
        if 'password' in data:
            password = data['password']
            if len(password) < 6:
                return jsonify({'error': 'Password must be at least 6 characters long'}), 400
            user.password_hash = generate_password_hash(password)
        
        user.save()
        
        logger.info(f"User profile updated: {user.username}")
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/api-key/regenerate', methods=['POST'])
@jwt_required()
def regenerate_api_key():
    """Regenerate user API key"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Generate new API key
        new_api_key = generate_api_key()
        user.api_key = new_api_key
        user.save()
        
        logger.info(f"API key regenerated for user: {user.username}")
        return jsonify({
            'message': 'API key regenerated successfully',
            'api_key': new_api_key
        }), 200
        
    except Exception as e:
        logger.error(f"Error regenerating API key: {e}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/verify-token', methods=['GET'])
@jwt_required()
def verify_token():
    """Verify if token is valid"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'valid': True,
            'user_id': current_user_id,
            'username': user.username
        }), 200
        
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return jsonify({'error': str(e)}), 500

# JWT token verification functions
def check_if_token_revoked(jwt_header, jwt_payload):
    """Check if JWT token is revoked"""
    jti = jwt_payload['jti']
    return jti in revoked_tokens

def verify_api_key(api_key):
    """Verify API key"""
    try:
        user = User.query.filter_by(api_key=api_key).first()
        return user
    except Exception as e:
        logger.error(f"Error verifying API key: {e}")
        return None

# Middleware for API key authentication
def api_key_required(f):
    """Decorator for API key authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 401
        
        user = verify_api_key(api_key)
        if not user:
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Add user to request context
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function

# Rate limiting (basic implementation)
from collections import defaultdict
import time

request_counts = defaultdict(list)

def rate_limit(max_requests=100, window=3600):  # 100 requests per hour
    """Rate limiting decorator"""
    def decorator(f):
        from functools import wraps
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
            
            current_time = time.time()
            
            # Clean old requests
            request_counts[client_ip] = [
                req_time for req_time in request_counts[client_ip]
                if current_time - req_time < window
            ]
            
            # Check rate limit
            if len(request_counts[client_ip]) >= max_requests:
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            # Add current request
            request_counts[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

