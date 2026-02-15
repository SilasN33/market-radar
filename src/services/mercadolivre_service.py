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
    AUTH_URL = "https://api.mercadolibre.com/oauth/token"

    def __init__(self):
        self.access_token = None
        
        # Load Client ID and Secret (Static)
        self.client_id = os.getenv("ML_CLIENT_ID")
        self.client_secret = os.getenv("ML_CLIENT_SECRET")
        
        # 1. Try to get Refresh Token from DB (Persistent)
        try:
            self.refresh_token = get_config("ML_REFRESH_TOKEN")
        except:
            self.refresh_token = None
            
        # 2. Fallback: Get from ENV (First run / Bootstrap)
        if not self.refresh_token:
            self.refresh_token = os.getenv("ML_REFRESH_TOKEN")
        
        # Fallback to local .env if env vars are missing
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            self._load_env_fallback()
            if not self.client_id: self.client_id = os.getenv("ML_CLIENT_ID")
            if not self.client_secret: self.client_secret = os.getenv("ML_CLIENT_SECRET")
            # Recheck DB/Env for refresh token after loading .env
            if not self.refresh_token:
                self.refresh_token = os.getenv("ML_REFRESH_TOKEN")
            
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            logger.warning("⚠️ Credentials missing! Please set ML_CLIENT_ID, ML_CLIENT_SECRET, and ML_REFRESH_TOKEN.")
            # We don't raise immediately to allow import, but methods will fail.

    def _load_env_fallback(self):
        """Load .env file manually without external dependencies."""
        env_path = Path(__file__).resolve().parents[2] / ".env"
        if env_path.exists():
            logger.info("Loading credentials from local .env file...")
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"): continue
                        if "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip("'").strip('"')
                            if key and not os.getenv(key):
                                os.environ[key] = value
            except Exception as e:
                logger.error(f"Failed to load .env file: {e}")

    def authenticate(self):
        """Exchange refresh_token for a new access_token."""
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise ValueError("Cannot authenticate: Missing credentials.")

        logger.info("🔄 Refreshing Access Token...")
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token
        }
        
        try:
            response = requests.post(self.AUTH_URL, data=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            self.access_token = data["access_token"]
            
            # Handle Token Rotation
            new_refresh = data.get("refresh_token")
            if new_refresh:
                self.refresh_token = new_refresh
                # Persist to DB for next run
                try:
                    set_config("ML_REFRESH_TOKEN", new_refresh)
                    logger.info("💾 New Refresh Token saved to DB.")
                except Exception as db_err:
                    logger.error(f"Failed to persist token: {db_err}")
            
            logger.info("✅ Authentication successful (Token Refreshed)")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Authentication failed: {e}")
            if e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    def search_products(self, keyword_obj: Dict, limit: int = 50) -> List[Dict[str, Any]]:
        """Search products using the API."""
        term = keyword_obj.get("term", "")
        if not term: return []
        
        if not self.access_token:
            self.authenticate()

        logger.info(f"🔎 API Search: '{term}'")
        
        url = f"{self.API_URL}/sites/MLB/search"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        params = {
            "q": term,
            "limit": limit,
            # We can add explicit filters if needed
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
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results", [])
            processed_results = []
            
            negatives = keyword_obj.get("negatives", [])
            
            for item in results:
                adapted = self._adapt_product(item, negatives)
                if adapted:
                    processed_results.append(adapted)
            
            return processed_results

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Search Error for '{term}': {e}")
            return []

    def _adapt_product(self, item: Dict, negatives: List[str]) -> Optional[Dict]:
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
            seller_name = seller.get("nickname", "Mercado Livre Seller") # Default if nickname missing
            
            # API doesn't always perform well with reviews in search endpoint
            # We default to 0 to avoid N+1 calls
            rating = 0.0 
            reviews_count = 0
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "mercadolivre_api",
                "search_keyword": item.get("domain_id", "unknown"), # Can also use the search term
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
    """Main entrypoint for fetching products."""
    
    # Load keywords
    keywords, source = load_keywords(
        preferred_sources=("intent_clusters", "mercadolivre_trends"),
        return_rich_objects=True
    )
    
    if not keywords:
        logger.warning("No keywords found.")
        return []
        
    target_keywords = []
    if isinstance(keywords[0], str):
        target_keywords = [{"term": k} for k in keywords[:max_keywords]]
    else:
        target_keywords = keywords[:max_keywords]

    service = MercadoLivreService()
    
    try:
        service.authenticate()
    except Exception as e:
        logger.error(f"CRITICAL: Authentication failed. Aborting. {e}")
        return []

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
                # Inject correct keyword since _adapt_product doesn't have it easily
                p["search_keyword"] = term 
                upsert_product(p, term)
        else:
            print(f"❌ 0")
            
        time.sleep(0.5) # Gentle rate limit

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
