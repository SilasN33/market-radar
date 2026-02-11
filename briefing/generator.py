"""Placeholder for opportunity briefing generation via LLM."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import json

TEMPLATE = """# Brief: {keyword}

## Gancho principal
- {hook}

## Script de anúncio (30s Reels/TikTok)
1. {line1}
2. {line2}
3. {line3}

## CTA
- {cta}
"""


DEFAULT_HOOKS = [
    "Mostre o antes/depois real em menos de 3 segundos",
    "Explique o benefício financeiro/bem-estar logo no início",
    "Use depoimento curto + prova social (texto na tela)",
]


def draft_briefs(ranking_path: Path) -> List[str]:
    with ranking_path.open(encoding="utf-8") as fp:
        ranking: List[Dict[str, Any]] = json.load(fp)
    briefs = []
    for idx, item in enumerate(ranking, start=1):
        hook = DEFAULT_HOOKS[idx % len(DEFAULT_HOOKS)]
        briefs.append(
            TEMPLATE.format(
                keyword=item["keyword"],
                hook=hook,
                line1="Apresente o problema que o produto resolve",
                line2="Demonstre o uso em 5 segundos",
                line3="Mostre prova social + preço/condição",
                cta="Arraste para cima/Link na bio para aproveitar",
            )
        )
    return briefs


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("ranking", type=Path)
    args = parser.parse_args()
    for brief in draft_briefs(args.ranking):
        print(brief)
        print("-" * 40)
