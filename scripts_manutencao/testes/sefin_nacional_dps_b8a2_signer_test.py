from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from lxml import etree

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import NameOID

from app.fiscal.certificado_a1 import MaterialCertificadoA1
from app.fiscal.xml.dps_signer import (
    AssinaturaXmlDpsInvalida,
    C14N_URI,
    DSIG_NS,
    ENVELOPED_URI,
    RSA_SHA1_URI,
    SHA1_URI,
    assinar_xml_dps,
    validar_assinatura_xml_dps,
)


def _certificado(chave, *, nome="B8-A2"):
    agora = datetime.now(timezone.utc)

    nome_x509 = x509.Name(
        [
            x509.NameAttribute(
                NameOID.COUNTRY_NAME,
                "BR",
            ),
            x509.NameAttribute(
                NameOID.ORGANIZATION_NAME,
                "ERP JSP TESTE",
            ),
            x509.NameAttribute(
                NameOID.COMMON_NAME,
                nome,
            ),
        ]
    )

    return (
        x509.CertificateBuilder()
        .subject_name(nome_x509)
        .issuer_name(nome_x509)
        .public_key(chave.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(
            (agora - timedelta(days=1)).replace(tzinfo=None)
        )
        .not_valid_after(
            (agora + timedelta(days=30)).replace(tzinfo=None)
        )
        .sign(
            chave,
            hashes.SHA256(),
        )
    )


def _material_rsa():
    chave = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    return MaterialCertificadoA1(
        chave_privada=chave,
        certificado=_certificado(chave),
        cadeia=(),
        caminho=Path("certificado-teste.pfx"),
    )


def _xml():
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<DPS xmlns="http://www.sped.fazenda.gov.br/nfse" versao="1.01">'
        b'<infDPS Id="ID355450800000000000000000000000000000000001">'
        b'<tpAmb>2</tpAmb>'
        b'<serie>1</serie>'
        b'<nDPS>1</nDPS>'
        b'<teste>ORIGINAL</teste>'
        b'</infDPS>'
        b'</DPS>'
    )


def _q(ns, nome):
    return f"{{{ns}}}{nome}"


def test_b8a2_001_assina_e_valida_localmente():
    material = _material_rsa()

    xml_assinado = assinar_xml_dps(
        _xml(),
        material_certificado=material,
    )

    certificado = validar_assinatura_xml_dps(
        xml_assinado,
        certificado_esperado=material.certificado,
    )

    assert (
        certificado.serial_number
        == material.certificado.serial_number
    )


def test_b8a2_002_signature_fica_apos_infdps():
    xml_assinado = assinar_xml_dps(
        _xml(),
        material_certificado=_material_rsa(),
    )

    raiz = etree.fromstring(xml_assinado)

    assert [
        etree.QName(item).localname
        for item in raiz
    ] == [
        "infDPS",
        "Signature",
    ]


def test_b8a2_003_algoritmos_e_reference_corretos():
    xml_assinado = assinar_xml_dps(
        _xml(),
        material_certificado=_material_rsa(),
    )

    raiz = etree.fromstring(xml_assinado)

    signature = raiz.find(
        _q(DSIG_NS, "Signature")
    )

    signed_info = signature.find(
        _q(DSIG_NS, "SignedInfo")
    )

    canonicalization = signed_info.find(
        _q(DSIG_NS, "CanonicalizationMethod")
    )

    signature_method = signed_info.find(
        _q(DSIG_NS, "SignatureMethod")
    )

    reference = signed_info.find(
        _q(DSIG_NS, "Reference")
    )

    transforms = reference.find(
        _q(DSIG_NS, "Transforms")
    )

    digest_method = reference.find(
        _q(DSIG_NS, "DigestMethod")
    )

    assert (
        canonicalization.get("Algorithm")
        == C14N_URI
    )

    assert (
        signature_method.get("Algorithm")
        == RSA_SHA1_URI
    )

    assert reference.get("URI").startswith("#ID")

    assert [
        item.get("Algorithm")
        for item in transforms
    ] == [
        ENVELOPED_URI,
        C14N_URI,
    ]

    assert (
        digest_method.get("Algorithm")
        == SHA1_URI
    )


def test_b8a2_004_detecta_adulteracao_da_infdps():
    material = _material_rsa()

    xml_assinado = assinar_xml_dps(
        _xml(),
        material_certificado=material,
    )

    adulterado = xml_assinado.replace(
        b"ORIGINAL",
        b"ADULTERADO",
    )

    with pytest.raises(
        AssinaturaXmlDpsInvalida,
        match="DigestValue",
    ):
        validar_assinatura_xml_dps(
            adulterado
        )


def test_b8a2_005_detecta_signaturevalue_adulterado():
    material = _material_rsa()

    xml_assinado = assinar_xml_dps(
        _xml(),
        material_certificado=material,
    )

    raiz = etree.fromstring(
        xml_assinado
    )

    signature_value = raiz.find(
        ".//" + _q(
            DSIG_NS,
            "SignatureValue",
        )
    )

    signature_value.text = "AAAA"

    adulterado = etree.tostring(
        raiz,
        encoding="UTF-8",
        xml_declaration=True,
    )

    with pytest.raises(
        AssinaturaXmlDpsInvalida,
        match="SignatureValue",
    ):
        validar_assinatura_xml_dps(
            adulterado
        )


def test_b8a2_006_rejeita_assinatura_duplicada():
    material = _material_rsa()

    xml_assinado = assinar_xml_dps(
        _xml(),
        material_certificado=material,
    )

    with pytest.raises(
        AssinaturaXmlDpsInvalida,
        match="ja possui",
    ):
        assinar_xml_dps(
            xml_assinado,
            material_certificado=material,
        )


def test_b8a2_007_rejeita_id_ausente():
    xml = _xml().replace(
        b' Id="ID355450800000000000000000000000000000000001"',
        b"",
    )

    with pytest.raises(
        AssinaturaXmlDpsInvalida,
        match="Id",
    ):
        assinar_xml_dps(
            xml,
            material_certificado=_material_rsa(),
        )


def test_b8a2_008_rejeita_chave_que_nao_corresponde():
    chave_certificado = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    outra_chave = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    material = MaterialCertificadoA1(
        chave_privada=outra_chave,
        certificado=_certificado(
            chave_certificado
        ),
        cadeia=(),
        caminho=Path("divergente.pfx"),
    )

    with pytest.raises(
        AssinaturaXmlDpsInvalida,
        match="nao corresponde",
    ):
        assinar_xml_dps(
            _xml(),
            material_certificado=material,
        )


def test_b8a2_009_rejeita_certificado_nao_rsa():
    chave = ec.generate_private_key(
        ec.SECP256R1()
    )

    material = MaterialCertificadoA1(
        chave_privada=chave,
        certificado=_certificado(
            chave,
            nome="EC TESTE",
        ),
        cadeia=(),
        caminho=Path("ec.pfx"),
    )

    with pytest.raises(
        AssinaturaXmlDpsInvalida,
        match="RSA",
    ):
        assinar_xml_dps(
            _xml(),
            material_certificado=material,
        )


def test_b8a2_010_assinatura_e_deterministica():
    material = _material_rsa()

    primeira = assinar_xml_dps(
        _xml(),
        material_certificado=material,
    )

    segunda = assinar_xml_dps(
        _xml(),
        material_certificado=material,
    )

    assert primeira == segunda
