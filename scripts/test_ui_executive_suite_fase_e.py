# -*- coding: utf-8 -*-
"""Regressao visual da Fase E: Propostas e Pedidos."""

import os
import sys
from datetime import date
from decimal import Decimal

os.environ['FLASK_CONFIG'] = 'testing'
os.environ['FLASK_ENV'] = 'testing'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import create_app
from app.auth.usuario_model import Usuario
from app.cliente.cliente_model import Cliente
from app.configuracao import configuracao_utils
from app.extensoes import db
from app.fornecedor.fornecedor_model import Fornecedor
from app.pedido.pedido_model import Pedido
from app.pedido_compra.pedido_compra_model import PedidoCompra
from app.proposta.proposta_model import Proposta


PHASE_E_CSS = 'jsp-executive-suite-phase-e.css'


def executar_testes():
    configuracao_utils.get_config = lambda: None
    app = create_app('testing')
    client = app.test_client()

    with app.app_context():
        db.create_all()
        admin = Usuario(
            nome='Admin Fase E', email='admin_fasee@example.com', usuario='admin_fasee',
            tipo_usuario='admin', ativo=True, email_confirmado=True, primeiro_login=False,
        )
        admin.set_senha('SenhaForte123!')
        cliente = Cliente(nome='TEST_FASEE_Cliente', tipo='PF', cpf_cnpj='12345678901', ativo=True)
        fornecedor = Fornecedor(nome='TEST_FASEE_Fornecedor', tipo='PJ', cnpj_cpf='11222333000144', ativo=True)
        db.session.add_all([admin, cliente, fornecedor])
        db.session.commit()

        proposta = Proposta(cliente_id=cliente.id, titulo='TEST_FASEE_Proposta', status='pendente', data_emissao=date.today(), valor_total=Decimal('100.00'))
        db.session.add(proposta)
        db.session.commit()
        pedido = Pedido(cliente_id=cliente.id, data_pedido=date.today(), status=Pedido.STATUS_RASCUNHO, valor_total=Decimal('100.00'))
        db.session.add(pedido)
        db.session.commit()
        pedido_compra = PedidoCompra(fornecedor_id=fornecedor.id, data_emissao=date.today(), status=PedidoCompra.STATUS_RASCUNHO, finalidade=PedidoCompra.FINALIDADE_ESTOQUE, total=Decimal('100.00'))
        db.session.add(pedido_compra)
        db.session.commit()
        proposta_id, pedido_id, pedido_compra_id = proposta.id, pedido.id, pedido_compra.id

    client.post('/auth/login', data={'identificador': 'admin_fasee', 'senha': 'SenhaForte123!'})

    paginas = {
        '/propostas/': ('Gerenciamento de Propostas', PHASE_E_CSS),
        '/propostas/nova': ('name="cliente_id"', PHASE_E_CSS),
        f'/propostas/{proposta_id}': ('TEST_FASEE_Proposta', PHASE_E_CSS),
        f'/propostas/{proposta_id}/editar': ('id="valorTotal"', PHASE_E_CSS),
        '/pedido/': ('Pedidos', PHASE_E_CSS),
        '/pedido/novo': ('id="pedidoForm"', PHASE_E_CSS),
        f'/pedido/{pedido_id}': ('Pedido', PHASE_E_CSS),
        f'/pedido/{pedido_id}/editar': ('id="tabelaItens"', PHASE_E_CSS),
        '/pedido-compra/': ('Pedidos de Compra', PHASE_E_CSS),
        '/pedido-compra/novo': ('id="itens-body"', PHASE_E_CSS),
        f'/pedido-compra/{pedido_compra_id}': ('TEST_FASEE_Fornecedor', PHASE_E_CSS),
        f'/pedido-compra/{pedido_compra_id}/editar': ('id="item-row-template"', PHASE_E_CSS),
    }
    for url, expected in paginas.items():
        response = client.get(url)
        assert response.status_code == 200, (url, response.status_code)
        html = response.get_data(as_text=True)
        for text in expected:
            assert text in html, (url, text)

    for url in ['/auth/login', '/dashboard', '/cliente/listar', '/fornecedor/listar', '/produto/listar', '/servico/listar', '/equipamentos/listar', '/financeiro/', '/ordem_servico/listar']:
        response = client.get(url)
        assert response.status_code in (200, 302, 308), (url, response.status_code)

    with app.app_context():
        PedidoCompra.query.filter(PedidoCompra.id == pedido_compra_id).delete()
        Pedido.query.filter(Pedido.id == pedido_id).delete()
        Proposta.query.filter(Proposta.id == proposta_id).delete()
        Cliente.query.filter(Cliente.nome == 'TEST_FASEE_Cliente').delete()
        Fornecedor.query.filter(Fornecedor.nome == 'TEST_FASEE_Fornecedor').delete()
        db.session.commit()

    print('FASE E: Propostas e Pedidos OK')


if __name__ == '__main__':
    executar_testes()
