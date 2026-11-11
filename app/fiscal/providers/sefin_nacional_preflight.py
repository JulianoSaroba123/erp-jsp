"""Preflight local e sem rede da integracao SEFIN Nacional.

H4-F8:
- aceita somente HOMOLOGACAO;
- exige o disjuntor externo desativado;
- valida perfil PRODREST e XSD local;
- valida endpoint operacional de Producao Restrita;
- valida material A1 e sua materializacao mTLS;
- nao realiza HTTP;
- nao transmite NFS-e.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa

from app.fiscal.certificado_a1 import (
    carregar_certificado_a1_do_ambiente,
)
from app.fiscal.providers.sefin_nacional_config import (
    obter_configuracao_sefin,
)
from app.fiscal.providers.sefin_nacional_endpoints import (
    ConfiguracaoEndpointSefinInvalida,
    compor_url,
    obter_base_url,
)
from app.fiscal.providers.sefin_nacional_mtls import (
    materializar_mtls_sefin,
)
from app.fiscal.xsd import obter_caminho_xsd_dps


HOST_PRODREST_OFICIAL = (
    "sefin.producaorestrita.nfse.gov.br"
)
PERFIL_XSD_PRODREST = (
    "PRODREST-v1.01-20261020"
)


class PreflightSefinInvalido(ValueError):
    """Configuracao local nao esta segura para o proximo marco."""


@dataclass(frozen=True)
class ResultadoPreflightSefin:
    ambiente: str
    ambiente_externo: str
    perfil_xsd: str
    caminho_xsd: str
    base_url: str
    endpoint_emissao: str
    certificado_sha256: str
    mtls_ok: bool
    integracao_ativa: bool
    rede_utilizada: bool


def _validar_configuracao_local(
    configuracao_fiscal,
) -> str:
    if configuracao_fiscal is None:
        raise PreflightSefinInvalido(
            "Configuracao fiscal nao informada."
        )

    provider = str(
        getattr(
            configuracao_fiscal,
            "provider",
            "",
        )
        or ""
    ).strip().upper()

    if provider != "SEFIN_NACIONAL":
        raise PreflightSefinInvalido(
            "Preflight exige provider SEFIN_NACIONAL."
        )

    ambiente = str(
        getattr(
            configuracao_fiscal,
            "ambiente",
            "",
        )
        or ""
    ).strip().upper()

    if ambiente != "HOMOLOGACAO":
        raise PreflightSefinInvalido(
            "H4-F8 aceita somente HOMOLOGACAO."
        )

    if bool(
        getattr(
            configuracao_fiscal,
            "integracao_ativa",
            False,
        )
    ):
        raise PreflightSefinInvalido(
            "Disjuntor fiscal deve permanecer desativado "
            "durante o preflight local."
        )

    return ambiente


def _validar_endpoint_prodrest(
    *,
    ambiente: str,
    metadados: dict,
) -> tuple[str, str]:
    rota = metadados[
        "rotas"
    ][
        "emitir_nfse"
    ]

    if str(
        rota.get("metodo") or ""
    ).strip().upper() != "POST":
        raise PreflightSefinInvalido(
            "Rota de emissao SEFIN deve utilizar POST."
        )

    try:
        base_url = obter_base_url(
            ambiente=ambiente,
            servico=rota["servico"],
        )
    except ConfiguracaoEndpointSefinInvalida as exc:
        raise PreflightSefinInvalido(
            f"Endpoint operacional invalido: {exc}"
        ) from exc

    partes = urlparse(
        base_url
    )

    if (
        partes.scheme.lower() != "https"
        or partes.hostname != HOST_PRODREST_OFICIAL
    ):
        raise PreflightSefinInvalido(
            "Endpoint de HOMOLOGACAO nao aponta para "
            "a Producao Restrita oficial."
        )

    caminho_base = (
        partes.path or ""
    ).rstrip("/")

    if caminho_base != "/API/SefinNacional":
        raise PreflightSefinInvalido(
            "Base operacional da SEFIN em HOMOLOGACAO "
            "deve terminar em /API/SefinNacional."
        )

    try:
        endpoint = compor_url(
            ambiente=ambiente,
            servico=rota["servico"],
            rota=rota["rota"],
        )
    except ConfiguracaoEndpointSefinInvalida as exc:
        raise PreflightSefinInvalido(
            f"Endpoint de emissao invalido: {exc}"
        ) from exc

    return (
        base_url,
        endpoint,
    )


def executar_preflight_local_sefin(
    *,
    configuracao_fiscal,
    material_certificado=None,
) -> ResultadoPreflightSefin:
    """Executa verificacoes locais sem qualquer chamada HTTP."""

    ambiente = _validar_configuracao_local(
        configuracao_fiscal
    )

    metadados = obter_configuracao_sefin(
        ambiente
    )

    if (
        metadados.get("ambiente_externo")
        != "PRODUCAO_RESTRITA"
    ):
        raise PreflightSefinInvalido(
            "Ambiente externo esperado e PRODUCAO_RESTRITA."
        )

    if (
        metadados.get("perfil_xsd")
        != PERFIL_XSD_PRODREST
    ):
        raise PreflightSefinInvalido(
            "Perfil XSD da HOMOLOGACAO diverge do release 20261020."
        )

    caminho_xsd = obter_caminho_xsd_dps(
        metadados["layout_dps"],
        ambiente=ambiente,
    )

    if not Path(
        caminho_xsd
    ).is_file():
        raise PreflightSefinInvalido(
            "XSD da Producao Restrita nao encontrado."
        )

    base_url, endpoint = (
        _validar_endpoint_prodrest(
            ambiente=ambiente,
            metadados=metadados,
        )
    )

    material = (
        material_certificado
        if material_certificado is not None
        else carregar_certificado_a1_do_ambiente()
    )

    certificado = getattr(
        material,
        "certificado",
        None,
    )
    chave_privada = getattr(
        material,
        "chave_privada",
        None,
    )

    if not isinstance(
        certificado,
        x509.Certificate,
    ):
        raise PreflightSefinInvalido(
            "Material A1 nao possui certificado X.509 valido."
        )

    if not isinstance(
        chave_privada,
        rsa.RSAPrivateKey,
    ):
        raise PreflightSefinInvalido(
            "Chave privada do A1 deve ser RSA."
        )

    chave_publica = certificado.public_key()

    if not isinstance(
        chave_publica,
        rsa.RSAPublicKey,
    ):
        raise PreflightSefinInvalido(
            "Certificado A1 deve possuir chave publica RSA."
        )

    if (
        chave_privada.public_key().public_numbers()
        != chave_publica.public_numbers()
    ):
        raise PreflightSefinInvalido(
            "Chave privada do A1 nao corresponde ao certificado."
        )

    agora = datetime.now(
        timezone.utc
    )

    if (
        agora < certificado.not_valid_before_utc
        or agora > certificado.not_valid_after_utc
    ):
        raise PreflightSefinInvalido(
            "Certificado A1 fora do periodo de validade."
        )

    try:
        fingerprint = certificado.fingerprint(
            hashes.SHA256()
        ).hex().upper()

        with materializar_mtls_sefin(
            material
        ) as caminhos:
            cert_path = Path(
                caminhos[0]
            )
            key_path = Path(
                caminhos[1]
            )

            if (
                not cert_path.is_file()
                or not key_path.is_file()
            ):
                raise PreflightSefinInvalido(
                    "Material mTLS temporario nao foi criado."
                )

            if (
                cert_path.stat().st_size <= 0
                or key_path.stat().st_size <= 0
            ):
                raise PreflightSefinInvalido(
                    "Material mTLS temporario esta vazio."
                )

    except PreflightSefinInvalido:
        raise
    except Exception as exc:
        raise PreflightSefinInvalido(
            "Falha ao validar material A1/mTLS localmente."
        ) from exc

    return ResultadoPreflightSefin(
        ambiente=ambiente,
        ambiente_externo=metadados[
            "ambiente_externo"
        ],
        perfil_xsd=metadados[
            "perfil_xsd"
        ],
        caminho_xsd=str(
            caminho_xsd
        ),
        base_url=base_url,
        endpoint_emissao=endpoint,
        certificado_sha256=fingerprint,
        mtls_ok=True,
        integracao_ativa=False,
        rede_utilizada=False,
    )
