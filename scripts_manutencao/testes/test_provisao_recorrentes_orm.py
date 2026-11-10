# -*- coding: utf-8 -*-
"""Testes de provisionamento mensal em banco descartável, sem Render."""
from datetime import date
from decimal import Decimal

from app.extensoes import db
from app.financeiro.financeiro_model import (
    CustoFixo, ContaBancaria, LancamentoFinanceiro, ExtratoBancario,
    ConciliacaoBancariaItem
)
from scripts_manutencao.testes.test_pr46_os_recebimento import (
    banco_pr46, caso_jumirim_ficticio
)


def criar_custo(ids, nome='Contabilidade', categoria='Contabilidade', valor='350.00'):
    custo = CustoFixo(
        nome=nome, descricao='Teste recorrência, sem dados reais',
        tipo='DESPESA', categoria=categoria, valor_mensal=Decimal(valor),
        dia_vencimento=10, gerar_automaticamente=True,
        data_inicio=date(2026, 1, 1), data_fim=None,
        conta_bancaria_id=ids['conta'], ativo=True
    )
    db.session.add(custo)
    db.session.commit()
    return custo


def test_provisao_competencia_pendente_idempotente_sem_credito_debito(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        custo = criar_custo(ids)
        banco_antes = db.session.get(ContaBancaria, ids['conta']).saldo_atual
        quant_extratos = ExtratoBancario.query.count()
        quant_vinculos = ConciliacaoBancariaItem.query.count()
        novo = custo.gerar_lancamento_mes(2026, 12)
        assert novo is not None
        assert novo.tipo == 'conta_pagar'
        assert novo.status == 'pendente'
        assert novo.data_vencimento == date(2026, 12, 10)
        assert novo.data_pagamento is None
        assert novo.valor == Decimal('350.00')
        assert novo.origem == 'CUSTO_FIXO'
        assert novo.custo_fixo_id == custo.id
        assert custo.gerar_lancamento_mes(2026, 12) is None
        assert LancamentoFinanceiro.query.filter_by(
            custo_fixo_id=custo.id, ativo=True
        ).count() == 1
        db.session.expire_all()
        assert db.session.get(ContaBancaria, ids['conta']).saldo_atual == banco_antes
        assert ExtratoBancario.query.count() == quant_extratos
        assert ConciliacaoBancariaItem.query.count() == quant_vinculos


def test_pagamento_manual_custo_fixo_nao_duplica_titulo(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        custo = criar_custo(ids, nome='Energia Elétrica',categoria='Energia', valor='400.00')
        manual = LancamentoFinanceiro(
            descricao='Pagamento CPFL conta de energia elétrica',
            tipo='conta_pagar', status='pendente', categoria='Despesas Fixas',
            valor=Decimal('415.34'), conta_bancaria_id=ids['conta'],
            data_lancamento=date(2026,12,1), data_vencimento=date(2026,12,19),
            origem='MANUAL', ativo=True
        )
        db.session.add(manual)
        db.session.commit()
        antes = LancamentoFinanceiro.query.count()
        assert custo.gerar_lancamento_mes(2026,12) is None
        assert LancamentoFinanceiro.query.count() == antes


def test_cadastros_sem_validacao_nao_viram_divida_real(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        custo = criar_custo(ids, nome='Dr. Adinho Imoveis',
                            categoria='Aluguel',valor='1930.50')
        antes = LancamentoFinanceiro.query.count()
        assert custo.gerar_lancamento_mes(2026, 12) is None
        assert LancamentoFinanceiro.query.count() == antes


def test_fluxo_caixa_sem_checkpoint_usa_fallback_sinalizado(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    client=app.test_client()
    login=client.post('/auth/login',data={
        'identificador':'admin_pr46','senha':'SenhaPr46Teste!'
    })
    assert login.status_code == 302
    resp=client.get(f'/financeiro/fluxo-caixa?conta_id={ids["conta"]}&periodo=30')
    assert resp.status_code == 200
    assert b'Fluxo de Caixa Projetado' in resp.data
    assert b'checkpoint banc' in resp.data.lower() or b'nÃ£o possui' in resp.data.lower()
