# 🔧 Configuração do Supabase Connection Pooler para Vercel

## ⚠️ Problema Atual

O erro que você está vendo:
```
psycopg2.OperationalError: connection to server at "db.qjiwyqnvvmpizvfzbvid.supabase.co" (2600:1f1e:75b:4b0e:17ae:eb57:7a6c:37f), port 5432 failed: Cannot assign requested address
```

**Causa**: O Vercel tem problemas com conexões IPv6, e a conexão direta do Supabase (porta 5432) usa IPv6 por padrão.

## ✅ Solução: Usar o Connection Pooler do Supabase

O Supabase oferece um **Connection Pooler** (porta 6543) que:
- É compatível com IPv4
- Foi projetado especificamente para ambientes serverless como Vercel
- Gerencia conexões de forma mais eficiente

## 📋 Passos para Configurar

### 1️⃣ Obter a Connection String do Pooler no Supabase

1. Acesse seu projeto no [Supabase Dashboard](https://app.supabase.com)
2. Vá em **Settings** (⚙️) → **Database**
3. Role até **Connection String**
4. Você verá duas opções:
   - **Direct connection** (porta 5432) - ❌ Não funciona bem no Vercel
   - **Transaction pooler** (porta 6543) - ✅ Use esta!

5. Selecione **"Transaction"** ou **"Session"** mode
6. Copie a connection string que deve ter este formato:
   ```
   postgresql://postgres.PROJECT_REF:[PASSWORD]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
   ```
   
   **Observação importante**: Note o `.pooler.` no hostname e a porta `6543`

### 2️⃣ Configurar no Vercel

1. Acesse seu projeto no [Vercel Dashboard](https://vercel.com)
2. Vá em **Settings** → **Environment Variables**
3. **SUBSTITUA** a variável `DATABASE_URL` atual pela connection string do **pooler**:
   - Name: `DATABASE_URL`
   - Value: `postgresql://postgres.PROJECT_REF:[SUA_SENHA]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres`
   - Environments: ✅ Production, ✅ Preview, ✅ Development

4. Clique em **Save**

### 3️⃣ Fazer Redeploy

Após salvar a nova variável de ambiente:

1. Vá em **Deployments**
2. Clique nos 3 pontinhos do último deployment
3. Selecione **Redeploy**
4. ✅ Certifique-se de marcar "Use existing Build Cache" = **OFF** para forçar um rebuild completo

## 🔍 Como Verificar se Está Funcionando

Após o redeploy, verifique os logs do Vercel. Você deve ver:

```
[database_patch] ✅ Using Postgres (Supabase) - Host: aws-0-sa-east-1.pooler.supabase.com:6543 [Pooler (IPv4)]
```

Se ainda estiver usando a porta 5432, você verá:
```
[database_patch] ✅ Using Postgres (Supabase) - Host: db.qjiwyqnvvmpizvfzbvid.supabase.co:5432 [Direct (may use IPv6)]
```

## 🆚 Comparação: Direct vs Pooler

| Característica | Direct Connection (5432) | Connection Pooler (6543) |
|---|---|---|
| **Compatibilidade Vercel** | ❌ Problemas com IPv6 | ✅ IPv4 compatível |
| **Performance Serverless** | ⚠️ Abre nova conexão a cada request | ✅ Reutiliza conexões |
| **Ideal para** | Aplicações tradicionais | Serverless/Edge functions |
| **Limite de conexões** | Limitado pelo banco | Gerenciado pelo pooler |

## 🔐 Importante: Segurança

- ✅ **SEMPRE** use `sslmode=require` (já configurado no código)
- ✅ Certifique-se de que a senha não contém caracteres especiais sem escape
- ✅ Mantenha as variáveis de ambiente privadas no Vercel
- ✅ Não commite a `DATABASE_URL` no código

## 🆘 Troubleshooting

### Problema: Ainda vejo erro de conexão

1. **Verifique a senha**: Certifique-se de que a senha do banco está correta
2. **Verifique IP restrictions**: No Supabase Dashboard → Settings → Database → Network Restrictions, certifique-se de que está em "Allow all IP addresses"
3. **Verifique o formato da URL**: Deve incluir `.pooler.` e porta `6543`

### Problema: "Password authentication failed"

- A senha pode estar incorreta ou conter caracteres especiais
- Obtenha a senha correta do Supabase Dashboard
- Se tiver caracteres especiais, o código já faz o unquote automaticamente

### Problema: "Database does not exist"

- Certifique-se de que o nome do banco na URL está correto (geralmente `postgres`)

## 📚 Referências

- [Supabase Connection Pooling Documentation](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [Vercel + Supabase Integration Guide](https://vercel.com/guides/nextjs-prisma-postgres)
- [psycopg2 Connection Parameters](https://www.psycopg.org/docs/module.html#psycopg2.connect)

---

## 🎯 Resumo Rápido

**Para resolver o erro:**
1. Acesse Supabase → Database → Connection String
2. Copie a URL do **Transaction Pooler** (porta 6543)
3. No Vercel → Settings → Environment Variables
4. Atualize `DATABASE_URL` com a URL do pooler
5. Faça Redeploy (sem cache)
6. Verifique os logs - deve mostrar "Pooler (IPv4)"

✅ Pronto! Sua aplicação deve conectar sem erros.
