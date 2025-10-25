"""
Adicionar colunas faltantes na tabela propostas
"""
from app.app import create_app
from app.extensoes import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Adicionando colunas faltantes...")
    
    # Lista de colunas para adicionar
    colunas = [
        ("data_validade", "DATE"),
        ("condicoes_pagamento", "TEXT"),
    ]
    
    for coluna, tipo in colunas:
        try:
            db.session.execute(text(f"ALTER TABLE propostas ADD COLUMN {coluna} {tipo}"))
            db.session.commit()
            print(f"✅ Adicionada coluna: {coluna}")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print(f"⏭️  Coluna {coluna} já existe")
            else:
                print(f"❌ Erro ao adicionar {coluna}: {e}")
            db.session.rollback()
    
    print("\n✅ Atualização concluída!")
