"""H4-F5 - serializador dual para Producao e Producao Restrita."""

from copy import deepcopy
from pathlib import Path
import runpy

import pytest
from lxml import etree

from app.fiscal.xsd import obter_caminho_xsd_dps
from app.fiscal.xml.dps_serializer import (
    SerializacaoDpsInvalida,
    montar_xml_dps,
    montar_xml_dps_serializado,
)
from app.fiscal.xml.dps_xsd_validator import validar_xml_dps_xsd


def _dados_completos():
    caminho = Path(__file__).with_name(
        "sefin_nacional_dps_b6_test.py"
    )
    namespace = runpy.run_path(str(caminho))
    return deepcopy(
        namespace["_dados_completos_xsd"]()
    )


def _localname(elemento):
    return etree.QName(elemento).localname


def _filho(pai, nome):
    for elemento in pai:
        if _localname(elemento) == nome:
            return elemento

    raise AssertionError(
        f"Elemento XML nao encontrado: {nome}"
    )


def _inf_dps(raiz):
    return _filho(
        raiz,
        "infDPS",
    )


def test_h4f5_001_producao_preserva_vdedred():
    dados = _dados_completos()
    dados["valores"]["deducoes"] = "100.00"

    raiz = montar_xml_dps(
        dados,
        ambiente="PRODUCAO",
    )

    valores = _filho(
        _inf_dps(raiz),
        "valores",
    )

    nomes = [
        _localname(elemento)
        for elemento in valores
    ]

    assert "vDedRed" in nomes
    assert "vAjusteBC" not in nomes

    v_ded_red = _filho(
        valores,
        "vDedRed",
    )

    assert _filho(
        v_ded_red,
        "vDR",
    ).text == "100.00"


def test_h4f5_002_homologacao_usa_vajustebc():
    dados = _dados_completos()
    dados["valores"]["deducoes"] = "100.00"

    raiz = montar_xml_dps(
        dados,
        ambiente="HOMOLOGACAO",
    )

    valores = _filho(
        _inf_dps(raiz),
        "valores",
    )

    nomes = [
        _localname(elemento)
        for elemento in valores
    ]

    assert "vAjusteBC" in nomes
    assert "vDedRed" not in nomes

    ajuste = _filho(
        valores,
        "vAjusteBC",
    )

    assert _filho(
        ajuste,
        "vAjusteBCISSQN",
    ).text == "100.00"


def test_h4f5_003_producao_preserva_ibscbs_legado():
    raiz = montar_xml_dps(
        _dados_completos(),
        ambiente="PRODUCAO",
    )

    ibs = _filho(
        _inf_dps(raiz),
        "IBSCBS",
    )

    assert _localname(ibs[0]) == "finNFSe"

    trib = _filho(
        _filho(
            ibs,
            "valores",
        ),
        "trib",
    )

    assert [
        _localname(elemento)
        for elemento in trib
    ] == [
        "gIBSCBS",
    ]

    g_ibs_cbs = _filho(
        trib,
        "gIBSCBS",
    )

    assert [
        _localname(elemento)
        for elemento in g_ibs_cbs
    ] == [
        "CST",
        "cClassTrib",
    ]


def test_h4f5_004_homologacao_reposiciona_ibscbs():
    raiz = montar_xml_dps(
        _dados_completos(),
        ambiente="HOMOLOGACAO",
    )

    inf_dps = _inf_dps(raiz)

    nomes_inf_dps = [
        _localname(elemento)
        for elemento in inf_dps
    ]

    assert nomes_inf_dps[
        nomes_inf_dps.index("tpEmit") + 1
    ] == "finNFSe"

    assert nomes_inf_dps[
        nomes_inf_dps.index("finNFSe") + 1
    ] == "cLocEmi"

    assert _filho(
        inf_dps,
        "finNFSe",
    ).text == "0"

    ibs = _filho(
        inf_dps,
        "IBSCBS",
    )

    nomes_ibs = [
        _localname(elemento)
        for elemento in ibs
    ]

    assert "finNFSe" not in nomes_ibs
    assert nomes_ibs == [
        "indFinal",
        "cIndOp",
        "indDest",
        "valores",
    ]

    trib = _filho(
        _filho(
            ibs,
            "valores",
        ),
        "trib",
    )

    assert [
        _localname(elemento)
        for elemento in trib
    ] == [
        "CST",
        "cClassTrib",
    ]

    assert _filho(
        trib,
        "CST",
    ).text == "000"

    assert _filho(
        trib,
        "cClassTrib",
    ).text == "000001"


def test_h4f5_005_xml_homologacao_valida_xsd_20261020():
    dados = _dados_completos()
    dados["valores"]["deducoes"] = "100.00"

    xml = montar_xml_dps_serializado(
        dados,
        ambiente="HOMOLOGACAO",
    )

    caminho_xsd = obter_caminho_xsd_dps(
        ambiente="HOMOLOGACAO"
    )

    resultado = validar_xml_dps_xsd(
        xml,
        caminho_xsd,
    )

    assert resultado.valido is True, resultado.erros


def test_h4f5_006_rejeita_ambiente_desconhecido():
    with pytest.raises(
        SerializacaoDpsInvalida,
        match="Ambiente de serializacao",
    ):
        montar_xml_dps(
            _dados_completos(),
            ambiente="DESCONHECIDO",
        )
