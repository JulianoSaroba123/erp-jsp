# -*- coding: utf-8 -*-
"""Sincronização transacional do recebimento financeiro com a parcela da OS.

Não cria lançamentos, extratos nem movimentos de saldo. Chamador controla
commit/rollback. Vínculo é exclusivamente por FK, nunca por valor/descrição.
"""
from decimal import Decimal

from app.ordem_servico.ordem_servico_model import OrdemServico, OrdemServicoParcela
from app.financeiro.financeiro_utils import _sincronizar_status_pagamento_os


class SincronizacaoParcelaInvalida(ValueError):
    """Dados divergentes: nenhuma baixa deve ser assumida."""


def sincronizar_parcela_os_recebida(session, lancamento):
    """Marca a parcela vinculada como paga após um recebimento validado.

    Idempotente. Não baixa parcelas sem vínculo explícito, com valor
    diferente, inativas ou cujo pagamento possua data conflitante.
    """
    parcela_id = getattr(lancamento, "ordem_servico_parcela_id", None)
    os_id = getattr(lancamento, "ordem_servico_id", None)
    if not parcela_id or not os_id:
        return False
    if not getattr(lancamento, "ativo", False):
        raise SincronizacaoParcelaInvalida("Título de OS inativo.")
    if getattr(lancamento, "tipo", None) != "conta_receber":
        raise SincronizacaoParcelaInvalida("Tipo financeiro incompatível com recebimento de OS.")
    if getattr(lancamento, "status", None) != "recebido":
        return False
    data = getattr(lancamento, "data_pagamento", None)
    if data is None:
        raise SincronizacaoParcelaInvalida("Recebimento de OS sem data efetiva.")

    ordem = (session.query(OrdemServico)
             .filter_by(id=os_id, ativo=True).with_for_update().one_or_none())
    if ordem is None:
        raise SincronizacaoParcelaInvalida("OS inexistente ou inativa.")
    parcelas = (session.query(OrdemServicoParcela)
                .filter_by(ordem_servico_id=os_id, ativo=True)
                .order_by(OrdemServicoParcela.id)
                .with_for_update().all())
    parcela = next((p for p in parcelas if p.id == parcela_id), None)
    if parcela is None:
        raise SincronizacaoParcelaInvalida("Título não corresponde à parcela ativa da OS.")
    valor_titulo = Decimal(str(lancamento.valor)).quantize(Decimal("0.01"))
    valor_parcela = Decimal(str(parcela.valor)).quantize(Decimal("0.01"))
    if valor_titulo <= 0 or valor_titulo != valor_parcela:
        raise SincronizacaoParcelaInvalida("Valor do título difere do valor da parcela.")
    if parcela.data_pagamento is not None and parcela.data_pagamento != data:
        raise SincronizacaoParcelaInvalida("Parcela já possui outra data de pagamento.")
    if parcela.pago and parcela.data_pagamento is None:
        raise SincronizacaoParcelaInvalida("Parcela marcada paga sem data; exige auditoria.")

    alterado = not parcela.pago
    parcela.pago = True
    parcela.data_pagamento = data
    _sincronizar_status_pagamento_os(ordem, parcelas)
    return alterado
