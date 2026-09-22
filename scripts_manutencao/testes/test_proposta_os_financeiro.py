# -*- coding: utf-8 -*-
"""D25F03-A4 - Proposta -> OS sem duplicidade financeira."""

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
from app.financeiro.financeiro_utils import (
    gerar_lancamento_ordem_servico,
)
from app.financeiro.proposta_financeiro_service import (
    sincronizar_lancamentos_proposta,
)
from app.ordem_servico.ordem_servico_model import (
    OrdemServico,
)
from app.proposta.proposta_model import (
    Proposta,
    PropostaServico,
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
        codigo="PROP-D25F03-A4",
        cliente_id=cliente.id,
        titulo="Instalacao de Tanque Externo e Sensor de Nivel",
        status="pendente",
        data_emissao=date(2026, 9, 17),
        valor_total=Decimal("2300.00"),
        valor_servicos=Decimal("2300.00"),
        entrada=Decimal("50.00"),
        forma_pagamento="parcelado",
        numero_parcelas=1,
        intervalo_parcelas=28,
        ativo=True,
    )

    db.session.add(proposta)
    db.session.flush()

    servico = PropostaServico(
        proposta_id=proposta.id,
        descricao="Instalacao de tanque externo e sensor",
        tipo_servico="fechado",
        quantidade=Decimal("1.00"),
        valor_unitario=Decimal("2300.00"),
        valor_total=Decimal("2300.00"),
        ativo=True,
    )

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
        [servico, entrada, saldo]
    )
    db.session.commit()

    proposta.aprovar()

    entrada = db.session.get(
        ParcelaProposta,
        entrada.id,
    )

    entrada.status = "pago"
    entrada.data_pagamento = date(
        2026,
        9,
        17,
    )

    sincronizar_lancamentos_proposta(
        proposta
    )

    db.session.commit()

    return {
        "conta_id": conta.id,
        "proposta_id": proposta.id,
        "entrada_id": entrada.id,
        "saldo_id": saldo.id,
    }


def test_conversao_preserva_financeiro_sem_duplicar():
    app = _app()

    with app.app_context():
        ids = _cenario()

        proposta = db.session.get(
            Proposta,
            ids["proposta_id"],
        )

        antes = (
            LancamentoFinanceiro.query
            .filter_by(
                proposta_id=proposta.id,
                ativo=True,
            )
            .all()
        )

        assert len(antes) == 2

        ids_antes = {
            item.id
            for item in antes
        }

        assert sum(
            item.valor
            for item in antes
        ) == Decimal("2300.00")

        ordem = proposta.gerar_ordem_servico()

        assert ordem is not None
        assert ordem.proposta_id == proposta.id
        assert ordem.valor_total == Decimal("2300.00")
        assert ordem.valor_entrada == Decimal("1150.00")
        assert ordem.status_pagamento == "parcial"

        parcelas = sorted(
            list(ordem.parcelas),
            key=lambda item: item.numero_parcela,
        )

        assert len(parcelas) == 2

        entrada_os = parcelas[0]
        saldo_os = parcelas[1]

        assert entrada_os.numero_parcela == 0
        assert entrada_os.valor == Decimal("1150.00")
        assert entrada_os.pago is True
        assert entrada_os.data_pagamento == date(2026, 9, 17)

        assert saldo_os.numero_parcela == 1
        assert saldo_os.valor == Decimal("1150.00")
        assert saldo_os.pago is False

        depois = (
            LancamentoFinanceiro.query
            .filter_by(
                proposta_id=proposta.id,
                ativo=True,
            )
            .all()
        )

        assert len(depois) == 2

        assert {
            item.id
            for item in depois
        } == ids_antes

        por_parcela = {
            item.proposta_parcela_id:
            item
            for item in depois
        }

        lanc_entrada = por_parcela[
            ids["entrada_id"]
        ]

        lanc_saldo = por_parcela[
            ids["saldo_id"]
        ]

        assert lanc_entrada.ordem_servico_id == ordem.id
        assert lanc_saldo.ordem_servico_id == ordem.id

        assert (
            lanc_entrada.ordem_servico_parcela_id
            == entrada_os.id
        )

        assert (
            lanc_saldo.ordem_servico_parcela_id
            == saldo_os.id
        )

        assert lanc_entrada.origem == "PROPOSTA"
        assert lanc_entrada.status == "recebido"

        mesma_os = proposta.gerar_ordem_servico()

        assert mesma_os.id == ordem.id

        assert (
            OrdemServico.query
            .filter_by(
                proposta_id=proposta.id,
                ativo=True,
            )
            .count()
            == 1
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


def test_conclusao_os_reaproveita_recebiveis_da_proposta():
    app = _app()

    with app.app_context():
        ids = _cenario()

        proposta = db.session.get(
            Proposta,
            ids["proposta_id"],
        )

        ordem = proposta.gerar_ordem_servico()

        ids_antes = {
            item.id
            for item
            in LancamentoFinanceiro.query
            .filter_by(
                proposta_id=proposta.id,
                ativo=True,
            )
            .all()
        }

        ordem.status = "concluida"
        ordem.data_conclusao = datetime(
            2026,
            9,
            19,
            12,
            0,
        )

        db.session.commit()

        resultado = gerar_lancamento_ordem_servico(
            ordem,
            forma_pagamento="pix",
        )

        assert len(resultado) == 2

        depois = (
            LancamentoFinanceiro.query
            .filter_by(
                proposta_id=proposta.id,
                ativo=True,
            )
            .all()
        )

        assert len(depois) == 2

        assert {
            item.id
            for item in depois
        } == ids_antes

        assert sum(
            item.valor
            for item in depois
        ) == Decimal("2300.00")

        por_numero = {
            item.numero_parcela:
            item
            for item in depois
        }

        entrada = por_numero["Entrada"]
        saldo = por_numero["1/1"]

        assert entrada.status == "recebido"
        assert entrada.origem == "PROPOSTA"

        assert saldo.status == "pendente"
        assert saldo.origem == "ORDEM_SERVICO"

        assert entrada.proposta_id == proposta.id
        assert saldo.proposta_id == proposta.id

        assert ordem.status_pagamento == "parcial"
