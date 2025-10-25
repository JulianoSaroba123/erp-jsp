# -*- coding: utf-8 -*-
"""
Script para adicionar a coluna `data_validade` na tabela `propostas`.
"""

from app.extensoes import db
from app.app import create_app

def adicionar_coluna_data_validade():
    app = create_app()
    with app.app_context():
        try:
            db.engine.execute('ALTER TABLE propostas ADD COLUMN data_validade DATE;')
            print('Coluna `data_validade` adicionada com sucesso.')
        except Exception as e:
            print(f'Erro ao adicionar coluna: {e}')

if __name__ == '__main__':
    adicionar_coluna_data_validade()