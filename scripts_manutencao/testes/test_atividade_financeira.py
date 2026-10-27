"""Testes isolados: nenhum dado de produção é acessado."""
from datetime import date
from decimal import Decimal
import pytest
from app.extensoes import db
from app.financeiro.financeiro_model import (ContaBancaria, LancamentoFinanceiro, HistoricoFinanceiro, ExtratoBancario, ConciliacaoBancariaItem)
from app.financeiro.inativacao_service import alterar_atividade, OperacaoFinanceiraInvalida
from app.financeiro.indicadores_service import resumir_financeiro_periodo
from scripts_manutencao.testes.test_pr46_os_recebimento import banco_pr46, caso_jumirim_ficticio


def _criar(ids, **campos):
    valores = dict(descricao='Aluguel duplicado fictício', tipo='conta_pagar',
                   status='pago', valor=Decimal('1938.29'), categoria='Aluguel',
                   conta_bancaria_id=ids['conta'], data_lancamento=date(2026,9,10),
                   data_pagamento=date(2026,9,10), origem='MANUAL', ativo=True)
    valores.update(campos)
    registro = LancamentoFinanceiro(**valores)
    db.session.add(registro)
    db.session.commit()
    return registro


def test_inativar_reativar_sem_movimentar_banco_e_com_auditoria(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        lanc = _criar(ids)
        valor_inicial = db.session.get(ContaBancaria, ids['conta']).saldo_atual
        total_antes = resumir_financeiro_periodo(date(2026,9,1), date(2026,9,30)).despesas_realizadas
        alterar_atividade(lanc.id, ativar=False, motivo='Duplicidade comprovada', usuario='9')
        db.session.commit()
        db.session.expire_all()
        assert db.session.get(ContaBancaria, ids['conta']).saldo_atual == valor_inicial
        assert resumir_financeiro_periodo(date(2026,9,1), date(2026,9,30)).despesas_realizadas == total_antes - Decimal('1938.29')
        assert ExtratoBancario.query.filter_by(id=ids['extrato']).one().valor == Decimal('15000.00')
        alterar_atividade(lanc.id, ativar=True, motivo='Correção revisada', usuario='9')
        db.session.commit()
        db.session.expire_all()
        assert db.session.get(ContaBancaria, ids['conta']).saldo_atual == valor_inicial
        assert resumir_financeiro_periodo(date(2026,9,1), date(2026,9,30)).despesas_realizadas == total_antes
        historico = HistoricoFinanceiro.query.filter_by(lancamento_id=lanc.id).order_by(HistoricoFinanceiro.id).all()
        assert [(x.acao,x.usuario,x.motivo) for x in historico] == [('inativacao','9','Duplicidade comprovada'),('reativacao','9','Correção revisada')]
        assert LancamentoFinanceiro.query.filter_by(id=lanc.id).count() == 1


def test_vinculos_e_conciliacao_bloqueiam(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        lanc = _criar(ids, ordem_servico_id=ids['os'])
        with pytest.raises(OperacaoFinanceiraInvalida, match='integrado'):
            alterar_atividade(lanc.id, ativar=False, motivo='teste', usuario='9')
        db.session.rollback()
        lanc = _criar(ids, descricao='Outro título', tipo='conta_receber', valor=Decimal('15000.00'))
        extrato = db.session.get(ExtratoBancario, ids['extrato'])
        extrato.lancamento_id = lanc.id
        extrato.conciliado = True
        db.session.commit()
        with pytest.raises(OperacaoFinanceiraInvalida, match='vínculo'):
            alterar_atividade(lanc.id, ativar=False, motivo='teste', usuario='9')
        db.session.rollback()
        assert extrato.lancamento_id == lanc.id and extrato.conciliado
        assert lanc.ativo


def test_validacao_reativacao_duplicada_e_motivo(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        lanc = _criar(ids)
        with pytest.raises(OperacaoFinanceiraInvalida, match='motivo'):
            alterar_atividade(lanc.id, ativar=False, motivo=' ', usuario='9')
        db.session.rollback()
        alterar_atividade(lanc.id, ativar=False, motivo='Duplicidade', usuario='9')
        db.session.commit()
        _criar(ids)
        with pytest.raises(OperacaoFinanceiraInvalida, match='duplicado'):
            alterar_atividade(lanc.id, ativar=True, motivo='teste', usuario='9')
        db.session.rollback()
        assert not lanc.ativo


def test_http_permissoes_csrf_filtro_e_rota_antiga(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        lid = _criar(ids).id
    client = app.test_client()
    path = f'/financeiro/lancamentos/{lid}/atividade'
    assert client.get(path).status_code == 302
    client.post('/auth/login', data={'identificador':'comum_pr46','senha':'SenhaPr46Teste!'})
    assert client.get(path).status_code == 403
    client.get('/auth/logout')
    client.post('/auth/login', data={'identificador':'admin_pr46','senha':'SenhaPr46Teste!'})
    assert client.get(path).status_code == 200
    assert client.post(path, data={'acao':'inativar','motivo':'teste'}).status_code == 400
    assert client.post(f'/financeiro/lancamentos/{lid}/excluir').status_code == 403
    with client.session_transaction() as sess:
        token = sess['_csrf_atividade_financeira']
    response = client.post(path, data={'csrf_atividade':token,'acao':'inativar','motivo':'Duplicado'})
    assert response.status_code == 302
    assert b'Aluguel duplicado' not in client.get('/financeiro/lancamentos?atividade=ativos').data
    assert b'Aluguel duplicado' in client.get('/financeiro/lancamentos?atividade=inativos').data
    assert b'Aluguel duplicado' in client.get('/financeiro/lancamentos?atividade=todos').data


def test_setembro_124_161_ficticios_preservam_conciliacao(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        duplicado = _criar(ids, id=124, recorrente=True, frequencia='mensal')
        correto = _criar(ids, id=161, descricao='Aluguel empresa fictício', valor=Decimal('1000.00'))
        extrato = db.session.get(ExtratoBancario, ids['extrato'])
        extrato.valor = Decimal('1000.00')
        extrato.tipo_movimento = 'debito'
        item = ConciliacaoBancariaItem(extrato_id=extrato.id, lancamento_id=correto.id,
                                       valor_conciliado=Decimal('1000.00'), ativo=True)
        db.session.add(item)
        db.session.commit()
        saldo = db.session.get(ContaBancaria, ids['conta']).saldo_atual
        antes = resumir_financeiro_periodo(date(2026,9,1), date(2026,9,30)).despesas_realizadas
        with pytest.raises(OperacaoFinanceiraInvalida, match='vínculo'):
            alterar_atividade(161, ativar=False, motivo='teste', usuario='9')
        db.session.rollback()
        alterar_atividade(124, ativar=False, motivo='Duplicidade comprovada', usuario='9')
        db.session.commit()
        db.session.expire_all()
        assert resumir_financeiro_periodo(date(2026,9,1), date(2026,9,30)).despesas_realizadas == antes - Decimal('1938.29')
        assert db.session.get(LancamentoFinanceiro, 161).ativo
        assert db.session.get(LancamentoFinanceiro, 124).recorrente is True
        assert db.session.get(LancamentoFinanceiro, 124).frequencia == 'mensal'
        assert db.session.get(ContaBancaria, ids['conta']).saldo_atual == saldo
        assert db.session.get(ExtratoBancario, ids['extrato']).valor == Decimal('1000.00')
        assert ConciliacaoBancariaItem.query.filter_by(lancamento_id=161, ativo=True).count() == 1
        assert LancamentoFinanceiro.query.filter(LancamentoFinanceiro.id.in_([124,161])).count() == 2


def test_titulo_inativo_nao_pode_ser_conciliado(caso_jumirim_ficticio):
    from app.financeiro.conciliacao_adapter import executar_conciliacao_bancaria
    from app.financeiro.conciliacao_service import ConciliacaoInvalida, SolicitacaoAlocacao
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        lanc = _criar(ids, tipo='conta_receber', valor=Decimal('15000.00'))
        alterar_atividade(lanc.id, ativar=False, motivo='Duplicidade', usuario='9')
        db.session.commit()
        with pytest.raises(ConciliacaoInvalida, match='inativo'):
            executar_conciliacao_bancaria(
                ids['extrato'], [SolicitacaoAlocacao(lancamento_id=lanc.id, valor=Decimal('15000.00'))],
                usuario='9')
        assert ConciliacaoBancariaItem.query.filter_by(lancamento_id=lanc.id).count() == 0
        assert not db.session.get(ExtratoBancario, ids['extrato']).conciliado
