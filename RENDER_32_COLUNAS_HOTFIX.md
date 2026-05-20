# 🚨 AÇÃO URGENTE - RENDER COM APENAS 32 COLUNAS

## 🎯 DIAGNÓSTICO REAL

**Banco local:** 94 colunas na tabela `calculo_energia_solar`  
**Banco Render:** **32 colunas** na tabela `calculo_energia_solar`

**Erro atual:**
```
column calculo_energia_solar.placa_id does not exist
```

O model Python está tentando acessar 94 colunas, mas o PostgreSQL no Render tem apenas 32.

---

## ✅ SOLUÇÃO IMEDIATA

Rodar script atualizado que **detecta quais colunas existem** antes de tentar adicionar.

### **COMANDO NO RENDER SHELL:**

```bash
python adicionar_kit_id_coluna.py
```

---

## 📊 O QUE O SCRIPT FAZ AGORA

1. **Lista colunas existentes** no banco do Render (32 colunas)
2. **Verifica colunas essenciais:**
   - `kit_id` ✅/❌
   - `placa_id` ✅/❌
   - `inversor_id` ✅/❌
3. **Adiciona APENAS as que faltam:**
   - `kit_id INTEGER` (se não existir)
   - Se `placa_id` e `inversor_id` não existirem, **AVISA** mas não quebra
4. **Tenta inferir kit_id** (só se `placa_id` e `inversor_id` existirem)
5. **Mostra dados do Projeto #6** (usando apenas colunas disponíveis)

---

## 📋 OUTPUT ESPERADO

### **Caso 1: kit_id não existe**
```
✅ Coluna kit_id adicionada com sucesso!
✅ Foreign Key adicionada com sucesso!
```

### **Caso 2: placa_id não existe**
```
⚠️ Coluna placa_id não existe! Execute adicionar_coluna_kit_id() primeiro.
⚠️ Colunas necessárias não existem no banco:
  placa_id: ❌
  inversor_id: ❌
⚠️ Não é possível inferir kit automaticamente.
```

### **Caso 3: Projeto #6 sem erro**
```
🔍 Verificando Projeto #6...

📊 Dados do Projeto 6:
  id: 6
  nome_cliente: Cliente Exemplo
  kit_id: 5
  
✅ KIT ENCONTRADO:
  ID: 5
  Fabricante: DEYE
  Descrição: Kit 5.6kWp
  Preço: R$ 2.800,00
```

---

## 🛠️ SE PLACA_ID NÃO EXISTIR

O Render pode ter uma estrutura diferente. Precisaremos:

1. **Identificar quais são as 32 colunas reais** do banco
2. **Ver se há campos alternativos** para placa/inversor
3. **Adaptar a estratégia** de acordo

### **Comando para listar as 32 colunas:**

```bash
python -c "
from app import create_app
from app.extensoes import db
from sqlalchemy import inspect

app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    cols = [col['name'] for col in inspector.get_columns('calculo_energia_solar')]
    print(f'Total: {len(cols)} colunas')
    for i, col in enumerate(cols, 1):
        print(f'{i:2}. {col}')
"
```

---

## 🎯 JAVASCRIPT CORRIGIDO

O JavaScript agora usa **campos que existem COM CERTEZA** no `kit_solar`:

```javascript
kit: {
    id: {{ projeto.kit.id }},
    nome: "{{ projeto.kit.descricao|e }}",  // ✅ campo real
    valor: {{ projeto.kit.preco or 0 }}      // ✅ campo real
}
```

**Antes (ERRADO):**
- `projeto.kit.nome_exibicao` ❌ (property, pode não funcionar)
- `projeto.kit.valor_orcamento` ❌ (property, pode não funcionar)

**Agora (CORRETO):**
- `projeto.kit.descricao` ✅ (coluna real da tabela)
- `projeto.kit.preco` ✅ (coluna real da tabela)

---

## 🚀 PLANO DE AÇÃO

### **AGORA (Render Shell):**

```bash
python adicionar_kit_id_coluna.py
```

📸 **Me envie o output completo!**

### **Se kit_id for adicionado:**
✅ Testar no navegador:
1. https://erp-jsp-th5o.onrender.com/energia-solar/projetos/6/dashboard
2. Ctrl+F5
3. Abrir Console (F12)
4. Clicar "Editar Orçamento"
5. Verificar se kit aparece

### **Se placa_id não existir:**
⚠️ Rodar comando para listar as 32 colunas  
⚠️ Me enviar output para adaptar estratégia

---

## ⏱️ TEMPO

- **5 minutos** se `kit_id` for adicionado com sucesso
- **10-15 minutos** se precisar diagnosticar as 32 colunas reais
- **20-30 minutos** se precisar criar migration completa

---

## 📞 PRÓXIMO PASSO

**RODE AGORA NO RENDER:**

```bash
python adicionar_kit_id_coluna.py
```

E me envie **screenshot ou copiar/colar** do output!
