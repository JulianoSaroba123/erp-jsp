# -*- coding: utf-8 -*-
"""D25F03-A6.3 - Conciliacao baixa recebivel de proposta."""

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
    ExtratoBancario,
    LancamentoFinanceiro,
)
from app.financeiro.conciliacao_adapter import (
    executar_conciliacao_bancaria,
)
from app.financeiro.conciliacao_service import (
    SolicitacaoAlocacao,
)
from app.proposta.proposta_model import (
    Proposta,
    ParcelaProposta,
)


SALDO_BASE = Decimal("2877.74")
VALOR = Decimal("1150.00")


def _app():
    app = create_app("testing")

    with app.app_context():
        db.drop_all()
        db.create_all()

    return app


def _cenario():
    cliente = Cliente(
        nome="COMPUSERVICE",
        razao_social="MSTI INFORMATICA LTDA",
        nome_fantasia="COMPUSERVICE",
        cpf_cnpj="72.019.805/0001-98",
        ativo=True,
    )

    conta = ContaBancaria(
        nome="Cora",
        tipo="conta_corrente",
        saldo_inicial=SALDO_BASE,
        saldo_atual=SALDO_BASE,
        limite_credito=Decimal("0.00"),
        ativa=True,
        principal=True,
        ativo=True,
    )

    db.session.add_all(
        [cliente, conta]
    )
    db.session.flush()

    proposta = Proposta(
        codigo="PROP20260013",
        cliente_id=cliente.id,
        titulo="Instalacao de Tanque Externo",
        status="pendente",
        data_emissao=date(2026, 9, 17),
        valor_total=VALOR,
        entrada=Decimal("100.00"),
        forma_pagamento="prazo",
        ativo=True,
    )

    db.session.add(proposta)
    db.session.flush()

    parcela = ParcelaProposta(
        proposta_id=proposta.id,
        numero_parcela=0,
        valor_parcela=VALOR,
        data_vencimento=date(2026, 10, 2),
        descricao="Entrada",
        status="pendente",
        ativo=True,
    )

    db.session.add(parcela)
    db.session.commit()

    proposta.aprovar()

    lancamento = (
        LancamentoFinanceiro.query
        .filter_by(
            proposta_id=proposta.id,
            proposta_parcela_id=parcela.id,
            ativo=True,
        )
        .one()
    )

    db.session.refresh(conta)

    assert lancamento.status == "pendente"
    assert conta.saldo_atual == SALDO_BASE

    return {
        "conta_id": conta.id,
        "proposta_id": proposta.id,
        "parcela_id": parcela.id,
        "lancamento_id": lancamento.id,
    }


def _extrato(conta_id, valor=VALOR):
    extrato = ExtratoBancario(
        conta_bancaria_id=conta_id,
        data_movimento=date(2026, 9, 17),
        descricao="Transf Pix recebida",
        documento="MSTI INFORMATICA LTDA EPP",
        valor=valor,
        tipo_movimento="credito",
        conciliado=False,
        ativo=True,
    )

    db.session.add(extrato)
    db.session.commit()

    return extrato.id


def test_integral_quita_e_movimenta_uma_vez():
    app = _app()

    with app.app_context():
        ids = _cenario()
        extrato_id = _extrato(ids["conta_id"])

        executar_conciliacao_bancaria(
            extrato_id=extrato_id,
            alocacoes=[
                SolicitacaoAlocacao(
                    lancamento_id=ids["lancamento_id"],
                    valor=VALOR,
                ),
            ],
            usuario="A6.3",
        )

        db.session.expire_all()

        conta = db.session.get(
            ContaBancaria,
            ids["conta_id"],
        )
        lanc = db.session.get(
            LancamentoFinanceiro,
            ids["lancamento_id"],
        )
        parcela = db.session.get(
            ParcelaProposta,
            ids["parcela_id"],
        )

        assert lanc.status == "recebido"
        assert lanc.data_pagamento == date(2026, 9, 17)

        assert parcela.status == "recebido"
        assert parcela.data_pagamento == date(2026, 9, 17)

        assert conta.saldo_atual == Decimal("4027.74")


def test_baixa_manual_antes_nao_duplica_caixa():
    app = _app()

    with app.app_context():
        ids = _cenario()

        lanc = db.session.get(
            LancamentoFinanceiro,
            ids["lancamento_id"],
        )

        lanc.status = "recebido"
        lanc.data_pagamento = date(2026, 9, 19)

        db.session.commit()
        db.session.expire_all()

        conta = db.session.get(
            ContaBancaria,
            ids["conta_id"],
        )

        saldo_antes = conta.saldo_atual

        assert saldo_antes == Decimal("4027.74")

        extrato_id = _extrato(ids["conta_id"])

        executar_conciliacao_bancaria(
            extrato_id=extrato_id,
            alocacoes=[
                SolicitacaoAlocacao(
                    lancamento_id=ids["lancamento_id"],
                    valor=VALOR,
                ),
            ],
            usuario="A6.3",
        )

        db.session.expire_all()

        conta = db.session.get(
            ContaBancaria,
            ids["conta_id"],
        )
        lanc = db.session.get(
            LancamentoFinanceiro,
            ids["lancamento_id"],
        )
        parcela = db.session.get(
            ParcelaProposta,
            ids["parcela_id"],
        )

        assert conta.saldo_atual == saldo_antes

        assert lanc.status == "recebido"
        assert lanc.data_pagamento == date(2026, 9, 17)

        assert parcela.status == "recebido"
        assert parcela.data_pagamento == date(2026, 9, 17)


def test_reaprovar_repara_parcela_sem_remexer_caixa():
    app = _app()

    with app.app_context():
        ids = _cenario()

        lanc = db.session.get(
            LancamentoFinanceiro,
            ids["lancamento_id"],
        )

        lanc.status = "recebido"
        lanc.data_pagamento = date(2026, 9, 17)

        db.session.commit()
        db.session.expire_all()

        conta = db.session.get(
            ContaBancaria,
            ids["conta_id"],
        )

        saldo_antes = conta.saldo_atual

        proposta = db.session.get(
            Proposta,
            ids["proposta_id"],
        )

        proposta.aprovar()

        db.session.expire_all()

        conta = db.session.get(
            ContaBancaria,
            ids["conta_id"],
        )
        parcela = db.session.get(
            ParcelaProposta,
            ids["parcela_id"],
        )

        assert parcela.status == "recebido"
        assert parcela.data_pagamento == date(2026, 9, 17)
        assert conta.saldo_atual == saldo_antes


def test_parcial_nao_quita():
    app = _app()

    with app.app_context():
        ids = _cenario()

        extrato_id = _extrato(
            ids["conta_id"],
            Decimal("500.00"),
        )

        executar_conciliacao_bancaria(
            extrato_id=extrato_id,
            alocacoes=[
                SolicitacaoAlocacao(
                    lancamento_id=ids["lancamento_id"],
                    valor=Decimal("500.00"),
                ),
            ],
            usuario="A6.3",
        )

        db.session.expire_all()

        conta = db.session.get(
            ContaBancaria,
            ids["conta_id"],
        )
        lanc = db.session.get(
            LancamentoFinanceiro,
            ids["lancamento_id"],
        )
        parcela = db.session.get(
            ParcelaProposta,
            ids["parcela_id"],
        )

        assert lanc.status == "pendente"
        assert lanc.data_pagamento is None

        assert parcela.status == "pendente"
        assert parcela.data_pagamento is None

        assert conta.saldo_atual == SALDO_BASE
