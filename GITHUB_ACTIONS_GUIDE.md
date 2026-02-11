# 🚀 Guia Visual - Configurar GitHub Actions

## 📍 Passo 1: Acessar Configurações do Repositório

1. **Vá para seu repositório:**
   ```
   https://github.com/SilasN33/market-radar
   ```

2. **Localize a aba "Settings" (⚙️):**
   ```
   [Code] [Issues] [Pull requests] [Actions] [Projects] [Wiki] [Security] [Insights] [⚙️ Settings]
                                                                              ↑
                                                                    Clique aqui!
   ```
   
   **Importante:** 
   - É a última aba no menu horizontal
   - Você precisa ser o **dono do repositório** para ver esta aba
   - Se não aparecer, você não tem permissão de admin

---

## 🔐 Passo 2: Adicionar Secrets (Credenciais)

### 2.1 - Navegue até Secrets

No menu lateral **esquerdo** da página Settings:

```
Settings (lateral esquerdo)
├── General
├── Collaborators
├── Code and automation
│   ├── Branches
│   ├── Tags
│   ├── Actions
│   │   └── Secrets and variables  ← Clique aqui!
│   │       └── Actions            ← Depois clique aqui!
```

**Caminho visual:**
```
Settings → (menu esquerdo) → Secrets and variables → Actions
```

### 2.2 - Adicionar DATABASE_URL

1. **Clique no botão verde "New repository secret"** (canto superior direito)

2. **Preencha o formulário:**
   ```
   Name: DATABASE_URL
   
   Value: postgresql://postgres.PROJECT_REF:[SUA_SENHA]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
   ```
   
   **Onde obter essa URL:**
   - Supabase Dashboard → Settings → Database → Connection String
   - Selecione "Transaction Pooler" (porta 6543)
   - Copie a URL completa

3. **Clique em "Add secret"**

### 2.3 - Adicionar OPENAI_API_KEY (Opcional)

Se você tem uma chave da OpenAI:

1. **Clique em "New repository secret"** novamente

2. **Preencha:**
   ```
   Name: OPENAI_API_KEY
   
   Value: sk-proj-xxxxxxxxxxxxxxxxxxxxx
   ```

3. **Clique em "Add secret"**

**Após adicionar, você verá:**
```
Repository secrets
├── DATABASE_URL         (Updated XX ago)
└── OPENAI_API_KEY       (Updated XX ago)
```

---

## ▶️ Passo 3: Rodar o Workflow

### 3.1 - Ir para a aba Actions

Na navegação principal do repositório:

```
[Code] [Issues] [Pull requests] [▶️ Actions] [Projects] [Wiki]
                                      ↑
                              Clique aqui!
```

### 3.2 - Habilitar Actions (se necessário)

**Se for a primeira vez**, você pode ver uma tela assim:

```
┌────────────────────────────────────────────────┐
│  Workflows aren't being run on this repository │
│                                                │
│  [I understand, enable GitHub Actions]         │
└────────────────────────────────────────────────┘
```

**Clique no botão** para habilitar.

### 3.3 - Selecionar o Workflow

No **menu lateral esquerdo** da página Actions:

```
All workflows
├── Market Radar Pipeline  ← Clique aqui!
```

### 3.4 - Executar Manualmente

Na página do workflow "Market Radar Pipeline":

```
┌─────────────────────────────────────────────────────┐
│  Market Radar Pipeline                              │
│                                                     │
│  [Run workflow ▼]  ← Clique neste botão (azul)     │
└─────────────────────────────────────────────────────┘
```

**Um dropdown vai abrir:**

```
┌────────────────────────────────┐
│ Use workflow from              │
│ Branch: main ▼                 │
│                                │
│ [Run workflow]  ← Clique aqui! │
└────────────────────────────────┘
```

**Após clicar:**
- Um novo workflow run aparecerá na lista
- Status: 🟡 In progress → 🟢 Success (ou 🔴 Failed)

### 3.5 - Acompanhar a Execução

1. **Clique no workflow run** que acabou de iniciar
2. Você verá os jobs:
   ```
   ├── run-pipeline
   │   ├── Set up job
   │   ├── Run actions/checkout@v3
   │   ├── Set up Python
   │   ├── Install dependencies
   │   ├── Run Intent Signals       🟡 (executando...)
   │   ├── Run AI Processor
   │   ├── Run Mercado Livre Scraper
   │   ├── Run Ranker
   │   └── Complete job
   ```

3. **Clique em qualquer step** para ver os logs detalhados

**Tempo estimado:** ~3-5 minutos

---

## ✅ Verificar se Funcionou

### No Dashboard

1. **Acesse sua aplicação:**
   ```
   https://market-radar-XXXXXXX.vercel.app
   ```

2. **Faça login**

3. **Você deve ver:**
   - 🏆 Top Oportunidades com scores
   - 📊 KPIs (Total de oportunidades, score médio, etc)
   - 🛍️ Lista de produtos

### Nos Logs do GitHub Actions

Status **🟢 Success** significa que:
- ✅ Sinais coletados
- ✅ IA processou (se OPENAI_API_KEY configurado)
- ✅ Produtos scrapados do Mercado Livre
- ✅ Ranking gerado e salvo no banco

---

## 🔄 Automação

Após a primeira execução manual, o workflow vai rodar **automaticamente**:

```
Agendamento: A cada 6 horas
Próximas execuções:
├── 06:00 UTC (03:00 BRT)
├── 12:00 UTC (09:00 BRT)
├── 18:00 UTC (15:00 BRT)
└── 00:00 UTC (21:00 BRT)
```

---

## 🆘 Troubleshooting

### "Aba Actions não aparece"

**Solução:**
1. Settings → Actions → General
2. Em "Actions permissions":
   - Selecione: ✅ "Allow all actions and reusable workflows"
3. Save

### "Workflow falhou"

**Verifique os logs:**
1. Actions → Market Radar Pipeline → (clique no run falho)
2. Clique no step que falhou (🔴)
3. Veja o erro no log

**Erros comuns:**
- ❌ `DATABASE_URL` não configurado → Adicione o secret
- ❌ `OPENAI_API_KEY` inválido → Verifique a chave
- ❌ Rate limit do scraping → Normal, vai funcionar na próxima

### "Secret não aparece depois de adicionar"

**Normal!** Por segurança, secrets não mostram o valor, apenas:
```
DATABASE_URL (Updated XX minutes ago)
```

---

## 📚 Próximos Passos

Após configurar:

1. ✅ **Primeira execução manual** - Para popular o banco imediatamente
2. ⏰ **Deixar automático** - Vai rodar a cada 6 horas
3. 📊 **Monitorar no dashboard** - Ver os produtos atualizando
4. 🔄 **Rodar manualmente** quando quiser - Sempre disponível

---

## 🎯 Resumo Rápido

```bash
# 1. Adicionar secrets
GitHub → Settings → Secrets and variables → Actions
  → New repository secret
  → DATABASE_URL = postgresql://...pooler.supabase.com:6543/postgres
  → OPENAI_API_KEY = sk-... (opcional)

# 2. Rodar workflow
GitHub → Actions → Market Radar Pipeline
  → Run workflow → Branch: main → Run workflow

# 3. Aguardar conclusão (~3-5 min)
# 4. Verificar dashboard
```

Pronto! 🎉
