"""Metrics Service for Market Radar V2."""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

from src.database import get_term_history


def calculate_search_velocity(term: str) -> Dict[str, float]:
    """Calculate velocity index (0-1) based on history."""
    history = get_term_history(term, limit=7)
    
    if not history or len(history) < 2:
        return {
            "velocity_index": 0.5,
            "acceleration": 0.0,
            "trend_direction": "stable"
        }

    history.sort(key=lambda x: x['captured_at'])
    current = history[-1]['metric_value']
    previous = history[-2]['metric_value']
    
    velocity = 0.0
    if previous > 0:
        velocity = (current - previous) / abs(previous)
        
    acceleration = 0.0
    if len(history) >= 3:
        prev_prev = history[-3]['metric_value']
        v1 = (previous - prev_prev)
        v2 = (current - previous)
        acceleration = v2 - v1

    # Normalize (-0.5 to +0.5 range mapped to 0-1)
    norm_velocity = max(0, min(1, (velocity + 0.5) / 2))
    
    direction = "stable"
    if velocity > 0.2: direction = "growing"
    if velocity > 0.8: direction = "exploding"
    if velocity < -0.1: direction = "declining"

    return {
        "velocity_index": norm_velocity,
        "acceleration": acceleration,
        "trend_direction": direction
    }


def analyze_market_concentration(scraped_items: List[Dict]) -> float:
    """Calculate concentration (0-1). 1.0 = Monopoly."""
    if not scraped_items: return 0.0
    sellers = {}
    for item in scraped_items:
        s = item.get('seller_name') or item.get('brand') or "Unknown"
        sellers[s] = sellers.get(s, 0) + 1
    
    sorted_sellers = sorted(sellers.values(), reverse=True)
    top_3 = sum(sorted_sellers[:3])
    return top_3 / len(scraped_items)


def analyze_price_compression(scraped_items: List[Dict]) -> float:
    """Calculate price compression (0-1). 1.0 = Race to bottom."""
    prices = [i.get('price', 0) for i in scraped_items if i.get('price', 0) > 0]
    if len(prices) < 2: return 0.0
    
    min_p, max_p = min(prices), max(prices)
    if max_p == 0: return 0.0
    
    spread = (max_p - min_p) / max_p
    return max(0.0, min(1.0, 1.0 - spread))


def analyze_quality_opportunity(scraped_items: List[Dict]) -> float:
    """Calculate quality opportunity (0-1). 1.0 = Competitors are bad."""
    ratings = [i.get('rating', 0) for i in scraped_items if i.get('rating', 0) > 0]
    if not ratings: return 0.5
    
    avg_rating = sum(ratings) / len(ratings)
    
    # Formula: (5 - Rating) / 5 * booster
    opp_index = (5.0 - avg_rating) / 5.0
    if avg_rating < 4.0: opp_index *= 1.5
    
    return max(0.0, min(1.0, opp_index))
