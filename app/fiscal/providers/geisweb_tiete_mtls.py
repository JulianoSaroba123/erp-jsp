from __future__ import annotations

import shutil
import ssl
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import requests
from requests.adapters import HTTPAdapter

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12


class GeisWebMtlsError(RuntimeError):
    """Erro de preparação da infraestrutura mTLS do GeisWeb Tietê."""


# OpenSSL SSL_OP_LEGACY_SERVER_CONNECT.
#
# Algumas combinações Python/OpenSSL não expõem a constante através do
# módulo ssl, embora o OpenSSL suporte a opção.
_OP_LEGACY_SERVER_CONNECT = getattr(
    ssl,
    "OP_LEGACY_SERVER_CONNECT",
    0x00000004,
)


def _senha_pkcs12_bytes(senha: str | bytes | None) -> bytes | None:
    if senha is None:
        return None

    if isinstance(senha, bytes):
        return senha

    if not isinstance(senha, str):
        raise GeisWebMtlsError(
            "Senha do certificado A1 deve ser str, bytes ou None."
        )

    return senha.encode("utf-8")


def _extrair_pems_pkcs12(
    certificado_a1: str | Path,
    senha: str | bytes | None,
) -> tuple[bytes, bytes]:
    """
    Extrai certificado/cadeia X509 e chave privada de um PKCS#12.

    A senha nunca é incluída em mensagens de erro.
    """
    caminho = Path(certificado_a1)

    if not caminho.is_file():
        raise GeisWebMtlsError(
            "Arquivo do certificado A1 PKCS#12 não encontrado."
        )

    try:
        dados = caminho.read_bytes()

        chave, certificado, cadeia = pkcs12.load_key_and_certificates(
            dados,
            _senha_pkcs12_bytes(senha),
        )
    except Exception as exc:
        raise GeisWebMtlsError(
            "Não foi possível abrir o certificado A1 PKCS#12."
        ) from exc

    if chave is None:
        raise GeisWebMtlsError(
            "Certificado A1 PKCS#12 não contém chave privada."
        )

    if certificado is None:
        raise GeisWebMtlsError(
            "Certificado A1 PKCS#12 não contém certificado X509."
        )

    try:
        chave_pem = chave.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        certificado_pem = certificado.public_bytes(
            serialization.Encoding.PEM
        )

        for certificado_cadeia in cadeia or ():
            certificado_pem += certificado_cadeia.public_bytes(
                serialization.Encoding.PEM
            )

        return certificado_pem, chave_pem

    except Exception as exc:
        raise GeisWebMtlsError(
            "Não foi possível preparar certificado e chave A1 para mTLS."
        ) from exc


@contextmanager
def _pems_temporarios(
    certificado_pem: bytes,
    chave_pem: bytes,
) -> Iterator[tuple[Path, Path, Path]]:
    """
    Materializa PEMs somente pelo tempo necessário para SSLContext.load_cert_chain.

    Os arquivos são removidos no bloco finally, inclusive em caso de erro.
    """
    diretorio = Path(
        tempfile.mkdtemp(prefix="erp_jsp_geisweb_mtls_")
    )

    caminho_certificado = diretorio / "certificado-cadeia.pem"
    caminho_chave = diretorio / "chave-privada.pem"

    try:
        caminho_certificado.write_bytes(certificado_pem)
        caminho_chave.write_bytes(chave_pem)

        # Proteção best effort. Em Windows o chmod não possui a mesma semântica
        # POSIX, mas ainda evitamos permissões excessivas quando suportado.
        try:
            caminho_certificado.chmod(0o600)
            caminho_chave.chmod(0o600)
        except OSError:
            pass

        yield caminho_certificado, caminho_chave, diretorio

    finally:
        shutil.rmtree(diretorio, ignore_errors=True)


def criar_ssl_context_a1(
    certificado_a1: str | Path,
    senha: str | bytes | None,
    *,
    cafile: str | Path | None = None,
) -> ssl.SSLContext:
    """
    Constrói SSLContext cliente para autenticação mTLS com certificado A1.

    Não realiza qualquer operação HTTP.
    """
    certificado_pem, chave_pem = _extrair_pems_pkcs12(
        certificado_a1,
        senha,
    )

    try:
        contexto = ssl.create_default_context(
            purpose=ssl.Purpose.SERVER_AUTH,
            cafile=str(cafile) if cafile is not None else None,
        )

        contexto.check_hostname = True
        contexto.verify_mode = ssl.CERT_REQUIRED

        if hasattr(ssl, "TLSVersion"):
            contexto.minimum_version = ssl.TLSVersion.TLSv1_2

        contexto.options |= _OP_LEGACY_SERVER_CONNECT

        with _pems_temporarios(
            certificado_pem,
            chave_pem,
        ) as (caminho_certificado, caminho_chave, _):
            contexto.load_cert_chain(
                certfile=str(caminho_certificado),
                keyfile=str(caminho_chave),
            )

        return contexto

    except GeisWebMtlsError:
        raise

    except Exception as exc:
        raise GeisWebMtlsError(
            "Não foi possível construir o SSLContext mTLS do GeisWeb Tietê."
        ) from exc


class GeisWebTieteHTTPSAdapter(HTTPAdapter):
    """
    HTTPAdapter que injeta SSLContext próprio no urllib3.

    O adapter somente configura transporte HTTPS.
    Nenhuma requisição é realizada aqui.
    """

    def __init__(
        self,
        ssl_context: ssl.SSLContext,
        *args,
        **kwargs,
    ) -> None:
        self._ssl_context = ssl_context
        super().__init__(*args, **kwargs)

    @property
    def ssl_context(self) -> ssl.SSLContext:
        return self._ssl_context

    def init_poolmanager(
        self,
        connections,
        maxsize,
        block=False,
        **pool_kwargs,
    ):
        pool_kwargs["ssl_context"] = self._ssl_context

        return super().init_poolmanager(
            connections,
            maxsize,
            block=block,
            **pool_kwargs,
        )

    def proxy_manager_for(self, proxy, **proxy_kwargs):
        proxy_kwargs["ssl_context"] = self._ssl_context
        return super().proxy_manager_for(proxy, **proxy_kwargs)


def criar_session_mtls(
    ssl_context: ssl.SSLContext,
) -> requests.Session:
    """
    Cria Session preparada para HTTPS/mTLS.

    Importante:
    esta função apenas monta a Session.
    Não executa GET, POST ou qualquer acesso de rede.
    """
    if not isinstance(ssl_context, ssl.SSLContext):
        raise GeisWebMtlsError(
            "SSLContext inválido para Session mTLS."
        )

    session = requests.Session()

    session.mount(
        "https://",
        GeisWebTieteHTTPSAdapter(
            ssl_context=ssl_context,
        ),
    )

    return session


def criar_session_a1(
    certificado_a1: str | Path,
    senha: str | bytes | None,
    *,
    cafile: str | Path | None = None,
) -> requests.Session:
    """
    Atalho para criar SSLContext A1 e Session HTTPS/mTLS.

    Não realiza comunicação de rede.
    """
    contexto = criar_ssl_context_a1(
        certificado_a1,
        senha,
        cafile=cafile,
    )

    return criar_session_mtls(contexto)