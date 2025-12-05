# 🔧 Guia: Resolver Problemas Render + DBeaver

## 📋 Problema
- Render não está salvando clientes
- Importações não funcionam
- Banco de dados PostgreSQL não está configurado corretamente

## 🛠️ Solução com DBeaver

### PASSO 1: Conectar DBeaver ao PostgreSQL do Render

1. **Pegar credenciais no Render Dashboard:**
   - Acesse: https://dashboard.render.com
   - Vá em seu banco PostgreSQL
   - Clique em **"Info"**
   - Copie as informações:
     - **Hostname** (Internal Database URL)
     - **Database**
     - **Username**
     - **Password**
     - **Port** (geralmente 5432)

2. **Conectar no DBeaver:**
   - Abra DBeaver
   - Clique em **"Nova Conexão"** (ícone de tomada com +)
   - Selecione **PostgreSQL**
   - Preencha:
     - **Host:** [hostname do Render]
     - **Port:** 5432
     - **Database:** [nome do banco]
     - **Username:** [usuário do Render]
     - **Password:** [senha do Render]
   - Em **"SSL"** → Ative **"Use SSL"**
   - Teste conexão e Salve

### PASSO 2: Verificar se as tabelas existem

```sql
-- Execute no DBeaver para ver todas as tabelas
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

**Se NÃO houver tabelas:**
- As tabelas não foram criadas no Render
- Precisamos criar via Shell do Render

### PASSO 3: Criar tabelas via Render Shell

1. No dashboard do Render, acesse seu **Web Service**
2. Vá em **"Shell"** no menu lateral
3. Execute:

```bash
python -c "from app.app import create_app; from app.extensoes import db; app = create_app(); app.app_context().push(); db.create_all(); print('Tabelas criadas!')"
```

4. Verifique no DBeaver se as tabelas apareceram (F5 para refresh)

### PASSO 4: Criar usuário admin

No Shell do Render:

```bash
python -c "
from app.app import create_app
from app.extensoes import db
from app.auth.models import Usuario
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    admin = Usuario(
        usuario='admin',
        senha=generate_password_hash('admin123'),
        nome_completo='Administrador',
        email='admin@jspsolar.com.br',
        tipo_usuario='admin',
        ativo=True
    )
    db.session.add(admin)
    db.session.commit()
    print('Admin criado!')
"
```

### PASSO 5: Verificar se está salvando

No DBeaver, execute:

```sql
-- Ver usuários
SELECT * FROM usuario;

-- Ver clientes (se existir)
SELECT * FROM clientes;

-- Ver configuração
SELECT * FROM configuracao;
```

### PASSO 6: Testar salvamento de cliente

1. Acesse seu app no Render
2. Faça login com: **admin / admin123**
3. Tente cadastrar um cliente
4. No DBeaver, execute:

```sql
SELECT * FROM clientes ORDER BY id DESC LIMIT 5;
```

Se o cliente aparecer → ✅ Resolvido!
Se NÃO aparecer → Problema está no código ou commit do banco

### PASSO 7: Diagnóstico avançado com DBeaver

Execute no DBeaver:

```sql
-- 1. Verificar conexões ativas
SELECT * FROM pg_stat_activity WHERE datname = current_database();

-- 2. Verificar transações pendentes
SELECT * FROM pg_stat_activity WHERE state = 'idle in transaction';

-- 3. Ver logs de erros
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;

-- 4. Verificar constraints (podem estar bloqueando inserções)
SELECT conname, contype, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'clientes'::regclass;
```

### PASSO 8: Importação de dados

**Opção A: Via interface do app**
1. Acesse `/painel/importar-auto` no Render
2. Clique para importar dados

**Opção B: Via Shell do Render**
```bash
python -c "
from app.app import create_app
from app.painel.importar_dados import importar_dados_automatico

app = create_app()
with app.app_context():
    resultado = importar_dados_automatico()
    print(resultado)
"
```

**Opção C: Via DBeaver (copiar dados do SQLite local)**
1. Conecte o DBeaver ao seu SQLite local (`c:/ERP_JSP/erp.db`)
2. Selecione dados da tabela `clientes`
3. Copie (Ctrl+C)
4. Cole na tabela `clientes` do PostgreSQL (Ctrl+V)

### PASSO 9: Verificar variáveis de ambiente no Render

No Render Dashboard → Web Service → Environment:

```env
DATABASE_URL=postgresql://...  ✓ (deve estar preenchida automaticamente)
FLASK_ENV=production
SECRET_KEY=[uma chave secreta forte]
```

### PASSO 10: Logs do Render

No Render Dashboard → Logs, procure por:
- `OperationalError` → Problema de conexão/banco
- `IntegrityError` → Problema de constraints/duplicação
- `ProgrammingError` → Tabela não existe
- `CommitError` → Problema no commit

## 🔍 Comandos úteis DBeaver

```sql
-- Resetar sequence de ID (se estiver dando erro de duplicação)
SELECT setval('clientes_id_seq', (SELECT MAX(id) FROM clientes));

-- Ver estrutura da tabela
\d clientes

-- Ver índices
SELECT * FROM pg_indexes WHERE tablename = 'clientes';

-- Forçar commit de transações pendentes (cuidado!)
COMMIT;
```

## ⚠️ Problemas comuns

### 1. "relation does not exist"
→ Tabelas não foram criadas (volte ao PASSO 3)

### 2. "IntegrityError: duplicate key"
→ ID duplicado, resetar sequence (comando acima)

### 3. "Connection refused"
→ SSL não configurado no DBeaver ou credenciais erradas

### 4. "Data não está salvando mas não dá erro"
→ Falta `db.session.commit()` no código ou transação não foi concluída

### 5. "ImportError no Shell"
→ Render não instalou dependências, force rebuild

## 📞 Checklist final

- [ ] DBeaver conectado ao PostgreSQL Render
- [ ] Tabelas criadas e visíveis no DBeaver
- [ ] Usuário admin criado
- [ ] Teste de inserção manual no DBeaver funciona
- [ ] Teste de cadastro via interface funciona
- [ ] Dados importados (se necessário)
- [ ] Logs do Render sem erros

---

**Próximos passos:** Se mesmo após seguir todos os passos o problema persistir, execute o script de diagnóstico no Shell do Render e envie a saída completa.
