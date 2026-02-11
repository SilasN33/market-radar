"""Fetch Google Trends data for Brazil using Google News RSS."""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
import xml.etree.ElementTree as ET

import requests

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def fetch_trending(limit: int = 20) -> List[Dict[str, Any]]:
    """Fetch trending topics from Google News RSS for Brazil."""
    timestamp = datetime.now(timezone.utc).isoformat()
    trending: List[Dict[str, Any]] = []
    
    FEED_URL = "https://news.google.com/rss?hl=pt-BR&gl=BR&ceid=BR:pt-419"
    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        print(f"[info] Buscando notícias do Google News RSS...")
        resp = requests.get(FEED_URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        
        root = ET.fromstring(resp.text)
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else []
        
        print(f"[info] Encontradas {len(items)} notícias, processando top {limit}...")
        
        for item in items[:limit]:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")
            
            # Extrair keywords do título (palavras principais)
            keywords = [word for word in title.split() if len(word) > 4][:3]
            
            trending.append({
                "timestamp": timestamp,
                "source": "google_news",
                "query": title,
                "traffic": "trending",
                "related": keywords,
                "articles": [{"link": link, "pubDate": pub_date}],
            })
        
        print(f"[success] ✓ {len(trending)} tendências coletadas")
        
    except Exception as e:
        print(f"[error] ✗ Erro ao buscar Google News: {e}")
        # Retornar dados de fallback
        trending = _get_fallback_data(limit, timestamp)
    
    return trending


def _get_fallback_data(limit: int, timestamp: str) -> List[Dict[str, Any]]:
    """Retornar dados de fallback quando a coleta principal falha."""
    print("[warn] Usando dados de fallback genéricos...")
    
    # Tópicos genéricos comuns no Brasil
    fallback_topics = [
        "smartphones",
        "eletrônicos",
        "games",
        "moda e acessórios",
        "casa e jardim",
        "beleza e cuidados pessoais",
        "esportes e fitness",
        "livros e e-books",
        "brinquedos",
        "automotivo",
    ]
    
    trending = []
    for topic in fallback_topics[:limit]:
        trending.append({
            "timestamp": timestamp,
            "source": "fallback",
            "query": topic,
            "traffic": "unknown",
            "related": [],
            "articles": [],
        })
    
    return trending


def save_payload(payload: List[Dict[str, Any]], output: Path | None = None) -> Path:
    if output is None:
        output = DATA_DIR / f"google_trends-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    with output.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Google Trends data")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload = fetch_trending(limit=args.limit)
    path = save_payload(payload, output=args.output)
    print(f"Google Trends salvo em {path} ({len(payload)} itens)")


if __name__ == "__main__":
    main()
