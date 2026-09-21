# -*- coding: utf-8 -*-
"""D26F03-A1 - Contrato Pedido de Venda -> Estoque."""

from decimal import Decimal

import pytest


@pytest.fixture()
def app_ctx():
    from app import create_app
    from app.extensoes import db

    app = create_app("testing")

    with app.app_context():
        from app.cliente.cliente_model import Cliente  # noqa: F401
        from app.pedido.pedido_model import Pedido, PedidoItem  # noqa: F401
        from app.produto.produto_model import Produto  # noqa: F401

        # Modelo alvo do D26F03.
        from app.estoque.estoque_model import MovimentacaoEstoque  # noqa: F401

        db.drop_all()
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


def _seed_cliente(db):
    from app.cliente.cliente_model import Cliente

    cliente = Cliente(
        nome="Cliente Estoque D26F03",
        tipo="PJ",
        cpf_cnpj="11222333000199",
    )

    db.session.add(cliente)
    db.session.commit()

    return cliente


def _seed_produto(
    db,
    *,
    nome="Produto Estoque D26F03",
    estoque="10.000",
    controla_estoque=True,
):
    from app.produto.produto_model import Produto

    produto = Produto(
        nome=nome,
        preco_custo=Decimal("20.00"),
        preco_venda=Decimal("40.00"),
        estoque_atual=Decimal(estoque),
        estoque_minimo=Decimal("1.000"),
        estoque_maximo=Decimal("100.000"),
        controla_estoque=controla_estoque,
    )

    db.session.add(produto)
    db.session.commit()

    return produto


def _criar_pedido(
    db,
    cliente,
    *,
    status,
):
    from app.pedido.pedido_model import Pedido

    pedido = Pedido(
        cliente_id=cliente.id,
        status=status,
        subtotal=Decimal("0.00"),
        desconto=Decimal("0.00"),
        valor_total=Decimal("0.00"),
    )

    db.session.add(pedido)
    db.session.flush()

    return pedido


def _adicionar_produto(
    db,
    pedido,
    produto,
    quantidade,
    ordem=1,
):
    from app.pedido.pedido_model import PedidoItem

    item = PedidoItem(
        pedido_id=pedido.id,
        tipo_item=PedidoItem.TIPO_PRODUTO,
        produto_id=produto.id,
        descricao=produto.nome,
        quantidade=Decimal(str(quantidade)),
        valor_unitario=Decimal(str(produto.preco_venda or 0)),
        desconto=Decimal("0.00"),
        ordem=ordem,
    )

    db.session.add(item)
    db.session.flush()

    return item


def test_pedido_concluido_baixa_estoque_e_cria_movimento_idempotente(
    app_ctx,
):
    from app.extensoes import db
    from app.estoque.estoque_model import MovimentacaoEstoque
    from app.estoque.pedido_estoque_service import (
        sincronizar_estoque_pedido,
    )
    from app.pedido.pedido_model import Pedido

    cliente = _seed_cliente(db)
    produto = _seed_produto(db, estoque="10.000")

    pedido = _criar_pedido(
        db,
        cliente,
        status=Pedido.STATUS_CONCLUIDO,
    )

    # Duas linhas do mesmo produto.
    # O estoque deve gerar UMA movimentacao agregada.
    _adicionar_produto(
        db,
        pedido,
        produto,
        "1.250",
        ordem=1,
    )
    _adicionar_produto(
        db,
        pedido,
        produto,
        "1.250",
        ordem=2,
    )

    movimentos = sincronizar_estoque_pedido(pedido)
    db.session.commit()

    assert len(movimentos) == 1

    db.session.refresh(produto)

    assert Decimal(str(produto.estoque_atual)) == Decimal("7.500")

    movimento = MovimentacaoEstoque.query.one()

    assert movimento.pedido_id == pedido.id
    assert movimento.produto_id == produto.id
    assert movimento.tipo == "SAIDA"
    assert movimento.origem == "PEDIDO"
    assert Decimal(str(movimento.quantidade)) == Decimal("2.500")
    assert Decimal(str(movimento.estoque_anterior)) == Decimal("10.000")
    assert Decimal(str(movimento.estoque_posterior)) == Decimal("7.500")
    assert movimento.documento == pedido.numero

    # Segunda sincronizacao nao pode baixar novamente.
    sincronizar_estoque_pedido(pedido)
    db.session.commit()

    db.session.refresh(produto)

    assert Decimal(str(produto.estoque_atual)) == Decimal("7.500")

    assert (
        MovimentacaoEstoque.query.filter_by(
            pedido_id=pedido.id,
            produto_id=produto.id,
            tipo="SAIDA",
            ativo=True,
        ).count()
        == 1
    )


def test_pedido_nao_concluido_nao_movimenta_estoque(app_ctx):
    from app.extensoes import db
    from app.estoque.estoque_model import MovimentacaoEstoque
    from app.estoque.pedido_estoque_service import (
        sincronizar_estoque_pedido,
    )
    from app.pedido.pedido_model import Pedido

    cliente = _seed_cliente(db)
    produto = _seed_produto(db, estoque="10.000")

    pedido = _criar_pedido(
        db,
        cliente,
        status=Pedido.STATUS_CONFIRMADO,
    )

    _adicionar_produto(
        db,
        pedido,
        produto,
        "2.000",
    )

    assert sincronizar_estoque_pedido(pedido) == []

    db.session.flush()
    db.session.refresh(produto)

    assert Decimal(str(produto.estoque_atual)) == Decimal("10.000")
    assert MovimentacaoEstoque.query.count() == 0


def test_produto_sem_controle_nao_movimenta_estoque(app_ctx):
    from app.extensoes import db
    from app.estoque.estoque_model import MovimentacaoEstoque
    from app.estoque.pedido_estoque_service import (
        sincronizar_estoque_pedido,
    )
    from app.pedido.pedido_model import Pedido

    cliente = _seed_cliente(db)

    produto = _seed_produto(
        db,
        estoque="10.000",
        controla_estoque=False,
    )

    pedido = _criar_pedido(
        db,
        cliente,
        status=Pedido.STATUS_CONCLUIDO,
    )

    _adicionar_produto(
        db,
        pedido,
        produto,
        "2.000",
    )

    assert sincronizar_estoque_pedido(pedido) == []

    db.session.flush()
    db.session.refresh(produto)

    assert Decimal(str(produto.estoque_atual)) == Decimal("10.000")
    assert MovimentacaoEstoque.query.count() == 0


def test_estoque_insuficiente_bloqueia_movimento(app_ctx):
    from app.extensoes import db
    from app.estoque.estoque_model import MovimentacaoEstoque
    from app.estoque.pedido_estoque_service import (
        sincronizar_estoque_pedido,
    )
    from app.pedido.pedido_model import Pedido

    cliente = _seed_cliente(db)
    produto = _seed_produto(db, estoque="1.000")

    pedido = _criar_pedido(
        db,
        cliente,
        status=Pedido.STATUS_CONCLUIDO,
    )

    _adicionar_produto(
        db,
        pedido,
        produto,
        "2.000",
    )

    with pytest.raises(
        ValueError,
        match="Estoque insuficiente",
    ):
        sincronizar_estoque_pedido(pedido)

    db.session.rollback()

    produto = db.session.get(
        type(produto),
        produto.id,
    )

    assert Decimal(str(produto.estoque_atual)) == Decimal("1.000")
    assert MovimentacaoEstoque.query.count() == 0


def test_servico_nao_gera_movimentacao_de_estoque(app_ctx):
    from app.extensoes import db
    from app.estoque.estoque_model import MovimentacaoEstoque
    from app.estoque.pedido_estoque_service import (
        sincronizar_estoque_pedido,
    )
    from app.pedido.pedido_model import Pedido, PedidoItem
    from app.servico.servico_model import Servico

    cliente = _seed_cliente(db)

    servico = Servico(
        nome="Servico sem estoque D26F03",
        valor_base=Decimal("150.00"),
        tipo_cobranca="servico",
    )

    db.session.add(servico)
    db.session.flush()

    pedido = _criar_pedido(
        db,
        cliente,
        status=Pedido.STATUS_CONCLUIDO,
    )

    item = PedidoItem(
        pedido_id=pedido.id,
        tipo_item=PedidoItem.TIPO_SERVICO,
        servico_id=servico.id,
        descricao=servico.nome,
        quantidade=Decimal("1.000"),
        valor_unitario=Decimal("150.00"),
        desconto=Decimal("0.00"),
        ordem=1,
    )

    db.session.add(item)
    db.session.flush()

    assert sincronizar_estoque_pedido(pedido) == []
    assert MovimentacaoEstoque.query.count() == 0


def test_servico_estoque_nao_realiza_commit_proprio(app_ctx):
    from app.extensoes import db
    from app.estoque.estoque_model import MovimentacaoEstoque
    from app.estoque.pedido_estoque_service import (
        sincronizar_estoque_pedido,
    )
    from app.pedido.pedido_model import Pedido
    from app.produto.produto_model import Produto

    cliente = _seed_cliente(db)
    produto = _seed_produto(db, estoque="10.000")

    produto_id = produto.id

    pedido = _criar_pedido(
        db,
        cliente,
        status=Pedido.STATUS_CONCLUIDO,
    )

    _adicionar_produto(
        db,
        pedido,
        produto,
        "2.000",
    )

    sincronizar_estoque_pedido(pedido)

    assert Decimal(str(produto.estoque_atual)) == Decimal("8.000")

    db.session.rollback()
    db.session.expire_all()

    produto = db.session.get(
        Produto,
        produto_id,
    )

    assert Decimal(str(produto.estoque_atual)) == Decimal("10.000")
    assert MovimentacaoEstoque.query.count() == 0


def test_campos_de_estoque_do_produto_suportam_quantidade_fracionada():
    from sqlalchemy import Numeric

    from app.produto.produto_model import Produto

    assert isinstance(
        Produto.__table__.c.estoque_atual.type,
        Numeric,
    )

    assert isinstance(
        Produto.__table__.c.estoque_minimo.type,
        Numeric,
    )

    assert isinstance(
        Produto.__table__.c.estoque_maximo.type,
        Numeric,
    )
