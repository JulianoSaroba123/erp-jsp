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
from app.app import create_app

# Cria a aplicação
app = create_app()

# Inicializa o banco se necessário
with app.app_context():
    try:
        from app.extensoes import db
        db.create_all()
        print("✅ Banco de dados verificado/criado com sucesso!")
    except Exception as e:
        print(f"❌ Erro na inicialização do banco: {e}")

if __name__ == '__main__':
    """
    Executa a aplicação em modo de desenvolvimento.
    
    Configurações:
    - Host: 0.0.0.0 (aceita conexões externas)
    - Port: 5001 (mudado para evitar conflito com OBPC)
    - Debug: Conforme configuração
    """
    
    # Porta do servidor (mudando para 5001 para evitar conflito)
    port = int(os.environ.get('PORT', 5001))
    
    # Executa a aplicação
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False  # Desabilitando debug
    )