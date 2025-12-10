# -*- coding: utf-8 -*-
"""
Script para adicionar coluna conteudo BYTEA no PostgreSQL (Render)
Execute este no console PSQL do Render
"""

sql_commands = """
-- Adicionar coluna conteudo BYTEA na tabela ordem_servico_anexos
ALTER TABLE ordem_servico_anexos 
ADD COLUMN IF NOT EXISTS conteudo BYTEA;

-- Verificar se a coluna foi criada
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'ordem_servico_anexos' 
AND column_name = 'conteudo';
"""

print("=" * 80)
print("🔧 SQL PARA EXECUTAR NO RENDER (PostgreSQL)")
print("=" * 80)
print("\nCopie e cole o comando abaixo no console PSQL do Render:\n")
print(sql_commands)
print("\n" + "=" * 80)
print("📋 INSTRUÇÕES:")
print("1. Acesse o Render Dashboard")
print("2. Vá em erp_jsp_db_iw6v")
print("3. Clique em 'PSQL Console'")
print("4. Cole o comando acima")
print("5. Execute")
print("=" * 80)
