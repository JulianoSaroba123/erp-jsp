#!/usr/bin/env python3
"""
ERP JSP SYSTEM - PRODUCTION VERSION
===================================
Sistema ERP completo funcionando em produção
"""

import os
import sys

# Garantir que encontramos nossos módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_app():
    """Cria a aplicação Flask completa"""
    
    print("🚀 Iniciando ERP JSP Sistema Completo...")
    
    try:
        # Importar sistema completo
        from app.app import create_app
        
        # Criar app em modo produção
        app = create_app('production')
        print("✅ Sistema ERP completo carregado!")
        
        # Inicializar banco PostgreSQL
        with app.app_context():
            try:
                from app.extensoes import db
                
                # Criar todas as tabelas
                db.create_all()
                print("✅ Banco PostgreSQL inicializado!")
                
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
                        print("✅ Usuário admin criado!")
                    else:
                        print("✅ Usuário admin já existe!")
                except Exception as e:
                    print(f"⚠️ Admin user warning: {e}")
                    
            except Exception as e:
                print(f"❌ Database error: {e}")
        
        return app
        
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        # Sistema de emergência mínimo
        from flask import Flask, jsonify
        
        app = Flask(__name__)
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'emergency-key')
        
        @app.route('/')
        def emergency():
            return jsonify({
                "status": "EMERGENCY_MODE",
                "message": "Sistema em modo de emergência",
                "error": str(e),
                "action": "Verificar logs do Render"
            })
        
        return app

# Criar aplicação
app = create_app()

if __name__ == '__main__':
    # Configuração para produção
    port = int(os.environ.get('PORT', 10000))
    host = '0.0.0.0'
    
    print(f"� ERP JSP iniciando em {host}:{port}")
    print("🌐 URL: https://erp-jsp.onrender.com")
    print("� Login: admin@jsp.com / admin123")
    
    # Executar aplicação
    app.run(
        host=host,
        port=port,
        debug=False,
        threaded=True
    )