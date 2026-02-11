from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user, UserMixin

from src.database import (
    create_user, get_user_by_email, verify_password, get_user_by_id,
    save_opportunity_for_user, get_user_saved_opportunities,
    create_project, get_user_projects
)

# Use Blueprint from init
from . import auth_bp

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.email = user_data['email']
        self.name = user_data.get('name', '')
        self.role = user_data.get('role', 'free')

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
        
    user_id = create_user(email, password, name)
    if not user_id:
        return jsonify({"error": "User already exists"}), 409
        
    return jsonify({"message": "User created", "user_id": user_id}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    user_data = get_user_by_email(email)
    if user_data and verify_password(user_data, password):
        user = User(user_data)
        login_user(user)
        return jsonify({"message": "Logged in", "user": {"email": email, "role": user.role}})
        
    return jsonify({"error": "Invalid credentials"}), 401

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out"})

@auth_bp.route('/me')
@login_required
def me():
    return jsonify({
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role
    })
