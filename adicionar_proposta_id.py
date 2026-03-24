#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Adiciona coluna proposta_id na tabela ordem_servico
"""

from app.app import create_app
from app.extensoes import db
from sqlalchemy import text, inspect

app = create_app()

with app.app_context():
    inspector = inspect(db.engine)
    colunas_existentes = [col['name'] for col in inspector.get_columns('ordem_servico')]
    
    print("=" * 60)
    print("ADICIONANDO COLUNA proposta_id")
    print("=" * 60)
    
    if 'proposta_id' in colunas_existentes:
        print("✅ Coluna 'proposta_id' já existe!")
    else:
        print("📝 Adicionando coluna 'proposta_id'...")
        try:
            # Adiciona a coluna
            sql = text("""
                ALTER TABLE ordem_servico 
                ADD COLUMN proposta_id INTEGER NULL
            """)
            db.session.execute(sql)
            
            # Adiciona foreign key se possível
            try:
                sql_fk = text("""
                    ALTER TABLE ordem_servico 
                    ADD CONSTRAINT fk_ordem_servico_proposta 
                    FOREIGN KEY (proposta_id) REFERENCES propostas(id)
                """)
                db.session.execute(sql_fk)
                print("✅ Foreign key adicionada!")
            except Exception as e:
                print(f"⚠️ Foreign key não adicionada: {e}")
            
            db.session.commit()
            print("✅ Coluna 'proposta_id' adicionada com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            db.session.rollback()
    
    print("=" * 60)
