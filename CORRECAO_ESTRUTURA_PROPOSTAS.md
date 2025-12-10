# 🔧 CORREÇÃO DEFINITIVA - Estrutura de Propostas

## 📊 **ANÁLISE DO PROBLEMA**

### **Problema Identificado:**
1. **Duplicação de tabelas:** Existem `proposta` e `propostas` no banco
2. **Inconsistência:** Models Flask usam `propostas`, mas `proposta` também existe
3. **Foreign Keys:** Algumas FKs podem apontar para a tabela errada
4. **Arquivo conflitante:** `proposta_model_novo.py` usa `__tablename__ = 'proposta'` (errado)

### **Diagnóstico Local (SQLite):**
```
✅ proposta: 0 registros (tabela órfã)
✅ propostas: 6 registros (tabela correta)
✅ Models Flask: Proposta.__tablename__ = 'propostas' ✅
✅ Foreign Keys: ordem_servico.proposta_id → propostas.id ✅
⚠️  1 órfão: Uma OS referencia proposta_id que não existe em 'proposta'
```

---

## ✅ **CORREÇÕES APLICADAS**

### **1. Código Flask (Local)**

#### **a) Arquivo Conflitante Removido**
```bash
app/proposta/proposta_model_novo.py → proposta_model_novo.py.BACKUP
```
**Motivo:** Usava `__tablename__ = 'proposta'` (singular, incorreto)

#### **b) Model Correto Mantido**
```python
# app/proposta/proposta_model.py
class Proposta(BaseModel):
    __tablename__ = 'propostas'  # ✅ Correto (plural)
```

#### **c) Foreign Keys nos Models**
```python
# app/ordem_servico/ordem_servico_model.py
class OrdemServico(BaseModel):
    __tablename__ = 'ordem_servico'
    
    # FK para propostas (plural) ✅
    proposta_id = db.Column(db.Integer, db.ForeignKey('propostas.id'), nullable=True)
    
    # FK para clientes ✅
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
```

---

## 🗄️ **CORREÇÕES NO BANCO DE DADOS (Render)**

### **2. Scripts SQL Criados**

#### **a) `scripts/sql/correcao_definitiva_propostas.sql`**
**Função:** Corrigir estrutura de tabelas no PostgreSQL

**Operações:**
1. **Diagnóstico inicial:** Lista tabelas, contagens, FKs existentes
2. **Identificar órfãos:** OS e propostas com referências inválidas
3. **Remover tabela órfã:** `DROP TABLE proposta CASCADE`
4. **Limpar órfãos:** Desativa/corrige registros com FKs inválidas
5. **Validação final:** Confirma que só existe `propostas` e 0 órfãos

**Como executar:**
```bash
# 1. Acesse Render Dashboard
# 2. Vá em: erp_jsp_db_iw6v → Connect → PSQL
# 3. Cole e execute o script SQL
```

#### **b) `scripts/sql/teste_integridade_inserts.sql`**
**Função:** Testar integridade após correção

**Operações:**
1. INSERT em `clientes`
2. INSERT em `propostas` com FK para cliente
3. INSERT em `ordem_servico` com FKs para cliente E proposta
4. ROLLBACK automático (não persiste dados)
5. Valida foreign keys funcionando

**Como executar:**
```bash
# Execute APÓS o script de correção
# No console PSQL do Render
```

---

## 📋 **PASSO A PASSO PARA PRODUÇÃO**

### **ETAPA 1: Backup (Render)**
```bash
# No Render Dashboard:
# Settings → Manual Backups → Create Backup
```

### **ETAPA 2: Conectar ao PostgreSQL**
```bash
# Render Dashboard → Database → Connect → PSQL
```

### **ETAPA 3: Executar Correção**
```sql
-- Copie e cole o conteúdo de:
-- scripts/sql/correcao_definitiva_propostas.sql
```

### **ETAPA 4: Validar Resultado**
```sql
-- Deve retornar APENAS 'propostas' (não 'proposta'):
SELECT tablename 
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename LIKE '%proposta%';

-- Deve retornar 0 em todas as linhas:
SELECT 'OS órfãs' as tipo, COUNT(*) FROM ordem_servico 
WHERE proposta_id IS NOT NULL 
  AND proposta_id NOT IN (SELECT id FROM propostas);
```

### **ETAPA 5: Testar INSERT**
```sql
-- Copie e cole o conteúdo de:
-- scripts/sql/teste_integridade_inserts.sql
```

### **ETAPA 6: Deploy Aplicação**
```bash
# Render faz auto-deploy quando você fizer push no GitHub
git add -A
git commit -m "🔧 Correção definitiva: estrutura de propostas"
git push origin main
```

---

## 🔍 **ESTRUTURA FINAL ESPERADA**

### **Tabelas no PostgreSQL:**
```
✅ clientes
✅ propostas (ÚNICO, plural)
✅ ordem_servico
✅ proposta_anexo
✅ proposta_parcela
✅ proposta_produto
✅ proposta_servico
❌ proposta (REMOVIDA)
```

### **Foreign Keys:**
```sql
ordem_servico.proposta_id  → propostas.id
ordem_servico.cliente_id   → clientes.id
propostas.cliente_id       → clientes.id
proposta_anexo.proposta_id → propostas.id
proposta_parcela.proposta_id → propostas.id
proposta_produto.proposta_id → propostas.id
proposta_servico.proposta_id → propostas.id
```

### **Órfãos:**
```
0 registros órfãos em todas as tabelas
```

---

## 🛡️ **GARANTIAS**

✅ **Não desativa foreign keys permanentemente**  
✅ **Usa transações (BEGIN/COMMIT/ROLLBACK)**  
✅ **Valida antes de remover (tabela deve estar vazia)**  
✅ **Scripts seguros para PostgreSQL**  
✅ **Não usa comandos SQLite**  
✅ **Backup recomendado antes de executar**  

---

## 📊 **QUERIES DE MONITORAMENTO**

### **Verificar Estrutura:**
```sql
SELECT tablename 
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename LIKE '%proposta%'
ORDER BY tablename;
```

### **Verificar Órfãos:**
```sql
SELECT 'OS → Propostas' as fk, COUNT(*) 
FROM ordem_servico 
WHERE proposta_id IS NOT NULL 
  AND proposta_id NOT IN (SELECT id FROM propostas)
UNION ALL
SELECT 'OS → Clientes', COUNT(*) 
FROM ordem_servico 
WHERE cliente_id NOT IN (SELECT id FROM clientes)
UNION ALL
SELECT 'Propostas → Clientes', COUNT(*) 
FROM propostas 
WHERE cliente_id NOT IN (SELECT id FROM clientes);
```

### **Verificar Contagens:**
```sql
SELECT 
    'Clientes' as tabela,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE ativo = TRUE) as ativos
FROM clientes
UNION ALL
SELECT 'Propostas', COUNT(*), COUNT(*) FILTER (WHERE ativo = TRUE)
FROM propostas
UNION ALL
SELECT 'Ordem Serviço', COUNT(*), COUNT(*) FILTER (WHERE ativo = TRUE)
FROM ordem_servico
ORDER BY tabela;
```

---

## 🚨 **TROUBLESHOOTING**

### **Erro: "Tabela proposta contém registros"**
```sql
-- Verificar registros:
SELECT * FROM proposta LIMIT 10;

-- Se houver dados importantes, migre antes:
INSERT INTO propostas (...)
SELECT ... FROM proposta;

-- Depois execute a remoção
```

### **Erro: "FK constraint violation"**
```sql
-- Listar FKs que impedem remoção:
SELECT constraint_name, table_name 
FROM information_schema.table_constraints 
WHERE constraint_type = 'FOREIGN KEY'
  AND constraint_name IN (
    SELECT constraint_name 
    FROM information_schema.constraint_column_usage 
    WHERE table_name = 'proposta'
  );

-- Remover FKs manualmente:
ALTER TABLE <table_name> DROP CONSTRAINT <constraint_name>;
```

### **Erro: "Password authentication failed"**
- **Causa:** Tentando conectar localmente ao Render com credenciais antigas
- **Solução:** Execute scripts SQL direto no console PSQL do Render

---

## 📝 **RESUMO EXECUTIVO**

| Item | Status | Ação |
|------|--------|------|
| Model Flask | ✅ Correto | Usa `propostas` (plural) |
| Arquivo conflitante | ✅ Removido | `proposta_model_novo.py.BACKUP` |
| Script SQL correção | ✅ Criado | `correcao_definitiva_propostas.sql` |
| Script SQL teste | ✅ Criado | `teste_integridade_inserts.sql` |
| Tabela `proposta` | ⚠️ Pendente | Executar script no Render |
| Foreign Keys | ✅ Corretas | Apontam para `propostas` |
| Órfãos | ⚠️ Pendente | Limpar via script SQL |

---

## 🔗 **ARQUIVOS RELACIONADOS**

- `app/proposta/proposta_model.py` - Model correto (propostas)
- `app/proposta/proposta_model_novo.py.BACKUP` - Model errado (removido)
- `app/ordem_servico/ordem_servico_model.py` - FKs corretas
- `scripts/sql/correcao_definitiva_propostas.sql` - Correção completa
- `scripts/sql/teste_integridade_inserts.sql` - Validação
- `scripts/diagnostico_estrutura_banco.py` - Diagnóstico automatizado

---

**Desenvolvido por JSP Soluções - 2025-12-10**
