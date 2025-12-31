# 🚀 Deploy Rápido - ERP JSP PWA

## 📝 Script de Deploy Automático

Use o script `deploy_pwa.py` para facilitar o processo de atualização e deploy.

### Como usar:

#### 1️⃣ **Para pequenas correções (patch):**
```bash
python deploy_pwa.py
# ou
python deploy_pwa.py patch
```
Incrementa: v1.0.0 → v1.0.1

#### 2️⃣ **Para novas funcionalidades (minor):**
```bash
python deploy_pwa.py minor
```
Incrementa: v1.0.0 → v1.1.0

#### 3️⃣ **Para mudanças grandes (major):**
```bash
python deploy_pwa.py major
```
Incrementa: v1.0.0 → v2.0.0

---

## 🎯 O que o script faz:

1. ✅ **Detecta a versão atual** do PWA
2. ✅ **Incrementa automaticamente** baseado no tipo
3. ✅ **Atualiza service-worker.js** com nova versão
4. ✅ **Atualiza manifest.json** (opcional)
5. ✅ **Faz commit** com mensagem descritiva
6. ✅ **Push para GitHub** automaticamente
7. ✅ **Render detecta** e faz deploy automático

---

## 📋 Exemplo de uso:

```bash
# Você fez correções no sistema
python deploy_pwa.py patch

# Saída:
============================================================
🚀 Deploy Automático - ERP JSP PWA
============================================================

ℹ️  Obtendo versão atual...
✅ Versão atual: v1.0.0
ℹ️  Incremento: PATCH
✅ Nova versão: v1.0.1

Deseja continuar? (s/n): s

ℹ️  Atualizando arquivos...
✅ service-worker.js atualizado
✅ manifest.json atualizado

ℹ️  Verificando repositório git...
✅ Alterações detectadas

Mensagem de commit (Enter para usar padrão): 

ℹ️  Adicionando alterações ao git...
ℹ️  Fazendo commit...
ℹ️  Enviando para o repositório...
✅ Commit e push realizados com sucesso!

============================================================
✅ DEPLOY CONCLUÍDO COM SUCESSO!
============================================================
✅ Versão v1.0.1 enviada para o repositório
ℹ️  O Render detectará as mudanças e fará deploy automático
ℹ️  Aguarde 5-10 minutos para o deploy completar
```

---

## 🔄 Processo completo:

```
1. Você faz alterações no código
   ↓
2. Executa: python deploy_pwa.py
   ↓
3. Script incrementa versão automaticamente
   ↓
4. Faz commit e push para GitHub
   ↓
5. Render detecta mudanças
   ↓
6. Deploy automático no Render (5-10 min)
   ↓
7. Service Worker detecta nova versão
   ↓
8. Usuários recebem notificação:
   "Nova versão disponível!"
```

---

## 💡 Tipos de incremento:

### **PATCH** (v1.0.X)
Use para:
- Correções de bugs
- Pequenos ajustes visuais
- Correções de texto
- Performance

### **MINOR** (v1.X.0)
Use para:
- Novas funcionalidades
- Melhorias significativas
- Novos módulos
- Novas páginas

### **MAJOR** (vX.0.0)
Use para:
- Mudanças grandes na estrutura
- Breaking changes
- Refatoração completa
- Nova versão do sistema

---

## 🎨 Personalizando a mensagem:

```bash
python deploy_pwa.py patch

# Quando pedir a mensagem:
Mensagem de commit (Enter para usar padrão): fix: Corrigido bug no formulário de clientes

# Resultado do commit:
fix: Corrigido bug no formulário de clientes

- Versão do cache atualizada: v1.0.1
- Data: 31/12/2025 17:30:00
```

---

## 🔍 Verificar versão atual:

```bash
# No código
cat app/static/service-worker.js | grep CACHE_NAME

# Resultado:
const CACHE_NAME = 'erp-jsp-v1.0.1';
```

---

## ⚡ Comandos rápidos:

```bash
# Deploy rápido (patch)
python deploy_pwa.py

# Deploy com nova funcionalidade
python deploy_pwa.py minor

# Deploy de versão maior
python deploy_pwa.py major

# Testar PWA localmente
python testar_pwa.py
```

---

## 🎯 Dicas:

1. **Sempre teste localmente** antes de fazer deploy
2. **Use mensagens descritivas** nos commits
3. **Incremente a versão correta** (patch/minor/major)
4. **Aguarde o deploy completar** antes de testar
5. **Verifique logs no Render** se algo der errado

---

## 📊 Monitoramento:

Depois do deploy:
1. Acesse: https://dashboard.render.com
2. Veja os logs do deploy
3. Confirme que está rodando
4. Teste no navegador
5. Verifique se PWA atualiza

---

**🎊 Agora você tem deploy automático com controle de versão!**

Qualquer mudança que fizer, basta executar `python deploy_pwa.py` e tudo é feito automaticamente! 🚀
