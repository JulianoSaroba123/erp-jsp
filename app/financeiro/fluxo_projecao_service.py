"""Projeção financeira a partir do saldo cadastrado e títulos pendentes."""
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from sqlalchemy import func

from app.extensoes import db
from app.financeiro.financeiro_compat import status_eh_pendente, tipo_eh_receita, tipo_eh_despesa
from app.financeiro.financeiro_model import ContaBancaria, LancamentoFinanceiro, ExtratoBancario, ConciliacaoBancariaItem
from app.financeiro.indicadores_service import lancamento_ativo


def projetar_fluxo(inicio, fim, conta_id=None):
    contas = ContaBancaria.query.filter_by(ativo=True)
    if conta_id:
        contas = contas.filter_by(id=conta_id)
    saldo_inicial = sum((c.saldo_atual or Decimal('0') for c in contas.all()), Decimal('0'))
    query = LancamentoFinanceiro.query.filter(
        LancamentoFinanceiro.ativo.is_(True),
        LancamentoFinanceiro.data_vencimento.isnot(None),
        LancamentoFinanceiro.data_vencimento <= fim,
    )
    if conta_id:
        query = query.filter(LancamentoFinanceiro.conta_bancaria_id == conta_id)
    candidatos = query.order_by(LancamentoFinanceiro.data_vencimento, LancamentoFinanceiro.id).all()
    ids = [x.id for x in candidatos]
    conciliado = defaultdict(Decimal)
    if ids:
        for lid, valor in db.session.query(ConciliacaoBancariaItem.lancamento_id,
                func.sum(ConciliacaoBancariaItem.valor_conciliado)).filter(
                ConciliacaoBancariaItem.ativo.is_(True),
                ConciliacaoBancariaItem.lancamento_id.in_(ids)).group_by(
                ConciliacaoBancariaItem.lancamento_id).all():
            conciliado[lid] += Decimal(str(valor or 0))
        # Vínculo legado só conta quando o movimento não tem itens N:N ativos.
        itens = db.session.query(ConciliacaoBancariaItem.extrato_id).filter(
            ConciliacaoBancariaItem.ativo.is_(True)).subquery()
        for lid, valor in db.session.query(ExtratoBancario.lancamento_id,
                func.sum(func.abs(ExtratoBancario.valor))).filter(
                ExtratoBancario.ativo.is_(True), ExtratoBancario.conciliado.is_(True),
                ExtratoBancario.lancamento_id.in_(ids),
                ~ExtratoBancario.id.in_(select_ids(itens))).group_by(
                ExtratoBancario.lancamento_id).all():
            conciliado[lid] += Decimal(str(valor or 0))
    por_dia = defaultdict(list)
    atrasados = []
    for lanc in candidatos:
        if not lancamento_ativo(lanc) or not status_eh_pendente(lanc.status) or lanc.data_pagamento:
            continue
        if (lanc.categoria or '').casefold() == 'transferência bancária':
            continue
        if not (tipo_eh_receita(lanc.tipo) or tipo_eh_despesa(lanc.tipo)):
            continue
        restante = max(Decimal('0'), Decimal(str(lanc.valor or 0)) - conciliado[lanc.id])
        if not restante:
            continue
        linha = {'lancamento': lanc, 'valor_restante': restante}
        if lanc.data_vencimento < inicio:
            atrasados.append(linha)
        else:
            por_dia[lanc.data_vencimento].append(linha)
    saldo = saldo_inicial
    dias = []
    dia = inicio
    while dia <= fim:
        itens_dia = por_dia[dia]
        entradas = sum((x['valor_restante'] for x in itens_dia if tipo_eh_receita(x['lancamento'].tipo)), Decimal('0'))
        saidas = sum((x['valor_restante'] for x in itens_dia if tipo_eh_despesa(x['lancamento'].tipo)), Decimal('0'))
        saldo += entradas - saidas
        dias.append({'data': dia, 'receitas': entradas, 'despesas': saidas,
                     'saldo_dia': entradas - saidas, 'saldo_acumulado': saldo, 'lancamentos': itens_dia})
        dia += timedelta(days=1)
    return {'projecao': dias, 'saldo_inicial': saldo_inicial, 'saldo_final': saldo,
            'total_receitas': sum((x['receitas'] for x in dias), Decimal('0')),
            'total_despesas': sum((x['despesas'] for x in dias), Decimal('0')),
            'alertas': [x for x in dias if x['saldo_acumulado'] < 0], 'atrasados': atrasados}


def select_ids(subquery):
    from sqlalchemy import select
    return select(subquery.c.extrato_id)
