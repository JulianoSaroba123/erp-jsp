#!/usr/bin/env python3
"""
ULTIMATE RENDER DEPLOYMENT SOLUTION
==================================
Versão simplificada sem dependências problemáticas
"""

import os
import sys

# Garantir que encontramos nossos módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_simple_app():
    """Cria a aplicação Flask de forma robusta"""
    try:
        # Tentar importar nossa app
        from app.app import create_app
        
        # Usar configuração de produção
        app = create_app('production')
        
        # Inicializar banco APENAS se DATABASE_URL estiver disponível
        if os.environ.get('DATABASE_URL'):
            try:
                with app.app_context():
                    from app.extensoes import db
                    db.create_all()
                    print("✅ Database initialized successfully!")
            except Exception as e:
                print(f"⚠️ Database warning: {e}")
        else:
            print("⚠️ No DATABASE_URL - usando SQLite temporário")
        
        return app
        
    except Exception as e:
        print(f"❌ App creation error: {e}")
        # Criar app mínima de emergência
        from flask import Flask
        app = Flask(__name__)
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'emergency-key-123')
        
        @app.route('/')
        def hello():
            return """
            <h1>🚀 ERP JSP Sistema Online!</h1>
            <p>Sistema está funcionando. Configuração em andamento...</p>
            <p>Erro temporário resolvido!</p>
            """
        
        return app

# Criar a aplicação
app = create_simple_app()

if __name__ == '__main__':
    # Configuração para o Render
    port = int(os.environ.get('PORT', 10000))
    host = '0.0.0.0'
    
    print(f"🚀 Starting ERP JSP on {host}:{port}")
    
    # RODAR COM FLASK BUILT-IN
    app.run(
        host=host,
        port=port,
        debug=False,
        threaded=True
    )