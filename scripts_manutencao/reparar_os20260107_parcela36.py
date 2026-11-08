# -*- coding: utf-8 -*-
"""Reparo controlado da parcela #36 da OS20260107.

Por padrão apenas diagnostica. Nunca é acionado pela aplicação web.
Execução requer operador autorizado, backup e aprovação explícita do deploy.

  python scripts_manutencao/reparar_os20260107_parcela36.py
  python scripts_manutencao/reparar_os20260107_parcela36.py --apply --confirm OS20260107-36

Sem criar/editar extratos, lançamentos ou conciliações N:N.
"""
import argparse
import os
import sys
from decimal import Decimal
from datetime import date

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import (
    LancamentoFinanceiro, ExtratoBancario, ConciliacaoBancariaItem,
    HistoricoFinanceiro,
)
from app.ordem_servico.ordem_servico_model import OrdemServico, OrdemServicoParcela
from app.ordem_servico.sincronizacao_financeira import (
    sincronizar_parcela_os_recebida,
)

VALOR = Decimal("3550.00")
DATA = date(2026, 11, 5)


def preflight():
    os_ = db.session.query(OrdemServico).filter_by(
        id=672, numero="OS20260107", ativo=True,
    ).with_for_update().one()
    parcelas = db.session.query(OrdemServicoParcela).filter_by(
        ordem_servico_id=os_.id, ativo=True,
    ).order_by(OrdemServicoParcela.id).with_for_update().all()
    assert len(parcelas) == 2 and {p.id for p in parcelas} == {36, 37}
    p1, p2 = parcelas
    assert p1.id == 36 and p1.numero_parcela == 1
    assert p2.id == 37 and p2.numero_parcela == 2
    assert Decimal(str(p1.valor)) == Decimal(str(p2.valor)) == VALOR
    assert not p2.pago and p2.data_pagamento is None
    titulo = db.session.query(LancamentoFinanceiro).filter_by(
        id=336, ordem_servico_id=672, ordem_servico_parcela_id=36,
        tipo="conta_receber", status="recebido", ativo=True,
    ).with_for_update().one()
    assert Decimal(str(titulo.valor)) == VALOR
    assert titulo.data_pagamento == DATA
    extrato = db.session.query(ExtratoBancario).filter_by(
        id=223, ativo=True, conciliado=True, tipo_movimento="credito",
    ).with_for_update().one()
    assert extrato.data_movimento == DATA
    item = db.session.query(ConciliacaoBancariaItem).filter_by(
        extrato_id=223, lancamento_id=336, ativo=True,
    ).with_for_update().one()
    assert Decimal(str(item.valor_conciliado)) == VALOR
    todos = db.session.query(ConciliacaoBancariaItem).filter_by(
        lancamento_id=336, ativo=True,
    ).all()
    assert sum((Decimal(str(i.valor_conciliado)) for i in todos), Decimal("0.00")) == VALOR
    if p1.pago:
        assert p1.data_pagamento == DATA
    else:
        assert p1.data_pagamento is None
    return os_, p1, p2, titulo


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args()
    if args.apply and args.confirm != "OS20260107-36":
        parser.error("--apply requer --confirm OS20260107-36")
    app = create_app()
    with app.app_context():
        try:
            os_, p1, p2, titulo = preflight()
            print(f"OS {os_.numero} | parcela #36 paga={p1.pago} | "
                  f"financeiro #336 recebido | extrato #223 conciliado")
            if not args.apply:
                print("SIMULAÇÃO: sem alterações. Use --apply após autorização.")
                db.session.rollback()
                return
            if p1.pago:
                print("IDEMPOTENTE: parcela já regularizada. Nenhuma alteração.")
                db.session.rollback()
                return
            sincronizar_parcela_os_recebida(db.session, titulo)
            db.session.add(HistoricoFinanceiro(
                lancamento_id=336, campo_alterado="sincronizacao_os_parcela",
                valor_anterior="parcela_36_pendente",
                valor_novo="parcela_36_recebida_2026-11-05",
                usuario="reparo_controlado_os20260107",
                acao="sincronizacao",
                motivo=("Parcela #36 da OS20260107 sincronizada com título #336 "
                        "e conciliação N:N #223, sem novo crédito bancário."),
            ))
            db.session.flush()
            assert p1.pago and p1.data_pagamento == DATA
            assert not p2.pago and p2.data_pagamento is None
            assert os_.status_pagamento == "parcial"
            db.session.commit()
            print("SUCESSO: somente parcela #36 e status_pagamento da OS atualizados.")
        except Exception:
            db.session.rollback()
            raise


if __name__ == "__main__":
    main()
