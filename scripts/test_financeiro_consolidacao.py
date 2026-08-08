# -*- coding: utf-8 -*-
"""
Testes de Consolidação e Deduplicação Financeira
================================================

Valida regras 8-11 de reconciliação funcional.
Testa deduplicação, chaves confiáveis e independência de lançamentos.

Execução:
    python scripts/test_financeiro_consolidacao.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import date
from decimal import Decimal

from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import ContaBancaria, HistoricoFinanceiro, LancamentoFinanceiro
from app.financeiro.financeiro_utils import atualizar_status_financeiro_ordem, calcular_metricas_dashboard
from app.financeiro.indicadores_service import (
    montar_registro_exibicao,
    _deduplicar_ocorrencias_confiaveis,
    carregar_registros_financeiros,
    resumir_financeiro_periodo,
)
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


def test_01_lancamentos_sem_chave_nao_deduplica():
    """Regra 9: OS diferentes com mesmo cliente/valor permanecem independentes."""
    app = _setup_app()
    with app.app_context():
        # Criar cliente
        cliente = Cliente(
            nome='Cliente Teste',
            cpf_cnpj='12345678901',
            telefone='11999999999',
            email='teste@teste.com',
            ativo=True
        )
        db.session.add(cliente)
        db.session.commit()

        # Dois lançamentos manuais mesmo valor, sem chave confiável
        lanc1 = LancamentoFinanceiro(
            tipo='receita',
            categoria='Serviço A',
            descricao='Serviço prestado',
            valor=Decimal('100.00'),
            data_lancamento=date(2025, 1, 10),
            data_vencimento=date(2025, 1, 10),
            status='pendente',
            cliente_id=cliente.id,
            origem='MANUAL',
            ativo=True
        )
        lanc2 = LancamentoFinanceiro(
            tipo='receita',
            categoria='Serviço B',
            descricao='Serviço prestado',
            valor=Decimal('100.00'),
            data_lancamento=date(2025, 1, 10),
            data_vencimento=date(2025, 1, 10),
            status='pendente',
            cliente_id=cliente.id,
            origem='MANUAL',
            ativo=True
        )
        db.session.add_all([lanc1, lanc2])
        db.session.commit()

        # Converter para views
        view1 = montar_registro_exibicao(lanc1)
        view2 = montar_registro_exibicao(lanc2)

        # Lançamentos manuais usam identidade própria por ID.
        assert view1.chave_ocorrencia_confiavel == f'lancamento:{lanc1.id}'
        assert view2.chave_ocorrencia_confiavel == f'lancamento:{lanc2.id}'

        # Deduplicar - ambos devem permanecer
        deduplicados = _deduplicar_ocorrencias_confiaveis([view1, view2])
        assert len(deduplicados) == 2, f"Esperado 2 registros, obtido {len(deduplicados)}"


def test_02_os_com_chave_deduplica():
    """Regra 8 e 11: Lançamentos de mesma OS com chave confiável deduplica."""
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
            titulo='Teste',
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

        # Dois lançamentos vinculados à mesma parcela persistente
        lanc1 = LancamentoFinanceiro(
            tipo='receita',
            categoria='Ordem de Serviço',
            descricao='OS 001 - Parcela 1',
            valor=Decimal('100.00'),
            data_lancamento=date(2025, 1, 10),
            data_vencimento=date(2025, 1, 10),
            status='pendente',
            cliente_id=cliente.id,
            ordem_servico_id=os.id,
            ordem_servico_parcela_id=parcela.id,
            numero_parcela='1/1',
            origem='ORDEM_SERVICO',
            ativo=True
        )
        lanc2 = LancamentoFinanceiro(
            tipo='receita',
            categoria='Ordem de Serviço (legado)',
            descricao='OS 001 - Parcela 1',
            valor=Decimal('100.00'),
            data_lancamento=date(2025, 1, 10),
            data_vencimento=date(2025, 1, 10),
            status='pendente',
            cliente_id=cliente.id,
            ordem_servico_id=os.id,
            ordem_servico_parcela_id=parcela.id,
            numero_parcela='1/1',
            origem='MANUAL',
            ativo=True
        )
        db.session.add_all([lanc1, lanc2])
        db.session.commit()

        # Converter para views
        view1 = montar_registro_exibicao(lanc1)
        view2 = montar_registro_exibicao(lanc2)

        # Ambos devem ter a mesma chave confiável
        assert view1.chave_ocorrencia_confiavel is not None
        assert view1.chave_ocorrencia_confiavel == view2.chave_ocorrencia_confiavel

        # Deduplicar - deve manter apenas o de origem ORDEM_SERVICO (prioridade maior)
        deduplicados = _deduplicar_ocorrencias_confiaveis([view1, view2])
        assert len(deduplicados) == 1, f"Esperado 1 registro após deduplicação, obtido {len(deduplicados)}"
        assert deduplicados[0].origem == 'ORDEM_SERVICO', "Deveria priorizar origem ORDEM_SERVICO"


def test_03_parcelas_legitimas_preservadas():
    """Regra 10: Parcelas legítimas da mesma OS são preservadas."""
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
            titulo='Teste Parcelas',
            cliente_id=cliente.id,
            status='concluida',
            ativo=True
        )
        db.session.add(os)
        db.session.flush()

        p1 = OrdemServicoParcela(
            ordem_servico_id=os.id,
            numero_parcela=1,
            data_vencimento=date(2025, 1, 10),
            valor=Decimal('100.00'),
        )
        p2 = OrdemServicoParcela(
            ordem_servico_id=os.id,
            numero_parcela=2,
            data_vencimento=date(2025, 2, 10),
            valor=Decimal('100.00'),
        )
        p3 = OrdemServicoParcela(
            ordem_servico_id=os.id,
            numero_parcela=3,
            data_vencimento=date(2025, 3, 10),
            valor=Decimal('100.00'),
        )
        db.session.add_all([p1, p2, p3])
        db.session.flush()

        # Três parcelas persistentes da mesma OS
        lanc1 = LancamentoFinanceiro(
            tipo='receita',
            descricao='OS 002 - Parcela 1/3',
            valor=Decimal('100.00'),
            data_lancamento=date(2025, 1, 10),
            data_vencimento=date(2025, 1, 10),
            status='pendente',
            ordem_servico_id=os.id,
            ordem_servico_parcela_id=p1.id,
            numero_parcela='1/3',
            origem='ORDEM_SERVICO',
            ativo=True
        )
        lanc2 = LancamentoFinanceiro(
            tipo='receita',
            descricao='OS 002 - Parcela 2/3',
            valor=Decimal('100.00'),
            data_lancamento=date(2025, 1, 10),
            data_vencimento=date(2025, 2, 10),
            status='pendente',
            ordem_servico_id=os.id,
            ordem_servico_parcela_id=p2.id,
            numero_parcela='2/3',
            origem='ORDEM_SERVICO',
            ativo=True
        )
        lanc3 = LancamentoFinanceiro(
            tipo='receita',
            descricao='OS 002 - Parcela 3/3',
            valor=Decimal('100.00'),
            data_lancamento=date(2025, 1, 10),
            data_vencimento=date(2025, 3, 10),
            status='pendente',
            ordem_servico_id=os.id,
            ordem_servico_parcela_id=p3.id,
            numero_parcela='3/3',
            origem='ORDEM_SERVICO',
            ativo=True
        )
        db.session.add_all([lanc1, lanc2, lanc3])
        db.session.commit()

        # Converter para views
        views = [montar_registro_exibicao(l) for l in [lanc1, lanc2, lanc3]]

        # Cada parcela deve ter chave diferente
        chaves = [v.chave_ocorrencia_confiavel for v in views]
        assert len(set(chaves)) == 3, f"Esperado 3 chaves únicas, obtido {len(set(chaves))}"

        # Deduplicar - todas devem permanecer
        deduplicados = _deduplicar_ocorrencias_confiaveis(views)
        assert len(deduplicados) == 3, f"Esperado 3 parcelas, obtido {len(deduplicados)}"


def test_04_os_cancelada_nao_aparece():
    """Regra 8: Lançamentos de OS cancelada não devem aparecer."""
    app = _setup_app()
    with app.app_context():
        # Criar cliente e OS cancelada
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
            titulo='Teste Cancelada',
            cliente_id=cliente.id,
            status='cancelada',  # OS cancelada
            ativo=True
        )
        db.session.add(os)
        db.session.flush()

        # Lançamento vinculado à OS cancelada
        lanc = LancamentoFinanceiro(
            tipo='receita',
            descricao='OS 003',
            valor=Decimal('100.00'),
            data_lancamento=date(2025, 1, 10),
            data_vencimento=date(2025, 1, 10),
            status='pendente',
            ordem_servico_id=os.id,
            origem='ORDEM_SERVICO',
            ativo=True
        )
        db.session.add(lanc)
        db.session.commit()

        # Tentar montar view - deve retornar None
        view = montar_registro_exibicao(lanc)
        assert view is None, "Lançamento de OS cancelada não deveria aparecer"


def test_05_cliente_diferentes_valor_igual_nao_deduplica():
    """Regra 9: Clientes diferentes com mesmo valor permanecem independentes."""
    app = _setup_app()
    with app.app_context():
        # Criar dois clientes
        cliente1 = Cliente(
            nome='Cliente A',
            cpf_cnpj='11111111111',
            telefone='11999999999',
            email='a@teste.com',
            ativo=True
        )
        cliente2 = Cliente(
            nome='Cliente B',
            cpf_cnpj='22222222222',
            telefone='11888888888',
            email='b@teste.com',
            ativo=True
        )
        db.session.add_all([cliente1, cliente2])
        db.session.commit()

        # Dois lançamentos mesmo valor, clientes diferentes, sem chave
        lanc1 = LancamentoFinanceiro(
            tipo='receita',
            descricao='Serviço A',
            valor=Decimal('150.00'),
            data_lancamento=date(2025, 1, 10),
            status='pendente',
            cliente_id=cliente1.id,
            origem='MANUAL',
            ativo=True
        )
        lanc2 = LancamentoFinanceiro(
            tipo='receita',
            descricao='Serviço B',
            valor=Decimal('150.00'),
            data_lancamento=date(2025, 1, 10),
            status='pendente',
            cliente_id=cliente2.id,
            origem='MANUAL',
            ativo=True
        )
        db.session.add_all([lanc1, lanc2])
        db.session.commit()

        # Carregar todos
        registros = carregar_registros_financeiros(date(2025, 1, 1), date(2025, 1, 31))
        assert len(registros) == 2, f"Esperado 2 lançamentos independentes, obtido {len(registros)}"


def test_06_identidade_usa_ordem_servico_parcela_id():
    """Valida identidade os_parcela:{id} com vínculo persistente."""
    app = _setup_app()
    with app.app_context():
        cliente = Cliente(
            nome='Cliente Teste',
            cpf_cnpj='33333333333',
            telefone='11999999999',
            email='identidade@teste.com',
            ativo=True,
        )
        db.session.add(cliente)
        db.session.flush()

        os = OrdemServico(numero='OS-2025-006', titulo='Identidade', cliente_id=cliente.id, status='concluida', ativo=True)
        db.session.add(os)
        db.session.flush()

        parcela = OrdemServicoParcela(
            ordem_servico_id=os.id,
            numero_parcela=1,
            data_vencimento=date(2025, 1, 10),
            valor=Decimal('120.00'),
        )
        db.session.add(parcela)
        db.session.flush()

        lanc = LancamentoFinanceiro(
            tipo='receita',
            descricao='OS 006',
            valor=Decimal('120.00'),
            data_lancamento=date(2025, 1, 10),
            status='pendente',
            ordem_servico_id=os.id,
            ordem_servico_parcela_id=parcela.id,
            numero_parcela='1/1',
            origem='ORDEM_SERVICO',
            ativo=True,
        )
        db.session.add(lanc)
        db.session.commit()

        view = montar_registro_exibicao(lanc)
        assert view.os_parcela_id == parcela.id
        assert view.chave_ocorrencia_confiavel == f'os_parcela:{parcela.id}'


def test_07_mudanca_texto_numero_parcela_nao_muda_identidade():
    """Troca de texto 1/12 para 1/10 não altera identidade persistente."""
    app = _setup_app()
    with app.app_context():
        cliente = Cliente(
            nome='Cliente Teste',
            cpf_cnpj='44444444444',
            telefone='11999999999',
            email='texto@teste.com',
            ativo=True,
        )
        db.session.add(cliente)
        db.session.flush()

        os = OrdemServico(numero='OS-2025-007', titulo='Texto Parcela', cliente_id=cliente.id, status='concluida', ativo=True)
        db.session.add(os)
        db.session.flush()

        parcela = OrdemServicoParcela(
            ordem_servico_id=os.id,
            numero_parcela=1,
            data_vencimento=date(2025, 1, 10),
            valor=Decimal('80.00'),
        )
        db.session.add(parcela)
        db.session.flush()

        lanc = LancamentoFinanceiro(
            tipo='receita',
            descricao='OS 007',
            valor=Decimal('80.00'),
            data_lancamento=date(2025, 1, 10),
            status='pendente',
            ordem_servico_id=os.id,
            ordem_servico_parcela_id=parcela.id,
            numero_parcela='1/12',
            origem='ORDEM_SERVICO',
            ativo=True,
        )
        db.session.add(lanc)
        db.session.commit()

        chave_antes = montar_registro_exibicao(lanc).chave_ocorrencia_confiavel
        lanc.numero_parcela = '1/10'
        db.session.commit()
        chave_depois = montar_registro_exibicao(lanc).chave_ocorrencia_confiavel

        assert chave_antes == chave_depois == f'os_parcela:{parcela.id}'


def test_08_mesmo_cliente_mesmo_valor_em_os_diferentes_permanece_separado():
    """Duas OS com mesmo cliente e valor não podem ser absorvidas entre si."""
    app = _setup_app()
    with app.app_context():
        cliente = Cliente(
            nome='Cliente Único',
            cpf_cnpj='55555555555',
            telefone='11999999999',
            email='mesmo@teste.com',
            ativo=True,
        )
        db.session.add(cliente)
        db.session.flush()

        os_a = OrdemServico(numero='OS-2025-008A', titulo='A', cliente_id=cliente.id, status='concluida', ativo=True)
        os_b = OrdemServico(numero='OS-2025-008B', titulo='B', cliente_id=cliente.id, status='concluida', ativo=True)
        db.session.add_all([os_a, os_b])
        db.session.flush()

        pa = OrdemServicoParcela(ordem_servico_id=os_a.id, numero_parcela=1, data_vencimento=date(2025, 1, 10), valor=Decimal('200.00'))
        pb = OrdemServicoParcela(ordem_servico_id=os_b.id, numero_parcela=1, data_vencimento=date(2025, 1, 10), valor=Decimal('200.00'))
        db.session.add_all([pa, pb])
        db.session.flush()

        la = LancamentoFinanceiro(tipo='receita', descricao='OS A', valor=Decimal('200.00'), data_lancamento=date(2025, 1, 10), status='pendente', ordem_servico_id=os_a.id, ordem_servico_parcela_id=pa.id, origem='ORDEM_SERVICO', ativo=True)
        lb = LancamentoFinanceiro(tipo='receita', descricao='OS B', valor=Decimal('200.00'), data_lancamento=date(2025, 1, 10), status='pendente', ordem_servico_id=os_b.id, ordem_servico_parcela_id=pb.id, origem='ORDEM_SERVICO', ativo=True)
        db.session.add_all([la, lb])
        db.session.commit()

        views = [montar_registro_exibicao(la), montar_registro_exibicao(lb)]
        dedup = _deduplicar_ocorrencias_confiaveis(views)
        assert len(dedup) == 2


def test_09_identidade_independe_de_texto_codigo_cliente_valor():
    """Com os_parcela_id preenchido, identidade não depende de campos descritivos/monetários."""
    app = _setup_app()
    with app.app_context():
        cliente_a = Cliente(
            nome='Cliente A',
            cpf_cnpj='77777777777',
            telefone='11999999999',
            email='a-chave@teste.com',
            ativo=True,
        )
        cliente_b = Cliente(
            nome='Cliente B',
            cpf_cnpj='88888888888',
            telefone='11888888888',
            email='b-chave@teste.com',
            ativo=True,
        )
        db.session.add_all([cliente_a, cliente_b])
        db.session.flush()

        os_ref = OrdemServico(numero='OS-2025-009', titulo='Identidade Dura', cliente_id=cliente_a.id, status='concluida', ativo=True)
        db.session.add(os_ref)
        db.session.flush()

        parcela = OrdemServicoParcela(
            ordem_servico_id=os_ref.id,
            numero_parcela=1,
            data_vencimento=date(2025, 1, 10),
            valor=Decimal('500.00'),
        )
        db.session.add(parcela)
        db.session.flush()

        lanc = LancamentoFinanceiro(
            tipo='receita',
            descricao='Descricao original',
            valor=Decimal('500.00'),
            data_lancamento=date(2025, 1, 10),
            status='pendente',
            ordem_servico_id=os_ref.id,
            ordem_servico_parcela_id=parcela.id,
            numero_parcela='1/12',
            origem='ORDEM_SERVICO',
            cliente_id=cliente_a.id,
            ativo=True,
        )
        db.session.add(lanc)
        db.session.commit()

        chave_antes = montar_registro_exibicao(lanc).chave_ocorrencia_confiavel

        lanc.descricao = 'Descricao alterada radicalmente'
        lanc.numero_parcela = '1/2'
        lanc.valor = Decimal('9999.99')
        lanc.cliente_id = cliente_b.id
        os_ref.numero = 'OS-2025-009-ALTERADA'
        db.session.commit()

        chave_depois = montar_registro_exibicao(lanc).chave_ocorrencia_confiavel
        assert chave_antes == chave_depois == f'os_parcela:{parcela.id}'


def test_10_os_finalizada_fica_pendente_no_financeiro():
    """OS finalizada permanece pendente no financeiro."""
    app = _setup_app()
    with app.app_context():
        cliente = Cliente(
            nome='Cliente OS',
            cpf_cnpj='10101010101',
            telefone='11999999999',
            email='cliente.os@teste.com',
            ativo=True,
        )
        db.session.add(cliente)
        db.session.flush()

        ordem = OrdemServico(
            numero='OS-FIN-001',
            titulo='Teste OS Finalizada',
            cliente_id=cliente.id,
            status='finalizada',
            valor_total=Decimal('250.00'),
            data_abertura=date(2025, 1, 10),
            data_prevista=date(2025, 1, 20),
            ativo=True,
        )
        db.session.add(ordem)
        db.session.flush()

        lanc = LancamentoFinanceiro(
            descricao='Lancamento OS Finalizada',
            valor=Decimal('250.00'),
            tipo='conta_receber',
            status='pendente',
            data_lancamento=date(2025, 1, 10),
            data_vencimento=date(2025, 1, 20),
            ordem_servico_id=ordem.id,
            origem='ORDEM_SERVICO',
            ativo=True,
        )
        db.session.add(lanc)
        db.session.commit()

        atualizar_status_financeiro_ordem(ordem)
        recarregado = db.session.get(LancamentoFinanceiro, lanc.id)

        assert recarregado.status == 'pendente'
        assert recarregado.data_pagamento is None


def test_11_tipo_case_insensitive_na_baixa():
    """Reconhecimento de tipo com variacao de caixa."""
    app = _setup_app()
    with app.app_context():
        receita = LancamentoFinanceiro(
            descricao='Receita caixa alta',
            valor=Decimal('100.00'),
            tipo='RECEITA',
            status='pendente',
            data_lancamento=date(2025, 1, 10),
            ativo=True,
        )
        despesa = LancamentoFinanceiro(
            descricao='Despesa caixa mista',
            valor=Decimal('40.00'),
            tipo='Conta_Pagar',
            status='pendente',
            data_lancamento=date(2025, 1, 10),
            ativo=True,
        )
        db.session.add_all([receita, despesa])
        db.session.commit()

        receita.marcar_como_pago(date(2025, 1, 11), usuario='tester')
        despesa.marcar_como_pago(date(2025, 1, 11), usuario='tester')

        assert receita.status == 'recebido'
        assert despesa.status == 'pago'


def test_12_pago_sem_data_permanece_inconsistente():
    """Pago sem data_pagamento segue como inconsistencia."""
    app = _setup_app()
    with app.app_context():
        lanc = LancamentoFinanceiro(
            descricao='Inconsistente sem data',
            valor=Decimal('80.00'),
            tipo='receita',
            status='recebido',
            data_lancamento=date(2025, 1, 10),
            data_vencimento=date(2025, 1, 10),
            data_pagamento=None,
            ativo=True,
        )
        db.session.add(lanc)
        db.session.commit()

        resumo = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert resumo.lancamentos_pagos_sem_data_qtd == 1
        assert resumo.lancamentos_pagos_sem_data_valor == Decimal('80.00')
        assert resumo.receitas_realizadas == Decimal('0')


def test_13_segunda_baixa_idempotente_nao_duplica_movimento_conta():
    """Segunda baixa nao altera saldo nem data da primeira baixa."""
    app = _setup_app()
    with app.app_context():
        conta = ContaBancaria(
            nome='Conta Teste',
            tipo='conta_corrente',
            saldo_inicial=Decimal('100.00'),
            saldo_atual=Decimal('100.00'),
            ativa=True,
            ativo=True,
        )
        db.session.add(conta)
        db.session.flush()

        lanc = LancamentoFinanceiro(
            descricao='Receita com conta',
            valor=Decimal('50.00'),
            tipo='receita',
            status='pendente',
            data_lancamento=date(2025, 1, 10),
            conta_bancaria_id=conta.id,
            ativo=True,
        )
        db.session.add(lanc)
        db.session.commit()

        primeira_data = date(2025, 1, 12)
        lanc.marcar_como_pago(primeira_data, usuario='auditor')
        saldo_apos_primeira = db.session.get(ContaBancaria, conta.id).saldo_atual

        lanc.marcar_como_pago(date(2025, 1, 20), usuario='auditor')
        conta_final = db.session.get(ContaBancaria, conta.id)
        lanc_final = db.session.get(LancamentoFinanceiro, lanc.id)

        assert saldo_apos_primeira == Decimal('150.00')
        assert conta_final.saldo_atual == Decimal('150.00')
        assert lanc_final.data_pagamento == primeira_data


def test_14_baixa_registra_historico_com_usuario():
    """Historico de baixa deve persistir usuario executor."""
    app = _setup_app()
    with app.app_context():
        lanc = LancamentoFinanceiro(
            descricao='Baixa com historico',
            valor=Decimal('90.00'),
            tipo='despesa',
            status='pendente',
            data_lancamento=date(2025, 1, 10),
            ativo=True,
        )
        db.session.add(lanc)
        db.session.commit()

        lanc.marcar_como_pago(date(2025, 1, 13), usuario='usuario.teste')

        hist = HistoricoFinanceiro.query.filter_by(lancamento_id=lanc.id).all()
        assert len(hist) == 1
        assert hist[0].acao == 'pagamento'
        assert hist[0].usuario == 'usuario.teste'


def test_15_dashboard_usa_totais_do_servico_central():
    """Totais do dashboard devem bater com resumo central."""
    app = _setup_app()
    with app.app_context():
        hoje = date.today()
        db.session.add(
            LancamentoFinanceiro(
                descricao='Receita realizada',
                valor=Decimal('120.00'),
                tipo='receita',
                status='recebido',
                data_lancamento=hoje,
                data_vencimento=hoje,
                data_pagamento=hoje,
                ativo=True,
            )
        )
        db.session.add(
            LancamentoFinanceiro(
                descricao='Despesa realizada',
                valor=Decimal('30.00'),
                tipo='despesa',
                status='pago',
                data_lancamento=hoje,
                data_vencimento=hoje,
                data_pagamento=hoje,
                ativo=True,
            )
        )
        db.session.commit()

        inicio = hoje.replace(day=1)
        resumo = resumir_financeiro_periodo(inicio, hoje)
        metricas = calcular_metricas_dashboard()

        assert metricas['total_receitas_mes'] == float(resumo.receitas_realizadas)
        assert metricas['total_despesas_mes'] == float(resumo.despesas_realizadas)
        assert metricas['saldo_mes'] == float(resumo.resultado_realizado)


def test_16_pendencias_respeitam_data_vencimento_no_periodo():
    """AR/AP devem considerar data_vencimento no periodo."""
    app = _setup_app()
    with app.app_context():
        db.session.add(
            LancamentoFinanceiro(
                descricao='Receber fevereiro',
                valor=Decimal('200.00'),
                tipo='conta_receber',
                status='pendente',
                data_lancamento=date(2025, 1, 5),
                data_vencimento=date(2025, 2, 10),
                ativo=True,
            )
        )
        db.session.add(
            LancamentoFinanceiro(
                descricao='Pagar janeiro',
                valor=Decimal('70.00'),
                tipo='conta_pagar',
                status='pendente',
                data_lancamento=date(2025, 1, 5),
                data_vencimento=date(2025, 1, 20),
                ativo=True,
            )
        )
        db.session.commit()

        jan = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        fev = resumir_financeiro_periodo(date(2025, 2, 1), date(2025, 2, 28))

        assert jan.contas_a_receber_pendentes == Decimal('0')
        assert jan.contas_a_pagar_pendentes == Decimal('70.00')
        assert fev.contas_a_receber_pendentes == Decimal('200.00')
        assert fev.contas_a_pagar_pendentes == Decimal('0')


def main():
    """Executa todos os testes."""
    print("\n" + "="*80)
    print("TESTES DE CONSOLIDAÇÃO E DEDUPLICAÇÃO FINANCEIRA")
    print("Validando Regras 8-11 de Reconciliação Funcional")
    print("="*80 + "\n")

    tests = [
        ("Regra 9: Lançamentos sem chave não deduplica", test_01_lancamentos_sem_chave_nao_deduplica),
        ("Regra 8/11: Lançamentos mesma OS deduplica por chave", test_02_os_com_chave_deduplica),
        ("Regra 10: Parcelas legítimas preservadas", test_03_parcelas_legitimas_preservadas),
        ("Regra 8: OS cancelada não aparece", test_04_os_cancelada_nao_aparece),
        ("Regra 9: Clientes diferentes não deduplica", test_05_cliente_diferentes_valor_igual_nao_deduplica),
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
