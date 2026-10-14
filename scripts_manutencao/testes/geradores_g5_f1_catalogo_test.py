# -*- coding: utf-8 -*-
"""Regressão G5-F1: catálogo puro, sem banco, rotas ou PDF em produção."""
import importlib.util
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FONTE = ROOT / "app/geradores/gerador_checklist_catalogo.py"


@pytest.fixture
def g5():
    spec = importlib.util.spec_from_file_location("jsp_g5_catalogo_puro", FONTE)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def IDs(g5, tipo):
    return set(g5.itens_do_modelo(tipo))


def respostas_validas(g5, tipo):
    resposta = {}
    for item_id, item in g5.itens_do_modelo(tipo).items():
        resposta[item_id] = {
            "status": "CONFORME",
            "medicao": "12,5" if item["unidade"] else "",
            "observacao": "",
        }
    return resposta


def test_tres_niveis_ja_existentes_no_g3(g5):
    assert g5.TIPOS == ("BASICA", "INTERMEDIARIA", "AVANCADA")


def test_basica_possui_secoes_e_itens_de_seguranca(g5):
    modelo = g5.obter_modelo("BASICA")
    assert modelo["versao"] == "G5-1.0"
    assert "SEG_EPI" in IDs(g5, "BASICA")
    assert "MOT_HORIMETRO" in IDs(g5, "BASICA")
    assert len(modelo["secoes"]) >= 5


def test_intermediaria_inclui_itens_da_basica(g5):
    assert IDs(g5, "BASICA") < IDs(g5, "INTERMEDIARIA")
    assert "MOT_TROCA_OLEO" in IDs(g5, "INTERMEDIARIA")
    assert "CTL_BACKUP" in IDs(g5, "INTERMEDIARIA")
    assert "PROT_PRESSAO" in IDs(g5, "INTERMEDIARIA")


def test_avancada_inclui_intermediaria(g5):
    assert IDs(g5, "INTERMEDIARIA") < IDs(g5, "AVANCADA")
    assert "QTA_TRANSFERENCIA" in IDs(g5, "AVANCADA")


def test_codigos_de_itens_unicos_nas_tres_versoes(g5):
    for tipo in g5.TIPOS:
        modelo = g5.obter_modelo(tipo)
        ids = [i["id"] for secao in modelo["secoes"] for i in secao["itens"]]
        assert len(ids) == len(set(ids))


def test_tipo_invalido_rejeitado(g5):
    for valor in ("EXTRA", "EMERGENCIA", "", None):
        with pytest.raises(g5.ChecklistDominioError):
            g5.obter_modelo(valor)


def test_normalizacao_do_tipo(g5):
    assert g5.obter_modelo(" intermediaria ")["tipo"] == "INTERMEDIARIA"


def test_modelos_nao_compartilham_estado_mutavel(g5):
    primeiro = g5.obter_modelo("BASICA")
    primeiro["secoes"][0]["itens"][0]["descricao"] = "ALTERADO"
    segundo = g5.obter_modelo("BASICA")
    assert segundo["secoes"][0]["itens"][0]["descricao"] != "ALTERADO"


def test_rascunho_nao_assinala_conformidade_automaticamente(g5):
    snapshot = g5.validar_respostas("BASICA", {})
    assert snapshot["apto_para_encerramento"] is False
    assert all(i["status"] is None for i in snapshot["respostas"])


def test_conclusao_exige_todos_os_itens_classificados(g5):
    with pytest.raises(g5.ChecklistDominioError, match="não avaliado"):
        g5.validar_respostas("BASICA", {}, encerrar=True)


def test_conclusao_aceita_status_validos_com_medicoes(g5):
    snapshot = g5.validar_respostas(
        "BASICA", respostas_validas(g5, "BASICA"), encerrar=True
    )
    assert snapshot["apto_para_encerramento"] is True
    assert snapshot["versao_modelo"] == g5.VERSAO_CATALOGO
    assert all(r["status"] == "CONFORME" for r in snapshot["respostas"])


@pytest.mark.parametrize("status", ["NAO_CONFORME", "NAO_APLICAVEL", "NAO_REALIZADO"])
def test_excecoes_exigem_justificativa_no_fechamento(g5, status):
    respostas = respostas_validas(g5, "BASICA")
    respostas["SEG_EPI"] = {"status": status, "observacao": ""}
    with pytest.raises(g5.ChecklistDominioError, match="justificativa"):
        g5.validar_respostas("BASICA", respostas, encerrar=True)


def test_excecao_justificada_permanece_explicita_no_pdf_futuro(g5):
    respostas = respostas_validas(g5, "BASICA")
    respostas["SEG_EPI"] = {
        "status": "NAO_REALIZADO",
        "observacao": "Acesso ao local não autorizado.",
    }
    snapshot = g5.validar_respostas("BASICA", respostas, encerrar=True)
    linha = next(x for x in snapshot["respostas"] if x["item_id"] == "SEG_EPI")
    assert linha["status"] == "NAO_REALIZADO"
    assert "não autorizado" in linha["observacao"]


def test_medicao_obrigatoria_em_conclusao_de_item_mensuravel(g5):
    respostas = respostas_validas(g5, "BASICA")
    respostas["MOT_HORIMETRO"]["medicao"] = ""
    with pytest.raises(g5.ChecklistDominioError, match="medição obrigatória"):
        g5.validar_respostas("BASICA", respostas, encerrar=True)


def test_medido_com_virgula_pt_br_normaliza_para_decimal(g5):
    snapshot = g5.validar_respostas("BASICA", {
        "MOT_HORIMETRO": {"status": "CONFORME", "medicao": "1,50"}
    })
    r = next(x for x in snapshot["respostas"] if x["item_id"] == "MOT_HORIMETRO")
    assert r["medicao"] == "1.50"
    assert r["unidade"] == "h"


@pytest.mark.parametrize("valor", ["nan", "inf", "1e1000000", "12/5", "abc", "1,2,3"])
def test_medicao_invalida_rejeitada(g5, valor):
    with pytest.raises(g5.ChecklistDominioError, match="numérica"):
        g5.validar_respostas(
            "BASICA", {"MOT_HORIMETRO": {"status": "CONFORME", "medicao": valor}}
        )


def test_nao_aceita_medicao_em_inspecao_sem_unidade(g5):
    with pytest.raises(g5.ChecklistDominioError, match="não admite medição"):
        g5.validar_respostas(
            "BASICA", {"SEG_EPI": {"status": "CONFORME", "medicao": "220"}}
        )


def test_rejeita_item_fora_do_tipo_do_plano(g5):
    with pytest.raises(g5.ChecklistDominioError, match="não previsto"):
        g5.validar_respostas("BASICA", {"QTA_TRANSFERENCIA": {}})


def test_rejeita_status_desconhecido(g5):
    with pytest.raises(g5.ChecklistDominioError, match="status inválido"):
        g5.validar_respostas("BASICA", {"SEG_EPI": {"status": "OK"}})


def test_rejeita_campos_extras(g5):
    with pytest.raises(g5.ChecklistDominioError, match="campo não reconhecido"):
        g5.validar_respostas("BASICA", {"SEG_EPI": {"valor_pago": 100}})


def test_rejeita_payload_de_item_malformado(g5):
    with pytest.raises(g5.ChecklistDominioError, match="resposta inválida"):
        g5.validar_respostas("BASICA", {"SEG_EPI": []})


def test_rejeita_notas_excessivamente_longas(g5):
    with pytest.raises(g5.ChecklistDominioError, match="excedido"):
        g5.validar_respostas(
            "BASICA", {"SEG_EPI": {"observacao": "x" * (g5.MAX_OBSERVACAO + 1)}}
        )


def test_respostas_de_entrada_nao_sao_modificadas(g5):
    respostas = {"MOT_HORIMETRO": {"status": "CONFORME", "medicao": "1,5"}}
    g5.validar_respostas("BASICA", respostas)
    assert respostas["MOT_HORIMETRO"]["medicao"] == "1,5"


def test_nao_ha_escrita_banco_flask_rotas_ou_pdf_nesta_fase(g5):
    codigo = FONTE.read_text(encoding="utf-8")
    proibidos = (
        "db.session", "db.create_all", "sqlalchemy", "flask",
        ".write_pdf(", "@bp.", "request.form", "Gerador.query",
    )
    # Comentários/docstrings podem mencionar Flask/SQLAlchemy;
    # o contrato real é não importar nem executar suas APIs.
    for termo in proibidos:
        if termo in {"flask", "sqlalchemy"}:
            assert f"import {termo}" not in codigo
            assert f"from {termo}" not in codigo
        else:
            assert termo not in codigo
