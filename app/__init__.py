# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Inicialização da Aplicação
==========================================

Arquivo principal da aplicação Flask.
Configura a aplicação usando o padrão Application Factory.

Autor: JSP Soluções
Data: 2025
"""

# Importa a factory function
from app.app import create_app

# Cria a instância Flask global para o Gunicorn
app = create_app()

# Log de inicialização para o Render
print("🚀 ERP JSP iniciado com sucesso no Render!")
print(f"📊 Configuração: {app.config.get('ENV', 'production')}")
print(f"🔧 Debug: {app.config.get('DEBUG', False)}")

# Marca este diretório como um pacote Python