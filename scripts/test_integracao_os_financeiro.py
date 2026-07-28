import json
import os
import tempfile
from datetime import date
from decimal import Decimal

from aplicacao import create_app
from aplicacao.extensoes import db
from aplicacao.cliente.cliente_model import Cliente
from aplicacao.ordem_servico.os_model import OrdemServico
from aplicacao.ordem_servico.ordem_servico_routes import integrar_financeiro_automatico
from aplicacao.financeiro.lancamento_os_model import LancamentoFinanceiroOS
from aplicacao.financeiro.indicadores_service import resumir_financeiro_periodo


VALOR_OS = Decimal("100.00")
VENCIMENTO_CONTROLADO = date(2025, 2, 10)
DATA_BAIXA_CONTROLADA = date(2025, 3, 15)


def _assert(cond, msg):
    if not cond:
        raise AssertionError(msg)


def _resumo(inicio, fim):
    return resumir_financeiro_periodo(inicio, fim)


def _contar_lancamentos_os(os_id):
    return LancamentoFinanceiroOS.query.filter_by(os_id=os_id).count()


def _obter_lancamento_os(os_id):
    return LancamentoFinanceiroOS.query.filter_by(os_id=os_id).one()


def _integrar_com_request_context(app, os_obj):
    with app.test_request_context(f"/ordens/{os_obj.id}/editar", method="POST"):
        integrar_financeiro_automatico(os_obj)


def _snapshot(app, os_obj, periodo_inicio, periodo_fim, rotulo):
    lanc = _obter_lancamento_os(os_obj.id)
    resumo = _resumo(periodo_inicio, periodo_fim)
    print(
        "[SNAPSHOT] "
        f"{rotulo} "
        f"os_id={os_obj.id} "
        f"lanc_id={lanc.id} "
        f"qtd_lanc={_contar_lancamentos_os(os_obj.id)} "
        f"status={lanc.status} "
        f"data_pagamento={lanc.data_pagamento} "
        f"valor={lanc.valor} "
        f"vencimento={lanc.data_vencimento} "
        f"saldo_conta={resumo.saldo_projetado} "
        f"realizado={resumo.resultado_realizado} "
        f"pendente={resumo.contas_a_receber_pendentes}"
    )


def _setup_app_temp_db():
    temp_dir = tempfile.mkdtemp(prefix="homolog_fin_os_")
    db_path = os.path.join(temp_dir, "integracao_os_financeiro.db")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.replace('\\', '/')}"

    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

    return app, db_path


def _criar_os_base(cliente_id, codigo, valor):
    os_obj = OrdemServico(
        codigo=codigo,
        cliente_id=cliente_id,
        status="Aberta",
        ativo=True,
        valor_total=float(valor),
        forma_pagamento="pix",
        condicao_pagamento="avista",
        qtd_parcelas=1,
        valor_entrada=Decimal("0.00"),
        status_pagamento="Pendente",
        parcelas_json=json.dumps([
            {
                "valor": str(valor),
                "data_vencimento": VENCIMENTO_CONTROLADO.strftime("%Y-%m-%d"),
            }
        ]),
    )
    db.session.add(os_obj)
    db.session.commit()
    return os_obj


def test_integracao_os_financeiro_unico():
    app, db_path = _setup_app_temp_db()
    print(f"[INFO] Banco temporario: {db_path}")

    with app.app_context():
        cliente = Cliente(nome="Cliente Integracao")
        db.session.add(cliente)
        db.session.commit()

        # 1. Criar uma OS ainda não concluida.
        os1 = _criar_os_base(cliente.id, "OS9001", VALOR_OS)
        _assert(os1.status == "Aberta", "PASSO 1: OS deve iniciar como Aberta")

        # 2. Confirmar que ela nao entra no realizado.
        r_mar = _resumo(date(2025, 3, 1), date(2025, 3, 31))
        _assert(r_mar.receita_realizada == Decimal("0"), "PASSO 2: OS nao concluida nao pode entrar no realizado")

        # 3. Concluir a OS.
        os1.status = "Concluída"
        db.session.commit()

        # 4. Confirmar que foi criada exatamente uma conta a receber pendente.
        _integrar_com_request_context(app, os1)
        _assert(_contar_lancamentos_os(os1.id) == 1, "PASSO 4: deveria existir exatamente 1 lancamento OS")

        lanc1 = _obter_lancamento_os(os1.id)

        # 5. Confirmar que a conclusao nao preenche data_pagamento.
        _assert(lanc1.data_pagamento is None, "PASSO 5: data_pagamento deve ficar vazia na conclusao")

        # 6. Confirmar que a OS nao entra como receita realizada.
        r_fev = _resumo(date(2025, 2, 1), date(2025, 2, 28))
        _assert(r_fev.receita_realizada == Decimal("0"), "PASSO 6: OS concluida sem baixa nao entra no realizado")

        # 7. Confirmar que aparece uma unica vez nas contas a receber e no projetado.
        _assert(r_fev.contas_a_receber_pendentes == VALOR_OS, "PASSO 7: valor deve aparecer em a receber")
        _assert(r_fev.saldo_projetado == VALOR_OS, "PASSO 7: valor deve entrar no saldo projetado")

        # 8. Editar novamente a OS concluida.
        os1.observacoes_internas = "edicao apos conclusao"
        db.session.commit()

        # 9. Confirmar que nao foi criado outro lancamento.
        _integrar_com_request_context(app, os1)
        _assert(_contar_lancamentos_os(os1.id) == 1, "PASSO 9: edicao nao deve duplicar lancamento")

        # 10. Repetir a operacao que dispara a integracao financeira.
        _integrar_com_request_context(app, os1)

        # 11. Confirmar idempotencia e ausencia de duplicidade.
        _assert(_contar_lancamentos_os(os1.id) == 1, "PASSO 11: repeticao da integracao nao deve duplicar")

        # 12. Tentar baixar sem data_pagamento.
        client = app.test_client()
        lanc1 = _obter_lancamento_os(os1.id)
        r_pre_falha = _resumo(date(2025, 2, 1), date(2025, 2, 28))

        resp_sem_data = client.post(
            f"/financeiro/editar-status-os/{lanc1.id}",
            data={"status": "Pago"},
            follow_redirects=False,
        )
        _assert(resp_sem_data.status_code in (302, 303), "PASSO 12: baixa sem data deve redirecionar com rejeicao")

        # 13. Confirmar rejeicao e rollback completo.
        lanc1 = _obter_lancamento_os(os1.id)
        _assert(lanc1.status == "Pendente", "PASSO 13: status deve permanecer Pendente")
        _assert(lanc1.data_pagamento is None, "PASSO 13: data_pagamento deve continuar vazia")

        # 14. Confirmar status, data, saldo da conta e quantidade inalterados.
        r_pos_falha = _resumo(date(2025, 2, 1), date(2025, 2, 28))
        _assert(r_pos_falha.contas_a_receber_pendentes == r_pre_falha.contas_a_receber_pendentes, "PASSO 14: pendencia nao pode mudar")
        _assert(r_pos_falha.saldo_projetado == r_pre_falha.saldo_projetado, "PASSO 14: projetado nao pode mudar")
        _assert(_contar_lancamentos_os(os1.id) == 1, "PASSO 14: quantidade de lancamentos deve permanecer 1")

        # 15. Efetuar baixa valida com data controlada.
        resp_baixa = client.post(
            f"/financeiro/editar-status-os/{lanc1.id}",
            data={
                "status": "Pago",
                "data_pagamento": DATA_BAIXA_CONTROLADA.strftime("%Y-%m-%d"),
            },
            follow_redirects=False,
        )
        _assert(resp_baixa.status_code in (302, 303), "PASSO 15: baixa valida deve concluir com redirect")

        # 16. Confirmar que o lancamento passou para pago com a data informada.
        lanc1 = _obter_lancamento_os(os1.id)
        _assert(lanc1.status == "Pago", "PASSO 16: status deveria estar Pago")
        _assert(lanc1.data_pagamento == DATA_BAIXA_CONTROLADA, "PASSO 16: data_pagamento deve ser a data controlada")

        # 17. Confirmar que o valor entrou no mes da baixa, nao da criacao/conclusao.
        r_fev_pos_baixa = _resumo(date(2025, 2, 1), date(2025, 2, 28))
        r_mar_pos_baixa = _resumo(date(2025, 3, 1), date(2025, 3, 31))
        _assert(r_fev_pos_baixa.receita_realizada == Decimal("0"), "PASSO 17: fevereiro nao pode receber realizado")
        _assert(r_mar_pos_baixa.receita_realizada == VALOR_OS, "PASSO 17: marco deve receber realizado")

        # 18. Confirmar que saiu das pendencias.
        _assert(r_fev_pos_baixa.contas_a_receber_pendentes == Decimal("0"), "PASSO 18: nao deve restar pendencia")

        # 19. Confirmar que entrou exatamente uma vez no realizado.
        _assert(r_mar_pos_baixa.receita_realizada == VALOR_OS, "PASSO 19: realizado deve contar uma unica vez")

        # 20. Repetir a mesma baixa.
        resp_baixa_repetida = client.post(
            f"/financeiro/editar-status-os/{lanc1.id}",
            data={
                "status": "Pago",
                "data_pagamento": DATA_BAIXA_CONTROLADA.strftime("%Y-%m-%d"),
            },
            follow_redirects=False,
        )
        _assert(resp_baixa_repetida.status_code in (302, 303), "PASSO 20: segunda baixa deve responder sem erro")

        # 21. Confirmar que o saldo da conta nao foi movimentado novamente.
        r_mar_pos_rebaixa = _resumo(date(2025, 3, 1), date(2025, 3, 31))
        _assert(r_mar_pos_rebaixa.receita_realizada == VALOR_OS, "PASSO 21: rebaixa nao pode dobrar realizado")

        # 22. Confirmar que nenhum segundo lancamento foi criado.
        _assert(_contar_lancamentos_os(os1.id) == 1, "PASSO 22: rebaixa nao pode criar novo lancamento")

        # 23. Editar a OS depois da baixa.
        _snapshot(app, os1, date(2025, 3, 1), date(2025, 3, 31), "antes_edicao_pos_baixa")
        os1.contato = "contato alterado apos baixa"
        db.session.commit()

        # 24. Confirmar que o lancamento nao voltou para pendente e nao foi duplicado.
        _integrar_com_request_context(app, os1)
        lanc1_pos_edicao = _obter_lancamento_os(os1.id)
        _snapshot(app, os1, date(2025, 3, 1), date(2025, 3, 31), "depois_edicao_pos_baixa")
        _assert(lanc1_pos_edicao.status == "Pago", "PASSO 24: apos editar OS baixada, status nao deveria voltar para Pendente")
        _assert(_contar_lancamentos_os(os1.id) == 1, "PASSO 24: apos editar OS baixada, nao deveria duplicar")

        # 25. Inativar a OS.
        os1.ativo = False
        db.session.commit()

        # 26. Confirmar comportamento definido para indicadores atuais, preservando historico.
        r_mar_os_inativa = _resumo(date(2025, 3, 1), date(2025, 3, 31))
        print(
            "[INFO] PASSO 26 comportamento OS inativa: "
            f"receita_realizada={r_mar_os_inativa.receita_realizada}, "
            f"a_receber={r_mar_os_inativa.contas_a_receber_pendentes}"
        )

        # 27. Criar duas OS diferentes com mesmo cliente e mesmo valor.
        os2 = _criar_os_base(cliente.id, "OS9002", VALOR_OS)
        os2.status = "Concluída"
        db.session.commit()
        _integrar_com_request_context(app, os2)

        os3 = _criar_os_base(cliente.id, "OS9003", VALOR_OS)
        os3.status = "Concluída"
        db.session.commit()
        _integrar_com_request_context(app, os3)

        # 28. Confirmar lancamentos independentes por OS, sem deduplicacao falsa.
        _assert(_contar_lancamentos_os(os2.id) == 1, "PASSO 28: OS2 deve ter 1 lancamento proprio")
        _assert(_contar_lancamentos_os(os3.id) == 1, "PASSO 28: OS3 deve ter 1 lancamento proprio")
        _assert(os2.id != os3.id, "PASSO 28: IDs de OS devem ser diferentes")

        # Compatibilidade com anexos sem extensao obrigatoria.
        os_legado = _criar_os_base(cliente.id, "OS9004", VALOR_OS)
        os_legado.anexos_dados = json.dumps([
            {
                "nome_arquivo": "legacy_arquivo_sem_ext",
                "nome_original": "sem_ext",
                "tamanho": 123,
            }
        ])
        os_legado.status = "Concluída"
        db.session.commit()
        _integrar_com_request_context(app, os_legado)
        _assert(_contar_lancamentos_os(os_legado.id) == 1, "ANEXOS: legado sem extensao nao deve bloquear conclusao")

        os_legado.observacoes_internas = "edicao apos legado sem extensao"
        db.session.commit()
        _integrar_com_request_context(app, os_legado)
        _assert(_contar_lancamentos_os(os_legado.id) == 1, "ANEXOS: legado sem extensao nao deve bloquear edicao")

    print("TESTE_INTEGRACAO_OS_FINANCEIRO_OK")


if __name__ == "__main__":
    test_integracao_os_financeiro_unico()
