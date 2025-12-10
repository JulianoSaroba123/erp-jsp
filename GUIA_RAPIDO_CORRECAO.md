# ⚡ GUIA RÁPIDO - Correção de Estrutura

## 🎯 O QUE FOI FEITO

### ✅ **Código Flask (Completo)**
- Arquivo conflitante removido: `proposta_model_novo.py` → `.BACKUP`
- Model correto mantido: `Proposta.__tablename__ = 'propostas'` ✅
- Foreign Keys validadas: `ordem_servico → propostas → clientes` ✅

### ⏳ **Banco de Dados (Pendente - Executar no Render)**
- Scripts SQL prontos para correção
- Remover tabela órfã `proposta`
- Limpar registros com FKs inválidas

---

## 🚀 EXECUTE AGORA NO RENDER

### **Passo 1: Acesse o Banco**
```
Render Dashboard → erp_jsp_db_iw6v → Connect → PSQL
```

### **Passo 2: Cole o Script de Correção**
Copie TODO o conteúdo de: `scripts/sql/correcao_definitiva_propostas.sql`

Cole no console PSQL e pressione ENTER.

### **Passo 3: Valide o Resultado**
Copie TODO o conteúdo de: `scripts/sql/teste_integridade_inserts.sql`

Cole no console PSQL e pressione ENTER.

---

## ✅ RESULTADO ESPERADO

### **Consulta de Validação:**
```sql
SELECT tablename 
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename LIKE '%proposta%'
ORDER BY tablename;
```

**Deve retornar APENAS:**
```
proposta_anexo
proposta_parcela
proposta_produto
proposta_servico
propostas          ← Correto (plural)
```

**NÃO deve aparecer:** `proposta` (singular)

### **Verificar Órfãos (deve ser 0):**
```sql
SELECT COUNT(*) 
FROM ordem_servico 
WHERE proposta_id IS NOT NULL 
  AND proposta_id NOT IN (SELECT id FROM propostas);
```

---

## 📊 ESTRUTURA CORRIGIDA

```
clientes (id) ←─┬─── propostas (id, cliente_id)
                │
                └─── ordem_servico (id, cliente_id, proposta_id)
                          ↓
                     propostas (id)
```

### **Foreign Keys:**
- ✅ `ordem_servico.cliente_id` → `clientes.id`
- ✅ `ordem_servico.proposta_id` → `propostas.id`
- ✅ `propostas.cliente_id` → `clientes.id`

---

## 🔍 SE DER ERRO

### **Erro: "Tabela proposta tem registros"**
```sql
-- Ver registros:
SELECT * FROM proposta;

-- Se tiver dados, migre antes:
-- (entre em contato para script de migração)
```

### **Erro: "FK constraint"**
```sql
-- Remova FKs problemáticas:
DROP TABLE proposta CASCADE;
```

### **Conexão falha localmente**
- ✅ Execute os scripts DIRETO no console do Render
- ❌ Não tente conectar via Python local

---

## 📞 CONTATO

Se encontrar problemas:
1. Copie a mensagem de erro completa
2. Tire print da query que falhou
3. Envie o print

---

**JSP Soluções - 2025-12-10**
