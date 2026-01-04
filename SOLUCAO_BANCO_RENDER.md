# ⚠️ SOLUÇÃO PARA ERRO 500 - BANCO INACESSÍVEL

## Problema Identificado

Nos logs do Render:
```
sqlalchemy.exc.OperationalError: (psycopg.OperationalError) 
falha ao resolver o host 'dpg-d4pfis49c44c73bdsdrg-...'
```

O banco PostgreSQL do Render está **inacessível** (pausado, expirado ou removido).

## Soluções

### Opção 1: Reativar PostgreSQL (RECOMENDADO)

1. Acesse https://dashboard.render.com
2. Encontre o banco de dados PostgreSQL
3. Status pode estar:
   - **Suspended** → Clique em "Resume"
   - **Expired** → Banco gratuito expirou após 90 dias
4. Se expirou, crie novo banco:
   - New → PostgreSQL
   - Nome: `erp-jsp-db`
   - Free tier
   - Copie a **Internal Database URL**
5. No serviço `erp-jsp-th5o`:
   - Environment → Edit
   - `DATABASE_URL` = cole a nova URL
   - Save → Manual Deploy

### Opção 2: Usar SQLite (TEMPORÁRIO)

No serviço `erp-jsp-th5o`:
1. Environment → Edit
2. **DELETE** a variável `DATABASE_URL` (deixe vazia)
3. Save Changes
4. Manual Deploy

⚠️ SQLite no Render tem limitações:
- Perde dados ao fazer redeploy
- Não recomendado para produção
- Use apenas para testes

### Opção 3: PostgreSQL Externo

Use um banco gratuito de outro provedor:
- Supabase (500MB grátis)
- ElephantSQL (20MB grátis)
- Neon (512MB grátis)

## Como Saber Qual Opção Escolher?

- **Tem dados importantes no banco?** → Opção 1 (reativar PostgreSQL)
- **Só testando?** → Opção 2 (SQLite temporário)
- **Banco expirou e não tem backup?** → Opção 3 (novo provedor)
