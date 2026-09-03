# -*- coding: utf-8 -*-
"""
Teste de Regressão: paridade financeira Dashboard Geral x Dashboard Financeiro
================================================================================

Garante que o resumo financeiro do Dashboard Geral (calcular_metricas_dashboard)
usa a MESMA fonte central de indicadores do Dashboard Financeiro
(indicadores_service.resumir_financeiro_periodo), evitando divergências como
a observada: Dashboard Geral zerado enquanto o Dashboard Financeiro mostrava
valores reais de Setembro/2026.

Cenários:
1. Com lançamentos reais no mês corrente, Dashboard Geral (stats) e Dashboard
   Financeiro (resumir_financeiro_periodo) retornam os mesmos valores de
   receitas, despesas, resultado e pendências.
2. A rota /dashboard (Geral) renderiza 200 e exibe os mesmos valores
   formatados que aparecem no /financeiro/ (Financeiro) para o mês corrente.
3. calcular_metricas_dashboard() não lança mais NameError (bug que zerava
   tudo silenciosamente) e não duplica cálculo financeiro via SQL bruto.
"""

import os
import sys
from datetime import date
from decimal import Decimal

os.environ['FLASK_CONFIG'] = 'testing'
os.environ['FLASK_ENV'] = 'testing'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import create_app
from app.extensoes import db
from app.auth.usuario_model import Usuario
from app.financeiro.financeiro_model import LancamentoFinanceiro, ContaBancaria
from app.financeiro.financeiro_utils import calcular_metricas_dashboard
from app.financeiro.indicadores_service import periodo_mes_atual, resumir_financeiro_periodo


def _criar_admin():
    admin = Usuario.query.filter_by(usuario='admin_paridade_test').first()
    if admin:
        return admin
    admin = Usuario(
        nome='Admin Paridade Test',
        email='admin_paridade_test@example.com',
        usuario='admin_paridade_test',
        tipo_usuario='admin',
        ativo=True,
        email_confirmado=True,
        primeiro_login=False,
    )
    admin.set_senha('SenhaForte123!')
    db.session.add(admin)
    db.session.commit()
    return admin


def executar_testes():
    print("=" * 70)
    print("TESTE: paridade financeira Dashboard Geral x Dashboard Financeiro")
    print("=" * 70)

    app = create_app('testing')
    client = app.test_client()

    with app.app_context():
        assert db.engine.url.drivername == 'sqlite'
        assert db.engine.url.database == ':memory:'

        db.create_all()
        _criar_admin()

        LancamentoFinanceiro.query.filter(
            LancamentoFinanceiro.descricao.like('TEST_PARIDADE_%')
        ).delete()
        db.session.commit()

        conta = ContaBancaria.query.filter_by(nome='Conta Teste Paridade').first()
        if not conta:
            conta = ContaBancaria(
                nome='Conta Teste Paridade',
                tipo='conta_corrente',
                banco='001',
                agencia='1234',
                numero_conta='99999-0',
                saldo_inicial=Decimal('0.00'),
                saldo_atual=Decimal('0.00'),
                ativa=True,
                ativo=True,
            )
            db.session.add(conta)
            db.session.commit()

        hoje = date.today()

        # Receita realizada no mês corrente
        receita = LancamentoFinanceiro(
            descricao='TEST_PARIDADE_Receita',
            valor=Decimal('540.00'),
            tipo='receita',
            status='recebido',
            categoria='Serviços',
            data_lancamento=hoje,
            data_vencimento=hoje,
            data_pagamento=hoje,
            conta_bancaria_id=conta.id,
            ativo=True,
        )
        # Despesa realizada no mês corrente
        despesa = LancamentoFinanceiro(
            descricao='TEST_PARIDADE_Despesa',
            valor=Decimal('547.18'),
            tipo='despesa',
            status='pago',
            categoria='Operacional',
            data_lancamento=hoje,
            data_vencimento=hoje,
            data_pagamento=hoje,
            conta_bancaria_id=conta.id,
            ativo=True,
        )
        # Pendências no mês corrente
        a_receber = LancamentoFinanceiro(
            descricao='TEST_PARIDADE_AReceber',
            valor=Decimal('990.00'),
            tipo='conta_receber',
            status='pendente',
            categoria='Serviços',
            data_lancamento=hoje,
            data_vencimento=hoje,
            conta_bancaria_id=conta.id,
            ativo=True,
        )
        a_pagar = LancamentoFinanceiro(
            descricao='TEST_PARIDADE_APagar',
            valor=Decimal('3363.90'),
            tipo='conta_pagar',
            status='pendente',
            categoria='Materiais',
            data_lancamento=hoje,
            data_vencimento=hoje,
            conta_bancaria_id=conta.id,
            ativo=True,
        )
        db.session.add_all([receita, despesa, a_receber, a_pagar])
        db.session.commit()

        print("\n[TESTE 1] calcular_metricas_dashboard() não lança NameError e usa o serviço central...")
        stats = calcular_metricas_dashboard()
        assert stats['total_receitas_mes'] == 540.00, f"Receitas divergentes: {stats['total_receitas_mes']}"
        assert stats['total_despesas_mes'] == 547.18, f"Despesas divergentes: {stats['total_despesas_mes']}"
        assert round(stats['saldo_mes'], 2) == round(540.00 - 547.18, 2), f"Saldo divergente: {stats['saldo_mes']}"
        assert stats['total_contas_receber'] == 990.00, f"Contas a receber divergentes: {stats['total_contas_receber']}"
        assert stats['total_contas_pagar'] == 3363.90, f"Contas a pagar divergentes: {stats['total_contas_pagar']}"
        print("  -> OK: Dashboard Geral não zera mais os indicadores financeiros.")

        print("\n[TESTE 2] Dashboard Geral e Dashboard Financeiro usam a mesma fonte central...")
        inicio_mes, fim_mes = periodo_mes_atual(hoje)
        resumo_financeiro = resumir_financeiro_periodo(inicio_mes, fim_mes)

        assert stats['total_receitas_mes'] == float(resumo_financeiro.receitas_realizadas)
        assert stats['total_despesas_mes'] == float(resumo_financeiro.despesas_realizadas)
        assert round(stats['saldo_mes'], 2) == round(float(resumo_financeiro.resultado_realizado), 2)
        assert stats['total_contas_receber'] == float(resumo_financeiro.contas_a_receber_pendentes)
        assert stats['total_contas_pagar'] == float(resumo_financeiro.contas_a_pagar_pendentes)
        print("  -> OK: valores idênticos aos do serviço central usado pelo Dashboard Financeiro.")

        print("\n[TESTE 3] Rotas /dashboard e /financeiro/ renderizam 200 com valores coerentes...")
        client.post('/auth/login', data={
            'identificador': 'admin_paridade_test',
            'senha': 'SenhaForte123!',
        }, follow_redirects=True)

        resp_geral = client.get('/dashboard')
        assert resp_geral.status_code == 200, f"Dashboard Geral falhou: {resp_geral.status_code}"
        html_geral = resp_geral.data.decode('utf-8')

        mes_atual = hoje.month
        ano_atual = hoje.year
        resp_fin = client.get(f'/financeiro/?mes={mes_atual}&ano={ano_atual}')
        assert resp_fin.status_code == 200, f"Dashboard Financeiro falhou: {resp_fin.status_code}"
        html_fin = resp_fin.data.decode('utf-8')

        assert 'R$ 540,00' in html_geral, "Dashboard Geral não exibe a receita real do mês"
        assert 'R$ 547,18' in html_geral, "Dashboard Geral não exibe a despesa real do mês"
        assert 'R$ 540,00' in html_fin, "Dashboard Financeiro não exibe a receita real do mês"
        assert 'R$ 547,18' in html_fin, "Dashboard Financeiro não exibe a despesa real do mês"
        print("  -> OK: os dois painéis exibem os mesmos valores para o mês corrente.")

        # Limpeza
        LancamentoFinanceiro.query.filter(
            LancamentoFinanceiro.descricao.like('TEST_PARIDADE_%')
        ).delete()
        db.session.commit()

    print("\n" + "=" * 70)
    print("PARIDADE FINANCEIRA DASHBOARD GERAL x FINANCEIRO VALIDADA COM SUCESSO!")
    print("=" * 70)


if __name__ == '__main__':
    executar_testes()
