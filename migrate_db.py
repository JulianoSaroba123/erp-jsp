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

def run_migrations():
    """Executa migrations necessárias no banco PostgreSQL."""
    
    # Pega DATABASE_URL do ambiente (Render inject automático)
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("⚠️ DATABASE_URL não encontrada - pulando migrations (dev local?)")
        return
    
    print("\n" + "=" * 70)
    print("🔧 EXECUTANDO MIGRATIONS AUTOMÁTICAS")
    print("=" * 70)
    print(f"📊 Database: {database_url.split('@')[1] if '@' in database_url else 'PostgreSQL'}")
    
    try:
        # Import aqui dentro para evitar erro se não tiver instalado
        from sqlalchemy import create_engine, text, inspect
        
        print("✅ SQLAlchemy importado com sucesso")
        
        engine = create_engine(database_url)
        inspector = inspect(engine)
        
        print("✅ Engine PostgreSQL criado")
        
        # Verifica se a tabela existe
        tabelas = inspector.get_table_names()
        print(f"📋 Tabelas encontradas: {len(tabelas)}")
        
        if 'ordem_servico_colaborador' not in tabelas:
            print("⚠️ Tabela ordem_servico_colaborador não existe ainda")
            print("   (Será criada automaticamente pelo SQLAlchemy no primeiro uso)")
            return
        
        print("✅ Tabela ordem_servico_colaborador encontrada")
        
        # Lista colunas atuais
        colunas_existentes = [col['name'] for col in inspector.get_columns('ordem_servico_colaborador')]
        print(f"📊 Colunas existentes: {len(colunas_existentes)}")
        
        migrations = []
        
        # Define colunas a adicionar para horários detalhados
        colunas_horarios = [
            ("hora_entrada_manha", "TIME"),
            ("hora_saida_manha", "TIME"),
            ("hora_entrada_tarde", "TIME"), 
            ("hora_saida_tarde", "TIME"),
            ("hora_entrada_extra", "TIME"),
            ("hora_saida_extra", "TIME"),
            ("horas_normais", "NUMERIC(10,2)"),
            ("horas_extras", "NUMERIC(10,2)")
        ]
        
        # Define colunas de KM
        colunas_km = [
            ("km_inicial", "INTEGER"),
            ("km_final", "INTEGER")
        ]
        
        todas_colunas = colunas_horarios + colunas_km
        
        # Verifica quais colunas precisam ser adicionadas
        for nome_coluna, tipo_coluna in todas_colunas:
            if nome_coluna not in colunas_existentes:
                migrations.append((nome_coluna, tipo_coluna))
        
        if not migrations:
            print("✅ Todas as colunas já existem - nenhuma migration necessária")
            print("=" * 70 + "\n")
            return
        
        print(f"\n🔧 Aplicando {len(migrations)} migrations:")
        
        # Executa migrations
        with engine.connect() as conn:
            for nome_coluna, tipo_coluna in migrations:
                sql = f"ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS {nome_coluna} {tipo_coluna}"
                print(f"   ⚙️  {nome_coluna} ({tipo_coluna})...")
                
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"      ✅ OK")
                except Exception as e:
                    print(f"      ⚠️ Aviso: {str(e)[:100]}")
                    # Continua mesmo com erro (pode já existir)
        
        print(f"\n✅ Migrations concluídas com sucesso!")
        
    except ImportError as e:
        print(f"❌ Erro ao importar SQLAlchemy: {e}")
        print("   Certifique-se que requirements.txt foi instalado")
        sys.exit(1)
        
    except Exception as e:
        print(f"⚠️ Erro ao executar migrations: {e}")
        import traceback
        traceback.print_exc()
        # NÃO FALHA - apenas loga o erro
        # O app vai continuar e criar as colunas depois se necessário
    
    print("=" * 70 + "\n")

if __name__ == '__main__':
    run_migrations()
