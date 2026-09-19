# -*- coding: utf-8 -*-
"""D25F03-A5.2 - Caso real MSTI / PROP20260013."""

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
from app.ordem_servico.ordem_servico_model import (
    OrdemServico,
    OrdemServicoItem,
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


def _cenario_msti():
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
        saldo_inicial=Decimal("3011.46"),
        saldo_atual=Decimal("3011.46"),
        limite_credito=Decimal("0.00"),
        ativa=True,
        principal=True,
        ativo=True,
    )

    db.session.add_all(
        [cliente, conta]
    )
    db.session.flush()

    # Outro servico do mesmo cliente.
    # Ele NAO pertence a PROP20260013.
    os85 = OrdemServico(
        numero="OS20260085",
        cliente_id=cliente.id,
        titulo=(
            "Adequa??o e veda??o do "
            "escapamento do grupo gerador"
        ),
        descricao="Outro servi?o",
        status="concluida",
        prioridade="normal",
        tipo_os="comercial",
        valor_servico=Decimal("550.00"),
        valor_pecas=Decimal("0.00"),
        valor_desconto=Decimal("0.00"),
        valor_total=Decimal("550.00"),
        status_pagamento="pago",
        ativo=True,
    )

    db.session.add(os85)
    db.session.flush()

    # O model da OS recalcula valor_total pelos itens.
    # Portanto o cenario real precisa materializar o
    # servico de R$ 550,00, em vez de depender apenas
    # do valor_total informado no construtor.
    item_os85 = OrdemServicoItem(
        ordem_servico=os85,
        descricao=(
            "Adequa??o e veda??o do "
            "escapamento do grupo gerador"
        ),
        tipo_servico="fechado",
        quantidade=Decimal("1.00"),
        valor_unitario=Decimal("550.00"),
        valor_total=Decimal("550.00"),
        ativo=True,
    )

    db.session.add(item_os85)

    # Marca a OS como alterada e deixa o listener
    # recalcular o total pelos itens reais.
    os85.valor_servico = Decimal("550.00")

    db.session.flush()

    assert (
        os85.valor_total
        == Decimal("550.00")
    )

    lanc_os85 = LancamentoFinanceiro(
        descricao=(
            "OS OS20260085 - Adequa??o e veda??o "
            "do escapamento do grupo gerador"
        ),
        valor=Decimal("550.00"),
        tipo="conta_receber",
        status="recebido",
        data_lancamento=date(2026, 8, 31),
        data_vencimento=date(2026, 9, 2),
        data_pagamento=date(2026, 9, 10),
        cliente_id=cliente.id,
        ordem_servico_id=os85.id,
        conta_bancaria_id=conta.id,
        origem="ORDEM_SERVICO",
        ativo=True,
    )

    # O saldo de teste e apenas sentinela.
    # Nao queremos somar os 550 novamente ao criar
    # este historico artificial.
    setattr(
        lanc_os85,
        "_saldo_bancario_event_skip",
        True,
    )

    db.session.add(lanc_os85)

    proposta = Proposta(
        codigo="PROP20260013",
        cliente_id=cliente.id,
        titulo=(
            "Instala??o de Tanque Externo de "
            "Combust?vel e Sensor de N?vel"
        ),
        status="pendente",
        data_emissao=date(2026, 9, 17),
        valor_total=Decimal("2300.00"),
        entrada=Decimal("50.00"),
        forma_pagamento="prazo",
        ativo=True,
    )

    db.session.add(proposta)
    db.session.flush()

    entrada = ParcelaProposta(
        proposta_id=proposta.id,
        numero_parcela=0,
        valor_parcela=Decimal("1150.00"),
        data_vencimento=date(2026, 10, 2),
        descricao="Entrada (50.00%)",
        status="pendente",
        ativo=True,
    )

    saldo = ParcelaProposta(
        proposta_id=proposta.id,
        numero_parcela=1,
        valor_parcela=Decimal("1150.00"),
        data_vencimento=date(2026, 11, 1),
        descricao="Parcela 1/1",
        status="pendente",
        ativo=True,
    )

    db.session.add_all(
        [entrada, saldo]
    )
    db.session.commit()

    return {
        "conta_id": conta.id,
        "os85_id": os85.id,
        "lanc_os85_id": lanc_os85.id,
        "proposta_id": proposta.id,
        "entrada_id": entrada.id,
        "saldo_id": saldo.id,
    }


def test_aprovar_prop13_cria_duas_cobrancas_sem_tocar_os85():
    app = _app()

    with app.app_context():
        ids = _cenario_msti()

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

        assert proposta.status == "aprovada"
        assert proposta.data_aprovacao is not None

        novos = (
            LancamentoFinanceiro.query
            .filter_by(
                proposta_id=proposta.id,
                origem="PROPOSTA",
                ativo=True,
            )
            .all()
        )

        assert len(novos) == 2

        por_parcela = {
            item.proposta_parcela_id:
            item
            for item in novos
        }

        entrada = por_parcela[
            ids["entrada_id"]
        ]

        restante = por_parcela[
            ids["saldo_id"]
        ]

        assert entrada.valor == Decimal("1150.00")
        assert restante.valor == Decimal("1150.00")

        assert entrada.status == "pendente"
        assert restante.status == "pendente"

        assert entrada.conta_bancaria_id == conta.id
        assert restante.conta_bancaria_id == conta.id

        assert entrada.ordem_servico_id is None
        assert restante.ordem_servico_id is None

        os85 = db.session.get(
            OrdemServico,
            ids["os85_id"],
        )

        lanc_os85 = db.session.get(
            LancamentoFinanceiro,
            ids["lanc_os85_id"],
        )

        assert os85.proposta_id is None
        assert os85.valor_total == Decimal("550.00")

        assert lanc_os85.valor == Decimal("550.00")
        assert lanc_os85.status == "recebido"
        assert lanc_os85.proposta_id is None

        db.session.refresh(conta)

        # Criar recebiveis pendentes nao altera caixa.
        assert conta.saldo_atual == saldo_antes


def test_proposta_financeirizada_nao_pode_voltar_para_pendente():
    app = _app()

    with app.app_context():
        ids = _cenario_msti()

        proposta = db.session.get(
            Proposta,
            ids["proposta_id"],
        )

        proposta.aprovar()
        proposta_id = proposta.id

    client = app.test_client()

    response = client.put(
        f"/propostas/api/{proposta_id}/status",
        json={
            "status": "Pendente",
        },
    )

    assert response.status_code == 409

    payload = response.get_json()

    assert "financeiros" in payload["error"]

    with app.app_context():
        proposta = db.session.get(
            Proposta,
            proposta_id,
        )

        assert proposta.status == "aprovada"

        assert (
            LancamentoFinanceiro.query
            .filter_by(
                proposta_id=proposta.id,
                ativo=True,
            )
            .count()
            == 2
        )


def test_reaprovar_prop13_continua_idempotente():
    app = _app()

    with app.app_context():
        ids = _cenario_msti()

        proposta = db.session.get(
            Proposta,
            ids["proposta_id"],
        )

        proposta.aprovar()

        ids_primeira = {
            item.id
            for item in
            LancamentoFinanceiro.query
            .filter_by(
                proposta_id=proposta.id,
                ativo=True,
            )
            .all()
        }

        proposta.aprovar()

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
        } == ids_primeira
