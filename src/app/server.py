"""Flask Application Factory (V2)."""
import os
from pathlib import Path

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager

from src.utils.env_loader import load_env
from src.database import get_user_by_id

# Import side-effects (routes registration)
import src.app.auth
import src.app.routes
from src.app import auth_bp, api_bp
from src.app.auth import User  # Needed for login_manager

load_env()

# Web folder is relative to this file: ../../web
WEB_DIR = Path(__file__).resolve().parents[2] / "web"

app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path='')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    user_data = get_user_by_id(int(user_id))
    return User(user_data) if user_data else None

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth') # /api/auth/login
app.register_blueprint(api_bp, url_prefix='/api')       # /api/ranking

# Static Routes
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'landing.html')

@app.route('/dashboard')
@app.route('/app')
def dashboard():
    # In a real SPA, this would serve index.html for client-side routing
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    """Serve static files directly or fallback to index.html."""
    try:
        return send_from_directory(app.static_folder, path)
    except:
        return send_from_directory(app.static_folder, 'index.html')


if __name__ == "__main__":
    print("🚀 Market Radar API Server v2.0 (Clean Architecture)")
    print(f"📊 Dashboard: http://localhost:5000")
    if not os.environ.get('SECRET_KEY'):
        print("⚠️  Warning: Using dev SECRET_KEY. Set env var in production.")
        
    app.run(host='0.0.0.0', port=5000, debug=True)
