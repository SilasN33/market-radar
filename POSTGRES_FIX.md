# Correção de Erros de Conexão PostgreSQL no Vercel

## Problema 1: Caracteres Especiais na Senha ✅ RESOLVIDO

### Erro Inicial
```
psycopg2.OperationalError: could not translate host name "33$@db.qjiwyqnvvmpizvfzbvid.supabase.co" to address: System error
```

### Causa
A URL de conexão do PostgreSQL continha **caracteres especiais na senha** (como `$`, `@`, etc.) que não estavam sendo tratados corretamente.

### Solução Implementada
Atualizamos o `database_patch.py` para fazer o **parsing adequado da URL** usando `urllib.parse`:

```python
from urllib.parse import urlparse, unquote

parsed = urlparse(DATABASE_URL)
conn_params = {
    'host': parsed.hostname,
    'port': parsed.port or 5432,
    'database': parsed.path.lstrip('/'),
    'user': unquote(parsed.username) if parsed.username else None,
    'password': unquote(parsed.password) if parsed.password else None,
    'sslmode': 'require'
}
```

---

## Problema 2: Incompatibilidade IPv6 no Vercel 🔧 REQUER CONFIGURAÇÃO

### Erro Atual
```
psycopg2.OperationalError: connection to server at "db.qjiwyqnvvmpizvfzbvid.supabase.co" (2600:1f1e:75b:4b0e:17ae:eb57:7a6c:37f), port 5432 failed: Cannot assign requested address
```

### Causa
O Vercel tem problemas com conexões IPv6. A conexão direta do Supabase (porta 5432) usa IPv6, causando falhas de conexão no ambiente serverless do Vercel.

### Solução: Usar o Connection Pooler do Supabase

O Supabase oferece um **Connection Pooler** (porta 6543) que:
- ✅ É compatível com IPv4
- ✅ Foi projetado para ambientes serverless
- ✅ Gerencia conexões de forma mais eficiente

### ⚠️ AÇÃO NECESSÁRIA NO VERCEL

**Você precisa atualizar a variável `DATABASE_URL` no Vercel para usar o Connection Pooler:**

1. **Obter URL do Pooler no Supabase:**
   - Acesse [Supabase Dashboard](https://app.supabase.com)
   - Settings → Database → Connection String
   - Selecione **"Transaction"** mode (porta 6543)
   - Copie a URL do pooler:
     ```
     postgresql://postgres.PROJECT_REF:[PASSWORD]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
     ```
     **Importante**: Note o `.pooler.` no hostname e a porta `6543`

2. **Atualizar no Vercel:**
   - Acesse [Vercel Dashboard](https://vercel.com)
   - Settings → Environment Variables
   - Atualize `DATABASE_URL` com a URL do pooler
   - Marque: Production, Preview, Development
   - Salve

3. **Fazer Redeploy:**
   - Deployments → último deployment → Redeploy
   - **Desmarque** "Use existing Build Cache"

### Verificação
Após o redeploy, nos logs você deve ver:
```
[database_patch] ✅ Using Postgres (Supabase) - Host: aws-0-sa-east-1.pooler.supabase.com:6543 [Pooler (IPv4)]
```

---

## Melhorias Implementadas no Código

### 1. Suporte a Connection Pooler (`database_patch.py`)
- ✅ Detecção automática se está usando pooler (porta 6543)
- ✅ Configurações otimizadas para serverless (timeouts, keepalives)
- ✅ Melhor tratamento de erros com mensagens informativas

### 2. Configurações de Conexão Otimizadas
```python
conn_params = {
    # ... outros parâmetros
    'connect_timeout': 10,
    'keepalives': 1,
    'keepalives_idle': 30,
    'keepalives_interval': 10,
    'keepalives_count': 5,
}
```

### 3. Importação do Patch em Todos os Arquivos
- ✅ `api/auth.py`
- ✅ `scoring/ranker.py`
- ✅ `sources/mercado_livre.py`

---

## Arquivos Modificados

1. `sources/database_patch.py` - Parsing de URL + configurações serverless
2. `api/auth.py` - Importação do patch
3. `scoring/ranker.py` - Importação do patch
4. `sources/mercado_livre.py` - Importação do patch
5. `VERCEL_SUPABASE_SETUP.md` - Guia completo de configuração

---

## 📚 Documentação Adicional

Para instruções detalhadas sobre como configurar o Connection Pooler, consulte:
- **[VERCEL_SUPABASE_SETUP.md](./VERCEL_SUPABASE_SETUP.md)** - Guia passo a passo completo

## Comparação: Direct vs Pooler

| Característica | Direct (5432) | Pooler (6543) |
|---|---|---|
| **Vercel** | ❌ Problemas IPv6 | ✅ IPv4 compatível |
| **Serverless** | ⚠️ Nova conexão/request | ✅ Reutiliza conexões |
| **Recomendado para** | Apps tradicionais | Vercel/Serverless |

## Referências

- [Supabase Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [Vercel + Supabase Guide](https://vercel.com/guides/nextjs-prisma-postgres)
- [psycopg2 Docs](https://www.psycopg.org/docs/module.html#psycopg2.connect)

