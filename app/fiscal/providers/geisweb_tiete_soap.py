"""Envelope SOAP 1.1 para GeisWeb Tiete.

Contrato confirmado no WSDL vivo:
- SOAP 1.1
- style=rpc
- use=encoded
- encodingStyle SOAP Encoding
- entrada xsd:string
- XML fiscal transportado como TEXTO escapado

Nenhum acesso de rede ocorre neste modulo.
"""

from __future__ import annotations

from lxml import etree

from app.fiscal.providers.geisweb_tiete_config import (
    SOAP_NAMESPACE_HOMOLOGACAO,
)
from app.fiscal.providers.geisweb_tiete_operacoes import (
    OPERACAO_ENVIA_LOTE_RPS,
    OPERACAO_ENVIA_SIGN_LOTE_RPS,
    obter_operacao_geisweb,
)


SOAP_ENV = (
    "http://schemas.xmlsoap.org/soap/envelope/"
)

SOAP_ENC = (
    "http://schemas.xmlsoap.org/soap/encoding/"
)

XSD_NS = (
    "http://www.w3.org/2001/XMLSchema"
)

XSI_NS = (
    "http://www.w3.org/2001/XMLSchema-instance"
)

NS_XML_NORMAL = (
    "http://www.gerenciadecidades.com.br/"
    "xsd/envio_lote_rps_reforma.xsd"
)

NS_XML_SIGN = (
    "http://www.gerenciadecidades.com.br/"
    "xsd/envio_lote_rps_sign_reforma.xsd"
)


class SoapGeisWebInvalido(ValueError):
    """Envelope ou parametro SOAP GeisWeb invalido."""


def _qname(namespace, nome):
    return f"{{{namespace}}}{nome}"


def _xml_fiscal_para_texto(xml):
    if isinstance(xml, str):
        texto = xml

    elif isinstance(
        xml,
        (bytes, bytearray),
    ):
        try:
            texto = bytes(xml).decode(
                "ISO-8859-1"
            )
        except UnicodeDecodeError as exc:
            raise SoapGeisWebInvalido(
                "XML fiscal nao pode ser decodificado "
                "como ISO-8859-1."
            ) from exc

    else:
        raise SoapGeisWebInvalido(
            "XML fiscal deve ser bytes ou str."
        )

    try:
        raiz = etree.fromstring(
            texto.encode(
                "ISO-8859-1"
            ),
            parser=etree.XMLParser(
                no_network=True,
                resolve_entities=False,
            ),
        )
    except etree.XMLSyntaxError as exc:
        raise SoapGeisWebInvalido(
            f"XML fiscal invalido: {exc}"
        ) from exc

    return texto, raiz


def _validar_xml_para_operacao(
    *,
    raiz,
    nome_operacao,
):
    qn = etree.QName(
        raiz
    )

    if (
        nome_operacao
        == OPERACAO_ENVIA_SIGN_LOTE_RPS
    ):
        raiz_esperada = (
            "EnviaSignLoteRps"
        )

        namespace_esperado = (
            NS_XML_SIGN
        )

    elif (
        nome_operacao
        == OPERACAO_ENVIA_LOTE_RPS
    ):
        raiz_esperada = (
            "EnviaLoteRps"
        )

        namespace_esperado = (
            NS_XML_NORMAL
        )

    else:
        raise SoapGeisWebInvalido(
            "Operacao de envio GeisWeb "
            "nao suportada pelo SOAP."
        )

    if (
        qn.localname != raiz_esperada
        or qn.namespace != namespace_esperado
    ):
        raise SoapGeisWebInvalido(
            "XML fiscal nao corresponde "
            f"a operacao {nome_operacao}."
        )


def montar_envelope_soap_geisweb(
    *,
    xml_fiscal,
    nome_operacao,
):
    """Monta SOAP 1.1 rpc/encoded sem transmitir."""

    operacao = obter_operacao_geisweb(
        nome_operacao
    )

    texto_xml, raiz_xml = (
        _xml_fiscal_para_texto(
            xml_fiscal
        )
    )

    _validar_xml_para_operacao(
        raiz=raiz_xml,
        nome_operacao=operacao.nome,
    )

    envelope = etree.Element(
        _qname(
            SOAP_ENV,
            "Envelope",
        ),
        nsmap={
            "SOAP-ENV": SOAP_ENV,
            "SOAP-ENC": SOAP_ENC,
            "xsd": XSD_NS,
            "xsi": XSI_NS,
            "ns1": (
                SOAP_NAMESPACE_HOMOLOGACAO
            ),
        },
    )

    envelope.set(
        _qname(
            SOAP_ENV,
            "encodingStyle",
        ),
        SOAP_ENC,
    )

    body = etree.SubElement(
        envelope,
        _qname(
            SOAP_ENV,
            "Body",
        ),
    )

    metodo = etree.SubElement(
        body,
        _qname(
            SOAP_NAMESPACE_HOMOLOGACAO,
            operacao.nome,
        ),
    )

    # RPC: o nome da part do WSDL e igual
    # ao nome da operacao.
    parametro = etree.SubElement(
        metodo,
        operacao.nome,
    )

    parametro.set(
        _qname(
            XSI_NS,
            "type",
        ),
        "xsd:string",
    )

    # IMPORTANTE:
    # XML fiscal e texto do xsd:string.
    # O lxml faz o escaping de <, > e &.
    parametro.text = texto_xml

    return etree.tostring(
        envelope,
        encoding="ISO-8859-1",
        xml_declaration=True,
        pretty_print=False,
    )


def montar_headers_soap_geisweb(
    *,
    nome_operacao,
):
    """Headers HTTP previstos para futura transmissao."""

    operacao = obter_operacao_geisweb(
        nome_operacao
    )

    return {
        "Content-Type": (
            "text/xml; charset=ISO-8859-1"
        ),
        "SOAPAction": (
            f'"{operacao.soap_action}"'
        ),
    }
