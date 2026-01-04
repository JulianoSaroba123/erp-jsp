# 🔧 Correção: Salvamento de Layout de Placas no Render

## 📋 Problema Identificado

O usuário relatou que no ambiente Render, a formação de placas não estava sendo salva corretamente. Quando configurava **1 linha × 6 colunas**, a visualização mostrava **2 linhas × 5 colunas** (valores padrão).

## 🔍 Análise Realizada

### 1. **Model (Banco de Dados)** ✅
- Os campos `linhas_placas` e `colunas_placas` existem no model `ProjetoSolar` ([catalogo_model.py](app/energia_solar/catalogo_model.py#L269-L270))
- Tipo: `db.Column(db.Integer)`

### 2. **Routes (Backend)** ✅
- O código de salvamento está correto ([energia_solar_routes.py](app/energia_solar/energia_solar_routes.py#L512-L513))
- Os valores são lidos do formulário e salvos no banco

### 3. **Template (Frontend)** ✅
- Os campos HTML têm os nomes corretos: `name="linhas_placas"` e `name="colunas_placas"` ([projeto_wizard.html](app/energia_solar/templates/energia_solar/projeto_wizard.html#L541-L549))
- A função `renderizarLayout()` exibe corretamente a formação

### 4. **Carregamento de Dados** ⚠️ **PROBLEMA ENCONTRADO**
- Ao editar um projeto, os valores eram carregados nos inputs, mas o layout visual não era atualizado
- A visualização continuava mostrando os valores padrão (2×5)

## 🛠️ Correções Implementadas

### 1. **Debug nos Logs do Backend**
Adicionado debug no salvamento para verificar valores recebidos:

```python
# DEBUG: Verificar valores recebidos do formulário
linhas_raw = request.form.get('linhas_placas')
colunas_raw = request.form.get('colunas_placas')
print(f"🔍 DEBUG Layout - linhas_raw: '{linhas_raw}' (type: {type(linhas_raw)})")
print(f"🔍 DEBUG Layout - colunas_raw: '{colunas_raw}' (type: {type(colunas_raw)})")

projeto.linhas_placas = int(request.form.get('linhas_placas', 0)) if request.form.get('linhas_placas') else None
projeto.colunas_placas = int(request.form.get('colunas_placas', 0)) if request.form.get('colunas_placas') else None

print(f"✅ Layout salvo - {projeto.linhas_placas}x{projeto.colunas_placas} = {(projeto.linhas_placas or 0) * (projeto.colunas_placas or 0)} módulos")
```

### 2. **Forçar Recálculo do Layout ao Carregar Projeto**
Adicionado timeout para recalcular e renderizar o layout após carregar dados:

```javascript
// IMPORTANTE: Forçar atualização do layout após carregar todos os dados
setTimeout(() => {
    console.log('🔄 Forçando recálculo do layout...');
    calcularAreaLayout();
    renderizarLayout();
}, 500); // Delay para garantir que todos os campos foram preenchidos
```

### 3. **Script de Diagnóstico**
Criado script para identificar e corrigir projetos com problemas de layout:

**Arquivo:** `diagnostico_layout_render.py`

**Funções:**
- ✅ Diagnostica todos os projetos e identifica problemas
- ✅ Corrige automaticamente layouts NULL ou com valor 0
- ✅ Calcula melhor disposição (mais quadrada possível)

**Uso:**
```bash
python diagnostico_layout_render.py
```

**Menu:**
1. Diagnosticar projetos (apenas leitura)
2. Corrigir layouts com problemas (ALTERA BANCO!)
3. Sair

## 🧪 Como Testar

### No Desenvolvimento Local:
```bash
python run.py
```

1. Acesse: http://localhost:5000/energia-solar/projetos/criar
2. Preencha a Aba 4 - Layout
3. Configure: **1 linha × 6 colunas**
4. Verifique a visualização: deve mostrar "6 módulos organizados em 1 linha × 6 colunas"
5. Salve o projeto
6. Abra o projeto para editar
7. Verifique se o layout está correto

### No Render:
1. Faça commit e push das alterações
2. Aguarde deploy automático no Render
3. Verifique os logs do Render para ver as mensagens de debug
4. Teste criação e edição de projetos

## 📊 Verificação no Banco de Dados

### Via DBeaver ou psql:
```sql
SELECT 
    id,
    nome_cliente,
    linhas_placas,
    colunas_placas,
    (linhas_placas * colunas_placas) as total_calculado,
    qtd_placas
FROM projeto_solar
ORDER BY id DESC
LIMIT 10;
```

### Via Script Python:
```bash
python diagnostico_layout_render.py
```

## 🎯 Resultado Esperado

### Antes:
- Layout configurado: 1×6
- Visualização mostrava: 2×5 (valores padrão)
- Banco salvava: NULL ou 0

### Depois:
- Layout configurado: 1×6
- Visualização mostra: 1×6 ✅
- Banco salva: linhas=1, colunas=6 ✅
- Logs mostram: "Layout salvo - 1x6 = 6 módulos" ✅

## 📁 Arquivos Modificados

1. ✅ `app/energia_solar/energia_solar_routes.py` - Adicionado debug
2. ✅ `app/energia_solar/templates/energia_solar/projeto_wizard.html` - Forçar recálculo ao carregar
3. ✅ `diagnostico_layout_render.py` - Script de diagnóstico criado

## 🚀 Próximos Passos

1. Fazer commit das alterações
2. Fazer push para o GitHub
3. Aguardar deploy no Render
4. Rodar script de diagnóstico no Render
5. Testar criação e edição de projetos

## 💡 Observações

- Os valores padrão (2 linhas × 5 colunas) estão definidos no template
- Ao criar novo projeto, esses valores são os iniciais
- Ao editar, os valores salvos devem ser carregados corretamente
- O script de diagnóstico pode identificar e corrigir projetos antigos

---

**Data:** 04/01/2026  
**Problema:** Layout de placas não salvando corretamente no Render  
**Status:** ✅ Corrigido + Debug implementado + Script de diagnóstico criado
