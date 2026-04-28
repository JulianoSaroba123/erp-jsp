# 💰 Sistema de Adicionais de Horas Extras - Interface

## 📋 Resumo
Sistema implementado para cálculo automático e visualização de adicionais de horas extras com separação entre **custo** (pago ao colaborador) e **receita** (cobrado do cliente).

---

## 🎯 Objetivo

Permitir que você:
1. **Siga a CLT** pagando 50% ou 100% de adicional ao colaborador conforme a lei
2. **Negocie livremente** com o cliente um percentual diferente (pode ser maior, igual ou menor)
3. **Visualize em tempo real** a margem de contribuição de cada hora trabalhada

---

## 🧮 Como Funciona

### 1. **Cálculo Automático do % CLT** 

O sistema calcula automaticamente baseado em:

| Condição | % Adicional CLT |
|----------|----------------|
| **Domingo ou Feriado** | 100% |
| **Sábado** | 50% |
| **Após 17h em dia de semana** | 50% |
| **Horário normal** | 0% |

**Feriados considerados:**
- 01/01 - Ano Novo
- 21/04 - Tiradentes
- 01/05 - Dia do Trabalho
- 07/09 - Independência
- 12/10 - N. Sra. Aparecida
- 02/11 - Finados
- 15/11 - Proclamação da República
- 25/12 - Natal

### 2. **% Cliente (Editável)**

Este campo é **editável** e permite negociar com o cliente:

- **Padrão:** Sistema preenche com o mesmo % CLT
- **Você pode alterar:** Para mais (lucro maior) ou menos (margem menor/negativa)

### 3. **Cálculo dos Valores**

Para cada hora trabalhada:

```
Valor Hora Base = R$ 50,00 (cadastrado no colaborador)

CUSTO (pago ao colaborador):
- % CLT = 100% (domingo/feriado)
- Multiplicador = 1 + (100/100) = 2,0
- Valor Custo = R$ 50,00 × 2,0 = R$ 100,00/hora

RECEITA (cobrada do cliente):  
- % Cliente = 50% (negociado)
- Multiplicador = 1 + (50/100) = 1,5
- Valor Receita = R$ 50,00 × 1,5 = R$ 75,00/hora

MARGEM:
- Margem = R$ 75,00 - R$ 100,00 = -R$ 25,00/hora ⚠️ PREJUÍZO
```

---

## 🖥️ Interface do Usuário

### **Campos na Tela de OS (Colaboradores)**

Depois dos campos de horas (Normais, Extras, Total), você verá:

```
═══════════════════════════════════════════
 Adicionais: Sistema calcula automaticamente os % 
            baseado em data/horário (CLT)
───────────────────────────────────────────
| % CLT      | % Cliente  | R$ Custo/h | R$ Receita/h | Margem/h  |
|------------|------------|------------|--------------|-----------|
| 100% 🔒    | [50 ✏️]   | R$ 100,00  | R$ 75,00     | -R$ 25,00 |
|            |            |     (🔴)   |     (🟢)     |    (🔴)   |
```

**Legenda:**
- 🔒 **Bloqueado** - Calculado automaticamente
- ✏️ **Editável** - Você pode alterar   
- 🔴 **Custo** - O que você paga
- 🟢 **Receita** - O que você recebe
- 🟡/🔴 **Margem** - Verde se positiva, Vermelha se negativa

---

## 🎬 Fluxo de Uso

### **1. Ao Adicionar/Editar Colaborador na OS:**

1. **Selecione o Colaborador** → Sistema carrega o `valor_hora` base
2. **Defina a Data de Trabalho** → Sistema calcula % CLT:
   - Verifica se é domingo, feriado, sábado
3. **Preencha os Horários** → Sistema verifica se tem horas após 17h
4. **Campo % CLT atualiza automaticamente** (ex: 100%)
5. **Campo % Cliente é preenchido** (padrão = mesmo % CLT)
6. **Você pode editar o % Cliente** conforme negociação
7. **Valores calculados em tempo real:**
   - R$ Custo/h (com % CLT)
   - R$ Receita/h (com % Cliente)
   - Margem/h (diferença)

### **2. Ao Salvar a OS:**

O sistema grava no banco:
- `percentual_adicional_cobranca` → Apenas se diferente do padrão
- `valor_hora_custo` → Valor com adicional CLT
- `valor_hora_receita` → Valor com adicional Cliente

---

## 💡 Exemplos Práticos

### **Exemplo 1: Feriado com Negociação Ruim**
```
Colaborador: João
Valor/hora base: R$ 50,00
Data: 21/04/2026 (Tiradentes - Feriado)
Horário: 08:00 às 17:00 (8 horas)

% CLT: 100% (automático)
% Cliente: 50% (você negociou mal)

Custo: R$ 50 × 2,0 = R$ 100/h → 8h × R$ 100 = R$ 800
Receita: R$ 50 × 1,5 = R$ 75/h → 8h × R$ 75 = R$ 600
Margem: R$ 600 - R$ 800 = -R$ 200 ⚠️ PREJUÍZO
```

### **Exemplo 2: Feriado com Negociação Boa**
```
Mesmos dados, mas % Cliente = 120%

Custo: R$ 800 (colaborador recebe igual)
Receita: R$ 50 × 2,2 = R$ 110/h → 8h × R$ 110 = R$ 880
Margem: R$ 880 - R$ 800 = R$ 80 ✅ LUCRO
```

### **Exemplo 3: Sábado Normal**
```
Colaborador: Maria
Valor/hora base: R$ 60,00
Data: Sábado
Horário: 09:00 às 13:00 (4 horas)

% CLT: 50% (automático)
% Cliente: 50% (padrão)

Custo: R$ 60 × 1,5 = R$ 90/h → 4h × R$ 90 = R$ 360
Receita: R$ 60 × 1,5 = R$ 90/h → 4h × R$ 90 = R$ 360
Margem: R$ 0 (empate) ⚖️
```

### **Exemplo 4: Dia Normal com Hora Extra**
```
Colaborador: Pedro
Valor/hora base: R$ 40,00
Data: Segunda-feira
Horário: 08:00 às 18:00 (saída às 18h)

% CLT: 50% (tem hora após 17h)
% Cliente: 75% (você negociou melhor)

Custo: R$ 40 × 1,5 = R$ 60/h
Receita: R$ 40 × 1,75 = R$ 70/h
Margem: R$ 10/h ✅ LUCRO
```

---

## 🔍 Detalhes Técnicos

### **Frontend (JavaScript)**

```javascript
// Cache de colaboradores com valor_hora
let colaboradoresCache = {};

// Função principal de cálculo
function calcularAdicionaisColaborador(index) {
    // 1. Busca dados do colaborador
    // 2. Analisa data e horários
    // 3. Calcula % CLT (0, 50 ou 100)
    // 4. Pega % Cliente (editável)
    // 5. Calcula custos e receitas
    // 6. Atualiza interface
}
```

**Triggers de Recálculo:**
- `onChange` do select de colaborador
- `onChange` da data de trabalho
- `onChange` dos horários (entrada/saída)
- `onChange` do campo % Cliente

### **Backend (Python/Flask)**

```python
# Salvar percentual customizado
trabalho.percentual_adicional_cobranca = Decimal(valor_ou_None)

# Calcular valores com adicionais
colaborador_obj = Colaborador.query.get(colaborador_id)
if colaborador_obj and colaborador_obj.valor_hora:
    trabalho.atualizar_valores_com_adicional(colaborador_obj.valor_hora)
    
# Grava no banco:
# - valor_hora_custo
# - valor_hora_receita
```

---

## ⚠️ Avisos Importantes

### **1. Margem Negativa**
Quando a margem aparece **vermelha**, você está tendo **prejuízo**. O sistema mostra claramente quando o % Cliente negociado é menor que o % CLT obrigatório.

### **2. Sem Cadastro de Valor/Hora**
Se o colaborador não tiver `valor_hora` cadastrado, os campos de custo/receita ficarão em R$ 0,00. **Cadastre o valor no perfil do colaborador!**

### **3. Alterações Manuais**
Ao alterar manualmente o **% Cliente**, os valores de receita e margem são recalculados **instantaneamente**. Isso permite simular diferentes cenários de negociação.

### **4. Relatórios Futuros**
Em versões futuras, o sistema poderá:
- Mostrar no PDF da OS o breakdown de custos vs receitas
- Gerar relatórios de rentabilidade por OS
- Alertas automáticos quando margem fica negativa

---

## 📊 Campos no Banco de Dados

```sql
-- Tabela: ordem_servico_colaborador

-- Percentual negociado com cliente (NULL = usar padrão)
percentual_adicional_cobranca NUMERIC(5, 2) NULL

-- Valor/hora pago ao colaborador (com adicional CLT)
valor_hora_custo NUMERIC(10, 2) NULL

-- Valor/hora cobrado do cliente (com adicional negociado)
valor_hora_receita NUMERIC(10, 2) NULL
```

---

## 🚀 Status de Implementação

✅ **Concluído:**
- Campos de adicionais na interface (editar OS)
- Cálculo automático de % CLT
- Campo editável de % Cliente
- Cálculo real-time de custo, receita e margem
- Indicadores visuais (cores para margem)
- Salvamento no banco de dados
- Recálculo ao alterar colaborador/data/horários

🔜 **Próximos Passos:**
- Exibir adicionais no PDF da OS
- Relatório de rentabilidade por OS/período
- Dashboard de margens nas OS operacionais
- Alertas visuais de margem negativa no listão

---

## 📚 Arquivos Modificados

1. **app/ordem_servico/templates/os/form.html** (+150 linhas)
   - Novos campos de adicionais (edição e novo)
   - Função JavaScript `calcularAdicionaisColaborador()`
   - Modificação de `carregarColaboradoresSelect()` para cache
   - Event listeners para recálculo automático

2. **app/ordem_servico/ordem_servico_routes.py** (+12 linhas)
   - Import de `Colaborador`
   - Extração de `percentual_adicional_cobranca` do form
   - Chamada de `atualizar_valores_com_adicional()`

3. **app/colaborador/colaborador_model.py** (já existente)
   - Métodos: `calcular_percentual_adicional_padrao()`
   - Métodos: `calcular_valores_com_adicional()`
   - Métodos: `atualizar_valores_com_adicional()`
   - Properties: `margem_contribuicao`

---

## 📞 Suporte

Dúvidas sobre o sistema:
1. Veja exemplos práticos neste documento
2. Teste com dados fictícios em ambiente local
3. Verifique se o `valor_hora` está cadastrado no colaborador
4. Confira os logs do navegador (F12) para debug do JavaScript

---

**Desenvolvido por:** JSP Soluções  
**Data:** Abril/2026  
**Versão:** 1.0
