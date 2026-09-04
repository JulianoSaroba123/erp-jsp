# -*- coding: utf-8 -*-
"""Regressão da Fase H2: isolamento dos estilos legados da Executive Suite."""
import os
import sys

os.environ['FLASK_CONFIG'] = 'testing'
os.environ['FLASK_ENV'] = 'testing'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import create_app
from app.auth.usuario_model import Usuario
from app.configuracao import configuracao_utils
from app.extensoes import db


def executar_testes():
    configuracao_utils.get_config = lambda: None
    app = create_app('testing')
    client = app.test_client()
    with app.app_context():
        db.create_all()
        admin = Usuario(nome='Admin Fase H2', email='admin_faseh2@example.com', usuario='admin_faseh2', tipo_usuario='admin', ativo=True, email_confirmado=True, primeiro_login=False)
        admin.set_senha('SenhaForte123!')
        db.session.add(admin)
        db.session.commit()

    client.post('/auth/login', data={'identificador': 'admin_faseh2', 'senha': 'SenhaForte123!'})
    paginas = ['/dashboard', '/cliente/listar', '/fornecedor/listar', '/produto/listar', '/servico/listar', '/equipamentos/listar', '/propostas/', '/pedido/', '/pedido-compra/', '/ordem_servico/listar', '/financeiro/', '/usuarios/', '/colaborador/listar', '/configuracao/']
    estilos_legados = ('css/neon-theme.css', 'css/form-override.css', 'css/navigation-enhanced-clean.css', 'css/navigation-enhanced.css')
    for url in paginas:
        response = client.get(url)
        assert response.status_code == 200, (url, response.status_code)
        html = response.get_data(as_text=True)
        assert 'jsp-executive-suite-components.css' in html, url
        assert all(estilo not in html for estilo in estilos_legados), url

    login = app.test_client().get('/auth/login').get_data(as_text=True)
    assert 'command-center.css' in login
    assert all(estilo not in login for estilo in estilos_legados)
    print('FASE H2: Limpeza CSS legado OK')


if __name__ == '__main__':
    executar_testes()