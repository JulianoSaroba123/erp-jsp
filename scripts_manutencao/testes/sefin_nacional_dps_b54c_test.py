"""D24F02-B5.4C - descontos e deducoes da DPS."""

import importlib.util
from pathlib import Path

from lxml import etree

from app.fiscal.xml.dps_serializer import montar_xml_dps


def _localname(elemento):
    return etree.QName(elemento).localname


def _filho(pai, nome):
    for elemento in pai:
        if _localname(elemento) == nome:
            return elemento

    raise AssertionError(
        f"Elemento XML nao encontrado: {nome}"
    )


def _dados_base():
    arquivo_b54b = Path(__file__).with_name(
        "sefin_nacional_dps_b54b_test.py"
    )

    spec = importlib.util.spec_from_file_location(
        "_sefin_nacional_dps_b54b_para_b54c",
        arquivo_b54b,
    )

    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    return modulo._dados_base()


def _valores(dados=None):
    raiz = montar_xml_dps(
        dados or _dados_base()
    )

    inf_dps = raiz[0]

    return _filho(
        inf_dps,
        "valores",
    )


def test_b54c_001_omite_descontos_e_deducoes_zerados():
    valores = _valores()

    nomes = [
        _localname(elemento)
        for elemento in valores
    ]

    assert nomes == [
        "vServPrest",
    ]


def test_b54c_002_serializa_desconto_incondicionado():
    dados = _dados_base()

    dados["valores"][
        "desconto_incondicionado"
    ] = "50.00"

    valores = _valores(dados)

    descontos = _filho(
        valores,
        "vDescCondIncond",
    )

    assert [
        _localname(elemento)
        for elemento in descontos
    ] == [
        "vDescIncond",
    ]

    assert descontos[0].text == "50.00"


def test_b54c_003_serializa_desconto_condicionado():
    dados = _dados_base()

    dados["valores"][
        "desconto_condicionado"
    ] = "25.00"

    valores = _valores(dados)

    descontos = _filho(
        valores,
        "vDescCondIncond",
    )

    assert [
        _localname(elemento)
        for elemento in descontos
    ] == [
        "vDescCond",
    ]

    assert descontos[0].text == "25.00"


def test_b54c_004_serializa_ambos_descontos_na_ordem_xsd():
    dados = _dados_base()

    dados["valores"][
        "desconto_incondicionado"
    ] = "50.00"

    dados["valores"][
        "desconto_condicionado"
    ] = "25.00"

    valores = _valores(dados)

    descontos = _filho(
        valores,
        "vDescCondIncond",
    )

    assert [
        _localname(elemento)
        for elemento in descontos
    ] == [
        "vDescIncond",
        "vDescCond",
    ]

    assert [
        elemento.text
        for elemento in descontos
    ] == [
        "50.00",
        "25.00",
    ]


def test_b54c_005_serializa_deducao_monetaria_em_vdr():
    dados = _dados_base()

    dados["valores"]["deducoes"] = "100.00"

    valores = _valores(dados)

    deducoes = _filho(
        valores,
        "vDedRed",
    )

    assert [
        _localname(elemento)
        for elemento in deducoes
    ] == [
        "vDR",
    ]

    assert deducoes[0].text == "100.00"


def test_b54c_006_respeita_ordem_tc_info_valores():
    dados = _dados_base()

    dados["valores"][
        "desconto_incondicionado"
    ] = "50.00"

    dados["valores"]["deducoes"] = "100.00"

    valores = _valores(dados)

    assert [
        _localname(elemento)
        for elemento in valores
    ] == [
        "vServPrest",
        "vDescCondIncond",
        "vDedRed",
    ]


def test_b54c_007_zero_em_formatos_equivalentes_e_omitido():
    dados = _dados_base()

    dados["valores"][
        "desconto_incondicionado"
    ] = "0"

    dados["valores"][
        "desconto_condicionado"
    ] = "0.0"

    dados["valores"]["deducoes"] = "0.00"

    valores = _valores(dados)

    assert [
        _localname(elemento)
        for elemento in valores
    ] == [
        "vServPrest",
    ]
