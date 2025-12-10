"""
🔍 DIAGNÓSTICO COMPLETO - Ordens de Serviço Render
===================================================

Script para verificar TUDO relacionado ao problema das OS.

Autor: JSP Soluções
Data: 2025-12-09
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.app import create_app
from app.extensoes import db
from sqlalchemy import text, inspect

app = create_app()

with app.app_context():
    print("="*80)
    print("🔍 DIAGNÓSTICO COMPLETO - ORDENS DE SERVIÇO")
    print("="*80)
    print()
    
    # 1. Verificar conexão do banco
    print("1️⃣ CONEXÃO DO BANCO:")
    print(f"   DATABASE_URL configurada: {bool(os.getenv('DATABASE_URL'))}")
    print(f"   SQLAlchemy URI: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
    print()
    
    # 2. Verificar tabelas
    print("2️⃣ TABELAS NO BANCO:")
    inspector = inspect(db.engine)
    tabelas = inspector.get_table_names()
    print(f"   Total de tabelas: {len(tabelas)}")
    
    if 'ordem_servico' in tabelas:
        print("   ✅ Tabela 'ordem_servico' existe")
    else:
        print("   ❌ Tabela 'ordem_servico' NÃO EXISTE!")
        print(f"   📋 Tabelas encontradas: {tabelas}")
    print()
    
    # 3. Verificar colunas da tabela ordem_servico
    if 'ordem_servico' in tabelas:
        print("3️⃣ COLUNAS DA TABELA ordem_servico:")
        colunas = inspector.get_columns('ordem_servico')
        for col in colunas[:10]:  # Primeiras 10 colunas
            print(f"   - {col['name']}: {col['type']}")
        print(f"   ... (total: {len(colunas)} colunas)")
        print()
    
    # 4. Query direta SQL
    print("4️⃣ QUERY DIRETA SQL:")
    try:
        result = db.session.execute(text("SELECT COUNT(*) FROM ordem_servico"))
        count = result.scalar()
        print(f"   Total de registros: {count}")
        
        if count > 0:
            result2 = db.session.execute(text("SELECT id, numero, titulo, ativo FROM ordem_servico LIMIT 5"))
            rows = result2.fetchall()
            print(f"   Primeiros 5 registros:")
            for row in rows:
                print(f"   - ID: {row[0]}, Número: {row[1]}, Título: {row[2]}, Ativo: {row[3]}")
    except Exception as e:
        print(f"   ❌ Erro ao executar query SQL: {e}")
    print()
    
    # 5. Query via ORM SQLAlchemy
    print("5️⃣ QUERY VIA ORM (SQLAlchemy):")
    try:
        from app.ordem_servico.ordem_servico_model import OrdemServico
        
        total_orm = OrdemServico.query.count()
        print(f"   Total via ORM: {total_orm}")
        
        if total_orm > 0:
            primeiras = OrdemServico.query.limit(5).all()
            print(f"   Primeiras 5 via ORM:")
            for os in primeiras:
                print(f"   - ID: {os.id}, Número: {os.numero}, Título: {os.titulo}, Ativo: {os.ativo}")
        else:
            print("   ⚠️ ORM retornou 0 registros!")
            
            # Debug adicional: verificar tablename
            print(f"\n   🔍 Model OrdemServico.__tablename__: {OrdemServico.__tablename__}")
            print(f"   🔍 Model OrdemServico.__table__.name: {OrdemServico.__table__.name}")
            
    except Exception as e:
        print(f"   ❌ Erro ao executar query ORM: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # 6. Verificar schema do banco
    print("6️⃣ SCHEMA DO BANCO:")
    try:
        result = db.session.execute(text("SELECT current_schema()"))
        schema = result.scalar()
        print(f"   Schema atual: {schema}")
        
        result2 = db.session.execute(text("SELECT schemaname, tablename FROM pg_tables WHERE tablename = 'ordem_servico'"))
        tables = result2.fetchall()
        if tables:
            for t in tables:
                print(f"   Tabela encontrada: {t[0]}.{t[1]}")
        else:
            print("   ❌ Tabela ordem_servico não encontrada em nenhum schema!")
    except Exception as e:
        print(f"   ⚠️ Não foi possível verificar schema: {e}")
    print()
    
    print("="*80)
    print("✅ DIAGNÓSTICO CONCLUÍDO")
    print("="*80)
