# 🚨 AÇÃO URGENTE - RENDER COM APENAS 32 COLUNAS

## 🎯 DIAGNÓSTICO REAL

**Banco local:** 94 colunas na tabela `calculo_energia_solar`  
**Banco Render:** **32 colunas** na tabela `calculo_energia_solar`

**Erro atual:**
```
column calculo_energia_solar.placa_id does not exist
column calculo_energia_solar.local_instalacao does not exist
```

O model Python está tentando acessar 94 colunas, mas o PostgreSQL no Render tem apenas 32.

---

## ✅ SOLUÇÃO DEFINITIVA - SCRIPT COMPLETO

Rodar script que **adiciona TODAS as 62 colunas faltantes** no PostgreSQL do Render.

### **COMANDO NO RENDER SHELL:**

```bash
python migrar_schema_completo_render.py
```

**⏱️ TEMPO:** 2-5 minutos  
**🔒 SEGURANÇA:** Preserva dados, não faz DROP/RECREATE  
**♻️ IDEMPOTENTE:** Pode rodar múltiplas vezes sem quebrar

---

## 📊 O QUE O SCRIPT FAZ

1. **Audita schema atual:**
   - Lista todas as colunas existentes no PostgreSQL
   - Identifica exatamente quais estão faltando
   - Exemplo: "📋 32 colunas existentes | ❌ 62 colunas faltantes"

2. **Adiciona colunas faltantes:**
   - Usa `ALTER TABLE ADD COLUMN IF NOT EXISTS`
   - Preserva dados existentes (não faz DROP)
   - Tipos SQL corretos para PostgreSQL:
     * TEXT para strings
     * NUMERIC(12,2) para valores monetários
     * INTEGER para IDs e contadores
     * TIMESTAMP para datas

3. **Adiciona Foreign Keys:**
   - `kit_id` → `kit_solar(id)`
   - `placa_id` → `placa_solar(id)`
   - `inversor_id` → `inversor_solar(id)`

4. **Relatório final:**
   - ✅ X colunas adicionadas
   - ❌ Y erros (se houver)
   - 📋 Total após migração: 94 colunas

---

## 📋 OUTPUT ESPERADO

### **✅ SUCESSO COMPLETO:**
```
🔍 AUDITORIA DO SCHEMA
============================================================
📋 Colunas existentes no banco: 32
❌ Colunas faltantes: 62

🔧 INICIANDO MIGRAÇÃO
============================================================
  ✅ local_instalacao              (TEXT)
  ✅ consumo_mensal                (NUMERIC(12,2))
  ✅ tarifa_energia                (NUMERIC(12,4))
  ✅ kit_id                        (INTEGER)
  ✅ placa_id                      (INTEGER)
  ✅ inversor_id                   (INTEGER)
  ... (57 linhas omitidas)

📊 RESULTADO DA MIGRAÇÃO
============================================================
✅ Colunas adicionadas: 62
❌ Erros: 0
📋 Total de colunas após migração: 94

🎉 MIGRAÇÃO COMPLETA!
   Banco agora possui todas as 94 colunas.

🔗 ADICIONANDO FOREIGN KEYS
============================================================
  ✅ FK fk_calculo_energia_kit adicionada
  ✅ FK fk_calculo_energia_placa adicionada
  ✅ FK fk_calculo_energia_inversor adicionada

✅ MIGRAÇÃO FINALIZADA COM SUCESSO!
```

### **⚠️ MIGRAÇÃO PARCIAL (raro):**
```
📊 RESULTADO DA MIGRAÇÃO
============================================================
✅ Colunas adicionadas: 60
❌ Erros: 2
📋 Total de colunas após migração: 92

⚠️ MIGRAÇÃO PARCIAL
   Esperado: 94 colunas
   Atual: 92 colunas
   Faltam: 2 colunas
```
→ Se isso acontecer, **me envie o log completo**

---

## 🚀 PLANO DE AÇÃO COMPLETO

### **PASSO 1: Rodar migração no Render (5 min)**

```bash
python migrar_schema_completo_render.py
```

📸 **Aguarde até ver:** `✅ MIGRAÇÃO FINALIZADA COM SUCESSO!`

### **PASSO 2: Testar no navegador (2 min)**

1. Abrir: https://erp-jsp-th5o.onrender.com/energia-solar/projetos/6/dashboard
2. Pressionar **Ctrl+F5** (limpar cache)
3. Abrir Console (F12)
4. Clicar "💰 Editar Orçamento"
5. Verificar Console:
   ```javascript
   dadosProjeto.kit: {id: 5, nome: "Kit 5.6kWp", valor: 2800}
   ```
6. Verificar tabela do modal:
   - ✅ "KIT FOTOVOLTAICO - Kit 5.6kWp" deve aparecer
   - ✅ Valor: R$ 2.800,00

### **PASSO 3: Verificar orçamento completo (1 min)**

- Kit aparece? ✅
- Placas aparecem? ✅
- Inversores aparecem? ✅
- Custos fixos aparecem? ✅
- Usuário pode editar valores? ✅

---

## 🔧 SE ALGO DER ERRADO

### **Erro: "table calculo_energia_solar does not exist"**
```bash
# Criar tabela primeiro
python scripts/criar_tabelas.py
# Depois rodar migração
python migrar_schema_completo_render.py
```

### **Erro: "permission denied"**
→ Usuário do Render não tem permissão para ALTER TABLE  
→ **Contate suporte do Render** ou verifique usuário do banco

### **Erro: "syntax error near..."**
→ PostgreSQL pode ter versão diferente  
→ **Me envie o erro completo** para adaptar SQL

---

## 📝 VALIDAÇÃO FINAL

Após rodar o script, execute este comando para **confirmar 94 colunas:**

```bash
python -c "
from app import create_app
from app.extensoes import db
from sqlalchemy import inspect

app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    cols = [col['name'] for col in inspector.get_columns('calculo_energia_solar')]
    print(f'✅ Total de colunas: {len(cols)}')
    
    essenciais = ['kit_id', 'placa_id', 'inversor_id', 'local_instalacao', 'consumo_mensal']
    for col in essenciais:
        existe = '✅' if col in cols else '❌'
        print(f'{existe} {col}')
"
```

**OUTPUT ESPERADO:**
```
✅ Total de colunas: 94
✅ kit_id
✅ placa_id
✅ inversor_id
✅ local_instalacao
✅ consumo_mensal
```

---

## ⏱️ CRONOGRAMA

| Etapa | Tempo | Ação |
|-------|-------|------|
| 1️⃣ Migração | 5 min | `python migrar_schema_completo_render.py` |
| 2️⃣ Validação | 1 min | Verificar output "94 colunas" |
| 3️⃣ Teste dashboard | 2 min | Abrir projeto #6, testar modal |
| 4️⃣ Verificação final | 1 min | Kit aparece no orçamento? |
| **TOTAL** | **9 min** | ✅ Problema resolvido |

---

## 🎯 RESULTADO FINAL

Após rodar a migração com sucesso:

✅ **Banco do Render:** 94 colunas (igual ao local)  
✅ **Model Python:** Funciona sem UndefinedColumn errors  
✅ **Projeto #6:** Dashboard carrega sem erros  
✅ **Modal orçamento:** Kit aparece automaticamente  
✅ **JavaScript:** Usa campos reais (descricao, preco)  
✅ **SISTEMA FUNCIONANDO:** 100%

---

## 📞 PRÓXIMO PASSO

**RODE AGORA NO RENDER:**

```bash
python migrar_schema_completo_render.py
```

E me envie **screenshot ou copiar/colar** do output completo!
