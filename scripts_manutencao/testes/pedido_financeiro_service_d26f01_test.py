# -*- coding: utf-8 -*-
"""D26F01-A1 - Contrato Pedido de Venda -> Financeiro."""

from datetime import date
from decimal import Decimal

import pytest


@pytest.fixture()
def app_ctx():
    from app import create_app
    from app.extensoes import db

    app = create_app("testing")

    with app.app_context():
        from app.pedido.pedido_model import Pedido  # noqa: F401

        db.drop_all()
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


def _criar_cliente(db):
    from app.cliente.cliente_model import Cliente

    cliente = Cliente(
        nome="PROPOSTA ENGENHARIA AMBIENTAL LTDA.",
        tipo="PJ",
        cpf_cnpj="12345678000199",
    )
    db.session.add(cliente)
    db.session.commit()
    return cliente


def test_venda_direta_concluida_gera_recebivel_idempotente(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro
    from app.financeiro.pedido_financeiro_service import (
        sincronizar_lancamentos_pedido,
    )
    from app.pedido.pedido_model import Pedido

    cliente = _criar_cliente(db)

    pedido = Pedido(
        numero="PED0001",
        cliente_id=cliente.id,
        data_pedido=date(2026, 9, 7),
        status=Pedido.STATUS_CONCLUIDO,
        subtotal=Decimal("1680.00"),
        desconto=Decimal("0.00"),
        valor_total=Decimal("1680.00"),
        condicoes_pagamento="PIX",
    )
    db.session.add(pedido)
    db.session.commit()

    resultado = sincronizar_lancamentos_pedido(pedido)
    db.session.commit()

    assert len(resultado) == 1

    lancamento = resultado[0]

    assert lancamento.pedido_id == pedido.id
    assert lancamento.cliente_id == cliente.id
    assert lancamento.numero_documento == "PED0001"
    assert lancamento.valor == Decimal("1680.00")
    assert lancamento.tipo == "conta_receber"
    assert lancamento.status == "pendente"
    assert lancamento.origem == "PEDIDO"

    # Segunda execução não pode duplicar recebível.
    sincronizar_lancamentos_pedido(pedido)
    db.session.commit()

    assert (
        LancamentoFinanceiro.query.filter_by(
            pedido_id=pedido.id,
            origem="PEDIDO",
            ativo=True,
        ).count()
        == 1
    )


def test_pedido_nao_concluido_nao_gera_recebivel(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro
    from app.financeiro.pedido_financeiro_service import (
        sincronizar_lancamentos_pedido,
    )
    from app.pedido.pedido_model import Pedido

    cliente = _criar_cliente(db)

    pedido = Pedido(
        cliente_id=cliente.id,
        status=Pedido.STATUS_CONFIRMADO,
        valor_total=Decimal("1680.00"),
    )
    db.session.add(pedido)
    db.session.commit()

    assert sincronizar_lancamentos_pedido(pedido) == []

    assert (
        LancamentoFinanceiro.query.filter_by(
            origem="PEDIDO",
            ativo=True,
        ).count()
        == 0
    )


def test_pedido_vinculado_a_proposta_nao_duplica_financeiro(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro
    from app.financeiro.pedido_financeiro_service import (
        sincronizar_lancamentos_pedido,
    )
    from app.pedido.pedido_model import Pedido
    from app.proposta.proposta_model import Proposta

    cliente = _criar_cliente(db)

    proposta = Proposta(
        cliente_id=cliente.id,
        titulo="Venda originada de proposta",
        status="aprovada",
        valor_total=Decimal("1680.00"),
    )
    db.session.add(proposta)
    db.session.commit()

    pedido = Pedido(
        cliente_id=cliente.id,
        proposta_id=proposta.id,
        status=Pedido.STATUS_CONCLUIDO,
        valor_total=Decimal("1680.00"),
    )
    db.session.add(pedido)
    db.session.commit()

    assert sincronizar_lancamentos_pedido(pedido) == []

    assert (
        LancamentoFinanceiro.query.filter_by(
            origem="PEDIDO",
            ativo=True,
        ).count()
        == 0
    )
