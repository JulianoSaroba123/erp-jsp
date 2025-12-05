# 🔍 Diagnóstico e Correção - Render

## Problemas Relatados
- Não está salvando dados
- Não está importando dados

## Possíveis Causas

### 1. Banco de Dados Não Inicializado
O PostgreSQL no Render pode estar vazio (sem tabelas).

**Solução:**
```bash
# No Render Shell, execute:
python -c "from app.app import create_app; from app.extensoes import db; app=create_app(); ctx=app.app_context(); ctx.push(); db.create_all(); print('Tabelas criadas!')"
```

### 2. Dados Não Importados
As tabelas existem mas estão vazias.

**Solução:**
- Acesse a rota de importação: `https://erp-jsp-th5o.onrender.com/painel/importar-auto`
- Isso importará todos os dados embutidos no código

### 3. Erro de Migração de Scripts
Os scripts de correção (`corrigir_valores_os.py`, `recalcular_itens_os.py`) foram commitados mas **não devem rodar automaticamente** no Render.

**Problema:** Esses scripts podem estar causando erro no build.

**Solução:** Remover do repositório ou adicionar ao `.gitignore`

### 4. Verificar Variáveis de Ambiente no Render

No Dashboard do Render > Settings > Environment:
- `DATABASE_URL`: Deve estar preenchida automaticamente
- `SECRET_KEY`: Deve existir (ex: `sua-chave-secreta-aqui`)
- `FLASK_ENV`: Deve ser `production`

### 5. Verificar Logs do Render

No Dashboard do Render > Logs:
- Procure por erros como:
  - `ModuleNotFoundError`
  - `sqlalchemy.exc.OperationalError`
  - `500 Internal Server Error`

## Ações Imediatas

### Passo 1: Verificar Build
Acesse: https://dashboard.render.com/web/srv-xxx/deploys
- Veja se o último deploy foi bem-sucedido
- Se falhou, leia a mensagem de erro

### Passo 2: Testar Importação
```bash
curl https://erp-jsp-th5o.onrender.com/painel/importar-auto
```

### Passo 3: Verificar Tabelas
No Render Shell:
```python
from app.app import create_app
from app.extensoes import db
app = create_app()
with app.app_context():
    print(db.engine.table_names())
```

### Passo 4: Forçar Recriação das Tabelas
No Render Shell:
```python
from app.app import create_app
from app.extensoes import db
app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()
    print("Banco recriado!")
```

Depois acesse a rota de importação.

## Checklist de Verificação

- [ ] Deploy bem-sucedido no Render?
- [ ] Variável `DATABASE_URL` configurada?
- [ ] Variável `SECRET_KEY` configurada?
- [ ] Tabelas criadas no PostgreSQL?
- [ ] Dados importados via `/painel/importar-auto`?
- [ ] Logo configurada (campo `logo_base64`)?
- [ ] WeasyPrint instalado (para PDF)?

## Contato de Suporte

Se o problema persistir, me informe:
1. Mensagem de erro nos logs do Render
2. URL que está tentando acessar
3. O que acontece ao tentar salvar/importar dados
