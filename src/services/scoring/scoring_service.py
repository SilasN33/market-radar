"""Scoring Service V2.0 for Market Radar."""
from __future__ import annotations

from typing import Dict, Any, List

# Metric Service
from src.services.metrics.metrics_service import (
    calculate_search_velocity,
    analyze_market_concentration,
    analyze_price_compression,
    analyze_quality_opportunity
)


def calculate_indice_intencao_v2(
    term: str,
    ai_confidence: float = 0.5,
    source_count: int = 1,
    scraped_data: List[Dict] = None
) -> Dict[str, Any]:
    """Calculate the Market Intent Score V2.0 (Predictive Gap)."""
    
    # 1. Search Velocity (25%)
    velocity_meta = calculate_search_velocity(term)
    idx_velocidade = min(1.0, max(0.0, velocity_meta.get("velocity_index", 0.5)))
    
    # 2. Supply Gap (25%) - Inverse of Concentration
    scraped_data = scraped_data or []
    concentration = analyze_market_concentration(scraped_data)
    idx_lacuna = 1.0 - concentration
    if not scraped_data: idx_lacuna = 1.0 # Blue Ocean
    
    # 3. Competitor Quality (15%) - Inverse of Rating
    idx_qualidade = analyze_quality_opportunity(scraped_data)
    
    # 4. Price Viability (15%) - Inverse of Compression
    compression = analyze_price_compression(scraped_data)
    idx_viabilidade = 1.0 - compression
    
    # 5. AI Confidence (10%)
    idx_ia = min(1.0, max(0.0, ai_confidence))
     
    # 6. Signal Diversity (10%)
    idx_fontes = min(1.0, max(0.0, 0.4 + (source_count - 1) * 0.3))
    
    # Weighted Sum
    raw_score = (
        (idx_velocidade * 0.25) +
        (idx_lacuna * 0.25) +
        (idx_qualidade * 0.15) +
        (idx_viabilidade * 0.15) +
        (idx_ia * 0.10) +
        (idx_fontes * 0.10)
    )
    
    final_score = round(raw_score * 100, 1)
    
    return {
        "score": final_score,
        "version": "v2.0",
        "breakdown": {
            "IndiceVelocidadeBusca": round(idx_velocidade, 2),
            "IndiceLacunaOferta": round(idx_lacuna, 2),
            "IndiceQualidadeConcorrencia": round(idx_qualidade, 2),
            "IndiceViabilidadePreco": round(idx_viabilidade, 2),
            "IndiceConfiancaIA": round(idx_ia, 2),
            "IndiceSinalMultiplasFontes": round(idx_fontes, 2),
            "meta_velocity": velocity_meta
        }
    }
