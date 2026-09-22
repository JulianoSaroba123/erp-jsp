# -*- coding: utf-8 -*-
"""D26F03-A4 - Gatilho Pedido -> Estoque."""

from decimal import Decimal

import pytest


@pytest.fixture()
def app_ctx():
    from app import create_app
    from app.extensoes import db

    app = create_app("testing")

    with app.app_context():
        from app.auth.usuario_model import Usuario  # noqa: F401
        from app.cliente.cliente_model import Cliente  # noqa: F401
        from app.estoque.estoque_model import MovimentacaoEstoque  # noqa: F401
        from app.financeiro.financeiro_model import LancamentoFinanceiro  # noqa: F401
        from app.pedido.pedido_model import Pedido, PedidoItem  # noqa: F401
        from app.produto.produto_model import Produto  # noqa: F401

        db.drop_all()
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


def _seed_cliente_produto(db, estoque="10.000"):
    from app.cliente.cliente_model import Cliente
    from app.produto.produto_model import Produto

    cliente = Cliente(
        nome="Cliente Estoque A4",
        tipo="PJ",
        cpf_cnpj="55666777000188",
    )

    produto = Produto(
        nome="Produto Estoque A4",
        preco_custo=Decimal("20.00"),
        preco_venda=Decimal("40.00"),
        estoque_atual=Decimal(estoque),
        estoque_minimo=Decimal("1.000"),
        estoque_maximo=Decimal("100.000"),
        controla_estoque=True,
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
        nome="Administrador Estoque A4",
        email="admin.estoque.a4@teste.local",
        usuario="admin_estoque_a4",
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


def _payload(
    cliente,
    produto,
    status,
    quantidade="2.000",
):
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
            "Produto Estoque A4"
        ],
        "item_quantidade[]": [
            quantidade
        ],
        "item_valor_unitario[]": [
            "40,00"
        ],
        "item_desconto[]": ["0"],
    }


def test_novo_pedido_concluido_baixa_estoque_e_gera_financeiro(
    app_ctx,
):
    from app.extensoes import db
    from app.estoque.estoque_model import MovimentacaoEstoque
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

    db.session.refresh(produto)

    assert (
        Decimal(str(produto.estoque_atual))
        == Decimal("8.000")
    )

    movimento = MovimentacaoEstoque.query.one()

    assert movimento.pedido_id == pedido.id
    assert movimento.produto_id == produto.id
    assert movimento.tipo == "SAIDA"
    assert movimento.origem == "PEDIDO"
    assert (
        Decimal(str(movimento.quantidade))
        == Decimal("2.000")
    )

    financeiro = (
        LancamentoFinanceiro.query
        .filter_by(
            pedido_id=pedido.id,
            origem="PEDIDO",
            ativo=True,
        )
        .one()
    )

    assert financeiro.status == "pendente"
    assert financeiro.tipo == "conta_receber"


def test_estoque_insuficiente_desfaz_pedido_e_financeiro(
    app_ctx,
):
    from app.extensoes import db
    from app.estoque.estoque_model import MovimentacaoEstoque
    from app.financeiro.financeiro_model import LancamentoFinanceiro
    from app.pedido.pedido_model import Pedido
    from app.produto.produto_model import Produto

    cliente, produto = _seed_cliente_produto(
        db,
        estoque="1.000",
    )

    produto_id = produto.id

    usuario = _seed_admin(db)

    client = app_ctx.test_client()
    _autenticar(client, usuario)

    response = client.post(
        "/pedido/novo",
        data=_payload(
            cliente,
            produto,
            "CONCLUIDO",
            quantidade="2.000",
        ),
        follow_redirects=False,
    )

    assert response.status_code == 200

    assert Pedido.query.count() == 0
    assert MovimentacaoEstoque.query.count() == 0
    assert LancamentoFinanceiro.query.count() == 0

    produto = db.session.get(
        Produto,
        produto_id,
    )

    assert (
        Decimal(str(produto.estoque_atual))
        == Decimal("1.000")
    )


def test_editar_rascunho_para_concluido_movimenta_uma_vez(
    app_ctx,
):
    from app.extensoes import db
    from app.estoque.estoque_model import MovimentacaoEstoque
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

    db.session.refresh(produto)

    assert (
        Decimal(str(produto.estoque_atual))
        == Decimal("10.000")
    )

    assert MovimentacaoEstoque.query.count() == 0

    response = client.post(
        f"/pedido/{pedido.id}/editar",
        data=_payload(
            cliente,
            produto,
            "CONCLUIDO",
        ),
        follow_redirects=False,
    )

    assert response.status_code == 302

    db.session.refresh(produto)

    assert (
        Decimal(str(produto.estoque_atual))
        == Decimal("8.000")
    )

    assert MovimentacaoEstoque.query.count() == 1

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

    # Tentar alterar quantidade depois da movimentacao.
    response = client.post(
        f"/pedido/{pedido.id}/editar",
        data=_payload(
            cliente,
            produto,
            "CONCLUIDO",
            quantidade="3.000",
        ),
        follow_redirects=False,
    )

    assert response.status_code == 302

    db.session.expire_all()

    pedido = db.session.get(
        Pedido,
        pedido.id,
    )

    produto = db.session.get(
        type(produto),
        produto.id,
    )

    item = pedido.itens.one()

    assert (
        Decimal(str(item.quantidade))
        == Decimal("2.000")
    )

    assert (
        Decimal(str(produto.estoque_atual))
        == Decimal("8.000")
    )

    assert MovimentacaoEstoque.query.count() == 1

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



def test_pedido_legado_concluido_sem_movimento_nao_baixa_estoque_ao_editar(
    app_ctx,
):
    """Pedido ja concluido antes do D26F03 nao sofre baixa retroativa."""

    from app.extensoes import db
    from app.estoque.estoque_model import MovimentacaoEstoque
    from app.financeiro.financeiro_model import LancamentoFinanceiro
    from app.financeiro.pedido_financeiro_service import (
        sincronizar_lancamentos_pedido,
    )
    from app.pedido.pedido_model import Pedido
    from app.produto.produto_model import Produto

    cliente, produto = _seed_cliente_produto(
        db,
        estoque="10.000",
    )

    produto_id = produto.id

    usuario = _seed_admin(db)

    client = app_ctx.test_client()
    _autenticar(client, usuario)

    # Primeiro cria um pedido sem movimentar estoque.
    response = client.post(
        "/pedido/novo",
        data=_payload(
            cliente,
            produto,
            "RASCUNHO",
            quantidade="2.000",
        ),
        follow_redirects=False,
    )

    assert response.status_code == 302

    pedido = Pedido.query.one()

    # Simula um pedido legado:
    # ele ja estava CONCLUIDO antes da entrada do D26F03
    # e ja possuia financeiro, mas nunca teve movimento
    # de estoque registrado.
    pedido.status = Pedido.STATUS_CONCLUIDO

    sincronizar_lancamentos_pedido(
        pedido
    )

    db.session.commit()

    pedido_id = pedido.id

    db.session.refresh(produto)

    assert (
        Decimal(str(produto.estoque_atual))
        == Decimal("10.000")
    )

    assert (
        MovimentacaoEstoque.query
        .filter_by(
            pedido_id=pedido_id,
        )
        .count()
        == 0
    )

    assert (
        LancamentoFinanceiro.query
        .filter_by(
            pedido_id=pedido_id,
            origem="PEDIDO",
            ativo=True,
        )
        .count()
        == 1
    )

    payload = _payload(
        cliente,
        produto,
        "CONCLUIDO",
        quantidade="2.000",
    )

    payload["observacoes"] = (
        "Edicao administrativa de pedido legado."
    )

    # Editar um pedido que JA ERA concluido nao pode
    # disparar baixa retroativa de estoque.
    response = client.post(
        f"/pedido/{pedido_id}/editar",
        data=payload,
        follow_redirects=False,
    )

    assert response.status_code == 302

    db.session.expire_all()

    produto = db.session.get(
        Produto,
        produto_id,
    )

    pedido = db.session.get(
        Pedido,
        pedido_id,
    )

    assert pedido.status == Pedido.STATUS_CONCLUIDO

    assert (
        Decimal(str(produto.estoque_atual))
        == Decimal("10.000")
    )

    assert (
        MovimentacaoEstoque.query
        .filter_by(
            pedido_id=pedido_id,
        )
        .count()
        == 0
    )

    # Financeiro tambem permanece idempotente.
    assert (
        LancamentoFinanceiro.query
        .filter_by(
            pedido_id=pedido_id,
            origem="PEDIDO",
            ativo=True,
        )
        .count()
        == 1
    )



def test_pedido_com_movimento_estoque_nao_pode_ser_excluido(
    app_ctx,
):
    from app.extensoes import db
    from app.estoque.pedido_estoque_service import (
        sincronizar_estoque_pedido,
    )
    from app.pedido.pedido_model import Pedido, PedidoItem

    cliente, produto = _seed_cliente_produto(db)
    usuario = _seed_admin(db)

    pedido = Pedido(
        cliente_id=cliente.id,
        status=Pedido.STATUS_CONCLUIDO,
        subtotal=Decimal("80.00"),
        desconto=Decimal("0.00"),
        valor_total=Decimal("80.00"),
    )

    db.session.add(pedido)
    db.session.flush()

    item = PedidoItem(
        pedido_id=pedido.id,
        tipo_item=PedidoItem.TIPO_PRODUTO,
        produto_id=produto.id,
        descricao=produto.nome,
        quantidade=Decimal("2.000"),
        valor_unitario=Decimal("40.00"),
        desconto=Decimal("0.00"),
        ordem=1,
    )

    db.session.add(item)
    db.session.flush()

    sincronizar_estoque_pedido(pedido)
    db.session.commit()

    pedido_id = pedido.id

    client = app_ctx.test_client()
    _autenticar(client, usuario)

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
