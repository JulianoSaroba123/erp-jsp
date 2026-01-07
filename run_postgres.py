# -*- coding: utf-8 -*-
"""
Run com PostgreSQL forçado
"""
import os
import sys

# FORÇA PostgreSQL ANTES de importar qualquer coisa
os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost/erp_jsp_local'
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = 'True'

print(f"🔧 DATABASE_URL forçada: {os.environ['DATABASE_URL']}")

# Agora importa o app
from app.app import app

if __name__ == '__main__':
    print("\n" + "="*60)
    print(" INICIANDO ERP JSP COM POSTGRESQL")
    print("="*60)
    print(f"📊 Banco: {app.config.get('SQLALCHEMY_DATABASE_URI')[:50]}...")
    print(f"🐛 Debug: {app.config.get('DEBUG')}")
    print("="*60 + "\n")
    
    app.run(
        host='127.0.0.1',
        port=5001,
        debug=True,
        use_reloader=False
    )
