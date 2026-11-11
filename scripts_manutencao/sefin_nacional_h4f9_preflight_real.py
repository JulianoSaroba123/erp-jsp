"""H4-F9 - preflight real local e standalone da SEFIN Nacional.

Uso:
    python -X utf8 scripts_manutencao/sefin_nacional_h4f9_preflight_real.py

Requisitos na sessao:
- NFSE_SEFIN_BASE_URL_HOMOLOGACAO
- NFSE_CERTIFICADO_PFX_PATH ou NFSE_CERTIFICADO_PFX_B64_PATH
- NFSE_CERTIFICADO_PFX_PASSWORD, quando o PFX exigir senha

Seguranca:
- NAO importa o pacote app;
- NAO inicializa Flask;
- NAO acessa banco;
- NAO carrega .env;
- NAO realiza HTTP;
- NAO transmite NFS-e;
- NAO imprime senha, chave privada ou caminho do certificado.
"""

from __future__ import annotations

import base64
from contextlib import contextmanager
from datetime import datetime, timezone
import os
from pathlib import Path
import tempfile
from urllib.parse import urlparse

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from lxml import etree


ENV_ENDPOINT = "NFSE_SEFIN_BASE_URL_HOMOLOGACAO"
ENV_PFX = "NFSE_CERTIFICADO_PFX_PATH"
ENV_PFX_B64 = "NFSE_CERTIFICADO_PFX_B64_PATH"
ENV_PFX_PASSWORD = "NFSE_CERTIFICADO_PFX_PASSWORD"

HOST_PRODREST_OFICIAL = "sefin.producaorestrita.nfse.gov.br"
BASE_PATH_OFICIAL = "/API/SefinNacional"
PERFIL_XSD = "PRODREST-v1.01-20261020"
AMBIENTE = "HOMOLOGACAO"
AMBIENTE_EXTERNO = "PRODUCAO_RESTRITA"

RAIZ_REPOSITORIO = Path(__file__).resolve().parents[1]
CAMINHO_XSD = (
    RAIZ_REPOSITORIO
    / "app"
    / "fiscal"
    / "xsd"
    / "sefin_nacional"
    / "1.01"
    / "producao_restrita"
    / "DPS_v1.01.xsd"
)


class PreflightStandaloneInvalido(ValueError):
    """Falha segura no preflight local standalone."""


def _presente(nome: str) -> bool:
    return bool(str(os.environ.get(nome, "") or "").strip())


def _mascarar_fingerprint(fingerprint: str) -> str:
    valor = str(fingerprint or "").strip()

    if len(valor) < 16:
        return "<indisponivel>"

    return valor[:8] + "..." + valor[-8:]


def _validar_variaveis_minimas() -> None:
    ausentes = []

    if not _presente(ENV_ENDPOINT):
        ausentes.append(ENV_ENDPOINT)

    if not (_presente(ENV_PFX) or _presente(ENV_PFX_B64)):
        ausentes.append(f"{ENV_PFX} ou {ENV_PFX_B64}")

    if ausentes:
        raise PreflightStandaloneInvalido(
            "Variaveis obrigatorias ausentes na sessao: "
            + ", ".join(ausentes)
            + "."
        )


def _validar_endpoint() -> str:
    base = str(os.environ.get(ENV_ENDPOINT, "") or "").strip().rstrip("/")

    partes = urlparse(base)

    if partes.scheme.lower() != "https":
        raise PreflightStandaloneInvalido(
            "Endpoint de HOMOLOGACAO deve usar HTTPS."
        )

    if partes.hostname != HOST_PRODREST_OFICIAL:
        raise PreflightStandaloneInvalido(
            "Endpoint de HOMOLOGACAO nao aponta para "
            "a Producao Restrita oficial."
        )

    if (partes.path or "").rstrip("/") != BASE_PATH_OFICIAL:
        raise PreflightStandaloneInvalido(
            "Base operacional de HOMOLOGACAO deve terminar em "
            "/API/SefinNacional."
        )

    return base + "/nfse"


def _validar_xsd() -> None:
    if not CAMINHO_XSD.is_file():
        raise PreflightStandaloneInvalido(
            "XSD PRODREST-v1.01-20261020 nao encontrado."
        )

    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
    )

    try:
        documento = etree.parse(
            str(CAMINHO_XSD),
            parser=parser,
        )
        etree.XMLSchema(documento)
    except (
        etree.XMLSyntaxError,
        etree.XMLSchemaParseError,
        OSError,
    ) as exc:
        raise PreflightStandaloneInvalido(
            "XSD PRODREST-v1.01-20261020 nao pode ser compilado."
        ) from exc


def _ler_pfx() -> tuple[bytes, str]:
    caminho = str(os.environ.get(ENV_PFX, "") or "").strip()
    caminho_b64 = str(os.environ.get(ENV_PFX_B64, "") or "").strip()

    if caminho:
        origem = Path(caminho).expanduser()

        if not origem.is_file():
            raise PreflightStandaloneInvalido(
                "Arquivo PFX configurado nao foi encontrado."
            )

        try:
            dados = origem.read_bytes()
        except OSError as exc:
            raise PreflightStandaloneInvalido(
                "Nao foi possivel ler o arquivo PFX configurado."
            ) from exc

        return dados, "PFX_PATH"

    origem_b64 = Path(caminho_b64).expanduser()

    if not origem_b64.is_file():
        raise PreflightStandaloneInvalido(
            "Arquivo Base64 do PFX configurado nao foi encontrado."
        )

    try:
        texto = origem_b64.read_text(encoding="ascii").strip()
        dados = base64.b64decode(texto, validate=True)
    except (OSError, UnicodeError, ValueError) as exc:
        raise PreflightStandaloneInvalido(
            "Arquivo Base64 do PFX e invalido."
        ) from exc

    return dados, "PFX_B64_PATH"


def _carregar_material_a1():
    dados, origem = _ler_pfx()

    if not dados:
        raise PreflightStandaloneInvalido(
            "Certificado A1 configurado esta vazio."
        )

    senha = os.environ.get(ENV_PFX_PASSWORD)

    if senha is None:
        senha_bytes = None
    else:
        senha_bytes = senha.encode("utf-8")

    try:
        chave_privada, certificado, cadeia = (
            pkcs12.load_key_and_certificates(
                dados,
                senha_bytes,
            )
        )
    except (TypeError, ValueError) as exc:
        raise PreflightStandaloneInvalido(
            "Certificado A1 invalido ou senha incorreta."
        ) from exc

    if not isinstance(chave_privada, rsa.RSAPrivateKey):
        raise PreflightStandaloneInvalido(
            "Chave privada do A1 deve ser RSA."
        )

    if not isinstance(certificado, x509.Certificate):
        raise PreflightStandaloneInvalido(
            "Certificado A1 X.509 nao encontrado."
        )

    chave_publica = certificado.public_key()

    if not isinstance(chave_publica, rsa.RSAPublicKey):
        raise PreflightStandaloneInvalido(
            "Certificado A1 deve possuir chave publica RSA."
        )

    if (
        chave_privada.public_key().public_numbers()
        != chave_publica.public_numbers()
    ):
        raise PreflightStandaloneInvalido(
            "Chave privada do A1 nao corresponde ao certificado."
        )

    agora = datetime.now(timezone.utc)

    if (
        agora < certificado.not_valid_before_utc
        or agora > certificado.not_valid_after_utc
    ):
        raise PreflightStandaloneInvalido(
            "Certificado A1 fora do periodo de validade."
        )

    return (
        chave_privada,
        certificado,
        tuple(cadeia or ()),
        origem,
    )


@contextmanager
def _materializar_mtls(
    chave_privada,
    certificado,
    cadeia,
):
    try:
        chave_pem = chave_privada.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        certificado_pem = certificado.public_bytes(
            serialization.Encoding.PEM
        )

        for item in cadeia:
            if not isinstance(item, x509.Certificate):
                raise PreflightStandaloneInvalido(
                    "Cadeia do A1 possui certificado invalido."
                )

            certificado_pem += item.public_bytes(
                serialization.Encoding.PEM
            )

    except PreflightStandaloneInvalido:
        raise
    except (TypeError, ValueError) as exc:
        raise PreflightStandaloneInvalido(
            "Falha ao serializar material A1 para mTLS."
        ) from exc

    with tempfile.TemporaryDirectory(
        prefix="erp_jsp_nfse_preflight_"
    ) as diretorio:
        raiz = Path(diretorio)
        cert_path = raiz / "cert.pem"
        key_path = raiz / "key.pem"

        cert_path.write_bytes(certificado_pem)
        key_path.write_bytes(chave_pem)

        try:
            os.chmod(cert_path, 0o600)
            os.chmod(key_path, 0o600)
        except OSError:
            pass

        if (
            not cert_path.is_file()
            or not key_path.is_file()
            or cert_path.stat().st_size <= 0
            or key_path.stat().st_size <= 0
        ):
            raise PreflightStandaloneInvalido(
                "Material mTLS temporario nao foi criado corretamente."
            )

        yield


def executar() -> int:
    _validar_variaveis_minimas()
    endpoint = _validar_endpoint()
    _validar_xsd()

    (
        chave_privada,
        certificado,
        cadeia,
        origem_certificado,
    ) = _carregar_material_a1()

    fingerprint = certificado.fingerprint(
        hashes.SHA256()
    ).hex().upper()

    with _materializar_mtls(
        chave_privada,
        certificado,
        cadeia,
    ):
        mtls_ok = True

    print("=== H4-F9 | PREFLIGHT REAL LOCAL SEFIN ===")
    print("STATUS: OK")
    print(f"AMBIENTE: {AMBIENTE}")
    print(f"AMBIENTE EXTERNO: {AMBIENTE_EXTERNO}")
    print(f"PERFIL XSD: {PERFIL_XSD}")
    print(f"ENDPOINT EMISSAO: {endpoint}")
    print(f"ORIGEM CERTIFICADO: {origem_certificado}")
    print(
        "CERTIFICADO SHA256: "
        + _mascarar_fingerprint(fingerprint)
    )
    print("MTLS LOCAL: " + ("OK" if mtls_ok else "FALHA"))
    print("FLASK INICIALIZADO: False")
    print("BANCO ACESSADO: False")
    print("INTEGRACAO ATIVA: False")
    print("REDE UTILIZADA: False")
    print("TRANSMISSAO: NAO EXECUTADA")

    return 0


def main() -> int:
    try:
        return executar()
    except PreflightStandaloneInvalido as exc:
        print("=== H4-F9 | PREFLIGHT REAL LOCAL SEFIN ===")
        print("STATUS: FALHA")
        print("MOTIVO: " + str(exc))
        print("FLASK INICIALIZADO: False")
        print("BANCO ACESSADO: False")
        print("REDE UTILIZADA: False")
        print("TRANSMISSAO: NAO EXECUTADA")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
