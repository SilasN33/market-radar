"""Collect real-time market signals from Mercado Livre Offers & Trends."""
import json
import requests
import random
import time
from datetime import datetime
from pathlib import Path
from typing import List
from bs4 import BeautifulSoup

from src.utils.keyword_utils import save_keywords

# Path adjustment
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 1. Offers Page (Rich Source)
URL_OFFERS = "https://www.mercadolivre.com.br/ofertas"

# 2. Best Sellers (Trends)
URL_TRENDS = "https://www.mercadolivre.com.br/mais-vendidos"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.mercadolivre.com.br/",
}

def extract_json_ld(soup) -> List[str]:
    """Extract product names from JSON-LD structured data (Hidden Gold Mine)."""
    titles = []
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            data = json.loads(script.string)
            # Schema.org/ItemList
            if data.get('@type') == 'ItemList':
                items = data.get('itemListElement', [])
                for item in items:
                    name = item.get('name') or item.get('item', {}).get('name')
                    if name: titles.append(name)
            
            # Schema.org/Product
            if data.get('@type') == 'Product':
                if data.get('name'): titles.append(data['name'])
                
        except: continue
    return titles

def scrape_real_signals() -> List[str]:
    """Scrape real offers and trends using robust headers and JSON-LD."""
    signals = []
    
    # Strategy 1: Offers Page
    print(f"🔥 Fetching Real Offers (Deals)...")
    try:
        resp = requests.get(URL_OFFERS, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 1. Try JSON-LD first (Most reliable)
            ld_titles = extract_json_ld(soup)
            signals.extend(ld_titles)
            
            # 2. Try CSS Selectors for Offer Cards
            # Targets: promotion-item__title, poly-component__title
            for cls in ["promotion-item__title", "poly-component__title", "ui-search-item__title"]:
                for el in soup.select(f".{cls}"):
                    signals.append(el.get_text(strip=True))
                    
    except Exception as e:
        print(f"❌ Error fetching offers: {e}")

    # Strategy 2: Trends Page
    print(f"📈 Fetching Best Sellers...")
    try:
        resp = requests.get(URL_TRENDS, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # JSON-LD
            signals.extend(extract_json_ld(soup))
            
            # Carousel Titles
            for el in soup.select(".ui-recommendations-card__title"):
                signals.extend([el.get_text(strip=True)])
                
            # Links inside carousels (often just the text)
            for link in soup.select("a.ui-recommendations-card__link"):
                signals.append(link.get_text(strip=True))
                
    except Exception as e:
        print(f"❌ Error fetching trends: {e}")

    # Cleaning
    # Remove nonsense, too short, or duplicates
    clean_signals = []
    seen = set()
    for s in signals:
        s = s.strip()
        if len(s) < 4 or len(s) > 100: continue
        if "frete" in s.lower() or "envio" in s.lower(): continue
        
        # Normalize simple keys to dedup
        key = s.lower()
        if key not in seen:
            seen.add(key)
            clean_signals.append(s)

    return clean_signals[:60] # Return top 60 unique real signals

def main():
    print("🚀 signal_collector: Starting Deep Signal Harvest...")
    
    trends = scrape_real_signals()
    
    if not trends:
        print("⚠️  Scraping blocked. Using Emergency Backup List (Last Resort).")
        # Backup list only if absolutely everything fails
        trends = [
            "Projetor HY300", "Fone Lenovo GM2 Pro", "Garrafa Pacco", 
            "Copo Stanley", "Mapache Pelúcia", "Câmera Lâmpada",
            "Mini Processador", "Umidificador Chama", "Faca Tática",
            "Smartwatch W29 Pro"
        ]
    else:
        print(f"✅ Success! Captured {len(trends)} REAL market signals.")
        print(f"� Examples: {trends[:5]}")
    
    print(f"💾 Saving to pipeline...")
    save_keywords(trends, source="mercadolivre_trends", prefix="intent_signals")

if __name__ == "__main__":
    main()
