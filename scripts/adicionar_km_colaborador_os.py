# -*- coding: utf-8 -*-
"""
Adiciona colunas de deslocamento por colaborador na tabela ordem_servico_colaborador.

Uso:
    python scripts/adicionar_km_colaborador_os.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from app import create_app
from app.extensoes import db


def main():
    app = create_app()

    with app.app_context():
        inspector = inspect(db.engine)
        tabelas = inspector.get_table_names()

        if 'ordem_servico_colaborador' not in tabelas:
            print("Tabela ordem_servico_colaborador não encontrada.")
            return

        colunas = {col['name'] for col in inspector.get_columns('ordem_servico_colaborador')}
        alteracoes = []

        if 'km_inicial' not in colunas:
            alteracoes.append("ALTER TABLE ordem_servico_colaborador ADD COLUMN km_inicial INTEGER")

        if 'km_final' not in colunas:
            alteracoes.append("ALTER TABLE ordem_servico_colaborador ADD COLUMN km_final INTEGER")

        if not alteracoes:
            print("Colunas km_inicial e km_final já existem.")
            return

        for sql in alteracoes:
            db.session.execute(text(sql))

        db.session.commit()
        print("Migração concluída com sucesso.")


if __name__ == '__main__':
    main()