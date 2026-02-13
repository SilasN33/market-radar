"""Script para executar todo o pipeline de coleta e análise de dados (MARKET INTENT ENGINE V2)."""
import sys
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent

def run_command(module_name: str, args: list[str] = None, description: str = "") -> bool:
    """Executa um módulo Python como script e retorna True se bem-sucedido."""
    print(f"\n{'=' * 60}")
    print(f"🔄 {description}")
    print(f"{'=' * 60}")
    
    cmd = [sys.executable, "-m", module_name]
    if args:
        cmd.extend(args)
    
    try:
        # Usamos cwd=PROJECT_ROOT para garantir que o python path inclua a raiz (src/)
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            print(result.stdout)
        
        if result.returncode != 0:
            print(f"❌ Erro: {result.stderr}")
            return False
        
        print(f"✅ {description} - Concluído!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao executar: {e}")
        return False


def main():
    print(f"""
╔══════════════════════════════════════════════════════════╗
║             MARKET RADAR - INTENT ENGINE V2.0            ║
║         Predictive Market Gap Identification System      ║
╚══════════════════════════════════════════════════════════╝

Iniciado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
Mode: V2 SCORING (Velocity + Gap + Quality)
""")
    
    steps = [
        # 1. ACQUIRE SIGNALS
        {
            "module": "src.services.intent_signals",
            "desc": "📡 Coletando Sinais de Intenção (Autocomplete + Trends)"
        },
        
        # 2. ANALYZE SIGNALS (AI)
        {
            "module": "src.services.ai_processor",
            "desc": "🧠 Analisando Sinais e Construindo Clusters de Intenção"
        },
        
        # 3. VALIDATE MARKET (Scraping V2 - Capturing Reviews & Seller)
        {
            "module": "src.services.mercadolivre_service",
            "args": ["--max-keywords", "25", "--products-per-keyword", "6"],
            "desc": "🛍️ Validando Produtos no Mercado Livre (Deep Validation)"
        },
        #{
        #    "module": "src.scrapers.amazon",
        #    "args": ["--max-keywords", "25", "--products-per-keyword", "6"],
        #    "desc": "🛒 Validando Produtos na Amazon BR",
        #    "optional": True,
        #},
        
        # 4. V2 ORCHESTRATION (Snapshot -> Scoring -> Persistence)
        {
            "module": "src.services.pipeline_v2",
            "desc": "🏆 Executando Motor de Scoring V2 (Velocidade, Lacuna, Qualidade)"
        }
    ]
    
    success_count = 0
    total_steps = len(steps)
    
    for step in steps:
        ok = run_command(step["module"], step.get("args"), step["desc"])
        if ok:
            success_count += 1
            continue

        if step.get("optional"):
            print(f"\n⚠️  Falha na etapa opcional: {step['desc']} (prosseguindo)")
            continue

        print(f"\n⚠️  Falha na etapa: {step['desc']}")
        print("Pipeline interrompido.")
        break
    
    print(f"\n{'=' * 60}")
    print(f"📊 RESUMO DO PIPELINE V2")
    print(f"{'=' * 60}")
    print(f"✅ Etapas concluídas: {success_count}/{total_steps}")
    print(f"📁 Relatórios salvos em: {PROJECT_ROOT / 'data' / 'reports'}")
    
    if success_count == total_steps:
        print(f"\n🎉 Pipeline V2 executado com sucesso!")
        print(f"\n💡 Próximos passos:")
        print(f"   1. Iniciar o servidor: python -m src.app.server")
        print(f"   2. Abrir o dashboard: http://localhost:5000")
    else:
        print(f"\n❌ Pipeline incompleto. Verifique os erros acima.")
        sys.exit(1)


if __name__ == "__main__":
    main()
