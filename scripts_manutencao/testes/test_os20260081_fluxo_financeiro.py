# -*- coding: utf-8 -*-
"""
Teste de regressão baseado no caso real OS20260081.

Objetivo:
- conclusão da OS não significa recebimento automático;
- status financeiro deve seguir cada parcela;
- vencimento e data real de pagamento são fatos distintos;
- sincronização repetida não pode duplicar lançamentos;
- status_pagamento da OS deve refletir as parcelas.
"""

import os
import sys
from datetime import date, datetime
from decimal import Decimal

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    ),
)

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


def _criar_cenario_os20260081():
    app = create_app("testing")

    with app.app_context():
        db.create_all()

        cliente = Cliente(
            nome="A C PASQUOTTO & CIA LTDA",
            ativo=True,
        )
        db.session.add(cliente)
        db.session.flush()

        ordem = OrdemServico(
            numero="OS20260081",
            titulo="Montagem de Painel Elétrico de Comando",
            cliente_id=cliente.id,
            tipo_os="comercial",
            status="concluida",
            data_abertura=date(2026, 8, 11),
            data_inicio=datetime(2026, 8, 17, 12, 7),
            data_conclusao=datetime(2026, 8, 26, 12, 8),
            condicao_pagamento="parcelado",
            numero_parcelas=2,
            valor_entrada=Decimal("2800.00"),
            data_primeira_parcela=date(2026, 8, 11),
            status_pagamento="pendente",
            ativo=True,
        )
        db.session.add(ordem)
        db.session.flush()

        item = OrdemServicoItem(
            ordem_servico_id=ordem.id,
            descricao="Serviço fechado",
            tipo_servico="fechado",
            quantidade=Decimal("1.00"),
            valor_unitario=Decimal("5600.00"),
        )
        item.calcular_total()
        db.session.add(item)

        parcela_1 = OrdemServicoParcela(
            ordem_servico_id=ordem.id,
            numero_parcela=1,
            data_vencimento=date(2026, 8, 11),
            valor=Decimal("2800.00"),
            pago=True,
            data_pagamento=date(2026, 8, 11),
        )
        parcela_2 = OrdemServicoParcela(
            ordem_servico_id=ordem.id,
            numero_parcela=2,
            data_vencimento=date(2026, 8, 28),
            valor=Decimal("2800.00"),
            pago=False,
            data_pagamento=None,
        )
        db.session.add_all([parcela_1, parcela_2])
        db.session.commit()

        # Garante o total do cenário real após a criação dos itens.
        ordem.valor_total = Decimal("5600.00")
        db.session.commit()

        return app, ordem.id, parcela_1.id, parcela_2.id


def test_os20260081_conclusao_respeita_pagamento_de_cada_parcela():
    app, ordem_id, p1_id, p2_id = _criar_cenario_os20260081()

    with app.app_context():
        ordem = db.session.get(OrdemServico, ordem_id)

        resultado = gerar_lancamento_ordem_servico(
            ordem,
            forma_pagamento="pix",
        )

        assert len(resultado) == 2

        lancamentos = {
            lanc.ordem_servico_parcela_id: lanc
            for lanc in LancamentoFinanceiro.query.filter_by(
                ordem_servico_id=ordem.id
            ).all()
        }

        assert len(lancamentos) == 2

        entrada = lancamentos[p1_id]
        saldo = lancamentos[p2_id]

        assert entrada.valor == Decimal("2800.00")
        assert entrada.data_vencimento == date(2026, 8, 11)
        assert entrada.status == "recebido"
        assert entrada.data_pagamento == date(2026, 8, 11)

        assert saldo.valor == Decimal("2800.00")
        assert saldo.data_vencimento == date(2026, 8, 28)
        assert saldo.status == "pendente"
        assert saldo.data_pagamento is None

        db.session.refresh(ordem)
        assert ordem.status_pagamento == "parcial"


def test_os20260081_pagamento_do_saldo_em_04_09_e_idempotente():
    app, ordem_id, p1_id, p2_id = _criar_cenario_os20260081()

    with app.app_context():
        ordem = db.session.get(OrdemServico, ordem_id)
        gerar_lancamento_ordem_servico(ordem, forma_pagamento="pix")

        ids_antes = {
            lanc.ordem_servico_parcela_id: lanc.id
            for lanc in LancamentoFinanceiro.query.filter_by(
                ordem_servico_id=ordem.id
            ).all()
        }

        parcela_2 = db.session.get(OrdemServicoParcela, p2_id)
        parcela_2.pago = True
        parcela_2.data_pagamento = date(2026, 9, 4)
        db.session.commit()

        gerar_lancamento_ordem_servico(ordem, forma_pagamento="pix")

        registros = LancamentoFinanceiro.query.filter_by(
            ordem_servico_id=ordem.id
        ).all()

        assert len(registros) == 2

        lancamentos = {
            lanc.ordem_servico_parcela_id: lanc
            for lanc in registros
        }

        assert lancamentos[p1_id].id == ids_antes[p1_id]
        assert lancamentos[p2_id].id == ids_antes[p2_id]

        assert lancamentos[p1_id].status == "recebido"
        assert lancamentos[p1_id].data_pagamento == date(2026, 8, 11)

        assert lancamentos[p2_id].status == "recebido"
        assert lancamentos[p2_id].data_vencimento == date(2026, 8, 28)
        assert lancamentos[p2_id].data_pagamento == date(2026, 9, 4)

        db.session.refresh(ordem)
        assert ordem.status_pagamento == "pago"
