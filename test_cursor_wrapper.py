"""
Teste para verificar se o PostgresCursor converte ? para %s corretamente
"""

class MockCursor:
    """Mock cursor para testes"""
    def __init__(self):
        self.last_query = None
        self.last_params = None
    
    def execute(self, query, params=None):
        self.last_query = query
        self.last_params = params
        return True
    
    def fetchone(self):
        return {"id": 1, "email": "test@example.com"}

# Importar a classe PostgresCursor
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[0] / "sources"))

# Simular que estamos em ambiente Postgres
import os
os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost:6543/db'

# Importar o módulo que tem o PostgresCursor
import importlib
import sources.database_patch as db_patch

# Testar manualmente
if hasattr(db_patch, 'PostgresCursor'):
    print("✅ PostgresCursor encontrado!")
    
    mock = MockCursor()
    wrapper = db_patch.PostgresCursor(mock)
    
    # Teste 1: Query simples com ?
    wrapper.execute("SELECT * FROM users WHERE email = ?", ("test@example.com",))
    assert mock.last_query == "SELECT * FROM users WHERE email = %s", f"Esperado: %s, Got: {mock.last_query}"
    print("✅ Teste 1: Query com single ? convertida corretamente")
    
    # Teste 2: Query com múltiplos ?
    wrapper.execute("INSERT INTO users (email, name, role) VALUES (?, ?, ?)", ("a@b.com", "User", "admin"))
    assert mock.last_query == "INSERT INTO users (email, name, role) VALUES (%s, %s, %s)"
    print("✅ Teste 2: Query com múltiplos ? convertida corretamente")
    
    # Teste 3: Query sem ?
    wrapper.execute("SELECT COUNT(*) FROM users", None)
    assert mock.last_query == "SELECT COUNT(*) FROM users"
    print("✅ Teste 3: Query sem ? mantida inalterada")
    
    # Teste 4: Fetchone
    result = wrapper.fetchone()
    assert result == {"id": 1, "email": "test@example.com"}
    print("✅ Teste 4: fetchone() funciona corretamente")
    
    print("\n🎉 Todos os testes passaram!")
else:
    print("⚠️ PostgresCursor não encontrado - provavelmente DATABASE_URL não está setada")
    print("Isso é normal em ambiente local SQLite")
