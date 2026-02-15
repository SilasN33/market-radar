
import sys
import importlib
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

def check_module(module_name):
    print(f"Testing import: {module_name}...", end=" ")
    try:
        importlib.import_module(module_name)
        print("✅ OK")
        return True
    except ImportError as e:
        print(f"❌ FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

metadata = {
    "src.services.intent_signals": "BeautifulSoup4, Requests",
    "src.services.mercadolivre_service": "Requests",
    "src.services.ai_processor": "Requests, Utils",
    "src.services.pipeline_v2": "Database, Scoring",
    "src.database": "Psycopg2/SQLite"
}

failed = []
print("--- DEPENDENCY CHECK ---")
for mod in metadata:
    if not check_module(mod):
        failed.append(mod)

if failed:
    print(f"\n❌ {len(failed)} modules failed to import.")
    sys.exit(1)
else:
    print("\n✅ All core modules imported successfully.")
    sys.exit(0)
