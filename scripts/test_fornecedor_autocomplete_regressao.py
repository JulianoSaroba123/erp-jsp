# -*- coding: utf-8 -*-
"""Regressao estrutural do autocomplete de CNPJ no cadastro de fornecedor."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORM = ROOT / 'app' / 'fornecedor' / 'templates' / 'fornecedor' / 'form.html'
API = ROOT / 'app' / 'fornecedor' / 'consultas_api.py'


def executar_testes():
    form = FORM.read_text(encoding='utf-8')
    api = API.read_text(encoding='utf-8')

    # Elementos essenciais do formulario.
    assert 'id="cpf_cnpj"' in form
    assert 'id="btn-consultar-cnpj"' in form
    assert "const btnCnpj = document.getElementById('btn-consultar-cnpj');" in form

    # O listener deve usar a mesma variavel declarada e existir uma unica vez.
    assert 'btnConsultarCnpj' not in form, 'variavel JS inexistente btnConsultarCnpj voltou ao template'
    assert form.count("btnCnpj.addEventListener('click'") == 1, 'listener CNPJ duplicado ou ausente'

    # Marcadores da corrupcao sintatica encontrada em producao.
    assert "carregado com sucesso!'e();" not in form
    assert "console.log('✅ Script de fornecedor carregado com sucesso!');" in form

    # Inicializacao da interface precisa continuar presente para exibir o botao em PJ.
    assert 'atualizarInterface();' in form

    # O frontend deve consultar a rota especifica do fornecedor.
    assert '/fornecedor/api/consultar-cnpj/${cnpjLimpo}' in form
    assert "@fornecedor_bp.route('/api/consultar-cnpj/<cnpj>')" in api

    print('FORNECEDOR AUTOCOMPLETE CNPJ: OK')


if __name__ == '__main__':
    executar_testes()
