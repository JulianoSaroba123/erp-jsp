# -*- coding: utf-8 -*-
"""Regressao da desconciliacao N:N. So usa SQLite em memoria ou PG local de teste."""
from datetime import date, datetime
from decimal import Decimal

import pytest

from app.extensoes import db
from app.financeiro.conciliacao_adapter import (
    desfazer_conciliacao_bancaria, executar_conciliacao_bancaria,
)
from app.financeiro.conciliacao_service import (
    ConciliacaoInvalida, SolicitacaoAlocacao,
)
from app.financeiro.financeiro_model import (
    ContaBancaria, ConciliacaoBancariaItem, ExtratoBancario,
    LancamentoFinanceiro,
)
from scripts_manutencao.testes.test_pr46_os_recebimento import (
    banco_pr46, caso_jumirim_ficticio,
)


def _lancamento(ids, valor, descricao="Material escritorio ficticio"):
    obj = LancamentoFinanceiro(
        descricao=descricao, valor=Decimal(valor), tipo="despesa",
        status="pago", ativo=True, origem="MANUAL",
        data_lancamento=date(2026, 9, 26),
        data_pagamento=date(2026, 9, 26),
        conta_bancaria_id=ids["conta"],
    )
    db.session.add(obj)
    db.session.flush()
    return obj


def _extrato(ids, valor, descricao="Pix ficticio", conciliado=False,
             lancamento_id=None):
    obj = ExtratoBancario(
        conta_bancaria_id=ids["conta"], data_movimento=date(2026, 9, 26),
        descricao=descricao, valor=Decimal(valor), tipo_movimento="debito",
        conciliado=conciliado, lancamento_id=lancamento_id,
        data_conciliacao=datetime.utcnow() if conciliado else None,
        ativo=True,
    )
    db.session.add(obj)
    db.session.flush()
    return obj


def _alocacao(extrato, lancamento, valor):
    obj = ConciliacaoBancariaItem(
        extrato_id=extrato.id, lancamento_id=lancamento.id,
        valor_conciliado=Decimal(valor), ativo=True,
        usuario="teste", observacoes="Conciliação original.",
    )
    db.session.add(obj)
    db.session.flush()
    return obj


@pytest.mark.parametrize("banco_pr46", ["sqlite", "postgres"], indirect=True)
def test_corrige_par_pendente_com_alocacao_fantasma(caso_jumirim_ficticio):
    """Replica o problema real: extrato 82 pendente, mas reserva R$24,50 no 212."""
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        lanc = _lancamento(ids, "100.00")
        extrato_errado = _extrato(ids, "24.50", "Extrato 82")
        extrato_certo = _extrato(ids, "100.00", "Extrato 81")
        item = _alocacao(extrato_errado, lanc, "24.50")
        db.session.commit()
        dados = (lanc.id, extrato_errado.id, extrato_certo.id, item.id)
        saldo_inicial = db.session.get(ContaBancaria, ids["conta"]).saldo_atual

        resultado = desfazer_conciliacao_bancaria(
            extrato_id=extrato_errado.id,
            lancamento_id=lanc.id,
            motivo="Valor atribuido ao extrato errado.",
            usuario="admin_teste",
        )
        assert resultado["alocacoes_desfeitas"] == 1
        db.session.expire_all()
        assert not db.session.get(ConciliacaoBancariaItem, dados[3]).ativo
        assert "Valor atribuido" in db.session.get(
            ConciliacaoBancariaItem, dados[3]).observacoes
        assert not db.session.get(ExtratoBancario, dados[1]).conciliado

        executar_conciliacao_bancaria(
            extrato_id=dados[2],
            alocacoes=[SolicitacaoAlocacao(
                lancamento_id=dados[0], valor=Decimal("100.00"))],
            usuario="admin_teste",
        )
        db.session.expire_all()
        assert db.session.get(ExtratoBancario, dados[2]).conciliado
        assert db.session.get(ExtratoBancario, dados[2]).lancamento_id == dados[0]
        assert db.session.get(ConciliacaoBancariaItem, dados[3]).ativo is False
        assert db.session.get(LancamentoFinanceiro, dados[0]).status == "pago"
        assert db.session.get(ContaBancaria, ids["conta"]).saldo_atual == saldo_inicial


def test_desfaz_erro_cem_reais_e_reconcilia_com_titulo_correto(
    caso_jumirim_ficticio,
):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        anterior = _lancamento(ids, "100.00", "Abastecimento antigo")
        correto = _lancamento(ids, "100.00", "Abastecimento do dia")
        extrato = _extrato(
            ids, "100.00", "Extrato 84", conciliado=True,
            lancamento_id=anterior.id,
        )
        errado = _alocacao(extrato, anterior, "100.00")
        db.session.commit()
        eid, cid, iid = extrato.id, correto.id, errado.id

        desfazer_conciliacao_bancaria(
            eid, lancamento_id=anterior.id, motivo="Periodo de agosto errado.",
            usuario="admin_teste",
        )
        db.session.expire_all()
        assert db.session.get(ExtratoBancario, eid).lancamento_id is None
        assert not db.session.get(ExtratoBancario, eid).conciliado
        assert not db.session.get(ConciliacaoBancariaItem, iid).ativo

        executar_conciliacao_bancaria(
            extrato_id=eid,
            alocacoes=[SolicitacaoAlocacao(
                lancamento_id=cid, valor=Decimal("100.00"))],
            usuario="admin_teste",
        )
        assert db.session.get(ExtratoBancario, eid).lancamento_id == cid
        assert db.session.get(ExtratoBancario, eid).conciliado
        assert db.session.get(ConciliacaoBancariaItem, iid).ativo is False


def test_desfaz_so_uma_alocacao_e_exige_id_em_extrato_multiplo(
    caso_jumirim_ficticio,
):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        a = _lancamento(ids, "30.00", "Auxiliar A")
        b = _lancamento(ids, "70.00", "Auxiliar B")
        extrato = _extrato(ids, "100.00", "Extrato com duas OS", True)
        item_a = _alocacao(extrato, a, "30.00")
        item_b = _alocacao(extrato, b, "70.00")
        db.session.commit()
        eid, aid, item_a_id, item_b_id = (
            extrato.id, a.id, item_a.id, item_b.id
        )

        with pytest.raises(ConciliacaoInvalida, match="selecione"):
            desfazer_conciliacao_bancaria(
                eid, motivo="Corrigir uma das OS sem alterar outra.",
            )
        assert db.session.get(ConciliacaoBancariaItem, item_a_id).ativo
        assert db.session.get(ConciliacaoBancariaItem, item_b_id).ativo

        desfazer_conciliacao_bancaria(
            eid, lancamento_id=aid,
            motivo="OS A nao corresponde a este Pix.", usuario="admin_teste",
        )
        db.session.expire_all()
        assert db.session.get(ConciliacaoBancariaItem, item_a_id).ativo is False
        assert db.session.get(ConciliacaoBancariaItem, item_b_id).ativo is True
        assert not db.session.get(ExtratoBancario, eid).conciliado
        assert db.session.get(ExtratoBancario, eid).lancamento_id is None
        with pytest.raises(ConciliacaoInvalida, match="Nenhum vinculo"):
            desfazer_conciliacao_bancaria(
                eid, lancamento_id=aid,
                motivo="Tentativa repetida de reversao.",
            )


def test_legado_sem_nn_e_reconciliacao_preservam_auditoria(
    caso_jumirim_ficticio,
):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        lanc = _lancamento(ids, "25.00", "Legacy")
        extrato = _extrato(
            ids, "25.00", "Extrato 1:1 antigo",
            conciliado=True, lancamento_id=lanc.id,
        )
        db.session.commit()
        eid, lid = extrato.id, lanc.id

        desfazer_conciliacao_bancaria(
            eid, lancamento_id=lid,
            motivo="Cadastro legado equivocado.", usuario="admin_teste",
        )
        db.session.expire_all()
        antigo = db.session.get(ExtratoBancario, eid)
        assert not antigo.conciliado
        assert antigo.lancamento_id is None
        assert "Cadastro legado" in antigo.observacoes

        # Depois do desfazer, o mesmo par pode voltar a ser conciliado
        # pelo fluxo N:N, sem apagar o motivo registrado no extrato.
        executar_conciliacao_bancaria(
            extrato_id=eid,
            alocacoes=[SolicitacaoAlocacao(
                lancamento_id=lid, valor=Decimal("25.00"))],
            usuario="admin_teste",
        )
        assert db.session.get(ExtratoBancario, eid).conciliado


def test_reativacao_de_par_unico_preserva_motivo(
    caso_jumirim_ficticio,
):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        lanc = _lancamento(ids, "35.00", "Ferramentas")
        extrato = _extrato(ids, "35.00", "Pagamento original", True, lanc.id)
        item = _alocacao(extrato, lanc, "35.00")
        db.session.commit()
        eid, lid, iid = extrato.id, lanc.id, item.id

        desfazer_conciliacao_bancaria(
            eid, lancamento_id=lid,
            motivo="Vinculo substituido para verificacao.", usuario="admin",
        )
        executar_conciliacao_bancaria(
            extrato_id=eid,
            alocacoes=[SolicitacaoAlocacao(
                lancamento_id=lid, valor=Decimal("35.00"))],
            usuario="admin",
            observacoes="Nova conciliacao revisada.",
        )
        db.session.expire_all()
        registro = db.session.get(ConciliacaoBancariaItem, iid)
        assert registro.ativo
        assert registro.valor_conciliado == Decimal("35.00")
        assert "Vinculo substituido" in registro.observacoes
        assert "Reconciliado" in registro.observacoes
        assert "Nova conciliacao revisada" in registro.observacoes


def test_rota_desconciliacao_requer_admin_csrf_e_motivo(
    caso_jumirim_ficticio,
):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        lanc = _lancamento(ids, "24.50", "Compra de valor errado")
        extrato = _extrato(ids, "24.50", "Pix 82", conciliado=False)
        _alocacao(extrato, lanc, "24.50")
        db.session.commit()
        eid, lid = extrato.id, lanc.id

    path = f"/financeiro/conciliacao-bancaria/desconciliar/{eid}"
    client = app.test_client()
    assert client.post(path).status_code == 302  # exige login
    client.post("/auth/login", data={
        "identificador": "comum_pr46", "senha": "SenhaPr46Teste!"
    })
    assert client.post(path).status_code == 403
    client.get("/auth/logout")
    client.post("/auth/login", data={
        "identificador": "admin_pr46", "senha": "SenhaPr46Teste!"
    })

    assert client.post(path).status_code == 400  # exige token
    resposta = client.get(
        f"/financeiro/conciliacao-bancaria/historico?conta_id={ids['conta']}"
    )
    assert resposta.status_code == 200
    assert b"Desfazer" in resposta.data
    with client.session_transaction() as state:
        token = state["_csrf_desconciliacao"]
    assert client.post(path, data={
        "csrf_desconciliacao": token, "lancamento_id": lid,
        "motivo": "curto",
    }).status_code == 302
    with app.app_context():
        assert ConciliacaoBancariaItem.query.filter_by(
            extrato_id=eid, lancamento_id=lid, ativo=True
        ).count() == 1

    assert client.post(path, data={
        "csrf_desconciliacao": token, "lancamento_id": lid,
        "motivo": "Alocacao feita no extrato errado.",
    }).status_code == 302
    with app.app_context():
        assert ConciliacaoBancariaItem.query.filter_by(
            extrato_id=eid, lancamento_id=lid, ativo=True
        ).count() == 0
        assert db.session.get(ExtratoBancario, eid).conciliado is False
