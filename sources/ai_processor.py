"""AI-powered Market Signal Analyst using OpenAI REST API."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

import requests

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
from env_loader import load_env
from database import save_cluster, init_db

# Load environment variables
load_env()

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def load_latest_signals() -> List[Dict[str, Any]]:
    """Carregar os sinais de intenção mais recentes (Marketplace Intent Signals)."""
    # Prioriza os sinais de intenção direta (intent_signals-*.json)
    signal_files = sorted(DATA_DIR.glob("intent_signals-*.json"), reverse=True)
    
    if signal_files:
        print(f"[info] 📡 Carregando sinais de intenção de: {signal_files[0].name}")
        with signal_files[0].open("r", encoding="utf-8") as f:
            return json.load(f)
            
    print("[error] ⛔ CRITICAL: Nenhum arquivo de Marketplace Intent Signals encontrado!")
    print("        Execute 'python sources/intent_signals.py' primeiro.")
    return []


def load_context_signals() -> str:
    """Load Google Trends/News ONLY as contextual signals (Secondary)."""
    trend_files = sorted(DATA_DIR.glob("google_trends-*.json"), reverse=True)
    if trend_files:
        try:
            with trend_files[0].open("r", encoding="utf-8") as f:
                data = json.load(f)
                summary = [t.get("query") for t in data[:10]]
                return ", ".join(summary)
        except:
            return ""
    return ""


def call_openai_api(prompt: str, api_key: str) -> str | None:
    """Chamar OpenAI API (gpt-4o-mini) para análise de mercado."""
    url = "https://api.openai.com/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a Senior Market Signal Analyst. "
                    "You analyze raw marketplace data to detect REAL BUYING INTENT. "
                    "You DO NOT guess. You DO NOT invent products. "
                    "You return 'NO ACTIONABLE SIGNAL DETECTED' if the data is weak."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3, # Lower temperature for analytical precision
        "max_tokens": 2500
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return content.strip()
        
    except Exception as e:
        print(f"[error] Erro ao chamar OpenAI: {e}")
        return None


def analyze_market_signals(signals: List[Dict[str, Any]], context: str, max_clusters: int = 20) -> List[Dict]:
    """
    USAR IA PARA CONSTRUIR CLUSTERS DE INTENÇÃO DE COMPRA.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[warn] ⚠️  OPENAI_API_KEY não configurada. Impossível analisar sinais.")
        return []
    
    # Preparar resumo dos sinais
    # Agrupar por fonte para dar contexto à IA
    by_source = {}
    for s in signals:
        src = s.get("source", "unknown")
        term = s.get("term", "")
        if term:
            by_source.setdefault(src, []).append(term)
    
    signal_summary = ""
    for src, terms in by_source.items():
        # Amostra de até 50 termos por fonte para não estourar contexto
        # unique terms only
        unique = list(set(terms))[:50]
        signal_summary += f"\nSOURCE [{src.upper()}]:\n" + ", ".join(unique) + "\n"

    prompt = f"""
ACT AS: Senior Market Signal Analyst.

YOUR TASK: Analyze the provided MARKETPLACE INTENT SIGNALS and group them into VALIDATED INTENT CLUSTERS.

CONTEXTUAL TRENDS (For reference only, NOT primary): {context}

RAW SIGNALS:
{signal_summary}

---

STRICT ANALYSIS RULES:
1. **NO GUESSING**: Only output clusters supported by the signals.
2. **FILTER NOISE**: Ignore generic terms ("celular", "roupa", "presente") unless a specific modifier exists ("celular idosos", "roupa proteção uv").
3. **FOCUS ON PROBLEMS**: Look for "problem-solution" patterns in the signals (e.g., "for back pain", "portable", "silent").
4. **MICRO-NICHES**: Prefer emerging micro-niches over saturated mass markets.
5. **NO REPETITION**: Do not output duplicate clusters or slight variations of the same thing.

OUTPUT FORMAT (JSON ARRAY ONLY):
Return a JSON Array of objects. Each object MUST strictly follow this schema:

[
  {{
    "cluster_name": "Specific Opportunity Name (e.g., 'Ergonomic Vertical Mouse')",
    "buying_intent": "The core user problem/need (e.g., 'Wrist pain relief for office workers')",
    "validated_products": ["Vertical Mouse Wireless", "Mouse Ortopedico", "Mouse Vertical RGB"],
    "price_range_brl": {{"min": 50.0, "max": 200.0}},
    "negative_keywords": ["case", "capa", "usado", "pilha"],
    "why_trending": "Specific reason based on signals (e.g., 'High volume of 'dor pulso' queries combined with 'mouse vertical' autocomplete')",
    "source_signals_used": ["autocomplete", "internal_trends"],
    "competition_level": "Low/Medium/High",
    "risk_factors": "e.g., 'Niche too small', 'Seasonality', 'Big brand dominance'",
    "confidence_score": 85
  }}
]

CRITICAL:
1. **price_range_brl**: Estimate a reasonable price range in BRL (Brazilian Reais) for the MAIN product. This helps filtering out accessories.
2. **negative_keywords**: List 3-5 keywords that often appear in search results but are NOT the product (e.g. for a phone, exclude 'capa', 'película', 'cabo').
3. If the signals are too weak, generic, or conflicting to form a solid hypothesis, return EXACTLY:
[]
(Empty JSON Array)

DO NOT RETURN MARKDOWN. RETURN ONLY THE JSON.
"""

    print("[info] 🧠 Analisando sinais de mercado com IA (Market Signal Analyst)...")
    
    content = call_openai_api(prompt, api_key)
    
    if not content:
        return []
        
    if "NO ACTIONABLE SIGNAL DETECTED" in content:
        print("[info] IA: Nenhum sinal acionável detectado.")
        return []

    # Limpar markdown se houver
    content = content.replace("```json", "").replace("```", "").strip()
    
    try:
        clusters = json.loads(content)
        print(f"[success] ✅ {len(clusters)} Clusters de Intenção Identificados.")
        return clusters[:max_clusters]
    except json.JSONDecodeError:
        print(f"[error] Falha ao decodificar JSON da IA. Resposta bruta: {content[:100]}...")
        return []


def main():
    print("🤖 Keyword Intelligence Agent - Initializing...\n")
    
    # 1. Carregar Sinais (Marketplace Intent Signals ONLY)
    signals = load_latest_signals()
    if not signals:
        return
    
    # 2. Carregar Contexto (Google Trends - Secondary)
    context = load_context_signals()
    if context:
        print(f"[info] Contexto carregado: {len(context.split(','))} tópicos de news.")

    # 3. Analisar com IA
    clusters = analyze_market_signals(signals, context)
    
    if not clusters:
        print("⚠️  Nenhum cluster identificado. Tente: 1) Mais seeds na coleta 2) Aguardar acumulação de dados.")
        return
        
    # 4. Salvar Resultados (Clusters)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output_path = DATA_DIR / f"intent_clusters-{timestamp}.json"
    latest_path = DATA_DIR / "intent_clusters_latest.json"
    
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(clusters, f, ensure_ascii=False, indent=2)
        
    # 4b. Salvar no Banco de Dados (Phase 1: Persistence)
    try:
        init_db() # Ensure tables exist
        print(f"[info] 💾 Saving {len(clusters)} clusters into SQLite database...")
        for cluster in clusters:
            try:
                cid = save_cluster(cluster)
                # Helper: Add ID to cluster object for immediate use if needed (e.g. by ranker if we passed memory objects)
                cluster["db_id"] = cid
            except Exception as e:
                print(f"[warn] Failed to save cluster '{cluster.get('cluster_name')}': {e}")
                
    except Exception as e:
        print(f"[error] Database error: {e}")
        
    # Salvar 'latest' apenas se tiver sucesso
    if clusters:
        with latest_path.open("w", encoding="utf-8") as f:
            json.dump(clusters, f, ensure_ascii=False, indent=2)
        
    print(f"\n✅ Clusters salvos em: {output_path}")
    print("📋 Amostra de Oportunidades Identificadas:")
    for c in clusters[:3]:
        print(f"   - {c.get('cluster_name')} ({c.get('confidence_score')}%)")
        print(f"     Why: {c.get('why_trending')}")
        print(f"     Intent: {c.get('buying_intent')}")
        print("     ---")


if __name__ == "__main__":
    main()
