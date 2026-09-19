# -*- coding: utf-8 -*-
"""
ERP JSP - Adaptador da conciliacao bancaria N:N.

Integra o motor transacional puro de conciliacao com a infraestrutura
real do ERP, mantendo as dependencias ORM concentradas nesta camada.
"""

from decimal import Decimal

from app.extensoes import db
from app.financeiro.financeiro_model import (
    ExtratoBancario,
    LancamentoFinanceiro,
    ConciliacaoBancariaItem,
)
from app.financeiro.conciliacao_service import executar_conciliacao_orm


CENTAVO = Decimal("0.01")

_TIPOS_RECEBIVEIS = {
    "receita",
    "conta_receber",
}


def _dinheiro(valor):
    return Decimal(
        str(valor or 0)
    ).quantize(CENTAVO)


def _finalizar_baixas_proposta(
    *,
    session,
    extrato,
    lancamentos,
    preparacao,
    conciliado_por_lancamento,
    usuario=None,
):
    """Baixa recebiveis de proposta integralmente conciliados.

    Restrito a origem PROPOSTA.
    OS e demais origens preservam o comportamento do D25F01.
    """

    propostas_ids = set()

    for alocacao in preparacao.alocacoes:
        lancamento = lancamentos.get(
            alocacao.lancamento_id
        )

        if lancamento is None:
            continue

        origem = str(
            getattr(
                lancamento,
                "origem",
                "",
            )
            or ""
        ).strip().upper()

        tipo = str(
            getattr(
                lancamento,
                "tipo",
                "",
            )
            or ""
        ).strip().lower()

        if origem != "PROPOSTA":
            continue

        if tipo not in _TIPOS_RECEBIVEIS:
            continue

        if not getattr(
            lancamento,
            "proposta_id",
            None,
        ):
            continue

        if not getattr(
            lancamento,
            "proposta_parcela_id",
            None,
        ):
            continue

        total_antes = _dinheiro(
            conciliado_por_lancamento.get(
                lancamento.id,
                Decimal("0.00"),
            )
        )

        total_depois = (
            total_antes
            + _dinheiro(
                alocacao.valor
            )
        ).quantize(CENTAVO)

        total_lancamento = abs(
            _dinheiro(
                lancamento.valor
            )
        )

        # Pagamento parcial continua pendente.
        if total_depois != total_lancamento:
            continue

        lancamento.status = "recebido"

        # Data do movimento bancario passa a ser
        # a data canonica do recebimento.
        lancamento.data_pagamento = (
            extrato.data_movimento
        )

        if usuario:
            lancamento.usuario_editor = usuario

        propostas_ids.add(
            lancamento.proposta_id
        )

    if not propostas_ids:
        return

    # Imports tardios preservam testes isolados da conciliacao.
    from app.proposta.proposta_model import Proposta
    from app.financeiro.proposta_financeiro_service import (
        sincronizar_lancamentos_proposta,
    )

    for proposta_id in sorted(
        propostas_ids
    ):
        proposta = session.get(
            Proposta,
            proposta_id,
        )

        if proposta is not None:
            sincronizar_lancamentos_proposta(
                proposta
            )


def executar_conciliacao_bancaria(
    extrato_id,
    alocacoes,
    usuario=None,
    observacoes=None,
):
    """
    Executa a conciliacao bancaria usando os models e a sessao reais do ERP.

    Validacao e persistencia continuam centralizadas no motor N:N.
    O adaptador acrescenta apenas a sincronizacao transacional
    de recebiveis originados por PROPOSTA.
    """

    return executar_conciliacao_orm(
        session=db.session,
        extrato_model=ExtratoBancario,
        lancamento_model=LancamentoFinanceiro,
        item_model=ConciliacaoBancariaItem,
        extrato_id=extrato_id,
        alocacoes=alocacoes,
        usuario=usuario,
        observacoes=observacoes,
        finalizador_transacional=(
            _finalizar_baixas_proposta
        ),
    )
