import os
import tempfile
from contextlib import contextmanager
from datetime import date
from decimal import Decimal

from flask import template_rendered

from aplicacao import create_app
from aplicacao.extensoes import db
from aplicacao.cliente.cliente_model import Cliente
from aplicacao.ordem_servico.os_model import OrdemServico
from aplicacao.ordem_servico.ordem_servico_routes import integrar_financeiro_automatico
from aplicacao.financeiro.financeiro_model import LancamentoFinanceiro
from aplicacao.financeiro.lancamento_os_model import LancamentoFinanceiroOS
from aplicacao.financeiro.indicadores_service import (
    periodo_mes_atual,
    resumir_financeiro_periodo,
    resumir_registros_financeiros,
    carregar_registros_financeiros,
)


def _assert(cond, msg):
    if not cond:
        raise AssertionError(msg)


def _setup_app_temp_db():
    temp_dir = tempfile.mkdtemp(prefix="homolog_fin_consolidacao_")
    db_path = os.path.join(temp_dir, "consolidacao.db")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.replace('\\', '/')}"

    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
    return app


@contextmanager
def _captura_templates(app):
    gravados = []

    def registrar(sender, template, context, **extra):
        gravados.append((template, context))

    template_rendered.connect(registrar, app)
    try:
        yield gravados
    finally:
        template_rendered.disconnect(registrar, app)


def _integrar_com_request_context(app, os_obj):
    with app.test_request_context(f"/ordens/{os_obj.id}/editar", method="POST"):
        integrar_financeiro_automatico(os_obj)


def _nova_os(cliente_id, codigo, valor, status="Concluída", parcelas_json=None):
    if parcelas_json is None:
        parcelas_json = '[{"valor": "100.00", "data_vencimento": "2025-02-10"}]'
    os_obj = OrdemServico(
        codigo=codigo,
        cliente_id=cliente_id,
        status=status,
        ativo=True,
        valor_total=float(valor),
        forma_pagamento="pix",
        condicao_pagamento="avista",
        qtd_parcelas=1,
        status_pagamento="Pendente",
        parcelas_json=parcelas_json,
    )
    db.session.add(os_obj)
    db.session.commit()
    return os_obj


def test_01_fluxo_atual_gera_uma_fonte():
    app = _setup_app_temp_db()
    with app.app_context():
        cliente = Cliente(nome="Cliente A")
        db.session.add(cliente)
        db.session.commit()

        os1 = _nova_os(cliente.id, "OS9101", Decimal("100.00"))
        _integrar_com_request_context(app, os1)

        qtd_os = LancamentoFinanceiroOS.query.filter_by(os_id=os1.id).count()
        qtd_legado = LancamentoFinanceiro.query.filter_by(categoria=f"Ordem de Serviço {os1.codigo}").count()
        _assert(qtd_os + qtd_legado == 1, "T1: OS concluida deve gerar exatamente uma representacao financeira")


def test_02_repeticao_nao_cria_segunda_fonte():
    app = _setup_app_temp_db()
    with app.app_context():
        cliente = Cliente(nome="Cliente B")
        db.session.add(cliente)
        db.session.commit()

        os1 = _nova_os(cliente.id, "OS9102", Decimal("100.00"))
        _integrar_com_request_context(app, os1)
        _integrar_com_request_context(app, os1)

        os1.contato = "edicao cadastro"
        db.session.commit()
        _integrar_com_request_context(app, os1)

        qtd_os = LancamentoFinanceiroOS.query.filter_by(os_id=os1.id).count()
        qtd_legado = LancamentoFinanceiro.query.filter_by(categoria=f"Ordem de Serviço {os1.codigo}").count()
        _assert(qtd_os + qtd_legado == 1, "T2: repeticao de sincronizacao/edicao nao pode gerar segunda fonte")


def test_03_legado_nao_gera_duplicado_na_outra_fonte():
    app = _setup_app_temp_db()
    with app.app_context():
        cliente = Cliente(nome="Cliente C")
        db.session.add(cliente)
        db.session.commit()

        os1 = _nova_os(cliente.id, "OS9103", Decimal("100.00"))

        legado = LancamentoFinanceiro(
            tipo="Receita",
            categoria=f"Ordem de Serviço {os1.codigo}",
            descricao=f"Receita da OS {os1.codigo}",
            valor=100.0,
            data=date(2025, 2, 1),
            status="Pendente",
            observacoes=f"Lançamento automático pendente gerado da OS {os1.codigo}",
        )
        db.session.add(legado)
        db.session.commit()

        _integrar_com_request_context(app, os1)

        qtd_os = LancamentoFinanceiroOS.query.filter_by(os_id=os1.id).count()
        qtd_legado = LancamentoFinanceiro.query.filter_by(categoria=f"Ordem de Serviço {os1.codigo}").count()
        _assert(qtd_os == 0, "T3: com legado explicito, nao deve criar fonte OS nova")
        _assert(qtd_legado == 1, "T3: registro legado deve ser preservado")


def test_04_indicador_nao_dobra_quando_duplicidade_confiavel():
    app = _setup_app_temp_db()
    with app.app_context():
        cliente = Cliente(nome="Cliente D")
        db.session.add(cliente)
        db.session.commit()

        os1 = _nova_os(cliente.id, "OS9104", Decimal("100.00"))

        legado = LancamentoFinanceiro(
            tipo="Receita",
            categoria=f"Ordem de Serviço {os1.codigo}",
            descricao=f"Receita da OS {os1.codigo}",
            valor=100.0,
            data=date(2025, 3, 1),
            data_pagamento=date(2025, 3, 15),
            status="Pago",
            observacoes=f"Lançamento automático pendente gerado da OS {os1.codigo}",
        )
        db.session.add(legado)

        os_fin = LancamentoFinanceiroOS(
            os_id=os1.id,
            descricao=f"Parcela 1/1 - OS {os1.codigo} - Cliente",
            valor=Decimal("100.00"),
            data_vencimento=date(2025, 2, 10),
            data_pagamento=date(2025, 3, 15),
            forma_pagamento="pix",
            status="Pago",
            parcela=1,
            total_parcelas=1,
        )
        db.session.add(os_fin)
        db.session.commit()

        resumo = resumir_financeiro_periodo(date(2025, 3, 1), date(2025, 3, 31))
        _assert(resumo.receita_realizada == Decimal("100.00"), "T4: duplicidade confiavel nao deve dobrar realizado")


def test_05_os_distintas_mesmo_cliente_valor_contam_separado():
    app = _setup_app_temp_db()
    with app.app_context():
        cliente = Cliente(nome="Cliente E")
        db.session.add(cliente)
        db.session.commit()

        os1 = _nova_os(cliente.id, "OS9105", Decimal("100.00"))
        os2 = _nova_os(cliente.id, "OS9106", Decimal("100.00"))
        _integrar_com_request_context(app, os1)
        _integrar_com_request_context(app, os2)

        resumo = resumir_financeiro_periodo(date(2025, 2, 1), date(2025, 2, 28))
        _assert(resumo.contas_a_receber_pendentes == Decimal("200.00"), "T5: duas OS legitimas nao podem ser deduplicadas")


def test_06_parcelas_legitimas_nao_sao_eliminadas():
    app = _setup_app_temp_db()
    with app.app_context():
        cliente = Cliente(nome="Cliente F")
        db.session.add(cliente)
        db.session.commit()

        os1 = _nova_os(cliente.id, "OS9107", Decimal("200.00"), parcelas_json='[{"valor": "100.00", "data_vencimento": "2025-02-10"}, {"valor": "100.00", "data_vencimento": "2025-03-10"}]')
        _integrar_com_request_context(app, os1)

        registros = LancamentoFinanceiroOS.query.filter_by(os_id=os1.id).order_by(LancamentoFinanceiroOS.parcela.asc()).all()
        _assert(len(registros) == 2, "T6: parcelamento legitimo deve manter duas parcelas")

        resumo = resumir_financeiro_periodo(date(2025, 1, 1), date(2025, 3, 31))
        _assert(resumo.contas_a_receber_pendentes == Decimal("200.00"), "T6: parcelas legitimas devem somar integralmente")


def test_07_pago_sem_data_fica_fora_realizado_e_inconsistente():
    app = _setup_app_temp_db()
    with app.app_context():
        cliente = Cliente(nome="Cliente G")
        db.session.add(cliente)
        db.session.commit()

        os1 = _nova_os(cliente.id, "OS9108", Decimal("100.00"))
        lanc = LancamentoFinanceiroOS(
            os_id=os1.id,
            descricao="Parcela 1/1",
            valor=Decimal("100.00"),
            data_vencimento=date(2025, 2, 10),
            data_pagamento=None,
            forma_pagamento="pix",
            status="Pago",
            parcela=1,
            total_parcelas=1,
        )
        db.session.add(lanc)
        db.session.commit()

        resumo = resumir_financeiro_periodo(date(2025, 2, 1), date(2025, 2, 28))
        _assert(resumo.receita_realizada == Decimal("0"), "T7: pago sem data nao entra no realizado")
        _assert(resumo.lancamentos_pagos_sem_data_qtd == 1, "T7: pago sem data deve gerar inconsistência")


def test_08_dashboard_principal_e_financeiro_mesmos_indicadores():
    app = _setup_app_temp_db()
    with app.app_context():
        cliente = Cliente(nome="Cliente H")
        db.session.add(cliente)
        db.session.commit()

        hoje = date.today()
        inicio_mes, fim_mes = periodo_mes_atual(hoje)

        lanc = LancamentoFinanceiro(
            tipo="Receita",
            categoria="Teste",
            descricao="Receita do mes",
            valor=150.0,
            data=inicio_mes,
            data_pagamento=inicio_mes,
            status="Pago",
        )
        db.session.add(lanc)
        db.session.commit()

        client = app.test_client()
        with _captura_templates(app) as renderizados:
            resposta = client.get('/financeiro/dashboard')
            _assert(resposta.status_code == 200, "T8: dashboard financeiro deve responder 200")

        contexto = None
        for tpl, ctx in renderizados:
            if tpl.name.endswith('financeiro/dashboard.html'):
                contexto = ctx
                break

        _assert(contexto is not None, "T8: contexto do dashboard financeiro nao capturado")
        _assert(contexto['receitas'] == contexto['receitas_realizadas_painel'], "T8: receitas painel e dashboard devem ser iguais")
        _assert(contexto['despesas'] == contexto['despesas_pagas_painel'], "T8: despesas painel e dashboard devem ser iguais")
        _assert(contexto['saldo'] == contexto['saldo_realizado_painel'], "T8: saldo painel e dashboard devem ser iguais")


def test_09_lista_usa_resumo_central_sem_formula_local():
    app = _setup_app_temp_db()
    with app.app_context():
        cliente = Cliente(nome="Cliente I")
        db.session.add(cliente)
        db.session.commit()

        os1 = _nova_os(cliente.id, "OS9109", Decimal("120.00"))
        _integrar_com_request_context(app, os1)

        registros = carregar_registros_financeiros(date(2025, 2, 1), date(2025, 2, 28))
        resumo = resumir_registros_financeiros(registros)

        client = app.test_client()
        with _captura_templates(app) as renderizados:
            resposta = client.get('/financeiro/?de=2025-02-01&ate=2025-02-28')
            _assert(resposta.status_code == 200, "T9: listagem financeira deve responder 200")

        contexto = None
        for tpl, ctx in renderizados:
            if tpl.name.endswith('financeiro/lista_financeiro.html'):
                contexto = ctx
                break

        _assert(contexto is not None, "T9: contexto da lista financeira nao capturado")
        _assert(contexto['contas_a_receber_pendentes'] == resumo['contas_a_receber_pendentes'], "T9: lista deve usar resumo central para pendencias")
        _assert(contexto['saldo'] == resumo['saldo'], "T9: lista deve usar resumo central para saldo")


if __name__ == '__main__':
    testes = [
        ('01 uma fonte', test_01_fluxo_atual_gera_uma_fonte),
        ('02 sem segunda fonte repeticao', test_02_repeticao_nao_cria_segunda_fonte),
        ('03 legado nao duplica', test_03_legado_nao_gera_duplicado_na_outra_fonte),
        ('04 indicador sem dupla contagem', test_04_indicador_nao_dobra_quando_duplicidade_confiavel),
        ('05 os distintas preservadas', test_05_os_distintas_mesmo_cliente_valor_contam_separado),
        ('06 parcelas legitimas preservadas', test_06_parcelas_legitimas_nao_sao_eliminadas),
        ('07 pago sem data inconsistencia', test_07_pago_sem_data_fica_fora_realizado_e_inconsistente),
        ('08 dashboards consistentes', test_08_dashboard_principal_e_financeiro_mesmos_indicadores),
        ('09 lista usa resumo central', test_09_lista_usa_resumo_central_sem_formula_local),
    ]

    for nome, fn in testes:
        fn()
        print(f'[OK] {nome}')

    print('TESTES_CONSOLIDACAO_FINANCEIRA_OK')
