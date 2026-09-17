"""Testes D24F02-B5.2 - raiz DPS e identificacao infDPS."""

import pytest
from lxml import etree

from app.fiscal.xml.dps_serializer import (
    NAMESPACE_NFSE,
    SerializacaoDpsInvalida,
    montar_xml_dps,
    serializar_xml,
)


ID_DPS = (
    "DPS"
    + "3554508"
    + "2"
    + "12345678000195"
    + "00001"
    + "000000000000123"
)


def _dps_canonica():
    assert len(ID_DPS) == 45

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
            "nome": "JSP TESTE",
            "regime_tributario": {
                "op_simp_nac": "1",
                "reg_ap_trib_sn": None,
                "reg_esp_trib": "0",
            },
        },
        "tomador": None,
        "servico": {
            "codigo_lista_nacional": "010101",
            "codigo_tributacao_municipal": "101",
            "nbs": "123456789",
            "descricao": "Servico de teste",
            "municipio_incidencia_ibge": "3554508",
            "municipio_prestacao_ibge": "3550308",
        },
        "valores": {
            "valor_servicos": "1500.00",
            "valor_recebido": "1500.00",
            "desconto_incondicionado": "0.00",
            "desconto_condicionado": "0.00",
            "deducoes": "0.00",
        },
    }


def _localname(elemento):
    return etree.QName(elemento).localname


def test_b52_001_cria_dps_com_versao_na_raiz():
    raiz = montar_xml_dps(_dps_canonica())

    assert _localname(raiz) == "DPS"
    assert raiz.get("versao") == "1.01"
    assert raiz.nsmap[None] == NAMESPACE_NFSE


def test_b52_002_inf_dps_recebe_id_canonico():
    raiz = montar_xml_dps(_dps_canonica())
    inf_dps = raiz[0]

    assert _localname(inf_dps) == "infDPS"
    assert inf_dps.get("Id") == ID_DPS

    # O XSD define versao em DPS, nao em infDPS.
    assert inf_dps.get("versao") is None


def test_b52_003_respeita_ordem_do_tc_inf_dps():
    raiz = montar_xml_dps(_dps_canonica())
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


def test_b52_004_mapeia_valores_canonicos():
    raiz = montar_xml_dps(_dps_canonica())
    inf_dps = raiz[0]

    valores = {
        _localname(elemento): elemento.text
        for elemento in inf_dps[:8]
    }

    assert valores == {
        "tpAmb": "2",
        "dhEmi": "2026-09-16T22:30:00-03:00",
        "verAplic": "ERP-JSP-3.0",
        "serie": "1",
        "nDPS": "123",
        "dCompet": "2026-09-16",
        "tpEmit": "1",
        "cLocEmi": "3554508",
    }


def test_b52_005_serializacao_mantem_namespace_padrao():
    raiz = montar_xml_dps(_dps_canonica())

    xml = serializar_xml(raiz)
    texto = xml.decode("utf-8")

    assert (
        'xmlns="http://www.sped.fazenda.gov.br/nfse"'
        in texto
    )

    assert 'versao="1.01"' in texto
    assert f'Id="{ID_DPS}"' in texto

    assert "ns0:" not in texto


def test_b52_006_rejeita_identificacao_incompleta():
    dados = _dps_canonica()

    dados["identificacao"].pop("dh_emi")

    with pytest.raises(
        SerializacaoDpsInvalida,
        match="identificacao.dh_emi",
    ):
        montar_xml_dps(dados)


def test_b52_007_rejeita_versao_layout_incompativel():
    dados = _dps_canonica()

    dados["identificacao"]["versao_layout"] = "1.00"

    with pytest.raises(
        SerializacaoDpsInvalida,
        match="Versao da DPS canonica incompativel",
    ):
        montar_xml_dps(dados)
