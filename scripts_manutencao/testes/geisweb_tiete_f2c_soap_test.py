from lxml import etree
import pytest

from app.fiscal.providers.geisweb_tiete_operacoes import (
    OPERACAO_ENVIA_LOTE_RPS,
    OPERACAO_ENVIA_SIGN_LOTE_RPS,
)
from app.fiscal.providers.geisweb_tiete_soap import (
    NS_XML_NORMAL,
    NS_XML_SIGN,
    SOAP_ENC,
    SOAP_ENV,
    XSI_NS,
    SoapGeisWebInvalido,
    montar_envelope_soap_geisweb,
    montar_headers_soap_geisweb,
)


def _xml_assinado():
    return (
        '<?xml version="1.0" '
        'encoding="ISO-8859-1"?>'
        f'<EnviaSignLoteRps xmlns="{NS_XML_SIGN}">'
        '<CnpjCpf>11111111000191</CnpjCpf>'
        '<NumeroLote>7</NumeroLote>'
        '<Rps />'
        '</EnviaSignLoteRps>'
    ).encode(
        "ISO-8859-1"
    )


def _xml_normal():
    return (
        '<?xml version="1.0" '
        'encoding="ISO-8859-1"?>'
        f'<EnviaLoteRps xmlns="{NS_XML_NORMAL}">'
        '<CnpjCpf>11111111000191</CnpjCpf>'
        '<NumeroLote>7</NumeroLote>'
        '<Rps />'
        '</EnviaLoteRps>'
    ).encode(
        "ISO-8859-1"
    )


def _parse(xml):
    return etree.fromstring(
        xml
    )


def test_envelope_assinado_e_soap_11():
    envelope = montar_envelope_soap_geisweb(
        xml_fiscal=_xml_assinado(),
        nome_operacao=(
            OPERACAO_ENVIA_SIGN_LOTE_RPS
        ),
    )

    raiz = _parse(
        envelope
    )

    assert (
        etree.QName(raiz).namespace
        == SOAP_ENV
    )

    assert (
        etree.QName(raiz).localname
        == "Envelope"
    )

    assert (
        raiz.get(
            f"{{{SOAP_ENV}}}encodingStyle"
        )
        == SOAP_ENC
    )


def test_operacao_rpc_assinada_tem_parametro_xsd_string():
    envelope = montar_envelope_soap_geisweb(
        xml_fiscal=_xml_assinado(),
        nome_operacao=(
            OPERACAO_ENVIA_SIGN_LOTE_RPS
        ),
    )

    raiz = _parse(
        envelope
    )

    body = raiz.find(
        f"{{{SOAP_ENV}}}Body"
    )

    assert body is not None

    metodo = list(body)[0]

    assert (
        etree.QName(metodo).localname
        == "EnviaSignLoteRps"
    )

    parametro = list(
        metodo
    )[0]

    assert (
        etree.QName(parametro).localname
        == "EnviaSignLoteRps"
    )

    assert (
        parametro.get(
            f"{{{XSI_NS}}}type"
        )
        == "xsd:string"
    )


def test_xml_fiscal_viaja_como_texto_nao_como_filho():
    xml_fiscal = _xml_assinado()

    envelope = montar_envelope_soap_geisweb(
        xml_fiscal=xml_fiscal,
        nome_operacao=(
            OPERACAO_ENVIA_SIGN_LOTE_RPS
        ),
    )

    raiz = _parse(
        envelope
    )

    body = raiz.find(
        f"{{{SOAP_ENV}}}Body"
    )

    metodo = list(
        body
    )[0]

    parametro = list(
        metodo
    )[0]

    # Nenhum elemento XML fiscal foi injetado
    # estruturalmente no SOAP.
    assert len(parametro) == 0

    assert parametro.text == (
        xml_fiscal.decode(
            "ISO-8859-1"
        )
    )

    # Na serializacao SOAP o '<' do XML fiscal
    # precisa aparecer escapado.
    assert (
        b"&lt;EnviaSignLoteRps"
        in envelope
    )


def test_envelope_normal_tambem_respeita_contrato_rpc():
    envelope = montar_envelope_soap_geisweb(
        xml_fiscal=_xml_normal(),
        nome_operacao=(
            OPERACAO_ENVIA_LOTE_RPS
        ),
    )

    raiz = _parse(
        envelope
    )

    body = raiz.find(
        f"{{{SOAP_ENV}}}Body"
    )

    metodo = list(
        body
    )[0]

    assert (
        etree.QName(metodo).localname
        == "EnviaLoteRps"
    )

    parametro = list(
        metodo
    )[0]

    assert (
        etree.QName(parametro).localname
        == "EnviaLoteRps"
    )


def test_rejeita_xml_assinado_na_operacao_nao_assinada():
    with pytest.raises(
        SoapGeisWebInvalido,
        match="nao corresponde",
    ):
        montar_envelope_soap_geisweb(
            xml_fiscal=_xml_assinado(),
            nome_operacao=(
                OPERACAO_ENVIA_LOTE_RPS
            ),
        )


def test_headers_usam_soapaction_do_wsdl():
    headers = montar_headers_soap_geisweb(
        nome_operacao=(
            OPERACAO_ENVIA_SIGN_LOTE_RPS
        )
    )

    assert headers["Content-Type"] == (
        "text/xml; charset=ISO-8859-1"
    )

    assert headers[
        "SOAPAction"
    ].endswith(
        '#EnviaSignLoteRps"'
    )

    assert headers[
        "SOAPAction"
    ].startswith(
        '"urn:https://'
    )
