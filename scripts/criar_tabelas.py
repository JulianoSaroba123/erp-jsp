#!/usr/bin/env python3
"""Script para criar as tabelas do banco de dados."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from aplicacao.extensoes import db
from aplicacao import create_app

def criar_tabelas():
    app = create_app()
    with app.app_context():
        try:
            # Importar todos os modelos para garantir que estão registrados
            from aplicacao.cliente.cliente_model import Cliente
            from aplicacao.fornecedor.fornecedor_model import Fornecedor
            from aplicacao.produto.produto_model import Produto
            from aplicacao.autenticacao.models import Usuario
            
            print("Criando todas as tabelas...")
            db.create_all()
            print("✓ Tabelas criadas com sucesso!")
            
            # Verificar se as tabelas foram criadas
            inspector = db.inspect(db.engine)
            tabelas = inspector.get_table_names()
            print("\nTabelas existentes:")
            for tabela in tabelas:
                print(f"  - {tabela}")
                
        except Exception as e:
            print(f"Erro ao criar tabelas: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    criar_tabelas()