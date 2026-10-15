# -*- coding: utf-8 -*-
"""G5-F5: auditoria de operações e proteção dos PDFs concluídos.

Reutiliza a fixture SQLite isolada de G5-F3, sem acessar produção.
"""
import hashlib
from pathlib import Path

import pytest

from app.extensoes import db
from app.geradores.gerador_checklist_evento_model import GeradorChecklistEvento
from app.geradores.gerador_checklist_execucao_model import GeradorChecklistExecucao
from app.geradores.gerador_checklist_execucao_service import (
    criar_checklist, salvar_checklist,
)
from app.geradores.gerador_checklist_auditoria_service import (
    hash_respostas, registrar_evento, consultar_historico, conferir_integridade,
)
from scripts_manutencao.testes.geradores_g5_f3_checklist_digital_test import (
    ctx, login, resposta_para,
)


def _novo(ctx, tipo="BASICA"):
    _, ids = ctx
    checklist, criado = criar_checklist(
        ids["v1"], tipo, usuario_id=ids["admin"],
    )
    assert criado is True
    db.session.commit()
    return checklist, ids


def _concluir(checklist, usuario_id):
    salvar_checklist(
        checklist.id, resposta_para(checklist.tipo_plano),
        usuario_id=usuario_id, concluir=True,
    )
    db.session.commit()


def test_criacao_gera_evento_e_hash(ctx):
    checklist, ids = _novo(ctx)
    eventos = consultar_historico(checklist.id)
    assert len(eventos) == 1
    evento = eventos[0]
    assert evento.sequencia == 1
    assert evento.acao == "CRIADO"
    assert evento.estado_resultante == "RASCUNHO"
    assert evento.usuario_id == ids["admin"]
    assert evento.usuario_nome == "Admin G5 F3"
    assert evento.registrado_em is not None
    assert len(evento.sha256_respostas) == 64
    assert conferir_integridade(checklist, eventos)


def test_dois_rascunhos_e_conclusao_geram_sequencia(ctx):
    checklist, ids = _novo(ctx)
    for observacao in ("Primeiro rascunho", "Segundo rascunho"):
        salvar_checklist(
            checklist.id, {},
            usuario_id=ids["admin"], observacoes_gerais=observacao,
        )
        db.session.commit()
    _concluir(checklist, ids["admin"])
    eventos = consultar_historico(checklist.id)
    assert [(e.sequencia, e.acao, e.estado_resultante) for e in eventos] == [
        (1, "CRIADO", "RASCUNHO"),
        (2, "RASCUNHO_SALVO", "RASCUNHO"),
        (3, "RASCUNHO_SALVO", "RASCUNHO"),
        (4, "CONCLUIDO", "CONCLUIDO"),
    ]
    assert conferir_integridade(checklist, eventos)


def test_hash_estavel_com_ordenacao_de_chaves():
    esquerda = {"tipo": "BASICA", "respostas": [{"b": 2, "a": 1}]}
    direita = {"respostas": [{"a": 1, "b": 2}], "tipo": "BASICA"}
    assert hash_respostas(esquerda) == hash_respostas(direita)
    assert hash_respostas(esquerda) == hashlib.sha256(
        b'{"respostas":[{"a":1,"b":2}],"tipo":"BASICA"}'
    ).hexdigest()


def test_hash_nao_confunde_dados_diferentes():
    assert hash_respostas({"respostas": []}) != hash_respostas(
        {"respostas": [{"status": "CONFORME"}]}
    )


@pytest.mark.parametrize("invalido", [None, "texto", [], 1])
def test_hash_recusa_entrada_sem_objeto(invalido):
    with pytest.raises(ValueError, match="inválido"):
        hash_respostas(invalido)


def test_nao_admite_evento_com_acao_desconhecida(ctx):
    checklist, ids = _novo(ctx)
    with pytest.raises(ValueError, match="Ação"):
        registrar_evento(
            checklist, acao="EXCLUIDO", usuario_id=ids["admin"],
        )


def test_salvamento_rollback_desfaz_evento_e_respostas(ctx):
    checklist, ids = _novo(ctx)
    salvar_checklist(
        checklist.id,
        {"SEG_EPI": {"status": "CONFORME"}},
        usuario_id=ids["admin"],
    )
    assert GeradorChecklistEvento.query.filter_by(execucao_id=checklist.id).count() == 2
    db.session.rollback()
    db.session.expire_all()
    checklist = db.session.get(GeradorChecklistExecucao, checklist.id)
    assert len(consultar_historico(checklist.id)) == 1
    assert conferir_integridade(checklist, consultar_historico(checklist.id))


def test_rollback_criacao_nao_deixa_evento_orfao(ctx):
    _, ids = ctx
    checklist, _ = criar_checklist(
        ids["v1"], "AVANCADA", usuario_id=ids["admin"],
    )
    numero = checklist.id
    assert GeradorChecklistEvento.query.filter_by(execucao_id=numero).count() == 1
    db.session.rollback()
    assert db.session.get(GeradorChecklistExecucao, numero) is None
    assert GeradorChecklistEvento.query.filter_by(execucao_id=numero).count() == 0


def test_verifica_adulteracao_do_snapshot(ctx):
    checklist, ids = _novo(ctx)
    _concluir(checklist, ids["admin"])
    assert conferir_integridade(checklist, consultar_historico(checklist.id))
    modificado = dict(checklist.respostas_snapshot)
    modificado["informacao_injetada"] = "DIVERGENTE"
    checklist.respostas_snapshot = modificado
    db.session.flush()
    assert not conferir_integridade(checklist, consultar_historico(checklist.id))


def test_verifica_estado_concluido_sem_evento_final(ctx):
    checklist, ids = _novo(ctx)
    checklist.estado = "CONCLUIDO"
    db.session.flush()
    assert not conferir_integridade(checklist, consultar_historico(checklist.id))


def test_idempotencia_nao_repete_evento_criacao(ctx):
    checklist, ids = _novo(ctx)
    outro, criado = criar_checklist(
        ids["v1"], "BASICA", usuario_id=ids["admin"],
    )
    assert not criado
    assert outro.id == checklist.id
    assert len(consultar_historico(checklist.id)) == 1


def test_concluido_bloqueia_novos_eventos_espurios_por_servico(ctx):
    checklist, ids = _novo(ctx)
    _concluir(checklist, ids["admin"])
    from app.geradores.gerador_checklist_execucao_service import (
        ExecucaoChecklistError,
    )
    with pytest.raises(ExecucaoChecklistError):
        salvar_checklist(checklist.id, {}, usuario_id=ids["admin"])
    assert len(consultar_historico(checklist.id)) == 2


def test_rota_historico_exige_login(ctx):
    app, ids = ctx
    checklist, _ = _novo(ctx)
    client = app.test_client()
    assert client.get(
        f"/geradores/checklists/{checklist.id}/historico"
    ).status_code == 302


def test_rota_historico_bloqueia_usuario_comum(ctx):
    app, _ = ctx
    checklist, _ = _novo(ctx)
    client = app.test_client()
    login(client, "comum_g5f3")
    assert client.get(
        f"/geradores/checklists/{checklist.id}/historico"
    ).status_code == 403


def test_rota_historico_admin_exibe_eventos(ctx):
    app, _ = ctx
    checklist, ids = _novo(ctx)
    _concluir(checklist, ids["admin"])
    client = app.test_client()
    login(client)
    resp = client.get(f"/geradores/checklists/{checklist.id}/historico")
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "Checklist iniciado" in html
    assert "Checklist concluído" in html
    assert "Admin G5 F3" in html
    assert "Snapshot conferido" in html
    assert "Não é assinatura digital" in html


def test_historico_http_so_get(ctx):
    app, _ = ctx
    checklist, _ = _novo(ctx)
    client = app.test_client()
    login(client)
    assert client.post(
        f"/geradores/checklists/{checklist.id}/historico"
    ).status_code == 405


def test_pdf_preenchido_bloqueado_se_hash_divergente(ctx):
    app, _ = ctx
    checklist, ids = _novo(ctx)
    _concluir(checklist, ids["admin"])
    modificado = dict(checklist.respostas_snapshot)
    modificado["intruso"] = "valor alterado"
    checklist.respostas_snapshot = modificado
    db.session.commit()
    client = app.test_client()
    login(client)
    assert client.get(
        f"/geradores/checklists/{checklist.id}/pdf?modo=preenchido"
    ).status_code == 409


def test_pdf_preenchido_funciona_com_integridade_confirmada(ctx):
    app, _ = ctx
    checklist, ids = _novo(ctx)
    _concluir(checklist, ids["admin"])
    client = app.test_client()
    login(client)
    resp = client.get(
        f"/geradores/checklists/{checklist.id}/pdf?modo=preenchido"
    )
    assert resp.status_code == 200
    assert resp.data.startswith(b"%PDF-")


def test_pdf_em_branco_disponivel_em_rascunho(ctx):
    app, _ = ctx
    checklist, _ = _novo(ctx)
    client = app.test_client()
    login(client)
    resp = client.get(
        f"/geradores/checklists/{checklist.id}/pdf?modo=branco"
    )
    assert resp.status_code == 200


def test_integridade_rejeita_ausencia_de_evento(ctx):
    checklist, _ = _novo(ctx)
    assert not conferir_integridade(checklist, [])


def test_migration_f5_aditiva_e_encadeada():
    texto = (
        Path(__file__).resolve().parents[2]
        / "migrations/versions/20261015_01_geradores_g5_historico_auditoria.py"
    ).read_text(encoding="utf-8")
    assert 'revision = "20261015_01"' in texto
    assert 'down_revision = "20261014_02"' in texto
    assert "op.create_table(" in texto
    assert "Downgrade bloqueado" in texto
    assert "op.alter_column" not in texto


def test_ausencia_de_commit_no_servico_de_auditoria():
    fonte = (
        Path(__file__).resolve().parents[2]
        / "app/geradores/gerador_checklist_auditoria_service.py"
    ).read_text(encoding="utf-8")
    assert "db.session.commit(" not in fonte
    assert "MovimentacaoEstoque" not in fonte
    assert "LancamentoFinanceiro" not in fonte
