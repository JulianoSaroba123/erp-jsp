# -*- coding: utf-8 -*-
"""D25F03-A5.1 - Protecao de propostas financeirizadas."""

import os
import sys
from datetime import date
from decimal import Decimal


sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
        )
    ),
)


from app import create_app
from app.extensoes import db
from app.cliente.cliente_model import Cliente
from app.financeiro.financeiro_model import (
    LancamentoFinanceiro,
)
from app.proposta.proposta_model import (
    Proposta,
    ParcelaProposta,
)


def _app():
    app = create_app("testing")

    with app.app_context():
        db.create_all()

    return app


def _cenario():
    cliente = Cliente(
        nome="COMPUSERVICE",
        razao_social="MSTI INFORMATICA LTDA",
        ativo=True,
    )

    db.session.add(cliente)
    db.session.flush()

    proposta = Proposta(
        codigo="PROP-D25F03-A5",
        cliente_id=cliente.id,
        titulo="Contrato protegido",
        status="pendente",
        data_emissao=date(2026, 9, 17),
        valor_total=Decimal("2300.00"),
        entrada=Decimal("50.00"),
        forma_pagamento="parcelado",
        numero_parcelas=1,
        intervalo_parcelas=30,
        data_primeira_parcela=date(
            2026,
            9,
            17,
        ),
        ativo=True,
    )

    db.session.add(proposta)
    db.session.flush()

    entrada = ParcelaProposta(
        proposta_id=proposta.id,
        numero_parcela=0,
        valor_parcela=Decimal("1150.00"),
        data_vencimento=date(2026, 9, 17),
        descricao="Entrada",
        status="pendente",
        ativo=True,
    )

    saldo = ParcelaProposta(
        proposta_id=proposta.id,
        numero_parcela=1,
        valor_parcela=Decimal("1150.00"),
        data_vencimento=date(2026, 10, 17),
        descricao="Parcela 1/1",
        status="pendente",
        ativo=True,
    )

    db.session.add_all(
        [entrada, saldo]
    )

    db.session.commit()

    proposta.aprovar()

    return (
        cliente.id,
        proposta.id,
        entrada.id,
        saldo.id,
    )


def test_gerar_parcelas_preserva_ids_quando_ha_financeiro():
    app = _app()

    with app.app_context():
        (
            _,
            proposta_id,
            entrada_id,
            saldo_id,
        ) = _cenario()

        proposta = db.session.get(
            Proposta,
            proposta_id,
        )

        assert (
            LancamentoFinanceiro.query
            .filter_by(
                proposta_id=proposta.id,
                ativo=True,
            )
            .count()
            == 2
        )

        proposta.numero_parcelas = 3
        proposta.entrada = Decimal("20.00")

        resultado = proposta.gerar_parcelas()

        ids = [
            parcela.id
            for parcela in resultado
        ]

        assert ids == [
            entrada_id,
            saldo_id,
        ]

        assert (
            ParcelaProposta.query
            .filter_by(
                proposta_id=proposta.id,
                ativo=True,
            )
            .count()
            == 2
        )

        entrada = db.session.get(
            ParcelaProposta,
            entrada_id,
        )

        saldo = db.session.get(
            ParcelaProposta,
            saldo_id,
        )

        assert (
            entrada.valor_parcela
            == Decimal("1150.00")
        )

        assert (
            saldo.valor_parcela
            == Decimal("1150.00")
        )


def test_edicao_http_e_bloqueada_quando_ha_financeiro():
    app = _app()

    with app.app_context():
        (
            cliente_id,
            proposta_id,
            _,
            _,
        ) = _cenario()

    client = app.test_client()

    response = client.post(
        f"/propostas/{proposta_id}/editar",
        data={
            "titulo": "TITULO QUE NAO PODE ENTRAR",
            "cliente_id": str(
                cliente_id
            ),
        },
        follow_redirects=False,
    )

    assert response.status_code in {
        302,
        303,
    }

    with app.app_context():
        proposta = db.session.get(
            Proposta,
            proposta_id,
        )

        assert (
            proposta.titulo
            == "Contrato protegido"
        )

        assert (
            LancamentoFinanceiro.query
            .filter_by(
                proposta_id=proposta.id,
                ativo=True,
            )
            .count()
            == 2
        )
