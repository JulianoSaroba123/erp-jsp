# 🔴 SOLUÇÃO URGENTE: Parcelas de Proposta não salvas

## 📌 PROBLEMA IDENTIFICADO

A **Proposta 15** no Render (produção) não possui parcelas salvas no banco de dados, mesmo mostrando o preview correto no formulário.

### Evidências:
- ✅ Preview mostra: Entrada R$ 4.550 + 2 parcelas R$ 4.225
- ❌ Banco de dados: **ZERO** parcelas salvas
- ❌ OS 111 gerada com dados errados (1 parcela, R$ 0 entrada)

### Causa Raiz:
O código de salvar/editar proposta **NÃO** está persistindo os registros `ParcelaProposta` no banco.

---

## 🚀 SOLUÇÃO IMEDIATA (Render Production)

### Opção 1: Script via Render Shell (RECOMENDADO)

1. Acessar Render Dashboard → Shell
2. Executar o script de correção:

```bash
python scripts/corrigir_parcelas_orm.py
```

Esse script irá:
- ✅ Deletar parcelas antigas da Proposta 15
- ✅ Calcular valores corretos (entrada 35% + 2 parcelas)
- ✅ Criar 3 registros em `parcelas_proposta`:
  - Parcela 0 (entrada): R$ 4.550,00
  - Parcela 1: R$ 4.225,00
  - Parcela 2: R$ 4.225,00
- ✅ Verificar totais

### Opção 2: SQL Manual via pgAdmin/Render PostgreSQL Console

```sql
-- 1. Deletar parcelas antigas
DELETE FROM parcelas_proposta WHERE proposta_id = 15;

-- 2. Inserir parcelas corretas
INSERT INTO parcelas_proposta 
(proposta_id, numero_parcela, data_vencimento, valor_parcela, ativo, criado_em, atualizado_em)
VALUES 
(15, 0, CURRENT_DATE, 4550.00, true, NOW(), NOW()),           -- Entrada
(15, 1, CURRENT_DATE + INTERVAL '30 days', 4225.00, true, NOW(), NOW()),  -- Parcela 1
(15, 2, CURRENT_DATE + INTERVAL '60 days', 4225.00, true, NOW(), NOW());  -- Parcela 2

-- 3. Verificar
SELECT 
    numero_parcela,
    data_vencimento,
    valor_parcela,
    ativo
FROM parcelas_proposta
WHERE proposta_id = 15
ORDER BY numero_parcela;
```

---

## ✅ APÓS CORREÇÃO - Gerar OS Novamente

1. **Deletar OS 111** (tem dados errados)
   - Ir em Ordem de Serviço → OS 111 → Deletar

2. **Gerar nova OS da Proposta 15**
   - Ir em Propostas → Proposta PROP20260002
   - Clicar "Gerar Ordem de Serviço"
   - Verificar que agora mostra:
     - ✅ Número de Parcelas: **2**
     - ✅ Valor Entrada: **R$ 4.550,00**
     - ✅ Data 1ª Parcela: **30 dias depois**

3. **Verificar OS gerada**
   - Deve ter 2 parcelas em "Parcelas a Receber"
   - Entrada deve aparecer separada
   - Datas devem estar espaçadas 30 dias

---

## 🐛 CORREÇÃO PERMANENTE (Para Evitar Problema Futuro)

O problema está em `app/proposta/proposta_routes.py` na rota de salvar/editar proposta.

### Investigar:
- ❓ Onde o código deleta parcelas antigas?
- ❓ Onde o código cria novas parcelas baseado no formulário?
- ❓ Por que a criação não está funcionando?

### Buscar por:
```python
# Deve haver algo assim:
ParcelaProposta.query.filter_by(proposta_id=proposta.id).delete()

# E depois deve ter:
for i in range(num_parcelas):
    parcela = ParcelaProposta(...)
    db.session.add(parcela)

db.session.commit()  # CRÍTICO: Sem isso, não salva!
```

### Possíveis causas:
1. ❌ Código de criação comentado/removido
2. ❌ Commit faltando após adicionar parcelas
3. ❌ Condição if impedindo criação
4. ❌ Exceção silenciosa durante criação

---

## 📋 CHECKLIST

- [ ] Executar script de correção no Render
- [ ] Verificar que parcelas foram criadas no banco
- [ ] Deletar OS 111
- [ ] Gerar nova OS da Proposta 15
- [ ] Confirmar que OS tem dados corretos (2 parcelas, R$ 4.550 entrada)
- [ ] **DEPOIS**: Investigar e corrigir rota de salvar proposta

---

## 🎯 RESUMO EXECUTIVO

**Situação**: Proposta sem parcelas → OS com dados errados → Cliente não pode apresentar

**Ação Imediata**: Inserir parcelas manualmente no banco (via script ou SQL)

**Ação Futura**: Corrigir rota de salvar proposta para persistir parcelas automaticamente

**Prioridade**: 🔴 CRÍTICA - Bloqueando apresentação
