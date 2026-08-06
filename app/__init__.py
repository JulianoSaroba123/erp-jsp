# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Inicialização da Aplicação
==========================================

Arquivo principal da aplicação Flask.
Configura a aplicação usando o padrão Application Factory.

Autor: JSP Soluções
Data: 2025
"""

# Reexporta a instância global única criada em app.app.
from app.app import create_app, app

# Log de inicialização para o Render (sem emojis para compatibilidade)
print("ERP JSP iniciado com sucesso!")
print(f"Configuracao: {app.config.get('ENV', 'production')}")
print(f"Debug: {app.config.get('DEBUG', False)}")

# Marca este diretório como um pacote Python