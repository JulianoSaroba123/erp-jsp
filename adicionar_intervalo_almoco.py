#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para adicionar coluna intervalo_almoco na tabela ordem_servico
Uso: python adicionar_intervalo_almoco.py
"""

import os
import sys
from sqlalchemy import create_engine, text

def adicionar_intervalo_almoco():
    """Adiciona coluna intervalo_almoco à tabela ordem_servico"""
    
    # Pega a URL do banco do .env ou usa SQLite local
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    if not DATABASE_URL:
        # Banco local
        DATABASE_URL = 'sqlite:///database/database.db'
        print("📊 Usando banco SQLite local")
    else:
        print("📊 Usando banco PostgreSQL (Render)")
        # Fix para Render: postgres:// -> postgresql://
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    print(f"🔗 Conectando ao banco...")
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Verifica se a coluna já existe
            if 'postgresql' in DATABASE_URL:
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='ordem_servico' AND column_name='intervalo_almoco'
                """))
            else:
                result = conn.execute(text("""
                    SELECT sql FROM sqlite_master 
                    WHERE type='table' AND name='ordem_servico'
                """))
                table_sql = result.fetchone()
                if table_sql and 'intervalo_almoco' in table_sql[0]:
                    print("✅ Coluna intervalo_almoco já existe!")
                    return
                result = None
            
            if result and result.fetchone():
                print("✅ Coluna intervalo_almoco já existe!")
                return
            
            # Adiciona a coluna
            print("➕ Adicionando coluna intervalo_almoco...")
            conn.execute(text("""
                ALTER TABLE ordem_servico 
                ADD COLUMN intervalo_almoco INTEGER DEFAULT 60
            """))
            conn.commit()
            
            print("✅ Coluna intervalo_almoco adicionada com sucesso!")
            print("   - Tipo: INTEGER")
            print("   - Default: 60 (minutos)")
            print("   - Descrição: Intervalo de almoço descontado do total de horas")
            
    except Exception as e:
        print(f"❌ Erro ao adicionar coluna: {e}")
        sys.exit(1)
    
    print("\n✅ Migração concluída!")

if __name__ == '__main__':
    print("=" * 60)
    print("🔧 MIGRAÇÃO: Adicionar coluna intervalo_almoco")
    print("=" * 60)
    adicionar_intervalo_almoco()
