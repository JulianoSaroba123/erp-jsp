# -*- coding: utf-8 -*-
"""G5: testes do checklist genérico sem OS, sem gravação em produção."""
from pathlib import Path

import pytest

from app.geradores.gerador_checklist_catalogo import obter_modelo
from app.geradores.gerador_checklist_pdf_service import PDFChecklistError
from app.geradores.gerador_checklist_generico_pdf_service import (
    _FERRAMENTAS, _MATERIAIS, gerar_pdf_modelo_generico,
)
from scripts_manutencao.testes.geradores_g5_f3_checklist_digital_test import (
    ctx, login,
)

URL_TELA = "/geradores/checklists/modelo-generico"
URL_PDF = "/geradores/checklists/modelo-generico/pdf"


@pytest.mark.parametrize("tipo", ("BASICA", "INTERMEDIARIA", "AVANCADA"))
def test_pdf_generico_tres_niveis_sem_execucao_ou_os(tipo):
    """Gera diretamente do catálogo, sem depender de execução, IDs ou clientes."""
    assert obter_modelo(tipo)["secoes"]
    conteudo = gerar_pdf_modelo_generico(tipo)
    assert conteudo.startswith(b"%PDF-")
    assert b"%%EOF" in conteudo[-100:]
    assert len(conteudo) > 2500


@pytest.mark.parametrize("tipo", ("", "DESCONHECIDO", "../AVANCADA", "FISCAL"))
def test_tipo_nao_previsto_e_rejeitado(tipo):
    with pytest.raises(PDFChecklistError, match="inválido"):
        gerar_pdf_modelo_generico(tipo)


def test_lista_preparacao_contem_ferramentas_e_consumiveis():
    assert any("Multímetro" in x for x in _FERRAMENTAS)
    assert any("filtro" in x.lower() for x in _MATERIAIS)
    assert any("óleo" in x.lower() for x in _MATERIAIS)


def test_tela_e_pdf_exigem_login(ctx):
    app, _ = ctx
    cliente = app.test_client()
    assert cliente.get(URL_TELA).status_code == 302
    assert cliente.get(URL_PDF).status_code == 302


def test_usuario_nao_admin_nao_acessa(ctx):
    app, _ = ctx
    cliente = app.test_client()
    login(cliente, "comum_g5f3")
    assert cliente.get(URL_TELA).status_code == 403
    assert cliente.get(URL_PDF).status_code == 403


def test_admin_abre_tela_e_pdf_sem_parametro_de_os(ctx):
    app, _ = ctx
    cliente = app.test_client()
    login(cliente)
    pagina = cliente.get(URL_TELA)
    assert pagina.status_code == 200
    assert "Checklist genérico" in pagina.get_data(as_text=True)
    assert 'value="INTERMEDIARIA"' in pagina.get_data(as_text=True)
    pdf = cliente.get(URL_PDF + "?tipo=INTERMEDIARIA")
    assert pdf.status_code == 200
    assert pdf.mimetype == "application/pdf"
    assert pdf.data.startswith(b"%PDF-")
    assert "GENERICO_INTERMEDIARIA.pdf" in pdf.headers["Content-Disposition"]
    assert "no-store" in pdf.headers["Cache-Control"]
    assert pdf.headers["X-Content-Type-Options"] == "nosniff"


def test_tipo_invalido_retorna_400(ctx):
    app, _ = ctx
    cliente = app.test_client()
    login(cliente)
    assert cliente.get(URL_PDF + "?tipo=INCORRETO").status_code == 400


def test_exportacao_nao_aceita_post(ctx):
    app, _ = ctx
    cliente = app.test_client()
    login(cliente)
    assert cliente.post(URL_PDF, data={"tipo": "BASICA"}).status_code == 405


def test_servico_generico_nao_acessa_banco_ou_rede():
    raiz = Path(__file__).resolve().parents[2]
    origem = (
        raiz / "app/geradores/gerador_checklist_generico_pdf_service.py"
    ).read_text(encoding="utf-8")
    assert "db.session" not in origem
    assert "requests." not in origem
    assert "http://" not in origem
    assert "https://" not in origem
