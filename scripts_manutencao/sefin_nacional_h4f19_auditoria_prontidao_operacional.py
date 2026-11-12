"""H4-F19 - auditoria local de prontidão operacional SEFIN Nacional.

Somente leitura de código-fonte local:
- não acessa banco;
- não carrega certificado;
- não usa rede;
- não executa POST;
- não altera configuração.

Objetivo: separar fundação SEFIN pronta de acoplamentos legados GeisWeb
na camada de rotas/UI antes de qualquer ativação em Produção.
"""

from __future__ import annotations

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

ARQUIVOS = {
    "service": RAIZ / "app" / "fiscal" / "nfse_service.py",
    "provider": (
        RAIZ
        / "app"
        / "fiscal"
        / "providers"
        / "sefin_nacional.py"
    ),
    "routes": (
        RAIZ
        / "app"
        / "ordem_servico"
        / "ordem_servico_routes.py"
    ),
    "template": (
        RAIZ
        / "app"
        / "ordem_servico"
        / "templates"
        / "os"
        / "_painel_fiscal_parcelas.html"
    ),
    "config_routes": (
        RAIZ
        / "app"
        / "configuracao"
        / "configuracao_routes.py"
    ),
}


class AuditoriaProntidaoInvalida(RuntimeError):
    """Falha controlada na auditoria local de prontidão."""


def _ler(
    chave: str,
) -> str:
    caminho = ARQUIVOS[
        chave
    ]

    try:
        return caminho.read_text(
            encoding="utf-8-sig"
        )
    except OSError as exc:
        raise AuditoriaProntidaoInvalida(
            f"Não foi possível ler {caminho}."
        ) from exc


def executar_auditoria() -> dict:
    service = _ler(
        "service"
    )
    provider = _ler(
        "provider"
    )
    routes = _ler(
        "routes"
    )
    template = _ler(
        "template"
    )
    config_routes = _ler(
        "config_routes"
    )

    fundacao_sefin = {
        "provider_registrado": (
            'codigo = "SEFIN_NACIONAL"'
            in provider
        ),
        "transmissao_generica": (
            "def transmitir_payload_nfse("
            in service
            and "def transmitir_e_aplicar_nfse("
            in service
        ),
        "gate_convenio_antes_post": (
            "executar_consulta_convenio_http("
            in provider
            and "executar_emissao_nfse_http("
            in provider
        ),
        "dps_assinada_suportada": (
            "validar_assinatura_xml_dps("
            in service
        ),
    }

    acoplamentos_legados = {
        "precheck_rota_geisweb": (
            "def precheck_nfse_parcela_transmissao"
            in routes
            and "precheck_transmissao_geisweb"
            in routes
        ),
        "transmissao_rota_geisweb": (
            "def transmitir_nfse_parcela_homologacao"
            in routes
            and "transmitir_nfse_geisweb_homologacao_one_shot"
            in routes
        ),
        "ui_menciona_geisweb": (
            "GeisWeb"
            in template
            or "GEISWEB"
            in template
        ),
        "ui_transmissao_so_homologacao": (
            "Transmitir em HOMOLOGA"
            in template
            or "Transmitir em HOMOLOGA&Ccedil;&Atilde;O"
            in template
        ),
    }

    protecoes = {
        "integracao_desativada_ao_salvar": (
            "config_fiscal.integracao_ativa = False"
            in config_routes
        ),
        "one_shot_geisweb_restaura_disjuntor": (
            "finally:"
            in service
            and "configuracao.integracao_ativa = False"
            in service
        ),
        "sem_rota_producao_explicita": (
            "transmitir-producao"
            not in routes
            and "transmitir_nfse_parcela_producao"
            not in routes
        ),
    }

    fundacao_ok = all(
        fundacao_sefin.values()
    )

    legado_presente = any(
        acoplamentos_legados.values()
    )

    producao_bloqueada = (
        protecoes[
            "integracao_desativada_ao_salvar"
        ]
        and protecoes[
            "sem_rota_producao_explicita"
        ]
    )

    if (
        fundacao_ok
        and legado_presente
        and producao_bloqueada
    ):
        classificacao = (
            "BACKEND_SEFIN_PRONTO_UI_ROTAS_LEGADAS_PRODUCAO_BLOQUEADA"
        )
    elif not fundacao_ok:
        classificacao = (
            "FUNDACAO_SEFIN_INCOMPLETA"
        )
    elif not producao_bloqueada:
        classificacao = (
            "REVISAR_PROTECAO_DE_PRODUCAO"
        )
    else:
        classificacao = (
            "REVISAR_ACOPLAMENTOS_OPERACIONAIS"
        )

    bloqueios = []

    if acoplamentos_legados[
        "precheck_rota_geisweb"
    ]:
        bloqueios.append(
            "PRECHECK_ROUTE_GEISWEB"
        )

    if acoplamentos_legados[
        "transmissao_rota_geisweb"
    ]:
        bloqueios.append(
            "TRANSMISSION_ROUTE_GEISWEB"
        )

    if acoplamentos_legados[
        "ui_menciona_geisweb"
    ]:
        bloqueios.append(
            "UI_GEISWEB"
        )

    if acoplamentos_legados[
        "ui_transmissao_so_homologacao"
    ]:
        bloqueios.append(
            "UI_ONLY_HOMOLOGACAO"
        )

    return {
        "classificacao": classificacao,
        "fundacao_sefin": fundacao_sefin,
        "acoplamentos_legados": acoplamentos_legados,
        "protecoes": protecoes,
        "bloqueios": tuple(
            bloqueios
        ),
        "rede_utilizada": False,
        "banco_acessado": False,
        "post_executado": False,
        "arquivos_alterados": False,
    }


def executar() -> int:
    resultado = executar_auditoria()

    print(
        "=== H4-F19 | AUDITORIA PRONTIDAO OPERACIONAL SEFIN ==="
    )
    print(
        "CLASSIFICACAO: "
        + resultado[
            "classificacao"
        ]
    )

    print(
        "FUNDACAO SEFIN:"
    )
    for chave, valor in resultado[
        "fundacao_sefin"
    ].items():
        print(
            f"  {chave}: {valor}"
        )

    print(
        "ACOPLAMENTOS LEGADOS:"
    )
    for chave, valor in resultado[
        "acoplamentos_legados"
    ].items():
        print(
            f"  {chave}: {valor}"
        )

    print(
        "PROTECOES:"
    )
    for chave, valor in resultado[
        "protecoes"
    ].items():
        print(
            f"  {chave}: {valor}"
        )

    print(
        "BLOQUEIOS: "
        + (
            ", ".join(
                resultado[
                    "bloqueios"
                ]
            )
            if resultado[
                "bloqueios"
            ]
            else "<nenhum>"
        )
    )

    print(
        "REDE UTILIZADA: False"
    )
    print(
        "BANCO ACESSADO: False"
    )
    print(
        "POST /nfse: NAO EXECUTADO"
    )
    print(
        "ARQUIVOS ALTERADOS PELO SCRIPT: False"
    )

    return 0


def main() -> int:
    try:
        return executar()
    except AuditoriaProntidaoInvalida as exc:
        print(
            "=== H4-F19 | AUDITORIA PRONTIDAO OPERACIONAL SEFIN ==="
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
        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
