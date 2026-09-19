# -*- coding: utf-8 -*-
"""D26F01-A4.2 - Testes de seguranca do backfill PED0001."""

from datetime import date
from decimal import Decimal

import pytest


@pytest.fixture()
def app_ctx():
    from app import create_app
    from app.extensoes import db

    app = create_app("testing")

    with app.app_context():
        from app.cliente.cliente_model import Cliente  # noqa: F401
        from app.financeiro.financeiro_model import LancamentoFinanceiro  # noqa: F401
        from app.pedido.pedido_model import Pedido  # noqa: F401

        db.drop_all()
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


def _criar_pedido_canonico():
    from app.extensoes import db
    from app.cliente.cliente_model import Cliente
    from app.pedido.pedido_model import Pedido

    cliente = Cliente(
        nome="PROPOSTA ENGENHARIA AMBIENTAL LTDA.",
        tipo="PJ",
        cpf_cnpj="12345678000199",
    )

    db.session.add(cliente)
    db.session.flush()

    pedido = Pedido(
        numero="PED0001",
        cliente_id=cliente.id,
        proposta_id=None,
        data_pedido=date(2026, 9, 7),
        status=Pedido.STATUS_CONCLUIDO,
        valor_total=Decimal("1680.00"),
        subtotal=Decimal("1680.00"),
        desconto=Decimal("0.00"),
        condicoes_pagamento="PIX",
        ativo=True,
    )

    db.session.add(pedido)
    db.session.commit()

    return pedido


def test_schema_testing_possui_pedido_id(app_ctx):
    from scripts_manutencao.pedido_financeiro_backfill_d26f01 import (
        validar_schema,
    )

    validar_schema()


def test_pedido_canonico_passa_validacao(app_ctx):
    from scripts_manutencao.pedido_financeiro_backfill_d26f01 import (
        validar_pedido,
    )

    pedido = _criar_pedido_canonico()
    validar_pedido(pedido)


def test_pedido_com_valor_incorreto_e_bloqueado(app_ctx):
    from scripts_manutencao.pedido_financeiro_backfill_d26f01 import (
        validar_pedido,
    )
    from app.extensoes import db

    pedido = _criar_pedido_canonico()

    pedido.valor_total = Decimal("1679.99")
    db.session.flush()

    with pytest.raises(
        RuntimeError,
        match="valor_total inesperado",
    ):
        validar_pedido(pedido)


def test_pedido_vinculado_a_proposta_e_bloqueado(app_ctx):
    from scripts_manutencao.pedido_financeiro_backfill_d26f01 import (
        validar_pedido,
    )

    pedido = _criar_pedido_canonico()

    pedido.proposta_id = 999

    with pytest.raises(
        RuntimeError,
        match="nao e venda direta",
    ):
        validar_pedido(pedido)


def test_candidato_legado_bloqueia_apply(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro

    from scripts_manutencao.pedido_financeiro_backfill_d26f01 import (
        aplicar,
        buscar_candidatos_legados,
        buscar_vinculados,
    )

    pedido = _criar_pedido_canonico()

    legado = LancamentoFinanceiro(
        descricao="Recebimento antigo do cliente",
        valor=Decimal("1680.00"),
        valor_original=Decimal("1680.00"),
        tipo="conta_receber",
        status="pendente",
        cliente_id=pedido.cliente_id,
        numero_documento=None,
        origem="MANUAL",
        data_lancamento=date(2026, 9, 7),
        ativo=True,
    )

    db.session.add(legado)
    db.session.commit()

    vinculados = buscar_vinculados(pedido)
    candidatos = buscar_candidatos_legados(pedido)

    assert vinculados == []
    assert len(candidatos) == 1
    assert candidatos[0].id == legado.id

    with pytest.raises(
        RuntimeError,
        match="possiveis lancamentos legados",
    ):
        aplicar(
            pedido,
            vinculados,
            candidatos,
        )

    assert (
        LancamentoFinanceiro.query
        .filter_by(
            pedido_id=pedido.id,
            origem="PEDIDO",
        )
        .count()
        == 0
    )


def test_apply_cria_um_recebivel_e_e_idempotente(app_ctx):
    from app.financeiro.financeiro_model import LancamentoFinanceiro

    from scripts_manutencao.pedido_financeiro_backfill_d26f01 import (
        aplicar,
        buscar_candidatos_legados,
        buscar_vinculados,
    )

    pedido = _criar_pedido_canonico()

    vinculados = buscar_vinculados(pedido)
    candidatos = buscar_candidatos_legados(pedido)

    assert vinculados == []
    assert candidatos == []

    primeiro = aplicar(
        pedido,
        vinculados,
        candidatos,
    )

    assert primeiro.pedido_id == pedido.id
    assert primeiro.origem == "PEDIDO"
    assert primeiro.tipo == "conta_receber"
    assert primeiro.status == "pendente"
    assert primeiro.valor == Decimal("1680.00")

    vinculados = buscar_vinculados(pedido)
    candidatos = buscar_candidatos_legados(pedido)

    segundo = aplicar(
        pedido,
        vinculados,
        candidatos,
    )

    assert segundo.id == primeiro.id

    assert (
        LancamentoFinanceiro.query
        .filter_by(
            pedido_id=pedido.id,
            origem="PEDIDO",
        )
        .count()
        == 1
    )
