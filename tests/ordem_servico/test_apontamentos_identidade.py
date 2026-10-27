"""Testa preservação de apontamentos sem abrir conexão com banco externo."""
import ast
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import re

import pytest
from werkzeug.datastructures import MultiDict

SOURCE = Path(__file__).resolve().parents[2] / 'app/ordem_servico/ordem_servico_routes.py'


class Trabalho:
    def __init__(self, id=None, colaborador_id=None, ativo=True):
        self.id, self.colaborador_id, self.ativo = id, colaborador_id, ativo
        self.total_horas = self.horas_normais = self.horas_extras = Decimal('0')
        self.km_total = 0

    def calcular_horas_automatico(self):
        pass

    def atualizar_valores_com_adicional(self, *args):
        pass


class Query:
    def get(self, key):
        return SimpleNamespace(salario_mensal=0, valor_hora=0)


class Session:
    def __init__(self):
        self.added = []

    def add(self, value):
        self.added.append(value)


def functions():
    tree = ast.parse(SOURCE.read_text())
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {'extrair_colaboradores_form', 'processar_colaboradores_os'}]
    session = Session()
    ns = {'re': re, 'date': date, 'datetime': datetime, 'Decimal': Decimal,
          'safe_int_convert': lambda v: int(v) if v and str(v).isdigit() else None,
          'OrdemServicoColaborador': Trabalho, 'Colaborador': SimpleNamespace(query=Query()),
          'db': SimpleNamespace(session=session)}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(SOURCE), 'exec'), ns)
    return ns['processar_colaboradores_os'], session


def form(id='12', colaborador='7'):
    return MultiDict({'colaboradores[0][id]': id, 'colaboradores[0][colaborador_id]': colaborador,
                      'colaboradores[0][data_trabalho]': '2026-09-11'})


def ordem(*trabalhos):
    return SimpleNamespace(id=619, tipo_os='operacional', colaboradores_trabalho=list(trabalhos))


def test_atualiza_mesma_identidade():
    processar, session = functions()
    trabalho = Trabalho(12, 7)
    processar(ordem(trabalho), form())
    assert session.added == [trabalho] and trabalho.id == 12 and trabalho.ativo


def test_remocao_inativa_sem_excluir():
    processar, _ = functions()
    trabalho = Trabalho(12, 7)
    processar(ordem(trabalho), MultiDict())
    assert not trabalho.ativo and trabalho.id == 12


@pytest.mark.parametrize('identificador,colaborador', [('13', '7'), ('12', '8'), ('invalido', '7')])
def test_rejeita_identidade_invalida_ou_troca(identificador, colaborador):
    processar, _ = functions()
    with pytest.raises(ValueError):
        processar(ordem(Trabalho(12, 7)), form(identificador, colaborador))


def test_rejeita_id_repetido():
    processar, _ = functions()
    data = form()
    data.update({'colaboradores[1][id]': '12', 'colaboradores[1][colaborador_id]': '7'})
    with pytest.raises(ValueError):
        processar(ordem(Trabalho(12, 7)), data)


def test_pdf_fechamento_exige_admin_no_servidor():
    from flask import Flask, abort, request
    from werkzeug.exceptions import Forbidden

    tree = ast.parse(SOURCE.read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'gerar_relatorio_pdf')
    node.decorator_list = []
    app = Flask(__name__)
    for autenticado, admin in [(False, False), (True, False)]:
        ns = {'request': request, 'abort': abort,
              'current_user': SimpleNamespace(is_authenticated=autenticado),
              'usuario_eh_admin': lambda: admin}
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), 'exec'), ns)
        with app.test_request_context('/1/relatorio-pdf?fechamento=1'):
            with pytest.raises(Forbidden):
                ns['gerar_relatorio_pdf'](1)
