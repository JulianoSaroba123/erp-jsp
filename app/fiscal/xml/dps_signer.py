"""Assinatura XMLDSIG da DPS do Sistema Nacional NFS-e.

Responsabilidades:
- assinar exclusivamente o elemento infDPS pelo atributo Id;
- produzir XMLDSIG enveloped;
- validar criptograficamente a assinatura produzida;
- manter chave privada e certificado somente em memoria.

Esta camada nao transmite NFS-e e nao acessa HTTP.
"""

from __future__ import annotations

import base64
import hmac

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from lxml import etree


NFSE_NS = "http://www.sped.fazenda.gov.br/nfse"
DSIG_NS = "http://www.w3.org/2000/09/xmldsig#"

C14N_URI = (
    "http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
)
RSA_SHA1_URI = (
    "http://www.w3.org/2000/09/xmldsig#rsa-sha1"
)
SHA1_URI = (
    "http://www.w3.org/2000/09/xmldsig#sha1"
)
ENVELOPED_URI = (
    "http://www.w3.org/2000/09/xmldsig#"
    "enveloped-signature"
)


class AssinaturaXmlDpsInvalida(ValueError):
    """A DPS nao pode ser assinada ou sua assinatura e invalida."""


def _nfse(nome: str) -> str:
    return f"{{{NFSE_NS}}}{nome}"


def _ds(nome: str) -> str:
    return f"{{{DSIG_NS}}}{nome}"


def _parse_xml(xml) -> etree._Element:
    if isinstance(xml, str):
        dados = xml.encode("utf-8")
    elif isinstance(xml, (bytes, bytearray)):
        dados = bytes(xml)
    else:
        raise AssinaturaXmlDpsInvalida(
            "XML da DPS deve ser bytes ou string."
        )

    if not dados.strip():
        raise AssinaturaXmlDpsInvalida(
            "XML da DPS esta vazio."
        )

    if b"<!DOCTYPE" in dados.upper():
        raise AssinaturaXmlDpsInvalida(
            "DOCTYPE nao e permitido no XML da DPS."
        )

    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
        remove_blank_text=False,
        huge_tree=False,
    )

    try:
        return etree.fromstring(
            dados,
            parser=parser,
        )
    except etree.XMLSyntaxError as exc:
        raise AssinaturaXmlDpsInvalida(
            "XML da DPS malformado."
        ) from exc


def _canonicalizar(elemento: etree._Element) -> bytes:
    return etree.tostring(
        elemento,
        method="c14n",
        exclusive=False,
        with_comments=False,
    )


def _digest_sha1(dados: bytes) -> bytes:
    digestor = hashes.Hash(
        hashes.SHA1()
    )
    digestor.update(dados)
    return digestor.finalize()


def _base64(dados: bytes) -> str:
    return base64.b64encode(
        dados
    ).decode("ascii")


def _decodificar_base64(
    valor,
    *,
    campo: str,
) -> bytes:
    compacto = "".join(
        str(valor or "").split()
    )

    if not compacto:
        raise AssinaturaXmlDpsInvalida(
            f"{campo} ausente."
        )

    try:
        return base64.b64decode(
            compacto,
            validate=True,
        )
    except (ValueError, TypeError) as exc:
        raise AssinaturaXmlDpsInvalida(
            f"{campo} possui Base64 invalido."
        ) from exc


def _obter_inf_dps(
    raiz: etree._Element,
) -> tuple[etree._Element, str]:
    if raiz.tag != _nfse("DPS"):
        raise AssinaturaXmlDpsInvalida(
            "Elemento raiz deve ser DPS."
        )

    elementos = raiz.findall(
        _nfse("infDPS")
    )

    if len(elementos) != 1:
        raise AssinaturaXmlDpsInvalida(
            "DPS deve conter exatamente um infDPS."
        )

    inf_dps = elementos[0]

    identificador = str(
        inf_dps.get("Id") or ""
    ).strip()

    if not identificador:
        raise AssinaturaXmlDpsInvalida(
            "Atributo Id de infDPS obrigatorio."
        )

    if not identificador.startswith("ID"):
        raise AssinaturaXmlDpsInvalida(
            "Id de infDPS deve iniciar com ID."
        )

    return inf_dps, identificador


def _obter_unico(
    pai: etree._Element,
    tag: str,
    *,
    nome: str,
) -> etree._Element:
    encontrados = pai.findall(
        tag
    )

    if len(encontrados) != 1:
        raise AssinaturaXmlDpsInvalida(
            f"{nome} deve ocorrer exatamente uma vez."
        )

    return encontrados[0]


def _validar_material_rsa(
    *,
    chave_privada,
    certificado: x509.Certificate,
) -> None:
    if not isinstance(
        chave_privada,
        rsa.RSAPrivateKey,
    ):
        raise AssinaturaXmlDpsInvalida(
            "Chave privada do certificado deve ser RSA."
        )

    chave_publica_certificado = (
        certificado.public_key()
    )

    if not isinstance(
        chave_publica_certificado,
        rsa.RSAPublicKey,
    ):
        raise AssinaturaXmlDpsInvalida(
            "Certificado da DPS deve possuir chave RSA."
        )

    if (
        chave_privada.public_key().public_numbers()
        != chave_publica_certificado.public_numbers()
    ):
        raise AssinaturaXmlDpsInvalida(
            "Chave privada nao corresponde ao certificado."
        )


def _validar_estrutura_assinatura(
    *,
    signature: etree._Element,
    identificador: str,
):
    signed_info = _obter_unico(
        signature,
        _ds("SignedInfo"),
        nome="SignedInfo",
    )

    canonicalization = _obter_unico(
        signed_info,
        _ds("CanonicalizationMethod"),
        nome="CanonicalizationMethod",
    )

    if canonicalization.get("Algorithm") != C14N_URI:
        raise AssinaturaXmlDpsInvalida(
            "CanonicalizationMethod invalido."
        )

    signature_method = _obter_unico(
        signed_info,
        _ds("SignatureMethod"),
        nome="SignatureMethod",
    )

    if signature_method.get("Algorithm") != RSA_SHA1_URI:
        raise AssinaturaXmlDpsInvalida(
            "SignatureMethod invalido."
        )

    reference = _obter_unico(
        signed_info,
        _ds("Reference"),
        nome="Reference",
    )

    if reference.get("URI") != f"#{identificador}":
        raise AssinaturaXmlDpsInvalida(
            "Reference URI nao corresponde ao Id de infDPS."
        )

    transforms = _obter_unico(
        reference,
        _ds("Transforms"),
        nome="Transforms",
    )

    transformacoes = [
        item.get("Algorithm")
        for item in transforms.findall(
            _ds("Transform")
        )
    ]

    if transformacoes != [
        ENVELOPED_URI,
        C14N_URI,
    ]:
        raise AssinaturaXmlDpsInvalida(
            "Transforms da assinatura DPS invalidos."
        )

    digest_method = _obter_unico(
        reference,
        _ds("DigestMethod"),
        nome="DigestMethod",
    )

    if digest_method.get("Algorithm") != SHA1_URI:
        raise AssinaturaXmlDpsInvalida(
            "DigestMethod invalido."
        )

    digest_value = _obter_unico(
        reference,
        _ds("DigestValue"),
        nome="DigestValue",
    )

    signature_value = _obter_unico(
        signature,
        _ds("SignatureValue"),
        nome="SignatureValue",
    )

    key_info = _obter_unico(
        signature,
        _ds("KeyInfo"),
        nome="KeyInfo",
    )

    x509_data = _obter_unico(
        key_info,
        _ds("X509Data"),
        nome="X509Data",
    )

    x509_certificate = _obter_unico(
        x509_data,
        _ds("X509Certificate"),
        nome="X509Certificate",
    )

    return (
        signed_info,
        digest_value,
        signature_value,
        x509_certificate,
    )


def validar_assinatura_xml_dps(
    xml_assinado,
    *,
    certificado_esperado=None,
) -> x509.Certificate:
    """Valida digest, certificado embutido e assinatura RSA da DPS."""

    raiz = _parse_xml(
        xml_assinado
    )

    inf_dps, identificador = (
        _obter_inf_dps(
            raiz
        )
    )

    signatures = raiz.findall(
        _ds("Signature")
    )

    if len(signatures) != 1:
        raise AssinaturaXmlDpsInvalida(
            "DPS assinada deve conter exatamente uma Signature."
        )

    signature = signatures[0]

    (
        signed_info,
        digest_value,
        signature_value,
        x509_certificate,
    ) = _validar_estrutura_assinatura(
        signature=signature,
        identificador=identificador,
    )

    digest_informado = _decodificar_base64(
        digest_value.text,
        campo="DigestValue",
    )

    digest_calculado = _digest_sha1(
        _canonicalizar(
            inf_dps
        )
    )

    if not hmac.compare_digest(
        digest_informado,
        digest_calculado,
    ):
        raise AssinaturaXmlDpsInvalida(
            "DigestValue da DPS nao confere."
        )

    certificado_der = _decodificar_base64(
        x509_certificate.text,
        campo="X509Certificate",
    )

    try:
        certificado_embutido = (
            x509.load_der_x509_certificate(
                certificado_der
            )
        )
    except ValueError as exc:
        raise AssinaturaXmlDpsInvalida(
            "X509Certificate invalido."
        ) from exc

    chave_publica = (
        certificado_embutido.public_key()
    )

    if not isinstance(
        chave_publica,
        rsa.RSAPublicKey,
    ):
        raise AssinaturaXmlDpsInvalida(
            "Certificado embutido nao possui chave RSA."
        )

    if certificado_esperado is not None:
        esperado = certificado_esperado.fingerprint(
            hashes.SHA256()
        )
        recebido = certificado_embutido.fingerprint(
            hashes.SHA256()
        )

        if not hmac.compare_digest(
            esperado,
            recebido,
        ):
            raise AssinaturaXmlDpsInvalida(
                "Certificado embutido difere do certificado esperado."
            )

    assinatura = _decodificar_base64(
        signature_value.text,
        campo="SignatureValue",
    )

    try:
        chave_publica.verify(
            assinatura,
            _canonicalizar(
                signed_info
            ),
            padding.PKCS1v15(),
            hashes.SHA1(),
        )
    except InvalidSignature as exc:
        raise AssinaturaXmlDpsInvalida(
            "SignatureValue da DPS nao confere."
        ) from exc

    return certificado_embutido


def assinar_xml_dps(
    xml_dps,
    *,
    material_certificado,
) -> bytes:
    """Assina infDPS com XMLDSIG e valida o resultado localmente."""

    if material_certificado is None:
        raise AssinaturaXmlDpsInvalida(
            "Material do certificado A1 nao informado."
        )

    chave_privada = getattr(
        material_certificado,
        "chave_privada",
        None,
    )
    certificado = getattr(
        material_certificado,
        "certificado",
        None,
    )

    if certificado is None:
        raise AssinaturaXmlDpsInvalida(
            "Certificado A1 nao informado."
        )

    _validar_material_rsa(
        chave_privada=chave_privada,
        certificado=certificado,
    )

    raiz = _parse_xml(
        xml_dps
    )

    inf_dps, identificador = (
        _obter_inf_dps(
            raiz
        )
    )

    if raiz.findall(
        _ds("Signature")
    ):
        raise AssinaturaXmlDpsInvalida(
            "DPS ja possui assinatura XMLDSIG."
        )

    digest = _digest_sha1(
        _canonicalizar(
            inf_dps
        )
    )

    signature = etree.Element(
        _ds("Signature"),
        nsmap={
            None: DSIG_NS,
        },
    )

    signed_info = etree.SubElement(
        signature,
        _ds("SignedInfo"),
    )

    canonicalization = etree.SubElement(
        signed_info,
        _ds("CanonicalizationMethod"),
    )
    canonicalization.set(
        "Algorithm",
        C14N_URI,
    )

    signature_method = etree.SubElement(
        signed_info,
        _ds("SignatureMethod"),
    )
    signature_method.set(
        "Algorithm",
        RSA_SHA1_URI,
    )

    reference = etree.SubElement(
        signed_info,
        _ds("Reference"),
    )
    reference.set(
        "URI",
        f"#{identificador}",
    )

    transforms = etree.SubElement(
        reference,
        _ds("Transforms"),
    )

    transform_enveloped = etree.SubElement(
        transforms,
        _ds("Transform"),
    )
    transform_enveloped.set(
        "Algorithm",
        ENVELOPED_URI,
    )

    transform_c14n = etree.SubElement(
        transforms,
        _ds("Transform"),
    )
    transform_c14n.set(
        "Algorithm",
        C14N_URI,
    )

    digest_method = etree.SubElement(
        reference,
        _ds("DigestMethod"),
    )
    digest_method.set(
        "Algorithm",
        SHA1_URI,
    )

    digest_value = etree.SubElement(
        reference,
        _ds("DigestValue"),
    )
    digest_value.text = _base64(
        digest
    )

    # Anexa antes de canonicalizar SignedInfo para considerar
    # exatamente o contexto de namespaces do XML final.
    raiz.append(
        signature
    )

    signed_info_c14n = _canonicalizar(
        signed_info
    )

    assinatura = chave_privada.sign(
        signed_info_c14n,
        padding.PKCS1v15(),
        hashes.SHA1(),
    )

    signature_value = etree.SubElement(
        signature,
        _ds("SignatureValue"),
    )
    signature_value.text = _base64(
        assinatura
    )

    key_info = etree.SubElement(
        signature,
        _ds("KeyInfo"),
    )

    x509_data = etree.SubElement(
        key_info,
        _ds("X509Data"),
    )

    x509_certificate = etree.SubElement(
        x509_data,
        _ds("X509Certificate"),
    )
    x509_certificate.text = _base64(
        certificado.public_bytes(
            serialization.Encoding.DER
        )
    )

    resultado = etree.tostring(
        raiz,
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=False,
    )

    validar_assinatura_xml_dps(
        resultado,
        certificado_esperado=certificado,
    )

    return resultado
