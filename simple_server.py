#!/usr/bin/env python3
"""Servidor simples para testar ordem de serviço."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from app.app import create_app

def create_simple_server():
    """Cria servidor simples para teste."""
    print("🔧 Criando servidor simples...")
    
    try:
        # Criar app Flask
        app = create_app()
        
        # Não usar debug mode para evitar problemas com SQLite
        app.config['DEBUG'] = False
        
        # Usar caminho absoluto para o banco
        db_path = os.path.join(os.getcwd(), 'erp.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        
        print("📍 Configuração do banco:", app.config['SQLALCHEMY_DATABASE_URI'])
        
        # Testar se consegue acessar banco
        with app.app_context():
            from app.ordem_servico.ordem_servico_model import OrdemServico
            
            try:
                count = OrdemServico.query.count()
                print(f"✅ Conexão OK - {count} ordens no banco")
            except Exception as e:
                print(f"❌ Erro na conexão: {e}")
                return None
        
        return app
        
    except Exception as e:
        print(f"❌ Erro criando app: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    app = create_simple_server()
    if app:
        print("🚀 Iniciando servidor na porta 5003...")
        app.run(host='127.0.0.1', port=5003, debug=False)
    else:
        print("❌ Falha ao criar servidor")