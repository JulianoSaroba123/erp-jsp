from datetime import date
from decimal import Decimal

from aplicacao import create_app
from aplicacao.extensoes import db
from aplicacao.financeiro.financeiro_model import LancamentoFinanceiro
from aplicacao.financeiro.lancamento_os_model import LancamentoFinanceiroOS
from aplicacao.financeiro.indicadores_service import carregar_registros_financeiros, resumir_financeiro_periodo
from aplicacao.cliente.cliente_model import Cliente
from aplicacao.ordem_servico.os_model import OrdemServico


def _novo_tradicional(tipo, status, valor, data_lanc, data_pag=None):
    return LancamentoFinanceiro(
        tipo=tipo,
        categoria='Teste',
        descricao='Lancamento teste',
        valor=float(valor),
        data=data_lanc,
        data_pagamento=data_pag,
        forma_pagamento='PIX',
        status=status,
    )


def _novo_os(tipo, status, valor, data_prev, os_status='Concluida', data_pag=None):
    lanc = LancamentoFinanceiroOS(
        os_id=1,
        valor=Decimal(str(valor)),
        descricao='Lancamento OS teste',
        status=status,
        data_vencimento=data_prev,
        data_pagamento=data_pag,
        forma_pagamento='PIX',
    )
    lanc.os_status = os_status
    return lanc


def _setup_app():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
    return app


def _run(name, fn):
    fn()
    print(f'[OK] {name}')


def test_01_receita_paga_entra_realizado():
    app = _setup_app()
    with app.app_context():
        db.session.add(_novo_tradicional('Receita', 'Pago', 100, date(2025, 1, 10), date(2025, 1, 10)))
        db.session.commit()
        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.receita_realizada == Decimal('100')
        assert r.saldo_realizado == Decimal('100')


def test_02_despesa_paga_abate_realizado():
    app = _setup_app()
    with app.app_context():
        db.session.add(_novo_tradicional('Despesa', 'Pago', 40, date(2025, 1, 10), date(2025, 1, 10)))
        db.session.commit()
        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.despesa_realizada == Decimal('40')
        assert r.saldo_realizado == Decimal('-40')


def test_03_pendente_nao_entra_realizado():
    app = _setup_app()
    with app.app_context():
        db.session.add(_novo_tradicional('Receita', 'Pendente', 120, date(2025, 1, 10)))
        db.session.commit()
        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.receita_realizada == Decimal('0')


def test_04_receita_pendente_vai_receber():
    app = _setup_app()
    with app.app_context():
        db.session.add(_novo_tradicional('Receita', 'Pendente', 120, date(2025, 1, 10)))
        db.session.commit()
        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.a_receber_pendente == Decimal('120')


def test_05_despesa_pendente_vai_pagar():
    app = _setup_app()
    with app.app_context():
        db.session.add(_novo_tradicional('Despesa', 'Pendente', 33, date(2025, 1, 10)))
        db.session.commit()
        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.a_pagar_pendente == Decimal('33')


def test_06_projecao_saldo_corresponde_formula():
    app = _setup_app()
    with app.app_context():
        db.session.add(_novo_tradicional('Receita', 'Pago', 100, date(2025, 1, 10), date(2025, 1, 10)))
        db.session.add(_novo_tradicional('Despesa', 'Pendente', 40, date(2025, 1, 11)))
        db.session.add(_novo_tradicional('Receita', 'Pendente', 30, date(2025, 1, 12)))
        db.session.commit()
        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.saldo_projetado == Decimal('90')


def test_07_pago_sem_data_pagamento_inconsistencia():
    app = _setup_app()
    with app.app_context():
        db.session.add(_novo_tradicional('Receita', 'Pago', 100, date(2025, 1, 10), None))
        db.session.commit()
        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.total_inconsistencias == 1


def test_08_pago_com_data_pagamento_sem_inconsistencia():
    app = _setup_app()
    with app.app_context():
        db.session.add(_novo_tradicional('Receita', 'Pago', 100, date(2025, 1, 10), date(2025, 1, 11)))
        db.session.commit()
        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.total_inconsistencias == 0


def test_09_variacao_caixa_realizado_periodo_vazio_zero():
    app = _setup_app()
    with app.app_context():
        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.saldo_realizado == Decimal('0')


def test_10_variantes_status_pago_funcionam():
    app = _setup_app()
    with app.app_context():
        db.session.add(_novo_tradicional('Receita', 'PAGO', 55, date(2025, 1, 10), date(2025, 1, 10)))
        db.session.add(_novo_tradicional('Receita', 'Pago', 45, date(2025, 1, 10), date(2025, 1, 10)))
        db.session.commit()
        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.receita_realizada == Decimal('100')


def test_11_variantes_tipo_receita_despesa_funcionam():
    app = _setup_app()
    with app.app_context():
        db.session.add(_novo_tradicional('RECEITA', 'Pago', 90, date(2025, 1, 10), date(2025, 1, 10)))
        db.session.add(_novo_tradicional('despesa', 'Pago', 10, date(2025, 1, 10), date(2025, 1, 10)))
        db.session.commit()
        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.saldo_realizado == Decimal('80')


def test_12_os_concluida_pendente_conta_pendente():
    app = _setup_app()
    with app.app_context():
        db.session.add(_novo_os('Receita', 'Pendente', 200, date(2025, 1, 20), 'Concluida'))
        db.session.commit()
        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.a_receber_pendente == Decimal('200')


def test_13_os_concluida_paga_com_data_entra_realizado():
    app = _setup_app()
    with app.app_context():
        db.session.add(_novo_os('Receita', 'Pago', 200, date(2025, 1, 20), 'Concluida', date(2025, 1, 22)))
        db.session.commit()
        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.receita_realizada == Decimal('200')


def test_14_os_cancelada_nao_aparece_nos_totais():
    app = _setup_app()
    with app.app_context():
        cliente = Cliente(nome='Cliente Teste')
        db.session.add(cliente)
        db.session.flush()
        os_cancelada = OrdemServico(codigo='OS9999', cliente_id=cliente.id, status='Cancelada', ativo=False)
        db.session.add(os_cancelada)
        db.session.flush()

        lanc = LancamentoFinanceiroOS(
            os_id=os_cancelada.id,
            valor=Decimal('999'),
            descricao='Lancamento cancelado',
            status='Pago',
            data_vencimento=date(2025, 1, 20),
            data_pagamento=date(2025, 1, 22),
            forma_pagamento='PIX',
        )
        db.session.add(lanc)
        db.session.commit()
        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.receita_realizada == Decimal('0')


def test_15_timeline_prioriza_data_pagamento_quando_existe():
    app = _setup_app()
    with app.app_context():
        db.session.add(_novo_tradicional('Receita', 'Pago', 100, date(2025, 1, 5), date(2025, 1, 20)))
        db.session.commit()
        registros = carregar_registros_financeiros(date(2025, 1, 1), date(2025, 1, 31))
        assert len(registros) == 1
        assert registros[0].data_referencia == date(2025, 1, 20)


def test_16_registro_lista_tem_flags_esperadas():
    app = _setup_app()
    with app.app_context():
        db.session.add(_novo_tradicional('Receita', 'Pendente', 100, date(2025, 1, 5)))
        db.session.commit()
        registros = carregar_registros_financeiros(date(2025, 1, 1), date(2025, 1, 31))
        assert registros[0].tipo == 'Receita'
        assert registros[0].status == 'Pendente'


def test_17_dashboard_zero_quando_sem_movimento():
    app = _setup_app()
    with app.app_context():
        r = resumir_financeiro_periodo(date(2026, 1, 1), date(2026, 1, 31))
        assert r.receita_realizada == Decimal('0')
        assert r.despesa_realizada == Decimal('0')
        assert r.a_receber_pendente == Decimal('0')
        assert r.a_pagar_pendente == Decimal('0')


def test_18_soma_multiplos_lancamentos_mistos():
    app = _setup_app()
    with app.app_context():
        db.session.add(_novo_tradicional('Receita', 'Pago', 500, date(2025, 1, 1), date(2025, 1, 2)))
        db.session.add(_novo_tradicional('Despesa', 'Pago', 150, date(2025, 1, 3), date(2025, 1, 4)))
        db.session.add(_novo_tradicional('Receita', 'Pendente', 200, date(2025, 1, 5)))
        db.session.add(_novo_tradicional('Despesa', 'Pendente', 50, date(2025, 1, 6)))
        db.session.commit()
        r = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 1, 31))
        assert r.receita_realizada == Decimal('500')
        assert r.despesa_realizada == Decimal('150')
        assert r.saldo_realizado == Decimal('350')
        assert r.a_receber_pendente == Decimal('200')
        assert r.a_pagar_pendente == Decimal('50')
        assert r.saldo_projetado == Decimal('500')


if __name__ == '__main__':
    testes = [
        ('01 receita paga realizado', test_01_receita_paga_entra_realizado),
        ('02 despesa paga realizado', test_02_despesa_paga_abate_realizado),
        ('03 pendente fora realizado', test_03_pendente_nao_entra_realizado),
        ('04 receita pendente a receber', test_04_receita_pendente_vai_receber),
        ('05 despesa pendente a pagar', test_05_despesa_pendente_vai_pagar),
        ('06 formula saldo projetado', test_06_projecao_saldo_corresponde_formula),
        ('07 inconsistencia pago sem data', test_07_pago_sem_data_pagamento_inconsistencia),
        ('08 pago com data consistente', test_08_pago_com_data_pagamento_sem_inconsistencia),
        ('09 periodo vazio', test_09_variacao_caixa_realizado_periodo_vazio_zero),
        ('10 variantes status pago', test_10_variantes_status_pago_funcionam),
        ('11 variantes tipo', test_11_variantes_tipo_receita_despesa_funcionam),
        ('12 OS concluida pendente', test_12_os_concluida_pendente_conta_pendente),
        ('13 OS concluida paga com data', test_13_os_concluida_paga_com_data_entra_realizado),
        ('14 OS cancelada excluida', test_14_os_cancelada_nao_aparece_nos_totais),
        ('15 timeline data referencia', test_15_timeline_prioriza_data_pagamento_quando_existe),
        ('16 flags da lista', test_16_registro_lista_tem_flags_esperadas),
        ('17 dashboard sem movimento', test_17_dashboard_zero_quando_sem_movimento),
        ('18 misto completo', test_18_soma_multiplos_lancamentos_mistos),
    ]

    for nome, fn in testes:
        _run(nome, fn)

    print('TODOS OS 18 TESTES PASSARAM')
