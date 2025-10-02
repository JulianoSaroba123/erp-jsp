#!/usr/bin/env python3
"""Script para verificar tabelas no banco."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from aplicacao.extensoes import db
from aplicacao import create_app

def listar_tabelas():
    app = create_app()
    with app.app_context():
        try:
            # Para SQLite, usar este método
            inspector = db.inspect(db.engine)
            tabelas = inspector.get_table_names()
            print("Tabelas no banco de dados:")
            for tabela in tabelas:
                print(f"  - {tabela}")
                
            # Verificar se as tabelas específicas existem
            if 'produtos' in tabelas:
                print("\n✓ Tabela 'produtos' existe")
            else:
                print("\n✗ Tabela 'produtos' NÃO existe")
                
            if 'fornecedores' in tabelas:
                print("✓ Tabela 'fornecedores' existe")
            else:
                print("✗ Tabela 'fornecedores' NÃO existe")
                
        except Exception as e:
            print(f"Erro ao verificar tabelas: {e}")

if __name__ == "__main__":
    listar_tabelas()