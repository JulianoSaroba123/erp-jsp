"""Carregamento seguro de certificado digital A1 para NFS-e.

O certificado e a senha existem somente em memoria.
Nenhum segredo fiscal deve ser persistido no banco.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives.serialization import pkcs12


ENV_PFX_PATH = "NFSE_CERTIFICADO_PFX_PATH"
ENV_PFX_PASSWORD = "NFSE_CERTIFICADO_PFX_PASSWORD"


class CertificadoA1Invalido(ValueError):
    """O material criptografico A1 nao pode ser utilizado."""


@dataclass(frozen=True)
class MaterialCertificadoA1:
    """Material PKCS#12 carregado somente em memoria."""

    chave_privada: object
    certificado: x509.Certificate
    cadeia: tuple[x509.Certificate, ...]
    caminho: Path


def _normalizar_agora(agora=None) -> datetime:
    if agora is None:
        return datetime.now(timezone.utc)

    if agora.tzinfo is None:
        raise CertificadoA1Invalido(
            "Data de validacao do certificado deve possuir timezone."
        )

    return agora.astimezone(timezone.utc)


def _validar_periodo_certificado(
    certificado: x509.Certificate,
    *,
    agora=None,
) -> None:
    instante = _normalizar_agora(
        agora
    )

    inicio = certificado.not_valid_before_utc
    fim = certificado.not_valid_after_utc

    if instante < inicio:
        raise CertificadoA1Invalido(
            "Certificado A1 ainda nao esta valido."
        )

    if instante > fim:
        raise CertificadoA1Invalido(
            "Certificado A1 esta expirado."
        )


def carregar_certificado_a1(
    *,
    caminho,
    senha=None,
    agora=None,
) -> MaterialCertificadoA1:
    """Carrega um PKCS#12/PFX sem persistir senha ou chave privada."""

    caminho_normalizado = Path(
        str(caminho or "").strip()
    ).expanduser()

    if not str(caminho or "").strip():
        raise CertificadoA1Invalido(
            "Caminho do certificado A1 nao informado."
        )

    if (
        not caminho_normalizado.exists()
        or not caminho_normalizado.is_file()
    ):
        raise CertificadoA1Invalido(
            "Arquivo do certificado A1 nao encontrado."
        )

    try:
        dados = caminho_normalizado.read_bytes()
    except OSError as exc:
        raise CertificadoA1Invalido(
            "Nao foi possivel ler o certificado A1."
        ) from exc

    if not dados:
        raise CertificadoA1Invalido(
            "Arquivo do certificado A1 esta vazio."
        )

    if senha is None:
        senha_bytes = None
    elif isinstance(senha, bytes):
        senha_bytes = senha
    else:
        senha_bytes = str(senha).encode(
            "utf-8"
        )

    try:
        (
            chave_privada,
            certificado,
            cadeia,
        ) = pkcs12.load_key_and_certificates(
            dados,
            senha_bytes,
        )
    except (TypeError, ValueError) as exc:
        raise CertificadoA1Invalido(
            "Certificado A1 invalido ou senha incorreta."
        ) from exc

    if chave_privada is None:
        raise CertificadoA1Invalido(
            "Certificado A1 nao possui chave privada."
        )

    if certificado is None:
        raise CertificadoA1Invalido(
            "Certificado A1 nao possui certificado X.509."
        )

    _validar_periodo_certificado(
        certificado,
        agora=agora,
    )

    return MaterialCertificadoA1(
        chave_privada=chave_privada,
        certificado=certificado,
        cadeia=tuple(
            cadeia or ()
        ),
        caminho=caminho_normalizado.resolve(),
    )


def carregar_certificado_a1_do_ambiente(
    *,
    ambiente=None,
    agora=None,
) -> MaterialCertificadoA1:
    """Resolve caminho e senha exclusivamente do ambiente local."""

    origem = (
        os.environ
        if ambiente is None
        else ambiente
    )

    caminho = origem.get(
        ENV_PFX_PATH
    )

    if not str(caminho or "").strip():
        raise CertificadoA1Invalido(
            f"Variavel {ENV_PFX_PATH} nao configurada."
        )

    senha = origem.get(
        ENV_PFX_PASSWORD
    )

    return carregar_certificado_a1(
        caminho=caminho,
        senha=senha,
        agora=agora,
    )
