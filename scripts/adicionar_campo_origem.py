# -*- coding: utf-8 -*-
"""
Script para adicionar campo 'origem' e 'custo_fixo_id' 
na tabela lancamentos_financeiros.

Permite distinguir a origem de cada lançamento financeiro.
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import app
from app.extensoes import db
from sqlalchemy import text

def adicionar_campo_origem():
    """Adiciona campos origem e custo_fixo_id se não existirem."""
    with app.app_context():
        try:
            print("🔄 Verificando campos na tabela lancamentos_financeiros...")
            
            # Detectar tipo de banco
            is_postgres = 'postgresql' in str(db.engine.url)
            
            if is_postgres:
                # PostgreSQL
                # Verificar se a coluna 'origem' existe
                result = db.session.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_name='lancamentos_financeiros' 
                    AND column_name='origem'
                """))
                origem_exists = result.scalar() > 0
                
                if not origem_exists:
                    print("➕ Adicionando coluna 'origem' (PostgreSQL)...")
                    db.session.execute(text("""
                        ALTER TABLE lancamentos_financeiros 
                        ADD COLUMN origem VARCHAR(50) DEFAULT 'MANUAL'
                    """))
                    print("✅ Coluna 'origem' adicionada com sucesso!")
                else:
                    print("✔️  Coluna 'origem' já existe.")
                
                # Verificar se a coluna 'custo_fixo_id' existe
                result = db.session.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_name='lancamentos_financeiros' 
                    AND column_name='custo_fixo_id'
                """))
                custo_fixo_id_exists = result.scalar() > 0
                
                if not custo_fixo_id_exists:
                    print("➕ Adicionando coluna 'custo_fixo_id' (PostgreSQL)...")
                    db.session.execute(text("""
                        ALTER TABLE lancamentos_financeiros 
                        ADD COLUMN custo_fixo_id INTEGER 
                        REFERENCES custos_fixos(id)
                    """))
                    print("✅ Coluna 'custo_fixo_id' adicionada com sucesso!")
                else:
                    print("✔️  Coluna 'custo_fixo_id' já existe.")
                
            else:
                # SQLite
                # Verificar se a coluna 'origem' existe
                result = db.session.execute(text("""
                    SELECT COUNT(*) 
                    FROM pragma_table_info('lancamentos_financeiros') 
                    WHERE name='origem'
                """))
                origem_exists = result.scalar() > 0
                
                if not origem_exists:
                    print("➕ Adicionando coluna 'origem' (SQLite)...")
                    db.session.execute(text("""
                        ALTER TABLE lancamentos_financeiros 
                        ADD COLUMN origem VARCHAR(50) DEFAULT 'MANUAL'
                    """))
                    print("✅ Coluna 'origem' adicionada com sucesso!")
                else:
                    print("✔️  Coluna 'origem' já existe.")
                
                # Verificar se a coluna 'custo_fixo_id' existe
                result = db.session.execute(text("""
                    SELECT COUNT(*) 
                    FROM pragma_table_info('lancamentos_financeiros') 
                    WHERE name='custo_fixo_id'
                """))
                custo_fixo_id_exists = result.scalar() > 0
                
                if not custo_fixo_id_exists:
                    print("➕ Adicionando coluna 'custo_fixo_id' (SQLite)...")
                    db.session.execute(text("""
                        ALTER TABLE lancamentos_financeiros 
                        ADD COLUMN custo_fixo_id INTEGER
                    """))
                    print("✅ Coluna 'custo_fixo_id' adicionada com sucesso!")
                else:
                    print("✔️  Coluna 'custo_fixo_id' já existe.")
            
            # Atualizar lançamentos existentes sem origem
            print("\n🔄 Atualizando lançamentos existentes...")
            db.session.execute(text("""
                UPDATE lancamentos_financeiros 
                SET origem = 'MANUAL' 
                WHERE origem IS NULL
            """))
            
            db.session.commit()
            print("✅ Campos adicionados e dados atualizados com sucesso!")
            
            # Exibir estatísticas
            print("\n📊 Estatísticas:")
            result = db.session.execute(text("""
                SELECT origem, COUNT(*) as total
                FROM lancamentos_financeiros
                WHERE ativo = true
                GROUP BY origem
            """))
            
            for row in result:
                print(f"   • {row[0]}: {row[1]} lançamento(s)")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao adicionar campos: {str(e)}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("🔧 ADICIONAR CAMPO ORIGEM EM LANÇAMENTOS FINANCEIROS")
    print("=" * 60)
    print()
    
    sucesso = adicionar_campo_origem()
    
    print()
    if sucesso:
        print("✅ Script executado com sucesso!")
        print()
        print("📝 Próximos passos:")
        print("   1. Agora você pode distinguir lançamentos manuais de custos fixos")
        print("   2. Novos lançamentos de custos fixos terão origem='CUSTO_FIXO'")
        print("   3. Lançamentos manuais terão origem='MANUAL'")
    else:
        print("❌ Ocorreram erros durante a execução.")
    
    print("=" * 60)
