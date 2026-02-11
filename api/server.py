"""Flask API para servir dados do Market Radar."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager
import sys

# Add root directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# IMPORTANT: Import patch BEFORE database to enable Postgres
from sources import database_patch
from sources import database

# Import auth from api folder
try:
    from api.auth import auth_bp, User
except ImportError:
    from auth import auth_bp, User

app = Flask(__name__, static_folder='../web', static_url_path='')
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'  # TODO: Move to env
CORS(app)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    user_data = database.get_user_by_id(int(user_id))
    return User(user_data) if user_data else None

# Register authentication blueprint
app.register_blueprint(auth_bp, url_prefix='/api/auth')

@app.route('/')
def index():
    """Serve landing page or dashboard based on authentication."""
    from flask_login import current_user
    
    # If user is authenticated, show dashboard
    if current_user.is_authenticated:
        return send_from_directory(app.static_folder, 'index.html')
    
    # Otherwise, show landing page
    return send_from_directory(app.static_folder, 'landing.html')


@app.route('/api/ranking')
def get_ranking():
    """Retorna o ranking de oportunidades (últimos 20)."""
    try:
        opportunities = database.get_latest_ranking(limit=20)
        return jsonify({
            "opportunities": opportunities,
            "count": len(opportunities)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/stats')
def get_stats():
    """Retorna estatísticas do banco de dados."""
    try:
        stats = database.get_db_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/products')
def get_products():
    """Endpoint para listar todos os produtos rastreados."""
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id, 
                title, 
                url, 
                thumbnail, 
                marketplace,
                keyword,
                scraped_at
            FROM products
            ORDER BY scraped_at DESC
            LIMIT 100
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        products = []
        for row in rows:
            products.append({
                "id": row[0],
                "title": row[1],
                "url": row[2],
                "thumbnail": row[3],
                "marketplace": row[4],
                "keyword": row[5],
                "scraped_at": row[6]
            })
        
        return jsonify({
            "products": products,
            "count": len(products)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("🚀 Market Radar API Server v2.1")
    print(f"📊 Dashboard: http://localhost:5000")
    print("✅ Servidor rodando...")
    app.run(host='0.0.0.0', port=5000, debug=True)
