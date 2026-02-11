# 🔧 Problema: Row Factory Incompatibilidade

## Problema 5: Incompatibilidade de Row Objects ✅ RESOLVIDO

### Erro Encontrado
```
[error] Failed to create user: 0
HTTP 409 - Conflict
```

### Causa

O erro ocorria ao tentar criar usuários porque havia incompatibilidade entre como o SQLite e o PostgreSQL retornam resultados de queries:

**SQLite:**
- Usa `sqlite3.Row` objects
- Permite acesso por **índice** (`row[0]`) E por **nome** (`row['email']`)
- Funciona com `dict(row)` para conversão

**PostgreSQL com RealDictCursor (tentativa inicial):**
- Retorna **dicionários puros** `{'id': 1, 'email': 'test@example.com'}`
- Acesso por **nome** funciona (`row['email']`)
- Acesso por **índice NÃO funciona** (`row[0]` ❌ causa erro)

**Código problemático:**
```python
cursor.execute("INSERT INTO users (...) RETURNING id", (...))
user_id = cursor.fetchone()[0]  # ❌ Falha com RealDictCursor
```

### Solução Implementada

Criamos um **`PostgresRow`** customizado que emula completamente o comportamento do `sqlite3.Row`:

```python
class PostgresRow:
    """Compatível com sqlite3.Row - acesso por índice E por nome"""
    def __init__(self, values, description):
        self._values = values  # Tupla original
        self._description = description  # Metadados das colunas
        self._mapping = {desc[0]: val for desc, val in zip(description, values)}
    
    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]  # Acesso por índice
        return self._mapping[key]      # Acesso por nome
```

### Funcionalidades Suportadas

| Operação | SQLite | PostgreSQL (Nossa Solução) | RealDictCursor |
|----------|--------|---------------------------|----------------|
| `row[0]` | ✅ | ✅ | ❌ |
| `row['email']` | ✅ | ✅ | ✅ |
| `list(row)` | ✅ | ✅ | ✅ |
| `dict(row)` | ✅ | ✅ | ✅ |
| `len(row)` | ✅ | ✅ | ✅ |

### Exemplos de Uso

#### Exemplo 1: RETURNING id (caso problemático)

**Código no database.py:**
```python
cursor.execute("""
    INSERT INTO users (email, password_hash, name, role, credits)
    VALUES (?, ?, ?, ?, ?)
    RETURNING id
""", (email, password_hash, name, role, 10))

user_id = cursor.fetchone()[0]  # ✅ Funciona agora!
```

**Como funciona:**
- PostgreSQL retorna: `(42,)` (tupla)
- `PostgresRow` transforma em objeto que aceita `[0]`
- `user_id` recebe `42`

#### Exemplo 2: SELECT com acesso misto

**Código no database.py:**
```python
cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
row = cursor.fetchone()

# Ambos funcionam:
user_id = row[0]           # Acesso por índice ✅
email = row['email']       # Acesso por nome ✅
user_dict = dict(row)      # Conversão para dict ✅
```

### Queries Afetadas (todas corrigidas)

Todas as queries com `RETURNING id` agora funcionam:
1. ✅ `create_user()` - linha 395
2. ✅ `upsert_product()` - linha 170
3. ✅ `save_cluster()` - linha 242
4. ✅ `save_opportunity()` - linha 281
5. ✅ `save_opportunity_for_user()` - linha 441
6. ✅ `create_project()` - linha 474

### Vantagens da Abordagem

| Aspecto | Nossa Solução | Alternativa (Modificar database.py) |
|---------|---------------|-------------------------------------|
| **Mudanças no código** | Zero | Muitas linhas |
| **Compatibilidade SQLite** | ✅ Total | ⚠️ Precisaria condicionais |
| **Compatibilidade PostgreSQL** | ✅ Total | ✅ |
| **Manutenção** | ✅ Simples | ⚠️ Complexa |

### Implementação Técnica

O `PostgresCursor` wrapper agora:

1. **Intercepta `fetchone()`, `fetchall()`, `fetchmany()`**
   ```python
   def fetchone(self):
       row = self._cursor.fetchone()
       return self._make_row(row) if row else None
   ```

2. **Converte tuplas em PostgresRow**
   ```python
   def _make_row(self, values):
       if values is None or self._cursor.description is None:
           return values
       return PostgresRow(values, self._cursor.description)
   ```

3. **PostgresRow emula sqlite3.Row**
   - Acesso por índice: `__getitem__(int)`
   - Acesso por nome: `__getitem__(str)`
   - Iteração: `__iter__()`
   - Conversão: `keys()`, `values()`, `items()`

### Testado e Validado

```bash
py test_postgres_row.py
```

```
✅ Teste 1: Acesso por índice funciona
✅ Teste 2: Acesso por nome funciona
✅ Teste 3: Iteração funciona
✅ Teste 4: Conversão para dict funciona
✅ Teste 5: len() funciona
✅ Teste 6: RETURNING id funciona (row[0])

🎉 Todos os testes de PostgresRow passaram!
```

## Resumo dos Problemas e Soluções

| # | Problema | Causa | Solução |
|---|----------|-------|---------|
| 1️⃣ | Caracteres especiais | Senha com `$`, `@` | `urlparse()` + `unquote()` |
| 2️⃣ | IPv6 no Vercel | Porta 5432 usa IPv6 | Connection Pooler (6543) |
| 3️⃣ | Placeholders `?` vs `%s` | Sintaxe diferente | Conversão automática `?` → `%s` |
| 4️⃣ | DDL `AUTOINCREMENT` | Sintaxe diferente | Conversão `AUTOINCREMENT` → `SERIAL` |
| 5️⃣ | Row objects | RealDictCursor não suporta `[0]` | **PostgresRow customizado** |

## Arquivos Modificados

1. `sources/database_patch.py` - Adicionada classe `PostgresRow`
2. `test_postgres_row.py` - Testes de validação

---

**Status**: ✅ Todas as incompatibilidades resolvidas! O sistema agora funciona perfeitamente com SQLite (desenvolvimento) e PostgreSQL (produção) sem modificar nenhuma linha do `database.py`.
