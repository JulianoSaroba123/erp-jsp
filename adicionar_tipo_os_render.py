#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para adicionar coluna tipo_os no Render
===============================================

Adiciona a coluna tipo_os na tabela ordem_servico no banco PostgreSQL do Render.
"""

import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app import create_app
from app.extensoes import db

def adicionar_coluna_tipo_os():
    """Adiciona coluna tipo_os na tabela ordem_servico."""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("=" * 80)
            print("🔧 ADICIONANDO COLUNA tipo_os NO RENDER")
            print("=" * 80)
            
            # Verifica se a coluna já existe
            check_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='ordem_servico' AND column_name='tipo_os';
            """
            
            result = db.session.execute(db.text(check_sql)).fetchone()
            
            if result:
                print("✅ Coluna tipo_os já existe!")
                return
            
            print("\n📝 Adicionando coluna tipo_os...")
            
            # Adiciona a coluna com valor padrão
            alter_sql = """
            ALTER TABLE ordem_servico 
            ADD COLUMN tipo_os VARCHAR(20) DEFAULT 'comercial';
            """
            
            db.session.execute(db.text(alter_sql))
            db.session.commit()
            
            print("✅ Coluna tipo_os adicionada com sucesso!")
            
            # Atualiza ordens existentes vindas de propostas para 'comercial'
            print("\n📝 Atualizando ordens existentes...")
            
            update_sql = """
            UPDATE ordem_servico 
            SET tipo_os = 'comercial' 
            WHERE proposta_id IS NOT NULL AND tipo_os IS NULL;
            """
            
            db.session.execute(db.text(update_sql))
            db.session.commit()
            
            print("✅ Ordens existentes atualizadas!")
            
            # Verifica o total de registros
            count_sql = "SELECT COUNT(*) FROM ordem_servico WHERE tipo_os = 'comercial';"
            total = db.session.execute(db.text(count_sql)).scalar()
            
            print(f"\n📊 Total de OS com tipo_os='comercial': {total}")
            
            print("\n" + "=" * 80)
            print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ ERRO: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    adicionar_coluna_tipo_os()
