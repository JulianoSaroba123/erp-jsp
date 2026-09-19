from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from lxml import etree

from app.fiscal.providers.geisweb_tiete_signer import (
    ALG_C14N,
    ALG_ENVELOPED,
    ALG_RSA_SHA1,
    ALG_SHA1,
    NS_DSIG,
    NS_SIGN,
    AssinaturaGeisWebInvalida,
    assinar_xml_geisweb,
    validar_assinatura_xml_geisweb,
)


NS_NORMAL = (
    "http://www.gerenciadecidades.com.br/"
    "xsd/envio_lote_rps_reforma.xsd"
)


def _material():
    chave = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    agora = datetime.now(
        timezone.utc
    )

    nome = x509.Name([
        x509.NameAttribute(
            NameOID.COMMON_NAME,
            "CERTIFICADO TESTE GEISWEB",
        )
    ])

    certificado = (
        x509.CertificateBuilder()
        .subject_name(nome)
        .issuer_name(nome)
        .public_key(chave.public_key())
        .serial_number(
            x509.random_serial_number()
        )
        .not_valid_before(
            agora - timedelta(days=1)
        )
        .not_valid_after(
            agora + timedelta(days=30)
        )
        .sign(
            chave,
            hashes.SHA256(),
        )
    )

    return SimpleNamespace(
        chave_privada=chave,
        certificado=certificado,
        cadeia=(),
        caminho="TESTE",
    )


def _xml_base():
    # XML pequeno para testar exclusivamente o motor
    # criptografico e a conversao de namespace.
    return (
        '<?xml version="1.0" encoding="ISO-8859-1"?>'
        f'<EnviaLoteRps xmlns="{NS_NORMAL}">'
        '<CnpjCpf>11111111000191</CnpjCpf>'
        '<NumeroLote>1</NumeroLote>'
        '<Rps>'
        '<IdentificacaoRps>'
        '<NumeroRps>1</NumeroRps>'
        '</IdentificacaoRps>'
        '</Rps>'
        '</EnviaLoteRps>'
    ).encode("ISO-8859-1")


def _parse(xml):
    return etree.fromstring(xml)


def test_assinatura_converte_raiz_e_namespace():
    xml = assinar_xml_geisweb(
        _xml_base(),
        _material(),
    )

    raiz = _parse(xml)

    qn = etree.QName(raiz)

    assert qn.localname == "EnviaSignLoteRps"
    assert qn.namespace == NS_SIGN

    filhos = list(raiz)

    assert (
        etree.QName(filhos[-1]).localname
        == "Signature"
    )

    assert (
        etree.QName(filhos[-1]).namespace
        == NS_DSIG
    )


def test_assinatura_usa_algoritmos_geisweb():
    xml = assinar_xml_geisweb(
        _xml_base(),
        _material(),
    )

    raiz = _parse(xml)

    ns = {"ds": NS_DSIG}

    reference = raiz.xpath(
        "./ds:Signature/ds:SignedInfo/ds:Reference",
        namespaces=ns,
    )[0]

    assert reference.get("URI") == ""

    canonical = raiz.xpath(
        "./ds:Signature/ds:SignedInfo/"
        "ds:CanonicalizationMethod",
        namespaces=ns,
    )[0]

    signature_method = raiz.xpath(
        "./ds:Signature/ds:SignedInfo/"
        "ds:SignatureMethod",
        namespaces=ns,
    )[0]

    digest_method = raiz.xpath(
        "./ds:Signature/ds:SignedInfo/"
        "ds:Reference/ds:DigestMethod",
        namespaces=ns,
    )[0]

    transforms = raiz.xpath(
        "./ds:Signature/ds:SignedInfo/"
        "ds:Reference/ds:Transforms/ds:Transform",
        namespaces=ns,
    )

    assert canonical.get("Algorithm") == ALG_C14N
    assert signature_method.get("Algorithm") == ALG_RSA_SHA1
    assert digest_method.get("Algorithm") == ALG_SHA1

    assert [
        item.get("Algorithm")
        for item in transforms
    ] == [
        ALG_ENVELOPED,
        ALG_C14N,
    ]


def test_assinatura_valida_localmente():
    xml = assinar_xml_geisweb(
        _xml_base(),
        _material(),
    )

    resultado = (
        validar_assinatura_xml_geisweb(
            xml
        )
    )

    assert resultado.valido is True
    assert resultado.digest_valido is True
    assert resultado.assinatura_valida is True


def test_alteracao_do_xml_quebra_digest():
    xml = assinar_xml_geisweb(
        _xml_base(),
        _material(),
    )

    adulterado = xml.replace(
        b"<NumeroLote>1</NumeroLote>",
        b"<NumeroLote>2</NumeroLote>",
    )

    with pytest.raises(
        AssinaturaGeisWebInvalida,
        match="DigestValue",
    ):
        validar_assinatura_xml_geisweb(
            adulterado
        )


def test_keyinfo_contem_somente_certificado_final():
    xml = assinar_xml_geisweb(
        _xml_base(),
        _material(),
    )

    raiz = _parse(xml)

    ns = {"ds": NS_DSIG}

    certificados = raiz.xpath(
        "./ds:Signature/ds:KeyInfo/"
        "ds:X509Data/ds:X509Certificate",
        namespaces=ns,
    )

    assert len(certificados) == 1

    proibidas = {
        "X509SubjectName",
        "X509IssuerSerial",
        "X509IssuerName",
        "X509SerialNumber",
        "X509SKI",
        "KeyValue",
        "RSAKeyValue",
        "Modulus",
        "Exponent",
    }

    presentes = {
        etree.QName(elemento).localname
        for elemento in raiz.iter()
    }

    assert not (
        proibidas & presentes
    )
