"""D24F02-B5.4B - valores basicos da DPS."""

import importlib.util
from pathlib import Path

import pytest
from lxml import etree

from app.fiscal.xml.dps_serializer import (
    SerializacaoDpsInvalida,
    montar_xml_dps,
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


def _dados_base():
    arquivo_b54a = Path(__file__).with_name(
        "sefin_nacional_dps_b54a_test.py"
    )

    spec = importlib.util.spec_from_file_location(
        "_sefin_nacional_dps_b54a_para_b54b",
        arquivo_b54a,
    )

    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    return modulo._dps_canonica()


def _inf_dps(dados=None):
    raiz = montar_xml_dps(
        dados or _dados_base()
    )
    return raiz[0]


def test_b54b_001_valores_entra_apos_servico():
    inf_dps = _inf_dps()

    nomes = [
        _localname(elemento)
        for elemento in inf_dps
    ]

    assert nomes[-2:] == [
        "serv",
        "valores",
    ]


def test_b54b_002_cria_v_serv_prest_com_v_serv():
    valores = _filho(
        _inf_dps(),
        "valores",
    )

    assert [
        _localname(elemento)
        for elemento in valores
    ] == [
        "vServPrest",
    ]

    v_serv_prest = _filho(
        valores,
        "vServPrest",
    )

    assert [
        _localname(elemento)
        for elemento in v_serv_prest
    ] == [
        "vServ",
    ]

    assert (
        _filho(
            v_serv_prest,
            "vServ",
        ).text
        == "1500.00"
    )


def test_b54b_003_nao_mapeia_valor_recebido_para_v_receb():
    dados = _dados_base()

    dados["valores"]["valor_recebido"] = "999.99"

    valores = _filho(
        _inf_dps(dados),
        "valores",
    )

    v_serv_prest = _filho(
        valores,
        "vServPrest",
    )

    nomes = [
        _localname(elemento)
        for elemento in v_serv_prest
    ]

    assert "vReceb" not in nomes

    assert "999.99" not in [
        elemento.text
        for elemento in v_serv_prest
    ]


def test_b54b_004_rejeita_valores_ausentes():
    dados = _dados_base()
    dados.pop("valores")

    with pytest.raises(
        SerializacaoDpsInvalida,
        match="Grupo valores",
    ):
        montar_xml_dps(dados)


def test_b54b_005_rejeita_valor_servicos_ausente():
    dados = _dados_base()

    dados["valores"].pop(
        "valor_servicos"
    )

    with pytest.raises(
        SerializacaoDpsInvalida,
        match="valores.valor_servicos",
    ):
        montar_xml_dps(dados)
