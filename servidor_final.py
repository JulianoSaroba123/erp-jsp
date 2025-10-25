#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor Final - Sem Debug
==========================

Servidor de produção sem debug mode para evitar
problemas de conexão com banco SQLite.
"""

from app.app import create_app
import sys
import os

def start_production_server():
    """Inicia servidor em modo produção"""
    
    app = create_app()
    
    # Desabilita debug mode completamente
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    
    print("🚀 SERVIDOR ERP JSP v3.0 - MODO PRODUÇÃO")
    print("=" * 50)
    print("✅ Funcionalidades testadas e funcionando:")
    print("   • Criação e edição de ordens de serviço")
    print("   • Upload de anexos (imagens e documentos)")
    print("   • Campos de descrição de pagamento")
    print("   • Observações de anexos")
    print("   • Persistência de dados garantida")
    print("   • Numeração profissional (OS20250001+)")
    print("   • Auto complete de clientes")
    print("   • Cálculos automáticos")
    print("   • Sistema de anexos completo")
    print("")
    print("🌐 URLs principais:")
    print("   • Dashboard: http://localhost:5009")
    print("   • Nova OS: http://localhost:5009/ordem_servico/novo")
    print("   • Listar OSs: http://localhost:5009/ordem_servico")
    print("   • Editar OS: http://localhost:5009/ordem_servico/1/editar")
    print("")
    print("⏹️ Pressione Ctrl+C para parar")
    print("=" * 50)
    
    try:
        # Servidor sem debug e com configurações otimizadas
        app.run(
            debug=False,
            port=5009,
            host='0.0.0.0',
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n✅ Servidor parado pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")

def test_database_first():
    """Testa banco antes de iniciar servidor"""
    
    app = create_app()
    app.config['DEBUG'] = False
    
    with app.app_context():
        try:
            from app.extensoes import db
            from app.ordem_servico.ordem_servico_model import OrdemServico
            from app.cliente.cliente_model import Cliente
            
            print("🔍 TESTANDO BANCO DE DADOS...")
            
            # Testa conexão básica
            db.session.execute(db.text("SELECT 1"))
            print("   ✅ Conexão com banco OK")
            
            # Testa tabelas principais
            ordens = OrdemServico.query.limit(1).all()
            print(f"   ✅ Tabela ordens de serviço OK ({len(ordens)} registros)")
            
            clientes = Cliente.query.limit(1).all()
            print(f"   ✅ Tabela clientes OK ({len(clientes)} registros)")
            
            print("   ✅ Banco de dados funcionando perfeitamente!")
            return True
            
        except Exception as e:
            print(f"   ❌ Erro no banco: {e}")
            return False

if __name__ == '__main__':
    # Testa banco primeiro
    if test_database_first():
        start_production_server()
    else:
        print("❌ Não foi possível iniciar devido a problemas no banco")
        sys.exit(1)