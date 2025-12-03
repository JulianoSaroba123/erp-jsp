#!/usr/bin/env python3
"""
ERP JSP v3.0 - Ponto de Entrada para Desenvolvimento Local
==========================================================

Este arquivo serve apenas para desenvolvimento local.
Para produção (Render), o Gunicorn usa app.app:app (pasta app/__init__.py)

Autor: JSP Soluções
Data: 2025
"""

# Importa a aplicação da estrutura modular
from app import app

if __name__ == '__main__':
    # Configuração para desenvolvimento local
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(" ERP JSP - Servidor de Desenvolvimento")
    print(f"📍 Porta: {port}")
    print(f" Debug: {debug}")
    print(f" URL: http://localhost:{port}")
    print(" Para produção, use: gunicorn app.app:app")
    
    app.run(host='0.0.0.0', port=port, debug=debug)