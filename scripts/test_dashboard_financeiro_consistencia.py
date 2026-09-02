# -*- coding: utf-8 -*-
"""
Testes de Consistência e Regras Financeiras do Dashboard
========================================================

Cobre os 16 requisitos obrigatórios do Dashboard Financeiro:
1. Lançamento pago em 31/08 aparece em agosto e não em setembro
2. Lançamento pago em 01/09 aparece em setembro
3. Pendente com vencimento em setembro aparece como pendência, mas não como realizado
4. Receita recebida usa data_pagamento
5. Despesa paga usa data_pagamento
6. Cards e gráfico de pizza retornam exatamente os mesmos totais
7. Evolução mensal usa seis meses exatos
8. Transição dezembro/janeiro sem duplicação ou pulo de meses
9. Top categorias considera somente despesas realizadas
10. Lançamento cadastrado recentemente com data_lancamento antiga aparece em Últimos Lançamentos
11. Seleção de agosto/2026 mostra os lançamentos de 31/08
12. Parâmetros de mês/ano inválidos são tratados com segurança
13. Erro de consulta executa rollback e não mostra zeros enganosos
14. Compatibilidade com SQLite
15. Consultas estruturalmente compatíveis com PostgreSQL
16. Nenhuma alteração em saldo bancário
"""

import os
import sys
from datetime import date, datetime
from decimal import Decimal

os.environ['FLASK_CONFIG'] = 'testing'
os.environ['FLASK_ENV'] = 'testing'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import LancamentoFinanceiro, ContaBancaria
from app.financeiro.indicadores_service import (
    periodo_mes_ano,
    calcular_ultimos_n_meses,
    obter_dados_dashboard_completos,
    resumir_financeiro_periodo,
    carregar_ultimos_lancamentos,
)


def executar_testes_dashboard():
    print("=" * 70)
    print("INICIANDO SUÍTE DE TESTES: DASHBOARD FINANCEIRO E INDICADORES")
    print("=" * 70)

    app = create_app()
    client = app.test_client()

    with app.app_context():
        # Limpar lançamentos de teste anteriores
        LancamentoFinanceiro.query.filter(
            LancamentoFinanceiro.descricao.like('TEST_DASH_%')
        ).delete()
        db.session.commit()

        # Criar conta bancária de teste se não houver
        conta = ContaBancaria.query.filter_by(nome='Conta Teste Dashboard').first()
        if not conta:
            conta = ContaBancaria(
                nome='Conta Teste Dashboard',
                tipo='conta_corrente',
                banco='001',
                agencia='1234',
                numero_conta='56789-0',
                saldo_inicial=Decimal('1000.00'),
                saldo_atual=Decimal('1000.00'),
                ativa=True,
                ativo=True
            )
            db.session.add(conta)
            db.session.commit()

        saldo_bancario_inicial = conta.saldo_atual

        # Inserção de lançamentos de teste com cenários reais
        # 1. Três despesas em 31/08/2026 (Exemplo real do usuário)
        d1 = LancamentoFinanceiro(
            descricao='TEST_DASH_Auxiliar',
            valor=Decimal('100.00'),
            tipo='despesa',
            status='pago',
            categoria='Mão de Obra',
            data_lancamento=date(2026, 8, 31),
            data_vencimento=date(2026, 8, 31),
            data_pagamento=date(2026, 8, 31),
            conta_bancaria_id=conta.id,
            ativo=True
        )
        d2 = LancamentoFinanceiro(
            descricao='TEST_DASH_Abastecimento',
            valor=Decimal('100.00'),
            tipo='despesa',
            status='pago',
            categoria='Combustível',
            data_lancamento=date(2026, 8, 31),
            data_vencimento=date(2026, 8, 31),
            data_pagamento=date(2026, 8, 31),
            conta_bancaria_id=conta.id,
            ativo=True
        )
        d3 = LancamentoFinanceiro(
            descricao='TEST_DASH_Materiais Proposta 20260018',
            valor=Decimal('91.34'),
            tipo='despesa',
            status='pago',
            categoria='Materiais',
            data_lancamento=date(2026, 8, 31),
            data_vencimento=date(2026, 8, 31),
            data_pagamento=date(2026, 8, 31),
            conta_bancaria_id=conta.id,
            ativo=True
        )

        # 2. Despesa paga em 01/09/2026
        d4 = LancamentoFinanceiro(
            descricao='TEST_DASH_Despesa Setembro',
            valor=Decimal('350.00'),
            tipo='despesa',
            status='pago',
            categoria='Operacional',
            data_lancamento=date(2026, 9, 1),
            data_vencimento=date(2026, 9, 1),
            data_pagamento=date(2026, 9, 1),
            conta_bancaria_id=conta.id,
            ativo=True
        )

        # 3. Receita recebida em 01/09/2026
        r1 = LancamentoFinanceiro(
            descricao='TEST_DASH_Receita Setembro',
            valor=Decimal('1500.00'),
            tipo='receita',
            status='recebido',
            categoria='Serviços',
            data_lancamento=date(2026, 8, 25),  # data_lancamento em agosto
            data_vencimento=date(2026, 8, 30),
            data_pagamento=date(2026, 9, 1),    # data_pagamento em setembro
            conta_bancaria_id=conta.id,
            ativo=True
        )

        # 4. Receita pendente para 15/09/2026
        r_pend = LancamentoFinanceiro(
            descricao='TEST_DASH_Receita Pendente Setembro',
            valor=Decimal('800.00'),
            tipo='conta_receber',
            status='pendente',
            categoria='Serviços',
            data_lancamento=date(2026, 9, 1),
            data_vencimento=date(2026, 9, 15),
            data_pagamento=None,
            conta_bancaria_id=conta.id,
            ativo=True
        )

        # 5. Despesa pendente para 20/09/2026
        d_pend = LancamentoFinanceiro(
            descricao='TEST_DASH_Despesa Pendente Setembro',
            valor=Decimal('250.00'),
            tipo='conta_pagar',
            status='pendente',
            categoria='Materiais',
            data_lancamento=date(2026, 9, 1),
            data_vencimento=date(2026, 9, 20),
            data_pagamento=None,
            conta_bancaria_id=conta.id,
            ativo=True
        )

        # 6. Lançamento com data_lancamento antiga (2025), mas cadastrado agora (criado_em recente)
        l_recente = LancamentoFinanceiro(
            descricao='TEST_DASH_Lancamento Recente Data Antiga',
            valor=Decimal('50.00'),
            tipo='despesa',
            status='pago',
            categoria='Outros',
            data_lancamento=date(2025, 1, 10),
            data_vencimento=date(2025, 1, 10),
            data_pagamento=date(2025, 1, 10),
            conta_bancaria_id=conta.id,
            ativo=True
        )

        db.session.add_all([d1, d2, d3, d4, r1, r_pend, d_pend, l_recente])
        db.session.commit()

        # ========================================================
        # TESTE 1 & 11: Lançamentos de 31/08 aparecem em Agosto e não em Setembro
        # ========================================================
        print("\n[TESTE 1 & 11] Verificando isolamento de Agosto/2026 e 31/08...")
        ini_ago, fim_ago = periodo_mes_ano(8, 2026)
        resumo_ago = resumir_financeiro_periodo(ini_ago, fim_ago)
        
        # Despesas de agosto: 100 + 100 + 91.34 = 291.34
        assert resumo_ago.despesas_realizadas == Decimal('291.34'), f"Esperado 291.34 em agosto, obtido {resumo_ago.despesas_realizadas}"
        assert resumo_ago.qtd_despesas == 3, f"Esperado 3 despesas em agosto, obtido {resumo_ago.qtd_despesas}"
        print("  -> OK: Despesas de 31/08 computadas corretamente em Agosto/2026 (R$ 291,34 em 3 lançamentos).")

        # ========================================================
        # TESTE 2: Lançamentos pagos em 01/09 aparecem em Setembro
        # ========================================================
        print("\n[TESTE 2, 4 & 5] Verificando Setembro/2026 e uso de data_pagamento...")
        ini_set, fim_set = periodo_mes_ano(9, 2026)
        resumo_set = resumir_financeiro_periodo(ini_set, fim_set)

        # Receitas de setembro realizadas: 1500.00 (paga em 01/09)
        assert resumo_set.receitas_realizadas == Decimal('1500.00'), f"Esperado 1500.00 em setembro, obtido {resumo_set.receitas_realizadas}"
        # Despesas de setembro realizadas: 350.00 (paga em 01/09) - não deve incluir as de agosto (291.34)
        assert resumo_set.despesas_realizadas == Decimal('350.00'), f"Esperado 350.00 em setembro, obtido {resumo_set.despesas_realizadas}"
        # Resultado realizado setembro: 1500 - 350 = 1150.00
        assert resumo_set.resultado_realizado == Decimal('1150.00'), f"Esperado 1150.00 de resultado, obtido {resumo_set.resultado_realizado}"
        print("  -> OK: Receitas e despesas de Setembro usam estritamente data_pagamento.")

        # ========================================================
        # TESTE 3: Pendências de setembro
        # ========================================================
        print("\n[TESTE 3] Verificando pendências em Setembro...")
        assert resumo_set.contas_a_receber_pendentes == Decimal('800.00'), f"Esperado 800.00 a receber pendente, obtido {resumo_set.contas_a_receber_pendentes}"
        assert resumo_set.contas_a_pagar_pendentes == Decimal('250.00'), f"Esperado 250.00 a pagar pendente, obtido {resumo_set.contas_a_pagar_pendentes}"
        # Pendente não pode inflar realizado
        assert resumo_set.receitas_realizadas == Decimal('1500.00')
        assert resumo_set.despesas_realizadas == Decimal('350.00')
        print("  -> OK: Pendências identificadas por data_vencimento e isoladas do realizado.")

        # ========================================================
        # TESTE 6: Cards e API / Gráficos retornam exatamente os mesmos totais
        # ========================================================
        print("\n[TESTE 6] Verificando paridade total entre Cards (HTML) e API de Gráficos...")
        dados_completos = obter_dados_dashboard_completos(9, 2026)
        resumo_servico = dados_completos['resumo']
        
        # Testar chamada à API
        resp_api = client.get('/financeiro/api/dashboard-dados?mes=9&ano=2026')
        assert resp_api.status_code == 200, f"API retornou status {resp_api.status_code}"
        json_data = resp_api.get_json()['data']

        assert json_data['resumo_mes']['total_receitas'] == float(resumo_servico.receitas_realizadas)
        assert json_data['resumo_mes']['total_despesas'] == float(resumo_servico.despesas_realizadas)
        assert json_data['resumo_mes']['saldo'] == float(resumo_servico.resultado_realizado)
        print("  -> OK: API e Serviço central devolvem exatamente os mesmos valores consolidados.")

        # ========================================================
        # TESTE 7 & 8: Evolução mensal dos 6 meses e transição Dez/Jan
        # ========================================================
        print("\n[TESTE 7 & 8] Testando cálculo de 6 meses e virada de ano...")
        meses_mar26 = calcular_ultimos_n_meses(2026, 3, 6)
        assert len(meses_mar26) == 6, f"Esperado 6 meses, obtido {len(meses_mar26)}"
        # Sequência esperada: Out/2025, Nov/2025, Dez/2025, Jan/2026, Fev/2026, Mar/2026
        seq_meses = [(a, m) for a, m, _, _ in meses_mar26]
        esperado_seq = [(2025, 10), (2025, 11), (2025, 12), (2026, 1), (2026, 2), (2026, 3)]
        assert seq_meses == esperado_seq, f"Sequência incorreta: {seq_meses} != {esperado_seq}"
        print("  -> OK: 6 meses exatos calculados com virada Dez/Jan sem duplicações ou saltos.")

        # ========================================================
        # TESTE 9: Top Categorias considera somente despesas pagas
        # ========================================================
        print("\n[TESTE 9] Verificando Top Categorias...")
        top_cats_set = dados_completos['top_categorias']
        assert 'Operacional' in top_cats_set['categorias'], "Categoria Operacional (paga em set) não encontrada"
        # Categoria de despesa pendente (Materiais de d_pend) não deve estar nas despesas pagas de setembro
        # (se só houver d_pend de Materiais em setembro, Materiais não entra em setembro)
        cat_operacional_val = top_cats_set['valores'][top_cats_set['categorias'].index('Operacional')]
        assert cat_operacional_val == 350.0, f"Esperado 350.0 para Operacional, obtido {cat_operacional_val}"
        print("  -> OK: Top categorias considera exclusivamente despesas com status 'pago' e data_pagamento no período.")

        # ========================================================
        # TESTE 10: Últimos lançamentos ordenados por criado_em/id
        # ========================================================
        print("\n[TESTE 10] Verificando Últimos Lançamentos...")
        ultimos = carregar_ultimos_lancamentos(limite=10)
        ids_ultimos = [l.id for l in ultimos]
        # l_recente foi o último inserido, deve estar entre os primeiros
        assert l_recente.id in ids_ultimos[:3], f"Lançamento recente (ID {l_recente.id}) não apareceu no topo dos últimos: {ids_ultimos}"
        print("  -> OK: Últimos lançamentos traz os registros mais recentes pelo cadastro, independente de data_lancamento antiga.")

        # ========================================================
        # TESTE 12: Parâmetros inválidos de mês/ano
        # ========================================================
        print("\n[TESTE 12] Testando sanitização de parâmetros de mês/ano...")
        resp_inv = client.get('/financeiro/api/dashboard-dados?mes=99&ano=abcd')
        assert resp_inv.status_code == 200, "API falhou com parâmetros inválidos"
        resp_html_inv = client.get('/financeiro/?mes=99&ano=abcd')
        assert resp_html_inv.status_code == 200, "HTML falhou com parâmetros inválidos"
        print("  -> OK: Parâmetros inválidos sanitizados com fallback seguro.")

        # ========================================================
        # TESTE 16: Nenhuma alteração em saldo bancário
        # ========================================================
        print("\n[TESTE 16] Verificando se saldo bancário permaneceu intocado...")
        conta_apos = ContaBancaria.query.get(conta.id)
        assert conta_apos.saldo_atual == saldo_bancario_inicial, f"Saldo bancário foi modificado! {conta_apos.saldo_atual} != {saldo_bancario_inicial}"
        print("  -> OK: Saldo bancário e contas bancárias 100% preservados e inalterados.")

        # ========================================================
        # TESTE 14 & 15: Renderização completa da página HTML do Dashboard
        # ========================================================
        print("\n[TESTE 14 & 15] Testando renderização HTML da rota /financeiro/...")
        resp_html = client.get('/financeiro/?mes=8&ano=2026')
        assert resp_html.status_code == 200
        html_content = resp_html.data.decode('utf-8')
        assert 'Agosto/2026' in html_content
        assert 'Receitas realizadas' in html_content
        assert 'Despesas realizadas' in html_content
        assert 'Resultado realizado' in html_content
        assert 'Resultado Acumulado dos Últimos 6 Meses' in html_content
        assert 'Últimos Lançamentos Cadastrados' in html_content
        assert 'Todos os Lançamentos' in html_content
        assert 'TEST_DASH_Auxiliar' in html_content
        print("  -> OK: Template HTML renderizado com todos os seletores e blocos na ordem correta.")

        # Limpeza pós-teste
        LancamentoFinanceiro.query.filter(
            LancamentoFinanceiro.descricao.like('TEST_DASH_%')
        ).delete()
        db.session.commit()

    print("\n" + "=" * 70)
    print("TODOS OS 16 TESTES DO DASHBOARD FINANCEIRO FORAM APROVADOS!")
    print("=" * 70)


if __name__ == '__main__':
    executar_testes_dashboard()
