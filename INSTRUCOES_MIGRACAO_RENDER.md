# 🚨 INSTRUÇÕES URGENTES - RODAR MIGRAÇÃO NO RENDER

## 🎯 PROBLEMA
O campo `kit_id` foi adicionado no código, mas **não existe no banco de dados do Render**.

Por isso o kit não aparece no modal de orçamento.

## ✅ CORREÇÃO APLICADA
O script foi **corrigido** para usar SQL direto em vez do ORM do SQLAlchemy, evitando conflitos com campos que não existem no banco do Render.

---

## ✅ SOLUÇÃO: RODAR MIGRAÇÃO NO RENDER

### **PASSO 1: Acessar o Shell do Render**

1. Acesse: https://dashboard.render.com
2. Entre no serviço: **erp-jsp-th5o**
3. No menu lateral, clique em **Shell**
4. Aguarde o terminal carregar

---

### **PASSO 2: Rodar o Script de Migração**

No terminal do Render, digite:

```bash
python adicionar_kit_id_coluna.py
```

**OU** (se preferir usar o shell script):

```bash
bash run_migration_render.sh
```

---

### **PASSO 3: Verificar Output**

Você deve ver:

```
🚀 MIGRAÇÃO: Adicionar coluna kit_id e inferir kits

🔧 Adicionando coluna kit_id...
✅ Coluna kit_id adicionada com sucesso!
✅ Foreign Key adicionada com sucesso!

🔍 Tentando inferir kit_id dos projetos...
📊 Total de projetos: X
  ✅ Projeto 6: kit_id definido como Y (...)

🔍 Verificando Projeto #6...
📊 Dados do Projeto 6:
  ID: 6
  Nome Cliente: ...
  kit_id: Y
  placa_id: ...
  inversor_id: ...

✅ KIT ENCONTRADO:
  ID: Y
  Fabricante: ...
  Descrição: ...
  Preço: R$ ...
```

Se aparecer:
- ✅ `kit_id adicionada com sucesso!` → Perfeito!
- ✅ `Projeto 6: kit_id definido` → Excelente!
- ✅ `KIT ENCONTRADO` → Tudo certo!

---

### **PASSO 4: Testar no Browser**

1. Acesse: https://erp-jsp-th5o.onrender.com/energia-solar/projetos/6/dashboard
2. **Pressione Ctrl+F5** (limpar cache)
3. Abra o **Console do navegador** (F12)
4. Clique no botão **"💰 Editar Orçamento"**

**Logs esperados no console:**

```javascript
📊 dadosProjeto carregado: {kit: {id: X, nome: "...", valor: 600}, ...}
🚀 Modal de orçamento aberto
🧹 Limpando equipamentos automáticos antigos...
📡 Carregando itens do servidor...
➕ Adicionando equipamentos do projeto...
✅ Adicionando KIT: [nome do kit]
```

**No modal, você deve ver:**

```
DESCRIÇÃO                              VALOR        AÇÕES
------------------------------------------------------
KIT FOTOVOLTAICO - [nome]             R$ 600,00    [✏️] [🗑️]
Instalação os Módulos                  R$ 100,00    [✏️] [🗑️]
TRT                                    R$ 100,00    [✏️] [🗑️]
Projeto                                R$ 200,00    [✏️] [🗑️]
...
```

---

## ⚠️ SE ALGO DER ERRADO

### **Erro: "column kit_id already exists"**
✅ **Significa que a coluna já foi adicionada!** Pule para o PASSO 4 e teste.

### **Erro: "column calculo_energia_solar.local_instalacao does not exist"**
✅ **JÁ CORRIGIDO!** Esse erro ocorria porque o script usava ORM. Agora usa SQL direto. Faça `git pull` no Render e tente novamente.

### **Erro: "Projeto 6 não encontrado"**
❌ O projeto realmente não existe no banco. Crie um novo projeto para testar.

### **Erro: "No module named 'app'"**
❌ Execute o comando no diretório raiz do projeto. Use `cd /opt/render/project/src` primeiro.

### **Erro: "Nenhum kit compatível encontrado"**
⚠️ O projeto 6 tem `placa_id` e `inversor_id`, mas não existe um `kit_solar` com essa combinação.
**Solução manual:** Acesse o dashboard do projeto e selecione um kit manualmente.

---

## 📋 COMANDOS ÚTEIS NO RENDER SHELL

```bash
# Ver se a coluna foi adicionada
python -c "from app import create_app; from app.extensoes import db; from sqlalchemy import inspect; app = create_app(); app.app_context().push(); inspector = inspect(db.engine); print([col['name'] for col in inspector.get_columns('calculo_energia_solar')])"

# Ver dados do Projeto 6
python -c "from app import create_app; from app.energia_solar.energia_solar_model import CalculoEnergiaSolar; app = create_app(); app.app_context().push(); p = CalculoEnergiaSolar.query.filter_by(id=6).first(); print(f'kit_id: {p.kit_id}, placa_id: {p.placa_id}, inversor_id: {p.inversor_id}') if p else print('Projeto 6 não encontrado')"

# Ver todos os kits disponíveis
python -c "from app import create_app; from app.energia_solar.catalogo_model import KitSolar; app = create_app(); app.app_context().push(); kits = KitSolar.query.all(); [print(f'Kit {k.id}: {k.fabricante} - {k.descricao} (placa_id={k.placa_id}, inversor_id={k.inversor_id})') for k in kits]"
```

---

## 🎯 RESULTADO FINAL ESPERADO

✅ Coluna `kit_id` criada no PostgreSQL  
✅ Foreign Key constraint adicionada  
✅ Projeto #6 com `kit_id` definido automaticamente  
✅ Modal "Editar Orçamento" mostra o KIT na primeira linha  
✅ Não duplica ao abrir/fechar modal  
✅ Valor correto do kit aparece  

---

**⏱️ TEMPO ESTIMADO:** 5 minutos  
**🔧 DIFICULDADE:** Baixa (apenas copiar e colar comandos)

**ME ENVIE SCREENSHOT DO OUTPUT quando rodar a migração!** 📸
