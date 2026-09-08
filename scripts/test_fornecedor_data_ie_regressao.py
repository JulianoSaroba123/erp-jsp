# -*- coding: utf-8 -*-
"""Regressao estrutural do cadastro de fornecedor: nome/razao social, Data de Fundacao e IE."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FORM = ROOT / 'app' / 'fornecedor' / 'templates' / 'fornecedor' / 'form.html'
ROUTES = ROOT / 'app' / 'fornecedor' / 'fornecedor_routes.py'
API = ROOT / 'app' / 'fornecedor' / 'consultas_api.py'


def executar_testes():
    form = FORM.read_text(encoding='utf-8')
    routes = ROUTES.read_text(encoding='utf-8')
    api = API.read_text(encoding='utf-8')

    # PF e PJ nao podem compartilhar o mesmo name no POST.
    assert 'id="nome"' in form
    assert 'name="nome_pf"' in form
    assert 'id="razao_social_pj"' in form
    assert 'name="razao_social"' in form
    assert form.count('name="nome"') == 0

    # Backend resolve um unico nome canonico conforme o tipo.
    assert "request.form.get('razao_social', '').strip()" in routes
    assert "request.form.get('nome_pf', '').strip()" in routes
    assert 'nome=nome_fornecedor' in routes

    # Uma unica fonte de IE/RG no formulario.
    assert form.count('id="rg_ie"') == 1
    assert 'id="inscricao_estadual"' not in form
    assert 'name="inscricao_estadual"' not in form

    # Data de Fundacao deve usar DD/MM/AAAA e nao o seletor nativo segmentado.
    match_data = re.search(r'<input(?=[^>]*id="data_fundacao")[^>]*>', form, re.S)
    assert match_data, 'input data_fundacao nao encontrado'
    trecho_data = match_data.group(0)
    assert 'type="text"' in trecho_data
    assert 'placeholder="DD/MM/AAAA"' in trecho_data
    assert 'inputmode="numeric"' in trecho_data
    assert 'mascaraData' in form

    # Parser compativel com formato antigo e novo.
    assert "('%Y-%m-%d', '%d/%m/%Y')" in routes

    # Novo e editar usam rg_ie como fonte unica.
    assert "inscricao_estadual=(request.form.get('rg_ie', '').strip()" in routes
    assert "fornecedor.rg_ie = request.form.get('rg_ie', '').strip()" in routes
    assert "fornecedor.inscricao_estadual = fornecedor.rg_ie if fornecedor.tipo == 'PJ' else ''" in routes

    # Edicao precisa persistir Data de Fundacao.
    assert "fornecedor.data_fundacao = _parse_date(request.form.get('data_fundacao'))" in routes

    # Consulta CNPJ deve expor razao_social explicitamente e o frontend deve usa-la.
    assert "'razao_social': razao_social" in api
    assert "data.data.razao_social || data.data.nome" in form

    print('FORNECEDOR CADASTRO: OK')


if __name__ == '__main__':
    executar_testes()
