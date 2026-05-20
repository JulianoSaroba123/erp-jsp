"""
Script para adicionar campos financeiros ao modelo CalculoEnergiaSolar
Campos: concessionaria_id, tarifa_kwh, aliquota_fio_b
"""
import os
import sys

# Configurar path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault('FLASK_ENV', 'production')

from app import create_app
from app.extensoes import db
from sqlalchemy import text, inspect

def adicionar_campos_financeiros():
    """Adiciona campos financeiros ao projeto solar"""
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        colunas_existentes = [col['name'] for col in inspector.get_columns('calculo_energia_solar')]
        
        print("=" * 70)
        print("🔧 ADICIONAR CAMPOS FINANCEIROS AO PROJETO SOLAR")
        print("=" * 70)
        print(f"\n📊 Total de colunas existentes: {len(colunas_existentes)}\n")
        
        campos_adicionar = {
            'concessionaria_id': 'INTEGER',  # FK para concessionária
            'tarifa_kwh': 'NUMERIC(10,4)',   # Tarifa final com impostos (R$/kWh)
            'aliquota_fio_b': 'NUMERIC(5,2)' # % de impostos (PIS+COFINS+ICMS)
        }
        
        campos_adicionados = 0
        
        for campo, tipo_sql in campos_adicionar.items():
            if campo not in colunas_existentes:
                try:
                    sql = f"ALTER TABLE calculo_energia_solar ADD COLUMN {campo} {tipo_sql}"
                    db.session.execute(text(sql))
                    db.session.commit()
                    print(f"   ✅ Coluna '{campo}' adicionada ({tipo_sql})")
                    campos_adicionados += 1
                except Exception as e:
                    print(f"   ❌ Erro ao adicionar '{campo}': {e}")
                    db.session.rollback()
            else:
                print(f"   ⏭️ Coluna '{campo}' já existe")
        
        # Adicionar FK para concessionaria (se tabela existir)
        try:
            # Verificar se tabela concessionaria existe
            tabelas = inspector.get_table_names()
            if 'concessionaria' in tabelas:
                # Tentar adicionar FK (pode falhar se já existir)
                sql_fk = """
                ALTER TABLE calculo_energia_solar 
                ADD CONSTRAINT fk_projeto_concessionaria 
                FOREIGN KEY (concessionaria_id) 
                REFERENCES concessionaria(id)
                """
                db.session.execute(text(sql_fk))
                db.session.commit()
                print("\n   🔗 Foreign Key adicionada: concessionaria_id -> concessionaria(id)")
            else:
                print("\n   ⚠️ Tabela 'concessionaria' não encontrada, FK não criada")
        except Exception as e:
            # FK pode já existir ou dar erro de sintaxe
            if 'already exists' not in str(e).lower():
                print(f"\n   ℹ️ FK não adicionada: {str(e)[:100]}")
            db.session.rollback()
        
        print("\n" + "=" * 70)
        print(f"✅ MIGRAÇÃO CONCLUÍDA!")
        print(f"   📊 {campos_adicionados} novos campos adicionados")
        print("=" * 70)
        
        # Verificar colunas atualizadas
        inspector = inspect(db.engine)
        colunas_atuais = [col['name'] for col in inspector.get_columns('calculo_energia_solar')]
        print(f"\n📋 Total de colunas agora: {len(colunas_atuais)}")
        
        # Verificar se os campos estão presentes
        print("\n🔍 Verificando campos financeiros:")
        for campo in campos_adicionar.keys():
            status = "✅ OK" if campo in colunas_atuais else "❌ FALTANDO"
            print(f"   {status} - {campo}")

if __name__ == '__main__':
    adicionar_campos_financeiros()
