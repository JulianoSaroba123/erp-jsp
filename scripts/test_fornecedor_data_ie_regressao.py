# -*- coding: utf-8 -*-
"""Regressao estrutural do cadastro de fornecedor: Data de Fundacao e IE."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORM = ROOT / 'app' / 'fornecedor' / 'templates' / 'fornecedor' / 'form.html'
ROUTES = ROOT / 'app' / 'fornecedor' / 'fornecedor_routes.py'


def executar_testes():
    form = FORM.read_text(encoding='utf-8')
    routes = ROUTES.read_text(encoding='utf-8')

    # Uma unica fonte de IE/RG no formulario.
    assert form.count('id="rg_ie"') == 1
    assert 'id="inscricao_estadual"' not in form
    assert 'name="inscricao_estadual"' not in form

    # Data de Fundacao deve usar DD/MM/AAAA e nao o seletor nativo segmentado.
    trecho_data = form.split('id="data_fundacao"', 1)[0][-200:] + form.split('id="data_fundacao"', 1)[1][:400]
    assert 'type="text"' in trecho_data
    assert 'placeholder="DD/MM/AAAA"' in trecho_data
    assert 'mascaraData' in form

    # Parser compativel com formato antigo e novo.
    assert "('%Y-%m-%d', '%d/%m/%Y')" in routes

    # Novo e editar usam rg_ie como fonte unica.
    assert "inscricao_estadual=(request.form.get('rg_ie', '').strip()" in routes
    assert "fornecedor.rg_ie = request.form.get('rg_ie', '').strip()" in routes
    assert "fornecedor.inscricao_estadual = fornecedor.rg_ie if fornecedor.tipo == 'PJ' else ''" in routes

    # Edicao precisa persistir Data de Fundacao.
    assert "fornecedor.data_fundacao = _parse_date(request.form.get('data_fundacao'))" in routes

    print('FORNECEDOR DATA/IE: OK')


if __name__ == '__main__':
    executar_testes()
