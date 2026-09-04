# -*- coding: utf-8 -*-
"""Regressao visual da Fase H1: administracao e cadastros auxiliares."""
import os
import sys

os.environ['FLASK_CONFIG'] = 'testing'
os.environ['FLASK_ENV'] = 'testing'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import create_app
from app.auth.usuario_model import Usuario
from app.colaborador.colaborador_model import Colaborador
from app.configuracao import configuracao_utils
from app.configuracao.configuracao_model import Configuracao
from app.extensoes import db


def executar_testes():
    configuracao_utils.get_config = lambda: None
    app = create_app('testing')
    client = app.test_client()
    with app.app_context():
        db.create_all()
        admin = Usuario(nome='Admin Fase H1', email='admin_faseh1@example.com', usuario='admin_faseh1', tipo_usuario='admin', ativo=True, email_confirmado=True, primeiro_login=False)
        admin.set_senha('SenhaForte123!')
        colaborador = Colaborador(nome='TEST_FASEH1_Colaborador', cpf='12345678901', cargo='tecnico', ativo=True)
        configuracao = Configuracao(id=1, nome_fantasia='TEST_FASEH1_Empresa')
        db.session.add_all([admin, colaborador, configuracao])
        db.session.commit()
        admin_id = admin.id
        colaborador_id = colaborador.id

    client.post('/auth/login', data={'identificador': 'admin_faseh1', 'senha': 'SenhaForte123!'})
    paginas = {
        '/usuarios/': ('Gerenciamento de Usuários', 'cc-table', 'jsp-executive-suite-phase-h1.css'),
        '/usuarios/novo': ('id="formUsuario"', 'name="tipo_usuario"', 'name="senha"'),
        f'/usuarios/{admin_id}/editar': ('id="formUsuario"', 'Admin Fase H1'),
        '/colaborador/listar': ('Gerenciamento de Colaboradores', 'cc-table', 'jsp-executive-suite-phase-h1.css'),
        '/colaborador/novo': ('id="formColaborador"', 'id="cpf"', 'name="salario_mensal"'),
        f'/colaborador/editar/{colaborador_id}': ('id="formColaborador"', 'TEST_FASEH1_Colaborador'),
        f'/colaborador/visualizar/{colaborador_id}': ('Informações Pessoais', 'cc-form-card'),
        '/configuracao/': ('Configurações do Sistema', 'id="btn_lookup_cnpj"', 'id="btn_lookup_cep"', 'jsp-executive-suite-phase-h1.css'),
        '/auth/perfil': ('Informações do Perfil', 'jsp-executive-suite-phase-h1.css'),
        '/auth/alterar-senha': ('Alterar Senha', 'id="senha_atual"'),
    }
    for url, expected in paginas.items():
        response = client.get(url)
        assert response.status_code == 200, (url, response.status_code)
        html = response.get_data(as_text=True)
        for marker in expected:
            assert marker in html, (url, marker)
    print('FASE H1: Administracao OK')


if __name__ == '__main__':
    executar_testes()
