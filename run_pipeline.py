"""Script para executar todo o pipeline de coleta e análise de dados (MARKET INTENT ENGINE)."""
import sys
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent

def run_command(cmd: list[str], description: str) -> bool:
    """Executa um comando e retorna True se bem-sucedido."""
    print(f"\n{'=' * 60}")
    print(f"🔄 {description}")
    print(f"{'=' * 60}")
    
    try:
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
║                MARKET RADAR - INTENT ENGINE              ║
║         Real-time Opportunity Discovery Pipeline         ║
╚══════════════════════════════════════════════════════════╝

Iniciado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
""")
    
    # PIPELINE EVOLUTION: From Search Volume to Intent Signals
    
    steps = [
        # 1. ACQUIRE SIGNALS (The raw intent data)
        {
            "cmd": [sys.executable, "sources/intent_signals.py"],
            "desc": "📡 Coletando Sinais de Intenção (Autocomplete + Trends)"
        },
        
        # 2. ANALYZE SIGNALS (The AI filter/cluster)
        {
            "cmd": [sys.executable, "sources/ai_processor.py"],
            "desc": "🧠 Analisando Sinais e Construindo Clusters de Intenção"
        },
        
        # 3. VALIDATE MARKET (Scraping real data for the AI suggestions)
        {
            "cmd": [sys.executable, "sources/mercado_livre.py", "--max-keywords", "25", "--products-per-keyword", "4"],
            "desc": "🛍️ Validando Produtos no Mercado Livre"
        },
        {
            "cmd": [sys.executable, "sources/amazon.py", "--max-keywords", "25", "--products-per-keyword", "4"],
            "desc": "🛒 Validando Produtos na Amazon BR",
            "optional": True,
        },
        
        # 4. RANK OPPORTUNITIES (Final scoring)
        {
            "cmd": [sys.executable, "scoring/ranker.py"],
            "desc": "🏆 Gerando Ranking de Oportunidades (Intent Score)"
        }
    ]
    
    success_count = 0
    total_steps = len(steps)
    
    for step in steps:
        ok = run_command(step["cmd"], step["desc"])
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
    print(f"📊 RESUMO DO PIPELINE")
    print(f"{'=' * 60}")
    print(f"✅ Etapas concluídas: {success_count}/{total_steps}")
    print(f"📁 Dados salvos em: {PROJECT_ROOT / 'data' / 'reports'}")
    
    if success_count == total_steps:
        print(f"\n🎉 Pipeline executado com sucesso!")
        print(f"\n💡 Próximos passos:")
        print(f"   1. Iniciar o servidor: python api/server.py")
        print(f"   2. Abrir o dashboard: http://localhost:5000")
    else:
        print(f"\n❌ Pipeline incompleto. Verifique os erros acima.")
        sys.exit(1)


if __name__ == "__main__":
    main()
