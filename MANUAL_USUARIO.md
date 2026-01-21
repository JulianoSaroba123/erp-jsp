# 📘 MANUAL DO USUÁRIO - ERP JSP v3.1.0

## 🏢 Sistema de Gestão Empresarial Completo

### Guia Prático de Uso

---

## 📑 ÍNDICE

1. [Primeiros Passos](#primeiros-passos)
2. [Dashboard Financeiro](#dashboard-financeiro)
3. [Lançamentos Financeiros](#lançamentos-financeiros)
4. [Contas Bancárias](#contas-bancárias)
5. [Conciliação Bancária](#conciliação-bancária)
6. [Fluxo de Caixa](#fluxo-de-caixa)
7. [DRE - Demonstrativo de Resultados](#dre)
8. [Plano de Contas](#plano-de-contas)
9. [Orçamento Anual](#orçamento-anual)
10. [Centros de Custo](#centros-de-custo)
11. [Custos Fixos](#custos-fixos)
12. [Notas Fiscais](#notas-fiscais)
13. [🆕 Notificações e Alertas](#notificações)
14. [🆕 Importação em Lote](#importação-em-lote)
15. [🆕 Rateio de Despesas](#rateio-de-despesas)
16. [🆕 Relatórios Customizados](#relatórios-customizados)

---

## 1. PRIMEIROS PASSOS {#primeiros-passos}

### Acessar o Sistema

1. Abra seu navegador
2. Digite: `https://seu-dominio.com` ou `http://localhost:5000`
3. Faça login com suas credenciais

### Estrutura do Menu

O menu lateral está organizado por módulos:

```
📊 PAINEL
└── Dashboard Principal

💰 FINANCEIRO
├── Dashboard Financeiro
├── Lançamentos
├── Contas a Pagar
├── Contas a Receber
└── Chaves de Documentos

🏦 GESTÃO BANCÁRIA
├── Contas Bancárias
├── Conciliação Bancária
├── Transferências
└── Extratos

📈 ANÁLISES E RELATÓRIOS
├── Fluxo de Caixa
├── DRE
├── Orçamento Anual
└── 🆕 Relatórios Customizados

🔧 GESTÃO DE CUSTOS
├── Centros de Custo
├── Custos Fixos
├── 🆕 Rateio de Despesas
└── Plano de Contas

📄 DOCUMENTOS
├── Notas Fiscais
└── 🆕 Importação em Lote

🔔 ALERTAS
└── 🆕 Notificações
```

---

## 2. DASHBOARD FINANCEIRO {#dashboard-financeiro}

### O que você vê

- 📊 **Cards resumo**:
  - Total de receitas do mês
  - Total de despesas do mês
  - Saldo do mês
  - Lançamentos pendentes

- 📈 **Gráficos**:
  - Evolução mensal
  - Contas a pagar/receber

- 📋 **Últimos lançamentos**

### Como usar

1. No menu, clique em **"Financeiro > Dashboard"**
2. Visualize os indicadores principais
3. Clique nos cards para ver detalhes
4. Use os filtros para mudar o período

---

## 3. LANÇAMENTOS FINANCEIROS {#lançamentos-financeiros}

### O que são

Todos os registros de entrada e saída de dinheiro da empresa.

### Tipos de Lançamento

- 💰 **Receita**: Dinheiro que entrou
- 💸 **Despesa**: Dinheiro que saiu
- 📥 **Conta a Receber**: Dinheiro que vai entrar
- 📤 **Conta a Pagar**: Dinheiro que vai sair

### Como CRIAR um Lançamento

1. **Menu**: Financeiro > Lançamentos > **"+ Novo Lançamento"**

2. **Preencha os campos**:
   - **Descrição**: Ex: "Pagamento fornecedor ABC"
   - **Valor**: Ex: R$ 1.500,00
   - **Tipo**: Escolha (Receita/Despesa/Conta a Pagar/Conta a Receber)
   - **Data Lançamento**: Quando aconteceu
   - **Data Vencimento**: Quando vence
   - **Categoria**: Ex: "Fornecedores", "Vendas"
   - **Status**: Pendente, Pago, Recebido, etc.

3. **Campos opcionais**:
   - Cliente/Fornecedor
   - Conta Bancária
   - Centro de Custo
   - Nº Documento
   - Forma de Pagamento
   - Observações

4. Clique em **"Salvar"**

### Como PAGAR/RECEBER um Lançamento

**Opção 1 - Rápida**:
1. Na lista de lançamentos, clique no botão **"💰 Pagar"** ou **"✅ Receber"**
2. Confirme a data de pagamento
3. Pronto!

**Opção 2 - Detalhada**:
1. Abra o lançamento (clique nele)
2. Clique em **"Editar"**
3. Altere o status para **"Pago"** ou **"Recebido"**
4. Preencha a **Data de Pagamento**
5. Salve

### Como FILTRAR Lançamentos

Use os filtros no topo da lista:
- **Tipo**: Receita, Despesa, etc.
- **Status**: Pendente, Pago, etc.
- **Categoria**: Escolha uma
- **Período**: Data início e fim
- Clique em **"Filtrar"**

### Como EXPORTAR para Excel

1. Filtre os lançamentos desejados
2. Clique no botão **"📥 Exportar Excel"**
3. O arquivo será baixado

---

## 4. CONTAS BANCÁRIAS {#contas-bancárias}

### O que são

Cadastro das contas bancárias e caixas da empresa.

### Como CADASTRAR uma Conta

1. **Menu**: Financeiro > Contas Bancárias > **"+ Nova Conta"**

2. **Preencha**:
   - **Nome**: Ex: "Banco do Brasil - Conta Corrente"
   - **Tipo**: Conta Corrente, Poupança ou Caixa
   - **Banco**: Nome do banco
   - **Agência**: Ex: 1234-5
   - **Número da Conta**: Ex: 12345-6
   - **Saldo Inicial**: Saldo atual da conta
   - **Limite de Crédito**: Se tiver cheque especial

3. **Marque**:
   - ✅ **Ativa**: Se está em uso
   - ✅ **Principal**: Se for a conta principal da empresa

4. Salve

### Como fazer TRANSFERÊNCIA entre Contas

1. **Menu**: Financeiro > Contas Bancárias > **"Transferência"**

2. **Preencha**:
   - **Conta Origem**: De onde sai o dinheiro
   - **Conta Destino**: Para onde vai
   - **Valor**: R$ 1.000,00
   - **Data**: Quando foi feita
   - **Descrição**: Ex: "Transferência para pagar fornecedores"

3. Clique em **"Transferir"**

O sistema automaticamente:
- ✅ Desconta da conta origem
- ✅ Adiciona na conta destino
- ✅ Cria os lançamentos correspondentes

---

## 5. CONCILIAÇÃO BANCÁRIA {#conciliação-bancária}

### O que é

Comparar seu extrato bancário com os lançamentos do sistema para garantir que está tudo correto.

### Como fazer CONCILIAÇÃO

#### Passo 1: Importar Extrato

1. **Menu**: Financeiro > Conciliação Bancária > **"📤 Importar Extrato"**

2. **Faça upload** do arquivo:
   - Formatos aceitos: **OFX** ou **CSV**
   - Baixe o extrato no site do seu banco

3. **Selecione a conta bancária**

4. Clique em **"Importar"**

#### Passo 2: Conciliar

1. Você verá duas colunas:
   - **Esquerda**: Extratos bancários pendentes
   - **Direita**: Lançamentos do sistema

2. **Para conciliar**:
   - Clique em um extrato da esquerda (ele fica destacado)
   - Clique no lançamento correspondente da direita
   - Clique em **"🔗 Conciliar"**

3. Repita para todos os itens

#### Passo 3: Verificar Diferenças

- **Extratos sem lançamento**: Algo que está no banco mas não no sistema
  - *Ação*: Crie o lançamento correspondente

- **Lançamentos sem extrato**: Algo que está no sistema mas não no banco
  - *Ação*: Verifique se foi realmente pago/recebido

### Histórico de Conciliações

**Menu**: Financeiro > Conciliação Bancária > **"📜 Histórico"**
- Veja todas as conciliações já feitas
- Desconcilie se necessário

---

## 6. FLUXO DE CAIXA {#fluxo-de-caixa}

### O que é

Projeção de entradas e saídas de dinheiro para os próximos dias.

### Como usar

1. **Menu**: Financeiro > Fluxo de Caixa

2. **Escolha o período**:
   - 30 dias (padrão)
   - 60 dias
   - 90 dias

3. **Filtre por conta** (opcional):
   - Todas as contas
   - Ou uma específica

4. Clique em **"Carregar"**

### O que você vê

- 📊 **Gráfico**: Evolução do saldo dia a dia
- 💰 **Saldo Inicial**: Quanto você tem hoje
- 📈 **A Receber**: Quanto vai entrar
- 📉 **A Pagar**: Quanto vai sair
- 🎯 **Saldo Projetado**: Quanto terá no final

### Exportar

Clique em **"📥 Exportar Excel"** para baixar a planilha completa.

---

## 7. DRE - DEMONSTRATIVO DE RESULTADOS {#dre}

### O que é

Relatório contábil que mostra o resultado (lucro ou prejuízo) da empresa.

### Como gerar

1. **Menu**: Financeiro > DRE

2. **Escolha o período**:
   - **Mês**: Selecione mês e ano
   - **Ano**: Deixe o mês em branco

3. **Escolha comparação** (opcional):
   - Mensal: Compara com mês anterior
   - Anual: Compara com ano anterior

4. Clique em **"Gerar DRE"**

### O que você vê

```
RECEITA BRUTA
(-) Deduções
= RECEITA LÍQUIDA ..................... 100%

(-) Custos
= LUCRO BRUTO ......................... 35%

(-) Despesas Operacionais
= LUCRO OPERACIONAL ................... 20%

(+/-) Resultado Financeiro
= LUCRO LÍQUIDO ....................... 15%
```

### Indicadores

- 📊 **Margem Bruta**: % de lucro sobre vendas
- 📊 **Margem Operacional**: % depois das despesas
- 📊 **Margem Líquida**: % de lucro final

### Exportar

Clique em **"📥 Exportar Excel"** para baixar o DRE formatado.

---

## 8. PLANO DE CONTAS {#plano-de-contas}

### O que é

Estrutura hierárquica para organizar receitas e despesas.

### Estrutura Padrão

```
1. ATIVO
  1.1 Ativo Circulante
    1.1.1 Caixa e Bancos
    1.1.2 Contas a Receber

2. PASSIVO
  2.1 Passivo Circulante
    2.1.1 Fornecedores
    2.1.2 Contas a Pagar

3. RECEITAS
  3.1 Receita de Serviços
  3.2 Receita de Vendas

4. DESPESAS
  4.1 Despesas Operacionais
    4.1.1 Salários
    4.1.2 Aluguel
```

### Como ADICIONAR uma Conta

1. **Menu**: Financeiro > Plano de Contas > **"+ Nova Conta"**

2. **Preencha**:
   - **Código**: Ex: 4.1.5
   - **Nome**: Ex: "Telefone e Internet"
   - **Tipo**: ATIVO, PASSIVO, RECEITA ou DESPESA
   - **Conta Pai**: Conta acima na hierarquia
   - **Aceita Lançamento**: Marque se for usar diretamente

3. Salve

### Como CRIAR Plano Padrão

Se ainda não tem plano de contas:
1. Clique em **"🎯 Criar Plano Padrão"**
2. O sistema cria automaticamente todas as contas básicas
3. Você pode editar depois

---

## 9. ORÇAMENTO ANUAL {#orçamento-anual}

### O que é

Planejamento de quanto você espera receber e gastar por mês/categoria.

### Como CRIAR Orçamento

1. **Menu**: Financeiro > Orçamento Anual > **"+ Novo Orçamento"**

2. **Preencha**:
   - **Ano**: 2026
   - **Mês**: Janeiro (1 a 12)
   - **Tipo**: RECEITA ou DESPESA
   - **Categoria**: Ex: "Vendas", "Fornecedores"
   - **Valor Orçado**: R$ 50.000,00

3. Salve

### Como ACOMPANHAR Execução

1. **Menu**: Financeiro > Orçamento Anual > **"Dashboard"**

2. Você verá:
   - 💰 **Orçado**: Quanto planejou
   - ✅ **Realizado**: Quanto aconteceu
   - 📊 **% Executado**: Percentual
   - ⚖️ **Variação**: Diferença

### Status do Orçamento

- 🟢 **Dentro** (<80%): Tudo ok
- 🟡 **Atenção** (80-100%): Cuidado
- 🔴 **Estourado** (>100%): Passou do limite!

### Criar Orçamento Padrão

Clique em **"🎯 Criar Orçamento Padrão"** para o sistema criar automaticamente orçamentos para todas as principais categorias.

---

## 10. CENTROS DE CUSTO {#centros-de-custo}

### O que são

Departamentos, projetos ou áreas que você quer acompanhar os custos separadamente.

### Exemplos

- Departamento Comercial
- Departamento Administrativo
- Departamento TI
- Projeto Solar Cliente X
- Filial São Paulo

### Como CADASTRAR

1. **Menu**: Financeiro > Centros de Custo > **"+ Novo Centro"**

2. **Preencha**:
   - **Código**: Ex: CC-001
   - **Nome**: Ex: "Departamento Comercial"
   - **Tipo**: Departamento, Projeto, Filial ou Produto
   - **Responsável**: Nome do gerente
   - **Orçamento Mensal**: R$ 20.000,00

3. Salve

### Como usar

Ao criar um lançamento, selecione o **Centro de Custo** para atribuir a despesa.

### Relatórios

Clique em **"📊 Relatório"** no centro de custo para ver:
- Total de despesas do centro
- Comparação com orçamento
- Evolução mensal

---

## 11. CUSTOS FIXOS {#custos-fixos}

### O que são

Despesas que se repetem todo mês (aluguel, salários, etc.).

### Como CADASTRAR

1. **Menu**: Financeiro > Custos Fixos > **"+ Novo Custo Fixo"**

2. **Preencha**:
   - **Nome**: Ex: "Aluguel do Escritório"
   - **Valor Mensal**: R$ 2.500,00
   - **Categoria**: Ex: "Aluguel"
   - **Dia do Vencimento**: 5 (dia 5 de cada mês)
   - **Data Início**: 01/01/2026
   - **Data Fim**: Deixe vazio se for indefinido

3. **Opções**:
   - ✅ **Gerar Automaticamente**: Sistema cria os lançamentos automaticamente
   - Escolha **Conta Bancária**
   - Escolha **Centro de Custo**

4. Salve

### Gerar Lançamentos Automaticamente

1. **Menu**: Financeiro > Custos Fixos > **"Dashboard"**
2. Clique em **"⚙️ Gerar Lançamentos do Mês"**
3. O sistema cria todos os lançamentos dos custos fixos automaticamente!

---

## 12. NOTAS FISCAIS {#notas-fiscais}

### O que é

Gestão de notas fiscais de entrada (compras) e saída (vendas).

### Como ADICIONAR Nota Fiscal

1. **Menu**: Financeiro > Notas Fiscais > **"+ Nova Nota"**

2. **Upload de Arquivos**:
   - **XML**: Arquivo da NF-e (o sistema lê automaticamente!)
   - **PDF**: DANFE para visualização

3. O sistema **extrai automaticamente**:
   - Número e série
   - Chave de acesso
   - Valores
   - Emitente/Destinatário
   - Impostos

4. **Ou preencha manualmente**:
   - Número, série, data
   - Valores
   - Cliente/Fornecedor

5. **Tipo**: ENTRADA ou SAÍDA

6. Salve

### Criar Lançamento da Nota

Clique em **"💰 Criar Lançamento"** para gerar automaticamente um lançamento financeiro da nota fiscal.

### Galeria de Notas

**Menu**: Financeiro > Notas Fiscais > **"🖼️ Galeria"**
- Visualize todas as notas em formato visual
- Filtre por mês/ano
- Baixe os arquivos XML/PDF

---

## 13. 🆕 NOTIFICAÇÕES E ALERTAS {#notificações}

### O que são

Sistema que avisa automaticamente sobre eventos importantes.

### Tipos de Alertas

#### 1. ⏰ Vencimentos
- **Hoje**: Alerta URGENTE
- **3 dias**: Alerta ALTA prioridade
- **7 dias**: Alerta MÉDIA prioridade

#### 2. 💰 Saldo Negativo
- Quando conta bancária fica negativa

#### 3. 📊 Estouro de Orçamento
- Quando orçamento passa de 90%
- Quando orçamento passa de 100%

#### 4. 📋 Conciliação Pendente
- Quando tem extratos não conciliados

### Como usar

1. **Menu**: Financeiro > **🔔 Notificações**

2. Você verá:
   - Total de notificações não lidas
   - Lista de todas as notificações

3. **Filtros**:
   - Por tipo
   - Por prioridade
   - Lidas ou não lidas

4. **Ações**:
   - ✅ **Marcar como Lida**: Clique no botão
   - 🔗 **Ir para Ação**: Clique no botão de ação
   - 📋 **Ver Todas Lidas**: Use o filtro

### Verificar Alertas Manualmente

Clique em **"🔄 Verificar Alertas"** para o sistema buscar novos alertas agora.

### Badge no Menu

O ícone 🔔 no menu mostra o número de notificações não lidas.

---

## 14. 🆕 IMPORTAÇÃO EM LOTE {#importação-em-lote}

### O que é

Importar dezenas ou centenas de lançamentos de uma vez através de Excel ou CSV.

### Como IMPORTAR

#### Passo 1: Preparar o Arquivo

Crie uma planilha Excel com estas colunas:

| data | descrição | valor | tipo |
|------|-----------|-------|------|
| 21/01/2026 | Pagamento Fornecedor ABC | 1500,00 | DESPESA |
| 22/01/2026 | Venda Cliente XYZ | 3000,00 | RECEITA |
| 23/01/2026 | Aluguel Janeiro | 2500,00 | DESPESA |

**Colunas obrigatórias**:
- **data**: Formato dd/mm/aaaa
- **descrição**: Texto
- **valor**: Número (pode usar vírgula)
- **tipo**: RECEITA, DESPESA, CONTA_RECEBER ou CONTA_PAGAR

**Colunas opcionais**:
- categoria
- status
- conta_bancaria
- centro_custo

#### Passo 2: Upload

1. **Menu**: Financeiro > Importação em Lote > **"📤 Nova Importação"**

2. **Selecione o arquivo**: .xlsx, .xls ou .csv

3. **Mapeie as colunas**:
   - Coluna Data → Escolha qual coluna do Excel
   - Coluna Descrição → Escolha qual coluna
   - Coluna Valor → Escolha qual coluna
   - Coluna Tipo → Escolha qual coluna

4. Clique em **"🚀 Importar"**

#### Passo 3: Verificar Resultado

O sistema mostra:
- ✅ **Importados**: Quantos foram importados com sucesso
- ❌ **Erros**: Quantos deram erro
- 📋 **Detalhes**: Clique para ver quais linhas erraram e porquê

### Histórico de Importações

**Menu**: Financeiro > Importação em Lote
- Veja todas as importações realizadas
- Status: Processando, Concluída, Erro, Parcial
- Clique em **"Ver Detalhes"** para ver os erros

### Exemplo de Uso

**Cenário**: Você tem 100 lançamentos de janeiro no Excel
1. Ajuste as colunas conforme o padrão
2. Faça upload
3. Em 30 segundos, todos os 100 lançamentos estarão no sistema!
4. Economiza horas de digitação manual

---

## 15. 🆕 RATEIO DE DESPESAS {#rateio-de-despesas}

### O que é

Dividir uma despesa entre vários departamentos/projetos.

### Quando usar

**Exemplos**:
- Aluguel dividido entre 3 departamentos
- Internet compartilhada por toda empresa
- Energia elétrica proporcional por área

### Como RATEAR uma Despesa

#### Passo 1: Criar o Lançamento

Crie normalmente:
- Descrição: "Aluguel Janeiro"
- Valor: R$ 10.000,00
- Tipo: DESPESA

#### Passo 2: Ratear

1. Na lista de lançamentos, clique em **"💰 Ratear"**

2. **Adicione os centros**:

   **Centro 1**: Departamento Comercial
   - Percentual: 50%
   - Valor: R$ 5.000,00 (calculado automaticamente)

   **Centro 2**: Departamento Administrativo
   - Percentual: 30%
   - Valor: R$ 3.000,00

   **Centro 3**: Departamento TI
   - Percentual: 20%
   - Valor: R$ 2.000,00

3. **Total**: Deve somar 100%
   - ✅ Sistema valida automaticamente

4. Clique em **"Salvar Rateio"**

### Ver Rateios de um Centro

1. **Menu**: Financeiro > Centros de Custo
2. Clique em **"Ver Rateios"** no centro desejado
3. Veja todas as despesas rateadas para esse centro
4. Filtre por período

### Exemplo Prático

**Despesa**: Energia Elétrica R$ 3.000,00

**Rateio por área ocupada**:
- Produção (60%): R$ 1.800,00
- Escritório (30%): R$ 900,00
- Almoxarifado (10%): R$ 300,00

Agora cada centro sabe exatamente quanto pagou de energia!

---

## 16. 🆕 RELATÓRIOS CUSTOMIZADOS {#relatórios-customizados}

### O que são

Crie seus próprios relatórios escolhendo campos, filtros e formato.

### Como CRIAR um Relatório

#### Passo 1: Novo Relatório

1. **Menu**: Financeiro > Relatórios Customizados > **"+ Novo Relatório"**

2. **Informações Básicas**:
   - **Nome**: Ex: "Despesas Operacionais Janeiro"
   - **Descrição**: Ex: "Todas despesas operacionais do mês"
   - **Tipo**: Escolha (Lançamentos, Contas a Pagar, etc.)

#### Passo 2: Escolher Campos

Marque os campos que deseja ver:
- [ ] Data Lançamento
- [x] Data Vencimento
- [x] Descrição
- [x] Valor
- [x] Status
- [x] Categoria
- [x] Centro de Custo
- [ ] Número Documento

#### Passo 3: Definir Filtros

Configure os filtros:
- **Tipo**: DESPESA
- **Status**: PENDENTE
- **Categoria**: Operacional
- **Data Início**: 01/01/2026
- **Data Fim**: 31/01/2026
- **Centro de Custo**: Comercial

#### Passo 4: Ordenação

- **Ordenar por**: Data Vencimento
- **Direção**: Crescente (ASC) ou Decrescente (DESC)

#### Passo 5: Formato

- **Formato Padrão**: EXCEL (ou PDF, CSV)

5. Clique em **"Salvar"**

### Como EXECUTAR um Relatório

1. **Menu**: Financeiro > Relatórios Customizados
2. Clique em **"▶️ Executar"** no relatório
3. Veja os resultados na tela
4. Clique em **"📥 Exportar"** para baixar

### Favoritos

Marque relatórios como **⭐ Favorito** para acessá-los mais rápido.

### Exemplos de Relatórios Úteis

#### 1. Despesas Pendentes do Mês
- **Campos**: Data Vencimento, Descrição, Valor
- **Filtros**: Tipo=DESPESA, Status=PENDENTE, Mês Atual
- **Ordenação**: Data Vencimento

#### 2. Receitas por Cliente
- **Campos**: Cliente, Data, Valor, Status
- **Filtros**: Tipo=RECEITA, Ano Atual
- **Agrupamento**: Cliente

#### 3. Custos por Centro
- **Campos**: Centro de Custo, Categoria, Valor
- **Filtros**: Tipo=DESPESA, Período Custom
- **Agrupamento**: Centro de Custo

---

## 💡 DICAS E BOAS PRÁTICAS

### Organização

1. ✅ **Categorize** todos os lançamentos
2. ✅ **Use centros de custo** para análises detalhadas
3. ✅ **Faça conciliação** bancária semanalmente
4. ✅ **Configure custos fixos** para economizar tempo

### Alertas

1. ✅ Verifique as **notificações** diariamente
2. ✅ Aja nos alertas **URGENTES** imediatamente
3. ✅ Programe **pagamentos** com antecedência

### Relatórios

1. ✅ Gere o **DRE** mensalmente
2. ✅ Acompanhe o **Fluxo de Caixa** semanalmente
3. ✅ Revise o **Orçamento** mensalmente

### Backup

1. ✅ Exporte dados importantes em **Excel**
2. ✅ Mantenha cópias dos **XMLs** das notas fiscais

---

## 🆘 SOLUÇÃO DE PROBLEMAS

### Lançamento não aparece no fluxo de caixa
- ✅ Verifique se tem **Data de Vencimento**
- ✅ Verifique o **Status** (deve ser Pendente)
- ✅ Verifique o **Período** selecionado

### Conciliação não encontra lançamento
- ✅ Verifique se o **valor** é exatamente igual
- ✅ Verifique a **data** (pode estar alguns dias diferente)
- ✅ Crie o lançamento se não existir

### Orçamento não mostra realizado
- ✅ Verifique se os lançamentos têm a mesma **categoria**
- ✅ Verifique o **período** (mês e ano)
- ✅ Verifique o **tipo** (RECEITA ou DESPESA)

### Importação dá erro
- ✅ Verifique o **formato da data** (dd/mm/aaaa)
- ✅ Verifique o **tipo** (RECEITA, DESPESA, etc.)
- ✅ Veja os **detalhes do erro** clicando no histórico

---

## 📞 ATALHOS DO TECLADO

| Atalho | Ação |
|--------|------|
| `Alt + N` | Novo Lançamento |
| `Alt + F` | Abrir Filtros |
| `Alt + S` | Salvar Formulário |
| `Esc` | Fechar Modal |

---

## 📊 FLUXO DE TRABALHO RECOMENDADO

### Diário (5 minutos)
1. ✅ Verificar **notificações**
2. ✅ Registrar **lançamentos** do dia
3. ✅ Pagar contas **vencendo hoje**

### Semanal (30 minutos)
1. ✅ Fazer **conciliação bancária**
2. ✅ Ver **fluxo de caixa** da semana
3. ✅ Agendar **pagamentos** da próxima semana

### Mensal (2 horas)
1. ✅ Gerar **DRE** do mês
2. ✅ Comparar **Orçamento x Realizado**
3. ✅ Revisar **custos** por centro
4. ✅ Importar **notas fiscais** do mês
5. ✅ Gerar **relatórios** para gerência

---

## 🎯 CONCLUSÃO

Este manual cobre as principais funcionalidades do **ERP JSP v3.1.0**.

### Benefícios do Sistema

- 💰 Controle financeiro completo
- 📊 Relatórios gerenciais profissionais
- ⏰ Alertas automáticos
- 📥 Importação em massa
- 🎯 Análises por centro de custo
- 💡 Decisões baseadas em dados reais

### Próximos Passos

1. Explore cada módulo com calma
2. Configure seus custos fixos
3. Crie seu plano de contas
4. Comece a registrar lançamentos
5. Acompanhe os indicadores

---

## 📖 MAIS INFORMAÇÕES

- **Documentação Técnica**: `NOVAS_FUNCIONALIDADES_v3.1.md`
- **Análise Completa**: `ANALISE_SISTEMA_FINANCEIRO_COMPLETA.md`
- **Suporte**: Consulte a equipe de TI

---

**ERP JSP v3.1.0**  
*Sistema de Gestão Empresarial Profissional*  
*© 2026 JSP Soluções*

---

📘 **Manual do Usuário** | Versão 3.1.0 | Janeiro 2026
