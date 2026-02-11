"""Collect intent signals directly from Market Trends (High Confidence)."""
import json
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import List

from src.utils.keyword_utils import save_keywords

# Path adjustment
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Official ML Trends API (No Auth required for public trends)
ML_TRENDS_API = "https://api.mercadolibre.com/sites/MLB/trends/search"

def fetch_ml_trends(category: str = None) -> List[str]:
    """Fetch top search trends from Mercado Livre."""
    url = ML_TRENDS_API
    if category:
        url = f"{ML_TRENDS_API}/{category}"
        
    print(f"🔥 Fetching Market Trends from: {url}")
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            trends = resp.json()
            # Trends is top-level listing or specific dict
            if isinstance(trends, list):
                return [t.get("keyword") for t in trends if t.get("keyword")]
        return []
    except Exception as e:
        print(f"❌ Error fetching trends: {e}")
        return []

def main():
    print("🚀 signal_collector: Switching to DIRECT TRENDS mode...")
    
    # 1. Get General Trends (The hottest items right now)
    general_trends = fetch_ml_trends()
    print(f"✅ Captured {len(general_trends)} 'Hot' Trends (General)")
    
    # 2. (Optional) Get Category Trends for 'Eletrônicos, Áudio e Vídeo' (MLB1000)
    # This adds niche specificity
    tech_trends = fetch_ml_trends("MLB1000") 
    print(f"✅ Captured {len(tech_trends)} Tech Trends")
    
    # Combine & Dedup
    all_signals = list(set(general_trends + tech_trends))
    
    # Slice to avoid API limits downstream (Top 40 is plenty for a run)
    limited_signals = all_signals[:40]
    
    print(f"💾 Saving {len(limited_signals)} High-Velocity Signals for Processing...")
    
    # Save as 'mercadolivre_trends' so keyword_utils picks it up with priority
    save_keywords(limited_signals, source="mercadolivre_trends", prefix="intent_signals")

if __name__ == "__main__":
    main()
