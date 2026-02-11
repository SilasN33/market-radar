# Deploy Vercel + Supabase (100% Gratuito)

## 🎯 Stack Completa Gratuita

- **Frontend + API**: Vercel (grátis)
- **Database**: Supabase Postgres (grátis - 500 MB)
- **Pipeline**: GitHub Actions (grátis)

---

## 📋 Passo 1: Configurar Supabase (5 minutos)

### 1.1 Criar Conta e Projeto

1. Acesse https://supabase.com
2. Clique **Start your project**
3. Faça login com GitHub
4. Clique **New Project**
5. Preencha:
   - **Name**: `market-radar`
   - **Database Password**: Escolha uma senha forte (anote!)
   - **Region**: Escolha a mais próxima (ex: `South America (São Paulo)`)
   - **Pricing Plan**: Free
6. Clique **Create new project**
7. Aguarde ~2 minutos (setup do banco)

### 1.2 Obter Connection String

1. No painel do Supabase, vá em **Settings** (⚙️) → **Database**
2. Role até **Connection string**
3. Selecione **URI** 
4. Copie a string (algo como):
   ```
   postgresql://postgres.abc123:[YOUR-PASSWORD]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
   ```
5. **Substitua `[YOUR-PASSWORD]`** pela senha que você criou
6. **Guarde essa URL** - você vai usar várias vezes

---

## 📋 Passo 2: Migrar Database (Local)

### 2.1 Configurar URL localmente

```powershell
# Cole sua connection string do Supabase
$env:DATABASE_URL="postgresql://postgres.abc123:SUA_SENHA@aws-0-sa-east-1.pooler.supabase.com:6543/postgres"
```

### 2.2 Rodar Migration

```powershell
python scripts/migrate_to_postgres.py
```

Você verá:
```
🔄 Connecting to Supabase Postgres...
📊 Creating tables...
🔍 Creating indexes...
✅ Postgres migration complete!
```

### 2.3 Verificar no Supabase

1. No Supabase, vá em **Table Editor**
2. Você deve ver as tabelas:
   - `products`
   - `trends`
   - `intent_clusters`
   - `opportunities`
   - `users`
   - `user_projects`
   - `saved_opportunities`

---

## 📋 Passo 3: Subir para GitHub

```powershell
# No diretório do projeto
cd c:\Users\silas\.openclaw\workspace\market-radar

# Inicializar Git (se ainda não iniciou)
git init
git add .
git commit -m "Initial commit - Market Radar with Supabase"

# Conectar ao GitHub
git remote add origin https://github.com/SilasN33/market-radar.git
git branch -M main
git push -u origin main
```

Se der erro "src refspec main does not match", faça:
```powershell
git checkout -b main
git push -u origin main
```

---

## 📋 Passo 4: Deploy na Vercel

### 4.1 Conectar Repositório

1. Acesse https://vercel.com
2. Faça login com GitHub
3. Clique **Add New** → **Project**
4. Selecione `market-radar`
5. **NÃO clique Deploy ainda!**

### 4.2 Configurar Environment Variables

Ainda na tela de setup do projeto:

1. Vá em **Environment Variables**
2. Adicione (use Add another para cada):

```
Name: DATABASE_URL
Value: (cole sua connection string do Supabase)

Name: OPENAI_API_KEY
Value: (sua chave OpenAI - sk-...)

Name: FLASK_SECRET_KEY
Value: (gere uma string aleatória - ex: mkt-radar-2026-secret-xyz)
```

### 4.3 Deploy!

1. Clique **Deploy**
2. Aguarde ~2 minutos
3. Pronto! Sua app está no ar 🎉

URL final: `https://market-radar.vercel.app`

---

## 📋 Passo 5: Configurar GitHub Actions (Pipeline)

### 5.1 Adicionar Secrets no GitHub

1. Vá para https://github.com/SilasN33/market-radar
2. Clique **Settings** → **Secrets and variables** → **Actions**
3. Clique **New repository secret**
4. Adicione 2 secrets:

**Secret 1:**
- Name: `DATABASE_URL`
- Value: (sua connection string do Supabase)

**Secret 2:**
- Name: `OPENAI_API_KEY`
- Value: (sua chave OpenAI)

### 5.2 Testar Pipeline Manualmente

1. No GitHub, vá em **Actions**
2. Selecione **Market Radar Pipeline**
3. Clique **Run workflow** → **Run workflow**
4. Aguarde ~5 minutos
5. Verifique se ficou verde (✅)

Se funcionar, o pipeline rodará automaticamente a cada 6 horas!

---

## 🎉 Resultado Final

Você agora tem:

```
┌─────────────────────────────────┐
│   https://market-radar.vercel.app
│                                 │
│  - Landing Page (pública)       │
│  - Dashboard (autenticado)      │
│  - API REST (/api/*)            │
└─────────────┬───────────────────┘
              │
              ↓
┌─────────────────────────────────┐
│      Supabase Postgres          │
│  - 500 MB storage               │
│  - Backups automáticos          │
│  - Interface visual             │
└─────────────────────────────────┘
              ↑
              │
┌─────────────────────────────────┐
│      GitHub Actions             │
│  - Pipeline a cada 6h           │
│  - Alimenta o banco             │
└─────────────────────────────────┘
```

---

## 💰 Custos: R$ 0/mês ✅

| Serviço | Limite Gratuito | Suficiente? |
|---------|-----------------|-------------|
| Vercel | 100 GB bandwidth | ✅ Sim |
| Supabase | 500 MB DB | ✅ Sim |
| GitHub Actions | 2,000 min/mês | ✅ Sim |

---

## 🔧 Troubleshooting

### Erro: "Connection refused" no Supabase
- Verifique se a connection string está correta
- Certifique-se de ter substituído `[YOUR-PASSWORD]`

### Erro: "No module named psycopg2"
```powershell
pip install psycopg2-binary
```

### Pipeline falha no GitHub Actions
- Verifique se os Secrets estão configurados
- Veja os logs em **Actions** → clique no workflow → veja o erro

### Dados não aparecem no dashboard
1. Rode o pipeline manualmente no GitHub Actions
2. Após 5 minutos, recarregue o dashboard

---

## 📊 Visualizar Dados no Supabase

1. Acesse Supabase → **Table Editor**
2. Selecione uma tabela (ex: `opportunities`)
3. Veja todos registros em tempo real
4. Pode editar/deletar manualmente se precisar

---

## 🚀 Comandos Úteis

```powershell
# Testar localmente (com Supabase)
$env:DATABASE_URL="sua-connection-string"
python run_pipeline.py

# Ver logs da Vercel
vercel logs

# Forçar novo deploy
git commit --allow-empty -m "Force redeploy"
git push
```

---

**Tudo 100% grátis e pronto para produção!** 🎉

Qualquer dúvida em algum passo, me avise!
