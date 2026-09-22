from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from app.fiscal import nfse_service as service
from app.fiscal.certificado_a1 import MaterialCertificadoA1
from app.fiscal.xml.dps_signer import assinar_xml_dps


def _material():
    chave = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    agora = datetime.now(timezone.utc)

    nome = x509.Name(
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
                "B8-A2.3",
            ),
        ]
    )

    certificado = (
        x509.CertificateBuilder()
        .subject_name(nome)
        .issuer_name(nome)
        .public_key(chave.public_key())
        .serial_number(
            x509.random_serial_number()
        )
        .not_valid_before(
            (agora - timedelta(days=1)).replace(
                tzinfo=None
            )
        )
        .not_valid_after(
            (agora + timedelta(days=30)).replace(
                tzinfo=None
            )
        )
        .sign(
            chave,
            hashes.SHA256(),
        )
    )

    return MaterialCertificadoA1(
        chave_privada=chave,
        certificado=certificado,
        cadeia=(),
        caminho=Path("b8-a2-3-teste.pfx"),
    )


def _xml():
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<DPS xmlns="http://www.sped.fazenda.gov.br/nfse" '
        b'versao="1.01">'
        b'<infDPS '
        b'Id="ID355450800000000000000000000000000000000001">'
        b'<tpAmb>2</tpAmb>'
        b'<teste>ORIGINAL</teste>'
        b'</infDPS>'
        b'</DPS>'
    )


def _documento(status="PREPARADA"):
    return SimpleNamespace(
        status=status,
        mensagem_status=None,
    )


def test_b8a2_gate_001_bloqueia_xml_sem_assinatura():
    documento = _documento()

    with pytest.raises(
        service.TransicaoStatusNfseInvalida,
        match="assinatura XMLDSIG invalida",
    ):
        service.preparar_nfse_para_envio(
            documento=documento,
            payload={
                "conteudo": _xml(),
            },
        )

    assert documento.status == "PREPARADA"


def test_b8a2_gate_002_libera_xml_assinado_valido():
    documento = _documento()

    xml_assinado = assinar_xml_dps(
        _xml(),
        material_certificado=_material(),
    )

    resultado = service.preparar_nfse_para_envio(
        documento=documento,
        payload={
            "conteudo": xml_assinado,
        },
    )

    assert resultado is documento
    assert documento.status == "PENDENTE_ENVIO"


def test_b8a2_gate_003_bloqueia_xml_assinado_adulterado():
    documento = _documento()

    xml_assinado = assinar_xml_dps(
        _xml(),
        material_certificado=_material(),
    )

    adulterado = xml_assinado.replace(
        b"ORIGINAL",
        b"ALTERADO",
    )

    with pytest.raises(
        service.TransicaoStatusNfseInvalida,
        match="assinatura XMLDSIG invalida",
    ):
        service.preparar_nfse_para_envio(
            documento=documento,
            payload={
                "conteudo": adulterado,
            },
        )

    assert documento.status == "PREPARADA"


def test_b8a2_gate_004_estado_invalido_bloqueia_antes_da_assinatura():
    documento = _documento(
        status="RASCUNHO"
    )

    with pytest.raises(
        service.TransicaoStatusNfseInvalida,
        match="nao pode ser marcado",
    ):
        service.preparar_nfse_para_envio(
            documento=documento,
            payload={
                "conteudo": _xml(),
            },
        )

    assert documento.status == "RASCUNHO"
