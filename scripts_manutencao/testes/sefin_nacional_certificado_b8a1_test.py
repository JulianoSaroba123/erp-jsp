from datetime import datetime, timedelta, timezone
import base64

import pytest

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from app.fiscal import certificado_a1 as cert_mod


SENHA = "senha-teste-b8a1"


def _gerar_pfx(
    tmp_path,
    *,
    inicio,
    fim,
    senha=SENHA,
):
    chave = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

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
                "CERTIFICADO TESTE B8-A1",
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
            inicio.replace(tzinfo=None)
        )
        .not_valid_after(
            fim.replace(tzinfo=None)
        )
        .sign(
            chave,
            hashes.SHA256(),
        )
    )

    dados_pfx = pkcs12.serialize_key_and_certificates(
        name=b"erp-jsp-b8a1",
        key=chave,
        cert=certificado,
        cas=None,
        encryption_algorithm=(
            serialization.BestAvailableEncryption(
                senha.encode("utf-8")
            )
        ),
    )

    caminho = tmp_path / "certificado_teste.pfx"
    caminho.write_bytes(dados_pfx)

    return caminho, certificado


def test_b8a1_001_carrega_pfx_valido(
    tmp_path,
):
    agora = datetime.now(timezone.utc)

    caminho, certificado_original = _gerar_pfx(
        tmp_path,
        inicio=agora - timedelta(days=1),
        fim=agora + timedelta(days=30),
    )

    material = cert_mod.carregar_certificado_a1(
        caminho=caminho,
        senha=SENHA,
        agora=agora,
    )

    assert material.chave_privada is not None
    assert material.certificado is not None
    assert material.cadeia == ()
    assert material.caminho == caminho.resolve()

    assert (
        material.certificado.serial_number
        == certificado_original.serial_number
    )


def test_b8a1_002_rejeita_senha_incorreta(
    tmp_path,
):
    agora = datetime.now(timezone.utc)

    caminho, _ = _gerar_pfx(
        tmp_path,
        inicio=agora - timedelta(days=1),
        fim=agora + timedelta(days=30),
    )

    with pytest.raises(
        cert_mod.CertificadoA1Invalido,
        match="senha incorreta",
    ):
        cert_mod.carregar_certificado_a1(
            caminho=caminho,
            senha="senha-errada",
            agora=agora,
        )


def test_b8a1_003_rejeita_certificado_expirado(
    tmp_path,
):
    agora = datetime.now(timezone.utc)

    caminho, _ = _gerar_pfx(
        tmp_path,
        inicio=agora - timedelta(days=30),
        fim=agora - timedelta(days=1),
    )

    with pytest.raises(
        cert_mod.CertificadoA1Invalido,
        match="expirado",
    ):
        cert_mod.carregar_certificado_a1(
            caminho=caminho,
            senha=SENHA,
            agora=agora,
        )


def test_b8a1_004_carrega_por_variaveis_de_ambiente(
    tmp_path,
):
    agora = datetime.now(timezone.utc)

    caminho, _ = _gerar_pfx(
        tmp_path,
        inicio=agora - timedelta(days=1),
        fim=agora + timedelta(days=30),
    )

    ambiente = {
        cert_mod.ENV_PFX_PATH: str(caminho),
        cert_mod.ENV_PFX_PASSWORD: SENHA,
    }

    material = (
        cert_mod.carregar_certificado_a1_do_ambiente(
            ambiente=ambiente,
            agora=agora,
        )
    )

    assert material.caminho == caminho.resolve()
    assert material.chave_privada is not None


def test_b8a1_005_rejeita_ambiente_sem_caminho():
    with pytest.raises(
        cert_mod.CertificadoA1Invalido,
        match="NFSE_CERTIFICADO_PFX_PATH",
    ):
        cert_mod.carregar_certificado_a1_do_ambiente(
            ambiente={},
        )


def test_b8a1_006_rejeita_arquivo_inexistente(
    tmp_path,
):
    inexistente = (
        tmp_path
        / "certificado_que_nao_existe.pfx"
    )

    with pytest.raises(
        cert_mod.CertificadoA1Invalido,
        match="nao encontrado",
    ):
        cert_mod.carregar_certificado_a1(
            caminho=inexistente,
            senha=SENHA,
        )


def test_b8a1_007_rejeita_instante_sem_timezone(
    tmp_path,
):
    agora = datetime.now(timezone.utc)

    caminho, _ = _gerar_pfx(
        tmp_path,
        inicio=agora - timedelta(days=1),
        fim=agora + timedelta(days=30),
    )

    with pytest.raises(
        cert_mod.CertificadoA1Invalido,
        match="timezone",
    ):
        cert_mod.carregar_certificado_a1(
            caminho=caminho,
            senha=SENHA,
            agora=datetime.now(),
        )



def test_b8a1_008_carrega_secret_file_base64(
    tmp_path,
):
    agora = datetime.now(timezone.utc)

    caminho_pfx, certificado_original = _gerar_pfx(
        tmp_path,
        inicio=agora - timedelta(days=1),
        fim=agora + timedelta(days=30),
    )

    caminho_base64 = (
        tmp_path
        / "certificado_teste.pfx.b64"
    )

    caminho_base64.write_text(
        base64.b64encode(
            caminho_pfx.read_bytes()
        ).decode("ascii"),
        encoding="ascii",
    )

    ambiente = {
        cert_mod.ENV_PFX_B64_PATH: str(
            caminho_base64
        ),
        cert_mod.ENV_PFX_PASSWORD: SENHA,
    }

    material = (
        cert_mod.carregar_certificado_a1_do_ambiente(
            ambiente=ambiente,
            agora=agora,
        )
    )

    assert material.caminho.exists()
    assert material.caminho.suffix == ".pfx"
    assert material.chave_privada is not None

    assert (
        material.certificado.serial_number
        == certificado_original.serial_number
    )


def test_b8a1_009_rejeita_base64_invalido(
    tmp_path,
):
    arquivo_base64 = (
        tmp_path
        / "certificado_invalido.pfx.b64"
    )

    arquivo_base64.write_text(
        "ISTO-NAO-E-BASE64!",
        encoding="ascii",
    )

    ambiente = {
        cert_mod.ENV_PFX_B64_PATH: str(
            arquivo_base64
        ),
        cert_mod.ENV_PFX_PASSWORD: SENHA,
    }

    with pytest.raises(
        cert_mod.CertificadoA1Invalido,
        match="Base64",
    ):
        cert_mod.carregar_certificado_a1_do_ambiente(
            ambiente=ambiente,
        )
