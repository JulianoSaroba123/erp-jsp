#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CREATE ALL TABLES + MIGRATIONS - Solução completa
"""

import os
import sys

# Adiciona path do app
sys.path.insert(0, '/opt/render/project/src')

def setup_database():
    """Cria tabelas E adiciona colunas faltantes."""
    
    print("\n" + "=" * 70)
    print("🔨 SETUP COMPLETO DO BANCO DE DADOS")
    print("=" * 70)
    
    try:
        from app.app import create_app
        from app.extensoes import db
        from sqlalchemy import text, inspect
        
        print("✅ Importando app...")
        app = create_app()
        
        with app.app_context():
            print("✅ Verificando schema...")
            
            # Passo 1: Cria tabelas que não existem
            print("\n📋 Passo 1: Criando tabelas novas...")
            db.create_all()
            print("✅ Tabelas criadas")
            
            # Passo 2: Adiciona colunas faltantes
            print("\n📋 Passo 2: Adicionando colunas faltantes...")
            
            inspector = inspect(db.engine)
            tabelas = inspector.get_table_names()
            
            migrations_executadas = 0
            
            # Migrations para ordem_servico
            if 'ordem_servico' in tabelas:
                print("   🔍 Verificando ordem_servico...")
                colunas_existentes = [col['name'] for col in inspector.get_columns('ordem_servico')]
                
                migrations_os = [
                    ("intervalo_almoco", "INTEGER DEFAULT 60"),
                    ("hora_entrada_manha", "TIME"),
                    ("hora_saida_almoco", "TIME"),
                    ("hora_retorno_almoco", "TIME"),
                    ("hora_saida", "TIME"),
                    ("hora_entrada_extra", "TIME"),
                    ("hora_saida_extra", "TIME"),
                    ("horas_normais", "NUMERIC(10,2)"),
                    ("horas_extras", "NUMERIC(10,2)")
                ]
                
                for coluna, tipo in migrations_os:
                    if coluna not in colunas_existentes:
                        sql = f"ALTER TABLE ordem_servico ADD COLUMN {coluna} {tipo}"
                        print(f"      + Adicionando {coluna}...")
                        try:
                            db.session.execute(text(sql))
                            db.session.commit()
                            migrations_executadas += 1
                        except Exception as e:
                            print(f"        ⚠️ {str(e)[:80]}")
                            db.session.rollback()
            
            # Migrations para ordem_servico_colaborador
            if 'ordem_servico_colaborador' in tabelas:
                print("   🔍 Verificando ordem_servico_colaborador...")
                colunas_existentes = [col['name'] for col in inspector.get_columns('ordem_servico_colaborador')]
                
                migrations_colab = [
                    ("hora_entrada_manha", "TIME"),
                    ("hora_saida_manha", "TIME"),
                    ("hora_entrada_tarde", "TIME"),
                    ("hora_saida_tarde", "TIME"),
                    ("hora_entrada_extra", "TIME"),
                    ("hora_saida_extra", "TIME"),
                    ("horas_normais", "NUMERIC(10,2)"),
                    ("horas_extras", "NUMERIC(10,2)"),
                    ("km_inicial", "INTEGER"),
                    ("km_final", "INTEGER")
                ]
                
                for coluna, tipo in migrations_colab:
                    if coluna not in colunas_existentes:
                        sql = f"ALTER TABLE ordem_servico_colaborador ADD COLUMN {coluna} {tipo}"
                        print(f"      + Adicionando {coluna}...")
                        try:
                            db.session.execute(text(sql))
                            db.session.commit()
                            migrations_executadas += 1
                        except Exception as e:
                            print(f"        ⚠️ {str(e)[:80]}")
                            db.session.rollback()
            
            print(f"\n✅ Setup concluído! {migrations_executadas} migration(s) aplicada(s)")
            print("=" * 70 + "\n")
            
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 70 + "\n")
        sys.exit(1)

if __name__ == '__main__':
    setup_database()

