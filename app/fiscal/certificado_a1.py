"""Carregamento seguro de certificado digital A1 para NFS-e.

O certificado e a senha existem somente em memoria.
Nenhum segredo fiscal deve ser persistido no banco.
"""

from dataclasses import dataclass
import base64
from datetime import datetime, timezone
import os
import tempfile
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives.serialization import pkcs12


ENV_PFX_PATH = "NFSE_CERTIFICADO_PFX_PATH"
ENV_PFX_B64_PATH = "NFSE_CERTIFICADO_PFX_B64_PATH"
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


def _materializar_pfx_base64(
    caminho_base64,
) -> Path:
    """Decodifica PFX Base64 para arquivo efemero protegido.

    O Secret File permanece textual no Render.
    O PFX binario existe somente no filesystem efemero do container.
    """

    origem = Path(
        str(caminho_base64 or "").strip()
    ).expanduser()

    if not str(caminho_base64 or "").strip():
        raise CertificadoA1Invalido(
            "Caminho do certificado A1 Base64 nao informado."
        )

    if (
        not origem.exists()
        or not origem.is_file()
    ):
        raise CertificadoA1Invalido(
            "Arquivo Base64 do certificado A1 nao encontrado."
        )

    try:
        conteudo_base64 = (
            origem.read_text(
                encoding="ascii"
            )
            .strip()
        )
    except (
        OSError,
        UnicodeError,
    ) as exc:
        raise CertificadoA1Invalido(
            "Nao foi possivel ler o certificado A1 Base64."
        ) from exc

    if not conteudo_base64:
        raise CertificadoA1Invalido(
            "Arquivo Base64 do certificado A1 esta vazio."
        )

    try:
        dados_pfx = base64.b64decode(
            conteudo_base64,
            validate=True,
        )
    except Exception as exc:
        raise CertificadoA1Invalido(
            "Conteudo Base64 do certificado A1 e invalido."
        ) from exc

    if not dados_pfx:
        raise CertificadoA1Invalido(
            "Certificado A1 decodificado esta vazio."
        )

    diretorio = (
        Path(
            tempfile.gettempdir()
        )
        / "erp_jsp_nfse"
    )

    try:
        diretorio.mkdir(
            parents=True,
            exist_ok=True,
        )

        destino = (
            diretorio
            / f"certificado_a1_{os.getpid()}.pfx"
        )

        temporario = destino.with_suffix(
            ".tmp"
        )

        temporario.write_bytes(
            dados_pfx
        )

        try:
            temporario.chmod(
                0o600
            )
        except OSError:
            pass

        temporario.replace(
            destino
        )

        try:
            destino.chmod(
                0o600
            )
        except OSError:
            pass

        return destino

    except OSError as exc:
        raise CertificadoA1Invalido(
            "Nao foi possivel materializar o certificado A1."
        ) from exc


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

    caminho_base64 = origem.get(
        ENV_PFX_B64_PATH
    )

    if str(caminho or "").strip():
        caminho_resolvido = caminho

    elif str(caminho_base64 or "").strip():
        caminho_resolvido = _materializar_pfx_base64(
            caminho_base64
        )

    else:
        raise CertificadoA1Invalido(
            "Certificado A1 nao configurado. "
            f"Informe {ENV_PFX_PATH} ou {ENV_PFX_B64_PATH}."
        )

    senha = origem.get(
        ENV_PFX_PASSWORD
    )

    return carregar_certificado_a1(
        caminho=caminho_resolvido,
        senha=senha,
        agora=agora,
    )
