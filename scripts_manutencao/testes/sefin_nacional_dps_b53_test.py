"""Testes D24F02-B5.3 - prestador e tomador XML."""

import pytest
from lxml import etree

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


def _localname(elemento):
    return etree.QName(elemento).localname


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
            "municipio_ibge": "3554508",
            "nome": "JSP ELETRICA INDUSTRIAL",
            "regime_tributario": {
                "op_simp_nac": "3",
                "reg_ap_trib_sn": "1",
                "reg_esp_trib": "0",
            },
        },
        "tomador": {
            "tipo_documento": "CNPJ",
            "documento": "98765432000110",
            "nome": "CLIENTE TESTE LTDA",
            "email": "cliente@example.com",
            "endereco": {
                "cep": "18530000",
                "logradouro": "Rua Teste",
                "numero": "100",
                "complemento": None,
                "bairro": "Centro",
                "cidade": "Tiete",
                "uf": "SP",
                "pais": "BR",
            },
        },
    }


def _inf_dps(dados=None):
    raiz = montar_xml_dps(
        dados or _dps_canonica()
    )
    return raiz[0]


def test_b53_001_prestador_respeita_ordem_xsd():
    inf_dps = _inf_dps()
    prest = inf_dps[-2]

    assert _localname(prest) == "prest"

    assert [
        _localname(elemento)
        for elemento in prest
    ] == [
        "CNPJ",
        "IM",
        "xNome",
        "regTrib",
    ]

    assert prest[0].text == "12345678000195"
    assert prest[1].text == "123456"
    assert prest[2].text == "JSP ELETRICA INDUSTRIAL"


def test_b53_002_regime_tributario_respeita_tc_reg_trib():
    inf_dps = _inf_dps()
    prest = inf_dps[-2]
    reg_trib = prest[-1]

    assert _localname(reg_trib) == "regTrib"

    assert [
        _localname(elemento)
        for elemento in reg_trib
    ] == [
        "opSimpNac",
        "regApTribSN",
        "regEspTrib",
    ]

    assert [
        elemento.text
        for elemento in reg_trib
    ] == [
        "3",
        "1",
        "0",
    ]


def test_b53_003_reg_ap_trib_sn_pode_ser_omitido():
    dados = _dps_canonica()

    dados["prestador"]["regime_tributario"][
        "reg_ap_trib_sn"
    ] = None

    inf_dps = _inf_dps(dados)
    reg_trib = inf_dps[-2][-1]

    assert [
        _localname(elemento)
        for elemento in reg_trib
    ] == [
        "opSimpNac",
        "regEspTrib",
    ]


def test_b53_004_tomador_cnpj_nome_email():
    inf_dps = _inf_dps()
    toma = inf_dps[-1]

    assert _localname(toma) == "toma"

    assert [
        _localname(elemento)
        for elemento in toma
    ] == [
        "CNPJ",
        "xNome",
        "email",
    ]

    assert toma[0].text == "98765432000110"
    assert toma[1].text == "CLIENTE TESTE LTDA"
    assert toma[2].text == "cliente@example.com"


def test_b53_005_tomador_pode_ser_cpf():
    dados = _dps_canonica()

    dados["tomador"]["tipo_documento"] = "CPF"
    dados["tomador"]["documento"] = "12345678901"

    toma = _inf_dps(dados)[-1]

    assert _localname(toma[0]) == "CPF"
    assert toma[0].text == "12345678901"

    assert all(
        _localname(elemento) != "CNPJ"
        for elemento in toma
    )


def test_b53_006_tomador_pode_ser_omitido():
    dados = _dps_canonica()
    dados["tomador"] = None

    inf_dps = _inf_dps(dados)

    nomes = [
        _localname(elemento)
        for elemento in inf_dps
    ]

    assert "prest" in nomes
    assert "toma" not in nomes


def test_b53_007_rejeita_tipo_documento_nao_suportado():
    dados = _dps_canonica()

    dados["prestador"]["tipo_documento"] = "NIF"

    with pytest.raises(
        SerializacaoDpsInvalida,
        match="Tipo de documento nao suportado",
    ):
        montar_xml_dps(dados)


def test_b53_008_rejeita_regime_tributario_ausente():
    dados = _dps_canonica()
    dados["prestador"]["regime_tributario"] = None

    with pytest.raises(
        SerializacaoDpsInvalida,
        match="regime_tributario",
    ):
        montar_xml_dps(dados)


def test_b53_009_nao_inventa_endereco_nacional():
    inf_dps = _inf_dps()
    toma = inf_dps[-1]

    nomes = [
        _localname(elemento)
        for elemento in toma
    ]

    assert "end" not in nomes
