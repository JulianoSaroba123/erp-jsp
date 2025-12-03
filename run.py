# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Ponto de Entrada
================================

Script principal para executar a aplicação.
Configura o ambiente e inicia o servidor Flask.

Autor: JSP Soluções
Data: 2025

Para rodar:
    python run.py
"""

import os
# Importa a aplicação já criada (também usada pelo Gunicorn)
from app.app import app

if __name__ == '__main__':
    """
    Executa a aplicação em modo de desenvolvimento.
    
    Configurações:
    - Host: 127.0.0.1 (localhost apenas)
    - Port: 5001 (mudado para evitar conflito com OBPC)
    - Debug: Habilitado para debug
    """
    
    print(" INICIANDO ERP JSP...")
    
    # Porta do servidor (mudando para 5001 para evitar conflito)
    port = int(os.environ.get('PORT', 5001))
    
    # Configurar debug
    app.config['DEBUG'] = True
    
    print(f" Iniciando servidor em http://127.0.0.1:{port}")
    
    # Executa a aplicação
    app.run(
        host='127.0.0.1',  # Apenas localhost por enquanto
        port=port,
        debug=False,  # Debug desabilitado para evitar múltiplos processos
        use_reloader=False  # Evita recarregamento automático
    )