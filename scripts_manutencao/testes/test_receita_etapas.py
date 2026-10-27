"""Receita por etapa: somente dados fictícios em banco descartável."""
from datetime import date
from decimal import Decimal
import pytest
from app.extensoes import db
from app.ordem_servico.ordem_servico_model import OrdemServico, ReconhecimentoReceitaOS
from app.ordem_servico.receita_etapas import registrar_etapa
from app.financeiro.financeiro_model import ContaBancaria, ExtratoBancario, LancamentoFinanceiro
from app.financeiro.financeiro_routes import receita_etapas_periodo, calcular_dre
from scripts_manutencao.testes.test_pr46_os_recebimento import banco_pr46, caso_jumirim_ficticio, _registrar


def test_etapas_separam_competencia_de_caixa_e_sao_idempotentes(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        os = db.session.get(OrdemServico, ids['os'])
        _registrar(ids)
        db.session.commit()
        saldo = db.session.get(ContaBancaria, ids['conta']).saldo_atual
        assert receita_etapas_periodo(date(2026,9,1), date(2026,9,30)) == 0
        parametros = dict(os_id=os.id, competencia=date(2026,9,20), descricao='Montagem executada',
                          valor='4000.00', usuario='9', chave='etapa-ficticia-1')
        e = registrar_etapa(**parametros)
        db.session.commit()
        assert registrar_etapa(**parametros).id == e.id
        db.session.commit()
        with pytest.raises(ValueError, match='etapa igual'):
            registrar_etapa(**{**parametros, 'chave': 'outra-operacao'})
        db.session.rollback()
        registrar_etapa(os_id=os.id, competencia=date(2026,10,15), descricao='Testes executados',
                        valor='6000.00', usuario='9', chave='etapa-ficticia-2')
        db.session.commit()
        assert receita_etapas_periodo(date(2026,9,1), date(2026,9,30)) == Decimal('4000')
        assert receita_etapas_periodo(date(2026,10,1), date(2026,10,31)) == Decimal('6000')
        assert calcular_dre([], receita_etapas_periodo(date(2026,9,1),date(2026,9,30)))['receita_bruta'] == Decimal('4000')
        assert os.status == 'iniciada' and os.status_pagamento == 'parcial'
        assert db.session.get(ContaBancaria, ids['conta']).saldo_atual == saldo
        assert not db.session.get(ExtratoBancario, ids['extrato']).conciliado
        assert LancamentoFinanceiro.query.filter_by(ordem_servico_id=os.id, status='recebido').count() == 1
        with pytest.raises(ValueError, match='ultrapassa'):
            registrar_etapa(os_id=os.id, competencia=date(2026,9,21), descricao='Valor excessivo',
                            valor='20001', usuario='9', chave='etapa-ficticia-3')
        db.session.rollback()
        assert ReconhecimentoReceitaOS.query.filter_by(ordem_servico_id=os.id).count() == 2


def test_http_etapas_restricao_e_csrf(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    client = app.test_client()
    path = f'/ordem_servico/{ids["os"]}/receita-etapas'
    assert client.get(path).status_code == 302
    client.post('/auth/login', data={'identificador':'comum_pr46','senha':'SenhaPr46Teste!'})
    assert client.get(path).status_code == 403
    client.get('/auth/logout')
    client.post('/auth/login', data={'identificador':'admin_pr46','senha':'SenhaPr46Teste!'})
    assert client.get(path).status_code == 200
    assert client.post(path, data={'csrf':'inválido', 'descricao':'teste'}).status_code == 400
    with client.session_transaction() as sess:
        csrf = sess['_csrf_etapas_receita']
    resposta = client.post(path, data={'csrf':csrf,'competencia':'2026-09-20','descricao':'Montagem',
                                       'valor':'1000.00','chave':'teste-etapa-http'})
    assert resposta.status_code == 302
    with app.app_context():
        assert ReconhecimentoReceitaOS.query.filter_by(ordem_servico_id=ids['os']).count() == 1
