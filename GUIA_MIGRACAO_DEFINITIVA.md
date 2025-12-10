# 🚀 GUIA DE MIGRAÇÃO DEFINITIVA - SQLite → PostgreSQL

## 📋 **VISÃO GERAL**

Este guia documenta o processo **completo e profissional** para migrar dados do SQLite local para PostgreSQL no Render, garantindo integridade referencial.

---

## 🎯 **ESTRATÉGIA**

### **Por que usar chaves naturais?**
- IDs auto-incrementados do SQLite **não coincidem** com PostgreSQL
- Foreign keys quebram ao importar diretamente
- **Solução:** Usar `cpf_cnpj` (clientes), `codigo` (propostas), `numero` (OS)

### **Ordem de execução**
1. Limpar registros órfãos do PostgreSQL (se houver)
2. Importar Clientes → Criar mapeamento ID
3. Importar Propostas → Vincular cliente via cpf_cnpj
4. Importar OS → Vincular proposta via código

---

## 📂 **ARQUIVOS CRIADOS**

### **1. `scripts/sql/limpar_orfaos.sql`**
- Remove/desativa registros órfãos no PostgreSQL
- Identifica problemas de integridade
- Reseta sequences
- **Uso:** Execute no console do Render ANTES da migração

### **2. `scripts/migrar_dados_definitivo.py`**
- Script Python completo de migração
- Usa chaves naturais (cpf_cnpj, codigo)
- Cria mapeamento de IDs automaticamente
- **Uso:** Execute localmente (conecta ao Render via DATABASE_URL)

### **3. `scripts/sql/verificar_migracao.sql`**
- Valida integridade pós-migração
- Detecta órfãos, duplicatas, campos vazios
- Verifica sequences
- **Uso:** Execute no Render APÓS a migração

---

## 🔧 **PASSO A PASSO**

### **ETAPA 1: Preparar PostgreSQL (Render)**

1. Acesse o console do Render:
   ```
   Dashboard → erp_jsp_db_iw6v → Connect → PSQL
   ```

2. Execute a limpeza de órfãos (OPCIONAL - só se houver dados antigos):
   ```sql
   -- Opção A: Remover órfãos (irreversível)
   DELETE FROM ordem_servico WHERE cliente_id NOT IN (SELECT id FROM clientes);
   DELETE FROM propostas WHERE cliente_id NOT IN (SELECT id FROM clientes);
   DELETE FROM clientes WHERE cpf_cnpj IS NULL OR cpf_cnpj = '';
   
   -- Opção B: Desativar órfãos (recomendado)
   UPDATE ordem_servico SET ativo = FALSE WHERE cliente_id NOT IN (SELECT id FROM clientes);
   UPDATE propostas SET ativo = FALSE WHERE cliente_id NOT IN (SELECT id FROM clientes);
   UPDATE clientes SET ativo = FALSE WHERE cpf_cnpj IS NULL OR cpf_cnpj = '';
   ```

3. Verificar estado atual:
   ```sql
   SELECT 'Clientes' as tabela, COUNT(*) as total FROM clientes;
   SELECT 'Propostas' as tabela, COUNT(*) as total FROM propostas;
   SELECT 'OS' as tabela, COUNT(*) as total FROM ordem_servico;
   ```

---

### **ETAPA 2: Executar Migração (Local)**

1. Certifique-se que `erp.db` existe localmente:
   ```powershell
   ls erp.db
   ```

2. Configure `DATABASE_URL` no `.env`:
   ```env
   DATABASE_URL=postgresql://erp_jsp_db_iw6v_user:roBPw29VFmZKdksaGXw1tv4mYLKQwnl@dpg-d4pf1s49c44c73bdsdrg-a.oregon-postgres.render.com/erp_jsp_db_iw6v
   ```

3. Execute o script:
   ```powershell
   python scripts/migrar_dados_definitivo.py
   ```

4. Observe a saída:
   ```
   ✅ Clientes: 5 importados, 5 mapeados
   ✅ Propostas: 3 importadas, 3 mapeadas
   ✅ Ordens de Serviço: 12 importadas
   ```

---

### **ETAPA 3: Verificar Integridade (Render)**

1. Execute queries de verificação:
   ```sql
   -- Verificar órfãos (deve retornar 0)
   SELECT COUNT(*) FROM ordem_servico 
   WHERE cliente_id NOT IN (SELECT id FROM clientes);
   
   SELECT COUNT(*) FROM propostas 
   WHERE cliente_id NOT IN (SELECT id FROM clientes);
   
   -- Verificar duplicatas (deve retornar vazio)
   SELECT cpf_cnpj, COUNT(*) FROM clientes 
   GROUP BY cpf_cnpj HAVING COUNT(*) > 1;
   ```

2. Ou execute o script completo:
   ```sql
   \i scripts/sql/verificar_migracao.sql
   ```

---

## 🛠️ **TROUBLESHOOTING**

### **Erro: "Cliente não encontrado"**
- **Causa:** Cliente não foi importado (cpf_cnpj inválido)
- **Solução:** Verifique se o cliente tem cpf_cnpj no SQLite:
  ```sql
  SELECT * FROM clientes WHERE cpf_cnpj IS NULL;
  ```

### **Erro: "Proposta já existe"**
- **Causa:** Proposta com mesmo código já no PostgreSQL
- **Solução:** Script pula automaticamente (usa RETURNING id)

### **Erro: "Foreign key violation"**
- **Causa:** Tentando inserir OS antes do cliente/proposta
- **Solução:** Script já segue ordem correta (Clientes → Propostas → OS)

### **Sequences desatualizadas**
- **Causa:** IDs inseridos manualmente ou via SQL direto
- **Solução:** Execute no PostgreSQL:
  ```sql
  SELECT setval(pg_get_serial_sequence('clientes', 'id'), 
                (SELECT MAX(id) FROM clientes));
  SELECT setval(pg_get_serial_sequence('propostas', 'id'), 
                (SELECT MAX(id) FROM propostas));
  SELECT setval(pg_get_serial_sequence('ordem_servico', 'id'), 
                (SELECT MAX(id) FROM ordem_servico));
  ```

---

## ✅ **CHECKLIST FINAL**

- [ ] Backup do `erp.db` local criado
- [ ] DATABASE_URL configurado no `.env`
- [ ] Órfãos limpos no PostgreSQL (se necessário)
- [ ] Script `migrar_dados_definitivo.py` executado com sucesso
- [ ] Queries de verificação retornam 0 órfãos
- [ ] Sequences resetadas corretamente
- [ ] Listagem de OS no Render mostra todos os registros
- [ ] Dashboard mostra estatísticas corretas

---

## 📊 **LOGS ESPERADOS**

### **Migração Bem-Sucedida**
```
================================================================================
🔄 MIGRAÇÃO DEFINITIVA - SQLite → PostgreSQL
================================================================================

📋 ETAPA 1: Importando CLIENTES
--------------------------------------------------------------------------------
   ✅ MR JACKY COMERCIO DE PRODUTOS           (novo ID: 1)
   ✅ RICARDO CURY DA SILVA ME                (novo ID: 2)
   ...
✅ Clientes: 5 importados, 5 mapeados

📋 ETAPA 2: Importando PROPOSTAS
--------------------------------------------------------------------------------
   ✅ PROP-2024-001   (novo ID: 1)
   ✅ PROP-2024-002   (novo ID: 2)
   ...
✅ Propostas: 3 importadas, 3 mapeadas

📋 ETAPA 3: Importando ORDENS DE SERVIÇO
--------------------------------------------------------------------------------
   ✅ OS-2024-0001    (novo ID: 1)
   ✅ OS-2024-0002    (novo ID: 2)
   ...
✅ Ordens de Serviço: 12 importadas

================================================================================
✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO
================================================================================
📊 Resumo:
   • Clientes: 5 mapeados
   • Propostas: 3 mapeadas
   • Ordens de Serviço: 12 importadas
================================================================================
```

---

## 🔒 **SEGURANÇA**

- ✅ Usa transações (COMMIT/ROLLBACK automático)
- ✅ Não desativa foreign keys permanentemente
- ✅ Valida chaves naturais antes de inserir
- ✅ Pula duplicatas automaticamente (INSERT RETURNING id)
- ✅ Registra todos os mapeamentos de IDs

---

## 📞 **SUPORTE**

Em caso de dúvidas:
1. Execute `scripts/sql/verificar_migracao.sql` e envie o resultado
2. Execute `python scripts/migrar_dados_definitivo.py` e envie o log completo
3. Acesse `/status/sistema` no Render para ver estado atual do banco

---

**Desenvolvido por JSP Soluções - 2025**
