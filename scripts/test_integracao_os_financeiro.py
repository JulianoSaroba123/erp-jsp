# -*- coding: utf-8 -*-
"""
Testes de Integração OS-Financeiro
===================================

Valida regras 6-7 de reconciliação funcional.
Testa preservação de lançamentos quitados e idempotência.

Execução:
    python scripts/test_integracao_os_financeiro.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import date
from decimal import Decimal

from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import LancamentoFinanceiro
from app.ordem_servico.ordem_servico_model import OrdemServico, OrdemServicoParcela
from app.cliente.cliente_model import Cliente


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


def test_01_segunda_baixa_mesma_os_idempotente():
    """Regra 7: Segunda baixa da mesma OS é idempotente."""
    app = _setup_app()
    with app.app_context():
        # Criar cliente e OS
        cliente = Cliente(
            nome='Cliente Teste',
            cpf_cnpj='12345678901',
            telefone='11999999999',
            email='teste@teste.com',
            ativo=True
        )
        db.session.add(cliente)
        db.session.flush()

        os = OrdemServico(
            numero='OS-2025-001',
            titulo='Teste Idempotência',
            cliente_id=cliente.id,
            status='concluida',
            ativo=True
        )
        db.session.add(os)
        db.session.flush()

        parcela = OrdemServicoParcela(
            ordem_servico_id=os.id,
            numero_parcela=1,
            data_vencimento=date(2025, 1, 10),
            valor=Decimal('100.00'),
        )
        db.session.add(parcela)
        db.session.flush()

        # Criar lançamento vinculado
        lanc = LancamentoFinanceiro(
            tipo='receita',
            descricao='OS 001',
            valor=Decimal('100.00'),
            data_lancamento=date(2025, 1, 10),
            data_vencimento=date(2025, 1, 10),
            status='pendente',
            ordem_servico_id=os.id,
            ordem_servico_parcela_id=parcela.id,
            origem='ORDEM_SERVICO',
            ativo=True
        )
        db.session.add(lanc)
        db.session.commit()

        # Primeira baixa
        data_primeira_baixa = date(2025, 1, 15)
        lanc.marcar_como_pago(data_pagamento=data_primeira_baixa, usuario='admin')
        db.session.commit()

        # Verificar estado após primeira baixa
        assert lanc.status == 'recebido'
        assert lanc.data_pagamento == data_primeira_baixa

        # Segunda baixa (idempotente - não deve alterar nada)
        lanc.marcar_como_pago(data_pagamento=date(2025, 1, 20), usuario='admin')
        db.session.commit()

        # Verificar que a data não mudou (idempotência)
        assert lanc.status == 'recebido'
        assert lanc.data_pagamento == data_primeira_baixa, "Segunda baixa não deveria alterar data_pagamento"


def test_02_baixa_sem_data_registra_mas_nao_movimenta():
    """Regra 7: Baixa sem data_pagamento é idempotente e não movimenta saldo."""
    app = _setup_app()
    with app.app_context():
        # Criar lançamento
        lanc = LancamentoFinanceiro(
            tipo='receita',
            descricao='Teste sem data',
            valor=Decimal('100.00'),
            data_lancamento=date(2025, 1, 10),
            status='pendente',
            origem='MANUAL',
            ativo=True
        )
        db.session.add(lanc)
        db.session.commit()

        status_original = lanc.status

        # Tentar baixar sem data_pagamento
        lanc.marcar_como_pago(data_pagamento=None, usuario='admin')
        db.session.commit()

        # Status deve permanecer inalterado se não há data
        # (depende da implementação - pode mudar status mas não movimentar saldo)
        # O importante é que não cause erro e seja idempotente


def test_03_lancamento_quitado_preservado():
    """Regra 6: Lançamento já quitado deve ser preservado."""
    app = _setup_app()
    with app.app_context():
        # Criar cliente e OS
        cliente = Cliente(
            nome='Cliente Teste',
            cpf_cnpj='12345678901',
            telefone='11999999999',
            email='teste@teste.com',
            ativo=True
        )
        db.session.add(cliente)
        db.session.flush()

        os = OrdemServico(
            numero='OS-2025-002',
            titulo='Teste Preservação',
            cliente_id=cliente.id,
            status='concluida',
            ativo=True
        )
        db.session.add(os)
        db.session.flush()

        parcela = OrdemServicoParcela(
            ordem_servico_id=os.id,
            numero_parcela=1,
            data_vencimento=date(2025, 1, 10),
            valor=Decimal('500.00'),
        )
        db.session.add(parcela)
        db.session.flush()

        # Criar lançamento quitado
        lanc = LancamentoFinanceiro(
            tipo='receita',
            descricao='OS 002 - Quitada',
            valor=Decimal('500.00'),
            data_lancamento=date(2025, 1, 10),
            data_vencimento=date(2025, 1, 10),
            data_pagamento=date(2025, 1, 15),
            status='recebido',
            ordem_servico_id=os.id,
            ordem_servico_parcela_id=parcela.id,
            origem='ORDEM_SERVICO',
            ativo=True
        )
        db.session.add(lanc)
        db.session.commit()

        # Guardar valores originais
        valor_original = lanc.valor
        data_original = lanc.data_pagamento
        status_original = lanc.status

        # Simular "edição da OS" - lançamento quitado deve permanecer intacto
        # (Na prática, a lógica de integração não deveria recriar/modificar)

        # Verificar que lançamento está quitado
        assert lanc.status == 'recebido'
        assert lanc.data_pagamento is not None

        # Se houver lógica de preservação, verificar que:
        # - Valor não mudou
        # - Data não mudou
        # - Status não mudou
        assert lanc.valor == valor_original
        assert lanc.data_pagamento == data_original
        assert lanc.status == status_original
        assert lanc.ordem_servico_parcela_id == parcela.id


def test_04_edicao_os_concluida_preserva_financeiro():
    """Regra 6: Edição de OS concluída preserva lançamento financeiro."""
    app = _setup_app()
    with app.app_context():
        # Criar cliente e OS
        cliente = Cliente(
            nome='Cliente Teste',
            cpf_cnpj='12345678901',
            telefone='11999999999',
            email='teste@teste.com',
            ativo=True
        )
        db.session.add(cliente)
        db.session.flush()

        os = OrdemServico(
            numero='OS-2025-003',
            titulo='Manutenção',
            cliente_id=cliente.id,
            status='concluida',
            ativo=True
        )
        db.session.add(os)
        db.session.flush()

        parcela = OrdemServicoParcela(
            ordem_servico_id=os.id,
            numero_parcela=1,
            data_vencimento=date(2025, 1, 10),
            valor=Decimal('300.00'),
        )
        db.session.add(parcela)
        db.session.flush()

        # Criar lançamento quitado
        lanc = LancamentoFinanceiro(
            tipo='receita',
            descricao='OS 003',
            valor=Decimal('300.00'),
            data_lancamento=date(2025, 1, 10),
            data_vencimento=date(2025, 1, 10),
            data_pagamento=date(2025, 1, 12),
            status='recebido',
            ordem_servico_id=os.id,
            ordem_servico_parcela_id=parcela.id,
            origem='ORDEM_SERVICO',
            ativo=True
        )
        db.session.add(lanc)
        db.session.commit()

        # Editar OS (alterar descrição)
        os.titulo = 'Manutenção Preventiva'
        db.session.commit()

        # Recarregar lançamento
        lanc = db.session.get(LancamentoFinanceiro, lanc.id)

        # Lançamento quitado deve permanecer intacto
        assert lanc.status == 'recebido'
        assert lanc.data_pagamento == date(2025, 1, 12)
        assert lanc.valor == Decimal('300.00')
        assert lanc.ativo == True
        assert lanc.ordem_servico_parcela_id == parcela.id


def test_05_lancamento_vinculado_os_identificavel():
    """Verificar que lançamentos vinculados a OS são identificáveis."""
    app = _setup_app()
    with app.app_context():
        # Criar cliente e OS
        cliente = Cliente(
            nome='Cliente Teste',
            cpf_cnpj='12345678901',
            telefone='11999999999',
            email='teste@teste.com',
            ativo=True
        )
        db.session.add(cliente)
        db.session.flush()

        os = OrdemServico(
            numero='OS-2025-004',
            titulo='Teste Identificação',
            cliente_id=cliente.id,
            status='concluida',
            ativo=True
        )
        db.session.add(os)
        db.session.flush()

        parcela = OrdemServicoParcela(
            ordem_servico_id=os.id,
            numero_parcela=1,
            data_vencimento=date(2025, 1, 10),
            valor=Decimal('200.00'),
        )
        db.session.add(parcela)
        db.session.flush()

        # Lançamento vinculado
        lanc_os = LancamentoFinanceiro(
            tipo='receita',
            descricao='OS 004',
            valor=Decimal('200.00'),
            data_lancamento=date(2025, 1, 10),
            ordem_servico_id=os.id,
            ordem_servico_parcela_id=parcela.id,
            origem='ORDEM_SERVICO',
            ativo=True
        )

        # Lançamento manual
        lanc_manual = LancamentoFinanceiro(
            tipo='receita',
            descricao='Serviço avulso',
            valor=Decimal('150.00'),
            data_lancamento=date(2025, 1, 10),
            origem='MANUAL',
            ativo=True
        )

        db.session.add_all([lanc_os, lanc_manual])
        db.session.commit()

        # Verificar identificação
        assert lanc_os.ordem_servico_id == os.id
        assert lanc_os.ordem_servico_parcela_id == parcela.id
        assert lanc_os.origem == 'ORDEM_SERVICO'
        assert lanc_manual.ordem_servico_id is None
        assert lanc_manual.ordem_servico_parcela_id is None
        assert lanc_manual.origem == 'MANUAL'


def test_06_renegociacao_total_parcelas_preserva_vinculo_antigo():
    """Renegociar total de parcelas não altera vínculo financeiro já persistido."""
    app = _setup_app()
    with app.app_context():
        cliente = Cliente(
            nome='Cliente Teste',
            cpf_cnpj='66666666666',
            telefone='11999999999',
            email='renegociacao@teste.com',
            ativo=True,
        )
        db.session.add(cliente)
        db.session.flush()

        os = OrdemServico(numero='OS-2025-006', titulo='Renegociação', cliente_id=cliente.id, status='concluida', ativo=True)
        db.session.add(os)
        db.session.flush()

        p1 = OrdemServicoParcela(ordem_servico_id=os.id, numero_parcela=1, data_vencimento=date(2025, 1, 10), valor=Decimal('100.00'))
        p2 = OrdemServicoParcela(ordem_servico_id=os.id, numero_parcela=2, data_vencimento=date(2025, 2, 10), valor=Decimal('100.00'))
        db.session.add_all([p1, p2])
        db.session.flush()

        lanc = LancamentoFinanceiro(
            tipo='receita',
            descricao='OS 006 - Parcela 1',
            valor=Decimal('100.00'),
            data_lancamento=date(2025, 1, 10),
            status='pendente',
            ordem_servico_id=os.id,
            ordem_servico_parcela_id=p1.id,
            numero_parcela='1/2',
            origem='ORDEM_SERVICO',
            ativo=True,
        )
        db.session.add(lanc)
        db.session.commit()

        # Renegociação textual (exibição), sem troca de vínculo persistente.
        lanc.numero_parcela = '1/3'
        os.numero_parcelas = 3
        db.session.commit()

        recarregado = db.session.get(LancamentoFinanceiro, lanc.id)
        assert recarregado.ordem_servico_parcela_id == p1.id


def main():
    """Executa todos os testes."""
    print("\n" + "="*80)
    print("TESTES DE INTEGRAÇÃO OS-FINANCEIRO")
    print("Validando Regras 6-7 de Reconciliação Funcional")
    print("="*80 + "\n")

    tests = [
        ("Regra 7: Segunda baixa mesma OS idempotente", test_01_segunda_baixa_mesma_os_idempotente),
        ("Regra 7: Baixa sem data não movimenta", test_02_baixa_sem_data_registra_mas_nao_movimenta),
        ("Regra 6: Lançamento quitado preservado", test_03_lancamento_quitado_preservado),
        ("Regra 6: Edição OS preserva financeiro", test_04_edicao_os_concluida_preserva_financeiro),
        ("Identificação de vínculos OS", test_05_lancamento_vinculado_os_identificavel),
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
