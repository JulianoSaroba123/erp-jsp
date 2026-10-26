# -*- coding: utf-8 -*-
"""PR #46: cenário Jumirim inteiramente FICTÍCIO, SQLite em memória.

Nunca consulta OS 619/Extrato 45 de produção. IDs, cliente e datas abaixo são
dados artificiais criados pela própria fixture para validar as regras.
Executar com DATABASE_URL apontando para SQLite TEMP, nunca Render.
"""
from datetime import date
from decimal import Decimal

import pytest
from flask import g
from types import SimpleNamespace

from app.extensoes import db
from app.cliente.cliente_model import Cliente
from app.financeiro.financeiro_model import (
    ContaBancaria, ConciliacaoBancariaItem, ExtratoBancario,
    HistoricoFinanceiro, LancamentoFinanceiro,
)
from app.financeiro.financeiro_utils import gerar_lancamento_ordem_servico
from app.ordem_servico.ordem_servico_model import (
    OrdemServico, OrdemServicoParcela,
)
from app.ordem_servico.recebimento_parcelas import (
    RecebimentoParcelaInvalido, registrar_recebimento_parcela,
)


@pytest.fixture()
def caso_jumirim_ficticio():
    # Configuracao testing usa SQLAlchemy SQLite :memory:.
    from app.app import create_app
    app = create_app("testing")
    assert app.config["TESTING"] is True
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        cliente = Cliente(nome="JUMIRIM - HOMOLOGACAO FICTICIA", ativo=True)
        conta = ContaBancaria(
            nome="Cora HOMOLOGACAO", tipo="conta_corrente", banco="Cora",
            saldo_inicial=Decimal("15000.00"),
            saldo_atual=Decimal("15000.00"),
            ativa=True, ativo=True, principal=False,
        )
        db.session.add_all([cliente, conta])
        db.session.flush()
        ordem = OrdemServico(
            numero="OS-PR46-TESTE", titulo="Manutencao ficticia",
            cliente_id=cliente.id, tipo_os="comercial",
            status="iniciada", status_pagamento="pendente",
            condicao_pagamento="parcelado", numero_parcelas=3,
            valor_entrada=Decimal("15000.00"), valor_servico=Decimal("30000.00"),
            valor_total=Decimal("30000.00"),
            data_abertura=date(2026, 9, 15), ativo=True,
        )
        db.session.add(ordem)
        db.session.flush()
        parcelas = [
            OrdemServicoParcela(
                ordem_servico_id=ordem.id, numero_parcela=i,
                valor=valor, data_vencimento=vencimento,
                pago=False, ativo=True,
            )
            for i, valor, vencimento in (
                (1, Decimal("15000.00"), date(2026, 9, 17)),
                (2, Decimal("7500.00"), date(2026, 10, 17)),
                (3, Decimal("7500.00"), date(2026, 11, 17)),
            )
        ]
        extrato = ExtratoBancario(
            id=45, conta_bancaria_id=conta.id,
            data_movimento=date(2026, 9, 17),
            descricao="CRÉDITO FICTÍCIO Cora",
            tipo_movimento="credito", valor=Decimal("15000.00"),
            saldo=Decimal("15000.00"), conciliado=False, ativo=True,
        )
        db.session.add_all(parcelas + [extrato])
        db.session.commit()
        ids = {
            "os": ordem.id, "conta": conta.id,
            "parcelas": [p.id for p in parcelas],
            "extrato": extrato.id,
        }
        yield app, ids
        db.session.remove()


def _registrar(ids, **overrides):
    parametros = dict(
        os_id=ids["os"], parcela_id=ids["parcelas"][0],
        data_recebimento=date(2026, 9, 17),
        valor_recebido="15000.00", forma_pagamento="pix",
        conta_bancaria_id=ids["conta"],
        observacao="Recebimento comprovado, conciliar com extrato",
        usuario="admin-teste",
    )
    parametros.update(overrides)
    return registrar_recebimento_parcela(**parametros)


def test_jumirim_tres_titulos_pendentes_antes_da_conclusao(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        ordem = db.session.get(OrdemServico, ids["os"])
        itens = gerar_lancamento_ordem_servico(ordem)
        assert len(itens) == 3
        assert {i.status for i in itens} == {"pendente"}
        assert {i.ordem_servico_parcela_id for i in itens} == set(ids["parcelas"])
        assert sum((i.valor for i in itens), Decimal("0.00")) == Decimal("30000.00")
        assert db.session.get(ContaBancaria, ids["conta"]).saldo_atual == Decimal("15000.00")


def test_recebimento_antecipado_auditoria_e_idempotencia(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        ordem = db.session.get(OrdemServico, ids["os"])
        assert len(gerar_lancamento_ordem_servico(ordem)) == 3
        recebimento = _registrar(ids)
        db.session.commit()
        assert recebimento.status == "recebido"
        assert recebimento.data_pagamento == date(2026, 9, 17)
        assert recebimento.conta_bancaria_id == ids["conta"]
        assert recebimento.sem_movimentacao_bancaria is True
        assert ordem.status == "iniciada"
        assert ordem.status_pagamento == "parcial"

        lista = LancamentoFinanceiro.query.filter_by(
            ordem_servico_id=ids["os"], ativo=True,
        ).order_by(LancamentoFinanceiro.id).all()
        assert len(lista) == 3
        assert sum((i.valor for i in lista if i.status == "recebido"), Decimal("0.00")) == Decimal("15000.00")
        assert sum((i.valor for i in lista if i.status == "pendente"), Decimal("0.00")) == Decimal("15000.00")
        assert len([i for i in lista if i.status == "recebido"]) == 1
        assert HistoricoFinanceiro.query.filter_by(
            lancamento_id=recebimento.id, acao="pagamento",
        ).count() == 1
        assert db.session.get(ExtratoBancario, ids["extrato"]).conciliado is False
        db.session.expire_all()  # Eventos de saldo fazem SQL direto: reler do banco.
        assert db.session.get(ContaBancaria, ids["conta"]).saldo_atual == Decimal("15000.00")

        with pytest.raises(RecebimentoParcelaInvalido, match="já recebida"):
            _registrar(ids)
        db.session.rollback()
        assert len(gerar_lancamento_ordem_servico(ordem)) == 3
        ordem.status = "concluida"
        db.session.commit()
        assert len(gerar_lancamento_ordem_servico(ordem)) == 3
        assert HistoricoFinanceiro.query.filter_by(lancamento_id=recebimento.id).count() == 1
        assert db.session.get(ContaBancaria, ids["conta"]).saldo_atual == Decimal("15000.00")


@pytest.mark.parametrize("alteracoes,erro", [
    ({"valor_recebido": "14999.99"}, "igual"),
    ({"valor_recebido": "NaN"}, "inválido"),
    ({"valor_recebido": "15000.001"}, "inválido"),
    ({"forma_pagamento": "cripto"}, "não permitida"),
    ({"conta_bancaria_id": "invalido"}, "bancária"),
    ({"conta_bancaria_id": 99999}, "inexistente"),
    ({"data_recebimento": date(2099, 1, 1)}, "futura"),
    ({"parcela_id": 987654}, "não pertence"),
])
def test_entrada_invalida_nao_modifica_parcela(caso_jumirim_ficticio, alteracoes, erro):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        with pytest.raises(RecebimentoParcelaInvalido, match=erro):
            _registrar(ids, **alteracoes)
        db.session.rollback()
        assert not db.session.get(OrdemServicoParcela, ids["parcelas"][0]).pago
        assert db.session.get(OrdemServico, ids["os"]).status == "iniciada"
        assert db.session.get(ContaBancaria, ids["conta"]).saldo_atual == Decimal("15000.00")


def test_detecta_duplicidade_preexistente_e_reverte(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        ordem = db.session.get(OrdemServico, ids["os"])
        assert len(gerar_lancamento_ordem_servico(ordem)) == 3
        original = LancamentoFinanceiro.query.filter_by(
            ordem_servico_parcela_id=ids["parcelas"][0],
        ).one()
        duplicado = LancamentoFinanceiro(
            descricao="TITULO DUPLICADO - FICTICIO", valor=original.valor,
            tipo="conta_receber", status="pendente",
            ordem_servico_id=ids["os"],
            ordem_servico_parcela_id=ids["parcelas"][0],
            data_lancamento=date(2026, 9, 15),
            ativo=True,
        )
        from sqlalchemy.exc import IntegrityError
        db.session.add(duplicado)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        assert not db.session.get(OrdemServicoParcela, ids["parcelas"][0]).pago


def test_conciliacao_nn_extrato_existente_nao_duplica_saldo(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        from app.financeiro.conciliacao_adapter import executar_conciliacao_bancaria
        from app.financeiro.conciliacao_service import SolicitacaoAlocacao

        ordem = db.session.get(OrdemServico, ids["os"])
        gerar_lancamento_ordem_servico(ordem)
        lancamento = _registrar(ids)
        db.session.commit()

        resultado = executar_conciliacao_bancaria(
            extrato_id=ids["extrato"],
            alocacoes=[SolicitacaoAlocacao(
                lancamento_id=lancamento.id, valor=Decimal("15000.00"),
            )],
            usuario="admin-teste",
        )
        assert resultado.preparacao.status_final == "CONCILIADO"
        itens = ConciliacaoBancariaItem.query.filter_by(
            extrato_id=ids["extrato"], lancamento_id=lancamento.id,
            ativo=True,
        ).all()
        assert len(itens) == 1
        assert itens[0].valor_conciliado == Decimal("15000.00")
        db.session.expire_all()
        assert db.session.get(ContaBancaria, ids["conta"]).saldo_atual == Decimal("15000.00")
        assert ordem.status == "iniciada"
        assert db.session.get(OrdemServicoParcela, ids["parcelas"][0]).pago is True


def test_http_csrf_e_permissoes(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    client = app.test_client()
    path = f"/ordem_servico/{ids['os']}/parcelas/{ids['parcelas'][0]}/receber"
    payload = {
        "data_recebimento": "2026-09-17",
        "valor_recebido": "15000.00",
        "forma_pagamento": "pix",
        "conta_bancaria_id": str(ids["conta"]),
    }
    @app.before_request
    def usuario_admin_teste():
        g._login_user = SimpleNamespace(
            id=1, tipo_usuario="admin", is_authenticated=True,
        )

    # Falta token => 400, sem escrever.
    assert client.post(path, data=payload).status_code == 400
    with client.session_transaction() as sess:
        sess["_csrf_os_recebimento_v1"] = "token-de-teste"
    assert client.post(
        path, data={**payload, "csrf_os_recebimento": "invalido"}
    ).status_code == 400
    resposta = client.post(
        path, data={**payload, "csrf_os_recebimento": "token-de-teste"}
    )
    assert resposta.status_code in (302, 303)
    with app.app_context():
        parcela = db.session.get(OrdemServicoParcela, ids["parcelas"][0])
        assert parcela.pago is True
        assert db.session.get(OrdemServico, ids["os"]).status == "iniciada"



def test_erro_durante_auditoria_reverte_baixa_inteira(caso_jumirim_ficticio):
    from unittest.mock import patch

    app, ids = caso_jumirim_ficticio
    with app.app_context():
        ordem = db.session.get(OrdemServico, ids["os"])
        assert len(gerar_lancamento_ordem_servico(ordem)) == 3
        with patch(
            "app.ordem_servico.recebimento_parcelas.HistoricoFinanceiro",
            side_effect=RuntimeError("Falha simulada ao criar auditoria"),
        ):
            with pytest.raises(RuntimeError, match="Falha simulada"):
                _registrar(ids)
        db.session.rollback()
        db.session.expire_all()
        parcela = db.session.get(OrdemServicoParcela, ids["parcelas"][0])
        assert parcela.pago is False
        assert parcela.data_pagamento is None
        assert db.session.get(OrdemServico, ids["os"]).status_pagamento == "pendente"
        lancamento = LancamentoFinanceiro.query.filter_by(
            ordem_servico_parcela_id=parcela.id,
        ).one()
        assert lancamento.status == "pendente"
        assert lancamento.data_pagamento is None
        assert HistoricoFinanceiro.query.filter_by(
            lancamento_id=lancamento.id,
        ).count() == 0


def test_nao_admin_bloqueado_na_rota(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    client = app.test_client()

    @app.before_request
    def usuario_comum_teste():
        g._login_user = SimpleNamespace(
            id=9, tipo_usuario="comum", is_authenticated=True,
        )

    with client.session_transaction() as sess:
        sess["_csrf_os_recebimento_v1"] = "token-de-teste"
    resposta = client.post(
        f"/ordem_servico/{ids['os']}/parcelas/{ids['parcelas'][0]}/receber",
        data={
            "csrf_os_recebimento": "token-de-teste",
            "data_recebimento": "2026-09-17",
            "valor_recebido": "15000.00",
            "forma_pagamento": "pix",
            "conta_bancaria_id": str(ids["conta"]),
        },
    )
    assert resposta.status_code == 403
    with app.app_context():
        assert db.session.get(OrdemServicoParcela, ids["parcelas"][0]).pago is False



def test_titulo_inativo_vinculado_bloqueia_recriacao(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        ordem = db.session.get(OrdemServico, ids["os"])
        gerar_lancamento_ordem_servico(ordem)
        titulo = LancamentoFinanceiro.query.filter_by(
            ordem_servico_parcela_id=ids["parcelas"][0],
        ).one()
        titulo.ativo = False
        db.session.commit()
        with pytest.raises(RecebimentoParcelaInvalido, match="histórico inativo"):
            _registrar(ids)
        db.session.rollback()
        assert not db.session.get(OrdemServicoParcela, ids["parcelas"][0]).pago


def test_evento_bancario_legado_permanece_ativo_para_outros_titulos(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        conta = db.session.get(ContaBancaria, ids["conta"])
        inicial = conta.saldo_atual
        titulo = LancamentoFinanceiro(
            descricao="Recebimento avulso fictício",
            tipo="conta_receber", status="pendente",
            origem="MANUAL", valor=Decimal("75.00"),
            cliente_id=db.session.get(OrdemServico, ids["os"]).cliente_id,
            conta_bancaria_id=conta.id,
            data_lancamento=date(2026, 9, 18),
            ativo=True, sem_movimentacao_bancaria=False,
        )
        db.session.add(titulo)
        db.session.commit()
        titulo.status = "recebido"
        titulo.data_pagamento = date(2026, 9, 18)
        db.session.commit()
        db.session.expire_all()
        assert db.session.get(ContaBancaria, ids["conta"]).saldo_atual == (
            inicial + Decimal("75.00")
        )



def test_edicao_posterior_ao_recebimento_nao_aplica_delta_bancario(
    caso_jumirim_ficticio,
):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        ordem = db.session.get(OrdemServico, ids["os"])
        gerar_lancamento_ordem_servico(ordem)
        lancamento = _registrar(ids)
        db.session.commit()
        lancamento.observacoes = "Conferido novamente com o extrato"
        db.session.commit()
        db.session.expire_all()
        assert db.session.get(LancamentoFinanceiro, lancamento.id).sem_movimentacao_bancaria
        assert db.session.get(ContaBancaria, ids["conta"]).saldo_atual == Decimal("15000.00")


def test_parcela_quitada_nao_pode_ser_reprecificada(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        from app.ordem_servico.ordem_servico_routes import _reconciliar_parcelas_ordem
        ordem = db.session.get(OrdemServico, ids["os"])
        gerar_lancamento_ordem_servico(ordem)
        _registrar(ids)
        db.session.commit()
        with pytest.raises(ValueError, match="não pode ser alterada"):
            _reconciliar_parcelas_ordem(ordem, [
                (1, date(2026, 9, 17), Decimal("14000.00")),
                (2, date(2026, 10, 17), Decimal("8500.00")),
                (3, date(2026, 11, 17), Decimal("7500.00")),
            ])
        db.session.rollback()
        assert db.session.get(OrdemServicoParcela, ids["parcelas"][0]).valor == Decimal("15000.00")
