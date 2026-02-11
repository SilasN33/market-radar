"""
Marketplace Intent Signal Layer.
Aggregates keywords ONLY from:
1) Marketplace Search Autocomplete (Direct Intent)
2) Marketplace Internal Trends (Confirmed Demand)
3) New Listings Detection (Seller Behavior)
4) Recent Reviews Analysis (Problem Identification)
"""
import argparse
import json
import time
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Set, Any
import random

# Shared utils
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from keyword_utils import save_keywords

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Referer": "https://www.mercadolivre.com.br/",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

# 1. Autocomplete Seeds (Expanded for extraction)
# "seeds" to trigger autocomplete, not the final keywords.
INTENT_SEEDS = [
    "melhor", "novo", "comprar", "kit", "promoção", "oferta", 
    "lancamento", "tendencia", "mais vendido", "barato", "review",
    "como usar", "para que serve", "qual o melhor", 
    "smartphone", "fone", "casa", "cozinha", "gamer", "beleza", 
    "ferramentas", "moda", "bebe", "esporte", "pet", "acessorios"
]

class MarketplaceSignals:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.signals = []
        self.seen_terms = set()

    def add_signal(self, term: str, source: str, meta: Dict[str, Any] = None):
        """Add a unique validated signal."""
        clean_term = term.strip().lower()
        if not clean_term or len(clean_term) < 3:
            return
        
        # Deduplication strategy
        if clean_term in self.seen_terms:
            return
        
        self.seen_terms.add(clean_term)
        self.signals.append({
            "term": term.strip(), # Keep original case for display
            "source": source,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "meta": meta or {}
        })

    # --- SOURCE 1: Autocomplete (Direct Intent) ---
    def fetch_autocomplete(self, seed: str):
        """Fetch real-time autocomplete suggestions."""
        url = "https://http2.mlstatic.com/resources/sites/MLB/autosuggest"
        params = {"show_category": "true", "q": seed, "limit": 10}
        
        try:
            resp = self.session.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("suggested_queries", [])
                for item in items:
                    q = item.get("q")
                    if q:
                        self.add_signal(q, "autocomplete", {"seed": seed})
        except Exception as e:
            print(f"[warn] Autocomplete failed for '{seed}': {e}")

    # --- SOURCE 2: Internal Trends (Confirmed Demand) ---
    def fetch_internal_trends(self):
        """Scrape 'Mais Vendidos' pages."""
        print("   Checking Internal Trends (Mais Vendidos)...")
        # ML BR High Volume Categories
        urls = [
            "https://www.mercadolivre.com.br/mais-vendidos/MLB1051", # Celulares
            "https://www.mercadolivre.com.br/mais-vendidos/MLB5726", # Eletrodomesticos
            "https://www.mercadolivre.com.br/mais-vendidos/MLB1648", # Informatica
            "https://www.mercadolivre.com.br/mais-vendidos/MLB1144", # Games
            "https://www.mercadolivre.com.br/mais-vendidos/MLB1246", # Beleza
        ]
        
        for url in urls:
            try:
                resp = self.session.get(url, timeout=10)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    # Updated selectors for new ML layout
                    items = soup.select('a.ui-recommendations-card__link') or \
                            soup.select('p.ui-recommendations-card__title')
                    
                    count = 0
                    for item in items[:15]:
                        text = item.get_text(strip=True)
                        if text:
                            self.add_signal(text, "internal_trends", {"url": url})
                            count += 1
                    print(f"      -> Found {count} trends in {url.split('/')[-1]}")
                time.sleep(1) # Politeness
            except Exception as e:
                print(f"[warn] Trends scrape failed: {e}")

    # --- SOURCE 3: New Listings (Seller Behavior) ---
    def fetch_new_listings_signals(self, query="lancamento"):
        """
        Analyze recent listings to see what sellers are betting on.
        Uses the 'Novo' tag or 'Ordem: Mais Recentes' logic if available.
        """
        print(f"   Analyzing New Listings for '{query}'...")
        # Sort by: relevant (default) but looking for 'Novo' tags
        url = f"https://lista.mercadolivre.com.br/{query}_NoIndex_True" 
        
        try:
            resp = self.session.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Look for items with "Novo" status logic if possible (usually hidden in ML now)
            # Instead, we look for items that are distinct in specific niches
            items = soup.select('.ui-search-layout__item')
            
            count = 0
            for item in items[:15]:
                title_el = item.select_one('.ui-search-item__title')
                if not title_el: continue
                title = title_el.get_text(strip=True)
                
                # Check for "Novo" condition if visible
                condition = item.select_one('.ui-search-item__group__element--condition')
                is_new = condition and "novo" in condition.get_text().lower()
                
                # We interpret "New Listing" signals as items that appear in "lancamento" searches
                # and explicitly look "New" (no reviews/sold count low but nice presentation).
                
                sold_el = item.select_one('.ui-search-item__group__element--quantity')
                sold_text = sold_el.get_text() if sold_el else ""
                
                # Use simplified heuristic: Title + "Novo" is a signal of seller intent
                self.add_signal(title, "new_listing", {"query": query, "is_new_condition": is_new})
                count += 1
                
            print(f"      -> Extracted {count} listing titles")
            
        except Exception as e:
            print(f"[warn] New listings scrape failed: {e}")

    # --- SOURCE 4: Recent Reviews (Problem Analysis) ---
    def fetch_review_problems(self):
        """
        Mock/Light version: Scrapes review snippets from a few popular items 
        to capture problem-based language ('ruim', 'quebrou', 'melhoraria').
        """
        print("   Mining Review Sentiment (Simulated/Light)...")
        # In a full production run, we would visit product pages. 
        # For this pass, we will look for 'review' related keywords in autocomplete
        # as a proxy for what people are complaining/asking about.
        
        # Real review scraping is heavy (IP blocks). 
        # Strategy: Use autocomplete for negative intents.
        negative_seeds = ["reclame aqui", "defeito", "problema", "nao funciona", "ruim"]
        for seed in negative_seeds:
            self.fetch_autocomplete(seed)
            
    def run(self, seeds: List[str] = None):
        print("🚀 Starting Marketplace Intent Signal Layer...")
        
        # 1. Autocomplete (The broadest net)
        target_seeds = seeds or INTENT_SEEDS
        print(f"   Step 1: Autocomplete ({len(target_seeds)} seeds)...")
        for seed in target_seeds:
            self.fetch_autocomplete(seed)
            # Add a-z expansion for the first few seeds to get 'long tail'
            if seed in target_seeds[:3]:
                for char in "abcdefghijklmnopqrstuvwxyz"[::4]: # skip some for speed
                    self.fetch_autocomplete(f"{seed} {char}")
            time.sleep(0.2)
            
        # 2. Internal Trends
        print(f"   Step 2: Internal Trends...")
        self.fetch_internal_trends()
        
        # 3. New Listings
        print(f"   Step 3: Seller Behavior (New Listings)...")
        self.fetch_new_listings_signals("lancamento 2026")
        self.fetch_new_listings_signals("novidade")
        
        # 4. Reviews (Problem mining)
        print(f"   Step 4: Problem Mining...")
        self.fetch_review_problems()
        
        return self.signals

def main():
    parser = argparse.ArgumentParser(description="Collect Marketplace Intent Signals")
    parser.add_argument("--seeds", type=str, help="Comma-separated seed terms")
    args = parser.parse_args()
    
    seeds = [s.strip() for s in args.seeds.split(",") if s.strip()] if args.seeds else None
    
    miner = MarketplaceSignals()
    signals = miner.run(seeds)
    
    # Save Report
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output_path = DATA_DIR / f"intent_signals-{timestamp}.json"
    
    try:
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(signals, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Captured {len(signals)} VALIDATED Intent Signals.")
        print(f"📁 Saved to: {output_path}")
    except Exception as e:
        print(f"[error] Failed to save signals: {e}")

if __name__ == "__main__":
    main()
