# 🐛 PROBLEMAS COMUNS EM PROJETOS NOVOS - SOLUÇÕES

Este documento explica os 4 problemas mais comuns quando um projeto é criado sem preencher todos os dados obrigatórios e como resolver definitivamente.

---

## ❌ PROBLEMA 1: Economia Mensal = R$ 0

### Causa:
O campo `economia_mensal` não é calculado automaticamente na criação do projeto. Ele só é calculado quando você salva os "Dados Financeiros".

### Solução Manual:
1. Abrir o Dashboard do projeto
2. Clicar em **"$ Dados Financeiros"**
3. Preencher a **"Tarifa Final (R$/kWh)"**
4. Clicar em **"Salvar Dados Financeiros"**
5. O sistema calculará: `economia_mensal = consumo_kwh_mes × tarifa_kwh`

### Solução Automática (Código):
Adicionar cálculo automático ao salvar qualquer aba do projeto.

**Arquivo:** `app/energia_solar/energia_solar_routes.py`
**Rota:** `projeto_salvar_consumo` (linha ~1650)

---

## ❌ PROBLEMA 2: Nome do Cliente = "Novo Projeto"

### Causa:
O projeto é criado sem vincular um cliente. O campo `nome_cliente` fica vazio.

### Solução Manual:
1. Abrir o Dashboard do projeto
2. Clicar em **"✏️ EDITAR CLIENTE"**
3. Selecionar um cliente da lista OU digitar o nome manualmente
4. Salvar

### Solução Automática (Código):
Tornar obrigatório vincular cliente OU preencher nome ao criar projeto.

**Arquivo:** `app/energia_solar/templates/energia_solar/projeto_wizard.html`
**Campo:** Adicionar `required` no campo `nome_cliente`

---

## ❌ PROBLEMA 3: Área Necessária = 0.00 m²

### Causa:
A área não é calculada automaticamente. Depende de:
- Dimensões da placa (comprimento × largura)
- Quantidade de placas

### Solução Manual:
1. Verificar se a placa tem dimensões cadastradas
2. O cálculo é: `area = comprimento_placa × largura_placa × qtd_placas`
3. Se a placa não tem dimensões, cadastrar em **"⚙️ Equipamentos > Placas"**

### Solução Automática (Código):
Calcular área automaticamente ao selecionar placas.

**Arquivo:** `app/energia_solar/energia_solar_routes.py`
**Rota:** `projeto_salvar_equipamentos`

**Código a adicionar:**
```python
# Calcular área necessária
if projeto.qtd_placas and placa:
    comprimento = float(placa.comprimento or 0)
    largura = float(placa.largura or 0)
    if comprimento > 0 and largura > 0:
        projeto.area_necessaria = comprimento * largura * projeto.qtd_placas
```

---

## ❌ PROBLEMA 4: Valores = R$ 0.00 na Proposta

### Causa:
Os custos e valor de venda não são preenchidos automaticamente. Precisam ser inseridos manualmente.

### Solução Manual:
1. Abrir o Dashboard do projeto
2. Clicar em **"💰 Editar Orçamento"** OU **"💳 Financiamento"**
3. Preencher:
   - Custo de Equipamentos
   - Custo de Instalação
   - Custo de Projeto
   - Margem de Lucro
4. O sistema calculará automaticamente o `valor_venda`

### Solução Automática (Código):
Calcular custos baseados em:
- Preço do kit (se usar kit)
- Preço das placas + inversor (se individual)
- Custos fixos cadastrados

**Arquivo:** `app/energia_solar/energia_solar_routes.py`
**Rota:** `projeto_salvar_equipamentos`

---

## ✅ CHECKLIST PARA CRIAR PROJETO COMPLETO

### Passo 1: Cliente e Localização
- [ ] Vincular cliente OU preencher nome
- [ ] Preencher CEP
- [ ] Verificar irradiação solar

### Passo 2: Consumo
- [ ] Preencher consumo mensal (kWh)
- [ ] Preencher tarifa (R$/kWh)

### Passo 3: Equipamentos
- [ ] Selecionar placas (verificar dimensões)
- [ ] Selecionar inversor
- [ ] Definir quantidade de placas

### Passo 4: Dados Financeiros
- [ ] Salvar "Dados Financeiros" (calcula economia)
- [ ] Preencher orçamento (custos e valor venda)

---

## 🔧 IMPLEMENTAÇÃO DE CÁLCULO AUTOMÁTICO

Vou criar uma função helper que calcula todos os valores automaticamente:

```python
def recalcular_valores_projeto(projeto):
    """Recalcula todos os valores derivados do projeto"""
    
    # 1. Economia mensal
    if projeto.consumo_kwh_mes and projeto.tarifa_kwh:
        projeto.economia_mensal = float(projeto.consumo_kwh_mes) * float(projeto.tarifa_kwh)
        projeto.economia_anual = projeto.economia_mensal * 12
    
    # 2. Área necessária
    if projeto.qtd_placas and projeto.placa:
        comprimento = float(projeto.placa.comprimento or 0)
        largura = float(projeto.placa.largura or 0)
        if comprimento > 0 and largura > 0:
            projeto.area_necessaria = comprimento * largura * projeto.qtd_placas
    
    # 3. Nome do cliente
    if not projeto.nome_cliente and projeto.cliente_id:
        from app.cliente.cliente_model import Cliente
        cliente = Cliente.query.get(projeto.cliente_id)
        if cliente:
            projeto.nome_cliente = cliente.nome
    
    # 4. Custo total
    if projeto.custo_equipamentos or projeto.custo_instalacao or projeto.custo_projeto:
        projeto.custo_total = (
            float(projeto.custo_equipamentos or 0) +
            float(projeto.custo_instalacao or 0) +
            float(projeto.custo_projeto or 0)
        )
    
    # 5. Valor de venda
    if projeto.custo_total and projeto.margem_lucro:
        margem = 1 + (float(projeto.margem_lucro) / 100)
        projeto.valor_venda = float(projeto.custo_total) * margem
    
    return projeto
```

**Chamar essa função em todas as rotas de salvamento:**
- `projeto_salvar_cliente`
- `projeto_salvar_consumo`
- `projeto_salvar_equipamentos`
- `projeto_salvar_dados_financeiros`

---

## 📝 RESUMO

| Problema | Causa | Solução Imediata |
|----------|-------|------------------|
| Economia R$ 0 | Dados financeiros não salvos | Clicar em "$ Dados Financeiros" e salvar |
| Nome "Novo Projeto" | Cliente não vinculado | Clicar em "Editar Cliente" e vincular |
| Área 0.00 m² | Placa sem dimensões | Cadastrar dimensões da placa |
| Valores R$ 0 | Orçamento não preenchido | Clicar em "Editar Orçamento" e preencher |

**Solução Definitiva:** Implementar cálculos automáticos em todas as rotas de salvamento.
