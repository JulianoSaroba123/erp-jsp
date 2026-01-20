# 📋 Backlog - Módulo Financeiro

## ✅ Já Implementado

### 1. Contas Bancárias ✅
- [x] CRUD completo (criar, listar, editar, excluir)
- [x] Dashboard com saldos e projeções
- [x] Transferências entre contas
- [x] Atualização automática de saldos
- [x] Validações de saldo

### 2. Centros de Custo ✅
- [x] CRUD completo com hierarquia
- [x] Controle de orçamento
- [x] Relatórios por período
- [x] Integração com lançamentos
- [x] Percentual de uso do orçamento

### 3. Conciliação Bancária ✅
- [x] Upload de extratos CSV
- [x] Parser inteligente
- [x] Interface de conciliação lado a lado
- [x] Conciliação manual
- [x] Histórico de conciliações
- [x] Desfazer conciliações

### 4. Custos Fixos ✅ **NOVO!**
- [x] CRUD completo (criar, listar, editar, excluir)
- [x] Geração automática de lançamentos mensais
- [x] Dashboard analítico com Chart.js
- [x] Próximos vencimentos com alertas
- [x] Integração com Contas e Centros
- [x] Controle de data início/fim
- [x] Categorização flexível
- [x] Totais mensais e anuais
- [x] Filtros por categoria e status

**Documentação**: `MODULO_CUSTOS_FIXOS.md`  
**Arquivos**: 
- Model: `app/financeiro/financeiro_model.py` (classe CustoFixo)
- Rotas: `app/financeiro/financeiro_routes.py` (7 rotas)
- Templates: `app/financeiro/templates/financeiro/custos_fixos/` (3 arquivos)
- SQL: `scripts/criar_tabela_custos_fixos.sql`

---

## 🔴 MUST HAVE - Prioridade Máxima

### 5. Fluxo de Caixa Projetado ✅ **NOVO!**
**Descrição**: Projeção de entradas e saídas futuras para planejamento financeiro.

**Funcionalidades**:
- [x] Visualização gráfica (receitas vs despesas)
- [x] Projeção para 30, 60, 90 dias
- [x] Inclusão de lançamentos recorrentes
- [x] Saldo projetado por período
- [x] Alertas de saldo negativo futuro
- [x] Filtro por conta bancária
- [x] Exportar para Excel

**Documentação**: `MODULO_FLUXO_CAIXA.md`  
**Arquivos**: 
- Rotas: `app/financeiro/financeiro_routes.py` (2 rotas)
- Template: `app/financeiro/templates/financeiro/fluxo_caixa/dashboard.html`
- Gráficos: Chart.js (linha + barras)

**Complexidade**: Média  
**Impacto**: Alto  
**Tempo Estimado**: 4-6 horas ✅ CONCLUÍDO

---

### 6. DRE - Demonstrativo de Resultados do Exercício ❌
**Descrição**: Relatório contábil estruturado de receitas, despesas e resultado líquido.
---

### 6. DRE - Demonstrativo de Resultados do Exercício ✅ **NOVO!**
**Descrição**: Relatório contábil estruturado de receitas, despesas e resultado líquido.

**Funcionalidades**:
- [x] Estrutura DRE padrão (Receita Bruta, Deduções, Receita Líquida, Custos, Despesas Operacionais, Resultado)
- [x] Comparação mensal/anual
- [x] Análise vertical (percentuais)
- [x] Análise horizontal (evolução)
- [x] Gráficos de evolução
- [x] Filtro por período customizado
- [x] Exportar para Excel

**Documentação**: `MODULO_DRE.md`  
**Arquivos**: 
- Rotas: `app/financeiro/financeiro_routes.py` (função calcular_dre + 2 rotas)
- Template: `app/financeiro/templates/financeiro/dre/dashboard.html`
- Gráficos: Chart.js (evolução mensal)

**Complexidade**: Alta  
**Impacto**: Alto  
**Tempo Estimado**: 6-8 horas ✅ CONCLUÍDO

---

## 🟡 SHOULD HAVE - Alta Prioridade

### 7. Plano de Contas (Interface) ❌
**Descrição**: CRUD completo para gerenciamento do plano de contas contábil.

**Funcionalidades**:
- [ ] CRUD completo (tabela já existe)
- [ ] Hierarquia de contas (pai/filho)
- [ ] Classificação contábil (ativo, passivo, receita, despesa)
- [ ] Código da conta (ex: 1.1.01.001)
- [ ] Ativar/desativar contas
- [ ] Vincular lançamentos a contas
- [ ] Relatório de balancete

**Tabela Existente**: `plano_contas` ✅  
**Complexidade**: Média  
**Impacto**: Alto  
**Tempo Estimado**: 4-5 horas

---

### 8. Orçamento Anual ❌
**Descrição**: Planejamento financeiro por categorias e períodos.

**Funcionalidades**:
- [ ] Definir orçamento mensal por categoria
- [ ] Comparação realizado vs orçado
- [ ] Percentual de execução
- [ ] Alertas de estouro de orçamento
- [ ] Revisões de orçamento
- [ ] Histórico de orçamentos
- [ ] Dashboard visual

**Complexidade**: Média
**Impacto**: Médio  
**Tempo Estimado**: 5-6 horas

---

### 8. Gestão de Notas Fiscais ❌
**Descrição**: Upload, armazenamento e vinculação de NFs com lançamentos.

**Funcionalidades**:
- [ ] Upload de arquivos (PDF, XML)
- [ ] Leitura de XML de NF-e
- [ ] Vinculação automática com lançamentos
- [ ] Galeria de anexos
- [ ] Download de NFs
- [ ] Validação de CNPJ/valores
- [ ] Status (pendente, processada, paga)

**Complexidade**: Alta  
**Impacto**: Alto  
**Tempo Estimado**: 6-8 horas

---

## 🟢 COULD HAVE - Desejável

### 9. Análise de Rentabilidade ❌
**Descrição**: Análise de lucro/margem por projeto, cliente ou produto.

**Funcionalidades**:
- [ ] Rentabilidade por projeto solar
- [ ] Rentabilidade por cliente
- [ ] Margem bruta e líquida
- [ ] Custos diretos e indiretos
- [ ] Comparação entre projetos
- [ ] Gráficos de rentabilidade
- [ ] Ranking de projetos mais lucrativos

**Complexidade**: Alta  
**Impacto**: Médio  
**Tempo Estimado**: 8-10 horas

---

### 10. Dashboard Executivo ❌
**Descrição**: Painel com KPIs e métricas avançadas para gestores.

**Funcionalidades**:
- [ ] KPIs principais (faturamento, margem, inadimplência)
- [ ] Gráficos interativos (Chart.js)
- [ ] Comparação com meses anteriores
- [ ] Metas vs realizado
- [ ] Top 5 clientes/fornecedores
- [ ] Previsão de recebimentos
- [ ] Alertas e notificações

**Complexidade**: Alta  
**Impacto**: Médio  
**Tempo Estimado**: 8-10 horas

---

### 11. Conciliação Bancária Automática ❌
**Descrição**: Matching automático de extratos com lançamentos usando ML/regras.

**Funcionalidades**:
- [ ] Matching por valor exato + data ±3 dias
- [ ] Matching por descrição (fuzzy matching)
- [ ] Sugestões inteligentes
- [ ] Aprendizado com histórico
- [ ] Regras customizáveis
- [ ] Conciliação em lote
- [ ] Taxa de acerto

**Complexidade**: Muito Alta  
**Impacto**: Alto  
**Tempo Estimado**: 12-15 horas

---

### 12. API de Integração Bancária ❌
**Descrição**: Integração com Open Banking para sincronização automática.

**Funcionalidades**:
- [ ] Integração com Pluggy/Belvo
- [ ] Sincronização automática de extratos
- [ ] Webhook para novos lançamentos
- [ ] Atualização de saldos em tempo real
- [ ] Suporte a múltiplos bancos
- [ ] Histórico de sincronizações
- [ ] Logs e auditoria

**Complexidade**: Muito Alta  
**Impacto**: Muito Alto  
**Tempo Estimado**: 20-25 horas

---

## 🔵 WON'T HAVE - Baixa Prioridade (Futuro)

### 13. Gestão de Impostos ❌
- [ ] Cálculo automático de impostos
- [ ] DARF, DAS, guias
- [ ] Regime tributário
- [ ] Obrigações acessórias

### 14. Múltiplas Moedas ❌
- [ ] Suporte a USD, EUR
- [ ] Conversão automática
- [ ] Cotações diárias

### 15. Auditoria Completa ❌
- [ ] Log de todas as ações
- [ ] Rastreabilidade total
- [ ] Relatório de auditoria
- [ ] Compliance

---

## 📊 Resumo do Backlog

| Prioridade | Funcionalidade | Status | Complexidade | Impacto |
|------------|---------------|--------|--------------|---------|
| ✅ DONE | Contas Bancárias | Completo | Média | Alto |
| ✅ DONE | Centros de Custo | Completo | Média | Médio |
| ✅ DONE | Conciliação Bancária Manual | Completo | Média | Alto |
| 🔴 MUST | Fluxo de Caixa Projetado | Pendente | Média | Alto |
| 🔴 MUST | DRE | Pendente | Alta | Alto |
| 🟡 SHOULD | Plano de Contas (UI) | Pendente | Média | Alto |
| 🟡 SHOULD | Orçamento Anual | Pendente | Média | Médio |
| 🟡 SHOULD | Gestão de Notas Fiscais | Pendente | Alta | Alto |
| 🟢 COULD | Análise de Rentabilidade | Pendente | Alta | Médio |
| 🟢 COULD | Dashboard Executivo | Pendente | Alta | Médio |
| 🟢 COULD | Conciliação Automática | Pendente | Muito Alta | Alto |
| 🟢 COULD | API Open Banking | Pendente | Muito Alta | Muito Alto |

---

## 🎯 Roadmap Sugerido

### Sprint 1 (Atual) ✅
- [x] Contas Bancárias
- [x] Centros de Custo
- [x] Conciliação Bancária Manual

### Sprint 2 (Próxima)
- [ ] Fluxo de Caixa Projetado
- [ ] DRE

### Sprint 3
- [ ] Plano de Contas (Interface)
- [ ] Orçamento Anual

### Sprint 4
- [ ] Gestão de Notas Fiscais
- [ ] Dashboard Executivo

### Sprint 5
- [ ] Análise de Rentabilidade
- [ ] Conciliação Automática

### Sprint 6 (Futuro)
- [ ] API Open Banking
- [ ] Gestão de Impostos

---

## 📝 Notas Importantes

### Melhorias Técnicas Pendentes:
- [ ] Testes automatizados (unittest/pytest)
- [ ] Validações de formulário no front-end (JavaScript)
- [ ] Cache de queries pesadas
- [ ] Paginação em listas grandes
- [ ] Exportação em múltiplos formatos
- [ ] Logs de auditoria
- [ ] Permissões por perfil de usuário

### Otimizações de Performance:
- [ ] Índices no banco de dados
- [ ] Lazy loading de relacionamentos
- [ ] Queries otimizadas (evitar N+1)
- [ ] Cache Redis para dashboards

### UX/UI:
- [ ] Loading spinners
- [ ] Confirmações de ações críticas
- [ ] Mensagens de sucesso/erro mais claras
- [ ] Atalhos de teclado
- [ ] Responsividade mobile

---

**Última atualização**: 19/01/2026  
**Versão**: 1.0  
**Responsável**: JSP Soluções
