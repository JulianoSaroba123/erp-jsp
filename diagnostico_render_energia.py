#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para Energia Solar no Render
Verifica tabelas, modelos e rotas
"""

import os
import sys

# Adiciona o diretório ao path
sys.path.insert(0, os.path.dirname(__file__))

def diagnosticar():
    print("=" * 80)
    print("DIAGNÓSTICO MÓDULO ENERGIA SOLAR - RENDER")
    print("=" * 80)
    
    try:
        print("\n1. Carregando configuração...")
        from app.config import config
        config_name = os.environ.get('FLASK_ENV', 'production')
        print(f"   ✅ Ambiente: {config_name}")
        
        print("\n2. Importando extensões...")
        from app.extensoes import db
        print("   ✅ db importado")
        
        print("\n3. Criando app...")
        from app.app import create_app
        app = create_app(config_name)
        print("   ✅ App criado")
        
        with app.app_context():
            print("\n4. Verificando conexão com banco...")
            from sqlalchemy import text
            result = db.session.execute(text("SELECT 1")).scalar()
            print(f"   ✅ Conexão OK: {result}")
            
            print("\n5. Listando tabelas existentes...")
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tabelas = inspector.get_table_names()
            print(f"   📋 Total de tabelas: {len(tabelas)}")
            
            tabelas_energia = [t for t in tabelas if 'concession' in t or 'orcamento' in t or 'solar' in t]
            if tabelas_energia:
                print("   ✅ Tabelas de Energia Solar encontradas:")
                for t in tabelas_energia:
                    print(f"      - {t}")
            else:
                print("   ❌ NENHUMA tabela de Energia Solar encontrada!")
            
            print("\n6. Tentando importar models...")
            try:
                from app.concessionaria.concessionaria_model import Concessionaria
                print("   ✅ Concessionaria importada")
            except Exception as e:
                print(f"   ❌ ERRO ao importar Concessionaria: {e}")
            
            try:
                from app.energia_solar.orcamento_model import OrcamentoItem
                print("   ✅ OrcamentoItem importada")
            except Exception as e:
                print(f"   ❌ ERRO ao importar OrcamentoItem: {e}")
            
            print("\n7. Tentando importar rotas...")
            try:
                from app.energia_solar.energia_solar_routes import energia_solar_bp
                print(f"   ✅ Blueprint energia_solar_bp importado")
                print(f"      Rotas: {len(energia_solar_bp.url_map._rules) if hasattr(energia_solar_bp, 'url_map') else 'N/A'}")
            except Exception as e:
                print(f"   ❌ ERRO ao importar energia_solar_bp: {e}")
                import traceback
                traceback.print_exc()
            
            try:
                from app.concessionaria.concessionaria_routes import concessionaria_bp
                print(f"   ✅ Blueprint concessionaria_bp importado")
            except Exception as e:
                print(f"   ❌ ERRO ao importar concessionaria_bp: {e}")
                import traceback
                traceback.print_exc()
            
            print("\n8. Criando tabelas se necessário...")
            try:
                db.create_all()
                print("   ✅ db.create_all() executado")
            except Exception as e:
                print(f"   ❌ ERRO em create_all: {e}")
            
            print("\n9. Verificando tabelas novamente...")
            inspector = inspect(db.engine)
            tabelas = inspector.get_table_names()
            tabelas_energia = [t for t in tabelas if 'concession' in t or 'orcamento' in t or 'solar' in t]
            if tabelas_energia:
                print("   ✅ Tabelas criadas:")
                for t in tabelas_energia:
                    colunas = [c['name'] for c in inspector.get_columns(t)]
                    print(f"      - {t}: {len(colunas)} colunas")
            
            print("\n10. Testando rota /energia-solar/projetos...")
            try:
                with app.test_client() as client:
                    # Simula login (se necessário)
                    response = client.get('/energia-solar/projetos')
                    print(f"   Status Code: {response.status_code}")
                    if response.status_code != 200:
                        print(f"   ❌ Resposta: {response.data[:500]}")
                    else:
                        print("   ✅ Rota OK")
            except Exception as e:
                print(f"   ❌ ERRO ao testar rota: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 80)
        print("DIAGNÓSTICO CONCLUÍDO")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    diagnosticar()
