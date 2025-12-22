# 🔧 Migração de Campos - Propostas

## Problema
Os campos `forma_pagamento`, `prazo_execucao` e `garantia` estavam com limite muito pequeno:
- `forma_pagamento`: 50 caracteres
- `prazo_execucao`: 100 caracteres  
- `garantia`: 100 caracteres

Isso causava erro ao salvar propostas com textos maiores.

## Solução
Aumentei o limite para **500 caracteres** em cada campo.

## Como aplicar no Render

### Opção 1: Via Python Shell do Render
1. Acesse o dashboard do Render
2. Entre no seu serviço `erp-jsp-th5o`
3. Vá em **Shell** (menu lateral)
4. Execute:
```bash
python scripts/migrar_campos_proposta.py
```

### Opção 2: Via SQL direto (mais rápido)
1. Conecte no banco via DBeaver ou pgAdmin
2. Execute estas queries:
```sql
ALTER TABLE propostas ALTER COLUMN forma_pagamento TYPE VARCHAR(500);
ALTER TABLE propostas ALTER COLUMN prazo_execucao TYPE VARCHAR(500);
ALTER TABLE propostas ALTER COLUMN garantia TYPE VARCHAR(500);
```

### Opção 3: Aguardar o próximo deploy
O Render pode aplicar automaticamente quando detectar mudanças no modelo, mas é mais seguro executar manualmente.

## Verificação
Após executar, teste criar/editar uma proposta com textos longos nesses campos.
