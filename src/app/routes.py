from flask import Blueprint, jsonify, request
from src.database import get_latest_ranking, get_db_stats

from . import api_bp

@api_bp.route('/ranking')
def get_ranking():
    """Get latest ranking (opportunities)."""
    limit = request.args.get('limit', 50, type=int)
    opps = get_latest_ranking(limit=limit)
    return jsonify({
        "opportunities": opps,
        "count": len(opps)
    })

@api_bp.route('/stats')
def get_stats():
    """Get database stats."""
    return jsonify(get_db_stats())

@api_bp.route('/products')
def get_products():
    """Get validated products (proxy to ranking)."""
    # For now, just alias ranking as products
    opps = get_latest_ranking(limit=100)
    
    products = []
    for o in opps:
        products.append({
            "id": o.get("id"),
            "title": o.get("keyword"), # Use keyword as title proxy
            "url": o.get("url"),
            "thumbnail": o.get("thumbnail"),
            "price": o.get("price"),
            "marketplace": o.get("marketplace"),
            "score": o.get("score"),
            "cluster": o.get("cluster_name")
        })
    return jsonify({"products": products, "count": len(products)})
