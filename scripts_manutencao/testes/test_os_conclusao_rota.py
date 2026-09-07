# -*- coding: utf-8 -*-
"""
Regressão da conclusão da OS pela rota /<id>/concluir.

Objetivo:
- concluir a OS pelo fluxo real da interface;
- padronizar o status final como "concluida";
- gerar conta a receber pendente para parcela ainda não paga;
- não fabricar data de pagamento.
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
from app.ordem_servico.ordem_servico_model import (
    OrdemServico,
    OrdemServicoItem,
    OrdemServicoParcela,
)


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


def test_concluir_os_pela_rota_gera_conta_receber_pendente():
    app = create_app("testing")

    with app.app_context():
        db.create_all()

        cliente = Cliente(
            nome="Cliente Conclusao",
            ativo=True,
        )
        db.session.add(cliente)
        db.session.flush()

        ordem = OrdemServico(
            numero="OS-CONCLUSAO-001",
            titulo="Teste conclusão pela rota",
            cliente_id=cliente.id,
            tipo_os="comercial",
            status="em_execucao",
            condicao_pagamento="parcelado",
            numero_parcelas=1,
            status_pagamento="pendente",
            data_abertura=date(2026, 9, 7),
            ativo=True,
        )
        db.session.add(ordem)
        db.session.flush()

        item = OrdemServicoItem(
            ordem_servico_id=ordem.id,
            descricao="Serviço fechado",
            tipo_servico="fechado",
            quantidade=Decimal("1.00"),
            valor_unitario=Decimal("1000.00"),
        )
        item.calcular_total()
        db.session.add(item)

        parcela = OrdemServicoParcela(
            ordem_servico_id=ordem.id,
            numero_parcela=1,
            data_vencimento=date(2026, 9, 14),
            valor=Decimal("1000.00"),
            pago=False,
            data_pagamento=None,
        )
        db.session.add(parcela)
        db.session.commit()

        ordem.valor_total = Decimal("1000.00")
        db.session.commit()

        ordem_id = ordem.id
        parcela_id = parcela.id

    client = _login_admin(app)
    response = client.post(f"/ordem_servico/{ordem_id}/concluir")

    assert response.status_code in (302, 303)

    with app.app_context():
        ordem = db.session.get(OrdemServico, ordem_id)

        assert ordem.status == "concluida"
        assert ordem.data_conclusao is not None

        lancamentos = LancamentoFinanceiro.query.filter_by(
            ordem_servico_id=ordem.id
        ).all()

        assert len(lancamentos) == 1

        lancamento = lancamentos[0]
        assert lancamento.ordem_servico_parcela_id == parcela_id
        assert lancamento.tipo == "conta_receber"
        assert lancamento.status == "pendente"
        assert lancamento.data_vencimento == date(2026, 9, 14)
        assert lancamento.data_pagamento is None
