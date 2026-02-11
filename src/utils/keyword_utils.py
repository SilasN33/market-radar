"""Shared helpers for keyword management across data sources."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple, Dict

# Ajuste de path: src/utils/keyword_utils.py -> raiz é parents[2]
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FALLBACK_KEYWORDS = [
    "smartphone",
    "fone bluetooth",
    "smartwatch",
    "power bank",
    "use case: kit solar",
    "use case: home office ergonomia",
    "use case: cozinha gourmet",
    "câmera de segurança",
    "cadeira gamer",
    "aspirador robô",
]


def save_keywords(
    keywords: List[str],
    source: str,
    prefix: str = "keywords",
    metadata: dict | None = None,
) -> Path:
    """Persist keyword list to disk with metadata."""
    keywords = [kw.strip() for kw in keywords if kw and kw.strip()]
    if not keywords:
        return None
        
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "keywords": keywords,
        "count": len(keywords),
        "metadata": metadata or {},
    }
    filename = f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    path = DATA_DIR / filename
    with path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)
    return path


def load_keywords(
    preferred_sources: Tuple[str, ...] | None = None,
    min_keywords: int = 5,
    return_rich_objects: bool = False
) -> Tuple[List[Dict | str], str]:
    """
    Return keywords from the most recent file.
    If return_rich_objects=True, returns List[Dict] with {term, price_range, negatives}.
    Else, returns List[str].
    """
    
    # 1. Try to load newest Intent Clusters first (High Quality)
    cluster_files = sorted(DATA_DIR.glob("intent_clusters-*.json"), reverse=True)
    
    # If explicitly asked for something else, skip this unless "intent_clusters" is in preferred
    use_clusters = True
    if preferred_sources and "intent_clusters" not in preferred_sources:
        # Check if ALL preferred sources are legacy
        if not any(s in ("intent_clusters", "ai_cluster") for s in preferred_sources):
             use_clusters = False
             
    if use_clusters and cluster_files:
        try:
            with cluster_files[0].open(encoding="utf-8") as fp:
                clusters = json.load(fp)
                
                rich_keywords = []
                plain_keywords = []

                # Clusters is a list of Dicts
                if isinstance(clusters, list):
                    for c in clusters:
                        if isinstance(c, dict):
                            p_list = c.get("validated_products", [])
                            # Metadata
                            p_range = c.get("price_range_brl", {})
                            negatives = c.get("negative_keywords", [])
                            
                            if isinstance(p_list, list):
                                for p in p_list:
                                    if p and isinstance(p, str) and p.strip():
                                        plain_keywords.append(p.strip())
                                        rich_keywords.append({
                                            "term": p.strip(),
                                            "price_min": p_range.get("min", 0),
                                            "price_max": p_range.get("max", 0),
                                            "negatives": negatives
                                        })
                
                if plain_keywords:
                    if return_rich_objects:
                        return rich_keywords, "intent_clusters"
                    else:
                        # Deduplicate strings
                        return list(dict.fromkeys(plain_keywords)), "intent_clusters"
                        
        except Exception as e:
            print(f"[warn] Failed to load intent clusters: {e}")

    # 2. Try legacy keyword files
    files = sorted(DATA_DIR.glob("*keywords-*.json"), reverse=True)
    
    def read_keywords(path) -> Tuple[List[str], str]:
        try:
            with path.open(encoding="utf-8") as fp:
                data = json.load(fp)
                kws = [kw.strip() for kw in data.get("keywords", []) if kw and kw.strip()]
                return kws, data.get("source", "unknown")
        except:
            return [], "unknown"

    # Try preferred sources
    if preferred_sources:
        for src in preferred_sources:
            # Check files matching source roughly by name or content
            for path in files:
                kws, source = read_keywords(path)
                if kws and source == src:
                    return kws, source

    # Fallback to any file
    for path in files:
        kws, source = read_keywords(path)
        if kws:
            return kws, source

    # Absolute fallback
    return FALLBACK_KEYWORDS[:], "fallback_manual"
