"""H4-F9 - preflight real local da SEFIN Nacional.

Uso:
    python -X utf8 scripts_manutencao/sefin_nacional_h4f9_preflight_real.py

Requisitos no ambiente da sessao:
- NFSE_SEFIN_BASE_URL_HOMOLOGACAO
- NFSE_CERTIFICADO_PFX_PATH ou NFSE_CERTIFICADO_PFX_B64_PATH
- NFSE_CERTIFICADO_PFX_PASSWORD, quando o PFX exigir senha

Seguranca:
- nao acessa banco;
- nao carrega .env;
- nao realiza HTTP;
- nao transmite NFS-e;
- nao imprime senha, chave privada ou caminho do certificado.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys
from types import SimpleNamespace


RAIZ_REPOSITORIO = Path(__file__).resolve().parents[1]

if str(RAIZ_REPOSITORIO) not in sys.path:
    sys.path.insert(
        0,
        str(RAIZ_REPOSITORIO),
    )


from app.fiscal.certificado_a1 import CertificadoA1Invalido
from app.fiscal.providers.sefin_nacional_endpoints import (
    ConfiguracaoEndpointSefinInvalida,
)
from app.fiscal.providers.sefin_nacional_mtls import (
    MaterialMtlsSefinInvalido,
)
from app.fiscal.providers.sefin_nacional_preflight import (
    PreflightSefinInvalido,
    executar_preflight_local_sefin,
)


ENV_ENDPOINT = "NFSE_SEFIN_BASE_URL_HOMOLOGACAO"
ENV_PFX = "NFSE_CERTIFICADO_PFX_PATH"
ENV_PFX_B64 = "NFSE_CERTIFICADO_PFX_B64_PATH"
ENV_PFX_PASSWORD = "NFSE_CERTIFICADO_PFX_PASSWORD"


def _presente(nome: str) -> bool:
    return bool(
        str(
            os.environ.get(
                nome,
                "",
            )
            or ""
        ).strip()
    )


def _mascarar_fingerprint(
    fingerprint: str,
) -> str:
    valor = str(
        fingerprint or ""
    ).strip()

    if len(valor) < 16:
        return "<indisponivel>"

    return (
        valor[:8]
        + "..."
        + valor[-8:]
    )


def _validar_variaveis_minimas() -> None:
    ausentes = []

    if not _presente(
        ENV_ENDPOINT
    ):
        ausentes.append(
            ENV_ENDPOINT
        )

    if not (
        _presente(
            ENV_PFX
        )
        or _presente(
            ENV_PFX_B64
        )
    ):
        ausentes.append(
            f"{ENV_PFX} ou {ENV_PFX_B64}"
        )

    if ausentes:
        raise PreflightSefinInvalido(
            "Variaveis obrigatorias ausentes na sessao: "
            + ", ".join(
                ausentes
            )
            + "."
        )


def executar() -> int:
    """Executa o diagnostico real local sem rede."""

    _validar_variaveis_minimas()

    configuracao = SimpleNamespace(
        provider="SEFIN_NACIONAL",
        ambiente="HOMOLOGACAO",
        integracao_ativa=False,
    )

    resultado = executar_preflight_local_sefin(
        configuracao_fiscal=configuracao,
    )

    print("=== H4-F9 | PREFLIGHT REAL LOCAL SEFIN ===")
    print("STATUS: OK")
    print(
        "AMBIENTE: "
        + resultado.ambiente
    )
    print(
        "AMBIENTE EXTERNO: "
        + resultado.ambiente_externo
    )
    print(
        "PERFIL XSD: "
        + resultado.perfil_xsd
    )
    print(
        "ENDPOINT EMISSAO: "
        + resultado.endpoint_emissao
    )
    print(
        "CERTIFICADO SHA256: "
        + _mascarar_fingerprint(
            resultado.certificado_sha256
        )
    )
    print(
        "MTLS LOCAL: "
        + (
            "OK"
            if resultado.mtls_ok
            else "FALHA"
        )
    )
    print(
        "INTEGRACAO ATIVA: "
        + str(
            resultado.integracao_ativa
        )
    )
    print(
        "REDE UTILIZADA: "
        + str(
            resultado.rede_utilizada
        )
    )
    print(
        "TRANSMISSAO: NAO EXECUTADA"
    )

    return 0


def main() -> int:
    try:
        return executar()
    except (
        PreflightSefinInvalido,
        CertificadoA1Invalido,
        MaterialMtlsSefinInvalido,
        ConfiguracaoEndpointSefinInvalida,
    ) as exc:
        print(
            "=== H4-F9 | PREFLIGHT REAL LOCAL SEFIN ==="
        )
        print(
            "STATUS: FALHA"
        )
        print(
            "MOTIVO: "
            + str(
                exc
            )
        )
        print(
            "REDE UTILIZADA: False"
        )
        print(
            "TRANSMISSAO: NAO EXECUTADA"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
