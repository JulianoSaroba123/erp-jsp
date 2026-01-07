"""
Script para adicionar coluna 'numero' na tabela projeto_solar
"""
import os
from sqlalchemy import create_engine, text

# Usar DATABASE_URL do ambiente ou SQLite local
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    DATABASE_URL = 'sqlite:///erp.db'
elif DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+psycopg://', 1)
elif DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        # Adicionar coluna numero se não existir
        if 'sqlite' in DATABASE_URL:
            # SQLite
            conn.execute(text("""
                ALTER TABLE projeto_solar ADD COLUMN numero VARCHAR(20)
            """))
        else:
            # PostgreSQL
            conn.execute(text("""
                ALTER TABLE projeto_solar ADD COLUMN IF NOT EXISTS numero VARCHAR(20)
            """))
        
        conn.commit()
        print("✅ Coluna 'numero' adicionada com sucesso!")
        
except Exception as e:
    if 'already exists' in str(e).lower() or 'duplicate column' in str(e).lower():
        print("⚠️  Coluna 'numero' já existe!")
    else:
        print(f"❌ Erro: {e}")
