# 🏛️ Arquitetura Market Radar - Motor de Intenção V2.0

Esta arquitetura implementa o conceito de **Predictive Gap Identification System**, focado em encontrar lacunas de mercado antes que saturem.

---

## 📂 Estrutura Modular (src/)

O código foi migrado para uma estrutura Python limpa e escalável.

- **`src/app/`**: Camada de Aplicação (Flask API)
    - `server.py`: Entry point da API.
    - `auth.py`: Autenticação SaaS (JWT/Session).
    - `routes.py`: Endpoints de dados (/ranking, /stats).
- **`src/database/`**: Camada de Persistência (Agnóstica)
    - `database.py`: Abstração SQLite (Local) / Postgres (Prod).
    - Suporta JSON complexo (`scoring_breakdown`) e Histórico (`search_term_history`).
- **`src/scrapers/`**: Coleta de Dados V2
    - `mercado_livre.py` / `amazon.py`
    - Coleta **Rating, Reviews Count e Vendedor** para análise de qualidade.
- **`src/services/`**: Inteligência de Negócio
    - `intent_signals.py`: Coleta de Autocomplete/Trends.
    - `ai_processor.py`: Clusterização Semântica (GPT-4o).
    - `pipeline_v2.py`: Orquestrador mestre do fluxo V2.
    - **`metrics/metrics_service.py`**: Cálculos matemáticos (Velocidade, Concentração).
    - **`scoring/scoring_service.py`**: Fórmula V2 ponderada.

---

## 🏎️ Motor de Scoring V2 (Algoritmo)

O ranking não é mais baseado apenas em volume, mas em uma composição ponderada:

1.  **Velocidade de Busca (25%)**: O termo está crescendo rápido? (Aceleração baseada em histórico).
2.  **Lacuna de Oferta (25%)**: O mercado está concentrado em poucos vendedores? (Concentração < 0.3 é ideal).
3.  **Qualidade da Concorrência (15%)**: Os produtos existentes são ruins? (Rating < 4.0 é oportunidade).
4.  **Viabilidade de Preço (15%)**: Existe compressão de preço? (Race to bottom).
5.  **Confiança IA (10%)**: A IA validou a dor do usuário?
6.  **Diversidade de Sinais (10%)**: Apareceu em múltiplas fontes?

---

## 🚀 Como Executar

### Pipeline de Dados (Background Job)
```bash
python run_pipeline.py
```
*(Executa orquestração modular: `python -m src.services.pipeline_v2`)*

### Servidor API (Web Dashboard)
```bash
python -m src.app.server
```
*(Acesse http://localhost:5000)*
