"""
Script para adicionar campo tipo_instalacao na tabela projeto_solar
"""
import os
os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:postgres@localhost/erp_jsp_local')

from app.app import create_app
from app.extensoes import db

app = create_app()

with app.app_context():
    try:
        # Adicionar coluna tipo_instalacao
        db.session.execute("""
            ALTER TABLE projeto_solar 
            ADD COLUMN IF NOT EXISTS tipo_instalacao VARCHAR(20) DEFAULT 'monofasica'
        """)
        db.session.commit()
        print("✅ Coluna tipo_instalacao adicionada com sucesso!")
        
        # Atualizar projetos existentes
        db.session.execute("""
            UPDATE projeto_solar 
            SET tipo_instalacao = 'monofasica' 
            WHERE tipo_instalacao IS NULL
        """)
        db.session.commit()
        print("✅ Projetos existentes atualizados!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        db.session.rollback()
