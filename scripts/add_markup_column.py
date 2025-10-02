#!/usr/bin/env python3
"""Script para adicionar a coluna markup na tabela produtos."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from aplicacao.extensoes import db
from aplicacao import create_app

def adicionar_coluna_markup():
    app = create_app()
    with app.app_context():
        try:
            # Tentar adicionar a coluna usando text() para SQLAlchemy 2.0+
            from sqlalchemy import text
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE produtos ADD COLUMN markup DECIMAL(5,2) DEFAULT 0.00'))
                conn.commit()
            print("✓ Coluna markup adicionada com sucesso!")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("✓ Coluna markup já existe")
            else:
                print(f"Erro ao adicionar coluna: {e}")
                
        # Verificar se a coluna foi adicionada
        inspector = db.inspect(db.engine)
        colunas = [col['name'] for col in inspector.get_columns('produtos')]
        if 'markup' in colunas:
            print("✓ Coluna markup confirmada na tabela produtos")
        else:
            print("✗ Coluna markup não foi encontrada")
            
        print(f"\nColunas da tabela produtos: {colunas}")

if __name__ == "__main__":
    adicionar_coluna_markup()