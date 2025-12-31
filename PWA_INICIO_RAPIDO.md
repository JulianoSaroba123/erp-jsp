# 📱 PWA - Início Rápido

## ✅ Status: CONFIGURADO!

O ERP JSP agora é um **Progressive Web App** completo!

## 🚀 Como Testar (Local)

### Opção 1: Com ngrok (Recomendado - Mais Fácil)
```bash
# Terminal 1: Execute o servidor
python run.py

# Terminal 2: Crie túnel HTTPS
# Baixe: https://ngrok.com/download
ngrok http 5000

# Acesse a URL HTTPS fornecida (ex: https://abc123.ngrok.io)
```

### Opção 2: Certificado SSL Local
```bash
# Instale mkcert
# Windows: choco install mkcert

# Gere certificados
mkcert localhost

# Execute com SSL (edite run.py se necessário)
```

## 📱 Instalar no Celular

1. Acesse o site via HTTPS
2. **Android**: Menu ⋮ → "Adicionar à tela inicial"
3. **iOS**: Compartilhar → "Adicionar à Tela de Início"

## 🖥️ Instalar no Desktop

1. Chrome/Edge: Ícone de instalação na barra de endereço
2. Ou banner que aparece após 10 segundos

## 🧪 Testar Configuração

```bash
python testar_pwa.py
```

## 📊 Auditoria Lighthouse

1. F12 → Lighthouse
2. Selecione "Progressive Web App"
3. "Generate report"

## 📚 Documentação Completa

Ver: `GUIA_PWA.md`

---

**🎉 Pronto para usar!**
