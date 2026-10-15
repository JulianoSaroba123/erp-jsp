# -*- coding: utf-8 -*-
"""G5-F4: regressão de PDFs A4 e controle HTTP, só SQLite descartável."""
from pathlib import Path

import pytest
from app.extensoes import db
from app.geradores.gerador_model import Gerador
from app.geradores.gerador_checklist_execucao_service import (
    criar_checklist, salvar_checklist,
)
from app.geradores.gerador_checklist_pdf_service import (
    PDFChecklistError, _seguro, _verificar_snapshot,
    gerar_pdf_checklist,
)

# Fixture de dados fictícios já homologada na F3, reutilizada sem
# duplicar dados e sem consultar qualquer serviço externo.
from scripts_manutencao.testes.geradores_g5_f3_checklist_digital_test import (
    ctx, login, resposta_para,
)


def novo_checklist(ctx, tipo="BASICA"):
    _, ids = ctx
    ex, criado = criar_checklist(
        ids["v1"], tipo, usuario_id=ids["admin"]
    )
    assert criado
    db.session.commit()
    return ex, ids


def concluir(ex, ids):
    salvar_checklist(
        ex.id, resposta_para(ex.tipo_plano),
        usuario_id=ids["admin"], concluir=True,
        observacoes_gerais="Resultados conferidos em campo pela equipe.",
    )
    db.session.commit()


def test_pdf_branco_valido_em_rascunho(ctx):
    ex, _ = novo_checklist(ctx)
    conteudo = gerar_pdf_checklist(ex, modo="branco")
    assert conteudo.startswith(b"%PDF-")
    assert b"%%EOF" in conteudo[-100:]
    assert len(conteudo) > 2500


def test_pdf_em_branco_nao_inclui_respostas(ctx):
    ex, _ = novo_checklist(ctx)
    salvar_checklist(
        ex.id,
        {"SEG_EPI": {"status": "NAO_CONFORME", "observacao": "Anomalia"} },
        usuario_id=ex.criado_por_id,
    )
    _, _, mapa = _verificar_snapshot(ex, "branco")
    assert mapa == {}
    assert gerar_pdf_checklist(ex, modo="branco").startswith(b"%PDF-")


def test_pdf_preenchido_bloqueado_antes_da_conclusao(ctx):
    ex, _ = novo_checklist(ctx)
    with pytest.raises(PDFChecklistError, match="somente após conclusão"):
        gerar_pdf_checklist(ex, modo="preenchido")


def test_pdf_preenchido_valido_apos_conclusao(ctx):
    ex, ids = novo_checklist(ctx, "INTERMEDIARIA")
    concluir(ex, ids)
    pdf = gerar_pdf_checklist(ex, modo="preenchido")
    assert pdf.startswith(b"%PDF-")
    assert b"%%EOF" in pdf[-100:]
    assert len(pdf) > 2500


def test_tres_niveis_pdf_branco(ctx):
    _, ids = ctx
    for tipo in ("BASICA", "INTERMEDIARIA", "AVANCADA"):
        ex, _ = criar_checklist(
            ids["v1"], tipo, usuario_id=ids["admin"],
        )
        db.session.commit()
        pdf = gerar_pdf_checklist(ex, modo="branco")
        assert pdf.startswith(b"%PDF-")


def test_pdf_preenchido_preserva_nao_conforme(ctx):
    ex, ids = novo_checklist(ctx)
    registros = resposta_para("BASICA")
    registros["SEG_EPI"] = {
        "status": "NAO_CONFORME",
        "observacao": "Proteção individual inadequada.",
    }
    salvar_checklist(
        ex.id, registros, usuario_id=ids["admin"], concluir=True
    )
    db.session.commit()
    _, _, mapa = _verificar_snapshot(ex, "preenchido")
    assert mapa["SEG_EPI"]["status"] == "NAO_CONFORME"
    assert "inadequada" in mapa["SEG_EPI"]["observacao"]
    assert gerar_pdf_checklist(ex, modo="preenchido").startswith(b"%PDF-")


def test_pdf_rejeita_resultado_tamperado(ctx):
    ex, ids = novo_checklist(ctx)
    concluir(ex, ids)
    ex.respostas_snapshot = {"apto_para_encerramento": True, "respostas": []}
    with pytest.raises(PDFChecklistError, match="não correspondem"):
        gerar_pdf_checklist(ex, modo="preenchido")


def test_pdf_rejeita_modelo_inconsistente(ctx):
    ex, _ = novo_checklist(ctx)
    modelo = dict(ex.modelo_snapshot)
    modelo["versao"] = "MODIFICADO"
    ex.modelo_snapshot = modelo
    with pytest.raises(PDFChecklistError, match="Versão"):
        gerar_pdf_checklist(ex, modo="branco")


@pytest.mark.parametrize("modo", ["desconhecido", "", None, "branco/../", "json"])
def test_modo_desconhecido_rejeitado(ctx, modo):
    ex, _ = novo_checklist(ctx)
    with pytest.raises(PDFChecklistError, match="Modo"):
        gerar_pdf_checklist(ex, modo=modo)


def test_html_do_cadastro_escapado(ctx):
    ex, _ = novo_checklist(ctx)
    identificacao = dict(ex.identificacao_snapshot)
    gerador = dict(identificacao["gerador"])
    gerador["modelo"] = "<script>alert('x')</script> & TESTE"
    identificacao["gerador"] = gerador
    ex.identificacao_snapshot = identificacao
    assert "&lt;script&gt;" in _seguro(gerador["modelo"])
    assert gerar_pdf_checklist(ex, modo="branco").startswith(b"%PDF-")


def test_nao_autenticado_nao_baixa_pdf(ctx):
    app, ids = ctx
    ex, _ = novo_checklist(ctx)
    client = app.test_client()
    assert client.get(
        f"/geradores/checklists/{ex.id}/pdf?modo=branco"
    ).status_code == 302


def test_usuario_comum_nao_gera_pdf(ctx):
    app, _ = ctx
    ex, _ = novo_checklist(ctx)
    client = app.test_client()
    login(client, "comum_g5f3")
    assert client.get(
        f"/geradores/checklists/{ex.id}/pdf?modo=branco"
    ).status_code == 403


def test_http_branco_status_headers_e_bytes(ctx):
    app, ids = ctx
    ex, _ = novo_checklist(ctx)
    client = app.test_client()
    login(client)
    resposta = client.get(
        f"/geradores/checklists/{ex.id}/pdf?modo=branco"
    )
    assert resposta.status_code == 200
    assert resposta.mimetype == "application/pdf"
    assert resposta.data.startswith(b"%PDF-")
    assert "EM_BRANCO.pdf" in resposta.headers["Content-Disposition"]
    assert "no-store" in resposta.headers["Cache-Control"]
    assert resposta.headers["X-Content-Type-Options"] == "nosniff"


def test_http_preenchido_rascunho_409(ctx):
    app, _ = ctx
    ex, _ = novo_checklist(ctx)
    client = app.test_client()
    login(client)
    assert client.get(
        f"/geradores/checklists/{ex.id}/pdf?modo=preenchido"
    ).status_code == 409


def test_http_preenchido_concluido_200(ctx):
    app, ids = ctx
    ex, _ = novo_checklist(ctx)
    concluir(ex, ids)
    client = app.test_client()
    login(client)
    resposta = client.get(
        f"/geradores/checklists/{ex.id}/pdf?modo=preenchido"
    )
    assert resposta.status_code == 200
    assert resposta.data.startswith(b"%PDF-")
    assert "PREENCHIDO.pdf" in resposta.headers["Content-Disposition"]


def test_http_modo_invalido_400(ctx):
    app, _ = ctx
    ex, _ = novo_checklist(ctx)
    client = app.test_client()
    login(client)
    assert client.get(
        f"/geradores/checklists/{ex.id}/pdf?modo=invalido"
    ).status_code == 400


def test_http_id_inexistente_404(ctx):
    app, _ = ctx
    client = app.test_client()
    login(client)
    assert client.get(
        "/geradores/checklists/999999999/pdf?modo=branco"
    ).status_code == 404


def test_pdf_concluido_continua_disponivel_apos_inativar_gerador(ctx):
    app, ids = ctx
    ex, _ = novo_checklist(ctx)
    concluir(ex, ids)
    gerador = db.session.get(Gerador, ids["g1"])
    gerador.ativo = False
    db.session.commit()
    client = app.test_client()
    login(client)
    assert client.get(
        f"/geradores/checklists/{ex.id}/pdf?modo=preenchido"
    ).status_code == 200


def test_pdf_service_sem_db_e_sem_rede():
    raiz = Path(__file__).resolve().parents[2]
    fonte = (
        raiz / "app/geradores/gerador_checklist_pdf_service.py"
    ).read_text(encoding="utf-8")
    assert "db.session" not in fonte
    assert "http://" not in fonte
    assert "https://" not in fonte
    assert "requests." not in fonte
    assert "ReportLab" in fonte


def test_pdf_routes_somente_get(ctx):
    app, _ = ctx
    ex, _ = novo_checklist(ctx)
    client = app.test_client()
    login(client)
    assert client.post(
        f"/geradores/checklists/{ex.id}/pdf?modo=branco"
    ).status_code == 405
