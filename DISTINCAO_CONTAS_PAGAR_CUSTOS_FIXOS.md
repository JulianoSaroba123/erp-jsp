# 📊 Distinção entre Contas a Pagar e Custos Fixos

## 🎯 Conceitos Fundamentais

### 1️⃣ **CONTAS A PAGAR** (Lançamentos Manuais)
Sãodespesas **pontuais ou eventuais** que você lança manualmente no sistema.

#### Características:
- ✅ Lançamento **manual** pelo usuário
- ✅ Podem ser **únicas** ou **recorrentes manuais**
- ✅ Flexíveis - valores e datas podem variar
- ✅ Origem: `MANUAL`
- ✅ Tipo: `conta_pagar`

#### Exemplos:
- Compra de materiais
- Pagamento de fornecedores eventuais
- Despesas variáveis
- Impostos específicos
- Manutenções não programadas

---

### 2️⃣ **CUSTOS FIXOS** (Lançamentos Automáticos)
São despesas **recorrentes e previsíveis** cadastradas uma vez e que geram lançamentos **automaticamente** todos os meses.

#### Características:
- ✅ Cadastro **único** do custo fixo
- ✅ Geração **automática** de lançamentos mensais
- ✅ Valor fixo ou previsível
- ✅ Origem: `CUSTO_FIXO`
- ✅ Tipo: Pode ser `DESPESA` ou `conta_pagar`
- ✅ Vinculado ao custo fixo original (campo `custo_fixo_id`)

#### Exemplos:
- Aluguel
- Salários
- Internet/Telefone
- Energia elétrica
- Plano de software (SaaS)
- Seguros mensais
- Condomínio

---

## 🔄 Como Funciona o Sistema

### Fluxo de Custos Fixos:

```
1. Você cadastra um CUSTO FIXO
   ↓
2. Define valor, dia de vencimento, categoria
   ↓
3. Sistema GERA automaticamente lançamentos todos os meses
   ↓
4. Lançamentos aparecem em "Contas a Pagar" com origem "CUSTO_FIXO"
   ↓
5. Você paga normalmente como qualquer conta a pagar
```

### Identificação Visual:

Nas listas de **Contas a Pagar**, agora você verá:

| Origem | Badge | Ícone | Significado |
|--------|-------|-------|-------------|
| **Manual** | 🔵 Azul | 👆 | Lançamento manual |
| **Custo Fixo** | 🟡 Amarelo | 🔁 | Gerado automaticamente |
| **Ordem de Serviço** | 🔵 Info | 🔧 | Da OS |

---

## 📍 Onde Encontrar

### Custos Fixos:
1. Menu lateral > Financeiro > **GESTÃO DE CUSTOS** > **Custos Fixos**
2. Ou acesse: `/financeiro/custos-fixos`

### Contas a Pagar:
1. Menu lateral > Financeiro > **Contas a Pagar**
2. Ou acesse: `/financeiro/contas-pagar`

---

## ✅ Resolução dos Problemas

### Problema 1: ✅ RESOLVIDO - Distinção entre Contas a Pagar e Custos Fixos

**Solução Implementada:**
1. ✅ Adicionado campo `origem` em `LancamentoFinanceiro`
2. ✅ Adicionado campo `custo_fixo_id` para vincular ao custo fixo
3. ✅ Badges visuais coloridas indicam a origem
4. ✅ Link direto para o custo fixo quando aplicável
5. ✅ Propriedades formatadas: `origem_formatada`, `origem_cor`, `origem_icone`

### Problema 2: ✅ RESOLVIDO - Lista de Custos Fixos não aparecia

**Solução Implementada:**
1. ✅ Corrigido template `listar.html` - adicionado `data_hoje` nas variáveis
2. ✅ Corrigida rota `listar_custos_fixos` - agora passa `data_hoje=date.today()`
3. ✅ Menu lateral já tem link para Custos Fixos (estava correto)

---

## 🛠️ Próximos Passos

### 1. Executar Script de Migração:
```bash
python scripts/adicionar_campo_origem.py
```

Este script:
- ✅ Adiciona coluna `origem` na tabela `lancamentos_financeiros`
- ✅ Adiciona coluna `custo_fixo_id` na tabela `lancamentos_financeiros`
- ✅ Atualiza lançamentos existentes com `origem = 'MANUAL'`

### 2. Testar Funcionalidades:

#### Criar um Custo Fixo:
1. Acesse: Financeiro > Custos Fixos > Novo Custo Fixo
2. Preencha:
   - Nome: Ex: "Aluguel do Escritório"
   - Valor Mensal: Ex: R$ 2.500,00
   - Categoria: "Aluguel"
   - Dia Vencimento: Ex: 10
   - Data Início: Data atual
3. Salve

#### Verificar Lançamentos Automáticos:
1. Acesse: Financeiro > Contas a Pagar
2. Procure por lançamentos com badge amarelo "Custo Fixo Recorrente"
3. Clique no link do custo fixo para ver detalhes

---

## 📊 Diferenças Visuais

### Na Listagem de Contas a Pagar:

**Antes:**
```
Descrição | Fornecedor | Valor | Vencimento | Status
```

**Agora:**
```
Descrição | Fornecedor | ORIGEM | Valor | Vencimento | Status
                        ^^^^^^^^
                        NOVO!
```

**Exemplo de Linha:**
```
Aluguel - 2026-02 | Imobiliária XYZ | [🟡 Custo Fixo Recorrente] | R$ 2.500,00 | 10/02/2026 | Pendente
                                      [🔗 Aluguel do Escritório]
                                      ↑ Link para o custo fixo
```

---

## 💡 Dicas de Uso

### Quando Usar Custos Fixos:
✅ Despesas que se repetem **todo mês**
✅ Valores **fixos** ou muito próximos
✅ Você quer **automação**
✅ Precisa de **controle orçamentário**

### Quando Usar Contas a Pagar (Manual):
✅ Despesas **eventuais**
✅ Valores que **variam muito**
✅ Lançamento **único**
✅ Despesas **não previstas**

---

## 🎯 Benefícios

1. **Organização**: Separação clara entre despesas fixas e variáveis
2. **Automação**: Não precisa lançar aluguel todo mês
3. **Rastreabilidade**: Sabe exatamente de onde veio cada lançamento
4. **Planejamento**: Visão clara dos custos fixos mensais
5. **Controle**: Dashboard específico para custos fixos

---

## 📞 Suporte

Se precisar de ajuda:
1. Verifique se executou o script de migração
2. Confira se os custos fixos estão com status "Ativo"
3. Verifique se a data de início é anterior à data atual
4. Teste criar um custo fixo novo e gerar lançamento
