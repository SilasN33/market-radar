# Vercel Deployment Guide - Market Radar

## 🚀 Deploy Grátis na Vercel

### Pré-requisitos
1. Conta GitHub (gratuita)
2. Conta Vercel (gratuita) - https://vercel.com
3. Código no GitHub

---

## 📋 Passo a Passo

### 1. Preparar o Repositório GitHub

```bash
# No diretório do projeto
git init
git add .
git commit -m "Initial commit - Market Radar SaaS"

# Criar repositório no GitHub e conectar
git remote add origin https://github.com/SEU_USUARIO/market-radar.git
git branch -M main
git push -u origin main
```

### 2. Configurar Vercel Postgres (Gratuito)

1. Acesse https://vercel.com
2. Faça login com GitHub
3. Vá em **Storage** → **Create Database** → **Postgres**
4. Nome: `market-radar-db`
5. Região: Escolha a mais próxima (ex: `iad1` para US East)
6. Copie a `DATABASE_URL` que será gerada

### 3. Deploy na Vercel

#### Opção A: Via Interface Web (Mais Fácil)

1. No Vercel Dashboard, clique **Add New** → **Project**
2. Importe seu repositório GitHub
3. Configure:
   - **Framework Preset**: Other
   - **Root Directory**: `./`
   - **Build Command**: (deixe vazio)
   - **Output Directory**: `web`

4. **Environment Variables**:
   ```
   DATABASE_URL=<cole-a-url-do-postgres>
   OPENAI_API_KEY=<sua-chave-openai>
   FLASK_SECRET_KEY=<gere-uma-chave-segura>
   ```

5. Clique **Deploy**

#### Opção B: Via CLI

```bash
# Instalar Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel

# Configurar environment variables
vercel env add DATABASE_URL
vercel env add OPENAI_API_KEY
vercel env add FLASK_SECRET_KEY
```

### 4. Migração do Banco de Dados

Como estamos usando Postgres agora, precisamos adaptar:

```bash
# Instalar psycopg2
pip install psycopg2-binary

# Criar tabelas no Postgres
python scripts/migrate_to_postgres.py
```

O script `migrate_to_postgres.py` (criado abaixo) irá:
- Conectar no Vercel Postgres
- Criar todas as tabelas
- Migrar dados do SQLite (se houver)

### 5. Automatizar Pipeline com GitHub Actions

O pipeline roda automaticamente a cada 6 horas via GitHub Actions (gratuito).

Arquivo já criado: `.github/workflows/pipeline.yml`

Adicione os **Secrets** no GitHub:
1. Vá em **Settings** → **Secrets and variables** → **Actions**
2. Adicione:
   - `DATABASE_URL`
   - `OPENAI_API_KEY`

---

## 🎯 Estrutura Final

```
Vercel (Gratuito)
├── Frontend Estático → /web/*
├── API Serverless → /api/*
└── Postgres Database → Vercel Storage

GitHub Actions (Gratuito)
└── Pipeline a cada 6h → Alimenta DB
```

---

## 💰 Custos (Tier Gratuito)

| Serviço | Limite Gratuito | Suficiente? |
|---------|-----------------|-------------|
| **Vercel Hosting** | 100 GB bandwidth/mês | ✅ Sim |
| **Vercel Functions** | 100 GB-hours/mês | ✅ Sim |
| **Vercel Postgres** | 256 MB storage | ✅ Para MVP |
| **GitHub Actions** | 2,000 minutos/mês | ✅ Sim (pipeline usa ~10min) |

**Total: R$ 0/mês** 🎉

---

## 🔧 Troubleshooting

### Erro: "Database connection failed"
- Verifique se `DATABASE_URL` está nas env vars
- Teste conexão localmente primeiro

### Erro: "Function timeout"
- Pipeline longo demovido → Use GitHub Actions
- Funções serverless têm timeout de 10s (free tier)

### Erro: "Module not found"
- Certifique-se que `requirements.txt` está completo
- Vercel instala deps automaticamente

---

## 🔄 Atualizações

Qualquer `git push` para `main` triggers automatic redeploy:

```bash
git add .
git commit -m "Update feature X"
git push origin main
# Vercel deployed automaticamente em ~30s
```

---

## 📊 Monitoramento

Acesse Vercel Dashboard → Seu Projeto:
- **Analytics**: Tráfego, performance
- **Logs**: Debug serverless functions
- **Deployments**: Histórico de deploys

---

## 🚀 URLs Finais

Após deploy, você terá:
```
Landing: https://market-radar.vercel.app
Dashboard: https://market-radar.vercel.app (com login)
API: https://market-radar.vercel.app/api/*
```

---

## ⚡ Performance Esperada

- **Landing Page**: ~200ms load
- **Dashboard**: ~500ms load
- **API calls**: ~300ms average
- **Database queries**: ~50ms

Tudo na edge network da Vercel (super rápido)! 🔥
