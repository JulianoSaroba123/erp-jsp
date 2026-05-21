# -*- coding: utf-8 -*-
"""
Script de migração para adicionar coluna nome_fantasia em clientes.
====================================================================

Adiciona a coluna nome_fantasia que estava faltando na tabela clientes.

Uso: python migrations/adicionar_nome_fantasia_cliente.py

Autor: JSP Soluções
Data: Abril 2026
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import inspect, text
from app.app import create_app
from app.extensoes import db


def adicionar_coluna():
    """Adiciona coluna nome_fantasia na tabela clientes."""
    
    print("=" * 80)
    print("MIGRAÇÃO: Adicionar nome_fantasia em clientes")
    print("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            colunas_existentes = [col['name'] for col in inspector.get_columns('clientes')]
            
            print(f"\n📋 Tabela 'clientes' encontrada")
            print(f"   Total de colunas atuais: {len(colunas_existentes)}")
            
            if 'nome_fantasia' in colunas_existentes:
                print(f"   ✓ Coluna 'nome_fantasia' já existe!")
                return
            
            print(f"   ➕ Adicionando coluna 'nome_fantasia'...")
            sql = 'ALTER TABLE clientes ADD COLUMN nome_fantasia VARCHAR(150)'
            db.session.execute(text(sql))
            db.session.commit()
            print(f"   ✓ Coluna 'nome_fantasia' adicionada com sucesso!")
            
            print("\n" + "=" * 80)
            print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("=" * 80)
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERRO ao adicionar coluna: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    adicionar_coluna()
