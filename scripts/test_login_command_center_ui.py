# -*- coding: utf-8 -*-
"""
Teste de Regressão: modernização visual da tela de login (Command Center)
==========================================================================

Valida que a nova UI da tela de login preserva o comportamento funcional:
- GET renderiza o formulário com os campos/ids esperados;
- flash messages continuam sendo renderizadas;
- POST com credenciais inválidas mantém o fluxo de erro;
- estilesheet do Design System é referenciada.
"""

import os
import sys

os.environ['FLASK_CONFIG'] = 'testing'
os.environ['FLASK_ENV'] = 'testing'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import create_app
from app.extensoes import db


def executar_testes():
    print("=" * 70)
    print("TESTE: modernização visual da tela de login (Command Center)")
    print("=" * 70)

    app = create_app('testing')
    client = app.test_client()

    with app.app_context():
        db.create_all()

        print("\n[TESTE 1] GET /auth/login renderiza estrutura e campos esperados...")
        resp = client.get('/auth/login')
        assert resp.status_code == 200, f"Status inesperado: {resp.status_code}"
        html = resp.data.decode('utf-8')

        for campo in ['id="identificador"', 'name="identificador"',
                      'id="senha"', 'name="senha"',
                      'id="lembrar"', 'name="lembrar"',
                      'id="toggleSenha"', 'id="iconeSenha"']:
            assert campo in html, f"Campo/atributo ausente no HTML: {campo}"
        assert 'css/command-center.css' in html, "Stylesheet do Design System não referenciada"
        assert 'method="POST"' in html, "Formulário de login não usa POST"
        print("  -> OK: formulário preserva ids/names/comportamento e referencia o novo CSS.")

        print("\n[TESTE 2] POST com credenciais inválidas mantém fluxo de erro e flash message...")
        resp = client.post('/auth/login', data={
            'identificador': 'usuario_inexistente',
            'senha': 'senha_errada',
        }, follow_redirects=True)
        assert resp.status_code == 200, f"Status inesperado: {resp.status_code}"
        html_erro = resp.data.decode('utf-8')
        assert 'Usuário ou senha incorretos.' in html_erro, "Mensagem de erro de login não renderizada"
        assert 'cc-alert' in html_erro, "Classe de alerta do novo design system não aplicada"
        print("  -> OK: mensagem de erro exibida corretamente com o novo estilo de alerta.")

    print("\n" + "=" * 70)
    print("TESTES DA TELA DE LOGIN (COMMAND CENTER) VALIDADOS COM SUCESSO!")
    print("=" * 70)


if __name__ == '__main__':
    executar_testes()
