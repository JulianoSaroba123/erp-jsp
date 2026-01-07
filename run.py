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
import sys

# CARREGA .env ANTES de importar qualquer coisa
from dotenv import load_dotenv
load_dotenv()

# Verifica se DATABASE_URL está configurada
if not os.getenv('DATABASE_URL'):
    print("⚠️  AVISO: DATABASE_URL não encontrada no .env")
    print("⚠️  Será usado SQLite por padrão")
else:
    print(f"✅ DATABASE_URL carregada: {os.getenv('DATABASE_URL')[:50]}...")

try:
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
        app.config['PROPAGATE_EXCEPTIONS'] = True
        
        print(f" Iniciando servidor em http://127.0.0.1:{port}")
        
        # Executa a aplicação
        app.run(
            host='127.0.0.1',  # Apenas localhost por enquanto
            port=port,
            debug=True,  # Debug habilitado para ver erros
            use_reloader=False  # Evita recarregamento automático
        )
        
except Exception as e:
    print(f"\n{'='*60}")
    print(f"ERRO FATAL AO INICIAR O SERVIDOR:")
    print(f"{'='*60}")
    print(f"{e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)