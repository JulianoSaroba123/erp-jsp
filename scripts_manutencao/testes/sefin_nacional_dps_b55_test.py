from copy import deepcopy
from pathlib import Path
import runpy

from lxml import etree

from app.fiscal.xml.dps_serializer import (
    NAMESPACE_NFSE,
    VERSAO_DPS,
    montar_xml_dps,
    montar_xml_dps_serializado,
    serializar_xml,
)


def _carregar_helper(nome_arquivo, nome_funcao):
    caminho = Path(__file__).with_name(nome_arquivo)
    namespace = runpy.run_path(str(caminho))
    return namespace[nome_funcao]()


def _dados_base():
    return _carregar_helper(
        "sefin_nacional_dps_b54d_test.py",
        "_dados_base",
    )


def _dados_completos():
    dados = _dados_base()

    dados["ibs_cbs"] = {
        "fin_nfse": "0",
        "ind_final": "1",
        "c_ind_op": "010101",
        "ind_dest": "0",
        "cst": "000",
        "c_class_trib": "000001",
    }

    return dados


def _localname(elemento):
    return etree.QName(elemento).localname


def test_b55_001_mesma_dps_gera_mesmos_bytes():
    dados = _dados_completos()

    xml_1 = montar_xml_dps_serializado(dados)
    xml_2 = montar_xml_dps_serializado(dados)

    assert xml_1 == xml_2


def test_b55_002_saida_e_bytes_utf8():
    xml = montar_xml_dps_serializado(
        _dados_completos()
    )

    assert isinstance(xml, bytes)
    xml.decode("utf-8")


def test_b55_003_declaracao_xml_estavel():
    xml = montar_xml_dps_serializado(
        _dados_completos()
    )

    assert xml.startswith(
        b"<?xml version='1.0' encoding='UTF-8'?>"
    )


def test_b55_004_namespace_raiz_estavel():
    xml = montar_xml_dps_serializado(
        _dados_completos()
    )

    raiz = etree.fromstring(xml)

    assert etree.QName(raiz).localname == "DPS"
    assert etree.QName(raiz).namespace == NAMESPACE_NFSE

    assert raiz.nsmap.get(None) == NAMESPACE_NFSE


def test_b55_005_versao_dps_estavel():
    xml = montar_xml_dps_serializado(
        _dados_completos()
    )

    raiz = etree.fromstring(xml)

    assert raiz.get("versao") == VERSAO_DPS
    assert raiz.get("versao") == "1.01"


def test_b55_006_id_inf_dps_estavel():
    dados = _dados_completos()

    xml = montar_xml_dps_serializado(dados)

    raiz = etree.fromstring(xml)
    inf_dps = raiz[0]

    assert _localname(inf_dps) == "infDPS"

    assert inf_dps.get("Id") == (
        dados["identificacao"]["id"]
    )


def test_b55_007_ordem_identificacao_estavel():
    raiz = montar_xml_dps(
        _dados_completos()
    )

    inf_dps = raiz[0]

    nomes = [
        _localname(elemento)
        for elemento in inf_dps
    ]

    assert nomes[:8] == [
        "tpAmb",
        "dhEmi",
        "verAplic",
        "serie",
        "nDPS",
        "dCompet",
        "tpEmit",
        "cLocEmi",
    ]


def test_b55_008_ordem_grupos_principais_estavel():
    raiz = montar_xml_dps(
        _dados_completos()
    )

    inf_dps = raiz[0]

    nomes = [
        _localname(elemento)
        for elemento in inf_dps
    ]

    assert nomes.index("prest") < nomes.index("serv")
    assert nomes.index("serv") < nomes.index("valores")
    assert nomes.index("valores") < nomes.index("IBSCBS")

    if "toma" in nomes:
        assert nomes.index("prest") < nomes.index("toma")
        assert nomes.index("toma") < nomes.index("serv")


def test_b55_009_sem_pretty_print_variavel():
    xml = montar_xml_dps_serializado(
        _dados_completos()
    )

    assert b"\n  <" not in xml
    assert b"\r\n" not in xml


def test_b55_010_serializacao_direta_equivale_fronteira():
    dados = _dados_completos()

    arvore = montar_xml_dps(dados)

    assert (
        montar_xml_dps_serializado(dados)
        == serializar_xml(arvore)
    )


def test_b55_011_nao_muta_dps_canonica():
    dados = _dados_completos()
    original = deepcopy(dados)

    montar_xml_dps_serializado(dados)

    assert dados == original


def test_b55_012_duas_arvores_independentes_mesmos_bytes():
    dados = _dados_completos()

    arvore_1 = montar_xml_dps(
        deepcopy(dados)
    )

    arvore_2 = montar_xml_dps(
        deepcopy(dados)
    )

    assert (
        serializar_xml(arvore_1)
        == serializar_xml(arvore_2)
    )
