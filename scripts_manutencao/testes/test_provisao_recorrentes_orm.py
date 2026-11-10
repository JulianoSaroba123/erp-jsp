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
        custo = criar_custo(ids, nome='Prolabore',
                            categoria='Salários',valor='3000.00')
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
    assert 'checkpoint banc' in resp.data.decode('utf-8').lower() or 'não possui' in resp.data.decode('utf-8').lower()


def test_aluguel_manual_pago_em_novembro_bloqueia_provisao_da_competencia(
    caso_jumirim_ficticio
):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        custo = criar_custo(
            ids, nome='Dr. Adinho Imoveis', categoria='Aluguel', valor='1000.00'
        )
        antigo = LancamentoFinanceiro(
            descricao='Reembolso de aluguel empresarial, 50%, novembro/2026',
            valor=Decimal('1000.00'),
            tipo='conta_pagar', status='pago',
            categoria='Despesa Fixa', subcategoria='Aluguel',
            data_lancamento=date(2026, 11, 10),
            data_vencimento=date(2026, 11, 10),
            data_pagamento=date(2026, 11, 10),
            conta_bancaria_id=ids['conta'], origem='MANUAL', ativo=True
        )
        db.session.add(antigo)
        db.session.commit()
        id_antigo = antigo.id
        antes = LancamentoFinanceiro.query.count()
        assert custo.gerar_lancamento_mes(2026, 11) is None
        assert LancamentoFinanceiro.query.count() == antes
        assert db.session.get(LancamentoFinanceiro, id_antigo).status == 'pago'
        # A mensalidade futura será independente, ainda pendente.
        dezembro = custo.gerar_lancamento_mes(2026, 12)
        assert dezembro is not None
        assert dezembro.status == 'pendente'
        assert dezembro.data_pagamento is None
        assert dezembro.custo_fixo_id == custo.id



def test_http_provisionamento_exige_admin_csrf_e_e_idempotente(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        custo = criar_custo(ids, nome='Contabilidade', categoria='Contabilidade')
        assert custo.id is not None
    client = app.test_client()
    rota = '/financeiro/custos-fixos/gerar-lancamentos'
    # Não aceitar POST anônimo.
    assert client.post(rota).status_code == 302
    client.post('/auth/login', data={
        'identificador': 'admin_pr46', 'senha': 'SenhaPr46Teste!'
    })
    # Admin sem CSRF também deve ser rejeitado.
    assert client.post(rota).status_code == 400
    pagina = client.get('/financeiro/custos-fixos/dashboard')
    assert pagina.status_code == 200
    with client.session_transaction() as sess:
        token = sess['_csrf_gerar_custos_fixos_v1']
    assert client.post(rota, data={'csrf_gerar_custos_fixos': 'invalido'}).status_code == 400
    correto = client.post(rota, data={'csrf_gerar_custos_fixos': token})
    assert correto.status_code == 302
    repetido = client.post(rota, data={'csrf_gerar_custos_fixos': token})
    assert repetido.status_code == 302
    with app.app_context():
        itens = LancamentoFinanceiro.query.filter_by(origem='CUSTO_FIXO').all()
        assert len(itens) == 1
        assert itens[0].tipo == 'conta_pagar'
        assert itens[0].status == 'pendente'
        assert itens[0].data_pagamento is None
        assert itens[0].valor == Decimal('350.00')
        assert itens[0].conta_bancaria_id == ids['conta']
