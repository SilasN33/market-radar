"""
Teste para verificar conversões DDL SQLite -> PostgreSQL
"""

def test_ddl_conversion():
    """Testa as conversões de DDL"""
    
    # Simular a função de conversão
    def convert_query(query):
        if not query:
            return query
        
        # Convert placeholders: ? -> %s
        if '?' in query:
            query = query.replace('?', '%s')
        
        # Convert DDL (Data Definition Language) for CREATE TABLE
        if 'CREATE TABLE' in query.upper():
            query = query.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
            query = query.replace('integer primary key autoincrement', 'SERIAL PRIMARY KEY')
            query = query.replace('DATETIME', 'TIMESTAMP')
        
        return query
    
    # Teste 1: AUTOINCREMENT -> SERIAL
    sql_in = "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"
    sql_out = convert_query(sql_in)
    expected = "CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT)"
    assert sql_out == expected, f"Expected: {expected}\nGot: {sql_out}"
    print("✅ Teste 1: AUTOINCREMENT convertido para SERIAL")
    
    # Teste 2: DATETIME -> TIMESTAMP
    sql_in = "CREATE TABLE logs (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
    sql_out = convert_query(sql_in)
    expected = "CREATE TABLE logs (id SERIAL PRIMARY KEY, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    assert sql_out == expected, f"Expected: {expected}\nGot: {sql_out}"
    print("✅ Teste 2: DATETIME convertido para TIMESTAMP")
    
    # Teste 3: Query normal com ?
    sql_in = "SELECT * FROM users WHERE email = ?"
    sql_out = convert_query(sql_in)
    expected = "SELECT * FROM users WHERE email = %s"
    assert sql_out == expected, f"Expected: {expected}\nGot: {sql_out}"
    print("✅ Teste 3: Placeholder ? convertido para %s")
    
    # Teste 4: INSERT com múltiplos placeholders
    sql_in = "INSERT INTO users (email, name, role) VALUES (?, ?, ?)"
    sql_out = convert_query(sql_in)
    expected = "INSERT INTO users (email, name, role) VALUES (%s, %s, %s)"
    assert sql_out == expected, f"Expected: {expected}\nGot: {sql_out}"
    print("✅ Teste 4: Múltiplos placeholders convertidos")
    
    # Teste 5: DDL completa (exemplo real do database.py)
    sql_in = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT,
        role TEXT DEFAULT 'free',
        credits INTEGER DEFAULT 10,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
    sql_out = convert_query(sql_in)
    assert 'SERIAL PRIMARY KEY' in sql_out, "AUTOINCREMENT não foi convertido"
    assert 'TIMESTAMP' in sql_out, "DATETIME não foi convertido"
    assert 'AUTOINCREMENT' not in sql_out, "AUTOINCREMENT ainda presente"
    assert 'DATETIME' not in sql_out, "DATETIME ainda presente"
    print("✅ Teste 5: DDL completa da tabela users convertida corretamente")
    
    print("\n🎉 Todos os testes de conversão DDL passaram!")

if __name__ == "__main__":
    test_ddl_conversion()
