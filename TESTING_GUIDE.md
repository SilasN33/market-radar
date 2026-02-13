# 🚀 Guia Rápido - Testar Refatoração Premium UI

## Como Visualizar as Mudanças

### Opção 1: Servidor Local (Recomendado)

```bash
# No diretório do projeto
cd c:\Users\silas\.openclaw\workspace\market-radar

# Iniciar servidor Python simples
python -m http.server 8000

# Ou com Node.js
npx http-server -p 8000
```

Depois acesse: `http://localhost:8000/web/index.html`

### Opção 2: Abrir Diretamente no Navegador

1. Navegue até: `c:\Users\silas\.openclaw\workspace\market-radar\web\`
2. Clique com botão direito em `index.html`
3. Abrir com → Chrome/Edge/Firefox

**Nota**: Algumas funcionalidades (fetch API) podem não funcionar sem servidor.

---

## ✨ O Que Testar

### 1. **Background Animado**
- [ ] Observe o gradiente mesh se movendo sutilmente
- [ ] Cores: roxo, rosa e verde em movimento lento

### 2. **Hero Section**
- [ ] Badge "Atualizado em tempo real" flutuando
- [ ] Partículas SVG subindo e descendo
- [ ] Stats pills com contador animado
- [ ] Hover nos pills (elevação + borda roxa)

### 3. **Cards com Tilt 3D**
- [ ] Passe o mouse sobre um card
- [ ] Card deve inclinar na direção do cursor
- [ ] Borda brilhante (glow) roxo→rosa→verde aparece
- [ ] Brilho interno segue o mouse
- [ ] Ao sair, card volta suavemente

### 4. **Glassmorphism**
- [ ] Cards semi-transparentes com blur
- [ ] Bordas roxas sutis
- [ ] Efeito de "shine" deslizante no hover

### 5. **Tipografia**
- [ ] Logo usa Space Grotesk
- [ ] Títulos com gradiente roxo→rosa
- [ ] Corpo de texto em Inter

### 6. **Responsividade**
- [ ] Redimensione a janela
- [ ] Cards se reorganizam (grid adaptativo)
- [ ] Hero Section se ajusta (3rem → 2rem)
- [ ] Stats pills vão para coluna no mobile

---

## 🎨 Paleta de Cores (Referência)

| Elemento | Cor | Hex |
|----------|-----|-----|
| Roxo Neon (Principal) | ![#8b5cf6](https://via.placeholder.com/15/8b5cf6/000000?text=+) | `#8b5cf6` |
| Rosa Secundário | ![#ec4899](https://via.placeholder.com/15/ec4899/000000?text=+) | `#ec4899` |
| Verde Fluorescente | ![#22c55e](https://via.placeholder.com/15/22c55e/000000?text=+) | `#22c55e` |
| Background | ![#0f172a](https://via.placeholder.com/15/0f172a/000000?text=+) | `#0f172a` |

---

## 🐛 Troubleshooting

### Cards não inclinam?
- Verifique se `app.js` está carregando
- Abra DevTools (F12) → Console → Procure por erros

### Stats não aparecem?
- Verifique se a API `/api/ranking` está respondendo
- Pode ser necessário fazer login primeiro

### Fontes não carregam?
- Verifique conexão com internet (Google Fonts)
- Fallback: Inter → system fonts

---

## 📊 Performance Check

Abra DevTools (F12) → Lighthouse → Run Audit

**Esperado**:
- Performance: > 90
- Accessibility: > 85
- Best Practices: > 90

---

## 🎯 Próximos Passos

1. ✅ Testar localmente
2. ✅ Validar responsividade (mobile/tablet/desktop)
3. ⏳ Deploy em staging/produção
4. ⏳ Coletar feedback de usuários
5. ⏳ Implementar Bento Grid (opcional)

---

**Dúvidas?** Consulte `PREMIUM_UI_REFACTOR.md` para documentação completa.
