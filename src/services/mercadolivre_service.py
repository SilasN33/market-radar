"""
Mercado Livre Service - Official API Implementation
Replaces scraping with robust API calls using OAuth2 authentication.
"""
import os
import json
import logging
import requests
import argparse
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

# Local imports
from src.utils.keyword_utils import load_keywords
from src.database import init_db, upsert_product, get_config, set_config

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

class MercadoLivreService:
    """Service to interact with Mercado Livre using the Official API."""
    
    API_URL = "https://api.mercadolibre.com"

    def __init__(self):
        # We don't need auth for public search/trends to avoid 403
        pass

    def get_trends(self, category_id: str = "MLB1051", limit: int = 10) -> List[str]:
        """
        Fetch current market trends (Most searched terms) from Mercado Livre API.
        Default Category: MLB1051 (Celulares e Telefones), or use 'MLB' for generic.
        NOTE: 'MLB' generic trends endpoint is deprecated or restricted, so we rotate sensible categories.
        """
        # List of hot categories to rotate: Electronics, Beauty, Home, Tools
        categories = ["MLB1051", "MLB1000", "MLB1574", "MLB1648", "MLB5672"] 
        all_trends = []
        
        import random
        selected_cats = random.sample(categories, 2) # Pick 2 random categories each run
        
        logger.info(f"📈 Fetching Real-Time Trends from Categories: {selected_cats}")

        for cat in selected_cats:
            url = f"{self.API_URL}/sites/MLB/trends/search?category={cat}"
            try:
                # Public API call - No Auth Header needed
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    trends = [t.get("keyword") for t in response.json() if t.get("keyword")]
                    all_trends.extend(trends[:limit])
                else:
                    logger.warning(f"Failed to fetch trends for {cat}: {response.status_code}")
            except Exception as e:
                logger.error(f"Error fetching trends: {e}")
        
        # Deduplicate
        return list(set(all_trends))


    def search_products(self, keyword_obj: Dict, limit: int = 50) -> List[Dict[str, Any]]:
        """Search products using the PUBLIC API (Anonymous to avoid 403)."""
        term = keyword_obj.get("term", "")
        if not term: return []
        
        logger.info(f"🔎 API Search: '{term}'")
        
        url = f"{self.API_URL}/sites/MLB/search"
        
        # NO AUTH HEADERS for public search to avoid 403 Forbidden on standard tokens
        params = {
            "q": term,
            "limit": limit,
        }
        
        # Apply Price Filters
        p_min = keyword_obj.get("price_min")
        p_max = keyword_obj.get("price_max")
        
        if p_min is not None and p_max is not None:
            params["price_range"] = f"{p_min}-{p_max}"
        elif p_min is not None:
             params["price_range"] = f"{p_min}-*"
        elif p_max is not None:
             params["price_range"] = f"*-{p_max}"

        try:
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 403:
                logger.error(f"❌ 403 Forbidden. The API blocked the request. Try reducing rate.")
                return []
                
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results", [])
            processed_results = []
            
            negatives = keyword_obj.get("negatives", [])
            
            for item in results:
                adapted = self._adapt_product(item, negatives, term)
                if adapted:
                    processed_results.append(adapted)
            
            return processed_results

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Search Error for '{term}': {e}")
            return []

    def _adapt_product(self, item: Dict, negatives: List[str], search_term: str) -> Optional[Dict]:
        """Convert API response to project dictionary format."""
        try:
            title = item.get("title")
            price = item.get("price")
            permalink = item.get("permalink")
            thumbnail = item.get("thumbnail")
            
            if not all([title, price, permalink]):
                return None
                
            # Filter Negatives
            if negatives and any(n.lower() in title.lower() for n in negatives):
                return None

            # Extra Fields
            shipping = item.get("shipping", {})
            free_shipping = shipping.get("free_shipping", False)
            
            seller = item.get("seller", {})
            seller_name = seller.get("nickname", "Mercado Livre Seller")
            
            # Reviews (API doesn't return full reviews in search, we use dummy or scrape details if needed)
            rating = 0.0 
            reviews_count = 0
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "mercadolivre_api",
                "search_keyword": search_term, 
                "marketplace": "Mercado Livre",
                "title": title,
                "price": float(price),
                "permalink": permalink,
                "thumbnail": thumbnail,
                "free_shipping": free_shipping,
                "rating": rating,
                "reviews_count": reviews_count,
                "seller_name": str(seller_name)
            }
        except Exception:
            return None


def fetch_products(max_keywords: int = 15, products_per_keyword: int = 6, output: Optional[Path] = None):
    """Main entrypoint: Auto-discover Trends -> Fetch Products."""
    
    service = MercadoLivreService()
    
    # 1. AUTONOMOUS DISCOVERY: Get Real Trends from API
    logger.info("🚀 Starting Trend Discovery (API)...")
    trends = service.get_trends(limit=max_keywords)
    
    if not trends:
        logger.warning("⚠️ No trends found from API. Falling back to internal list.")
        trends = ["Smartwatch", "Fones Bluetooth", "Projetor", "Câmera de Segurança"]
    else:
        logger.info(f"🔥 Hot Trends Discovered: {trends[:5]}...")

    # Convert to keyword objects
    target_keywords = [{"term": t} for t in trends]
    
    all_products = []
    
    for idx, kw_obj in enumerate(target_keywords, 1):
        term = kw_obj.get("term")
        print(f"[{idx}/{len(target_keywords)}] API '{term}'...", end=" ", flush=True)
        
        products = service.search_products(kw_obj, limit=products_per_keyword)
        
        if products:
            print(f"✅ {len(products)} found")
            all_products.extend(products)
            
            # Upsert to DB
            for p in products:
                upsert_product(p, term)
        else:
            print(f"❌ 0")
            
        time.sleep(1.0) # Respect Public API Rate Limits

    # Save results
    if output is None:
        output = DATA_DIR / f"mercado_livre-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    
    latest = DATA_DIR / "mercado_livre-latest.json"
    
    try:
        with output.open("w", encoding="utf-8") as fp:
            json.dump(all_products, fp, ensure_ascii=False, indent=2)
        
        with latest.open("w", encoding="utf-8") as fp:
            json.dump(all_products, fp, ensure_ascii=False, indent=2)
            
        print(f"\n✅ Results saved to {output}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")

    return all_products


def main():
    """CLI execution wrapper."""
    parser = argparse.ArgumentParser(description="Fetch ML products using Official API")
    parser.add_argument("--max-keywords", type=int, default=10)
    parser.add_argument("--products-per-keyword", type=int, default=6)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    # Ensure DB is ready
    try:
        init_db()
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")

    fetch_products(
        max_keywords=args.max_keywords,
        products_per_keyword=args.products_per_keyword,
        output=args.output
    )


if __name__ == "__main__":
    main()
