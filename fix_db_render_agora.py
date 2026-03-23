#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX EMERGENCIAL - Adiciona colunas faltantes no PostgreSQL do Render
Execute: python fix_db_render_agora.py
"""

import os
import sys

def fix_database():
    """Adiciona todas as colunas faltantes."""
    
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL não encontrada!")
        print("   Este script deve ser executado no Render Shell")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("🔧 FIX EMERGENCIAL - ADICIONANDO COLUNAS FALTANTES")
    print("=" * 70)
    
    try:
        import psycopg
        
        print("✅ Conectando ao PostgreSQL...")
        conn = psycopg.connect(database_url)
        cursor = conn.cursor()
        
        # Colunas para ordem_servico
        colunas_os = [
            "ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS intervalo_almoco INTEGER DEFAULT 60",
            "ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS hora_entrada_manha TIME",
            "ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS hora_saida_almoco TIME",
            "ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS hora_retorno_almoco TIME",
            "ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS hora_saida TIME",
            "ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS hora_entrada_extra TIME",
            "ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS hora_saida_extra TIME",
            "ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS horas_normais NUMERIC(10,2)",
            "ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS horas_extras NUMERIC(10,2)",
        ]
        
        # Colunas para ordem_servico_colaborador
        colunas_colab = [
            "ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS hora_entrada_manha TIME",
            "ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS hora_saida_manha TIME",
            "ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS hora_entrada_tarde TIME",
            "ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS hora_saida_tarde TIME",
            "ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS hora_entrada_extra TIME",
            "ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS hora_saida_extra TIME",
            "ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS horas_normais NUMERIC(10,2)",
            "ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS horas_extras NUMERIC(10,2)",
            "ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS km_inicial INTEGER",
            "ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS km_final INTEGER",
        ]
        
        todas = colunas_os + colunas_colab
        
        print(f"\n🔧 Aplicando {len(todas)} comandos SQL...\n")
        
        for i, sql in enumerate(todas, 1):
            # Extrai nome da tabela e coluna para exibição
            partes = sql.split()
            tabela = partes[2]
            coluna = partes[8]
            
            print(f"   [{i:02d}/{len(todas)}] {tabela}.{coluna}...", end=" ")
            
            try:
                cursor.execute(sql)
                conn.commit()
                print("✅")
            except Exception as e:
                print(f"⚠️ {str(e)[:50]}")
        
        print("\n✅ Todas as colunas foram adicionadas com sucesso!")
        print("=" * 70)
        
        cursor.close()
        conn.close()
        
        print("\n🎯 Próximo passo: Reinicie o serviço no Render Dashboard")
        print()
        
    except ImportError:
        print("❌ Biblioteca psycopg não encontrada!")
        print("   Execute: pip install psycopg[binary]")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    fix_database()
