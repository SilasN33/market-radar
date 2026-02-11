"""Collect intent signals directly from Market Trends (High Confidence) via Scraping."""
import json
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import List
from bs4 import BeautifulSoup

from src.utils.keyword_utils import save_keywords

# Path adjustment
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Scraping Trends Page (More reliable than hidden API)
ML_TRENDS_PAGE = "https://www.mercadolivre.com.br/mais-vendidos"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

def scrape_ml_trends() -> List[str]:
    """Scrape top selling product titles from Mercado Livre Trends page."""
    print(f"🔥 Scraping Market Trends from: {ML_TRENDS_PAGE}")
    try:
        resp = requests.get(ML_TRENDS_PAGE, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"❌ Failed to load page: {resp.status_code}")
            return []
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Extract titles from "Mais Vendidos" carousels
        # Look for product titles or search terms
        trends = []
        
        # Class names change frequently, look for common patterns
        # Usually inside <a> tags with specific classes or data attributes
        # Strategy: Find all <a> inside carousel items
        
        # Try finding product titles directly
        # Example selector: .ui-recommendations-card__title
        titles = soup.select(".ui-recommendations-card__title")
        if not titles:
            # Fallback to general links that look like products
            titles = soup.select("a.ui-search-item__group__element.ui-search-link__title-card")
            
        if not titles:
             # Fallback 2: Look for 'poly-component__title' (New UI)
             titles = soup.select(".poly-component__title")

        if not titles:
             # Fallback 3: Just look for any H2/H3 that might be a product
             titles = soup.select("h2, h3")

        for t in titles:
            text = t.get_text(strip=True)
            if len(text) > 5 and len(text) < 80: # Filter noise
                trends.append(text)

        # Dedup
        unique_trends = list(set(trends))
        return unique_trends[:50] # Top 50 is enough
        
    except Exception as e:
        print(f"❌ Error scraping trends: {e}")
        return []

def main():
    print("🚀 signal_collector: Starting Trends Scraping...")
    
    trends = scrape_ml_trends()
    
    if not trends:
        print("⚠️  Scraping failed or layout changed. Using fallback specific keywords...")
        trends = [
            "Smartwatch", "Fone Bluetooth", "Câmera de Segurança", 
            "Projetor Portátil", "Garrafa Térmica", "Air Fryer",
            "Power Bank", "Kindle", "Tablet", "Mouse Vertical"
        ]
    
    print(f"✅ Captured {len(trends)} Trends")
    print(f"💾 Saving High-Velocity Signals...")
    
    # Save as 'mercadolivre_trends' so keyword_utils picks it up with priority
    save_keywords(trends, source="mercadolivre_trends", prefix="intent_signals")

if __name__ == "__main__":
    main()
