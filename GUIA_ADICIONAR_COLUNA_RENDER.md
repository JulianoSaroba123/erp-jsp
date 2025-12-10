# GUIA: Como adicionar a coluna no PostgreSQL do Render

## OPÇÃO 1: Via Shell do Serviço Web

1. Acesse https://dashboard.render.com
2. Clique no seu **serviço web** (erp-jsp-th5o)
3. No menu lateral esquerdo, clique em **"Shell"**
4. No terminal que abrir, execute:

```bash
python
```

5. Depois cole este código Python:

```python
import os
import psycopg2

# Conecta no banco
DATABASE_URL = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Adiciona a coluna
try:
    cursor.execute("""
        ALTER TABLE ordem_servico_anexos 
        ADD COLUMN IF NOT EXISTS conteudo BYTEA;
    """)
    conn.commit()
    print("✅ Coluna 'conteudo' adicionada com sucesso!")
    
    # Verifica
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'ordem_servico_anexos' 
        AND column_name = 'conteudo';
    """)
    result = cursor.fetchone()
    if result:
        print(f"✅ Confirmado: {result}")
    else:
        print("❌ Coluna não encontrada")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()
```

## OPÇÃO 2: Criar um script de migração no próprio app

Eu posso criar um endpoint /admin/migrate que executa a migração quando você acessar.
Quer que eu faça isso?

## OPÇÃO 3: Via Render Dashboard (mais recente)

1. https://dashboard.render.com
2. Clique em **"erp_jsp_db_iw6v"** (o banco de dados)
3. Procure por:
   - **"Connect"** ou
   - **"External Connection"** ou
   - **"Info"** 
4. Copie a **External Database URL**
5. Use um cliente PostgreSQL (DBeaver, pgAdmin, etc) para conectar
6. Execute o SQL:

```sql
ALTER TABLE ordem_servico_anexos 
ADD COLUMN IF NOT EXISTS conteudo BYTEA;
```

## MAIS FÁCIL: Eu crio um endpoint admin

Posso criar uma rota `/admin/migrate-db` que você acessa no navegador e ela executa a migração automaticamente. É mais simples!

Quer que eu faça?
