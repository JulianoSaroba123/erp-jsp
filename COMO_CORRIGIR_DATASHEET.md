# 🔧 COMO CORRIGIR: Coluna datasheet faltando no Render

## ❌ Erro:
```
column placa_solar.datasheet does not exist
```

## ✅ SOLUÇÃO RÁPIDA - Via Shell do Render

### Passo 1: Acessar Shell do Render
1. Acesse https://dashboard.render.com
2. Clique no seu web service (erp-jsp-th5o)
3. Clique em **"Shell"** no menu lateral
4. Aguarde o terminal abrir

### Passo 2: Executar Script Python
No shell do Render, cole este comando:

```bash
python adicionar_datasheet_render.py "$DATABASE_URL"
```

**OU** execute o SQL diretamente:

### Passo 3: Executar SQL Direto (alternativa)
```bash
psql $DATABASE_URL << 'EOF'
ALTER TABLE placa_solar ADD COLUMN IF NOT EXISTS datasheet VARCHAR(500);
ALTER TABLE inversor_solar ADD COLUMN IF NOT EXISTS datasheet VARCHAR(500);
SELECT table_name, column_name FROM information_schema.columns WHERE table_name IN ('placa_solar', 'inversor_solar') AND column_name = 'datasheet';
EOF
```

### Passo 4: Verificar
Você deve ver algo como:
```
✅ Coluna datasheet adicionada em placa_solar
✅ Coluna datasheet adicionada em inversor_solar
```

## 📝 O que os scripts fazem:

**adicionar_datasheet_render.py:**
- Script Python que conecta direto no PostgreSQL
- Verifica se coluna existe antes de criar
- Usa a variável $DATABASE_URL do Render

**adicionar_datasheet.sql:**
- Script SQL puro
- Pode ser executado com `psql`
- Usa blocos DO para verificação

## 🎯 Depois de executar:

1. Aguarde ~30 segundos
2. Recarregue a página do projeto no navegador
3. Tente editar o projeto novamente
4. Deve funcionar! ✅

---

**Nota:** Esses scripts são idempotentes (podem ser executados várias vezes sem problema).
