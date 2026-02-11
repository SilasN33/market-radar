"""Market Radar AI Processor (Intent Clusterization)."""
import json
import os
import requests
import sys
from pathlib import Path
from datetime import datetime, timezone

# Imports
from src.utils.env_loader import load_env
from src.utils.keyword_utils import load_keywords, save_keywords
from src.database import save_cluster

load_env()

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

class AIProcessor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.endpoint = "https://api.openai.com/v1/chat/completions"

    def analyze_signals(self, signals: list[str]) -> list[dict]:
        """Convert raw signals into Intent Clusters."""
        if not self.api_key:
            print("❌ OPENAI_API_KEY missing. Skipping AI step.")
            return []
            
        print(f"🧠 Processing {len(signals)} signals with GPT-4o-mini...")
        
        prompt = f"""
        Analyze these search queries from Mercado Livre/Amazon:
        {json.dumps(signals[:50])} ...
        
        Group them into highly specific INTENT CLUSTERS.
        For each cluster, return JSON:
        [
          {{
            "cluster_name": "Specific Buying Desire (e.g. 'Fone Bluetooth Corrida')",
            "buying_intent": "High/Medium/Low",
            "validated_products": ["precise search term 1", "precise search term 2"],
            "price_range_brl": {{"min": 50, "max": 200}},
            "negative_keywords": ["case", "capinha", "conserto"],
            "why_trending": "Reason why this is growing now",
            "competition_level": "Low/Medium/High",
            "risk_factors": "Saturated/Fragile/Low Margin",
            "confidence_score": 0-100
          }}
        ]
        """
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a Senior E-commerce Strategist specialized in identifying under-served market gaps."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }
        
        try:
            resp = requests.post(self.endpoint, json=payload, headers=self.headers, timeout=60)
            if resp.status_code != 200:
                print(f"❌ OpenAI Error: {resp.text}")
                return []
                
            content = resp.json()['choices'][0]['message']['content']
            parsed = json.loads(content)
            clusters = parsed.get("clusters", parsed.get("intent_clusters", []))
            
            # Save raw output
            self._save_raw_output(clusters)
            
            # Save to DB
            for c in clusters:
                c["source_signals_used"] = signals[:5] # Approximation
                save_cluster(c)
                
            return clusters
            
        except Exception as e:
            print(f"❌ Automation Error: {e}")
            return []

    def _save_raw_output(self, clusters):
        fname = f"intent_clusters-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        with (DATA_DIR / fname).open("w", encoding="utf-8") as f:
            json.dump(clusters, f, indent=2, ensure_ascii=False)
        # Update latest pointer for pipeline
        with (DATA_DIR / "intent_clusters_latest.json").open("w", encoding="utf-8") as f:
             json.dump(clusters, f, indent=2, ensure_ascii=False)

def main():
    if not OPENAI_API_KEY:
        print("❌ Cannot run AI Processor: No API Key.")
        return

    # Load from Intent Signals step
    signals, source = load_keywords(preferred_sources=("intent_signals", "mercadolivre_trends"), return_rich_objects=False)
    
    if not signals:
        print("❌ No signals found to process.")
        return
        
    ai_bot = AIProcessor(OPENAI_API_KEY)
    ai_bot.analyze_signals(signals)
    print("✅ AI Processing Complete.")

if __name__ == "__main__":
    main()
