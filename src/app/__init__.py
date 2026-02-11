from flask import Blueprint

# Initialize blueprints to avoid circular imports later
auth_bp = Blueprint('auth', __name__)
api_bp = Blueprint('api', __name__)
