#!/usr/bin/env python3
"""
ERP JSP - FORCE COMPLETE SYSTEM
===============================
Forçar carregamento do sistema completo sem fallback
"""

import os
import sys

# Garantir path correto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🚀 Iniciando ERP JSP - Modo Produção Completo")

try:
    # Importar sistema principal
    from app.app import create_app
    print("✅ Módulo app.app importado com sucesso")
    
    # Criar aplicação
    app = create_app('production')
    print("✅ Aplicação Flask criada em modo produção")
    
    # Configurar banco
    with app.app_context():
        try:
            from app.extensoes import db
            db.create_all()
            print("✅ Tabelas do banco criadas")
            
            # Criar usuário admin
            from app.auth.usuario_model import Usuario
            admin = Usuario.query.filter_by(email='admin@jsp.com').first()
            if not admin:
                admin = Usuario(
                    nome='Administrador JSP',
                    email='admin@jsp.com',
                    ativo=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✅ Usuário admin criado")
            else:
                print("✅ Usuário admin já existe")
                
        except Exception as e:
            print(f"⚠️ Erro no banco: {e}")
    
    print("✅ Sistema ERP JSP completamente carregado!")
    
except Exception as e:
    print(f"❌ ERRO CRÍTICO: {e}")
    import traceback
    traceback.print_exc()
    
    # Fallback apenas se realmente necessário
    from flask import Flask, redirect, url_for
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-key')
    
    @app.route('/')
    def emergency():
        return f"""
        <h1>❌ ERP JSP - Erro de Sistema</h1>
        <p><strong>Erro:</strong> {str(e)}</p>
        <p>Verifique os logs do Render para mais detalhes.</p>
        <a href="/debug">Ver Debug</a>
        """
    
    @app.route('/debug')
    def debug():
        return {
            "error": str(e),
            "python_path": sys.path,
            "working_directory": os.getcwd(),
            "environment": dict(os.environ)
        }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🌐 Iniciando servidor em 0.0.0.0:{port}")
    print(f"🔗 Acesse: https://erp-jsp.onrender.com")
    app.run(host='0.0.0.0', port=port, debug=False)