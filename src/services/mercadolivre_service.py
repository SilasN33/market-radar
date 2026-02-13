"""
Mercado Livre Service - Browser Automation Implementation
Uses Playwright with stealth techniques to bypass WAF protections.
"""
import asyncio
import argparse
import random
import json
import logging
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from playwright.async_api import async_playwright, Page, BrowserContext
from playwright_stealth import stealth_async

# Local imports
from src.utils.keyword_utils import load_keywords
from src.database import init_db, upsert_product

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/121.0.0.0 Safari/537.36",
]


class MercadoLivreService:
    """Service to interact with Mercado Livre using Browser Automation."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.playwright = None

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        
        # Launch browser with arguments to improve stealth
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ]
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    suspend_timer = 0
    
    async def _create_context(self) -> BrowserContext:
        """Create a new browser context with stealth settings."""
        user_agent = random.choice(USER_AGENTS)
        viewport = {"width": 1920, "height": 1080}
        
        context = await self.browser.new_context(
            user_agent=user_agent,
            viewport=viewport,
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            permissions=["geolocation"],
        )
        
        # Apply stealth scripts
        page = await context.new_page()
        await stealth_async(page)
        await page.close()
        
        return context

    async def search_products(self, keyword_obj: Dict, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for products on Mercado Livre using the provided keyword object.
        Supports filtering by price and negative keywords.
        """
        keyword = keyword_obj.get("term", "")
        min_price = keyword_obj.get("price_min", 0)
        max_price = keyword_obj.get("price_max", 0)
        negatives = keyword_obj.get("negatives", [])
        
        encoded_keyword = urllib.parse.quote(keyword)
        url = f"https://lista.mercadolivre.com.br/{encoded_keyword}"
        
        results = []
        context = await self._create_context()
        page = await context.new_page()
        
        try:
            # Navigate with retry logic
            for attempt in range(3):
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    break
                except Exception as e:
                    if attempt == 2:
                        logger.error(f"Failed to load {url}: {e}")
                        return []
                    await asyncio.sleep(2 * (attempt + 1))

            # Handle cookie consent if present
            try:
                cookie_btn = page.locator("button[data-testid='action:understood-button']")
                if await cookie_btn.is_visible(timeout=2000):
                    await cookie_btn.click()
            except:
                pass

            # Wait for items to load
            try:
                # Try multiple selectors for item lists
                await page.wait_for_selector("li.ui-search-layout__item, div.ui-search-result__wrapper", timeout=10000)
            except:
                logger.warning(f"No results found for '{keyword}'")
                return []

            # Extract items
            items = await page.locator("li.ui-search-layout__item, div.ui-search-result__wrapper").all()
            
            soft_min = min_price * 0.8
            soft_max = max_price * 1.5 if max_price else float('inf')
            
            for item in items:
                if len(results) >= limit:
                    break
                
                try:
                    # Extract basic info
                    title_el = item.locator("h2.ui-search-item__title")
                    link_el = item.locator("a.ui-search-link")
                    price_el = item.locator(".ui-search-price__part-without-link, .price-tag-fraction").first
                    
                    if not await title_el.is_visible():
                        continue
                        
                    title = await title_el.text_content()
                    link = await link_el.get_attribute("href")
                    
                    price_text = await price_el.text_content()
                    try:
                        price = float(price_text.replace(".", "").replace(",", "."))
                    except:
                        price = 0.0

                    if not title or not link or not price:
                        continue

                    # Filtering
                    if negatives:
                        if any(neg.lower() in title.lower() for neg in negatives):
                            continue
                    
                    if price < soft_min or (max_price > 0 and price > soft_max):
                        continue

                    # Extract V2 Data (Seller, Rating, Reviews)
                    seller = "Mercado Livre Seller"
                    seller_el = item.locator(".ui-search-official-store-label, .poly-component__brand").first
                    if await seller_el.is_visible():
                        seller = await seller_el.text_content()

                    rating = 0.0
                    rating_el = item.locator(".ui-search-reviews__rating-number").first
                    if await rating_el.is_visible():
                        try:
                            rating = float(await rating_el.text_content())
                        except: pass

                    reviews = 0
                    reviews_el = item.locator(".ui-search-reviews__amount").first
                    if await reviews_el.is_visible():
                        try:
                            # Text format: (123)
                            rev_text = await reviews_el.text_content()
                            reviews = int(rev_text.replace("(", "").replace(")", "").strip())
                        except: pass
                    
                    # Image
                    thumb_url = ""
                    img_el = item.locator("img").first
                    if await img_el.is_visible():
                        thumb_url = await img_el.get_attribute("src") or ""

                    # Free Shipping
                    is_free_shipping = False
                    shipping_el = item.locator("text=frete grátis").first
                    if await shipping_el.count() > 0:
                        is_free_shipping = True

                    results.append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "source": "mercadolivre_scraping",
                        "search_keyword": keyword,
                        "title": title.strip(),
                        "price": price,
                        "permalink": link,
                        "thumbnail": thumb_url,
                        "free_shipping": is_free_shipping,
                        "rating": rating,
                        "reviews_count": reviews,
                        "seller_name": seller.strip(),
                    })
                    
                except Exception as e:
                    # Skip problematic items without crashing
                    continue

        except Exception as e:
            logger.error(f"Error scraping '{keyword}': {e}")
        finally:
            await page.close()
            await context.close()
            
        return results


async def fetch_products_async(max_keywords: int = 15, products_per_keyword: int = 6, output: Optional[Path] = None):
    """Main async entrypoint for fetching products."""
    
    # Load keywords
    keywords, source = load_keywords(
        preferred_sources=("intent_clusters", "mercadolivre_trends"),
        return_rich_objects=True
    )
    
    # Normalize keywords to list of dicts
    target_keywords = []
    if keywords:
        if isinstance(keywords[0], str):
            target_keywords = [{"term": k} for k in keywords[:max_keywords]]
        else:
            target_keywords = keywords[:max_keywords]
    
    if not target_keywords:
        logger.warning("No keywords found.")
        return []

    logger.info(f"Starting scraping for {len(target_keywords)} keywords. Source: {source}")
    
    all_products = []
    
    async with MercadoLivreService(headless=True) as service:
        for idx, kw_obj in enumerate(target_keywords, 1):
            term = kw_obj.get("term")
            print(f"[{idx}/{len(target_keywords)}] ML '{term}'...", end=" ", flush=True)
            
            products = await service.search_products(kw_obj, limit=products_per_keyword)
            
            if products:
                print(f"✅ {len(products)} found")
                all_products.extend(products)
                # Helper to upsert to DB immediately
                for p in products:
                    try:
                        upsert_product(p, term)
                    except Exception as db_err:
                         logger.error(f"DB Error: {db_err}")
            else:
                 print(f"❌ 0")
            
            # Small random delay to avoid aggressive rate limiting
            await asyncio.sleep(random.uniform(1.0, 3.0))

    # Save results to disk
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
    """Sync wrapper for CLI execution."""
    parser = argparse.ArgumentParser(description="Fetch ML products using Playwright")
    parser.add_argument("--max-keywords", type=int, default=10)
    parser.add_argument("--products-per-keyword", type=int, default=6)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    # Ensure DB is ready
    try:
        init_db()
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")

    asyncio.run(fetch_products_async(
        max_keywords=args.max_keywords,
        products_per_keyword=args.products_per_keyword,
        output=args.output
    ))


if __name__ == "__main__":
    main()
