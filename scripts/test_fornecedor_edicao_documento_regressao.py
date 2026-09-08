# -*- coding: utf-8 -*-
"""Regressão do fluxo de documento no cadastro/edição de fornecedor."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ROOT / 'app' / 'fornecedor' / 'fornecedor_routes.py'


def executar_testes():
    routes = ROUTES.read_text(encoding='utf-8')

    assert 'def _normalizar_documento(value):' in routes
    assert "request.form.get('cpf_cnpj', '')" in routes
    assert "request.form.get('cnpj_cpf', '')" not in routes
    assert 'return doc or None' in routes

    # Novo cadastro deve checar qualquer registro com o mesmo documento,
    # inclusive inativo, porque o índice UNIQUE do banco também considera inativos.
    assert "Fornecedor.query.filter(Fornecedor.cnpj_cpf == documento).first()" in routes

    # Edição deve excluir o próprio registro da verificação de duplicidade.
    assert 'Fornecedor.id != fornecedor.id' in routes

    # Qualquer exceção precisa limpar a sessão antes de renderizar novamente.
    assert routes.count('db.session.rollback()') >= 2

    print('FORNECEDOR EDICAO DOCUMENTO: OK')


if __name__ == '__main__':
    executar_testes()
