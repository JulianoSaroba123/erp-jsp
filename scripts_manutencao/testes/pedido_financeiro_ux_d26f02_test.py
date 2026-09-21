# -*- coding: utf-8 -*-
"""D26F02 - UX Pedido <-> Financeiro."""

from __future__ import annotations

import pytest


@pytest.fixture()
def app_ctx():
    from app import create_app
    from app.extensoes import db

    app = create_app("testing")

    with app.app_context():
        from app.auth.usuario_model import Usuario  # noqa: F401
        from app.cliente.cliente_model import Cliente  # noqa: F401
        from app.financeiro.financeiro_model import LancamentoFinanceiro  # noqa: F401
        from app.pedido.pedido_model import Pedido, PedidoItem  # noqa: F401
        from app.produto.produto_model import Produto  # noqa: F401
        from app.proposta.proposta_model import Proposta  # noqa: F401

        db.drop_all()
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


def _seed_cliente_produto(db):
    from app.cliente.cliente_model import Cliente
    from app.produto.produto_model import Produto

    cliente = Cliente(
        nome="Cliente UX Pedido",
        tipo="PJ",
        cpf_cnpj="11222333000144",
    )

    produto = Produto(
        nome="Produto UX",
        preco_venda=840,
    )

    db.session.add_all(
        [
            cliente,
            produto,
        ]
    )
    db.session.commit()

    return cliente, produto


def _seed_admin(db):
    from app.auth.usuario_model import Usuario

    usuario = Usuario(
        nome="Administrador UX",
        email="admin.ux@teste.local",
        usuario="admin_ux",
        tipo_usuario="admin",
        ativo=True,
        email_confirmado=True,
        primeiro_login=False,
    )

    usuario.set_senha("123456")

    db.session.add(usuario)
    db.session.commit()

    return usuario


def _autenticar(client, usuario):
    response = client.post(
        "/auth/login",
        data={
            "identificador": usuario.usuario,
            "senha": "123456",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302


def _payload(cliente, produto, status):
    return {
        "cliente_id": str(cliente.id),
        "status": status,
        "data_pedido": "2026-09-21",
        "condicoes_pagamento": "PIX",
        "desconto": "0,00",
        "item_tipo[]": ["PRODUTO"],
        "item_referencia_id[]": [
            f"P:{produto.id}"
        ],
        "item_descricao[]": [
            "Produto UX"
        ],
        "item_quantidade[]": ["2"],
        "item_valor_unitario[]": ["840,00"],
        "item_desconto[]": ["0"],
    }


def _criar_pedido(
    client,
    cliente,
    produto,
    status,
):
    from app.pedido.pedido_model import Pedido

    response = client.post(
        "/pedido/novo",
        data=_payload(
            cliente,
            produto,
            status,
        ),
        follow_redirects=False,
    )

    assert response.status_code == 302

    return Pedido.query.one()


def test_visualizacao_exibe_financeiro_vinculado(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro

    cliente, produto = _seed_cliente_produto(db)
    usuario = _seed_admin(db)

    client = app_ctx.test_client()
    _autenticar(client, usuario)

    pedido = _criar_pedido(
        client,
        cliente,
        produto,
        "CONCLUIDO",
    )

    financeiro = (
        LancamentoFinanceiro.query
        .filter_by(
            pedido_id=pedido.id,
            ativo=True,
        )
        .one()
    )

    response = client.get(
        f"/pedido/{pedido.id}"
    )

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert "Financeiro vinculado" in html
    assert "R$ 1.680,00" in html
    assert "Abrir lancamento" in html
    assert (
        f"/financeiro/lancamentos/{financeiro.id}/editar"
        in html
    )


def test_edicao_bloqueia_status_visualmente(app_ctx):
    from app.extensoes import db

    cliente, produto = _seed_cliente_produto(db)
    usuario = _seed_admin(db)

    client = app_ctx.test_client()
    _autenticar(client, usuario)

    pedido = _criar_pedido(
        client,
        cliente,
        produto,
        "CONCLUIDO",
    )

    response = client.get(
        f"/pedido/{pedido.id}/editar"
    )

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert 'aria-disabled="true"' in html

    assert (
        'type="hidden"\n'
        '                        name="status"\n'
        '                        value="CONCLUIDO"'
        in html
    )

    assert (
        "Status bloqueado: pedido possui "
        "financeiro vinculado."
        in html
    )


def test_pedido_sem_financeiro_mantem_status_editavel(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro

    cliente, produto = _seed_cliente_produto(db)
    usuario = _seed_admin(db)

    client = app_ctx.test_client()
    _autenticar(client, usuario)

    pedido = _criar_pedido(
        client,
        cliente,
        produto,
        "RASCUNHO",
    )

    assert (
        LancamentoFinanceiro.query
        .filter_by(
            pedido_id=pedido.id,
            ativo=True,
        )
        .count()
        == 0
    )

    response = client.get(
        f"/pedido/{pedido.id}/editar"
    )

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert (
        '<select class="form-select" name="status">'
        in html
    )

    assert (
        "Status bloqueado: pedido possui "
        "financeiro vinculado."
        not in html
    )
