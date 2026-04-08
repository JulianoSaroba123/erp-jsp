# 🔧 Correção: Contagem de Ordens Concluídas

## Problema Identificado

O dashboard mostra apenas **4 ordens concluídas** de um total de 55 porque:

1. **Status antigos no banco**: Ordens com status "aberta", "em_andamento", "Concluida" (antigos)
2. **Contagem filtrada por mês**: O código antigo mostrava apenas as concluídas **no mês atual** (abril/2026)

## Solução Aplicada

### 1. Método Estatísticas Atualizado
Arquivo: `app/ordem_servico/ordem_servico_model.py`

**Antes**: Contava apenas concluídas do mês atual  
**Depois**: Conta **TODAS** as ordens finalizadas

```python
# ANTES
concluidas_mes = cls.query.filter(..., data_conclusao == mes_atual).count()

# DEPOIS
concluidas_total = cls.query.filter(...).count()  # Sem filtro de mês
```

### 2. Script de Migração de Status
Arquivo: `migrar_status_ordens.py`

Converte status antigos para os padronizados:
- `aberta` / `Aberta` → `pendente`
- `em_andamento` / `Em Andamento` → `em_execucao`
- `concluida` / `Concluida` / `Concluída` / `fechada` → `finalizada`

## Como Aplicar no Render

### Opção 1: Via Git Deploy (RECOMENDADO)

```bash
# 1. Commitar as alterações
git add app/ordem_servico/ordem_servico_model.py migrar_status_ordens.py
git commit -m "fix: corrige contagem de ordens concluídas e migra status antigos"
git push origin main

# 2. Aguardar deploy automático do Render

# 3. Acessar Shell do Render e executar:
python migrar_status_ordens.py
```

### Opção 2: Via Shell do Render (Direto)

1. Acesse Render Dashboard
2. Vá em "Shell" no seu serviço
3. Execute:
```bash
python migrar_status_ordens.py
```

## O que a Migração Faz

1. **Mapeia status antigos**: Identifica todas as variações de status
2. **Atualiza no banco**: Converte para os status padronizados
3. **Corrige vazios**: Ordens sem status recebem "pendente"
4. **Mostra relatório**: Exibe quantas ordens foram atualizadas

## Resultado Esperado

Após a migração, o dashboard mostrará:
- ✅ **Total**: 55 (todas as ordens)
- ✅ **Pendentes**: Quantidade correta
- ✅ **Em Andamento**: Quantidade correta
- ✅ **Concluídas**: **TOTAL de ordens finalizadas** (não apenas do mês)

## Status Padronizados

O sistema agora usa apenas estes status:
- `pendente` - Ordem aberta, aguardando início
- `em_execucao` - Ordem em andamento
- `finalizada` - Ordem concluída
- `cancelada` - Ordem cancelada

## Verificação

Após aplicar:
1. Acesse o dashboard de Ordens de Serviço
2. Verifique os cards de estatísticas
3. O card "Concluídas" deve mostrar o total correto

## Arquivos Alterados

- `app/ordem_servico/ordem_servico_model.py` - Método `estatisticas_dashboard()`
- `migrar_status_ordens.py` - Script de migração (novo)
- `verificar_status_ordens.py` - Script de diagnóstico (novo)

## Rollback (Se Necessário)

Para reverter, no Shell do Render:
```python
from app.app import app
from app.extensoes import db
from app.ordem_servico.ordem_servico_model import OrdemServico

with app.app_context():
    # Não há rollback necessário - os status foram apenas normalizados
    # As ordens mantêm seus dados originais
    pass
```
