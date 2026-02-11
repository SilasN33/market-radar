"""Collect intent signals from multiple sources (Autocomplete, Trends)."""
import json
import requests
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict

# Clean Architecture Imports
from src.utils.keyword_utils import save_keywords, load_keywords

# Path adjustment: src/services -> parents[2] root
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TRENDS_SOURCES = {
    "mercadolivre": "https://http2.mlstatic.com/resources/sites/MLB/autosuggest",
    "google_trends": "https://trends.google.com/trends/api/dailytrends"
}

def fetch_mercadolivre_autocomplete(seed_keyword: str) -> List[str]:
    """Fetch autocomplete suggestions from ML API."""
    url = f"{TRENDS_SOURCES['mercadolivre']}?q={urllib.parse.quote(seed_keyword)}&limit=6"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return [item['q'] for item in data.get('suggested_queries', [])]
        return []
    except Exception:
        return []

def collect_signals(seed_list: List[str]) -> List[str]:
    """Expand seeds into long-tail intent keywords."""
    all_signals = set()
    print(f"📡 Capturing signals for {len(seed_list)} seeds...")
    
    for seed in seed_list:
        start_t = time.time()
        suggestions = fetch_mercadolivre_autocomplete(seed)
        all_signals.update(suggestions)
        
        # Recursive breadth (1 level deep)
        for sub in suggestions[:2]:
            sub_suggestions = fetch_mercadolivre_autocomplete(sub)
            all_signals.update(sub_suggestions)
            time.sleep(0.2)
            
        print(f"   Refined '{seed}': {len(suggestions)} signals ({time.time()-start_t:.2f}s)")
        
    return list(all_signals)

def main():
    # Load fallback if no dynamic seeds
    seeds, source = load_keywords(preferred_sources=("fallback_manual",), return_rich_objects=False)
    
    signals = collect_signals(seeds)
    print(f"✅ Total Signals Captured: {len(signals)}")
    
    save_keywords(signals, source="mercadolivre_autocomplete", prefix="intent_signals")

if __name__ == "__main__":
    main()
