#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Testa rota /energia-solar/ para identificar erro 500
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app import create_app
from app.extensoes import db

def testar():
    print("=" * 80)
    print("🔍 TESTE - ROTA /energia-solar/")
    print("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Verificar conexão
            print("\n1. Verificando conexão com banco...")
            from sqlalchemy import text
            result = db.session.execute(text('SELECT 1')).scalar()
            print(f"   ✅ Conexão OK: {result}")
            
            # 2. Verificar tabela CalculoEnergiaSolar
            print("\n2. Verificando tabela calculo_energia_solar...")
            from app.energia_solar.energia_solar_model import CalculoEnergiaSolar
            
            # Tentar importar
            print("   ✅ Model CalculoEnergiaSolar importado")
            
            # Verificar se tabela existe
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'calculo_energia_solar' in tables:
                print("   ✅ Tabela 'calculo_energia_solar' existe")
                
                # Verificar colunas
                columns = [col['name'] for col in inspector.get_columns('calculo_energia_solar')]
                print(f"   📋 Colunas ({len(columns)}): {', '.join(columns[:5])}...")
                
            else:
                print("   ❌ Tabela 'calculo_energia_solar' NÃO existe!")
                print("\n   🔧 Criando tabela...")
                db.create_all()
                print("   ✅ Tabelas criadas!")
            
            # 3. Tentar executar a query da rota
            print("\n3. Testando query da rota dashboard()...")
            try:
                calculos = CalculoEnergiaSolar.query.order_by(
                    CalculoEnergiaSolar.data_calculo.desc()
                ).limit(10).all()
                print(f"   ✅ Query executada: {len(calculos)} registros")
                
                # Estatísticas
                total_calculos = CalculoEnergiaSolar.query.count()
                print(f"   📊 Total de cálculos: {total_calculos}")
                
                potencia_total = db.session.query(
                    db.func.sum(CalculoEnergiaSolar.potencia_sistema)
                ).scalar() or 0
                print(f"   ⚡ Potência total: {potencia_total} kWp")
                
                economia_total = db.session.query(
                    db.func.sum(CalculoEnergiaSolar.economia_anual)
                ).scalar() or 0
                print(f"   💰 Economia total: R$ {economia_total}")
                
            except Exception as e:
                print(f"   ❌ ERRO na query: {e}")
                import traceback
                traceback.print_exc()
            
            # 4. Testar rota com test_client
            print("\n4. Testando rota HTTP...")
            with app.test_client() as client:
                # Primeiro fazer login
                response = client.post('/auth/login', data={
                    'usuario': 'admin',
                    'senha': 'admin123'
                }, follow_redirects=False)
                
                print(f"   Login status: {response.status_code}")
                
                # Testar rota
                response = client.get('/energia-solar/')
                print(f"   GET /energia-solar/ status: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"   ❌ ERRO: {response.data[:500]}")
                else:
                    print("   ✅ Rota OK!")
                    
        except Exception as e:
            print(f"\n❌ ERRO GERAL: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 80)
        print("✅ DIAGNÓSTICO CONCLUÍDO")
        print("=" * 80)

if __name__ == '__main__':
    testar()
