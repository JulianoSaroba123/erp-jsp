# -*- coding: utf-8 -*-
"""D25F03-A1 - Fundacao Proposta -> Financeiro."""

import os
import sys
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError


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
from app.financeiro.financeiro_model import LancamentoFinanceiro
from app.proposta.proposta_model import Proposta, ParcelaProposta


def _app():
    app = create_app("testing")

    with app.app_context():
        db.create_all()

    return app


def test_lancamento_rastreia_proposta_e_parcela():
    app = _app()

    with app.app_context():
        cliente = Cliente(
            nome="Cliente D25F03",
            ativo=True,
        )
        db.session.add(cliente)
        db.session.flush()

        proposta = Proposta(
            codigo="PROP-D25F03-A1",
            cliente_id=cliente.id,
            titulo="Proposta Financeira D25F03",
            status="aprovada",
            data_emissao=date(2026, 9, 19),
            valor_total=Decimal("2300.00"),
            entrada=Decimal("50.00"),
            forma_pagamento="parcelado",
            numero_parcelas=1,
            intervalo_parcelas=28,
            ativo=True,
        )
        db.session.add(proposta)
        db.session.flush()

        parcela = ParcelaProposta(
            proposta_id=proposta.id,
            numero_parcela=0,
            valor_parcela=Decimal("1150.00"),
            data_vencimento=date(2026, 9, 19),
            descricao="Entrada (50%)",
            status="pendente",
            ativo=True,
        )
        db.session.add(parcela)
        db.session.flush()

        lancamento = LancamentoFinanceiro(
            descricao=(
                "Entrada PROP-D25F03-A1 - "
                "Proposta Financeira D25F03"
            ),
            valor=Decimal("1150.00"),
            tipo="conta_receber",
            status="pendente",
            categoria="Servi?os",
            subcategoria="Proposta Comercial",
            data_lancamento=date(2026, 9, 19),
            data_vencimento=date(2026, 9, 19),
            numero_documento="PROP-D25F03-A1",
            cliente_id=cliente.id,
            proposta_id=proposta.id,
            proposta_parcela_id=parcela.id,
            origem="PROPOSTA",
            ativo=True,
        )

        db.session.add(lancamento)
        db.session.commit()

        assert lancamento.proposta_id == proposta.id
        assert lancamento.proposta_parcela_id == parcela.id

        assert lancamento.proposta.codigo == "PROP-D25F03-A1"
        assert (
            lancamento.proposta_parcela.valor_parcela
            == Decimal("1150.00")
        )

        assert (
            parcela.lancamento_financeiro.id
            == lancamento.id
        )

        assert (
            lancamento.origem_formatada
            == "Proposta Comercial"
        )


def test_parcela_proposta_nao_aceita_lancamento_duplicado():
    app = _app()

    with app.app_context():
        cliente = Cliente(
            nome="Cliente Idempotencia D25F03",
            ativo=True,
        )
        db.session.add(cliente)
        db.session.flush()

        proposta = Proposta(
            codigo="PROP-D25F03-IDEMP",
            cliente_id=cliente.id,
            titulo="Teste Idempotencia",
            status="aprovada",
            data_emissao=date(2026, 9, 19),
            valor_total=Decimal("1000.00"),
            entrada=Decimal("50.00"),
            forma_pagamento="parcelado",
            numero_parcelas=1,
            ativo=True,
        )
        db.session.add(proposta)
        db.session.flush()

        parcela = ParcelaProposta(
            proposta_id=proposta.id,
            numero_parcela=0,
            valor_parcela=Decimal("500.00"),
            data_vencimento=date(2026, 9, 19),
            descricao="Entrada",
            status="pendente",
            ativo=True,
        )
        db.session.add(parcela)
        db.session.flush()

        primeiro = LancamentoFinanceiro(
            descricao="Primeiro lan?amento",
            valor=Decimal("500.00"),
            tipo="conta_receber",
            status="pendente",
            data_lancamento=date(2026, 9, 19),
            cliente_id=cliente.id,
            proposta_id=proposta.id,
            proposta_parcela_id=parcela.id,
            origem="PROPOSTA",
            ativo=True,
        )

        db.session.add(primeiro)
        db.session.commit()

        duplicado = LancamentoFinanceiro(
            descricao="Lan?amento duplicado",
            valor=Decimal("500.00"),
            tipo="conta_receber",
            status="pendente",
            data_lancamento=date(2026, 9, 19),
            cliente_id=cliente.id,
            proposta_id=proposta.id,
            proposta_parcela_id=parcela.id,
            origem="PROPOSTA",
            ativo=True,
        )

        db.session.add(duplicado)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()
