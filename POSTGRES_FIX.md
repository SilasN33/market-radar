# Correção do Erro de Conexão PostgreSQL no Vercel

## Problema Identificado

O erro no log da Vercel:
```
psycopg2.OperationalError: could not translate host name "33$@db.qjiwyqnvvmpizvfzbvid.supabase.co" to address: System error
```

Este erro ocorria porque a URL de conexão do PostgreSQL (`DATABASE_URL`) continha **caracteres especiais na senha** (como `$`, `@`, etc.) que não estavam sendo tratados corretamente.

## Causa Raiz

O formato de uma URL de conexão PostgreSQL é:
```
postgresql://usuario:senha@host:porta/database
```

Quando a senha contém caracteres especiais como `$`, `@`, `%`, etc., esses caracteres podem ser interpretados incorretamente se não forem escapados ou parseados adequadamente.

No código original (`database_patch.py`), a URL estava sendo passada diretamente para `psycopg2.connect()`:
```python
self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
```

Isso fazia com que caracteres especiais na senha quebrassem o parsing da URL.

## Solução Implementada

### 1. Parsing Correto da URL (`database_patch.py`)

Atualizamos o `database_patch.py` para fazer o **parsing adequado da URL** usando `urllib.parse`:

```python
from urllib.parse import urlparse, unquote

# Parse DATABASE_URL to handle special characters correctly
parsed = urlparse(DATABASE_URL)

# Build connection parameters safely
conn_params = {
    'host': parsed.hostname,
    'port': parsed.port or 5432,
    'database': parsed.path.lstrip('/'),
    'user': unquote(parsed.username) if parsed.username else None,
    'password': unquote(parsed.password) if parsed.password else None,
    'sslmode': 'require'
}

# Connect using named parameters instead of connection string
self.conn = psycopg2.connect(**conn_params)
```

A função `unquote()` decodifica caracteres especiais que estão codificados na URL (como `%24` para `$`).

### 2. Garantir Importação do Patch

Atualizamos os seguintes arquivos para **importar o `database_patch` ANTES do `database`**:

- ✅ `api/auth.py`
- ✅ `scoring/ranker.py`
- ✅ `sources/mercado_livre.py`

Isso garante que o monkey patch seja aplicado antes de qualquer tentativa de conexão.

## Como Verificar se Funcionou

1. Depois de fazer o deploy no Vercel, verifique os logs para a mensagem:
   ```
   [database_patch] ✅ Using Postgres (Supabase) - Host: db.qjiwyqnvvmpizvfzbvid.supabase.co
   ```

2. Tente fazer login na aplicação - o endpoint `/api/auth/login` deve funcionar sem erros.

## Arquivos Modificados

1. `sources/database_patch.py` - Adicionado parsing correto da URL
2. `api/auth.py` - Adicionada importação do patch
3. `scoring/ranker.py` - Adicionada importação do patch
4. `sources/mercado_livre.py` - Adicionada importação do patch

## Teste Local

Para testar o parsing de URLs localmente:
```bash
py test_url_parsing.py
```

## Próximos Passos

1. Fazer commit das alterações
2. Fazer push para o repositório
3. Aguardar o deploy automático no Vercel
4. Verificar os logs do Vercel para confirmar que não há mais erros
5. Testar a funcionalidade de login

## Referências

- [psycopg2 Connection Parameters](https://www.psycopg.org/docs/module.html#psycopg2.connect)
- [URL Parsing - Python urllib.parse](https://docs.python.org/3/library/urllib.parse.html)
- [PostgreSQL Connection URIs](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING)
