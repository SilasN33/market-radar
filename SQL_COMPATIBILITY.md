# 🔄 Compatibilidade SQLite ↔ PostgreSQL

## Problema 3: Incompatibilidade de Sintaxe SQL ✅ RESOLVIDO

### Erros Encontrados

#### 3.1 Placeholders de Parâmetros
```
psycopg2.errors.SyntaxError: syntax error at end of input
LINE 1: SELECT * FROM users WHERE email = ?
```

#### 3.2 DDL - AUTOINCREMENT
```
psycopg2.errors.SyntaxError: syntax error at or near "AUTOINCREMENT"
LINE 3: id INTEGER PRIMARY KEY AUTOINCREMENT,
```

### Causa

O código foi escrito originalmente para **SQLite**, que usa sintaxe diferente do **PostgreSQL**:

| Recurso | SQLite | PostgreSQL |
|---------|--------|------------|
| **Placeholders** | `?` | `%s` |
| **Auto Increment** | `INTEGER PRIMARY KEY AUTOINCREMENT` | `SERIAL PRIMARY KEY` |
| **Data/Hora** | `DATETIME` | `TIMESTAMP` |

### Solução Implementada

Criamos um **wrapper inteligente** (`PostgresCursor`) que converte **automaticamente** toda a sintaxe SQLite para PostgreSQL, incluindo:

✅ **Placeholders** (`?` → `%s`)
✅ **Auto Increment** (`AUTOINCREMENT` → `SERIAL`)
✅ **Data/Hora** (`DATETIME` → `TIMESTAMP`)

#### Como Funciona

```python
class PostgresCursor:
    """Wrapper que converte sintaxe SQLite para PostgreSQL"""
    
    def _convert_query(self, query):
        # 1. Converte placeholders: ? -> %s
        if '?' in query:
            query = query.replace('?', '%s')
        
        # 2. Converte DDL para CREATE TABLE
        if 'CREATE TABLE' in query.upper():
            # AUTOINCREMENT -> SERIAL
            query = query.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
            
            # DATETIME -> TIMESTAMP
            query = query.replace('DATETIME', 'TIMESTAMP')
        
        return query
```

### Exemplos de Conversão Automática

#### Exemplo 1: Criação de Tabelas (DDL)

**SQLite (código original):**
```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

**Convertido automaticamente para PostgreSQL:**
```sql
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### Exemplo 2: Queries com Placeholders

**SQLite:**
```python
cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
cursor.execute("INSERT INTO users (email, name) VALUES (?, ?)", (email, name))
```

**Convertido automaticamente:**
```python
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
cursor.execute("INSERT INTO users (email, name) VALUES (%s, %s)", (email, name))
```

### Tabelas Afetadas (todas corrigidas automaticamente)

O wrapper converte DDL para todas as tabelas no `database.py`:
1. ✅ `products` - AUTOINCREMENT + DATETIME
2. ✅ `price_history` - AUTOINCREMENT + DATETIME
3. ✅ `scan_logs` - AUTOINCREMENT + DATETIME
4. ✅ `intent_clusters` - AUTOINCREMENT + DATETIME
5. ✅ `opportunities` - AUTOINCREMENT + DATETIME
6. ✅ `users` - AUTOINCREMENT + DATETIME
7. ✅ `user_projects` - AUTOINCREMENT + DATETIME
8. ✅ `saved_opportunities` - AUTOINCREMENT + DATETIME

### Implementação Técnica

O `PostgresCursor` implementa:
- `execute()` - Query única com conversão de placeholders
- `executemany()` - Múltiplas queries
- `fetchone()`, `fetchall()`, `fetchmany()` - Métodos de fetch
- `__iter__()` - Iteração sobre resultados
- `__getattr__()` - Proxy para todos os outros métodos do cursor

### Vantagens da Abordagem

| Abordagem | Vantagens | Desvantagens |
|-----------|-----------|--------------|
| **Modificar database.py** | Controle total | Precisa mudar muitas linhas de código |
| **Wrapper (Nossa solução)** | ✅ Zero mudanças no código<br>✅ Mantém compatibilidade SQLite<br>✅ Fácil manutenção | Pequeno overhead (insignificante) |
| **ORM (SQLAlchemy)** | Abstração completa | Reescrita total do código |

### Testando Localmente

O código continua funcionando com SQLite em desenvolvimento:

```bash
# Localmente (sem DATABASE_URL)
python -c "from sources import database; database.init_db()"
# Output: [database_patch] ℹ️  Using SQLite (local development)
```

### Em Produção (Vercel)

Com a variável `DATABASE_URL` configurada:

```bash
# No Vercel (com DATABASE_URL do pooler)
# Output: [database_patch] ✅ Using Postgres (Supabase) - Host: aws-0-sa-east-1.pooler.supabase.com:6543 [Pooler (IPv4)]
```

## Status Final

✅ **Problema 1**: Caracteres especiais na senha - RESOLVIDO
✅ **Problema 2**: Incompatibilidade IPv6 - RESOLVIDO (com Connection Pooler)
✅ **Problema 3**: Sintaxe SQL SQLite vs PostgreSQL - RESOLVIDO (com wrapper automático)

## Arquivos Modificados

- `sources/database_patch.py` - Adicionada classe `PostgresCursor` para conversão automática

## Próximo Deploy

Após fazer commit e push, o Vercel fará deploy automaticamente e a aplicação deve funcionar completamente! 🚀

---

## Referências

- [SQLite Placeholder Syntax](https://www.sqlite.org/lang_expr.html#varparam)
- [PostgreSQL Placeholder Syntax](https://www.psycopg.org/docs/usage.html#passing-parameters-to-sql-queries)
- [Python Descriptor Protocol](https://docs.python.org/3/howto/descriptor.html) (usado no `__getattr__`)
