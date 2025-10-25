# 🚀 Guia de Deploy - ERP JSP v3.0

## 📋 Pré-requisitos

✅ Git configurado e repositório inicializado  
✅ Código commitado localmente  
✅ Conta no GitHub  
✅ Conta no Render.com  

## 🔗 1. Conectar com GitHub

### 1.1 Criar repositório no GitHub
1. Acesse [github.com](https://github.com)
2. Clique em "New repository"
3. Nome: `erp-jsp-v3`
4. Descrição: `Sistema ERP JSP v3.0 - Flask com Autenticação`
5. **NÃO** marque "Initialize with README" (já temos)
6. Clique em "Create repository"

### 1.2 Conectar repositório local
```bash
# Adicionar remote origin
git remote add origin https://github.com/SEU_USUARIO/erp-jsp-v3.git

# Verificar se foi adicionado
git remote -v

# Fazer o primeiro push
git branch -M main
git push -u origin main
```

## 🌐 2. Deploy no Render

### 2.1 Criar serviço no Render
1. Acesse [render.com](https://render.com)
2. Clique em "New +" → "Web Service"
3. Conecte sua conta GitHub
4. Selecione o repositório `erp-jsp-v3`
5. Configure:
   - **Name**: `erp-jsp-v3`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app.app:app`

### 2.2 Configurar Banco PostgreSQL
1. No dashboard do Render, clique em "New +" → "PostgreSQL"
2. Configure:
   - **Name**: `erp-jsp-db`
   - **Database**: `erp_jsp`
   - **User**: `erp_jsp_user`
3. Anote as credenciais geradas

### 2.3 Configurar Variáveis de Ambiente
No painel do Web Service, vá em "Environment" e adicione:

```env
# Flask
FLASK_APP=app.app:app
FLASK_ENV=production
SECRET_KEY=sua_chave_secreta_super_segura_aqui

# Database
DATABASE_URL=postgresql://username:password@hostname:port/database
# Use a URL fornecida pelo Render PostgreSQL

# Segurança
WTF_CSRF_ENABLED=true
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true

# Upload (opcional)
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# Debug (produção)
DEBUG=False
TESTING=False

# Render específico
PORT=10000
HOST=0.0.0.0
```

### 2.4 Inicializar Banco de Dados
Após o primeiro deploy bem-sucedido:

1. Acesse o Shell do Render (Web Service → Shell)
2. Execute os comandos:
```bash
python scripts/criar_tabelas.py
python scripts/criar_dados_exemplo.py
```

## 🔧 3. Configurações Finais

### 3.1 Usuário Administrador Padrão
- **Email**: `admin@jsp.com`
- **Senha**: `admin123`
- **Altere imediatamente após primeiro login!**

### 3.2 Upload da Logo
1. Faça login no sistema
2. Vá em "Configurações"
3. Faça upload da logo da empresa
4. A logo aparecerá automaticamente na tela de login

### 3.3 Configuração da Empresa
Configure os dados da empresa em:
- Configurações → Dados da Empresa
- Nome, CNPJ, endereço, etc.

## 🚨 4. Segurança Importante

### 4.1 Alterar Credenciais Padrão
- [ ] Alterar senha do admin
- [ ] Gerar nova SECRET_KEY
- [ ] Configurar dados reais da empresa

### 4.2 SSL/HTTPS
O Render fornece HTTPS automaticamente.

### 4.3 Backup do Banco
Configure backups automáticos no painel do PostgreSQL.

## 🔍 5. Troubleshooting

### Build Error
- Verifique `requirements.txt`
- Confirme Python 3.9+ no Render

### Database Error
- Verifique DATABASE_URL
- Confirme se o PostgreSQL está ativo
- Execute script de criação de tabelas

### Upload Error
- Verifique permissões da pasta uploads
- Confirme MAX_CONTENT_LENGTH

## 📞 6. Suporte

### Logs
- Render Dashboard → Logs
- Monitore erros em tempo real

### URLs Importantes
- **App**: `https://seu-app.onrender.com`
- **Login**: `https://seu-app.onrender.com/auth/login`
- **Dashboard**: `https://seu-app.onrender.com/painel`

---

## ✅ Checklist Final

- [ ] Repositório no GitHub criado
- [ ] Código enviado para GitHub
- [ ] Web Service criado no Render
- [ ] PostgreSQL configurado
- [ ] Variáveis de ambiente definidas
- [ ] Primeiro deploy realizado
- [ ] Banco de dados inicializado
- [ ] Login admin testado
- [ ] Logo da empresa configurada
- [ ] Senha admin alterada
- [ ] Backup configurado

**🎉 Sistema ERP JSP v3.0 em produção!**