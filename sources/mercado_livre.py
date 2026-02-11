"""Fetch products from Mercado Livre via resilient HTML scraping."""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

from keyword_utils import load_keywords

# IMPORTANT: Import patch BEFORE database to enable Postgres
import database_patch
import database

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
}

REQUEST_TIMEOUT = 15
PAUSE_BETWEEN_KEYWORDS = 1.0


def get_keywords(max_keywords: int) -> List[Dict]:
    keywords, source = load_keywords(
        preferred_sources=("intent_clusters", "mercadolivre_trends", "openai_gpt4o_mini", "fallback_manual"),
        return_rich_objects=True
    )
    print(f"[info] 🔑 {len(keywords)} keywords carregadas da fonte {source}")
    # Handle legacy string-only keywords if source is old
    if keywords and isinstance(keywords[0], str):
         return [{"term": k} for k in keywords][:max_keywords]
    return keywords[:max_keywords]


def scrape_keyword(keyword_obj: Dict, limit: int) -> List[Dict]:
    """Scrape Mercado Livre result page for a keyword with filtering."""
    keyword = keyword_obj.get("term", "")
    min_price = keyword_obj.get("price_min", 0)
    max_price = keyword_obj.get("price_max", 0)
    negatives = keyword_obj.get("negatives", [])
    
    if not keyword:
        return []

    encoded = urllib.parse.quote(keyword)
    url = f"https://lista.mercadolivre.com.br/{encoded}"

    # Retry Logic (Phase 1)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            break # Success
        except requests.RequestException as exc:
            if attempt < max_retries - 1:
                print(f"[warn] Request '{keyword}' failed (Attempt {attempt+1}/{max_retries}). Retrying...")
                time.sleep(2 * (attempt + 1)) # Backoff
            else:
                print(f"[error] Request '{keyword}' failed after {max_retries} attempts: {exc}")
                return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.select(".ui-search-result__wrapper") or soup.select(".andes-card")

    results: List[Dict] = []
    
    # Calculate soft limits (20% tolerance)
    soft_min = min_price * 0.8 if min_price else 0
    soft_max = max_price * 1.5 if max_price else float('inf')

    for item in items:
        # Stop if we hit limit
        if len(results) >= limit:
            break
            
        title_elem = (
            item.select_one(".ui-search-item__title")
            or item.select_one("a.poly-component__title")
            or item.find("h2")
        )
        link_elem = (
            item.select_one("a.ui-search-link")
            or item.select_one("a.poly-component__title")
            or item.find("a", href=True)
        )
        price_elem = (
            item.select_one(".andes-money-amount__fraction")
            or item.select_one(".price-tag-fraction")
            or item.select_one(".poly-price__current .andes-money-amount__fraction")
        )
        thumb_elem = item.select_one("img")
        shipping_elem = item.find(string=lambda t: isinstance(t, str) and "frete" in t.lower())

        title = title_elem.get_text(strip=True) if title_elem else None
        link = link_elem["href"] if link_elem and link_elem.has_attr("href") else None
        price = None
        if price_elem:
            price_text = price_elem.get_text(strip=True).replace(".", "").replace(",", ".")
            try:
                price = float(price_text)
            except ValueError:
                price = None

        if not title or not link:
            continue

        # --- FILTERS ---
        
        # 1. Negative Keywords (e.g. skip "capa" if looking for phone)
        if negatives:
            title_lower = title.lower()
            if any(neg.lower() in title_lower for neg in negatives):
                continue
                
        # 2. Price Filter (if applicable)
        if price and (min_price > 0 or max_price > 0):
             if price < soft_min:
                 continue # Too cheap (likely accessory)
             if max_price > 0 and price > soft_max:
                 continue # Too expensive (maybe wrong product or pack)

        if link.startswith("/"):
            link = f"https://www.mercadolivre.com.br{link}"

        results.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "mercado_livre_scraper",
            "search_keyword": keyword,
            "title": title,
            "price": price,
            "permalink": link,
            "thumbnail": thumb_elem.get("data-src", thumb_elem.get("src", "")) if thumb_elem else "",
            "free_shipping": bool(shipping_elem and "grátis" in shipping_elem.lower()),
        })

    return results


def fetch_products(max_keywords: int = 8, products_per_keyword: int = 6) -> List[Dict]:
    keywords = get_keywords(max_keywords)
    aggregated: List[Dict] = []

    for idx, kw_obj in enumerate(keywords, start=1):
        term = kw_obj.get("term")
        print(f"[{idx}/{len(keywords)}] '{term}'...", end=" ")
        
        items = scrape_keyword(kw_obj, products_per_keyword)
        
        aggregated.extend(items)

        # Persistence (Phase 1)
        try:
            database.init_db()
            for item in items:
                database.upsert_product(item, keyword=term)
        except Exception as e:
            print(f"[warn] DB Save failed for batch '{term}': {e}")
            
        print(f"✅ {len(items)} produtos" if items else "❌ 0 produtos (filtrados)")
        
        if idx < len(keywords):
            time.sleep(PAUSE_BETWEEN_KEYWORDS)

    print(f"\n[success] ✅ Total Mercado Livre: {len(aggregated)} produtos")
    return aggregated


def save_payload(payload: List[Dict], output: Path | None = None) -> Path:
    if output is None:
        output = DATA_DIR / f"mercado_livre-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    with output.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Mercado Livre scraping")
    parser.add_argument("--max-keywords", type=int, default=8)
    parser.add_argument("--products-per-keyword", type=int, default=6)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload = fetch_products(
        max_keywords=args.max_keywords,
        products_per_keyword=args.products_per_keyword,
    )
    path = save_payload(payload, args.output)
    print(f"\n✅ Mercado Livre salvo em {path} ({len(payload)} itens)")


if __name__ == "__main__":
    main()
