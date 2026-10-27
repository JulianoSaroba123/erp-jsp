"""Inativação auditável de títulos manuais sem efeitos bancários."""
from datetime import datetime
from sqlalchemy import inspect, select, Table, MetaData

from app.extensoes import db
from app.financeiro.financeiro_model import LancamentoFinanceiro, HistoricoFinanceiro


class OperacaoFinanceiraInvalida(ValueError):
    pass


def _vinculos_externos(lancamento_id):
    """Verifica todas as FKs reais do banco; histórico é preservado, não bloqueia.

    Inclusive vínculos históricos inativos são bloqueados conservadoramente.
    Falhas de introspecção propagam e revertem a transação.
    """
    conexao = db.session.connection()
    inspetor = inspect(conexao)
    for nome in inspetor.get_table_names():
        if nome in {'historico_financeiro', 'lancamentos_financeiros', 'alembic_version'}:
            continue
        for fk in inspetor.get_foreign_keys(nome):
            if fk.get('referred_table') != 'lancamentos_financeiros':
                continue
            if fk.get('referred_columns') != ['id'] or len(fk.get('constrained_columns', [])) != 1:
                raise OperacaoFinanceiraInvalida('Vínculo financeiro complexo exige revisão manual.')
            tabela = Table(nome, MetaData(), autoload_with=conexao)
            coluna = tabela.c[fk['constrained_columns'][0]]
            if conexao.execute(select(coluna).where(coluna == lancamento_id).limit(1)).first():
                raise OperacaoFinanceiraInvalida(
                    'Lançamento possui vínculo financeiro ou conciliação; revisão manual necessária.'
                )


def alterar_atividade(lancamento_id, *, ativar, motivo, usuario):
    motivo = (motivo or '').strip()
    if not motivo or len(motivo) > 1000:
        raise OperacaoFinanceiraInvalida('Informe um motivo de até 1000 caracteres.')
    lanc = (db.session.query(LancamentoFinanceiro).filter_by(id=lancamento_id)
            .populate_existing().with_for_update().one_or_none())
    if lanc is None:
        raise OperacaoFinanceiraInvalida('Lançamento não encontrado.')
    if bool(lanc.ativo) == ativar:
        raise OperacaoFinanceiraInvalida('Lançamento já está no estado solicitado.')
    if any(getattr(lanc, campo, None) for campo in (
        'ordem_servico_id', 'ordem_servico_parcela_id', 'proposta_id',
        'proposta_parcela_id', 'pedido_id', 'custo_fixo_id',
    )) or (lanc.origem or 'MANUAL').strip().upper() != 'MANUAL':
        raise OperacaoFinanceiraInvalida('Lançamento integrado exige revisão manual.')
    if lanc.categoria == 'Transferência Bancária' or lanc.recorrente:
        raise OperacaoFinanceiraInvalida('Transferências e recorrências exigem revisão manual.')
    _vinculos_externos(lanc.id)
    if ativar:
        duplicado = LancamentoFinanceiro.query.filter(
            LancamentoFinanceiro.id != lanc.id,
            LancamentoFinanceiro.ativo.is_(True),
            LancamentoFinanceiro.descricao == lanc.descricao,
            LancamentoFinanceiro.valor == lanc.valor,
            LancamentoFinanceiro.tipo == lanc.tipo,
            LancamentoFinanceiro.data_lancamento == lanc.data_lancamento,
            LancamentoFinanceiro.data_pagamento == lanc.data_pagamento,
            LancamentoFinanceiro.conta_bancaria_id == lanc.conta_bancaria_id,
        ).first()
        if duplicado:
            raise OperacaoFinanceiraInvalida('Possível lançamento duplicado ativo. Revise antes de reativar.')
    lanc.ativo = ativar
    lanc.data_exclusao = None if ativar else datetime.utcnow()
    lanc.usuario_editor = str(usuario)
    db.session.add(HistoricoFinanceiro(
        lancamento_id=lanc.id, campo_alterado='ativo',
        valor_anterior='inativo' if ativar else 'ativo',
        valor_novo='ativo' if ativar else 'inativo',
        usuario=str(usuario), acao='reativacao' if ativar else 'inativacao', motivo=motivo,
    ))
    # Bypass apenas durante este flush: não alterar saldo por operação contábil.
    lanc._saldo_bancario_event_skip = True
    try:
        db.session.flush()
    finally:
        lanc._saldo_bancario_event_skip = False
    return lanc
