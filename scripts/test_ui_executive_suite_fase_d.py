# -*- coding: utf-8 -*-
"""Regressao visual da Fase D: Produtos, Servicos e Equipamentos."""

import os
import sys

os.environ['FLASK_CONFIG'] = 'testing'
os.environ['FLASK_ENV'] = 'testing'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import create_app
from app.auth.usuario_model import Usuario
from app.cliente.cliente_model import Cliente
from app.equipamento.equipamento_model import Equipamento
from app.extensoes import db
from app.produto.produto_model import Produto
from app.servico.servico_model import Servico
from app.configuracao import configuracao_utils


def _admin():
    admin = Usuario.query.filter_by(usuario='admin_fased_test').first()
    if admin:
        return
    admin = Usuario(
        nome='Admin Fase D',
        email='admin_fased@example.com',
        usuario='admin_fased_test',
        tipo_usuario='admin',
        ativo=True,
        email_confirmado=True,
        primeiro_login=False,
    )
    admin.set_senha('SenhaForte123!')
    db.session.add(admin)
    db.session.commit()


def executar_testes():
    configuracao_utils.get_config = lambda: None
    app = create_app('testing')
    client = app.test_client()

    with app.app_context():
        db.create_all()
        _admin()
        cliente = Cliente(nome='TEST_FASED_Cliente', tipo='PF', cpf_cnpj='12345678901', ativo=True)
        produto = Produto(nome='TEST_FASED_Produto', codigo='FASED-P1', ativo=True)
        servico = Servico(codigo='FASED-S1', nome='TEST_FASED_Servico', categoria='outros', tipo_cobranca='servico', valor_base=0, ativo=True)
        db.session.add_all([cliente, produto, servico])
        db.session.commit()
        equipamento = Equipamento(nome='TEST_FASED_Equipamento', cliente_id=cliente.id, ativo=True)
        db.session.add(equipamento)
        db.session.commit()
        produto_id = produto.id
        servico_id = servico.id
        equipamento_id = equipamento.id

    client.post('/auth/login', data={'identificador': 'admin_fased_test', 'senha': 'SenhaForte123!'})

    paginas = {
        '/produto/listar': ('TEST_FASED_Produto', 'cc-table'),
        '/produto/novo': ('name="codigo"', 'jsp-executive-suite-phase-d.css'),
        f'/produto/{produto_id}/editar': ('name="controla_estoque"', 'jsp-executive-suite-phase-d.css'),
        f'/produto/{produto_id}': ('TEST_FASED_Produto', 'jsp-executive-suite-phase-d.css'),
        '/servico/listar': ('TEST_FASED_Servico', 'cc-table'),
        '/servico/novo': ('id="formServico"', 'jsp-executive-suite-phase-d.css'),
        f'/servico/{servico_id}/editar': ('name="valor_base"', 'jsp-executive-suite-phase-d.css'),
        f'/servico/{servico_id}': ('TEST_FASED_Servico', 'jsp-executive-suite-phase-d.css'),
        '/equipamentos/listar': ('TEST_FASED_Equipamento', 'cc-table'),
        '/equipamentos/novo': ('id="cliente_id"', 'jsp-executive-suite-phase-d.css'),
        f'/equipamentos/editar/{equipamento_id}': ('id="numero_serie"', 'jsp-executive-suite-phase-d.css'),
        f'/equipamentos/detalhes/{equipamento_id}': ('TEST_FASED_Equipamento', 'jsp-executive-suite-phase-d.css'),
    }
    for url, expected in paginas.items():
        response = client.get(url)
        assert response.status_code == 200, (url, response.status_code)
        html = response.get_data(as_text=True)
        for text in expected:
            assert text in html, (url, text)

    with app.app_context():
        Equipamento.query.filter(Equipamento.nome.like('TEST_FASED_%')).delete()
        Produto.query.filter(Produto.nome.like('TEST_FASED_%')).delete()
        Servico.query.filter(Servico.nome.like('TEST_FASED_%')).delete()
        Cliente.query.filter(Cliente.nome.like('TEST_FASED_%')).delete()
        db.session.commit()

    print('FASE D: Produtos, Servicos e Equipamentos OK')


if __name__ == '__main__':
    executar_testes()
