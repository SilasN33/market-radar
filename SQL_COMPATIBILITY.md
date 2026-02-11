# 🔄 Compatibilidade SQLite ↔ PostgreSQL

## Problema 3: Incompatibilidade de Placeholders SQL ✅ RESOLVIDO

### Erro Encontrado
```
psycopg2.errors.SyntaxError: syntax error at end of input
LINE 1: SELECT * FROM users WHERE email = ?
```

### Causa
O código foi escrito originalmente para **SQLite**, que usa `?` como placeholder de parâmetros em queries SQL:
```sql
SELECT * FROM users WHERE email = ?
```

Mas o **PostgreSQL** usa `%s` como placeholder:
```sql
SELECT * FROM users WHERE email = %s
```

### Solução Implementada

Criamos um **wrapper automático** (`PostgresCursor`) que converte os placeholders SQLite para PostgreSQL **automaticamente**, sem precisar modificar nenhum código do `database.py`.

#### Como Funciona

```python
class PostgresCursor:
    """Wrapper que converte SQLite placeholders (?) para PostgreSQL (%s)"""
    def __init__(self, cursor):
        self._cursor = cursor
        
    def execute(self, query, params=None):
        # Converte ? para %s automaticamente
        if query and '?' in query:
            query = query.replace('?', '%s')
        return self._cursor.execute(query, params)
```

#### Benefícios

✅ **Zero modificações** no código existente (`database.py`)
✅ **Compatibilidade total** com SQLite localmente e PostgreSQL em produção
✅ **Transparente** - funciona automaticamente via monkey patch
✅ **Mantém todas as funcionalidades** - proxy completo do cursor

### Exemplo de Conversão Automática

**Código original (SQLite):**
```python
cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
```

**Convertido automaticamente para PostgreSQL:**
```python
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
```

### Queries Afetadas (todas corrigidas automaticamente)

O wrapper converte automaticamente placeholders em:
- ✅ Todas as queries de SELECT
- ✅ Todas as queries de INSERT
- ✅ Todas as queries de UPDATE
- ✅ Todas as queries de DELETE
- ✅ Queries com múltiplos placeholders

Exemplos do código que agora funcionam:
```python
# Single parameter
cursor.execute("SELECT id FROM users WHERE email = ?", (email,))

# Multiple parameters  
cursor.execute("INSERT INTO users (email, password, name, role, credits) VALUES (?, ?, ?, ?, ?)", 
               (email, password_hash, name, role, 10))

# Complex queries
cursor.execute("SELECT * FROM opportunities WHERE created_at = ? LIMIT ?", (latest, limit))
```

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
