from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from app.fiscal.certificado_a1 import MaterialCertificadoA1
from app.fiscal.providers.sefin_nacional_http import ClienteHttpSefin
from app.fiscal.providers.sefin_nacional_mtls import (
    materializar_mtls_sefin,
)


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
                "B8-A3.2",
            ),
        ]
    )

    certificado = (
        x509.CertificateBuilder()
        .subject_name(nome)
        .issuer_name(nome)
        .public_key(chave.public_key())
        .serial_number(x509.random_serial_number())
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
        caminho=Path("certificado-teste.pfx"),
    )


class RespostaFake:
    status_code = 200
    headers = {}
    content = b"OK"


class SessaoFake:
    def __init__(self):
        self.chamadas = []

    def request(self, **kwargs):
        self.chamadas.append(kwargs)
        return RespostaFake()


def test_b8a3a2_001_materializa_certificado_e_chave():
    material = _material()

    with materializar_mtls_sefin(material) as caminhos:
        cert, chave = caminhos

        cert_path = Path(cert)
        key_path = Path(chave)

        assert cert_path.exists()
        assert key_path.exists()
        assert b"BEGIN CERTIFICATE" in cert_path.read_bytes()
        assert b"BEGIN PRIVATE KEY" in key_path.read_bytes()


def test_b8a3a2_002_remove_temporarios_ao_final():
    material = _material()

    with materializar_mtls_sefin(material) as caminhos:
        cert_path = Path(caminhos[0])
        key_path = Path(caminhos[1])

        assert cert_path.exists()
        assert key_path.exists()

    assert not cert_path.exists()
    assert not key_path.exists()
    assert not cert_path.parent.exists()


def test_b8a3a2_003_http_recebe_certificado_cliente():
    sessao = SessaoFake()
    cliente = ClienteHttpSefin(session=sessao)
    material = _material()

    with materializar_mtls_sefin(material) as caminhos:
        cliente.requisitar(
            metodo="POST",
            url="https://sefin.teste/nfse",
            conteudo=b"<DPS/>",
            certificado_cliente=caminhos,
        )

        chamada = sessao.chamadas[0]

        assert chamada["cert"] == caminhos
        assert Path(caminhos[0]).exists()
        assert Path(caminhos[1]).exists()


def test_b8a3a2_004_http_sem_mtls_mantem_none():
    sessao = SessaoFake()

    cliente = ClienteHttpSefin(
        session=sessao
    )

    cliente.requisitar(
        metodo="GET",
        url="https://sefin.teste/nfse",
    )

    assert sessao.chamadas[0]["cert"] is None
