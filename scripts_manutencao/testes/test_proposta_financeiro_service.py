# -*- coding: utf-8 -*-
"""D25F03-A2 - Proposta -> Financeiro."""

import os
import sys
from datetime import date, datetime
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
from app.financeiro.proposta_financeiro_service import (
    sincronizar_lancamentos_proposta,
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


def _cliente():
    cliente = Cliente(
        nome="COMPUSERVICE",
        razao_social="MSTI INFORMATICA LTDA",
        ativo=True,
    )

    db.session.add(cliente)
    db.session.flush()

    return cliente


def _conta():
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

    db.session.add(conta)
    db.session.flush()

    return conta


def _proposta(
    cliente_id,
    *,
    codigo,
    status="aprovada",
):
    proposta = Proposta(
        codigo=codigo,
        cliente_id=cliente_id,
        titulo=(
            "Instala??o de Tanque Externo "
            "de Combust?vel e Sensor de N?vel"
        ),
        status=status,
        data_emissao=date(2026, 9, 17),
        data_aprovacao=datetime(
            2026,
            9,
            17,
            10,
            0,
        ),
        valor_total=Decimal("2300.00"),
        entrada=Decimal("50.00"),
        forma_pagamento="parcelado",
        numero_parcelas=1,
        intervalo_parcelas=28,
        ativo=True,
    )

    db.session.add(proposta)
    db.session.flush()

    return proposta


def _parcelas(proposta_id):
    entrada = ParcelaProposta(
        proposta_id=proposta_id,
        numero_parcela=0,
        valor_parcela=Decimal("1150.00"),
        data_vencimento=date(2026, 9, 17),
        descricao="Entrada (50%)",
        status="pendente",
        ativo=True,
    )

    saldo = ParcelaProposta(
        proposta_id=proposta_id,
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

    db.session.flush()

    return entrada, saldo


def test_proposta_aprovada_gera_recebiveis_idempotentes():
    app = _app()

    with app.app_context():
        cliente = _cliente()
        conta = _conta()

        proposta = _proposta(
            cliente.id,
            codigo="PROP-D25F03-A2",
        )

        entrada, saldo = _parcelas(
            proposta.id
        )

        db.session.commit()

        primeira_execucao = (
            sincronizar_lancamentos_proposta(
                proposta
            )
        )

        db.session.commit()

        assert len(primeira_execucao) == 2

        lancamentos = (
            LancamentoFinanceiro.query
            .filter_by(
                proposta_id=proposta.id,
                origem="PROPOSTA",
            )
            .order_by(
                LancamentoFinanceiro
                .proposta_parcela_id
            )
            .all()
        )

        assert len(lancamentos) == 2

        por_parcela = {
            item.proposta_parcela_id:
            item
            for item in lancamentos
        }

        lanc_entrada = por_parcela[
            entrada.id
        ]

        lanc_saldo = por_parcela[
            saldo.id
        ]

        assert (
            lanc_entrada.valor
            == Decimal("1150.00")
        )

        assert (
            lanc_saldo.valor
            == Decimal("1150.00")
        )

        assert (
            lanc_entrada.numero_documento
            == "PROP-D25F03-A2"
        )

        assert (
            lanc_entrada.numero_parcela
            == "Entrada"
        )

        assert (
            lanc_saldo.numero_parcela
            == "1/1"
        )

        assert (
            lanc_entrada.status
            == "pendente"
        )

        assert (
            lanc_saldo.status
            == "pendente"
        )

        assert (
            lanc_entrada.conta_bancaria_id
            == conta.id
        )

        assert (
            lanc_saldo.conta_bancaria_id
            == conta.id
        )

        db.session.refresh(conta)

        # Contas a receber pendentes nao mexem no caixa.
        assert (
            conta.saldo_atual
            == Decimal("1000.00")
        )

        ids_antes = {
            item.id
            for item in lancamentos
        }

        segunda_execucao = (
            sincronizar_lancamentos_proposta(
                proposta
            )
        )

        db.session.commit()

        assert len(segunda_execucao) == 2

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


def test_proposta_nao_aprovada_nao_gera_recebivel():
    app = _app()

    with app.app_context():
        cliente = _cliente()
        _conta()

        proposta = _proposta(
            cliente.id,
            codigo="PROP-D25F03-PEND",
            status="pendente",
        )

        _parcelas(
            proposta.id
        )

        db.session.commit()

        resultado = (
            sincronizar_lancamentos_proposta(
                proposta
            )
        )

        db.session.commit()

        assert resultado == []

        assert (
            LancamentoFinanceiro.query
            .filter_by(
                proposta_id=proposta.id
            )
            .count()
            == 0
        )


def test_recebivel_quitado_nao_e_reescrito():
    app = _app()

    with app.app_context():
        cliente = _cliente()
        conta = _conta()

        proposta = _proposta(
            cliente.id,
            codigo="PROP-D25F03-HIST",
        )

        entrada, _ = _parcelas(
            proposta.id
        )

        db.session.commit()

        sincronizar_lancamentos_proposta(
            proposta
        )

        db.session.commit()

        lancamento = (
            LancamentoFinanceiro.query
            .filter_by(
                proposta_parcela_id=entrada.id
            )
            .one()
        )

        lancamento.status = "recebido"
        lancamento.data_pagamento = date(
            2026,
            9,
            17,
        )

        db.session.commit()

        db.session.refresh(conta)

        assert (
            conta.saldo_atual
            == Decimal("2150.00")
        )

        # Simula edicao posterior da proposta.
        entrada.valor_parcela = Decimal(
            "1200.00"
        )

        entrada.data_vencimento = date(
            2026,
            9,
            20,
        )

        db.session.commit()

        sincronizar_lancamentos_proposta(
            proposta
        )

        db.session.commit()

        db.session.refresh(lancamento)
        db.session.refresh(conta)

        # Historico quitado permanece imutavel.
        assert (
            lancamento.valor
            == Decimal("1150.00")
        )

        assert (
            lancamento.data_vencimento
            == date(2026, 9, 17)
        )

        assert (
            lancamento.status
            == "recebido"
        )

        assert (
            lancamento.data_pagamento
            == date(2026, 9, 17)
        )

        # Ressincronizar nao baixa novamente.
        assert (
            conta.saldo_atual
            == Decimal("2150.00")
        )
