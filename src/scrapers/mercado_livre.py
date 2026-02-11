"""Fetch products from Mercado Livre using web scraping."""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

import requests
from bs4 import BeautifulSoup

# Corrected Imports for V2 Module
from src.utils.keyword_utils import load_keywords
from src.database import init_db, upsert_product

# Path adjustment: src/scrapers -> parents[2] root
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}


def get_keywords(max_keywords: int) -> List[Dict]:
    """Carregar keywords priorizando tendências."""
    keywords, source = load_keywords(
        preferred_sources=("intent_clusters", "mercadolivre_trends"),
        return_rich_objects=True
    )
    # Convert list of strings to dicts if needed
    if keywords and isinstance(keywords[0], str):
        return [{"term": k} for k in keywords[:max_keywords]]
    return keywords[:max_keywords]


def scrape_mercadolivre(keyword_obj: Dict, limit: int = 10) -> List[Dict[str, Any]]:
    """Fazer scraping do Mercado Livre com suporte a V2 fields (reviews, seller)."""
    keyword = keyword_obj.get("term", "")
    min_price = keyword_obj.get("price_min", 0)
    max_price = keyword_obj.get("price_max", 0)
    negatives = keyword_obj.get("negatives", [])
    
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://lista.mercadolivre.com.br/{encoded_keyword}"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        
        if resp.status_code != 200:
            return []
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Determine layout
        items = soup.find_all('li', class_='ui-search-layout__item')
        if not items:
            items = soup.find_all('div', class_='ui-search-result__wrapper')
            
        results = []
        soft_min = min_price * 0.8
        soft_max = max_price * 1.5 if max_price else float('inf')
        
        for item in items:
            if len(results) >= limit:
                break
                
            title_elem = item.select_one("h2.ui-search-item__title")
            link_elem = item.select_one("a.ui-search-link")
            price_elem = item.select_one(".ui-search-price__part-without-link") or item.select_one(".price-tag-fraction")
            thumb_elem = item.select_one("img")
            shipping_elem = item.find(string=lambda t: isinstance(t, str) and "frete" in t.lower())
            
            # --- V2 FIELDS ---
            rating_elem = item.select_one(".ui-search-reviews__rating-number")
            reviews_elem = item.select_one(".ui-search-reviews__amount")
            seller_elem = item.select_one(".ui-search-official-store-label") or item.select_one(".poly-component__brand")

            title = title_elem.get_text(strip=True) if title_elem else None
            link = link_elem["href"] if link_elem and link_elem.has_attr("href") else None
            
            price = None
            if price_elem:
                price_text = price_elem.get_text(strip=True).replace(".", "").replace(",", ".")
                try: price = float(price_text)
                except: pass
            
            if not title or not link or not price:
                continue

            # Filtering
            if negatives:
                if any(neg.lower() in title.lower() for neg in negatives):
                    continue
            
            if price < soft_min or (max_price > 0 and price > soft_max):
                continue
            
            # Extract V2 Data
            rating = 0.0
            if rating_elem:
                try: rating = float(rating_elem.get_text(strip=True))
                except: pass
                
            reviews = 0
            if reviews_elem:
                try: reviews = int(reviews_elem.get_text(strip=True).replace("(", "").replace(")", ""))
                except: pass
            
            seller = seller_elem.get_text(strip=True) if seller_elem else "Mercado Livre Seller"

            results.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "mercadolivre_scraping",
                "search_keyword": keyword,
                "title": title,
                "price": price,
                "permalink": link,
                "thumbnail": thumb_elem.get("data-src", thumb_elem.get("src", "")) if thumb_elem else "",
                "free_shipping": bool(shipping_elem and "grátis" in shipping_elem.lower()),
                "rating": rating,
                "reviews_count": reviews,
                "seller_name": seller,
            })
        
        return results

    except Exception:
        return []


def fetch_products(max_keywords: int = 15, products_per_keyword: int = 6) -> List[Dict[str, Any]]:
    """Buscar produtos no Mercado Livre."""
    keywords = get_keywords(max_keywords)
    
    if not keywords:
        return []
    
    all_products = []
    
    for idx, kw_obj in enumerate(keywords, 1):
        keyword = kw_obj.get("term")
        print(f"[{idx}] ML '{keyword}'...", end=" ")
        
        products = scrape_mercadolivre(kw_obj, limit=products_per_keyword)
        all_products.extend(products)
        
        if products:
             print(f"✅ {len(products)} produtos")
             # Salvar no DB v2
             for p in products:
                 upsert_product(p, keyword)
        else:
             print(f"❌ 0")
        
        if idx % 5 == 0:
            time.sleep(1)
    
    return all_products


def save_payload(payload: List[Dict[str, Any]], output: Path | None = None) -> Path:
    if output is None:
        output = DATA_DIR / f"mercado_livre-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        
    # Also save as latest for pipeline pickup
    latest = DATA_DIR / "mercado_livre-latest.json"
    
    with output.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)
        
    with latest.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)
        
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch ML products")
    parser.add_argument("--max-keywords", type=int, default=10)
    parser.add_argument("--products-per-keyword", type=int, default=6)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    # Ensure DB is ready
    init_db()

    payload = fetch_products(
        max_keywords=args.max_keywords,
        products_per_keyword=args.products_per_keyword
    )
    path = save_payload(payload, args.output)
    print(f"\n✅ ML salvo em {path} ({len(payload)} itens)")


if __name__ == "__main__":
    main()
