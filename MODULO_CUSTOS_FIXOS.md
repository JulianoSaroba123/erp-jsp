# 📊 Módulo de Custos Fixos - ERP JSP v3.0

## 📋 Visão Geral

O módulo de **Custos Fixos** permite gerenciar despesas e receitas recorrentes mensais, com geração automática de lançamentos financeiros. Ideal para controlar aluguéis, salários, assinaturas, serviços e outros custos que se repetem mensalmente.

---

## ✅ Status de Implementação

**Status**: ✅ **COMPLETO E FUNCIONAL**

**Data**: Janeiro 2025  
**Versão**: 1.0.0

### Componentes Implementados

- ✅ Model `CustoFixo` com 14 campos e métodos avançados
- ✅ 7 rotas Flask (CRUD + dashboard + geração automática)
- ✅ 3 templates Bootstrap 5 (listar, form, dashboard)
- ✅ Integração com Contas Bancárias e Centros de Custo
- ✅ Geração automática de lançamentos mensais
- ✅ Dashboard com gráficos e indicadores
- ✅ Menu de navegação atualizado
- ✅ Script SQL para deploy no Render

---

## 🎯 Funcionalidades

### 1. CRUD Completo
- **Listar** custos fixos com filtros (categoria, status)
- **Criar** novo custo fixo com validação
- **Editar** custos existentes
- **Excluir** (soft delete) custos fixos

### 2. Geração Automática
- Sistema inteligente que gera lançamentos mensais automaticamente
- Respeita data de início e fim do custo
- Controla último mês gerado para evitar duplicatas
- Ajusta dia de vencimento para meses com menos dias

### 3. Dashboard Analítico
- **Cards de Resumo**: Total mensal, anual, custos ativos
- **Gráfico Pizza**: Distribuição por categoria (Chart.js)
- **Próximos Vencimentos**: Alertas de vencimentos em 30 dias
- **Tabela Detalhada**: Todos os custos com informações completas

### 4. Integrações
- **Conta Bancária**: Vincula custo a uma conta específica
- **Centro de Custo**: Associa a departamento/projeto
- **Lançamentos**: Cria automaticamente em `lancamentos_financeiros`

---

## 📁 Estrutura de Arquivos

```
app/
├── financeiro/
│   ├── financeiro_model.py        # Model CustoFixo (linhas 650-800)
│   ├── financeiro_routes.py       # 7 rotas (linhas 1465-1685)
│   └── templates/financeiro/
│       └── custos_fixos/
│           ├── listar.html        # Lista com filtros e resumo
│           ├── form.html          # Formulário create/edit
│           └── dashboard.html     # Dashboard com gráficos
│
├── templates/
│   └── base.html                  # Menu atualizado (linha 270)
│
└── app.py                         # Import CustoFixo (linha 134)

scripts/
└── criar_tabela_custos_fixos.sql  # SQL para Render
```

---

## 🗄️ Estrutura do Banco de Dados

### Tabela: `custos_fixos`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | SERIAL | Chave primária |
| `nome` | VARCHAR(100) | Nome do custo (ex: "Aluguel do Galpão") |
| `descricao` | TEXT | Descrição detalhada (opcional) |
| `valor_mensal` | NUMERIC(10,2) | Valor mensal do custo |
| `categoria` | VARCHAR(50) | Categoria (Aluguel, Salários, etc) |
| `tipo` | VARCHAR(20) | DESPESA ou RECEITA |
| `dia_vencimento` | INTEGER | Dia do mês (1-31) |
| `gerar_automaticamente` | BOOLEAN | Se deve gerar lançamento auto |
| `data_inicio` | DATE | Data de início da vigência |
| `data_fim` | DATE | Data de fim (NULL = indeterminado) |
| `conta_bancaria_id` | INTEGER | FK para contas_bancarias |
| `centro_custo_id` | INTEGER | FK para centros_custo |
| `ativo` | BOOLEAN | Se está ativo |
| `ultimo_mes_gerado` | VARCHAR(7) | Último mês gerado (YYYY-MM) |
| `criado_em` | TIMESTAMP | Data de criação |
| `atualizado_em` | TIMESTAMP | Data de atualização |

### Índices Criados
- `idx_custos_fixos_ativo` - Filtro por status
- `idx_custos_fixos_categoria` - Filtro por categoria
- `idx_custos_fixos_conta` - Join com contas
- `idx_custos_fixos_centro` - Join com centros
- `idx_custos_fixos_vencimento` - Ordenação por dia

---

## 🛣️ Rotas Implementadas

### Visualização
```python
GET  /financeiro/custos-fixos                    # Lista todos
GET  /financeiro/custos-fixos/dashboard          # Dashboard analítico
```

### CRUD
```python
GET  /financeiro/custos-fixos/novo               # Formulário criar
POST /financeiro/custos-fixos/novo               # Salvar novo

GET  /financeiro/custos-fixos/<id>/editar        # Formulário editar
POST /financeiro/custos-fixos/<id>/editar        # Salvar edição

POST /financeiro/custos-fixos/<id>/excluir       # Soft delete
```

### Automação
```python
POST /financeiro/custos-fixos/gerar-lancamentos  # Gerar lançamentos do mês
```

---

## 🧩 Model: Métodos e Properties

### Properties
```python
@property
def valor_formatado(self):
    """Retorna: 'R$ 1.500,00'"""

@property
def proximo_vencimento(self):
    """Calcula próxima data de vencimento (date object)"""
```

### Métodos de Instância
```python
def gerar_lancamento_mes(self, ano, mes):
    """
    Gera lançamento para mês específico.
    
    Returns:
        LancamentoFinanceiro ou None (se já foi gerado)
    """
```

### Métodos de Classe
```python
@classmethod
def get_custos_ativos(cls):
    """
    Retorna custos ativos considerando data_inicio e data_fim.
    
    Returns:
        List[CustoFixo]
    """

@classmethod
def get_total_mensal(cls):
    """
    Calcula soma de todos os valores mensais ativos.
    
    Returns:
        Decimal
    """

@classmethod
def gerar_lancamentos_automaticos(cls):
    """
    Gera lançamentos para TODOS os custos com flag ativa.
    
    Returns:
        List[LancamentoFinanceiro]
    """
```

---

## 💡 Exemplos de Uso

### 1. Criar Custo Fixo de Aluguel
```python
from app.financeiro.financeiro_model import CustoFixo
from datetime import date

custo = CustoFixo(
    nome="Aluguel do Escritório",
    descricao="Aluguel mensal do escritório na Av. Paulista",
    valor_mensal=5000.00,
    categoria="Aluguel",
    tipo="DESPESA",
    dia_vencimento=10,  # Todo dia 10
    gerar_automaticamente=True,
    data_inicio=date(2025, 1, 1),
    data_fim=date(2025, 12, 31),  # Contrato de 1 ano
    conta_bancaria_id=1,
    centro_custo_id=2,
    ativo=True
)

db.session.add(custo)
db.session.commit()
```

### 2. Gerar Lançamento Manual
```python
# Gerar para fevereiro/2025
lancamento = custo.gerar_lancamento_mes(2025, 2)

print(lancamento.descricao)  # "Aluguel do Escritório - 2025-02"
print(lancamento.data_vencimento)  # 2025-02-10
```

### 3. Gerar Todos os Lançamentos do Mês
```python
# No início de cada mês, executar:
lancamentos = CustoFixo.gerar_lancamentos_automaticos()

print(f"{len(lancamentos)} lançamentos gerados!")
```

### 4. Consultar Custos Ativos
```python
custos = CustoFixo.get_custos_ativos()
total = CustoFixo.get_total_mensal()

print(f"Total mensal: R$ {total:,.2f}")
```

---

## 🎨 Interface do Usuário

### Página: Listar Custos Fixos
- **Cards de Resumo**: Total mensal, custos ativos, total anual
- **Filtros**: Categoria, Status (Ativo/Inativo/Todos)
- **Tabela**: 
  - Nome e descrição
  - Categoria (badge)
  - Valor formatado (vermelho=despesa, verde=receita)
  - Dia de vencimento
  - Próximo vencimento com alertas coloridos
  - Conta bancária e centro de custo
  - Ícone de auto-geração
  - Status (badge)
  - Botões de ação (editar/excluir)

### Página: Formulário
- **Campos Obrigatórios**: Nome, Tipo, Valor, Categoria, Dia Vencimento, Data Início
- **Campos Opcionais**: Descrição, Data Fim, Conta, Centro
- **Checkbox**: Gerar automaticamente
- **Ajuda**: Card explicativo sobre funcionamento
- **Validações**: JavaScript para formatação de moeda

### Página: Dashboard
- **4 Cards**: Total mensal, anual, custos ativos, próximos vencimentos
- **Gráfico Pizza**: Chart.js mostrando distribuição por categoria
- **Lista de Vencimentos**: Próximos 30 dias com badges coloridos
- **Botão**: "Gerar Lançamentos do Mês" (com confirmação)
- **Tabela Completa**: Todos os custos ordenados por vencimento

---

## 🚀 Deploy no Render

### 1. Executar Script SQL
```bash
# No console PostgreSQL do Render:
\i criar_tabela_custos_fixos.sql
```

### 2. Verificar Criação
```sql
SELECT COUNT(*) FROM custos_fixos;
```

### 3. Adicionar Coluna em Lançamentos (se necessário)
```sql
ALTER TABLE lancamentos_financeiros 
ADD COLUMN IF NOT EXISTS origem VARCHAR(20);
```

---

## 🔄 Automação com Cron Jobs

Para produção, configure um cron job para executar todo dia 1º:

```bash
# crontab -e
0 9 1 * * curl -X POST https://seu-erp.onrender.com/financeiro/custos-fixos/gerar-lancamentos
```

Ou use o Render Cron Jobs:
```yaml
# render.yaml
services:
  - type: cron
    name: gerar-custos-fixos
    schedule: "0 9 1 * *"  # Todo dia 1 às 9h
    command: python -c "from app.financeiro.financeiro_model import CustoFixo; CustoFixo.gerar_lancamentos_automaticos()"
```

---

## 📊 Categorias Padrão

O sistema sugere 14 categorias:
1. Aluguel
2. Salários
3. Encargos
4. Energia
5. Água
6. Internet
7. Telefone
8. Software
9. Manutenção
10. Seguros
11. Impostos
12. Contabilidade
13. Marketing
14. Outros

---

## 🐛 Troubleshooting

### Erro: "Tabela custos_fixos não existe"
**Solução**: Execute `criar_tabela_custos_fixos.sql` no Render

### Erro: "Coluna origem não existe"
**Solução**: 
```sql
ALTER TABLE lancamentos_financeiros ADD COLUMN origem VARCHAR(20);
```

### Lançamentos duplicados
**Causa**: Campo `ultimo_mes_gerado` não está sendo atualizado  
**Solução**: Verificar commit do lançamento no método `gerar_lancamento_mes()`

### Dia 31 em fevereiro
**Comportamento**: Sistema ajusta automaticamente para dia 28/29  
**Código**: `monthrange(ano, mes)[1]` limita ao último dia do mês

---

## 🎯 Próximas Melhorias (Roadmap)

### Fase 2 (Futuro)
- [ ] Múltiplas parcelas (ex: salário quinzenal)
- [ ] Custos variáveis (% sobre faturamento)
- [ ] Reajuste automático (IPCA, IGP-M)
- [ ] Notificações por email de vencimentos
- [ ] API REST para integração externa
- [ ] Histórico de alterações de valores
- [ ] Previsão de fluxo de caixa (12 meses)
- [ ] Comparativo mês a mês

---

## 📞 Suporte

**Desenvolvedor**: JSP Soluções  
**Módulo**: Financeiro - Custos Fixos  
**Versão**: 1.0.0  
**Data**: Janeiro 2025

---

## 📝 Changelog

### v1.0.0 - Janeiro 2025
- ✅ Implementação inicial completa
- ✅ Model com 14 campos + 5 métodos
- ✅ 7 rotas Flask
- ✅ 3 templates responsivos
- ✅ Dashboard com Chart.js
- ✅ Integração com Contas e Centros
- ✅ Geração automática de lançamentos
- ✅ Script SQL para Render
- ✅ Documentação completa
