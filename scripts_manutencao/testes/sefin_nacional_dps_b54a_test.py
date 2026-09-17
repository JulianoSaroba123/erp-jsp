"""Testes D24F02-B5.4A - servico XML."""

import importlib.util
from pathlib import Path

import pytest
from lxml import etree

from app.fiscal.providers.sefin_nacional_dps import (
    DpsCanonicaInvalida,
    montar_dps_canonica,
)
from app.fiscal.xml.dps_serializer import (
    SerializacaoDpsInvalida,
    montar_xml_dps,
)


ID_DPS = (
    "DPS"
    + "3554508"
    + "2"
    + "12345678000195"
    + "00001"
    + "000000000000123"
)


def _dados_provider_base():
    arquivo_b42 = Path(__file__).with_name(
        "sefin_nacional_dps_b42_test.py"
    )

    spec = importlib.util.spec_from_file_location(
        "_sefin_nacional_dps_b42_para_b54a",
        arquivo_b42,
    )

    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    return modulo._dados_base()


def _localname(elemento):
    return etree.QName(elemento).localname


def _filho(pai, nome):
    for elemento in pai:
        if _localname(elemento) == nome:
            return elemento

    raise AssertionError(
        f"Elemento XML nao encontrado: {nome}"
    )


def _dps_canonica():
    return {
        "identificacao": {
            "id": ID_DPS,
            "ambiente": "HOMOLOGACAO",
            "tp_amb": "2",
            "dh_emi": "2026-09-16T22:30:00-03:00",
            "versao_layout": "1.01",
            "versao_aplicativo": "ERP-JSP-3.0",
            "serie": "1",
            "numero_dps": "123",
            "competencia": "2026-09-16",
            "tipo_emitente": "1",
            "municipio_emissao_ibge": "3554508",
        },
        "prestador": {
            "tipo_documento": "CNPJ",
            "documento": "12345678000195",
            "inscricao_municipal": "123456",
            "nome": "JSP ELETRICA INDUSTRIAL",
            "regime_tributario": {
                "op_simp_nac": "3",
                "reg_ap_trib_sn": "1",
                "reg_esp_trib": "0",
            },
        },
        "tomador": None,
        "servico": {
            "codigo_lista_nacional": "010101",
            "codigo_tributacao_municipal": "101",
            "nbs": "123456789",
            "descricao": "Manutencao eletrica industrial",
            "municipio_incidencia_ibge": "3554508",
            "municipio_prestacao_ibge": "3550308",
        },
    }


def _inf_dps(dados=None):
    raiz = montar_xml_dps(
        dados or _dps_canonica()
    )
    return raiz[0]


def test_b54a_001_servico_entra_apos_prestador():
    inf_dps = _inf_dps()

    nomes = [
        _localname(elemento)
        for elemento in inf_dps
    ]

    assert nomes[-2:] == [
        "prest",
        "serv",
    ]


def test_b54a_002_tc_serv_respeita_ordem_xsd():
    serv = _filho(
        _inf_dps(),
        "serv",
    )

    assert [
        _localname(elemento)
        for elemento in serv
    ] == [
        "locPrest",
        "cServ",
    ]


def test_b54a_003_local_prestacao_usa_campo_proprio():
    serv = _filho(
        _inf_dps(),
        "serv",
    )

    loc_prest = _filho(
        serv,
        "locPrest",
    )

    assert [
        _localname(elemento)
        for elemento in loc_prest
    ] == [
        "cLocPrestacao",
    ]

    assert loc_prest[0].text == "3550308"


def test_b54a_004_nao_usa_municipio_incidencia_como_fallback():
    dados = _dps_canonica()

    dados["servico"].pop(
        "municipio_prestacao_ibge"
    )

    assert (
        dados["servico"]["municipio_incidencia_ibge"]
        == "3554508"
    )

    with pytest.raises(
        SerializacaoDpsInvalida,
        match="servico.municipio_prestacao_ibge",
    ):
        montar_xml_dps(dados)


def test_b54a_005_codigo_servico_respeita_ordem_xsd():
    serv = _filho(
        _inf_dps(),
        "serv",
    )

    c_serv = _filho(
        serv,
        "cServ",
    )

    assert [
        _localname(elemento)
        for elemento in c_serv
    ] == [
        "cTribNac",
        "cTribMun",
        "xDescServ",
        "cNBS",
    ]

    assert [
        elemento.text
        for elemento in c_serv
    ] == [
        "010101",
        "101",
        "Manutencao eletrica industrial",
        "123456789",
    ]


def test_b54a_006_codigo_municipal_pode_ser_omitido():
    dados = _dps_canonica()

    dados["servico"][
        "codigo_tributacao_municipal"
    ] = None

    serv = _filho(
        _inf_dps(dados),
        "serv",
    )

    c_serv = _filho(
        serv,
        "cServ",
    )

    assert "cTribMun" not in [
        _localname(elemento)
        for elemento in c_serv
    ]


def test_b54a_007_nbs_pode_ser_omitido():
    dados = _dps_canonica()
    dados["servico"]["nbs"] = None

    serv = _filho(
        _inf_dps(dados),
        "serv",
    )

    c_serv = _filho(
        serv,
        "cServ",
    )

    assert "cNBS" not in [
        _localname(elemento)
        for elemento in c_serv
    ]


def test_b54a_008_nao_serializa_municipio_incidencia():
    serv = _filho(
        _inf_dps(),
        "serv",
    )

    xml_texto = etree.tostring(
        serv,
        encoding="unicode",
    )

    assert "3550308" in xml_texto
    assert "3554508" not in xml_texto

def test_b54a_009_provider_preserva_municipio_prestacao():
    dados = _dados_provider_base()

    dados["servico"][
        "municipio_prestacao_ibge"
    ] = "3550308"

    dps = montar_dps_canonica(**dados)

    assert (
        dps["servico"]["municipio_prestacao_ibge"]
        == "3550308"
    )

    # Comprova tambem a passagem canonico -> XML.
    raiz = montar_xml_dps(dps)
    inf_dps = raiz[0]

    serv = _filho(
        inf_dps,
        "serv",
    )

    loc_prest = _filho(
        serv,
        "locPrest",
    )

    assert (
        _filho(
            loc_prest,
            "cLocPrestacao",
        ).text
        == "3550308"
    )


def test_b54a_010_provider_rejeita_municipio_prestacao_invalido():
    dados = _dados_provider_base()

    dados["servico"][
        "municipio_prestacao_ibge"
    ] = "355030"

    with pytest.raises(
        DpsCanonicaInvalida,
        match="Municipio de prestacao invalido",
    ):
        montar_dps_canonica(**dados)


def test_b54a_011_provider_mantem_compatibilidade_sem_campo():
    dados = _dados_provider_base()

    dados["servico"].pop(
        "municipio_prestacao_ibge",
        None,
    )

    dps = montar_dps_canonica(**dados)

    assert (
        "municipio_prestacao_ibge"
        not in dps["servico"]
    )

    assert (
        dps["servico"]["municipio_incidencia_ibge"]
        is not None
    )
