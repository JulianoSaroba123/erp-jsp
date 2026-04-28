# 💰 Sistema de Adicionais de Horas Extras - Interface

## 📋 Resumo
Sistema implementado para cálculo automático e visualização de adicionais de horas extras com separação entre **custo** (pago ao colaborador baseado no salário) e **receita** (cobrado do cliente baseado no valor/hora).

---

## 🎯 Objetivo

Permitir que você:
1. **Siga a CLT** pagando 50% ou 100% de adicional ao colaborador sobre seu custo real por hora
2. **Negocie livremente** com o cliente um percentual diferente sobre o valor/hora cobrado
3. **Visualize em tempo real** a margem de contribuição de cada hora trabalhada

---

## 🧮 Como Funciona

### **LÓGICA DE CÁLCULO:**

```
┌──────────────────────────────────────────────────────────┐
│ CADASTRO DO COLABORADOR:                                 │
│ • Salário Mensal: R$ 3.000,00 (custo da empresa)        │
│ • Valor/Hora Cliente: R$ 110,00 (preço cobrado)         │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ CUSTO (Pago ao Colaborador):                             │
│ 1. Salário Mensal ÷ 220 horas = Valor/hora base         │
│    R$ 3.000 ÷ 220h = R$ 13,64/h                         │
│                                                           │
│ 2. Aplicar % CLT (0%, 50% ou 100%)                      │
│    Feriado = 100% → R$ 13,64 × 2,0 = R$ 27,28/h        │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ RECEITA (Cobrada do Cliente):                            │
│ 1. Valor/Hora Cliente = R$ 110,00                       │
│                                                           │
│ 2. Aplicar % Negociado (padrão = % CLT)                 │
│    Feriado negociado 50% → R$ 110 × 1,5 = R$ 165,00/h  │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ MARGEM:                                                   │
│ Receita - Custo = R$ 165,00 - R$ 27,28 = R$ 137,72/h ✅ │
└──────────────────────────────────────────────────────────┘
```

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
EXEMPLO REAL: Trabalho em Feriado (21/04/2026)
═══════════════════════════════════════════════

DADOS DO COLABORADOR:
• Salário Mensal: R$ 3.000,00
• Valor/Hora Cliente: R$ 110,00

CUSTO (pago ao colaborador):
├─ Valor/hora base = R$ 3.000 ÷ 220h = R$ 13,64/h
├─ % CLT = 100% (feriado, obrigatório por lei)
├─ Multiplicador = 1 + (100/100) = 2,0
└─ Valor Custo = R$ 13,64 × 2,0 = R$ 27,28/hora

RECEITA (cobrada do cliente):  
├─ Valor/hora base = R$ 110,00 (cadastrado)
├─ % Cliente = 50% (você negociou)
├─ Multiplicador = 1 + (50/100) = 1,5
└─ Valor Receita = R$ 110,00 × 1,5 = R$ 165,00/hora

MARGEM:
└─ Margem = R$ 165,00 - R$ 27,28 = R$ 137,72/hora ✅ LUCRO

═══════════════════════════════════════════════

💰 8 HORAS TRABALHADAS:
   Custo Total: 8h × R$ 27,28 = R$ 218,24
   Receita Total: 8h × R$ 165,00 = R$ 1.320,00
   Lucro Total: R$ 1.320,00 - R$ 218,24 = R$ 1.101,76 ✅
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

### **Exemplo 1: Feriado - Seu Caso Real**
```
Colaborador: Anízio Nunes
Salário Mensal: R$ 3.000,00
Valor/Hora Cliente: R$ 110,00
Data: 21/04/2026 (Tiradentes - Feriado)
Horário: 08:00 às 17:00 (8 horas)

% CLT: 100% (automático, é feriado)
% Cliente: 50% (você negociou)

CUSTO:
├─ Base: R$ 3.000 ÷ 220 = R$ 13,64/h
├─ Com adicional: R$ 13,64 × 2,0 = R$ 27,28/h
└─ Total 8h: 8 × R$ 27,28 = R$ 218,24

RECEITA:
├─ Base: R$ 110,00/h
├─ Com adicional: R$ 110 × 1,5 = R$ 165,00/h
└─ Total 8h: 8 × R$ 165,00 = R$ 1.320,00

MARGEM: R$ 1.320,00 - R$ 218,24 = R$ 1.101,76 ✅ LUCRO EXCELENTE
```

### **Exemplo 2: Feriado com Negociação ainda Melhor**
```
Mesmos dados, mas % Cliente = 100% (igual ao CLT)

CUSTO: R$ 218,24 (mantém)

RECEITA:
├─ R$ 110 × 2,0 = R$ 220,00/h
└─ Total 8h: 8 × R$ 220,00 = R$ 1.760,00

MARGEM: R$ 1.760,00 - R$ 218,24 = R$ 1.541,76 ✅ LUCRO MAIOR AINDA
```

### **Exemplo 3: Sábado Normal**
```
Colaborador: Maria
Salário: R$ 2.640,00 (R$ 12/h base)
Valor/Hora Cliente: R$ 90,00
Data: Sábado
Horário: 09:00 às 13:00 (4 horas)

% CLT: 50% (automático, sábado)
% Cliente: 50% (padrão)

CUSTO:
├─ Base: R$ 2.640 ÷ 220 = R$ 12,00/h
├─ Com adicional: R$ 12 × 1,5 = R$ 18,00/h
└─ Total 4h: 4 × R$ 18,00 = R$ 72,00

RECEITA:
├─ Base: R$ 90,00/h
├─ Com adicional: R$ 90 × 1,5 = R$ 135,00/h
└─ Total 4h: 4 × R$ 135,00 = R$ 540,00

MARGEM: R$ 540,00 - R$ 72,00 = R$ 468,00 ✅ LUCRO
```

### **Exemplo 4: Dia Normal com Hora Extra Após 17h**
```
Colaborador: Pedro
Salário: R$ 1.760,00 (R$ 8/h base)
Valor/Hora Cliente: R$ 65,00
Data: Segunda-feira
Horário: 08:00 às 18:00 (saída às 18h = tem hora extra)

% CLT: 50% (tem hora após 17h)
% Cliente: 75% (você negociou melhor)

CUSTO:
├─ Base: R$ 1.760 ÷ 220 = R$ 8,00/h
├─ Com adicional: R$ 8 × 1,5 = R$ 12,00/h
└─ Total 10h: 10 × R$ 12,00 = R$ 120,00

RECEITA:
├─ Base: R$ 65,00/h
├─ Com adicional: R$ 65 × 1,75 = R$ 113,75/h
└─ Total 10h: 10 × R$ 113,75 = R$ 1.137,50

MARGEM: R$ 1.137,50 - R$ 120,00 = R$ 1.017,50 ✅ LUCRO EXCELENTE
```

---

## 🔍 Detalhes Técnicos

### **Frontend (JavaScript)**

```javascript
// Cache de colaboradores com salario_mensal e valor_hora
let colaboradoresCache = {};

// Função principal de cálculo
function calcularAdicionaisColaborador(index) {
    // 1. Busca dados do colaborador (salário + valor/hora)
    // 2. Analisa data e horários
    // 3. Calcula % CLT (0, 50 ou 100)
    // 4. CUSTO: salário_mensal ÷ 220h × (1 + % CLT)
    // 5. RECEITA: valor_hora × (1 + % Cliente)
    // 6. MARGEM: receita - custo
    // 7. Atualiza interface
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

# Calcular valores com adicionais (DUAS bases diferentes)
colaborador_obj = Colaborador.query.get(colaborador_id)
if colaborador_obj:
    salario = colaborador_obj.salario_mensal  # Base para CUSTO
    valor_hora = colaborador_obj.valor_hora    # Base para RECEITA
    trabalho.atualizar_valores_com_adicional(salario, valor_hora)
    
# Grava no banco:
# - valor_hora_custo (baseado em salário ÷ 220)
# - valor_hora_receita (baseado em valor/hora cliente)
```

---

## ⚠️ Avisos Importantes

### **1. Margem Negativa**
Quando a margem aparece **vermelha**, você está tendo **prejuízo**. O sistema mostra claramente quando o % Cliente negociado é menor que o % CLT obrigatório.

### **2. Sem Cadastro de Salário ou Valor/Hora**
Se o colaborador não tiver `salario_mensal` ou `valor_hora` cadastrados, os campos ficarão em R$ 0,00. **Complete o cadastro do colaborador!**

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

3. **app/colaborador/colaborador_model.py** (modificado)
   - Método `calcular_valores_com_adicional()` alterado para aceitar 2 parâmetros
   - Método `atualizar_valores_com_adicional()` alterado para aceitar 2 parâmetros
   - Lógica: CUSTO usa salário_mensal ÷ 220, RECEITA usa valor_hora

4. **app/colaborador/colaborador_routes.py** (+1 linha)
   - API `/api/buscar_ativos` agora retorna `salario_mensal` também

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
