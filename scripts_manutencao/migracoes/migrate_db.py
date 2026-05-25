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
        
        # Define colunas a adicionar para horários detalhados (colaboradores)
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
        
        # === MIGRAÇÃO ADICIONAL: Verificar tabela ordem_servico ===
        if 'ordem_servico' in tabelas:
            print("✅ Verificando tabela ordem_servico...")
            
            colunas_os = [col['name'] for col in inspector.get_columns('ordem_servico')]
            
            # Colunas adicionais que podem estar faltando
            colunas_adicionais_os = [
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
            
            for nome_col, tipo_col in colunas_adicionais_os:
                if nome_col not in colunas_os:
                    print(f"   ⚠️  Coluna {nome_col} faltando em ordem_servico - adicionando...")
                    migrations.append((nome_col, tipo_col, 'ordem_servico'))
        
        if not migrations:
            print("✅ Todas as colunas já existem - nenhuma migration necessária")
            print("=" * 70 + "\n")
            return
        
        print(f"\n🔧 Aplicando {len(migrations)} migrations:")
        
        # Executa migrations
        with engine.connect() as conn:
            for migration in migrations:
                # Pode ter 2 elementos (coluna, tipo) ou 3 (coluna, tipo, tabela)
                if len(migration) == 3:
                    nome_coluna, tipo_coluna, tabela = migration
                else:
                    nome_coluna, tipo_coluna = migration
                    tabela = 'ordem_servico_colaborador'
                
                sql = f"ALTER TABLE {tabela} ADD COLUMN IF NOT EXISTS {nome_coluna} {tipo_coluna}"
                print(f"   ⚙️  {tabela}.{nome_coluna} ({tipo_coluna})...")
                
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"      ✅ OK")
                except Exception as e:
                    print(f"      ⚠️ Aviso: {str(e)[:100]}")
                    # Continua mesmo com erro (pode já existir)
        
        print(f"\n✅ Migrations concluídas com sucesso!")
        
    except ImportError as e:
        print(f"\n❌ ERRO CRÍTICO: Não foi possível importar SQLAlchemy!")
        print(f"   Detalhes: {e}")
        print(f"   Verifique se requirements.txt foi instalado corretamente")
        print("=" * 70 + "\n")
        # FALHA HARD - não pode continuar sem SQLAlchemy
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO ao executar migrations!")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensagem: {e}")
        print("\n📋 Traceback completo:")
        import traceback
        traceback.print_exc()
        print("=" * 70 + "\n")
        # FALHA HARD - migrations são obrigatórias
        sys.exit(1)

if __name__ == '__main__':
    run_migrations()
