# -*- coding: utf-8 -*-
"""
Regressao do gatilho OS -> Financeiro.

Regras:
1. Criar uma OS aberta nao cria conta a receber pendente.
2. Antes da conclusao, somente pagamento antecipado explicitamente recebido
   pode gerar movimento financeiro.
3. Ao concluir a OS, o saldo ainda devido passa a existir como conta a receber.
4. Reconciliacao continua idempotente e preserva o recebimento antecipado.
"""

import os
import sys
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    ),
)

from flask import g

from app import create_app
from app.extensoes import db
from app.cliente.cliente_model import Cliente
from app.financeiro.financeiro_model import LancamentoFinanceiro
from app.financeiro.financeiro_utils import gerar_lancamento_ordem_servico
from app.ordem_servico.ordem_servico_model import (
    OrdemServico,
    OrdemServicoItem,
    OrdemServicoParcela,
)


def _app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
    return app


def _cliente(app, nome="Cliente Gatilho"):
    with app.app_context():
        cliente = Cliente(nome=nome, ativo=True)
        db.session.add(cliente)
        db.session.commit()
        return cliente.id


def _login_admin(app):
    client = app.test_client()
    admin = SimpleNamespace(
        id=1,
        tipo_usuario="admin",
        is_authenticated=True,
    )

    @app.before_request
    def load_test_admin():
        g._login_user = admin

    return client


def test_criar_os_aberta_nao_cria_conta_receber():
    app = _app()
    cliente_id = _cliente(app)
    client = _login_admin(app)

    response = client.post(
        "/ordem_servico/novo",
        data={
            "tipo_os": "comercial",
            "tipo_servico": "atendimento",
            "cliente_id": str(cliente_id),
            "titulo": "OS Gatilho Aberta",
            "descricao": "",
            "status": "aberta",
            "condicao_pagamento": "a_vista",
            "status_pagamento": "pendente",
            "numero_parcelas": "1",
            "valor_entrada": "0",
            "valor_desconto": "0",
            "prazo_garantia": "90",
            "forma_pagamento": "pix",
            "data_abertura": "2026-09-07",
            "data_vencimento_pagamento": "2026-09-14",
            "servico_descricao[]": "Servico gatilho",
            "servico_tipo[]": "fechado",
            "servico_quantidade[]": "1",
            "servico_valor[]": "1000",
        },
    )

    assert response.status_code in (302, 303)

    with app.app_context():
        ordem = OrdemServico.query.filter_by(
            titulo="OS Gatilho Aberta"
        ).one()

        assert ordem.status == "aberta"
        assert LancamentoFinanceiro.query.filter_by(
            ordem_servico_id=ordem.id
        ).count() == 0


def test_entrada_antecipada_e_saldo_na_conclusao():
    app = _app()
    cliente_id = _cliente(app, "Cliente Entrada")

    with app.app_context():
        ordem = OrdemServico(
            numero="OS-GATILHO-002",
            titulo="OS com entrada antecipada",
            cliente_id=cliente_id,
            tipo_os="comercial",
            status="em_andamento",
            condicao_pagamento="parcelado",
            numero_parcelas=2,
            valor_entrada=Decimal("2800.00"),
            status_pagamento="parcial",
            data_abertura=date(2026, 8, 11),
            ativo=True,
        )
        db.session.add(ordem)
        db.session.flush()

        item = OrdemServicoItem(
            ordem_servico_id=ordem.id,
            descricao="Servico fechado",
            tipo_servico="fechado",
            quantidade=Decimal("1.00"),
            valor_unitario=Decimal("5600.00"),
        )
        item.calcular_total()
        db.session.add(item)

        entrada = OrdemServicoParcela(
            ordem_servico_id=ordem.id,
            numero_parcela=1,
            data_vencimento=date(2026, 8, 11),
            valor=Decimal("2800.00"),
            pago=True,
            data_pagamento=date(2026, 8, 11),
        )
        saldo = OrdemServicoParcela(
            ordem_servico_id=ordem.id,
            numero_parcela=2,
            data_vencimento=date(2026, 8, 28),
            valor=Decimal("2800.00"),
            pago=False,
            data_pagamento=None,
        )
        db.session.add_all([entrada, saldo])
        db.session.commit()

        ordem.valor_total = Decimal("5600.00")
        db.session.commit()

        resultado_antes = gerar_lancamento_ordem_servico(
            ordem,
            forma_pagamento="pix",
        )

        assert len(resultado_antes) == 1

        antes = LancamentoFinanceiro.query.filter_by(
            ordem_servico_id=ordem.id
        ).all()

        assert len(antes) == 1
        assert antes[0].ordem_servico_parcela_id == entrada.id
        assert antes[0].status == "recebido"
        assert antes[0].data_pagamento == date(2026, 8, 11)

        ordem.status = "concluida"
        ordem.data_conclusao = date(2026, 8, 26)
        db.session.commit()

        resultado_depois = gerar_lancamento_ordem_servico(
            ordem,
            forma_pagamento="pix",
        )

        assert len(resultado_depois) == 2

        depois = {
            lanc.ordem_servico_parcela_id: lanc
            for lanc in LancamentoFinanceiro.query.filter_by(
                ordem_servico_id=ordem.id
            ).all()
        }

        assert len(depois) == 2

        assert depois[entrada.id].status == "recebido"
        assert depois[entrada.id].data_pagamento == date(2026, 8, 11)

        assert depois[saldo.id].status == "pendente"
        assert depois[saldo.id].data_vencimento == date(2026, 8, 28)
        assert depois[saldo.id].data_pagamento is None
