#!/usr/bin/env python3
"""
ULTIMATE RENDER DEPLOYMENT SOLUTION
==================================
Forçar carregamento do sistema completo
"""

import os
import sys

# Garantir que encontramos nossos módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_simple_app():
    """Cria a aplicação Flask de forma robusta"""
    
    # FORÇAR carregamento do sistema completo
    try:
        print("🚀 Tentando carregar sistema ERP completo...")
        
        # Importar nossa app principal
        from app.app import create_app
        
        # Criar app em modo produção
        app = create_app('production')
        print("✅ App principal criada com sucesso!")
        
        # Inicializar banco com DATABASE_URL
        if os.environ.get('DATABASE_URL'):
            try:
                with app.app_context():
                    from app.extensoes import db
                    
                    # Criar todas as tabelas
                    db.create_all()
                    print("✅ Database PostgreSQL initialized!")
                    
                    # Criar usuário admin se não existir
                    try:
                        from app.auth.usuario_model import Usuario
                        admin = Usuario.query.filter_by(email='admin@jsp.com').first()
                        if not admin:
                            admin = Usuario(
                                nome='Administrador',
                                email='admin@jsp.com',
                                ativo=True
                            )
                            admin.set_password('admin123')
                            db.session.add(admin)
                            db.session.commit()
                            print("✅ Admin user created!")
                        else:
                            print("✅ Admin user exists!")
                    except Exception as e:
                        print(f"⚠️ Admin user warning: {e}")
                        
            except Exception as e:
                print(f"❌ Database error: {e}")
                # Não falhar - continuar com SQLite
        
        print("✅ Sistema ERP COMPLETO carregado!")
        return app
        
    except Exception as e:
        print(f"❌ Erro ao carregar sistema principal: {e}")
        print("🔄 Usando fallback mínimo...")
        
        # Fallback apenas se REALMENTE não conseguir
        from flask import Flask
        app = Flask(__name__)
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'emergency-key-123')
        
        @app.route('/')
        def hello():
            return """
            <h1>❌ ERP JSP - Erro de Configuração</h1>
            <p>O sistema não conseguiu carregar completamente.</p>
            <p>Verifique as variáveis de ambiente no Render.</p>
            <p>Erro: Sistema em modo de emergência</p>
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