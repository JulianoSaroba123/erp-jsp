# -*- coding: utf-8 -*-
"""
Testes de Indicadores Financeiros
==================================

Valida as 12 regras de reconciliação funcional.
Usa banco SQLite temporário para testes isolados.

Execução:
    python scripts/test_financeiro_indicadores.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import date
from decimal import Decimal

from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import LancamentoFinanceiro
from app.financeiro.indicadores_service import resumir_financeiro_periodo


def _novo_lancamento(tipo, status, valor, data_lanc, data_venc=None, data_pag=None, origem='MANUAL'):
    """Helper para criar lançamento de teste."""
    return LancamentoFinanceiro(
        tipo=tipo,
        categoria='Teste',
        descricao='Lançamento teste',
        valor=Decimal(str(valor)),
        data_lancamento=data_lanc,
        data_vencimento=data_venc or data_lanc,
        data_pagamento=data_pag,
        forma_pagamento='PIX',
        status=status,
        origem=origem,
        ativo=True
    )


def _setup_app():
    """Cria aplicação com banco temporário."""
    # Usa TestingConfig que já tem SQLite :memory: e engine correto
    app = create_app('testing')

    with app.app_context():
        db.create_all()

    return app


def _run_test(name, fn):
    """Executa teste e reporta resultado."""
    try:
        fn()
        print(f'✓ [OK] {name}')
        return True
    except AssertionError as e:
        print(f'✗ [FALHA] {name}: {e}')
        return False
    except Exception as e:
        print(f'✗ [ERRO] {name}: {e}')
        return False


def test_01_receita_paga_entra_realizado():
    """Regra 1: Realizado calculado por data_pagamento."""
    app = _setup_app()
    with app.app_context():
        lanc = _novo_lancamento('receita', 'recebido', 100, date(2025, 1, 10), data_pag=date(2025, 1, 10))
        db.session.add(lanc)
        db.session.commit()

        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.receita_realizada == Decimal('100'), f"Esperado 100, obtido {r.receita_realizada}"
        assert r.saldo_realizado == Decimal('100'), f"Esperado 100, obtido {r.saldo_realizado}"


def test_02_despesa_paga_abate_realizado():
    """Regra 1: Despesa paga abate do realizado."""
    app = _setup_app()
    with app.app_context():
        lanc = _novo_lancamento('despesa', 'pago', 40, date(2025, 1, 10), data_pag=date(2025, 1, 10))
        db.session.add(lanc)
        db.session.commit()

        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.despesa_realizada == Decimal('40'), f"Esperado 40, obtido {r.despesa_realizada}"
        assert r.saldo_realizado == Decimal('-40'), f"Esperado -40, obtido {r.saldo_realizado}"


def test_03_pendente_nao_entra_realizado():
    """Regra 2: Pendente não integra realizado."""
    app = _setup_app()
    with app.app_context():
        lanc = _novo_lancamento('receita', 'pendente', 120, date(2025, 1, 10))
        db.session.add(lanc)
        db.session.commit()

        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.receita_realizada == Decimal('0'), f"Esperado 0, obtido {r.receita_realizada}"


def test_04_receita_pendente_vai_receber():
    """Regra 2: Receita pendente entra em contas a receber."""
    app = _setup_app()
    with app.app_context():
        lanc = _novo_lancamento('receita', 'pendente', 120, date(2025, 1, 10))
        db.session.add(lanc)
        db.session.commit()

        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.a_receber_pendente == Decimal('120'), f"Esperado 120, obtido {r.a_receber_pendente}"


def test_05_despesa_pendente_vai_pagar():
    """Regra 2: Despesa pendente entra em contas a pagar."""
    app = _setup_app()
    with app.app_context():
        lanc = _novo_lancamento('despesa', 'pendente', 33, date(2025, 1, 10))
        db.session.add(lanc)
        db.session.commit()

        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.a_pagar_pendente == Decimal('33'), f"Esperado 33, obtido {r.a_pagar_pendente}"


def test_06_projecao_saldo_corresponde_formula():
    """Regra 4: Saldo projetado = realizado + a_receber - a_pagar."""
    app = _setup_app()
    with app.app_context():
        db.session.add(_novo_lancamento('receita', 'recebido', 100, date(2025, 1, 10), data_pag=date(2025, 1, 10)))
        db.session.add(_novo_lancamento('despesa', 'pago', 40, date(2025, 1, 10), data_pag=date(2025, 1, 10)))
        db.session.add(_novo_lancamento('receita', 'pendente', 50, date(2025, 1, 15)))
        db.session.add(_novo_lancamento('despesa', 'pendente', 20, date(2025, 1, 15)))
        db.session.commit()

        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        # Realizado: 100 - 40 = 60
        # Projetado: 60 + 50 - 20 = 90
        assert r.saldo_realizado == Decimal('60'), f"Esperado 60, obtido {r.saldo_realizado}"
        assert r.saldo_projetado == Decimal('90'), f"Esperado 90, obtido {r.saldo_projetado}"


def test_07_pago_sem_data_eh_inconsistencia():
    """Regra 3: Lançamento pago sem data_pagamento é inconsistência."""
    app = _setup_app()
    with app.app_context():
        lanc = _novo_lancamento('receita', 'recebido', 100, date(2025, 1, 10), data_pag=None)
        db.session.add(lanc)
        db.session.commit()

        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.total_inconsistencias == 1, f"Esperado 1 inconsistência, obtido {r.total_inconsistencias}"
        assert r.lancamentos_pagos_sem_data_valor == Decimal('100'), f"Esperado 100, obtido {r.lancamentos_pagos_sem_data_valor}"
        # Inconsistências não entram no realizado
        assert r.receita_realizada == Decimal('0'), f"Esperado 0, obtido {r.receita_realizada}"


def test_08_data_pagamento_define_periodo_realizado():
    """Regra 1: data_pagamento define período do realizado, não data_lancamento."""
    app = _setup_app()
    with app.app_context():
        # Lançado em janeiro, pago em fevereiro
        lanc = _novo_lancamento('receita', 'recebido', 100,
                               data_lanc=date(2025, 1, 10),
                               data_venc=date(2025, 1, 15),
                               data_pag=date(2025, 2, 5))
        db.session.add(lanc)
        db.session.commit()

        # Janeiro: não deve aparecer no realizado
        r_jan = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r_jan.receita_realizada == Decimal('0'), f"Janeiro deveria ter 0, obtido {r_jan.receita_realizada}"

        # Fevereiro: deve aparecer no realizado
        r_fev = resumir_financeiro_periodo(date(2025, 2, 1), date(2025, 2, 28))
        assert r_fev.receita_realizada == Decimal('100'), f"Fevereiro deveria ter 100, obtido {r_fev.receita_realizada}"


def test_09_vencimento_define_periodo_pendente():
    """Regra 2: data_vencimento define período do pendente."""
    app = _setup_app()
    with app.app_context():
        # Lançado em janeiro, vence em fevereiro
        lanc = _novo_lancamento('receita', 'pendente', 100,
                               data_lanc=date(2025, 1, 10),
                               data_venc=date(2025, 2, 15))
        db.session.add(lanc)
        db.session.commit()

        # Janeiro: não deve aparecer
        r_jan = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r_jan.a_receber_pendente == Decimal('0'), f"Janeiro deveria ter 0, obtido {r_jan.a_receber_pendente}"

        # Fevereiro: deve aparecer
        r_fev = resumir_financeiro_periodo(date(2025, 2, 1), date(2025, 2, 28))
        assert r_fev.a_receber_pendente == Decimal('100'), f"Fevereiro deveria ter 100, obtido {r_fev.a_receber_pendente}"


def test_10_decimal_preserva_precisao():
    """Regra 4: Cálculos monetários usam Decimal."""
    app = _setup_app()
    with app.app_context():
        # Valores que causariam erro de arredondamento com float
        db.session.add(_novo_lancamento('receita', 'recebido', '33.33', date(2025, 1, 10), data_pag=date(2025, 1, 10)))
        db.session.add(_novo_lancamento('receita', 'recebido', '33.33', date(2025, 1, 10), data_pag=date(2025, 1, 10)))
        db.session.add(_novo_lancamento('receita', 'recebido', '33.34', date(2025, 1, 10), data_pag=date(2025, 1, 10)))
        db.session.commit()

        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.receita_realizada == Decimal('100.00'), f"Esperado 100.00, obtido {r.receita_realizada}"
        assert isinstance(r.receita_realizada, Decimal), "Deveria ser Decimal"


def main():
    """Executa todos os testes."""
    print("\n" + "="*80)
    print("TESTES DE INDICADORES FINANCEIROS")
    print("Validando Regras 1-4 de Reconciliação Funcional")
    print("="*80 + "\n")

    tests = [
        ("Regra 1: Receita paga entra no realizado", test_01_receita_paga_entra_realizado),
        ("Regra 1: Despesa paga abate do realizado", test_02_despesa_paga_abate_realizado),
        ("Regra 2: Pendente não entra no realizado", test_03_pendente_nao_entra_realizado),
        ("Regra 2: Receita pendente em contas a receber", test_04_receita_pendente_vai_receber),
        ("Regra 2: Despesa pendente em contas a pagar", test_05_despesa_pendente_vai_pagar),
        ("Regra 4: Projeção = realizado + a_receber - a_pagar", test_06_projecao_saldo_corresponde_formula),
        ("Regra 3: Pago sem data é inconsistência", test_07_pago_sem_data_eh_inconsistencia),
        ("Regra 1: data_pagamento define período realizado", test_08_data_pagamento_define_periodo_realizado),
        ("Regra 2: data_vencimento define período pendente", test_09_vencimento_define_periodo_pendente),
        ("Regra 4: Decimal preserva precisão monetária", test_10_decimal_preserva_precisao),
    ]

    results = []
    for name, test_fn in tests:
        results.append(_run_test(name, test_fn))

    print("\n" + "="*80)
    passed = sum(results)
    total = len(results)
    print(f"RESULTADO: {passed}/{total} testes passaram")

    if passed == total:
        print("✓ TODOS OS TESTES PASSARAM")
        return 0
    else:
        print(f"✗ {total - passed} TESTE(S) FALHARAM")
        return 1


if __name__ == '__main__':
    sys.exit(main())
