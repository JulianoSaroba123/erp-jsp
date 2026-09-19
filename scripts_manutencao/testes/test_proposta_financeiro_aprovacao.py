# -*- coding: utf-8 -*-
"""D25F03-A3 - Aprovacao da proposta integra com Financeiro."""

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
    ContaBancaria,
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


def _cenario(codigo):
    cliente = Cliente(
        nome="COMPUSERVICE",
        razao_social="MSTI INFORMATICA LTDA",
        ativo=True,
    )

    conta = ContaBancaria(
        nome="Cora Teste",
        tipo="conta_corrente",
        saldo_inicial=Decimal("1000.00"),
        saldo_atual=Decimal("1000.00"),
        limite_credito=Decimal("0.00"),
        ativa=True,
        principal=False,
        ativo=True,
    )

    db.session.add_all(
        [cliente, conta]
    )
    db.session.flush()

    proposta = Proposta(
        codigo=codigo,
        cliente_id=cliente.id,
        titulo=(
            "Instala??o de Tanque Externo "
            "de Combust?vel e Sensor de N?vel"
        ),
        status="pendente",
        data_emissao=date(2026, 9, 17),
        valor_total=Decimal("2300.00"),
        entrada=Decimal("50.00"),
        forma_pagamento="parcelado",
        numero_parcelas=1,
        intervalo_parcelas=28,
        ativo=True,
    )

    db.session.add(proposta)
    db.session.flush()

    entrada = ParcelaProposta(
        proposta_id=proposta.id,
        numero_parcela=0,
        valor_parcela=Decimal("1150.00"),
        data_vencimento=date(2026, 9, 17),
        descricao="Entrada (50%)",
        status="pendente",
        ativo=True,
    )

    saldo = ParcelaProposta(
        proposta_id=proposta.id,
        numero_parcela=1,
        valor_parcela=Decimal("1150.00"),
        data_vencimento=date(2026, 10, 15),
        descricao="Parcela 1/1",
        status="pendente",
        ativo=True,
    )

    db.session.add_all(
        [entrada, saldo]
    )

    db.session.commit()

    return (
        conta.id,
        proposta.id,
        entrada.id,
        saldo.id,
    )


def test_aprovar_proposta_cria_recebiveis_sem_duplicar():
    app = _app()

    with app.app_context():
        (
            conta_id,
            proposta_id,
            entrada_id,
            saldo_id,
        ) = _cenario(
            "PROP-D25F03-A3-MODEL"
        )

        proposta = db.session.get(
            Proposta,
            proposta_id,
        )

        proposta.aprovar()

        assert proposta.status == "aprovada"
        assert proposta.data_aprovacao is not None

        lancamentos = (
            LancamentoFinanceiro.query
            .filter_by(
                proposta_id=proposta.id,
                origem="PROPOSTA",
            )
            .all()
        )

        assert len(lancamentos) == 2

        por_parcela = {
            item.proposta_parcela_id:
            item
            for item in lancamentos
        }

        assert (
            por_parcela[entrada_id].valor
            == Decimal("1150.00")
        )

        assert (
            por_parcela[saldo_id].valor
            == Decimal("1150.00")
        )

        conta = db.session.get(
            ContaBancaria,
            conta_id,
        )

        # Recebiveis pendentes nao movimentam saldo.
        assert (
            conta.saldo_atual
            == Decimal("1000.00")
        )

        ids_antes = {
            item.id
            for item in lancamentos
        }

        proposta.aprovar()

        depois = (
            LancamentoFinanceiro.query
            .filter_by(
                proposta_id=proposta.id,
                origem="PROPOSTA",
            )
            .all()
        )

        assert len(depois) == 2

        assert {
            item.id
            for item in depois
        } == ids_antes


def test_api_aprovacao_normaliza_status_e_gera_financeiro():
    app = _app()

    with app.app_context():
        (
            _,
            proposta_id,
            _,
            _,
        ) = _cenario(
            "PROP-D25F03-A3-API"
        )

    client = app.test_client()

    response = client.put(
        f"/propostas/api/{proposta_id}/status",
        json={
            "status": "Aprovada",
        },
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["success"] is True
    assert payload["status"] == "aprovada"

    with app.app_context():
        proposta = db.session.get(
            Proposta,
            proposta_id,
        )

        assert proposta.status == "aprovada"
        assert proposta.data_aprovacao is not None

        assert (
            LancamentoFinanceiro.query
            .filter_by(
                proposta_id=proposta.id,
                origem="PROPOSTA",
            )
            .count()
            == 2
        )

    # Repetir pela API precisa continuar idempotente.
    response2 = client.put(
        f"/propostas/api/{proposta_id}/status",
        json={
            "status": "APROVADA",
        },
    )

    assert response2.status_code == 200

    with app.app_context():
        assert (
            LancamentoFinanceiro.query
            .filter_by(
                proposta_id=proposta_id,
                origem="PROPOSTA",
            )
            .count()
            == 2
        )
