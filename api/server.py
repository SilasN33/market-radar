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
from sources import database
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

# Register Auth Blueprint
app.register_blueprint(auth_bp, url_prefix='/api/auth')

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RAW_DIR = DATA_DIR / "raw"
REPORT_DIR = DATA_DIR / "reports"


def _latest(directory: Path, prefix: str) -> Path | None:
    """Encontra o arquivo mais recente com o prefixo dado."""
    candidates = sorted(directory.glob(f"{prefix}-*.json"))
    return candidates[-1] if candidates else None


def _load_json(path: Path) -> List[dict] | Dict[str, Any]:
    """Carrega dados JSON."""
    if not path or not path.exists():
        return []
    with path.open(encoding="utf-8") as fp:
        return json.load(fp)


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
    """Retorna o ranking mais recente (From DB)."""
    try:
        opportunities = database.get_latest_ranking()
        
        # Format timestamps/fields if needed
        timestamp = datetime.now().isoformat()
        if opportunities:
            # use the timestamp of the first item
            timestamp = opportunities[0].get("created_at", timestamp)

        return jsonify({
            "timestamp": timestamp,
            "count": len(opportunities),
            "opportunities": opportunities
        })
    except Exception as e:
        print(f"Error fetching ranking: {e}")
        return jsonify({"error": "Database error", "details": str(e)}), 500


@app.route('/api/trends/google')
def get_google_trends():
    """Retorna dados do Google Trends."""
    latest = _latest(RAW_DIR, "google_trends")
    if not latest:
        return jsonify({
            "error": "Nenhum dado do Google Trends disponível",
            "message": "Execute primeiro: python sources/google_trends.py"
        }), 404
    
    data = _load_json(latest)
    return jsonify({
        "timestamp": latest.stem.replace("google_trends-", ""),
        "count": len(data),
        "trends": data
    })


@app.route('/api/trends/mercadolivre')
def get_mercado_livre():
    """Retorna dados do Mercado Livre."""
    latest = _latest(RAW_DIR, "mercado_livre")
    if not latest:
        return jsonify({
            "error": "Nenhum dado do Mercado Livre disponível",
            "message": "Execute primeiro: python sources/mercado_livre.py"
        }), 404
    
    data = _load_json(latest)
    items = []
    if isinstance(data, list):
         items = data
    elif isinstance(data, dict):
         # Try to extract items from dict wrapper
         items = data.get("items") or data.get("products") or data.get("keywords") or []
    
    return jsonify({
        "timestamp": latest.stem.replace("mercado_livre-", ""),
        "count": len(items),
        "marketplace": "Mercado Livre",
        "items": items
    })


@app.route('/api/trends/amazon')
def get_amazon():
    """Retorna dados da Amazon BR."""
    latest = _latest(RAW_DIR, "amazon")
    if not latest:
        return jsonify({
            "error": "Nenhum dado da Amazon disponível",
            "message": "Execute primeiro: python sources/amazon.py"
        }), 404
    
    data = _load_json(latest)
    items = []
    if isinstance(data, list):
         items = data
    elif isinstance(data, dict):
         items = data.get("items") or data.get("products") or []
         
    return jsonify({
        "timestamp": latest.stem.replace("amazon-", ""),
        "count": len(items),
        "marketplace": "Amazon BR",
        "items": items
    })


@app.route('/api/products')
def get_all_products():
    """Retorna TODOS os produtos de TODOS os marketplaces (Mercado Livre + Amazon)."""
    # 1. Carregar Mercado Livre
    ml_latest = _latest(RAW_DIR, "mercado_livre")
    ml_products = []
    if ml_latest:
        data = _load_json(ml_latest)
        if isinstance(data, list):
            ml_products = data
        elif isinstance(data, dict):
            ml_products = data.get("items") or data.get("products") or []

    # 2. Carregar Amazon
    amz_latest = _latest(RAW_DIR, "amazon")
    amz_products = []
    if amz_latest:
        data = _load_json(amz_latest)
        if isinstance(data, list):
            amz_products = data
        elif isinstance(data, dict):
            amz_products = data.get("items") or data.get("products") or []

    # 3. Combinar e Identificar
    all_products = []
    
    # Adicionar ML
    for p in ml_products:
        if not p.get("marketplace"):
            p["marketplace"] = "Mercado Livre"
        all_products.append(p)
        
    # Adicionar Amazon
    for p in amz_products:
        if not p.get("marketplace"):
            p["marketplace"] = "Amazon BR"
        all_products.append(p)

    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "total_products": len(all_products),
        "sources": {
            "mercado_livre": len(ml_products),
            "amazon": len(amz_products)
        },
        "products": all_products
    })


@app.route('/api/stats')
def get_stats():
    """Retorna estatísticas gerais (From DB)."""
    try:
        stats = database.get_db_stats()
        stats["last_updated"] = datetime.now().isoformat()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("🚀 Market Radar API Server v2.1")
    print("📊 Dashboard: http://localhost:5000")
    print("✅ Servidor rodando...\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
