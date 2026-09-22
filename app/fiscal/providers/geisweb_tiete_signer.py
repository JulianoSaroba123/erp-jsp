"""Assinatura XMLDSIG local do GeisWeb Tiete.

Contrato adotado:
- XML Digital Signature;
- formato Enveloped;
- Canonical XML 1.0;
- RSA-SHA1;
- SHA-1 para Digest;
- Reference URI="";
- EndCertOnly;
- Signature como ultimo filho de EnviaSignLoteRps.

Este modulo nao acessa rede.
"""

from __future__ import annotations

import base64
import copy
import hashlib
from dataclasses import dataclass

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import Encoding
from lxml import etree


NS_NORMAL = (
    "http://www.gerenciadecidades.com.br/"
    "xsd/envio_lote_rps_reforma.xsd"
)

NS_SIGN = (
    "http://www.gerenciadecidades.com.br/"
    "xsd/envio_lote_rps_sign_reforma.xsd"
)

NS_DSIG = "http://www.w3.org/2000/09/xmldsig#"

ALG_C14N = (
    "http://www.w3.org/TR/2001/"
    "REC-xml-c14n-20010315"
)

ALG_ENVELOPED = (
    "http://www.w3.org/2000/09/"
    "xmldsig#enveloped-signature"
)

ALG_RSA_SHA1 = (
    "http://www.w3.org/2000/09/"
    "xmldsig#rsa-sha1"
)

ALG_SHA1 = (
    "http://www.w3.org/2000/09/"
    "xmldsig#sha1"
)


class AssinaturaGeisWebInvalida(ValueError):
    """Falha de construcao ou validacao da assinatura GeisWeb."""


@dataclass(frozen=True)
class ResultadoAssinaturaGeisWeb:
    valido: bool
    digest_valido: bool
    assinatura_valida: bool


def _parse_xml(xml):
    if isinstance(xml, str):
        xml = xml.encode("utf-8")

    if not isinstance(
        xml,
        (bytes, bytearray),
    ):
        raise AssinaturaGeisWebInvalida(
            "XML deve ser bytes ou str."
        )

    try:
        return etree.fromstring(
            bytes(xml),
            parser=etree.XMLParser(
                remove_blank_text=True,
                resolve_entities=False,
                no_network=True,
            ),
        )
    except etree.XMLSyntaxError as exc:
        raise AssinaturaGeisWebInvalida(
            f"XML invalido: {exc}"
        ) from exc


def _qname(namespace, nome):
    return f"{{{namespace}}}{nome}"


def _c14n(elemento):
    return etree.tostring(
        elemento,
        method="c14n",
        exclusive=False,
        with_comments=False,
    )


def _copiar_para_namespace_sign(elemento):
    qn = etree.QName(elemento)

    novo = etree.Element(
        _qname(
            NS_SIGN,
            qn.localname,
        )
    )

    for nome, valor in elemento.attrib.items():
        novo.set(
            nome,
            valor,
        )

    novo.text = elemento.text
    novo.tail = elemento.tail

    for filho in elemento:
        novo.append(
            _copiar_para_namespace_sign(
                filho
            )
        )

    return novo


def preparar_xml_envio_sign_lote_rps(
    xml_envio_lote_rps,
):
    """Converte EnviaLoteRps no envelope XML assinado."""

    raiz = _parse_xml(
        xml_envio_lote_rps
    )

    qn = etree.QName(raiz)

    if (
        qn.localname != "EnviaLoteRps"
        or qn.namespace != NS_NORMAL
    ):
        raise AssinaturaGeisWebInvalida(
            "XML base deve possuir raiz "
            "EnviaLoteRps do namespace GeisWeb Reforma."
        )

    raiz_sign = etree.Element(
        _qname(
            NS_SIGN,
            "EnviaSignLoteRps",
        ),
        nsmap={
            None: NS_SIGN,
        },
    )

    for nome, valor in raiz.attrib.items():
        raiz_sign.set(
            nome,
            valor,
        )

    raiz_sign.text = raiz.text

    for filho in raiz:
        raiz_sign.append(
            _copiar_para_namespace_sign(
                filho
            )
        )

    return raiz_sign


def _validar_material_certificado(
    material_certificado,
):
    chave = getattr(
        material_certificado,
        "chave_privada",
        None,
    )

    certificado = getattr(
        material_certificado,
        "certificado",
        None,
    )

    if not isinstance(
        chave,
        rsa.RSAPrivateKey,
    ):
        raise AssinaturaGeisWebInvalida(
            "Certificado GeisWeb deve possuir chave privada RSA."
        )

    if not isinstance(
        certificado,
        x509.Certificate,
    ):
        raise AssinaturaGeisWebInvalida(
            "Material GeisWeb deve possuir certificado X509."
        )

    return chave, certificado


def _montar_signature(
    *,
    raiz_sign,
    chave_privada,
    certificado,
):
    # Digest do documento sem a propria Signature.
    digest = hashlib.sha1(
        _c14n(
            raiz_sign
        )
    ).digest()

    signature = etree.SubElement(
        raiz_sign,
        _qname(
            NS_DSIG,
            "Signature",
        ),
        nsmap={
            None: NS_DSIG,
        },
    )

    signed_info = etree.SubElement(
        signature,
        _qname(
            NS_DSIG,
            "SignedInfo",
        ),
    )

    etree.SubElement(
        signed_info,
        _qname(
            NS_DSIG,
            "CanonicalizationMethod",
        ),
        Algorithm=ALG_C14N,
    )

    etree.SubElement(
        signed_info,
        _qname(
            NS_DSIG,
            "SignatureMethod",
        ),
        Algorithm=ALG_RSA_SHA1,
    )

    reference = etree.SubElement(
        signed_info,
        _qname(
            NS_DSIG,
            "Reference",
        ),
        URI="",
    )

    transforms = etree.SubElement(
        reference,
        _qname(
            NS_DSIG,
            "Transforms",
        ),
    )

    etree.SubElement(
        transforms,
        _qname(
            NS_DSIG,
            "Transform",
        ),
        Algorithm=ALG_ENVELOPED,
    )

    etree.SubElement(
        transforms,
        _qname(
            NS_DSIG,
            "Transform",
        ),
        Algorithm=ALG_C14N,
    )

    etree.SubElement(
        reference,
        _qname(
            NS_DSIG,
            "DigestMethod",
        ),
        Algorithm=ALG_SHA1,
    )

    digest_value = etree.SubElement(
        reference,
        _qname(
            NS_DSIG,
            "DigestValue",
        ),
    )

    digest_value.text = base64.b64encode(
        digest
    ).decode("ascii")

    signed_info_c14n = _c14n(
        signed_info
    )

    assinatura = chave_privada.sign(
        signed_info_c14n,
        padding.PKCS1v15(),
        hashes.SHA1(),
    )

    signature_value = etree.SubElement(
        signature,
        _qname(
            NS_DSIG,
            "SignatureValue",
        ),
    )

    signature_value.text = base64.b64encode(
        assinatura
    ).decode("ascii")

    key_info = etree.SubElement(
        signature,
        _qname(
            NS_DSIG,
            "KeyInfo",
        ),
    )

    x509_data = etree.SubElement(
        key_info,
        _qname(
            NS_DSIG,
            "X509Data",
        ),
    )

    x509_certificate = etree.SubElement(
        x509_data,
        _qname(
            NS_DSIG,
            "X509Certificate",
        ),
    )

    der = certificado.public_bytes(
        Encoding.DER
    )

    x509_certificate.text = base64.b64encode(
        der
    ).decode("ascii")


def serializar_xml_sign_geisweb(
    raiz,
):
    return etree.tostring(
        raiz,
        encoding="ISO-8859-1",
        xml_declaration=True,
        pretty_print=False,
    )


def assinar_xml_geisweb(
    xml_envio_lote_rps,
    material_certificado,
):
    """Converte, assina e serializa EnviaSignLoteRps."""

    chave, certificado = (
        _validar_material_certificado(
            material_certificado
        )
    )

    raiz = preparar_xml_envio_sign_lote_rps(
        xml_envio_lote_rps
    )

    _montar_signature(
        raiz_sign=raiz,
        chave_privada=chave,
        certificado=certificado,
    )

    return serializar_xml_sign_geisweb(
        raiz
    )


def validar_assinatura_xml_geisweb(
    xml_assinado,
):
    """Valida digest e assinatura criptografica localmente."""

    raiz = _parse_xml(
        xml_assinado
    )

    qn = etree.QName(raiz)

    if (
        qn.localname != "EnviaSignLoteRps"
        or qn.namespace != NS_SIGN
    ):
        raise AssinaturaGeisWebInvalida(
            "Raiz assinada GeisWeb invalida."
        )

    assinatura = raiz.find(
        _qname(
            NS_DSIG,
            "Signature",
        )
    )

    if assinatura is None:
        raise AssinaturaGeisWebInvalida(
            "Signature nao encontrada."
        )

    signed_info = assinatura.find(
        _qname(
            NS_DSIG,
            "SignedInfo",
        )
    )

    signature_value = assinatura.findtext(
        _qname(
            NS_DSIG,
            "SignatureValue",
        )
    )

    certificado_b64 = assinatura.findtext(
        ".//"
        + _qname(
            NS_DSIG,
            "X509Certificate",
        )
    )

    digest_value = assinatura.findtext(
        ".//"
        + _qname(
            NS_DSIG,
            "DigestValue",
        )
    )

    reference = assinatura.find(
        ".//"
        + _qname(
            NS_DSIG,
            "Reference",
        )
    )

    if (
        signed_info is None
        or not signature_value
        or not certificado_b64
        or not digest_value
        or reference is None
    ):
        raise AssinaturaGeisWebInvalida(
            "Estrutura XMLDSIG incompleta."
        )

    if reference.get("URI") != "":
        raise AssinaturaGeisWebInvalida(
            "Reference URI GeisWeb inesperada."
        )

    # Reaplica a transformacao Enveloped:
    # remove Signature antes do digest.
    raiz_sem_assinatura = copy.deepcopy(
        raiz
    )

    assinatura_copia = raiz_sem_assinatura.find(
        _qname(
            NS_DSIG,
            "Signature",
        )
    )

    if assinatura_copia is None:
        raise AssinaturaGeisWebInvalida(
            "Signature nao encontrada na copia."
        )

    raiz_sem_assinatura.remove(
        assinatura_copia
    )

    digest_calculado = hashlib.sha1(
        _c14n(
            raiz_sem_assinatura
        )
    ).digest()

    try:
        digest_informado = base64.b64decode(
            digest_value,
            validate=True,
        )
    except Exception as exc:
        raise AssinaturaGeisWebInvalida(
            "DigestValue Base64 invalido."
        ) from exc

    if digest_calculado != digest_informado:
        raise AssinaturaGeisWebInvalida(
            "DigestValue GeisWeb nao confere."
        )

    try:
        cert_der = base64.b64decode(
            certificado_b64,
            validate=True,
        )

        certificado = (
            x509.load_der_x509_certificate(
                cert_der
            )
        )
    except Exception as exc:
        raise AssinaturaGeisWebInvalida(
            "X509Certificate invalido."
        ) from exc

    chave_publica = certificado.public_key()

    if not isinstance(
        chave_publica,
        rsa.RSAPublicKey,
    ):
        raise AssinaturaGeisWebInvalida(
            "Chave publica nao e RSA."
        )

    try:
        assinatura_bytes = base64.b64decode(
            signature_value,
            validate=True,
        )

        chave_publica.verify(
            assinatura_bytes,
            _c14n(
                signed_info
            ),
            padding.PKCS1v15(),
            hashes.SHA1(),
        )

    except (
        InvalidSignature,
        ValueError,
    ) as exc:
        raise AssinaturaGeisWebInvalida(
            "SignatureValue GeisWeb invalido."
        ) from exc

    return ResultadoAssinaturaGeisWeb(
        valido=True,
        digest_valido=True,
        assinatura_valida=True,
    )
