#!/usr/bin/env python3
"""Script para adicionar campos de cliente ao modelo fornecedor."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from aplicacao.extensoes import db
from aplicacao import create_app
from sqlalchemy import text

def atualizar_tabela_fornecedores():
    app = create_app()
    with app.app_context():
        try:
            # Lista de colunas a serem adicionadas
            novas_colunas = [
                "ADD COLUMN email VARCHAR(100)",
                "ADD COLUMN numero VARCHAR(20)",
                "ADD COLUMN data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP",
                "ADD COLUMN complemento VARCHAR(100)",
                "ADD COLUMN bairro VARCHAR(100)",
                "ADD COLUMN uf VARCHAR(2)",
                "ADD COLUMN pais VARCHAR(50)",
                "ADD COLUMN inscricao_estadual VARCHAR(30)",
                "ADD COLUMN inscricao_municipal VARCHAR(30)",
                "ADD COLUMN observacoes TEXT",
                "ADD COLUMN ativo BOOLEAN DEFAULT 1",
                "ADD COLUMN nome_fantasia VARCHAR(100)",
                "ADD COLUMN logradouro VARCHAR(150)",
                "ADD COLUMN apelido VARCHAR(100)"
            ]
            
            with db.engine.connect() as conn:
                # Verificar colunas existentes primeiro
                inspector = db.inspect(db.engine)
                colunas_existentes = [col['name'] for col in inspector.get_columns('fornecedores')]
                print(f"Colunas atuais: {colunas_existentes}")
                
                for coluna_sql in novas_colunas:
                    nome_coluna = coluna_sql.split()[2]  # Extrair nome da coluna
                    
                    if nome_coluna not in colunas_existentes:
                        try:
                            sql = f"ALTER TABLE fornecedores {coluna_sql}"
                            conn.execute(text(sql))
                            print(f"✓ Coluna {nome_coluna} adicionada")
                        except Exception as e:
                            if "duplicate column name" not in str(e).lower():
                                print(f"⚠ Erro ao adicionar {nome_coluna}: {e}")
                    else:
                        print(f"- Coluna {nome_coluna} já existe")
                
                # Renomear coluna cnpj para cpf_cnpj (SQLite não suporta RENAME COLUMN diretamente)
                if 'cnpj' in colunas_existentes and 'cpf_cnpj' not in colunas_existentes:
                    print("\n⚠ SQLite não suporta RENAME COLUMN diretamente.")
                    print("Mantendo coluna 'cnpj' existente. Será necessário migrar os dados manualmente.")
                    # Adicionar a nova coluna cpf_cnpj
                    try:
                        conn.execute(text("ALTER TABLE fornecedores ADD COLUMN cpf_cnpj VARCHAR(20)"))
                        print("✓ Coluna cpf_cnpj adicionada")
                        
                        # Copiar dados da coluna cnpj para cpf_cnpj
                        conn.execute(text("UPDATE fornecedores SET cpf_cnpj = cnpj WHERE cnpj IS NOT NULL"))
                        print("✓ Dados migrados de cnpj para cpf_cnpj")
                    except Exception as e:
                        print(f"⚠ Erro na migração cnpj→cpf_cnpj: {e}")
                
                conn.commit()
                
            # Verificar resultado final
            inspector = db.inspect(db.engine)
            colunas_finais = [col['name'] for col in inspector.get_columns('fornecedores')]
            print(f"\nColunas finais da tabela fornecedores:")
            for coluna in sorted(colunas_finais):
                print(f"  - {coluna}")
                
        except Exception as e:
            print(f"Erro geral: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    atualizar_tabela_fornecedores()