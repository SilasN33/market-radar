"""Authentication Blueprint for Market Radar SaaS."""
from flask import Blueprint, request, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# IMPORTANT: Import patch BEFORE database to enable Postgres
from sources import database_patch
from sources import database

auth_bp = Blueprint('auth', __name__)

# User Model for Flask-Login
class User(UserMixin):
    def __init__(self, user_dict):
        self.id = user_dict['id']
        self.email = user_dict['email']
        self.name = user_dict.get('name', '')
        self.role = user_dict.get('role', 'free')
        self.credits = user_dict.get('credits', 0)

# --- Auth Routes ---

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Create a new user account."""
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    name = data.get('name', '')
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    # Initialize DB
    database.init_db()
    
    user_id = database.create_user(email, password, name)
    
    if not user_id:
        return jsonify({"error": "Email already registered"}), 409
    
    return jsonify({
        "message": "User created successfully",
        "user_id": user_id
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and create session."""
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    user_data = database.get_user_by_email(email)
    
    if not user_data or not database.verify_password(user_data, password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    user = User(user_data)
    login_user(user, remember=True)
    
    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "credits": user.credits
        }
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout current user."""
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current authenticated user info."""
    return jsonify({
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "credits": current_user.credits
    }), 200

@auth_bp.route('/saved', methods=['GET'])
@login_required
def get_saved():
    """Get user's saved opportunities."""
    saved = database.get_user_saved_opportunities(current_user.id)
    return jsonify({"saved": saved}), 200

@auth_bp.route('/save/<int:opportunity_id>', methods=['POST'])
@login_required
def save_opportunity(opportunity_id):
    """Save an opportunity to favorites."""
    data = request.get_json() or {}
    notes = data.get('notes', '')
    
    saved_id = database.save_opportunity_for_user(
        current_user.id, 
        opportunity_id, 
        notes=notes
    )
    
    return jsonify({"message": "Opportunity saved", "id": saved_id}), 201

@auth_bp.route('/projects', methods=['GET'])
@login_required
def get_projects():
    """Get user's projects."""
    projects = database.get_user_projects(current_user.id)
    return jsonify({"projects": projects}), 200

@auth_bp.route('/projects', methods=['POST'])
@login_required
def create_project():
    """Create a new project."""
    data = request.get_json()
    name = data.get('name')
    description = data.get('description', '')
    
    if not name:
        return jsonify({"error": "Project name required"}), 400
    
    project_id = database.create_project(current_user.id, name, description)
    return jsonify({"message": "Project created", "id": project_id}), 201
