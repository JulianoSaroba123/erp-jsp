# 🏦 Módulo de Conciliação Bancária - ERP JSP v3.0

## 📋 Visão Geral

O módulo de Conciliação Bancária permite importar extratos bancários em formato CSV e conciliá-los manualmente com os lançamentos financeiros registrados no sistema. Este processo garante que os registros internos estejam alinhados com as movimentações reais da conta bancária.

## ✨ Funcionalidades

### 1. **Importação de Extratos (CSV)**
- Upload de arquivos CSV exportados do banco
- Validação automática de formato
- Tratamento de erros (linhas inválidas são ignoradas)
- Suporte para múltiplos bancos

### 2. **Visualização Lado a Lado**
- **Coluna Esquerda**: Extratos bancários pendentes de conciliação
- **Coluna Direita**: Lançamentos do sistema não conciliados
- Interface drag-and-drop visual
- Filtro por conta bancária

### 3. **Conciliação Manual**
- Seleção de extrato bancário
- Vinculação com lançamento do sistema
- Validação de valores e tipos
- Confirmação antes de conciliar

### 4. **Histórico Completo**
- Listagem de todas as conciliações realizadas
- Filtro por conta bancária
- Estatísticas (créditos, débitos, total)
- Possibilidade de desfazer conciliação

### 5. **Dashboard de Controle**
- Saldo em sistema vs saldo bancário
- Quantidade de extratos pendentes
- Quantidade de lançamentos não conciliados
- Indicadores visuais de status

## 🗄️ Estrutura do Banco de Dados

### Tabela: `extratos_bancarios`

```sql
CREATE TABLE extratos_bancarios (
    id INTEGER PRIMARY KEY,
    conta_bancaria_id INTEGER NOT NULL,
    data_movimento DATE NOT NULL,
    descricao VARCHAR(255) NOT NULL,
    documento VARCHAR(50),
    valor NUMERIC(12, 2) NOT NULL,
    tipo_movimento VARCHAR(10) NOT NULL,  -- 'credito' ou 'debito'
    saldo NUMERIC(12, 2),
    conciliado BOOLEAN DEFAULT FALSE,
    data_conciliacao DATETIME,
    lancamento_id INTEGER,  -- FK para lancamentos_financeiros
    arquivo_origem VARCHAR(255),
    data_importacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    observacoes TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao DATETIME,
    
    FOREIGN KEY (conta_bancaria_id) REFERENCES contas_bancarias(id),
    FOREIGN KEY (lancamento_id) REFERENCES lancamentos_financeiros(id)
);
```

## 📂 Formato do Arquivo CSV

### Colunas Obrigatórias

| Coluna | Tipo | Formato | Descrição | Exemplo |
|--------|------|---------|-----------|---------|
| `data` | Data | DD/MM/YYYY | Data do movimento | 15/01/2025 |
| `descricao` | Texto | String | Descrição do lançamento | Pagamento Fornecedor ABC |
| `valor` | Decimal | 9999.99 | Valor do movimento | 1500.00 |
| `tipo` | Texto | credito/debito | Tipo de movimento | credito |

### Colunas Opcionais

| Coluna | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| `documento` | Texto | Número do documento | DOC123, TED456 |
| `saldo` | Decimal | Saldo após movimento | 5000.00 |

### Exemplo de CSV

```csv
data,descricao,documento,valor,tipo
01/01/2025,Pagamento Fornecedor ABC,DOC123,1500.00,debito
02/01/2025,Recebimento Cliente XYZ,TED456,3250.50,credito
03/01/2025,TED Recebida,TED789,5000.00,credito
```

## 🔗 Rotas Implementadas

### 1. `GET /financeiro/conciliacao-bancaria`
**Descrição**: Página principal de conciliação  
**Parâmetros**: `?conta_id=<id>` (opcional)  
**Retorna**: Interface de conciliação lado a lado

### 2. `GET/POST /financeiro/conciliacao-bancaria/upload`
**Descrição**: Upload e processamento de CSV  
**Method POST**:
- `conta_bancaria_id`: ID da conta (required)
- `arquivo`: Arquivo CSV (required)  
**Retorna**: Redireciona para conciliação com mensagem de sucesso/erro

### 3. `POST /financeiro/conciliacao-bancaria/conciliar/<extrato_id>/<lancamento_id>`
**Descrição**: Conciliar manualmente extrato com lançamento  
**Parâmetros**:
- `extrato_id`: ID do extrato bancário
- `lancamento_id`: ID do lançamento financeiro  
**Retorna**: Redireciona com confirmação

### 4. `POST /financeiro/conciliacao-bancaria/desconciliar/<extrato_id>`
**Descrição**: Desfazer conciliação  
**Parâmetros**: `extrato_id` - ID do extrato  
**Retorna**: Redireciona com confirmação

### 5. `GET /financeiro/conciliacao-bancaria/historico`
**Descrição**: Histórico de conciliações  
**Parâmetros**: `?conta_id=<id>` (opcional)  
**Retorna**: Lista de extratos conciliados

## 📁 Arquivos Criados

### Models
- ✅ `app/financeiro/financeiro_model.py` - Classe `ExtratoBancario` adicionada

### Routes
- ✅ `app/financeiro/financeiro_routes.py` - 5 novas rotas adicionadas

### Templates
- ✅ `app/financeiro/templates/financeiro/conciliacao_bancaria/conciliacao.html`
- ✅ `app/financeiro/templates/financeiro/conciliacao_bancaria/upload.html`
- ✅ `app/financeiro/templates/financeiro/conciliacao_bancaria/historico.html`

### Navegação
- ✅ `app/templates/base.html` - Menu atualizado com link "Conciliação Bancária"

### Exemplos
- ✅ `exemplo_extrato_bancario.csv` - Arquivo de exemplo para testes

## 🎨 Interface do Usuário

### Cores e Ícones
- **Verde** (`bg-success`): Lançamentos do sistema
- **Amarelo** (`bg-warning`): Extratos pendentes
- **Azul** (`bg-info`): Botão de seleção
- **Cinza** (`bg-secondary`): Informações complementares

### Ícones FontAwesome
- 🤝 `fa-handshake`: Conciliação Bancária
- 📤 `fa-upload`: Importar Extrato
- 🏦 `fa-file-invoice-dollar`: Extratos
- 📄 `fa-file-alt`: Lançamentos
- 🔗 `fa-link`: Conciliar
- 🔓 `fa-unlink`: Desconciliar
- 📊 `fa-history`: Histórico

## 🔧 Fluxo de Trabalho

### 1. **Importar Extrato**
1. Acesse: **Financeiro → Conciliação Bancária → Importar Extrato**
2. Selecione a **Conta Bancária**
3. Faça upload do arquivo **CSV**
4. Clique em **Importar Extrato**

### 2. **Conciliar Lançamentos**
1. Acesse: **Financeiro → Conciliação Bancária**
2. Selecione a **Conta Bancária**
3. Clique em um **extrato bancário** (coluna esquerda)
4. Clique no botão **🔗** do lançamento correspondente (coluna direita)
5. Confirme a conciliação

### 3. **Visualizar Histórico**
1. Acesse: **Financeiro → Conciliação Bancária → Histórico**
2. Filtre por conta (opcional)
3. Visualize todas as conciliações realizadas
4. **Desfazer** conciliação se necessário

## ⚠️ Validações e Regras

### Importação CSV
- ✅ Arquivo deve ser `.csv`
- ✅ Colunas obrigatórias: `data`, `descricao`, `valor`, `tipo`
- ✅ Data no formato `DD/MM/YYYY`
- ✅ Tipo deve ser `credito` ou `debito`
- ✅ Valor numérico (aceita separador decimal ponto ou vírgula)
- ⚠️ Linhas com erro são ignoradas (não bloqueiam importação)

### Conciliação
- ✅ Extrato não pode estar conciliado
- ✅ Lançamento não pode estar vinculado a outro extrato
- ✅ Valores não precisam ser idênticos (permite diferenças de tarifas)
- ✅ Tipos devem ser compatíveis (receita com crédito, despesa com débito)

### Desconciliação
- ✅ Apenas extratos já conciliados podem ser desconciliados
- ✅ Lançamento original não é excluído, apenas desvinculado
- ✅ Extrato volta para status "Pendente"

## 🧪 Testes

### Dados de Teste
Use o arquivo `exemplo_extrato_bancario.csv` incluído na raiz do projeto.

### Cenários de Teste

#### 1. **Importação Bem-Sucedida**
- Upload do CSV de exemplo
- Verificar 8 extratos importados
- Verificar mensagem de sucesso

#### 2. **Conciliação Manual**
- Criar lançamento de despesa de R$ 1.500,00
- Importar extrato com débito de R$ 1.500,00
- Conciliar manualmente
- Verificar status "Conciliado"

#### 3. **Desfazer Conciliação**
- Acessar histórico
- Clicar em "Desfazer" em uma conciliação
- Verificar extrato volta a status "Pendente"

#### 4. **Filtros**
- Criar extratos em 2 contas diferentes
- Filtrar por conta
- Verificar apenas extratos da conta selecionada

## 📊 Próximas Melhorias (Backlog)

### SHOULD HAVE
- [ ] **Conciliação Automática**: Matching automático por valor + data ±3 dias
- [ ] **Sugestões Inteligentes**: ML para sugerir conciliações baseado em histórico
- [ ] **Múltiplos Formatos**: Suporte para OFX, QIF além de CSV
- [ ] **Parsing Inteligente**: Detecção automática de colunas CSV
- [ ] **Conciliação em Lote**: Conciliar múltiplos lançamentos de uma vez

### COULD HAVE
- [ ] **API de Integração**: Webhooks para bancos que oferecem API
- [ ] **Relatório de Divergências**: Identificar lançamentos órfãos
- [ ] **Exportação**: Exportar conciliações para Excel/PDF
- [ ] **Auditoria**: Log detalhado de quem conciliou e quando
- [ ] **Notificações**: Alertas de divergências via email

## 🐛 Troubleshooting

### Erro: "Nenhum arquivo selecionado"
**Solução**: Certifique-se de selecionar um arquivo antes de clicar em "Importar"

### Erro: "Arquivo com 0 lançamentos importados"
**Solução**: Verifique se o CSV está no formato correto (veja exemplo acima)

### Erro: "Data inválida"
**Solução**: Use formato DD/MM/YYYY (ex: 15/01/2025)

### Erro: "Tipo inválido"
**Solução**: Coluna `tipo` deve ser exatamente `credito` ou `debito` (minúsculas)

### Extrato não aparece na lista
**Solução**: Verifique se a conta bancária selecionada está correta

## 📖 Referências

- **Padrão JSP v3.0**: Segue arquitetura MVC do projeto
- **BaseModel**: Herda soft delete e timestamps
- **Bootstrap 5**: Framework CSS utilizado
- **FontAwesome 6**: Ícones utilizados

---

**Desenvolvido por**: JSP Soluções  
**Versão**: 1.0.0  
**Data**: Janeiro 2025  
**Status**: ✅ **IMPLEMENTADO E FUNCIONAL**
