# -*- coding: utf-8 -*-
"""
ERP JSP - Adaptador da conciliacao bancaria N:N.

Integra o motor transacional puro de conciliacao com a infraestrutura
real do ERP, mantendo as dependencias ORM concentradas nesta camada.
"""

from app.extensoes import db
from app.financeiro.financeiro_model import (
    ExtratoBancario,
    LancamentoFinanceiro,
    ConciliacaoBancariaItem,
)
from app.financeiro.conciliacao_service import executar_conciliacao_orm


def executar_conciliacao_bancaria(
    extrato_id,
    alocacoes,
    usuario=None,
    observacoes=None,
):
    """
    Executa a conciliacao bancaria usando os models e a sessao reais do ERP.

    Esta funcao nao possui regra financeira propria. Toda validacao,
    distribuicao e persistencia permanecem em executar_conciliacao_orm().
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
    )