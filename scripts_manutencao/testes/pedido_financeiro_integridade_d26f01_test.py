# -*- coding: utf-8 -*-
"""D26F01-A5 - Integridade Pedido <-> Financeiro."""

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
        nome="Cliente Integridade Pedido",
        tipo="PJ",
        cpf_cnpj="98765432000199",
    )

    produto = Produto(
        nome="Produto Integridade",
        preco_venda=840,
    )

    db.session.add_all([cliente, produto])
    db.session.commit()

    return cliente, produto


def _seed_admin(db):
    from app.auth.usuario_model import Usuario

    usuario = Usuario(
        nome="Administrador Integridade",
        email="admin.integridade@teste.local",
        usuario="admin_integridade",
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
        "data_pedido": "2026-09-19",
        "condicoes_pagamento": "PIX",
        "desconto": "0,00",
        "item_tipo[]": ["PRODUTO"],
        "item_referencia_id[]": [f"P:{produto.id}"],
        "item_descricao[]": ["Produto Integridade"],
        "item_quantidade[]": ["2"],
        "item_valor_unitario[]": ["840,00"],
        "item_desconto[]": ["0"],
    }


def _criar_pedido_concluido(client, cliente, produto):
    from app.pedido.pedido_model import Pedido

    response = client.post(
        "/pedido/novo",
        data=_payload(
            cliente,
            produto,
            "CONCLUIDO",
        ),
        follow_redirects=False,
    )

    assert response.status_code == 302

    return Pedido.query.one()


def test_pedido_financeirizado_nao_pode_ser_rebaixado(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro
    from app.pedido.pedido_model import Pedido

    cliente, produto = _seed_cliente_produto(db)
    usuario = _seed_admin(db)

    client = app_ctx.test_client()
    _autenticar(client, usuario)

    pedido = _criar_pedido_concluido(
        client,
        cliente,
        produto,
    )

    assert (
        LancamentoFinanceiro.query
        .filter_by(
            pedido_id=pedido.id,
            ativo=True,
        )
        .count()
        == 1
    )

    response = client.post(
        f"/pedido/{pedido.id}/editar",
        data=_payload(
            cliente,
            produto,
            "RASCUNHO",
        ),
        follow_redirects=False,
    )

    assert response.status_code == 302

    db.session.expire_all()

    pedido = db.session.get(
        Pedido,
        pedido.id,
    )

    assert pedido.status == Pedido.STATUS_CONCLUIDO

    assert (
        LancamentoFinanceiro.query
        .filter_by(
            pedido_id=pedido.id,
            ativo=True,
        )
        .count()
        == 1
    )


def test_pedido_financeirizado_nao_pode_ser_excluido(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro
    from app.pedido.pedido_model import Pedido

    cliente, produto = _seed_cliente_produto(db)
    usuario = _seed_admin(db)

    client = app_ctx.test_client()
    _autenticar(client, usuario)

    pedido = _criar_pedido_concluido(
        client,
        cliente,
        produto,
    )

    pedido_id = pedido.id

    response = client.post(
        f"/pedido/{pedido_id}/excluir",
        follow_redirects=False,
    )

    assert response.status_code == 302

    db.session.expire_all()

    pedido = db.session.get(
        Pedido,
        pedido_id,
    )

    assert pedido.ativo is True

    assert (
        LancamentoFinanceiro.query
        .filter_by(
            pedido_id=pedido_id,
            ativo=True,
        )
        .count()
        == 1
    )


def test_pedido_sem_financeiro_continua_podendo_ser_excluido(app_ctx):
    from app.extensoes import db
    from app.pedido.pedido_model import Pedido

    cliente, produto = _seed_cliente_produto(db)
    usuario = _seed_admin(db)

    client = app_ctx.test_client()
    _autenticar(client, usuario)

    response = client.post(
        "/pedido/novo",
        data=_payload(
            cliente,
            produto,
            "RASCUNHO",
        ),
        follow_redirects=False,
    )

    assert response.status_code == 302

    pedido = Pedido.query.one()
    pedido_id = pedido.id

    response = client.post(
        f"/pedido/{pedido_id}/excluir",
        follow_redirects=False,
    )

    assert response.status_code == 302

    db.session.expire_all()

    pedido = db.session.get(
        Pedido,
        pedido_id,
    )

    assert pedido.ativo is False
