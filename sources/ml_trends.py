"""Generate product keywords by scraping Mercado Livre category showcases."""
from __future__ import annotations

import argparse
import json
import re
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

from keyword_utils import save_keywords
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MENU_ENDPOINT = "https://www.mercadolivre.com.br/menu/departments"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

DEFAULT_DEPARTMENT_COUNT = 6


def fetch_departments() -> List[dict]:
    resp = requests.get(MENU_ENDPOINT, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json().get("departments", [])


def normalize_link(url: str) -> str:
    url = url.split("#", 1)[0]
    if "lista.mercadolivre" in url:
        return url
    if url.startswith("https://www.mercadolivre.com.br/c/"):
        suffix = url.split("/c/", 1)[-1]
        return f"https://lista.mercadolivre.com.br/{suffix}"
    return url


def category_links(category: dict) -> List[str]:
    links: List[str] = []
    for child in category.get("children_categories", []) or []:
        link = child.get("permalink")
        if link:
            links.append(normalize_link(link))
    if not links and category.get("permalink"):
        links.append(normalize_link(category["permalink"]))
    return links


def clean_keyword(title: str) -> str:
    normalized = re.sub(r"\s+", " ", title).strip()
    return normalized[:80]


def scrape_listing(permalink: str, limit: int) -> List[str]:
    resp = requests.get(permalink, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.select(".ui-search-result__wrapper")
    keywords: List[str] = []
    for item in items[:limit]:
        title_elem = (
            item.select_one(".ui-search-item__title")
            or item.select_one("a.poly-component__title")
            or item.find("h2")
        )
        if not title_elem:
            continue
        title = title_elem.get_text(strip=True)
        if title:
            keywords.append(clean_keyword(title))
    return keywords


def build_keyword_pool(departments: List[dict], target_names: List[str] | None, per_category: int) -> Dict[str, List[str]]:
    pool: Dict[str, List[str]] = {}
    chosen = departments
    if target_names:
        name_lower = {d["name"].lower(): d for d in departments}
        chosen = [name_lower[name.lower()] for name in target_names if name.lower() in name_lower]
    else:
        chosen = departments[:DEFAULT_DEPARTMENT_COUNT]

    for dept in chosen:
        dept_name = dept.get("name", "Desconhecido")
        keywords: List[str] = []
        for category in dept.get("categories", [])[:3]:
            links = category_links(category)[:2]
            for link in links:
                try:
                    keywords.extend(scrape_listing(link, per_category))
                except requests.RequestException as exc:
                    print(f"[warn] Falha ao coletar '{link}': {exc}")
        pool[dept_name] = keywords
        print(f"[info] {dept_name}: {len(keywords)} itens capturados")
    return pool


def dedupe_keywords(pool: Dict[str, List[str]]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for dept_keywords in pool.values():
        for kw in dept_keywords:
            key = kw.lower()
            if key in seen:
                continue
            seen.add(key)
            ordered.append(kw)
    return ordered


def parse_targets(raw: str | None) -> List[str] | None:
    if not raw:
        return None
    return [part.strip() for part in raw.split(",") if part.strip()]


def main():
    parser = argparse.ArgumentParser(description="Gerar keywords a partir das vitrines do Mercado Livre")
    parser.add_argument("--departments", type=str, help="Lista de departamentos separados por vírgula")
    parser.add_argument("--per-category", type=int, default=8)
    args = parser.parse_args()

    departments = fetch_departments()
    targets = parse_targets(args.departments)
    pool = build_keyword_pool(departments, targets, args.per_category)
    keywords = dedupe_keywords(pool)

    metadata = {
        "departments": targets or [d.get("name") for d in departments[:DEFAULT_DEPARTMENT_COUNT]],
        "per_category": args.per_category,
    }
    path = save_keywords(keywords, source="mercadolivre_trends", prefix="ml_keywords", metadata=metadata)
    print(f"✅ {len(keywords)} keywords salvas em {path}")

    with (DATA_DIR / "ml_keywords_last.json").open("w", encoding="utf-8") as fp:
        json.dump({"file": path.name, "keywords": keywords}, fp, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
