"""
Teste para verificar se PostgresRow funciona como sqlite3.Row
"""

def test_postgres_row():
    """Testa se PostgresRow é compatível com sqlite3.Row"""
    
    # Simular description e values
    description = [('id',), ('email',), ('name',)]
    values = (1, 'test@example.com', 'Test User')
    
    # Criar PostgresRow
    class PostgresRow:
        def __init__(self, values, description):
            self._values = values
            self._description = description
            self._mapping = {desc[0]: val for desc, val in zip(description, values)}
        
        def __getitem__(self, key):
            if isinstance(key, int):
                return self._values[key]
            return self._mapping[key]
        
        def __iter__(self):
            return iter(self._values)
        
        def keys(self):
            return [desc[0] for desc in self._description]
        
        def values(self):
            return list(self._values)
        
        def items(self):
            return self._mapping.items()
        
        def __len__(self):
            return len(self._values)
    
    row = PostgresRow(values, description)
    
    # Teste 1: Acesso por índice (como tupla)
    assert row[0] == 1, "Acesso por índice falhou"
    assert row[1] == 'test@example.com', "Acesso por índice falhou"
    print("✅ Teste 1: Acesso por índice funciona")
    
    # Teste 2: Acesso por nome (como dicionário)
    assert row['id'] == 1, "Acesso por nome falhou"
    assert row['email'] == 'test@example.com', "Acesso por nome falhou"
    assert row['name'] == 'Test User', "Acesso por nome falhou"
    print("✅ Teste 2: Acesso por nome funciona")
    
    # Teste 3: Iteração (como tupla)
    values_list = list(row)
    assert values_list == [1, 'test@example.com', 'Test User'], "Iteração falhou"
    print("✅ Teste 3: Iteração funciona")
    
    # Teste 4: Conversão para dict
    d = dict(row.items())
    assert d == {'id': 1, 'email': 'test@example.com', 'name': 'Test User'}, "dict() falhou"
    print("✅ Teste 4: Conversão para dict funciona")
    
    # Teste 5: len()
    assert len(row) == 3, "len() falhou"
    print("✅ Teste 5: len() funciona")
    
    # Teste 6: Simular uso com RETURNING id
    returning_desc = [('id',)]
    returning_values = (42,)
    row_id = PostgresRow(returning_values, returning_desc)
    
    # O código faz: cursor.fetchone()[0]
    assert row_id[0] == 42, "RETURNING id falhou"
    print("✅ Teste 6: RETURNING id funciona (row[0])")
    
    print("\n🎉 Todos os testes de PostgresRow passaram!")

if __name__ == "__main__":
    test_postgres_row()
