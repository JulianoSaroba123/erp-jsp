from __future__ import annotations

import ssl
from datetime import datetime, timedelta, timezone

import pytest
import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from app.fiscal.providers import geisweb_tiete_mtls as mtls


def _gerar_certificado_a1_teste(tmp_path, senha: bytes = b"senha-teste"):
    agora = datetime.now(timezone.utc)

    chave_ca = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    nome_ca = x509.Name(
        [
            x509.NameAttribute(
                NameOID.COMMON_NAME,
                "ERP JSP CA TESTE",
            )
        ]
    )

    certificado_ca = (
        x509.CertificateBuilder()
        .subject_name(nome_ca)
        .issuer_name(nome_ca)
        .public_key(chave_ca.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(agora - timedelta(days=1))
        .not_valid_after(agora + timedelta(days=365))
        .add_extension(
            x509.BasicConstraints(
                ca=True,
                path_length=None,
            ),
            critical=True,
        )
        .sign(
            private_key=chave_ca,
            algorithm=hashes.SHA256(),
        )
    )

    chave_cliente = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    nome_cliente = x509.Name(
        [
            x509.NameAttribute(
                NameOID.COMMON_NAME,
                "ERP JSP CLIENTE TESTE",
            )
        ]
    )

    certificado_cliente = (
        x509.CertificateBuilder()
        .subject_name(nome_cliente)
        .issuer_name(nome_ca)
        .public_key(chave_cliente.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(agora - timedelta(days=1))
        .not_valid_after(agora + timedelta(days=30))
        .add_extension(
            x509.BasicConstraints(
                ca=False,
                path_length=None,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage(
                [ExtendedKeyUsageOID.CLIENT_AUTH]
            ),
            critical=False,
        )
        .sign(
            private_key=chave_ca,
            algorithm=hashes.SHA256(),
        )
    )

    conteudo_pfx = pkcs12.serialize_key_and_certificates(
        name=b"erp-jsp-teste",
        key=chave_cliente,
        cert=certificado_cliente,
        cas=[certificado_ca],
        encryption_algorithm=serialization.BestAvailableEncryption(
            senha
        ),
    )

    caminho = tmp_path / "cliente-teste.pfx"
    caminho.write_bytes(conteudo_pfx)

    return caminho


def test_f2d1_constroi_ssl_context_a1_com_tls_verify_e_legacy(tmp_path):
    certificado = _gerar_certificado_a1_teste(tmp_path)

    contexto = mtls.criar_ssl_context_a1(
        certificado,
        "senha-teste",
    )

    assert isinstance(contexto, ssl.SSLContext)
    assert contexto.check_hostname is True
    assert contexto.verify_mode == ssl.CERT_REQUIRED

    if hasattr(ssl, "TLSVersion"):
        assert contexto.minimum_version == ssl.TLSVersion.TLSv1_2

    assert (
        contexto.options & mtls._OP_LEGACY_SERVER_CONNECT
    ) == mtls._OP_LEGACY_SERVER_CONNECT


def test_f2d1_inclui_cadeia_x509_e_remove_pems_temporarios(tmp_path):
    certificado = _gerar_certificado_a1_teste(tmp_path)

    certificado_pem, chave_pem = mtls._extrair_pems_pkcs12(
        certificado,
        "senha-teste",
    )

    assert certificado_pem.count(
        b"-----BEGIN CERTIFICATE-----"
    ) == 2

    assert b"PRIVATE KEY" in chave_pem

    with mtls._pems_temporarios(
        certificado_pem,
        chave_pem,
    ) as (
        caminho_certificado,
        caminho_chave,
        diretorio,
    ):
        assert diretorio.exists()
        assert caminho_certificado.exists()
        assert caminho_chave.exists()

    assert not diretorio.exists()
    assert not caminho_certificado.exists()
    assert not caminho_chave.exists()


def test_f2d1_cria_session_https_com_adapter_sem_realizar_http(
    tmp_path,
    monkeypatch,
):
    certificado = _gerar_certificado_a1_teste(tmp_path)

    contexto = mtls.criar_ssl_context_a1(
        certificado,
        "senha-teste",
    )

    chamadas = []

    def request_proibido(*args, **kwargs):
        chamadas.append((args, kwargs))
        raise AssertionError(
            "D1 não pode executar comunicação HTTP."
        )

    monkeypatch.setattr(
        requests.Session,
        "request",
        request_proibido,
    )

    session = mtls.criar_session_mtls(contexto)

    try:
        adapter = session.get_adapter(
            "https://www.gerenciadecidades.com.br"
        )

        assert isinstance(
            adapter,
            mtls.GeisWebTieteHTTPSAdapter,
        )

        assert adapter.ssl_context is contexto
        assert chamadas == []

    finally:
        session.close()


def test_f2d1_senha_incorreta_nao_vaza_segredo_no_erro(tmp_path):
    certificado = _gerar_certificado_a1_teste(
        tmp_path,
        senha=b"SEGREDO-CORRETO",
    )

    segredo_incorreto = "SEGREDO-NAO-PODE-APARECER"

    with pytest.raises(mtls.GeisWebMtlsError) as exc_info:
        mtls.criar_ssl_context_a1(
            certificado,
            segredo_incorreto,
        )

    mensagem = str(exc_info.value)

    assert segredo_incorreto not in mensagem
    assert "PKCS#12" in mensagem


def test_f2d1_rejeita_certificado_a1_inexistente(tmp_path):
    caminho = tmp_path / "nao-existe.pfx"

    with pytest.raises(
        mtls.GeisWebMtlsError,
        match="não encontrado",
    ):
        mtls.criar_ssl_context_a1(
            caminho,
            "qualquer-senha",
        )