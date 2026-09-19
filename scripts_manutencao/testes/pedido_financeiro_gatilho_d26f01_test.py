# -*- coding: utf-8 -*-
"""D26F01-A3 - Gatilho Pedido de Venda -> Financeiro."""

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

        db.drop_all()
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


def _seed_cliente_produto(db):
    from app.cliente.cliente_model import Cliente
    from app.produto.produto_model import Produto

    cliente = Cliente(
        nome="PROPOSTA ENGENHARIA AMBIENTAL LTDA.",
        tipo="PJ",
        cpf_cnpj="12345678000199",
    )

    produto = Produto(
        nome="Produto Pedido Financeiro",
        preco_venda=840,
    )

    db.session.add(cliente)
    db.session.add(produto)
    db.session.commit()

    return cliente, produto


def _seed_admin(db):
    from app.auth.usuario_model import Usuario

    usuario = Usuario(
        nome="Administrador D26F01",
        email="admin.d26f01@teste.local",
        usuario="admin_d26f01",
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
        "data_pedido": "2026-09-07",
        "condicoes_pagamento": "PIX",
        "desconto": "0,00",
        "item_tipo[]": ["PRODUTO"],
        "item_referencia_id[]": [f"P:{produto.id}"],
        "item_descricao[]": ["Produto Pedido Financeiro"],
        "item_quantidade[]": ["2"],
        "item_valor_unitario[]": ["840,00"],
        "item_desconto[]": ["0"],
    }


def test_criar_pedido_concluido_gera_conta_receber(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro
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
            "CONCLUIDO",
        ),
        follow_redirects=False,
    )

    assert response.status_code == 302

    pedido = Pedido.query.one()

    assert pedido.status == Pedido.STATUS_CONCLUIDO
    assert float(pedido.valor_total) == pytest.approx(1680.00)

    recebivel = (
        LancamentoFinanceiro.query
        .filter_by(
            pedido_id=pedido.id,
            origem="PEDIDO",
            ativo=True,
        )
        .one()
    )

    assert recebivel.tipo == "conta_receber"
    assert recebivel.status == "pendente"
    assert float(recebivel.valor) == pytest.approx(1680.00)
    assert recebivel.numero_documento == pedido.numero
    assert recebivel.cliente_id == cliente.id


def test_editar_pedido_para_concluido_gera_um_unico_recebivel(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro
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

    assert (
        LancamentoFinanceiro.query
        .filter_by(
            pedido_id=pedido.id,
            origem="PEDIDO",
        )
        .count()
        == 0
    )

    payload_concluido = _payload(
        cliente,
        produto,
        "CONCLUIDO",
    )

    response = client.post(
        f"/pedido/{pedido.id}/editar",
        data=payload_concluido,
        follow_redirects=False,
    )

    assert response.status_code == 302

    recebiveis = (
        LancamentoFinanceiro.query
        .filter_by(
            pedido_id=pedido.id,
            origem="PEDIDO",
            ativo=True,
        )
        .all()
    )

    assert len(recebiveis) == 1
    assert float(recebiveis[0].valor) == pytest.approx(1680.00)

    # Repetir a edicao de um pedido ja concluido
    # nao pode criar um segundo recebivel.
    response = client.post(
        f"/pedido/{pedido.id}/editar",
        data=payload_concluido,
        follow_redirects=False,
    )

    assert response.status_code == 302

    assert (
        LancamentoFinanceiro.query
        .filter_by(
            pedido_id=pedido.id,
            origem="PEDIDO",
            ativo=True,
        )
        .count()
        == 1
    )
