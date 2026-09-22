"""Materializacao temporaria de certificado A1 para mTLS SEFIN.

D24F03-B8-A3.2:
- recebe MaterialCertificadoA1 ja validado;
- nao persiste certificado ou chave no banco;
- gera PEM somente durante o contexto;
- inclui cadeia adicional quando disponivel;
- remove integralmente os arquivos temporarios ao final.
"""

from contextlib import contextmanager
import os
from pathlib import Path
import tempfile

from cryptography import x509
from cryptography.hazmat.primitives import serialization


class MaterialMtlsSefinInvalido(ValueError):
    """Material criptografico insuficiente para mTLS SEFIN."""


def _validar_material(
    material_certificado,
):
    if material_certificado is None:
        raise MaterialMtlsSefinInvalido(
            "Material do certificado A1 nao informado."
        )

    chave_privada = getattr(
        material_certificado,
        "chave_privada",
        None,
    )

    certificado = getattr(
        material_certificado,
        "certificado",
        None,
    )

    cadeia = getattr(
        material_certificado,
        "cadeia",
        (),
    )

    if chave_privada is None:
        raise MaterialMtlsSefinInvalido(
            "Material A1 nao possui chave privada."
        )

    if not isinstance(
        certificado,
        x509.Certificate,
    ):
        raise MaterialMtlsSefinInvalido(
            "Material A1 nao possui certificado X.509 valido."
        )

    cadeia_normalizada = []

    for item in cadeia or ():
        if not isinstance(
            item,
            x509.Certificate,
        ):
            raise MaterialMtlsSefinInvalido(
                "Cadeia A1 possui certificado invalido."
            )

        cadeia_normalizada.append(
            item
        )

    return (
        chave_privada,
        certificado,
        tuple(cadeia_normalizada),
    )


def _escrever_privado(
    caminho: Path,
    conteudo: bytes,
) -> None:
    caminho.write_bytes(
        conteudo
    )

    try:
        os.chmod(
            caminho,
            0o600,
        )
    except OSError:
        pass


@contextmanager
def materializar_mtls_sefin(
    material_certificado,
):
    """Entrega (cert.pem, key.pem) apenas durante o contexto."""

    (
        chave_privada,
        certificado,
        cadeia,
    ) = _validar_material(
        material_certificado
    )

    try:
        chave_pem = chave_privada.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    except (TypeError, ValueError) as exc:
        raise MaterialMtlsSefinInvalido(
            "Nao foi possivel serializar a chave privada A1."
        ) from exc

    certificado_pem = certificado.public_bytes(
        serialization.Encoding.PEM
    )

    for certificado_cadeia in cadeia:
        certificado_pem += (
            certificado_cadeia.public_bytes(
                serialization.Encoding.PEM
            )
        )

    with tempfile.TemporaryDirectory(
        prefix="erp_jsp_nfse_mtls_"
    ) as diretorio:
        raiz = Path(
            diretorio
        )

        caminho_certificado = (
            raiz / "cert.pem"
        )

        caminho_chave = (
            raiz / "key.pem"
        )

        _escrever_privado(
            caminho_certificado,
            certificado_pem,
        )

        _escrever_privado(
            caminho_chave,
            chave_pem,
        )

        yield (
            str(caminho_certificado),
            str(caminho_chave),
        )
