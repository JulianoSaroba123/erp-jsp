# -*- coding: utf-8 -*-
"""
Adicionar coluna 'conteudo' BLOB na tabela ordem_servico_anexos
"""

import os
import sys
import sqlite3

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🔧 ADICIONAR COLUNA 'conteudo' NA TABELA ordem_servico_anexos")
print("=" * 80)

# Conecta no banco SQLite (tenta os dois possíveis)
db_paths = ['erp.db', os.path.join(os.path.dirname(__file__), 'database', 'database.db')]

db_path = None
for path in db_paths:
    if os.path.exists(path):
        db_path = path
        break

if not db_path:
    print(f"\n❌ Banco de dados não encontrado!")
    sys.exit(1)

print(f"\n📁 Banco de dados: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Verifica se a coluna já existe
    cursor.execute("PRAGMA table_info(ordem_servico_anexos)")
    colunas = [col[1] for col in cursor.fetchall()]
    
    if 'conteudo' in colunas:
        print(f"\n✅ Coluna 'conteudo' já existe!")
    else:
        print(f"\n🔨 Adicionando coluna 'conteudo' BLOB...")
        cursor.execute("ALTER TABLE ordem_servico_anexos ADD COLUMN conteudo BLOB")
        conn.commit()
        print(f"✅ Coluna 'conteudo' adicionada com sucesso!")
        
except Exception as e:
    print(f"\n❌ Erro: {str(e)}")
    conn.rollback()
finally:
    conn.close()

print("\n" + "=" * 80)
