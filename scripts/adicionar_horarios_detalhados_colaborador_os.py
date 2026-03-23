# -*- coding: utf-8 -*-
"""
Adiciona colunas de horários detalhados na tabela ordem_servico_colaborador.

Uso:
    python scripts/adicionar_horarios_detalhados_colaborador_os.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from app import create_app
from app.extensoes import db


COLUNAS = {
    'hora_entrada_manha': 'TIME',
    'hora_saida_manha': 'TIME',
    'hora_entrada_tarde': 'TIME',
    'hora_saida_tarde': 'TIME',
    'hora_entrada_extra': 'TIME',
    'hora_saida_extra': 'TIME',
    'horas_normais': 'NUMERIC(5,2) DEFAULT 0.00',
    'horas_extras': 'NUMERIC(5,2) DEFAULT 0.00',
}


def main():
    app = create_app()

    with app.app_context():
        inspector = inspect(db.engine)
        if 'ordem_servico_colaborador' not in inspector.get_table_names():
            print('Tabela ordem_servico_colaborador não encontrada.')
            return

        existentes = {col['name'] for col in inspector.get_columns('ordem_servico_colaborador')}
        alteracoes = []

        for coluna, definicao in COLUNAS.items():
            if coluna not in existentes:
                alteracoes.append(f'ALTER TABLE ordem_servico_colaborador ADD COLUMN {coluna} {definicao}')

        if not alteracoes:
            print('Colunas de horários detalhados já existem.')
            return

        for sql in alteracoes:
            db.session.execute(text(sql))

        db.session.commit()
        print('Migração de horários detalhados por colaborador concluída com sucesso.')


if __name__ == '__main__':
    main()