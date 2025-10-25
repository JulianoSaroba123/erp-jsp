# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Script de Debug
===============================

Script para debugar e testar a aplicação.
Útil para desenvolvimento e troubleshooting.

Autor: JSP Soluções
Data: 2025

Para executar:
    python scripts/debug_app.py
"""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.app import create_app
from app.extensoes import db

def debug_aplicacao():
    """
    Testa e exibe informações da aplicação.
    
    Útil para verificar se tudo está funcionando corretamente.
    """
    print("🐛 ERP JSP v3.0 - Debug da Aplicação")
    print("=" * 50)
    
    try:
        # Cria a aplicação
        app = create_app()
        
        print(f"✅ Aplicação criada com sucesso!")
        print(f"📍 Ambiente: {app.config.get('FLASK_ENV', 'desenvolvimento')}")
        print(f"🗄️  Banco: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        print(f"🔑 Debug: {app.config.get('DEBUG', False)}")
        print(f"🏢 Empresa: {app.config.get('COMPANY_NAME')}")
        print(f"📦 Versão: {app.config.get('SYSTEM_VERSION')}")
        
        with app.app_context():
            print("\n📊 Verificando banco de dados...")
            
            try:
                # Testa conexão com banco
                with db.engine.connect() as connection:
                    connection.execute(db.text('SELECT 1'))
                print("✅ Conexão com banco OK!")
                
                # Importa models
                from app.cliente.cliente_model import Cliente
                from app.fornecedor.fornecedor_model import Fornecedor
                from app.produto.produto_model import Produto
                
                # Verifica tabelas
                print("\n📋 Contagem de registros:")
                print(f"   Clientes: {Cliente.query.count()}")
                print(f"   Fornecedores: {Fornecedor.query.count()}")
                print(f"   Produtos: {Produto.query.count()}")
                
            except Exception as e:
                print(f"❌ Erro no banco: {str(e)}")
                print("💡 Execute: python scripts/criar_tabelas.py")
        
        print("\n🛣️  Rotas registradas:")
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                print(f"   {list(rule.methods)} {rule.rule} -> {rule.endpoint}")
        
        print("\n✅ Debug concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante debug: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def testar_imports():
    """Testa imports dos módulos principais."""
    print("\n🔍 Testando imports...")
    
    try:
        from app.app import create_app
        print("✅ app.app")
        
        from app.config import config
        print("✅ app.config")
        
        from app.extensoes import db
        print("✅ app.extensoes")
        
        from app.models import BaseModel
        print("✅ app.models")
        
        from app.cliente.cliente_model import Cliente
        from app.cliente.cliente_routes import cliente_bp
        print("✅ módulo cliente")
        
        from app.fornecedor.fornecedor_model import Fornecedor
        from app.fornecedor.fornecedor_routes import fornecedor_bp
        print("✅ módulo fornecedor")
        
        from app.produto.produto_model import Produto
        from app.produto.produto_routes import produto_bp
        print("✅ módulo produto")
        
        from app.painel.painel_routes import painel_bp
        print("✅ módulo painel")
        
        print("✅ Todos os imports OK!")
        return True
        
    except Exception as e:
        print(f"❌ Erro nos imports: {str(e)}")
        return False

if __name__ == '__main__':
    print("🚀 Iniciando debug completo...\n")
    
    # Testa imports primeiro
    if testar_imports():
        # Se imports OK, testa aplicação
        debug_aplicacao()
    else:
        print("❌ Falha nos imports. Verifique a estrutura do projeto.")
    
    print("\n🏁 Debug finalizado!")