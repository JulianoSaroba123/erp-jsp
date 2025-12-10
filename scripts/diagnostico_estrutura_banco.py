"""
🔍 DIAGNÓSTICO COMPLETO - Estrutura de Banco de Dados
======================================================

Verifica tabelas, foreign keys e registros órfãos no PostgreSQL.
Identifica inconsistências entre models e banco real.

Autor: JSP Soluções
Data: 2025-12-10
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.app import create_app
from app.extensoes import db
from sqlalchemy import inspect, text

def diagnosticar_banco():
    """Diagnóstico completo do banco de dados"""
    
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*80)
        print("🔍 DIAGNÓSTICO DO BANCO DE DADOS")
        print("="*80)
        
        # 1. INFORMAÇÕES DA CONEXÃO
        print("\n1️⃣ CONEXÃO:")
        print("-" * 80)
        db_url = str(db.engine.url)
        if 'postgresql' in db_url:
            print(f"   ✅ PostgreSQL (Render)")
            print(f"   Host: {db.engine.url.host}")
            print(f"   Database: {db.engine.url.database}")
        else:
            print(f"   ⚠️  SQLite Local")
            print(f"   Path: {db_url}")
        
        inspector = inspect(db.engine)
        
        # 2. TABELAS RELACIONADAS A PROPOSTA
        print("\n2️⃣ TABELAS (PROPOSTA*):")
        print("-" * 80)
        all_tables = inspector.get_table_names()
        proposta_tables = [t for t in all_tables if 'proposta' in t.lower()]
        
        if proposta_tables:
            for table in sorted(proposta_tables):
                count = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
                print(f"   • {table:30} {count:5} registros")
        else:
            print("   ❌ Nenhuma tabela 'proposta*' encontrada!")
        
        # 3. FOREIGN KEYS DE ORDEM_SERVICO
        print("\n3️⃣ FOREIGN KEYS - ordem_servico:")
        print("-" * 80)
        try:
            fks = inspector.get_foreign_keys('ordem_servico')
            for fk in fks:
                print(f"   • ordem_servico.{fk['constrained_columns'][0]:20} → {fk['referred_table']}.{fk['referred_columns'][0]}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        # 4. FOREIGN KEYS DE PROPOSTAS (se existir)
        for table_name in ['propostas', 'proposta']:
            if table_name in all_tables:
                print(f"\n4️⃣ FOREIGN KEYS - {table_name}:")
                print("-" * 80)
                try:
                    fks = inspector.get_foreign_keys(table_name)
                    if fks:
                        for fk in fks:
                            print(f"   • {table_name}.{fk['constrained_columns'][0]:20} → {fk['referred_table']}.{fk['referred_columns'][0]}")
                    else:
                        print("   ⚠️  Nenhuma foreign key encontrada")
                except Exception as e:
                    print(f"   ❌ Erro: {e}")
        
        # 5. REGISTROS ÓRFÃOS - ORDEM_SERVICO
        print("\n5️⃣ ÓRFÃOS - ordem_servico:")
        print("-" * 80)
        
        # Órfãos de cliente
        query_orfaos_cliente = text("""
            SELECT COUNT(*) 
            FROM ordem_servico 
            WHERE cliente_id NOT IN (SELECT id FROM clientes)
        """)
        orfaos_cliente = db.session.execute(query_orfaos_cliente).fetchone()[0]
        status = "❌" if orfaos_cliente > 0 else "✅"
        print(f"   {status} Cliente inválido: {orfaos_cliente} registro(s)")
        
        # Órfãos de proposta (em tabelas que existam)
        for table_name in ['propostas', 'proposta']:
            if table_name in all_tables:
                query_orfaos_proposta = text(f"""
                    SELECT COUNT(*) 
                    FROM ordem_servico 
                    WHERE proposta_id IS NOT NULL 
                      AND proposta_id NOT IN (SELECT id FROM {table_name})
                """)
                orfaos_proposta = db.session.execute(query_orfaos_proposta).fetchone()[0]
                status = "❌" if orfaos_proposta > 0 else "✅"
                print(f"   {status} Proposta inválida ({table_name}): {orfaos_proposta} registro(s)")
        
        # 6. REGISTROS ÓRFÃOS - PROPOSTAS
        for table_name in ['propostas', 'proposta']:
            if table_name in all_tables:
                print(f"\n6️⃣ ÓRFÃOS - {table_name}:")
                print("-" * 80)
                
                query_orfaos_cliente = text(f"""
                    SELECT COUNT(*) 
                    FROM {table_name} 
                    WHERE cliente_id NOT IN (SELECT id FROM clientes)
                """)
                orfaos_cliente = db.session.execute(query_orfaos_cliente).fetchone()[0]
                status = "❌" if orfaos_cliente > 0 else "✅"
                print(f"   {status} Cliente inválido: {orfaos_cliente} registro(s)")
        
        # 7. MODELS DO FLASK
        print("\n7️⃣ MODELS DO FLASK:")
        print("-" * 80)
        try:
            from app.proposta.proposta_model import Proposta
            print(f"   • Proposta.__tablename__ = '{Proposta.__tablename__}'")
            
            from app.ordem_servico.ordem_servico_model import OrdemServico
            print(f"   • OrdemServico.__tablename__ = '{OrdemServico.__tablename__}'")
            
            # Verificar FKs nos models
            print("\n   Foreign Keys nos Models:")
            for column in OrdemServico.__table__.columns:
                if column.foreign_keys:
                    for fk in column.foreign_keys:
                        print(f"      • OrdemServico.{column.name} → {fk.target_fullname}")
        except Exception as e:
            print(f"   ❌ Erro ao importar models: {e}")
        
        # 8. CONTAGENS GERAIS
        print("\n8️⃣ CONTAGENS:")
        print("-" * 80)
        try:
            total_clientes = db.session.execute(text("SELECT COUNT(*) FROM clientes")).fetchone()[0]
            total_os = db.session.execute(text("SELECT COUNT(*) FROM ordem_servico")).fetchone()[0]
            
            print(f"   • Clientes: {total_clientes}")
            print(f"   • Ordem Serviço: {total_os}")
            
            for table_name in ['propostas', 'proposta']:
                if table_name in all_tables:
                    total = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).fetchone()[0]
                    print(f"   • {table_name.capitalize()}: {total}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        # 9. RESUMO FINAL
        print("\n" + "="*80)
        print("📊 RESUMO:")
        print("="*80)
        
        problemas = []
        
        if 'propostas' not in all_tables and 'proposta' not in all_tables:
            problemas.append("❌ Nenhuma tabela de propostas encontrada")
        elif 'propostas' in all_tables and 'proposta' in all_tables:
            problemas.append("⚠️  DUPLICAÇÃO: Existem 'proposta' E 'propostas'")
        
        if orfaos_cliente > 0:
            problemas.append(f"❌ {orfaos_cliente} OS órfãs (cliente inválido)")
        
        if problemas:
            print("\n⚠️  PROBLEMAS IDENTIFICADOS:")
            for p in problemas:
                print(f"   {p}")
        else:
            print("\n✅ Nenhum problema crítico identificado")
        
        print("="*80)


if __name__ == '__main__':
    diagnosticar_banco()
