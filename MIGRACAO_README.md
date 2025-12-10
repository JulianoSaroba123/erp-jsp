# 🚀 INÍCIO RÁPIDO - MIGRAÇÃO DE DADOS

## ✅ **ESTADO ATUAL**

**Seus dados já estão corretos no Render!**  
Nenhuma ação necessária no momento.

---

## 📚 **QUANDO USAR OS SCRIPTS**

### **1. Novo Ambiente/Deploy**
```bash
python scripts/migrar_dados_definitivo.py
```
Importa dados do `erp.db` local para PostgreSQL novo.

### **2. Validar Integridade**
```bash
python scripts/testar_migracao.py
```
Verifica estrutura e cria backup automático.

### **3. Limpar Dados Corrompidos**
```sql
-- Execute no console do Render (PSQL)
\i scripts/sql/limpar_orfaos.sql
```
Remove registros órfãos (foreign keys quebradas).

### **4. Verificar Após Migração**
```sql
-- Execute no console do Render (PSQL)
\i scripts/sql/verificar_migracao.sql
```
Mostra relatório completo de integridade.

---

## 🔍 **DIAGNÓSTICO RÁPIDO**

### **Via Browser**
```
https://erp-jsp-th5o.onrender.com/status/sistema
```
Retorna JSON com status de todas as tabelas.

### **Via Terminal**
```bash
python scripts/testar_migracao.py
```
Análise completa local + backup automático.

---

## 📖 **DOCUMENTAÇÃO COMPLETA**

- **Guia Passo a Passo:** `GUIA_MIGRACAO_DEFINITIVA.md`
- **Status Atual:** `MIGRACAO_STATUS.md`
- **Scripts:**
  - `scripts/migrar_dados_definitivo.py` - Migração completa
  - `scripts/testar_migracao.py` - Testes e validação
  - `scripts/sql/limpar_orfaos.sql` - Limpeza PostgreSQL
  - `scripts/sql/verificar_migracao.sql` - Verificação pós-migração

---

## ⚡ **COMANDOS ÚTEIS**

```bash
# Backup local
python scripts/testar_migracao.py

# Migrar tudo
python scripts/migrar_dados_definitivo.py

# Verificar integridade no Render
curl https://erp-jsp-th5o.onrender.com/status/sistema
```

---

**JSP Soluções - 2025**
