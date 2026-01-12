# 📋 Mapeamento Completo - Módulo Energia Solar v3.0

**Data do Mapeamento:** 08/01/2026  
**Objetivo:** Redesign completo do módulo baseado no workflow do Excel atual  
**Status:** Planejamento Concluído ✅

---

## 📊 Visão Geral

### Situação Atual
- Wizard linear (8 etapas sequenciais)
- Foco excessivo em dados técnicos
- Sem dashboard visual
- Sem gestão de orçamento integrada
- Sem calculadora de financiamento
- Sem ferramentas de análise (tabelas 12/25 anos)
- Sem sistema de merge fields para documentos

### Estrutura Desejada (baseada no Excel)
- Dashboard com KPIs visuais
- Gestão de projetos (criação, edição, duplicação)
- Modais contextuais (Dados Técnicos, Financeiros, Orçamento)
- Ferramentas de análise e documentação
- Sistema de status e workflow
- Integração com concessionárias (ANEEL)

---

## 🗂️ Estrutura de Dados

### 📦 Novas Tabelas

#### 1. `concessionarias`
```sql
id                  SERIAL PRIMARY KEY
nome                VARCHAR(200) NOT NULL
regiao              VARCHAR(100)
te                  DECIMAL(10,4)      -- Tarifa de Energia (R$/kWh)
tusd                DECIMAL(10,4)      -- Tarifa Uso Sistema Distribuição
pis                 DECIMAL(5,2)       -- Percentual PIS
cofins              DECIMAL(5,2)       -- Percentual COFINS
icms                DECIMAL(5,2)       -- Percentual ICMS
data_atualizacao    DATE
ativo               BOOLEAN DEFAULT TRUE
created_at          TIMESTAMP DEFAULT NOW()
```

#### 2. `orcamento_itens`
```sql
id                  SERIAL PRIMARY KEY
projeto_id          INTEGER REFERENCES energia_solar_projeto(id)
descricao           VARCHAR(200) NOT NULL
quantidade          DECIMAL(10,2)
unidade_medida      VARCHAR(20)
preco_unitario      DECIMAL(10,2)
preco_total         DECIMAL(10,2)      -- Calculado
lucro_percentual    DECIMAL(5,2)
faturamento         VARCHAR(50)        -- EMPRESA, etc
ordem               INTEGER            -- Para ordenação
created_at          TIMESTAMP DEFAULT NOW()
```

#### 3. `projeto_financiamento`
```sql
id                  SERIAL PRIMARY KEY
projeto_id          INTEGER REFERENCES energia_solar_projeto(id) UNIQUE
valor_financiado    DECIMAL(10,2)
n_meses             INTEGER
juros_mensal        DECIMAL(5,2)
valor_parcela       DECIMAL(10,2)      -- Calculado
total_pagar         DECIMAL(10,2)      -- Calculado
total_juros         DECIMAL(10,2)      -- Calculado
incluir_em_pdf      BOOLEAN DEFAULT FALSE
created_at          TIMESTAMP DEFAULT NOW()
```

#### 4. `marco_legal_taxacao`
```sql
id                  SERIAL PRIMARY KEY
ano                 INTEGER NOT NULL UNIQUE
percentual_fio_b    DECIMAL(5,2)
descricao           VARCHAR(200)
created_at          TIMESTAMP DEFAULT NOW()
```

#### 5. `custos_fixos_template`
```sql
id                  SERIAL PRIMARY KEY
descricao           VARCHAR(200) NOT NULL
quantidade          DECIMAL(10,2) DEFAULT 1.00
unidade_medida      VARCHAR(20)
preco_unitario      DECIMAL(10,2) DEFAULT 0.00
lucro_percentual    DECIMAL(5,2) DEFAULT 0.00
faturamento         VARCHAR(50) DEFAULT 'EMPRESA'
ordem               INTEGER
ativo               BOOLEAN DEFAULT TRUE
created_at          TIMESTAMP DEFAULT NOW()
```

#### 6. `chaves_documentos` (view ou tabela de referência)
```sql
id                  SERIAL PRIMARY KEY
chave               VARCHAR(100) NOT NULL UNIQUE  -- [cliente_nome]
descricao           VARCHAR(200)
categoria           VARCHAR(50)  -- projeto, cliente, tecnico, financeiro
tipo_dado           VARCHAR(50)  -- texto, numero, data, moeda
exemplo             VARCHAR(200)
created_at          TIMESTAMP DEFAULT NOW()
```

### 🔄 Campos Novos em `energia_solar_projeto`

```sql
-- Gestão de Projeto
titulo_projeto          VARCHAR(200)
status_orcamento        VARCHAR(20)    -- EM ABERTO, APROVADO, REPROVADO
etapa_projeto           VARCHAR(20)    -- A VISITAR, VISITADO, FINALIZADO
conexao_tipo            VARCHAR(50)    -- HADO CERÂMICA, SOLO, TELHADO, etc
previsao_entrega        DATE
endereco_instalacao     TEXT

-- Dados Financeiros
concessionaria_id       INTEGER REFERENCES concessionarias(id)
economia_anual_prevista DECIMAL(10,2)
impostos_percentual     DECIMAL(5,2)   -- Impostos global do orçamento

-- Totais calculados
valor_orcamento_total   DECIMAL(10,2)
```

---

## 🏗️ Módulos e Funcionalidades

### 1️⃣ **Módulo Concessionárias**

**Objetivo:** Cadastro de distribuidoras de energia com tarifas e impostos

**Funcionalidades:**
- ✅ CRUD completo (estilo Cliente/Fornecedor)
- ✅ Campos: nome, região, TE, TUSD, PIS, COFINS, ICMS
- ✅ Data de atualização
- ✅ Status (ativa/inativa)
- ✅ Listagem com busca e filtros

**Integração:**
- Modal "Dados Financeiros" → Select concessionária → Auto-preenche tarifas e impostos

**Arquivos:**
```
app/concessionaria/
├── concessionaria_model.py
├── concessionaria_routes.py
└── templates/concessionaria/
    ├── concessionarias_list.html
    └── concessionaria_form.html
```

---

### 2️⃣ **Listagem de Projetos Redesenhada**

**Melhorias:**

**Colunas:**
- ID (clicável)
- CLIENTE
- TÍTULO DO PROJETO
- POTÊNCIA (kWp)
- **CONEXÃO** (tipo de instalação) 🆕
- DATA CADASTRO
- PREVISÃO DE ENTREGA
- **ORÇAMENTO** (status colorido) 🆕
  - 🟢 APROVADO (verde)
  - 🔴 REPROVADO (vermelho)
  - ⚪ EM ABERTO (branco)
- **ETAPA** (workflow) 🆕
  - A VISITAR
  - VISITADO
  - FINALIZADO

**Botões de Ação:**
- 🔓 **Abrir Projeto** → Dashboard
- 📑 **Duplicar Projeto** → Clone
- ⬍ **Ordenar Projetos** → Reordenação

**Arquivo:**
```
app/energia_solar/templates/energia_solar/projetos_list.html
```

---

### 3️⃣ **Dashboard do Projeto**

**Layout:**

**Cabeçalho:**
```
ID: 25 - Projeto: 430542277

[ORÇAMENTO: APROVADO] [ETAPA PROJETO: FINALIZADO] [PRAZO ENTREGA: 03/06/2026]

CLIENTE: ALESSANDRO FERREIRA DE SOUZA
LOCAL DE INSTALAÇÃO: RUA DOM PEDRO I, 141, LOTEAMENTO JARDIM RESIDEN...

[▼ Exibir Informações]
```

**KPIs (Cards):**

1. **Capacidade do Sistema**
   - Valor: 2,92 kWp
   - Ícone: ⚡

2. **Consumo Médio Mensal**
   - Valor: 178 kWh/Mês
   - Ícone: 📊

3. **Economia Anual Prevista**
   - Valor: R$ 8.715,18
   - Ícone: 🌱

4. **Valor do Orçamento**
   - Valor: R$ 10.930,07
   - Ícone: 💰

**Botões de Ação:**
- ⚙️ Editar Dados
- ⚡ Dados Técnicos
- 💰 Dados Financeiros
- 💵 Editar Orçamento
- 🏦 Financiamento

**Seções Expansíveis:**
- Resumo (coordenadas, irradiação, produção)
- Gráfico de Geração Mensal

**Arquivo:**
```
app/energia_solar/templates/energia_solar/projeto_dashboard.html
```

---

### 4️⃣ **Modal Criação/Edição de Projeto**

**Substituir wizard atual por modal simples**

**Campos:**
- Cliente * (select com busca)
- Título do Projeto *
- Data de Cadastro * (auto)
- Previsão de Entrega
- Status do Orçamento * (select)
  - EM ABERTO
  - APROVADO
  - REPROVADO
- Etapa do Projeto * (select)
  - A VISITAR
  - VISITADO
  - FINALIZADO
- Tipo de Conexão (select)
  - HADO CERÂMICA
  - SOLO
  - TELHADO
  - ESTRUTURA SOL
- Endereço de Instalação (textarea)

**Validações:**
- Cliente obrigatório
- Título obrigatório
- Status e Etapa obrigatórios

**Arquivo:**
```
app/energia_solar/templates/energia_solar/projeto_form_modal.html
```

---

### 5️⃣ **Dados Técnicos (4 Abas)**

**Reorganizar campos atuais em sub-wizard de 4 etapas**

#### **Aba 1: Dados Iniciais da Instalação**
- Latitude, Longitude
- Irradiação Solar (média, mín, máx, delta)
- Tipo de Instalação
- Orientação
- Inclinação

#### **Aba 2: Método de Cálculo**
- Consumo Médio Mensal (kWh)
- Método de Dimensionamento
  - Por Consumo
  - Por Área Disponível
- Seleção de Kit
- Seleção de Placas
- Seleção de Inversores

#### **Aba 3: Ajustes Técnicos**
- Ajuste de Sombreamento (%)
- Ajuste de Sujidade (%)
- Fator de Simultaneidade (%)
- Perda de Temperatura (%)
- Eficiência do Inversor (%)

#### **Aba 4: Demais Informações**
- Observações Técnicas (textarea)
- Anexos Técnicos
- Datasheets (múltiplos PDFs)

**Navegação:**
- Botões: [◀ Anterior] [Próximo ▶] [Salvar]
- Indicador de progresso: 1/4, 2/4, 3/4, 4/4

**Arquivo:**
```
app/energia_solar/templates/energia_solar/dados_tecnicos_modal.html
```

---

### 6️⃣ **Modal Dados Financeiros**

**Integração com Concessionárias**

**Campos:**

1. **Concessionária** * (select)
   - Ao selecionar → Auto-preenche:
     - TE (Tarifa de Energia)
     - TUSD
     - PIS (%)
     - COFINS (%)
     - ICMS (%)

2. **Tarifa Final Calculada** (readonly)
   - Fórmula: TE + TUSD + impostos

3. **Economia Anual Prevista** (calculado)
   - Baseado em consumo, geração e tarifa

**Cálculo Automático:**
```python
tarifa_final = (te + tusd) * (1 + pis/100 + cofins/100 + icms/100)
economia_mensal = geracao_mensal * tarifa_final
economia_anual = economia_mensal * 12
```

**Arquivo:**
```
app/energia_solar/templates/energia_solar/dados_financeiros_modal.html
```

---

### 7️⃣ **Sistema de Orçamento**

**Modal "Editar Orçamento"**

**Estrutura:**

**Campo Global:**
- IMPOSTOS (%) - Valor único para todo orçamento

**Tabela de Itens:**
| DESCRIÇÃO | QTD | PREÇO | VLR TOTAL | LUCRO (%) | FATURAMENTO | AÇÕES |
|-----------|-----|-------|-----------|-----------|-------------|-------|
| Kit Gerador | 1.00 | R$ 0,00 | R$ 0,00 | 0,00% | EMPRESA | ✏️ ❌ |
| ... | ... | ... | ... | ... | ... | ... |

**Botões:**
- ➕ Adicionar Item
- 💾 Salvar Orçamento

**Modal "Editar Custo":**
- Descrição *
- Quantidade *
- Unidade de Medida *
- Preço Unitário (R$) *
- Faturamento * (select: EMPRESA, etc)
- Lucro (%) *

**Cálculo Automático:**
```python
vlr_total = quantidade * preco_unitario
```

**Template Padrão:**
- Ao criar novo projeto → Copia itens de `custos_fixos_template`
- Usuário pode adicionar/remover/editar conforme necessidade

**Itens Padrão Comuns:**
- Kit Gerador Energia Solar
- Comissão da Distribuidora
- Comissão de Indicação
- Comissão de Venda
- Desconto Estadual
- Desconto Municipal
- Desconto para Fechamento
- Instalação dos Módulos
- Instalação Inversores
- Material CA
- Projeto
- TRT
- Deslocamento

**Arquivos:**
```
app/energia_solar/templates/energia_solar/orcamento_modal.html
app/energia_solar/templates/energia_solar/custo_item_modal.html
```

---

### 8️⃣ **Calculadora de Financiamento**

**Modal "Financiamento"**

**Campos:**

1. **Valor Total do Serviço** (readonly)
   - Vem do orçamento total
   - Ex: R$ 10.930,07

2. **Valor a Ser Financiado (R$)** *
   - Editável (pode financiar parte ou total)

3. **Nº de Meses** *
   - Ex: 12, 24, 36, 48, 60

4. **Juros Mensal (%)** *
   - Ex: 1.5%, 2.0%, 2.5%

**Botão:**
- 🧮 CALCULAR

**Resultado (após calcular):**
```
💰 Valor da Parcela:    R$ XXX,XX
📊 Total a Pagar:       R$ XXX,XX
📈 Total de Juros:      R$ XXX,XX
```

**Cálculo Price:**
```python
i = juros_mensal / 100
n = n_meses
pv = valor_financiado

pmt = pv * (((1 + i) ** n) * i) / (((1 + i) ** n) - 1)
total_pagar = pmt * n
total_juros = total_pagar - pv
```

**Botão Final:**
- 💾 Salvar Financiamento

**Opções:**
- ☑️ Incluir financiamento na proposta PDF

**Bônus:**
- Tabela de amortização (25 primeiras parcelas)

**Arquivo:**
```
app/energia_solar/templates/energia_solar/financiamento_modal.html
```

---

### 9️⃣ **Configurações - Marco Legal**

**Tabela de Taxação do Fio B (Lei 14.300/2022)**

**CRUD Editável:**

| ANO | TAXAÇÃO DO FIO B | AÇÕES |
|-----|------------------|-------|
| 2022 ou anterior | - (isento) | ✏️ |
| 2023 | 15,00% | ✏️ |
| 2024 | 30,00% | ✏️ |
| 2025 | 45,00% | ✏️ |
| 2026 | 60,00% | ✏️ |
| 2027 | 75,00% | ✏️ |
| 2028 | 90,00% | ✏️ |
| 2029+ | 100,00% | ✏️ |

**Botões:**
- ➕ Adicionar Ano
- 💾 Salvar Alterações

**Uso:**
- Cálculo de economia nas Tabelas 12/25 anos
- Compensação de créditos ajustada pela taxação
- Argumentação comercial (urgência)

**Arquivo:**
```
app/energia_solar/templates/energia_solar/config_marco_legal.html
```

---

### 🔟 **Configurações - Chaves de Documentos**

**Sistema de Merge Fields**

**Tela de Visualização:**

| CHAVE | VALOR ATUAL | DESCRIÇÃO | USAR |
|-------|-------------|-----------|------|
| [id_projeto] | 25 | Nº de ID do projeto | ☑️ |
| [projeto_titulo] | 430542277 | Título do Projeto | ☑️ |
| [cliente_nome] | Alessandro Ferreira | Nome do Cliente | ☑️ |
| [cliente_cpf] | 430.542.277-72 | CPF do Cliente | ☑️ |
| [latitude] | -23,1101 | Latitude do local | ☑️ |
| [longitude] | -47,7164 | Longitude do local | ☑️ |
| [potencia_sistema] | 2,92 kWp | Capacidade do Sistema | ☑️ |
| [consumo_medio] | 178 kWh/Mês | Consumo Médio Mensal | ☑️ |
| [economia_anual] | R$ 8.715,18 | Economia Anual Prevista | ☑️ |
| [valor_orcamento] | R$ 10.930,07 | Valor do Orçamento | ☑️ |
| ... | ... | ... | ... |

**Categorias de Variáveis:**

1. **Dados do Projeto**
   - [id_projeto], [projeto_titulo], [data_cadastro], [previsao_entrega]
   - [status_orcamento], [etapa_projeto], [conexao_tipo]

2. **Dados do Cliente**
   - [cliente_nome], [cliente_cpf], [cliente_email], [cliente_telefone]
   - [cliente_endereco], [cliente_cidade], [cliente_estado]

3. **Dados Técnicos**
   - [latitude], [longitude], [irradiacao_media], [irradiacao_min], [irradiacao_max]
   - [potencia_sistema], [n_placas], [modelo_placa], [potencia_placa]
   - [n_inversores], [modelo_inversor], [potencia_inversor]
   - [producao_mensal], [producao_anual]

4. **Dados Financeiros**
   - [concessionaria_nome], [te], [tusd], [pis], [cofins], [icms]
   - [tarifa_final], [consumo_medio], [economia_mensal], [economia_anual]

5. **Dados do Orçamento**
   - [valor_orcamento], [impostos_percentual]
   - [itens_orcamento] (tabela formatada)

6. **Dados de Financiamento**
   - [valor_financiado], [n_meses], [juros_mensal]
   - [valor_parcela], [total_pagar], [total_juros]

**Geração Automática:**
- Sistema gera automaticamente todas as variáveis disponíveis
- Valores vêm do projeto aberto no dashboard
- Coluna "USAR" para ativar/desativar na proposta

**Arquivo:**
```
app/energia_solar/templates/energia_solar/config_chaves_documentos.html
```

---

### 1️⃣1️⃣ **Barra de Ferramentas do Projeto**

**Acesso:**
- Dashboard → Botão **"Abrir Ferramentas"**
- Aparece toolbar preta abaixo do menu principal

**Ferramentas:**

```
[🔄 Trocar Projeto] [📄 Gerar Documento] [📊 Tabela 12 Meses] [📊 Tabela 25 Anos]
```

**Implementação:**
- Toolbar contextual (só aparece quando há projeto aberto)
- Cada botão abre modal específico
- Design: fundo preto, texto branco, ícones

**Arquivo:**
```
app/energia_solar/templates/energia_solar/projeto_toolbar.html
```

---

### 1️⃣2️⃣ **Ferramenta: Trocar Projeto**

**Modal com Seletor de Projetos**

**Layout:**
```
TROCAR DE PROJETO
┌─────────────────────────────────────────────────┐
│ ID  │ CLIENTE              │ TÍTULO    │ POTÊNCIA│
├─────────────────────────────────────────────────┤
│ 12  │ CLEBER ELIABE        │ 47029072  │ 7,02 kWp│ ← Destacado (atual)
│ 13  │ JOSÉ MIRANDA FILHO   │ 40668398  │ 4,26 kWp│
│ 14  │ JOSÉ MIRANDA FILHO   │ 40668398  │ 3,51 kWp│
│ ... │ ...                  │ ...       │ ...     │
└─────────────────────────────────────────────────┘

[ABRIR PROJETO]
```

**Funcionamento:**
- Projeto atual em destaque (azul)
- Clique na linha → Seleciona projeto
- Botão "Abrir Projeto" → Carrega dashboard do selecionado
- Fecha modal automaticamente

**Arquivo:**
```
app/energia_solar/templates/energia_solar/trocar_projeto_modal.html
```

---

### 1️⃣3️⃣ **Ferramenta: Gerar Documento**

**Sistema de Mail Merge com Word**

**Modal:**
```
GERAR DOCUMENTO

┌─────────────────────────────────────────────────┐
│ SELECIONE O MODELO DO DOCUMENTO *               │
│ [___________________________________________] 🔍│
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ LOCAL DE SALVAMENTO *                           │
│ [___________________________________________] 🔍│
└─────────────────────────────────────────────────┘

[GERAR]
```

**Funcionamento:**

1. **Criar Template Word:**
   - Documento .docx com variáveis: `[cliente_nome]`, `[valor_orcamento]`, etc.
   - Salvar em pasta de templates

2. **Selecionar Template:**
   - Dialog file picker (.docx)

3. **Selecionar Destino:**
   - Dialog folder picker

4. **Gerar:**
   - Sistema lê template
   - Substitui todas `[variaveis]` por valores reais
   - Salva novo documento no destino
   - Mensagem: "Documento gerado com sucesso!"

**Biblioteca Python:**
```python
from docx import Document
from docx2pdf import convert  # Opcional: gerar PDF

def gerar_documento(template_path, output_path, variaveis):
    doc = Document(template_path)
    
    # Substituir em parágrafos
    for paragraph in doc.paragraphs:
        for chave, valor in variaveis.items():
            if f'[{chave}]' in paragraph.text:
                paragraph.text = paragraph.text.replace(f'[{chave}]', str(valor))
    
    # Substituir em tabelas
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for chave, valor in variaveis.items():
                    if f'[{chave}]' in cell.text:
                        cell.text = cell.text.replace(f'[{chave}]', str(valor))
    
    doc.save(output_path)
```

**Arquivo:**
```
app/energia_solar/templates/energia_solar/gerar_documento_modal.html
app/energia_solar/utils/document_generator.py
```

---

### 1️⃣4️⃣ **Ferramenta: Tabela 12 Meses**

**Análise Comparativa de 3 Cenários**

**Cenários:**

1. **SEM SISTEMA** (Situação Atual)
   - Consumo kWh
   - Tarifa atual
   - Valor da fatura mensal
   - **Total Anual: R$ 20.100,76**

2. **COM SISTEMA - ANTES DA LEI 14.300** (Sem Taxação)
   - Consumo kWh
   - Geração kWh
   - Simultaneidade
   - Compensação mensal (100%)
   - Tarifa mínima
   - **Economia: R$ X.XXX,XX**

3. **COM SISTEMA - LEI 14.300** (Com Taxação Fio B)
   - Consumo kWh
   - Geração kWh
   - Simultaneidade
   - Compensação ajustada (considerando taxação)
   - Tarifa de cobrança ≠ Tarifa de compensação
   - **Economia: R$ X.XXX,XX** (menor que cenário 2)

**Colunas (Exemplo Cenário 3):**
- Mês
- Consumo kWh
- Geração kWh
- Taxa (%)
- Simultaneidade (kWh)
- Tarifa Cobrança
- TE FIO B
- TE COMPENS.
- FIO B
- Crédito kWh
- Compensação Mensal
- Tarifa Mínima
- Iluminação Pública
- Demais Custos
- **Valor da Fatura**
- **Economia**

**Totalizadores:**
- Total Consumo Anual
- Total Geração Anual
- Total Economia Anual
- Comparativo: Sem Sistema vs Com Sistema

**Cálculos:**
```python
# Cenário 1: Sem Sistema
fatura_sem_sistema = consumo * tarifa_final + ilum_publica + demais

# Cenário 2: Com Sistema (sem taxação)
geracao_excedente = geracao - simultaneidade
compensacao = min(geracao_excedente, consumo - simultaneidade)
consumo_liquido = consumo - simultaneidade - compensacao
fatura_com_sistema = max(consumo_liquido * tarifa_final, tarifa_minima) + ilum_publica

# Cenário 3: Com Sistema (com taxação)
tarifa_compensacao = te * (1 - taxacao_fio_b)
creditos_valor = compensacao * tarifa_compensacao
consumo_pagar = consumo - simultaneidade
fatura_com_sistema = (consumo_pagar * tarifa_final - creditos_valor) + tarifa_minima + ilum_publica

economia = fatura_sem_sistema - fatura_com_sistema
```

**Apresentação:**
- 3 abas (ou 3 seções expansíveis)
- Gráfico comparativo
- Botão: Exportar para Excel/PDF

**Arquivo:**
```
app/energia_solar/templates/energia_solar/tabela_12_meses.html
app/energia_solar/utils/calculadora_economia.py
```

---

### 1️⃣5️⃣ **Ferramenta: Tabela 25 Anos**

**Projeção de Longo Prazo**

**Estrutura:**
- Mesma dos 3 cenários da Tabela 12 Meses
- **25 linhas** (Ano 1 a Ano 25)
- Valores anualizados (soma dos 12 meses)

**Considerações:**

1. **Degradação dos Painéis:**
   - Típico: 0,5% a 0,7% ao ano
   - Geração ano N = Geração ano 1 × (1 - degradacao)^(N-1)

2. **Reajuste de Tarifa:**
   - Inflação energética estimada (ex: 5% ao ano)
   - Tarifa ano N = Tarifa ano 1 × (1 + inflacao)^(N-1)

3. **Taxação Progressiva:**
   - Anos 2023-2029: Aumento progressivo do Fio B
   - Anos 2029+: Taxação fixa em 100%

**Cálculos Adicionais:**
- **Economia Acumulada** (soma até o ano N)
- **ROI (Return on Investment)**
  - ROI = (Economia Acumulada / Investimento Inicial) × 100
- **Payback** (ano em que economia = investimento)

**Exemplo:**
```
Ano 1:  Economia = R$ 8.715,18  |  Acumulado = R$ 8.715,18    |  ROI = 79,7%
Ano 2:  Economia = R$ 8.803,22  |  Acumulado = R$ 17.518,40   |  ROI = 160,3%
Ano 3:  Economia = R$ 8.892,05  |  Acumulado = R$ 26.410,45   |  ROI = 241,6%
...
Ano 25: Economia = R$ 11.203,88 |  Acumulado = R$ 245.673,12  |  ROI = 2.247,5%
```

**Apresentação:**
- Tabela completa
- Gráfico de linha (Economia Acumulada)
- Indicador de Payback
- Botão: Exportar para Excel/PDF

**Arquivo:**
```
app/energia_solar/templates/energia_solar/tabela_25_anos.html
app/energia_solar/utils/calculadora_roi.py
```

---

### 1️⃣6️⃣ **Funcionalidade: Duplicar Projeto**

**Clonagem de Projeto Existente**

**Fluxo:**
1. Listagem → Selecionar projeto → Botão "Duplicar Projeto"
2. Sistema copia:
   - ✅ Todos dados técnicos
   - ✅ Dados financeiros
   - ✅ Itens do orçamento
   - ✅ Configurações
3. Sistema limpa/reseta:
   - ❌ ID (novo)
   - ❌ Data de cadastro (hoje)
   - ❌ Status do orçamento → EM ABERTO
   - ❌ Etapa do projeto → A VISITAR
4. Usuário pode alterar:
   - Cliente (manter ou trocar)
   - Título do projeto
   - Endereço de instalação

**Código:**
```python
@app.route('/projeto/duplicar/<int:id>')
def duplicar_projeto(id):
    original = ProjetoEnergiaSolar.query.get_or_404(id)
    
    novo = ProjetoEnergiaSolar(
        cliente_id=original.cliente_id,  # Pode ser alterado depois
        titulo_projeto=f"Cópia de {original.titulo_projeto}",
        # Copiar campos técnicos
        latitude=original.latitude,
        longitude=original.longitude,
        # ... todos os campos
        # Resetar status
        status_orcamento='EM ABERTO',
        etapa_projeto='A VISITAR',
        data_cadastro=date.today()
    )
    db.session.add(novo)
    db.session.commit()
    
    # Duplicar itens do orçamento
    for item in original.orcamento_itens:
        novo_item = OrcamentoItem(
            projeto_id=novo.id,
            descricao=item.descricao,
            # ... copiar campos
        )
        db.session.add(novo_item)
    
    db.session.commit()
    return redirect(url_for('projeto_dashboard', id=novo.id))
```

**Arquivo:**
```
app/energia_solar/energia_solar_routes.py (nova rota)
```

---

### 1️⃣7️⃣ **Melhorias em Custos Fixos**

**Redesign da Interface**

**Antes:**
- Tabela simples sem botões
- Difícil adicionar/editar/excluir

**Depois:**
- Interface CRUD visual
- Mesma estrutura do "Editar Orçamento"

**Layout:**
```
CUSTOS FIXOS (Template para Novos Projetos)

[➕ Adicionar Item]

┌──────────────────────────────────────────────────────────────────────┐
│ DESCRIÇÃO          │ QTD  │ UND │ PREÇO   │ LUCRO │ FATUR.  │ AÇÕES │
├──────────────────────────────────────────────────────────────────────┤
│ Kit Gerador        │ 1.00 │ UN  │ R$ 0,00 │ 0,00% │ EMPRESA │ ✏️ ❌ │
│ Comissão Distrib.  │ 1.00 │ 0,1 │ R$ 0,00 │ 0,00% │ EMPRESA │ ✏️ ❌ │
│ ...                │ ...  │ ... │ ...     │ ...   │ ...     │ ...   │
└──────────────────────────────────────────────────────────────────────┘

[💾 Salvar Template]
```

**Funcionalidades:**
- Adicionar/Editar/Excluir itens
- Ordenação drag-and-drop (opcional)
- Categorização (Comissões, Descontos, Instalação, etc.)
- Ativar/Desativar itens
- Ao criar novo projeto → Sistema copia itens ativos

**Arquivo:**
```
app/energia_solar/templates/energia_solar/config_custos_fixos.html
```

---

## 🔄 Fluxos de Trabalho

### Fluxo 1: Criar Novo Projeto Completo

```
1. Listagem de Projetos → [➕ Novo]
   ↓
2. Modal "Criar Projeto"
   - Preencher: Cliente, Título, Conexão, Endereço
   - Salvar
   ↓
3. Dashboard do Projeto (criado)
   ↓
4. Botão "Dados Técnicos" → Modal 4 abas
   - Aba 1: Dados Iniciais
   - Aba 2: Método de Cálculo
   - Aba 3: Ajustes
   - Aba 4: Observações
   - Salvar
   ↓
5. Botão "Dados Financeiros" → Modal
   - Selecionar Concessionária
   - Auto-preenche tarifas
   - Salvar
   ↓
6. Botão "Editar Orçamento" → Modal
   - Itens pré-carregados (template)
   - Editar quantidades e preços
   - Adicionar/Remover itens
   - Salvar
   ↓
7. Botão "Financiamento" → Modal (opcional)
   - Preencher condições
   - Calcular parcelas
   - Salvar
   ↓
8. Abrir Ferramentas → Gerar Documento
   - Selecionar template Word
   - Gerar proposta preenchida
   ↓
9. Atualizar Status: APROVADO / REPROVADO
```

### Fluxo 2: Análise de Viabilidade

```
1. Dashboard → Abrir Ferramentas
   ↓
2. Tabela 12 Meses
   - Ver economia mensal
   - Comparar 3 cenários
   ↓
3. Tabela 25 Anos
   - Ver economia acumulada
   - Identificar payback
   - Calcular ROI
   ↓
4. Exportar para PDF/Excel
   ↓
5. Apresentar para cliente
```

### Fluxo 3: Duplicar Projeto Existente

```
1. Listagem → Selecionar projeto similar
   ↓
2. Botão "Duplicar Projeto"
   ↓
3. Sistema clona dados técnicos e orçamento
   ↓
4. Editar: Cliente, Endereço, Título
   ↓
5. Ajustar orçamento conforme necessário
   ↓
6. Gerar nova proposta
```

---

## 📊 Priorização de Tarefas

### 🔥 **Prioridade ALTA** (Fundação)
1. ✅ Criar modelo de dados (novas tabelas)
2. ✅ Módulo Concessionárias (CRUD)
3. ✅ Adicionar campos novos em energia_solar_projeto
4. ✅ Modal Criação/Edição de Projeto
5. ✅ Dashboard do Projeto (KPIs básicos)

### 🟡 **Prioridade MÉDIA** (Core Features)
6. ✅ Redesenhar listagem de projetos
7. ✅ Modal Dados Financeiros (integração concessionárias)
8. ✅ Sistema de Orçamento (CRUD itens)
9. ✅ Configurações - Marco Legal
10. ✅ Configurações - Chaves de Documentos

### 🟢 **Prioridade BAIXA** (Advanced Features)
11. ✅ Redesenhar Dados Técnicos (4 abas)
12. ✅ Calculadora de Financiamento
13. ✅ Barra de Ferramentas
14. ✅ Ferramenta: Trocar Projeto
15. ✅ Ferramenta: Gerar Documento
16. ✅ Ferramenta: Tabela 12 Meses
17. ✅ Ferramenta: Tabela 25 Anos
18. ✅ Duplicar Projeto / Melhorar Custos Fixos

---

## 🎨 Referências de Design

### Cores (Padrão JSP)
```
Verde Principal:    #28a745
Verde Hover:        #218838
Azul Info:          #17a2b8
Amarelo Warning:    #ffc107
Vermelho Danger:    #dc3545
Cinza Neutro:       #6c757d
```

### Status Colors
```
APROVADO:           🟢 #28a745 (verde)
REPROVADO:          🔴 #dc3545 (vermelho)
EM ABERTO:          ⚪ #6c757d (cinza)
FINALIZADO:         🔵 #17a2b8 (azul)
```

### Ícones (Font Awesome)
```
Projeto:            📋 fa-clipboard
Cliente:            👤 fa-user
Dados Técnicos:     ⚡ fa-bolt
Dados Financeiros:  💰 fa-dollar-sign
Orçamento:          💵 fa-money-bill-wave
Financiamento:      🏦 fa-university
Gerar Documento:    📄 fa-file-word
Tabela/Gráfico:     📊 fa-chart-bar
Configurações:      ⚙️ fa-cog
```

---

## 📁 Estrutura de Arquivos

```
app/
├── energia_solar/
│   ├── energia_solar_model.py (atualizar campos)
│   ├── energia_solar_routes.py (novas rotas)
│   ├── utils/
│   │   ├── calculadora_economia.py
│   │   ├── calculadora_roi.py
│   │   ├── document_generator.py
│   │   └── financiamento_calculator.py
│   └── templates/energia_solar/
│       ├── projetos_list.html (redesenhar)
│       ├── projeto_dashboard.html (novo)
│       ├── projeto_form_modal.html (novo)
│       ├── dados_tecnicos_modal.html (4 abas)
│       ├── dados_financeiros_modal.html (novo)
│       ├── orcamento_modal.html (novo)
│       ├── custo_item_modal.html (novo)
│       ├── financiamento_modal.html (novo)
│       ├── projeto_toolbar.html (novo)
│       ├── trocar_projeto_modal.html (novo)
│       ├── gerar_documento_modal.html (novo)
│       ├── tabela_12_meses.html (novo)
│       ├── tabela_25_anos.html (novo)
│       ├── config_marco_legal.html (novo)
│       ├── config_chaves_documentos.html (novo)
│       └── config_custos_fixos.html (melhorar)
│
├── concessionaria/ (novo módulo)
│   ├── __init__.py
│   ├── concessionaria_model.py
│   ├── concessionaria_routes.py
│   └── templates/concessionaria/
│       ├── concessionarias_list.html
│       └── concessionaria_form.html
│
└── models/ (novos models compartilhados)
    ├── orcamento_item.py
    ├── projeto_financiamento.py
    ├── marco_legal_taxacao.py
    ├── custos_fixos_template.py
    └── chaves_documentos.py
```

---

## 🛠️ Tecnologias e Bibliotecas

### Backend
- **Flask** - Framework web
- **SQLAlchemy** - ORM
- **PostgreSQL** - Database
- **python-docx** - Geração de documentos Word
- **openpyxl** - Exportação Excel
- **ReportLab / WeasyPrint** - Geração PDF

### Frontend
- **Bootstrap 5** - UI Framework
- **Font Awesome** - Ícones
- **Chart.js** - Gráficos
- **DataTables** - Tabelas interativas
- **SweetAlert2** - Modais bonitos
- **Select2** - Selects com busca

### Úteis
- **python-dateutil** - Manipulação de datas
- **Jinja2** - Template engine
- **WTForms** - Formulários

---

## 📝 Notas de Implementação

### Migration Strategy
1. **Fase 1 - Database:**
   - Criar novas tabelas
   - Adicionar campos em energia_solar_projeto
   - Popular marco_legal_taxacao com dados padrão
   - Popular chaves_documentos

2. **Fase 2 - Backend:**
   - Módulo Concessionárias completo
   - Novas rotas de projeto
   - Utilitários de cálculo
   - Document generator

3. **Fase 3 - Frontend:**
   - Dashboard
   - Modais
   - Ferramentas
   - Configurações

4. **Fase 4 - Integration:**
   - Testes end-to-end
   - Ajustes finais
   - Documentação

### Backward Compatibility
- Manter wizard atual funcionando
- Migrar projetos antigos gradualmente
- Flag `usa_novo_layout` em projeto

### Performance
- Índices em foreign keys
- Cache de cálculos pesados (Tabelas 12/25 anos)
- Lazy loading de dados técnicos

### Security
- Validar todos inputs
- Sanitizar variáveis de documentos
- Proteger rotas sensíveis
- CSRF protection em formulários

---

## ✅ Checklist de Conclusão

### Database
- [ ] Criar tabela `concessionarias`
- [ ] Criar tabela `orcamento_itens`
- [ ] Criar tabela `projeto_financiamento`
- [ ] Criar tabela `marco_legal_taxacao`
- [ ] Criar tabela `custos_fixos_template`
- [ ] Criar tabela `chaves_documentos`
- [ ] Adicionar campos em `energia_solar_projeto`
- [ ] Popular dados padrão (marco legal, chaves)

### Backend - Módulos
- [ ] Concessionárias CRUD completo
- [ ] Rotas de projeto (criar, editar, duplicar)
- [ ] Rotas de orçamento (CRUD itens)
- [ ] Rotas de financiamento
- [ ] Rotas de ferramentas (tabelas, documentos)
- [ ] Rotas de configurações

### Backend - Utilities
- [ ] Calculadora de economia (3 cenários)
- [ ] Calculadora de ROI (25 anos)
- [ ] Gerador de documentos Word
- [ ] Calculadora Price (financiamento)
- [ ] Sistema de merge fields

### Frontend - Core
- [ ] Listagem redesenhada
- [ ] Dashboard do projeto
- [ ] Modal criação/edição projeto
- [ ] Modal dados técnicos (4 abas)
- [ ] Modal dados financeiros
- [ ] Modal editar orçamento
- [ ] Modal editar custo
- [ ] Modal financiamento

### Frontend - Ferramentas
- [ ] Barra de ferramentas
- [ ] Modal trocar projeto
- [ ] Modal gerar documento
- [ ] Tela tabela 12 meses
- [ ] Tela tabela 25 anos

### Frontend - Configurações
- [ ] Tela marco legal
- [ ] Tela chaves documentos
- [ ] Tela custos fixos melhorada

### Testing
- [ ] Testes de rotas
- [ ] Testes de cálculos
- [ ] Testes de geração de documentos
- [ ] Testes end-to-end

### Documentation
- [ ] README atualizado
- [ ] API docs (se houver)
- [ ] Manual do usuário
- [ ] Vídeo tutorial (opcional)

---

## 🚀 Próximos Passos Imediatos

1. **Criar script de migration do banco:**
   ```bash
   python scripts/migrate_energia_solar_v3.py
   ```

2. **Implementar Módulo Concessionárias primeiro:**
   - É base para Dados Financeiros
   - Independente de outras mudanças
   - Pode ser testado isoladamente

3. **Adicionar campos novos em energia_solar_projeto:**
   - Preparar modelo para novos dados
   - Manter compatibilidade com wizard atual

4. **Criar Dashboard básico:**
   - Primeira impressão visual
   - Motivador para continuar
   - Demonstra valor da mudança

5. **Implementar Modal Dados Financeiros:**
   - Integra com Concessionárias
   - Funcionalidade de alto valor
   - Diferencial competitivo

---

**Documento vivo - atualizar conforme implementação avança!**

**Última atualização:** 08/01/2026
