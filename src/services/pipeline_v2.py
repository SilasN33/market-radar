"""Market Radar Pipeline V2 Orchestrator."""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Services
from src.database import init_db, save_opportunity, get_cluster_id_by_name, add_term_history_snapshot
from src.services.scoring.scoring_service import calculate_indice_intencao_v2
from src.utils.keyword_utils import load_keywords

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
RAW_DIR = DATA_DIR / "raw"
REPORT_DIR = DATA_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path):
    if not path or not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def get_latest_file(prefix: str) -> Path | None:
    candidates = sorted(RAW_DIR.glob(f"{prefix}-*.json"), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None


def step_1_snapshot_velocity(clusters: list):
    """Snapshot search velocity."""
    print("📸 Snapshotting Search Term History (V2)...")
    for cluster in clusters:
        for product in cluster.get("validated_products", []):
            try:
                # Add snapshot (metric_value=1.0 as occurrence proxy)
                add_term_history_snapshot(str(product), 1.0, source="pipeline_v2", metric_type="occurrence")
            except Exception as e:
                print(f"[warn] Snapshot failed for {product}: {e}")

def step_2_process_ranking(clusters, ml_data, amazon_data, max_items=50):
    print("🏆 Calculating V2 Scores (Predictive Gap Analysis)...")
    
    opportunities = []
    scraped_map = {}
    
    # Simple indexing
    def index_data(data_list):
        if not data_list: return
        items = data_list if isinstance(data_list, list) else data_list.get("items", [])
        for item in items:
            kw = (item.get("search_keyword") or item.get("keyword") or "").lower().strip()
            if kw: scraped_map.setdefault(kw, []).append(item)

    index_data(ml_data)
    index_data(amazon_data)

    for cluster in clusters:
        cluster_name = cluster.get("cluster_name")
        ai_connf = cluster.get("confidence_score", 50) / 100.0
        
        for product in cluster.get("validated_products", []):
            term = str(product).strip()
            term_lower = term.lower()
            
            validation_items = scraped_map.get(term_lower, [])
            source_count = 1 + (1 if validation_items else 0)
            
            # SCORE V2
            try:
                score_result = calculate_indice_intencao_v2(
                    term=term,
                    ai_confidence=ai_connf,
                    source_count=source_count,
                    scraped_data=validation_items
                )
            except Exception as e:
                print(f"[err] Scoring failed for {term}: {e}")
                continue
            
            # META
            meta = {
                "cluster": cluster_name,
                "buying_intent": cluster.get("buying_intent"),
                "why_trending": cluster.get("why_trending"),
                "risk_factors": cluster.get("risk_factors"),
                "price_estimate": cluster.get("price_range_brl"),
                "velocity_meta": score_result["breakdown"].pop("meta_velocity", {})
            }
            
            if validation_items:
                top = validation_items[0]
                meta["thumbnail"] = top.get("thumbnail")
                meta["url"] = top.get("permalink")
                meta["price"] = f"R$ {top.get('price', 0)}"
                meta["marketplace"] = top.get("source", "unknown")

            opportunities.append({
                "keyword": term,
                "cluster_id": None, # Resolve later
                "score": score_result["score"],
                "signals": {
                    "v2_score": score_result["score"],
                    "v2_breakdown": score_result["breakdown"],
                    "signal_diversity_count": score_result["breakdown"]["IndiceSinalMultiplasFontes"] * 10 # Proxy
                },
                "meta": meta,
                "scoring_breakdown": score_result["breakdown"], # JSON for DB
                "analysis": {
                    "why": cluster.get("why_trending"),
                    "risk": cluster.get("risk_factors")
                }
            })

    opportunities.sort(key=lambda x: x["score"], reverse=True)
    return opportunities[:max_items]


def step_3_persistence(opportunities):
    print(f"💾 Persisting {len(opportunities)} V2 Opportunities...")
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = REPORT_DIR / f"ranking_v2-{timestamp}.json"
    latest_path = REPORT_DIR / "ranking_latest.json"
    
    payload = {
        "generated_at": timestamp,
        "algorithm": "v2.0",
        "count": len(opportunities),
        "opportunities": opportunities
    }
    
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    with latest_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        
    # DB Sync
    init_db()
    for opp in opportunities:
        c_name = opp["meta"].get("cluster")
        cid = get_cluster_id_by_name(c_name) if c_name else None
        save_opportunity(opp, cid)
        
    print(f"✅ Saved to {report_path}")


def main():
    print("🚀 Market Radar Pipeline V2 - Scoring Engine\n")
    
    # Load inputs (Latest from RAW)
    clusters_path = get_latest_file("intent_clusters")
    ml_path = get_latest_file("mercado_livre")
    amz_path = get_latest_file("amazon")
    
    if not clusters_path:
        # Fallback to hardcoded name if timestamped not found
        clusters_path = RAW_DIR / "intent_clusters_latest.json"
    
    if not clusters_path.exists():
        print("❌ No clusters found. Run AI Processor first.")
        return

    print(f"📂 Loading clusters from: {clusters_path.name}")
    clusters = load_json(clusters_path)
    ml_data = load_json(ml_path)
    amz_data = load_json(amz_path)
    
    step_1_snapshot_velocity(clusters)
    opps = step_2_process_ranking(clusters, ml_data, amz_data)
    step_3_persistence(opps)
    
    print("\n✅ V2 Execution Complete.")


if __name__ == "__main__":
    main()
