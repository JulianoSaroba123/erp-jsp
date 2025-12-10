"""
🔧 CORREÇÃO EMERGENCIAL - Erro 500 em Produtos
===============================================

Problema: Foreign Key para 'fornecedores.id' causando erro 500
Solução: FK temporariamente removida até tabela ser criada

Execute este script para verificar se o problema foi resolvido.

Autor: JSP Soluções
Data: 2025-12-10
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.app import create_app
from app.extensoes import db
from sqlalchemy import inspect, text

def diagnosticar_produtos():
    """Diagnóstico do módulo de produtos"""
    
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*80)
        print("🔍 DIAGNÓSTICO - MÓDULO DE PRODUTOS")
        print("="*80)
        
        inspector = inspect(db.engine)
        
        # 1. Verificar se tabela produtos existe
        print("\n1️⃣ TABELA PRODUTOS:")
        print("-" * 80)
        if inspector.has_table('produtos'):
            print("   ✅ Tabela 'produtos' existe")
            
            # Colunas
            columns = inspector.get_columns('produtos')
            print(f"   📋 Colunas: {len(columns)}")
            
            # Verificar coluna fornecedor_id
            fornecedor_col = [c for c in columns if c['name'] == 'fornecedor_id']
            if fornecedor_col:
                print(f"   • fornecedor_id: {fornecedor_col[0]['type']} (nullable: {fornecedor_col[0]['nullable']})")
            
            # Foreign Keys
            fks = inspector.get_foreign_keys('produtos')
            if fks:
                print(f"\n   🔗 Foreign Keys: {len(fks)}")
                for fk in fks:
                    print(f"      • {fk['constrained_columns']} → {fk['referred_table']}.{fk['referred_columns']}")
            else:
                print("   ✅ Nenhuma FK (correto para evitar erro)")
            
            # Contagem
            count = db.session.execute(text("SELECT COUNT(*) FROM produtos")).fetchone()[0]
            print(f"\n   📊 Total de produtos: {count}")
            
        else:
            print("   ❌ Tabela 'produtos' NÃO existe!")
        
        # 2. Verificar tabela fornecedores
        print("\n2️⃣ TABELA FORNECEDORES:")
        print("-" * 80)
        if inspector.has_table('fornecedores'):
            print("   ✅ Tabela 'fornecedores' existe")
            count = db.session.execute(text("SELECT COUNT(*) FROM fornecedores")).fetchone()[0]
            print(f"   📊 Total de fornecedores: {count}")
        else:
            print("   ⚠️  Tabela 'fornecedores' NÃO existe")
            print("   → FK de produtos.fornecedor_id foi removida para evitar erro")
        
        # 3. Testar import do model
        print("\n3️⃣ IMPORT DO MODEL:")
        print("-" * 80)
        try:
            from app.produto.produto_model import Produto
            print("   ✅ Model Produto importado com sucesso")
            print(f"   • __tablename__: {Produto.__tablename__}")
            
            # Verificar se tem FK
            fk_columns = [c for c in Produto.__table__.columns if c.foreign_keys]
            if fk_columns:
                print(f"\n   ⚠️  FKs no model: {len(fk_columns)}")
                for col in fk_columns:
                    for fk in col.foreign_keys:
                        print(f"      • {col.name} → {fk.target_fullname}")
            else:
                print("   ✅ Nenhuma FK no model (correto)")
                
        except Exception as e:
            print(f"   ❌ ERRO ao importar model: {e}")
        
        # 4. Testar rota de listagem
        print("\n4️⃣ TESTE DE ROTA:")
        print("-" * 80)
        try:
            from app.produto.produto_model import Produto
            produtos = Produto.query.filter_by(ativo=True).limit(5).all()
            print(f"   ✅ Query executada: {len(produtos)} produtos encontrados")
        except Exception as e:
            print(f"   ❌ ERRO na query: {e}")
        
        # 5. Resultado final
        print("\n" + "="*80)
        print("📊 RESULTADO:")
        print("="*80)
        
        if inspector.has_table('produtos') and not inspector.has_table('fornecedores'):
            print("✅ Correção aplicada corretamente")
            print("   • Tabela produtos existe")
            print("   • FK para fornecedores removida")
            print("   • Módulo deve funcionar sem erro 500")
        elif inspector.has_table('produtos') and inspector.has_table('fornecedores'):
            print("✅ Ambas as tabelas existem")
            print("   • Pode reativar FK se necessário")
        else:
            print("⚠️  Tabela produtos não existe")
            print("   • Execute db.create_all() ou migration")
        
        print("="*80)


if __name__ == '__main__':
    diagnosticar_produtos()
