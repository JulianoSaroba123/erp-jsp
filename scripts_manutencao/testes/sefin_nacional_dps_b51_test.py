"""Testes D24F02-B5.1 - fundacao do serializador XML."""

from lxml import etree

from app.fiscal.xml.dps_serializer import (
    NAMESPACE_NFSE,
    VERSAO_DPS,
    criar_elemento_nfse,
    serializar_xml,
)


def test_b51_001_namespace_oficial():
    assert NAMESPACE_NFSE == (
        "http://www.sped.fazenda.gov.br/nfse"
    )


def test_b51_002_versao_dps():
    assert VERSAO_DPS == "1.01"


def test_b51_003_cria_raiz_com_namespace_padrao():
    raiz = criar_elemento_nfse(
        "DPS",
        raiz=True,
    )

    assert raiz.tag == (
        f"{{{NAMESPACE_NFSE}}}DPS"
    )

    assert raiz.nsmap[None] == NAMESPACE_NFSE


def test_b51_004_cria_elemento_com_atributos():
    elemento = criar_elemento_nfse(
        "infDPS",
        Id="DPS123",
        versao=VERSAO_DPS,
    )

    assert elemento.tag == (
        f"{{{NAMESPACE_NFSE}}}infDPS"
    )

    assert elemento.get("Id") == "DPS123"
    assert elemento.get("versao") == "1.01"


def test_b51_005_serializa_utf8_com_declaracao():
    raiz = criar_elemento_nfse(
        "DPS",
        raiz=True,
    )

    xml = serializar_xml(raiz)

    assert isinstance(xml, bytes)
    assert xml.startswith(
        b"<?xml version='1.0' encoding='UTF-8'?>"
    )

    texto = xml.decode("utf-8")

    assert (
        'xmlns="http://www.sped.fazenda.gov.br/nfse"'
        in texto
    )

    assert "ns0:" not in texto


def test_b51_006_xml_serializado_e_parseavel():
    raiz = criar_elemento_nfse(
        "DPS",
        raiz=True,
    )

    xml = serializar_xml(raiz)
    reconstruido = etree.fromstring(xml)

    assert reconstruido.tag == (
        f"{{{NAMESPACE_NFSE}}}DPS"
    )
