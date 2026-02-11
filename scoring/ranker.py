"""Combine Intent Signals and Market Data into a Scored Opportunity Ranking."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import math
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# IMPORTANT: Import patch BEFORE database to enable Postgres
from sources import database_patch
from sources import database

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RAW_DIR = DATA_DIR / "raw"
REPORT_DIR = DATA_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Opportunity:
    keyword: str  # The product name/term
    intent_cluster: Optional[str] = None # Name of the intent cluster
    signals: Dict[str, float] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

    def score(self) -> float:
        """
        Calculate Market Opportunity Score (0.0 - 100.0)
        
        NEW SCORING MODEL (Strategic Evolution):
        - Signal Quality & Diversity (35%): How many *types* of intent did we find?
        - Intent Confidence (25%): AI assessment of the problem/solution fit.
        - Market Velocity (25%): Is it trending NOW? (Internal trends, new listings).
        - Market Validation (15%): Does it exist? (Scraping check).
        
        Prioritizes:
        - Growth velocity over absolute volume.
        - New seller bets (Youth).
        """
        # 1. Intent Confidence (From AI) - 0.0 to 1.0
        intent = self.signals.get("intent_confidence", 0.5)
        
        # 2. Market Validation (From Scrapers) - 0.0 to 1.0
        validation = self.signals.get("market_validation", 0.0)
        
        # 3. Signal Diversity (From Source Count)
        # 1 source = 0.5, 2 sources = 0.8, 3+ sources = 1.0
        source_count = self.signals.get("signal_diversity_count", 1)
        diversity_score = min(0.5 + (source_count * 0.15), 1.0)
        if source_count >= 3: diversity_score = 1.0
        
        # 4. Velocity & Freshness
        # Boost if "internal_trends" (Confirmed Demand) or "new_listing" (Seller Bet) present
        sources = self.meta.get("source_signals", [])
        velocity_score = 0.4 # Base
        if "internal_trends" in sources: velocity_score += 0.3
        if "new_listing" in sources: velocity_score += 0.3
        velocity_score = min(velocity_score, 1.0)

        # Weighted Calculation
        weighted_score = (
            (diversity_score * 0.35) +
            (intent * 0.25) +
            (velocity_score * 0.25) +
            (validation * 0.15)
        )
        
        return round(weighted_score * 100, 1) # Return 0-100 scale

    def to_dict(self) -> Dict[str, Any]:
        return {
            "keyword": self.keyword,
            "cluster": self.intent_cluster,
            "score": self.score(),
            "signals": self.signals,
            "sources": self.meta.get("source_signals", []), # Explicit sources for UI
            "meta": self.meta,
            "analysis": {
                "why": self.meta.get("why_trending", "N/A"),
                "buying_intent": self.meta.get("buying_intent", "N/A"),
                "risk": self.meta.get("risk_factors", "Unknown"),
                "competition": self.meta.get("competition_level", "Unknown")
            }
        }


def _latest(prefix: str) -> Optional[Path]:
    candidates = sorted(RAW_DIR.glob(f"{prefix}-*.json"), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None

def _load_json(path: Path) -> Any:
    if not path or not path.exists():
        return []
    with path.open(encoding="utf-8") as fp:
        return json.load(fp)

def build_opportunities(
    clusters_path: Optional[Path], 
    ml_path: Optional[Path], 
    amazon_path: Optional[Path] = None
) -> List[Opportunity]:
    
    opps: Dict[str, Opportunity] = {}

    # 1. Load Intent Clusters (The Foundation)
    if clusters_path and clusters_path.exists():
        clusters = _load_json(clusters_path)
        print(f"[info] Loading {len(clusters)} intent clusters from {clusters_path.name}...")
        
        for cluster in clusters:
            cluster_name = cluster.get("cluster_name", "Unknown")
            confidence = cluster.get("confidence_score", 50) / 100.0
            
            source_signals = cluster.get("source_signals_used", []) 
            # Normalize signals list if it's a string (AI glitch prevention)
            if isinstance(source_signals, str):
                source_signals = [source_signals]
            
            metadata = {
                "buying_intent": cluster.get("buying_intent", ""),
                "why_trending": cluster.get("why_trending", ""),
                "risk_factors": cluster.get("risk_factors", "Unknown"),
                "competition_level": cluster.get("competition_level", "Unknown"),
                "source_signals": source_signals
            }

            # Create an opportunity for each validated product
            for product in cluster.get("validated_products", []):
                norm_kw = product.strip().lower()
                if not norm_kw:
                    continue
                
                opp = opps.setdefault(norm_kw, Opportunity(
                    keyword=product.strip(),
                    intent_cluster=cluster_name
                ))
                
                # Set Intent Signals
                # If existing, keep higher confidence
                opp.signals["intent_confidence"] = max(opp.signals.get("intent_confidence", 0), confidence)
                opp.signals["signal_diversity_count"] = len(source_signals)
                opp.meta.update(metadata)

    # 2. Enrich with Mercado Livre Data (Validation)
    if ml_path and ml_path.exists():
        ml_data = _load_json(ml_path)
        # Handle dict wrapper if present
        if isinstance(ml_data, dict):
            # Try to find the list of items
            if "opportunities" in ml_data: ml_data = ml_data["opportunities"]
            elif "products" in ml_data: ml_data = ml_data["products"]
            elif "items" in ml_data: ml_data = ml_data["items"]
            elif "keywords" in ml_data: ml_data = ml_data["keywords"] 
        
        print(f"[info] Processing Mercado Livre data for validation ({len(ml_data) if isinstance(ml_data, list) else 'unknown'} items)...")
        
        kw_groups = {}
        if isinstance(ml_data, list):
            for item in ml_data:
                # Normalize key for matching
                sk = item.get("search_keyword", "") or item.get("keyword", "") or item.get("title", "")
                sk = sk.strip().lower()
                if sk:
                    kw_groups.setdefault(sk, []).append(item)
                
        # Update Opportunities
        for kw, items in kw_groups.items():
            if not items: continue
            
            # Match Logic
            opp = opps.get(kw)
            
            # Fuzzy Logic
            if not opp:
                for existing_kw in list(opps.keys()):
                    if existing_kw in kw or kw in existing_kw:
                        opp = opps[existing_kw]
                        break
            
            # Unclustered Logic
            if not opp:
                opp = Opportunity(keyword=items[0].get("search_keyword", kw), intent_cluster="Unclustered Signal")
                opp.signals["intent_confidence"] = 0.2
                opps[kw] = opp
            
            # Validation Logic
            validation_score = min(len(items) / 5.0, 1.0)
            opp.signals["market_validation"] = max(opp.signals.get("market_validation", 0), validation_score)
            
            # Metadata Update
            best_item = items[0]
            if not opp.meta.get("url"): opp.meta["url"] = best_item.get("permalink", "") or best_item.get("url", "")
            if not opp.meta.get("thumbnail"): opp.meta["thumbnail"] = best_item.get("thumbnail", "")
            
            valid_prices = [i.get("price", 0) for i in items if i.get("price")]
            if valid_prices:
                avg_price = sum(valid_prices) / len(valid_prices)
                if "price" not in opp.meta: opp.meta["price"] = f"R$ {avg_price:.2f}"
                opp.meta["ml_avg_price"] = f"R$ {avg_price:.2f}"
            
            opp.meta["ml_count"] = len(items)
            opp.meta["marketplace"] = "Mercado Livre" # default primary

    # 3. Enrich with Amazon Data (Optional)
    if amazon_path and amazon_path.exists():
        amz_data = _load_json(amazon_path)
        if isinstance(amz_data, dict):
             if "items" in amz_data: amz_data = amz_data["items"]
             elif "products" in amz_data: amz_data = amz_data["products"]

        kw_groups = {}
        if isinstance(amz_data, list):
            for item in amz_data:
                sk = item.get("search_keyword", "") or item.get("keyword", "") or item.get("title", "")
                sk = sk.strip().lower()
                if sk: kw_groups.setdefault(sk, []).append(item)
        
        for kw, items in kw_groups.items():
            # Match Logic
            opp = opps.get(kw)
            if not opp: 
                for existing_kw in list(opps.keys()):
                    if existing_kw in kw or kw in existing_kw:
                        opp = opps[existing_kw]
                        break
            
            # Unclustered Logic for Amazon
            if not opp and items:
                opp = Opportunity(keyword=items[0].get("search_keyword", kw), intent_cluster="Amazon Only Signal")
                opp.signals["intent_confidence"] = 0.2
                opps[kw] = opp
            
            if opp and items:
                current = opp.signals.get("market_validation", 0)
                # Boost if Amazon also confirms
                opp.signals["market_validation"] = min(current + 0.3, 1.0) 
                opp.meta["amazon_validation"] = True
                
                # Metadata fallback
                if not opp.meta.get("thumbnail") and items[0].get("thumbnail"):
                     opp.meta["thumbnail"] = items[0]["thumbnail"]
                if not opp.meta.get("url") and items[0].get("permalink"):
                     opp.meta["url"] = items[0].get("permalink")
                     
                # Amazon Prices
                valid_prices = [i.get("price", 0) for i in items if i.get("price")]
                if valid_prices:
                    avg_price = sum(valid_prices) / len(valid_prices)
                    opp.meta["amz_avg_price"] = f"R$ {avg_price:.2f}"
                    # If this opp was Amazon Only, set main price
                    if opp.intent_cluster == "Amazon Only Signal":
                         opp.meta["price"] = f"R$ {avg_price:.2f}"
                         opp.meta["marketplace"] = "Amazon BR"

    return sorted(opps.values(), key=lambda o: o.score(), reverse=True)


def save_report(opps: List[Opportunity], max_items: int) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report = REPORT_DIR / f"ranking-{timestamp}.json"
    
    payload = {
        "generated_at": timestamp,
        "count": len(opps),
        "opportunities": [o.to_dict() for o in opps[:max_items]]
    }
    
    with report.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)
    
    # Save 'latest' for API
    latest = REPORT_DIR / "ranking-latest.json"
    with latest.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)
        
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Score opportunities based on Intent Clusters")
    parser.add_argument("--max-items", type=int, default=50)
    
    # Defaults to latest available files
    clusters_file = DATA_DIR / "raw" / "intent_clusters_latest.json"
    mercado_file = _latest("mercado_livre") # Scraped data
    
    # Validation
    if not clusters_file.exists():
        # Try to find any clusters file
        found = _latest("intent_clusters")
        if found: 
            clusters_file = found
            print(f"[info] Using fallback cluster file: {found.name}")
        else:
            print("[warn] No intent clusters found. Run ai_processor.py first.")

    parser.add_argument("--clusters", type=Path, default=clusters_file)
    parser.add_argument("--mercado", type=Path, default=mercado_file)
    parser.add_argument("--amazon", type=Path, default=_latest("amazon"))
    
    args = parser.parse_args()

    print(f"📊 Ranking Evolution based on: {args.clusters.name if args.clusters.exists() else 'None'}")
    
    opps = build_opportunities(args.clusters, args.mercado, args.amazon)
    
    if not opps:
        print("No opportunities found to rank.")
        return

    report_path = save_report(opps, args.max_items)
    
    report_path = save_report(opps, args.max_items)
    print(f"✅ Ranking Generated: {report_path}")

    # Save to Database (Phase 1)
    try:
        database.init_db() # Ensure tables exist
        print(f"[info] 💾 Saving {len(opps)} opportunities to database...")
        saved_count = 0
        for opp in opps[:args.max_items]:
            cluster_id = None
            if opp.intent_cluster:
                cluster_id = database.get_cluster_id_by_name(opp.intent_cluster)
            
            try:
                database.save_opportunity(opp.to_dict(), cluster_id)
                saved_count += 1
            except Exception as e:
                print(f"[warn] Failed to save opportunity '{opp.keyword}': {e}")
        print(f"✅ {saved_count} opportunities persisted to DB.")

    except Exception as e:
        print(f"[error] Database syncing failed: {e}")

    print("\n🏆 KEYWORD OPPORTUNITY LEADERBOARD:")
    print(f"{'SCORE':<8} | {'KEYWORD':<30} | {'WHY IT IS A WINNER'}")
    print("-" * 80)
    
    for opp in opps[:5]:
        why = opp.meta.get('analysis', {}).get('why', 'N/A')
        if not why or why == "N/A":
             why = opp.meta.get('why_trending', 'N/A')
        why_short = why[:45] + "..."
        print(f"{opp.score():<8} | {opp.keyword[:30]:<30} | {why_short}")

if __name__ == "__main__":
    main()
