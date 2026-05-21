# 🔧 SOLUÇÃO: Erro ao Salvar Dados Financeiros no Render

## ❌ Problema
Erro 500 (Internal Server Error) ao salvar dados financeiros no modal do projeto solar.

**Causa:** As colunas financeiras (`concessionaria_id`, `tarifa_kwh`, `economia_mensal`, `economia_anual`, `impostos_percentual`) não existem no banco PostgreSQL do Render.

---

## ✅ SOLUÇÃO IMEDIATA (Executar AGORA)

### Passo 1: Acessar o Shell do Render

1. Acesse: https://dashboard.render.com/
2. Faça login com sua conta
3. Na lista de serviços, clique em **erp-jsp-th5o**
4. No menu superior, clique na aba **"Shell"**
5. Aguarde o terminal carregar (pode levar alguns segundos)

### Passo 2: Executar a Migração

No terminal do Shell, execute:

```bash
python migrations/aplicar_todas_migracoes.py
```

### Passo 3: Verificar o Resultado

Você deve ver uma saída como esta:

```
============================================================
🚀 APLICANDO MIGRAÇÕES DO BANCO DE DADOS
============================================================
🔗 Conectando ao banco: postgresql+psycopg://***@...
✅ Conexão estabelecida com sucesso!
🗄️  Banco: postgresql

============================================================
📊 MIGRAÇÃO: Dados Financeiros - projeto_solar
============================================================
  ✅ Coluna criada: concessionaria_id (INTEGER)
  ✅ Coluna criada: tarifa_kwh (NUMERIC(10,4) DEFAULT 0)
  ✅ Coluna criada: economia_mensal (NUMERIC(12,2) DEFAULT 0)
  ✅ Coluna criada: economia_anual (NUMERIC(12,2) DEFAULT 0)
  ✅ Coluna criada: impostos_percentual (NUMERIC(8,2) DEFAULT 0)
✅ Migração de dados financeiros aplicada com sucesso!

============================================================
✅ TODAS AS MIGRAÇÕES FORAM APLICADAS COM SUCESSO!
============================================================
```

### Passo 4: Testar

1. Volte ao seu projeto: https://erp-jsp-th5o.onrender.com/energia-solar/projetos/6/dashboard
2. Clique no botão **"💰 Dados Financeiros"**
3. Preencha os campos e clique em **"SALVAR"**
4. ✅ Deve salvar sem erro!

---

## 🔄 SOLUÇÃO AUTOMÁTICA (Já Configurada)

### O que foi feito:

✅ **Arquivo criado:** `migrations/aplicar_todas_migracoes.py`
- Script centralizado para todas as migrações do banco
- Executado automaticamente em cada deploy do Render
- Idempotente (pode rodar várias vezes sem problemas)

✅ **Build.sh atualizado:** Já estava configurado para executar migrações
```bash
python migrations/aplicar_todas_migracoes.py
```

✅ **Commit realizado:** Código já está no GitHub (commit `c1dc9e1`)

### Próximos Deploys:

A partir de agora, **toda vez que você fizer um deploy no Render**, as migrações serão aplicadas automaticamente. Você não precisa mais executar manualmente!

---

## 📝 Colunas Adicionadas

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `concessionaria_id` | INTEGER | ID da concessionária de energia |
| `tarifa_kwh` | NUMERIC(10,4) | Tarifa por kWh (R$) |
| `economia_mensal` | NUMERIC(12,2) | Economia mensal estimada (R$) |
| `economia_anual` | NUMERIC(12,2) | Economia anual estimada (R$) |
| `impostos_percentual` | NUMERIC(8,2) | Percentual de impostos (%) |

---

## 🆘 Em caso de erro:

### Erro: "python: command not found"
Execute:
```bash
python3 migrations/aplicar_todas_migracoes.py
```

### Erro: "No module named 'dotenv'"
Execute:
```bash
pip install python-dotenv
python migrations/aplicar_todas_migracoes.py
```

### Erro: "DATABASE_URL not found"
Verifique se a variável de ambiente `DATABASE_URL` está configurada no Render:
1. No dashboard do Render, vá em **Environment**
2. Confirme que `DATABASE_URL` está presente

### Ainda com problemas?
Me informe o erro completo que apareceu no terminal.

---

## ✅ Status

- [x] Script de migração criado
- [x] Commit realizado
- [x] Push para GitHub concluído
- [ ] **PENDENTE:** Executar migração manual no Render (Passo 2 acima)
- [ ] **PENDENTE:** Testar salvamento de dados financeiros

