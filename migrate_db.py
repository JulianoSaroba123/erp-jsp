#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🔧 Script de Migração Automática para Render
=============================================
Adiciona colunas de horários detalhados e KM aos colaboradores de OS.
É IDEMPOTENTE - pode rodar várias vezes sem erro.
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect

def run_migrations():
    """Executa migrations necessárias no banco PostgreSQL."""
    
    # Pega DATABASE_URL do ambiente (Render inject automático)
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("⚠️ DATABASE_URL não encontrada, pulando migrations")
        return
    
    print("=" * 70)
    print("🔧 EXECUTANDO MIGRATIONS AUTOMÁTICAS")
    print("=" * 70)
    
    try:
        engine = create_engine(database_url)
        inspector = inspect(engine)
        
        # Verifica se a tabela existe
        if 'ordem_servico_colaborador' not in inspector.get_table_names():
            print("⚠️ Tabela ordem_servico_colaborador não existe ainda")
            print("   (Será criada automaticamente pelo SQLAlchemy)")
            return
        
        # Lista colunas atuais
        colunas_existentes = [col['name'] for col in inspector.get_columns('ordem_servico_colaborador')]
        
        migrations = []
        
        # Define colunas a adicionar para horários detalhados
        colunas_horarios = [
            "hora_entrada_manha TIME",
            "hora_saida_manha TIME",
            "hora_entrada_tarde TIME", 
            "hora_saida_tarde TIME",
            "hora_entrada_extra TIME",
            "hora_saida_extra TIME",
            "horas_normais NUMERIC(10,2)",
            "horas_extras NUMERIC(10,2)"
        ]
        
        # Define colunas de KM
        colunas_km = [
            "km_inicial INTEGER",
            "km_final INTEGER"
        ]
        
        todas_colunas = colunas_horarios + colunas_km
        
        # Verifica quais colunas precisam ser adicionadas
        for coluna_def in todas_colunas:
            nome_coluna = coluna_def.split()[0]
            
            if nome_coluna not in colunas_existentes:
                migrations.append(
                    f"ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS {coluna_def}"
                )
        
        if not migrations:
            print("✅ Todas as colunas já existem - nenhuma migration necessária")
            return
        
        # Executa migrations
        with engine.connect() as conn:
            for sql in migrations:
                print(f"   🔧 {sql[:80]}...")
                conn.execute(text(sql))
                conn.commit()
        
        print(f"✅ {len(migrations)} migration(s) executada(s) com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao executar migrations: {e}")
        # NÃO FALHA - apenas loga o erro
        # O app vai continuar e criar as colunas depois se necessário
    
    print("=" * 70)

if __name__ == '__main__':
    run_migrations()
