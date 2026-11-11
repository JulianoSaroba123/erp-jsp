"""H4-F14 - dry-run corrigido após a primeira rejeição SEFIN.

Usa os dados confirmados pela NFS-e Nacional válida da JSP:
- pTotTribSN=2.31
- cTribNac=140101
- cNBS=101061900
- cLocPrestacao=3541653
- sem indTotTrib
- sem pAliq
- sem IM na DPS
- sem xNome quando tpEmit=1

Gera NOVA DPS sintética, valida, assina e empacota em memória.
Não usa rede, não acessa banco e não executa POST /nfse.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


SCRIPT_H4F11 = (
    Path(__file__).resolve().parent
    / "sefin_nacional_h4f11_dry_run_dps.py"
)

PTOTTRIBSN_CONFIRMADO = "2.31"
SERIE_H4F14 = "9999"
NUMERO_DPS_H4F14 = "999999999999998"
DESCRICAO_H4F14 = (
    "HOMOLOGACAO CONTROLADA H4-F14 - "
    "PRE-EMISSAO CORRIGIDA SEM TRANSMISSAO"
)
VERSAO_APLICATIVO_H4F14 = "ERP-JSP-H4F14"


class DryRunH4F14Invalido(RuntimeError):
    """Falha controlada no dry-run corrigido H4-F14."""


def _carregar_h4f11():
    nome = "h4f11_dry_run_h4f14"
    spec = importlib.util.spec_from_file_location(
        nome,
        SCRIPT_H4F11,
    )

    if spec is None or spec.loader is None:
        raise DryRunH4F14Invalido(
            "Nao foi possivel carregar o H4-F11."
        )

    modulo = importlib.util.module_from_spec(
        spec
    )
    sys.modules[
        nome
    ] = modulo
    spec.loader.exec_module(
        modulo
    )
    return modulo


h4f11 = _carregar_h4f11()


def executar_dry_run_corrigido(
    *,
    agora=None,
    material_a1=None,
):
    resultado = h4f11.executar_dry_run(
        agora=agora,
        material_a1=material_a1,
        percentual_tot_trib_sn=PTOTTRIBSN_CONFIRMADO,
        serie=SERIE_H4F14,
        numero_dps=NUMERO_DPS_H4F14,
        descricao=DESCRICAO_H4F14,
        versao_aplicativo=VERSAO_APLICATIVO_H4F14,
    )

    if resultado.id_dps.endswith(
        h4f11.NUMERO_DPS_DRY_RUN
    ):
        raise DryRunH4F14Invalido(
            "H4-F14 reutilizou o numero DPS do primeiro POST."
        )

    return resultado


def executar() -> int:
    resultado = executar_dry_run_corrigido()

    print(
        "=== H4-F14 | DRY-RUN CORRIGIDO DPS HOMOLOGACAO ==="
    )
    print(
        "STATUS: OK"
    )
    print(
        "PTOTTRIBSN CONFIRMADO: 2.31"
    )
    print(
        "SERIE: "
        + SERIE_H4F14
    )
    print(
        "NUMERO DPS: "
        + NUMERO_DPS_H4F14
    )
    print(
        "DPS ID: "
        + h4f11._mascarar_id(
            resultado.id_dps
        )
    )
    print(
        "XSD ANTES ASSINATURA: "
        + str(
            resultado.xsd_antes_ok
        )
    )
    print(
        "ASSINATURA A1: "
        + str(
            resultado.assinatura_ok
        )
    )
    print(
        "XSD DEPOIS ASSINATURA: "
        + str(
            resultado.xsd_depois_ok
        )
    )
    print(
        "XML ASSINADO SHA256: "
        + h4f11._sha256(
            resultado.xml_assinado
        )
    )
    print(
        "CORPO JSON SHA256: "
        + h4f11._sha256(
            resultado.corpo_json
        )
    )
    print(
        "REDE UTILIZADA: False"
    )
    print(
        "POST /nfse: NAO EXECUTADO"
    )
    print(
        "TRANSMISSAO: NAO EXECUTADA"
    )
    print(
        "FLASK INICIALIZADO: False"
    )
    print(
        "BANCO ACESSADO: False"
    )

    return 0


def main() -> int:
    try:
        return executar()
    except (
        DryRunH4F14Invalido,
        h4f11.DryRunDpsInvalido,
        h4f11.h4f9.PreflightStandaloneInvalido,
        h4f11.dps_model.DpsCanonicaInvalida,
        h4f11.serializer.SerializacaoDpsInvalida,
        h4f11.signer.AssinaturaXmlDpsInvalida,
        h4f11.validator.ValidacaoXsdDpsInvalida,
    ) as exc:
        print(
            "=== H4-F14 | DRY-RUN CORRIGIDO DPS HOMOLOGACAO ==="
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
            "POST /nfse: NAO EXECUTADO"
        )
        print(
            "TRANSMISSAO: NAO EXECUTADA"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
