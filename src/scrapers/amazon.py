"""Fetch products from Amazon BR using web scraping."""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

import requests
from bs4 import BeautifulSoup

# Imports Clean Architecture
from src.utils.keyword_utils import load_keywords
from src.database import init_db, upsert_product

# Path adjustment: src/scrapers -> parents[2] root
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Headers para simular navegador real
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}


def get_keywords(max_keywords: int) -> List[Dict]:
    """Carregar keywords priorizando tendências."""
    keywords, source = load_keywords(
        preferred_sources=("intent_clusters", "mercadolivre_trends"),
        return_rich_objects=True
    )
    if keywords and isinstance(keywords[0], str):
         return [{"term": k} for k in keywords[:max_keywords]]
    return keywords[:max_keywords]


def scrape_amazon(keyword_obj: Dict, limit: int = 10) -> List[Dict[str, Any]]:
    """Fazer scraping da Amazon BR com filtragem."""
    keyword = keyword_obj.get("term", "")
    min_price = keyword_obj.get("price_min", 0)
    max_price = keyword_obj.get("price_max", 0)
    negatives = keyword_obj.get("negatives", [])
    
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://www.amazon.com.br/s?k={encoded_keyword}&s=relevanceblender"
    
    try:
        session = requests.Session()
        resp = session.get(url, headers=HEADERS, timeout=15)
        
        if resp.status_code != 200:
            return []
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        items = soup.find_all('div', {'data-component-type': 's-search-result'})
        
        results = []
        soft_min = min_price * 0.8 if min_price else 0
        soft_max = max_price * 1.5 if max_price else float('inf')
        
        for item in items:
            if len(results) >= limit:
                break
                
            try:
                # Título
                title_elem = item.find('h2', class_='s-line-clamp-2') or item.find('span', class_='a-text-normal')
                title = title_elem.get_text(strip=True) if title_elem else "Sem título"
                
                # Preço
                price = 0
                price_whole = item.find('span', class_='a-price-whole')
                if price_whole:
                    try: price = float(price_whole.get_text(strip=True).replace('.', '').replace(',', '.'))
                    except: price = 0
                
                # Link
                link_elem = item.find('a', class_='a-link-normal')
                link = ("https://www.amazon.com.br" + link_elem['href']) if link_elem else ""
                
                # Thumbnail
                img_elem = item.find('img', class_='s-image')
                thumbnail = img_elem.get('src', '') if img_elem else ""
                
                # Rating
                rating = 0.0
                rating_elem = item.find('span', class_='a-icon-alt')
                if rating_elem:
                    match = re.search(r'([\d,]+)', rating_elem.get_text(strip=True))
                    if match:
                        try: rating = float(match.group(1).replace(',', '.'))
                        except: pass

                # V2: Reviews Count
                reviews = 0
                review_elem = item.find('span', class_='a-size-base s-underline-text')
                if review_elem:
                    try: reviews = int(review_elem.get_text(strip=True).replace('.', '').replace(',', ''))
                    except: pass
                
                # V2: Seller (Placeholder)
                seller = "Amazon Seller" 

                # Filtros
                if negatives and any(n.lower() in title.lower() for n in negatives):
                    continue
                if price and (price < soft_min or (max_price > 0 and price > soft_max)):
                    continue

                results.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": "amazon_br_scraping",
                    "search_keyword": keyword,
                    "title": title,
                    "price": price,
                    "permalink": link,
                    "thumbnail": thumbnail,
                    "rating": rating,
                    "reviews_count": reviews,
                    "seller_name": seller,
                })
                
            except Exception:
                continue
        
        return results
        
    except Exception:
        return []


def fetch_products(max_keywords: int = 15, products_per_keyword: int = 6) -> List[Dict[str, Any]]:
    """Buscar produtos da Amazon."""
    keywords = get_keywords(max_keywords)
    if not keywords: return []
    
    all_products = []
    
    for idx, kw_obj in enumerate(keywords, 1):
        keyword = kw_obj.get("term")
        print(f"[{idx}] Amazon '{keyword}'...", end=" ")
        
        products = scrape_amazon(kw_obj, limit=products_per_keyword)
        all_products.extend(products)
        
        if products:
            print(f"✅ {len(products)} produtos")
            # Salvar no DB v2
            for p in products:
                upsert_product(p, keyword)
        else:
            print(f"❌ 0")
        
        if idx % 5 == 0: time.sleep(2.0)
    
    return all_products


def save_payload(payload: List[Dict[str, Any]], output: Path | None = None) -> Path:
    if output is None:
        output = DATA_DIR / f"amazon-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    
    latest = DATA_DIR / "amazon-latest.json"

    with output.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)
    with latest.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)

    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Amazon BR products")
    parser.add_argument("--max-keywords", type=int, default=10)
    parser.add_argument("--products-per-keyword", type=int, default=6)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    init_db()

    payload = fetch_products(
        max_keywords=args.max_keywords,
        products_per_keyword=args.products_per_keyword
    )
    path = save_payload(payload, args.output)
    print(f"\n✅ Amazon salva em {path} ({len(payload)} itens)")


if __name__ == "__main__":
    main()
