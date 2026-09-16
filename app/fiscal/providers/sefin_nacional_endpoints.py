"""Resolucao segura de endpoints do provider SEFIN Nacional.

D24F02-B3:
- separa SEFIN Nacional de Parametros Municipais;
- bases operacionais vem de variaveis de ambiente;
- nao realiza HTTP;
- nao contem certificado ou segredo;
- nao assume que URL de Swagger e URL de runtime.
"""

import os


class ConfiguracaoEndpointSefinInvalida(ValueError):
    """Endpoint operacional SEFIN ausente ou invalido."""


URLS_DOCUMENTACAO_SEFIN = {
    "HOMOLOGACAO": {
        "SEFIN_NACIONAL": (
            "https://sefin.producaorestrita.nfse.gov.br/"
            "API/SefinNacional/docs/index"
        ),
        "PARAMETRIZACAO": (
            "https://adn.producaorestrita.nfse.gov.br/"
            "parametrizacao/docs/index.html"
        ),
    },
    "PRODUCAO": {
        "SEFIN_NACIONAL": (
            "https://sefin.nfse.gov.br/"
            "SefinNacional/docs/index"
        ),
        "PARAMETRIZACAO": (
            "https://adn.nfse.gov.br/"
            "parametrizacao/docs/index.html"
        ),
    },
}


_VARIAVEIS_BASE = {
    "HOMOLOGACAO": {
        "SEFIN_NACIONAL": (
            "NFSE_SEFIN_BASE_URL_HOMOLOGACAO"
        ),
        "PARAMETRIZACAO": (
            "NFSE_PARAMETRIZACAO_BASE_URL_HOMOLOGACAO"
        ),
    },
    "PRODUCAO": {
        "SEFIN_NACIONAL": (
            "NFSE_SEFIN_BASE_URL_PRODUCAO"
        ),
        "PARAMETRIZACAO": (
            "NFSE_PARAMETRIZACAO_BASE_URL_PRODUCAO"
        ),
    },
}


def _normalizar_ambiente(ambiente) -> str:
    valor = str(
        ambiente or ""
    ).strip().upper()

    if valor not in _VARIAVEIS_BASE:
        raise ConfiguracaoEndpointSefinInvalida(
            "Ambiente SEFIN Nacional invalido."
        )

    return valor


def obter_base_url(
    *,
    ambiente,
    servico: str,
) -> str:
    """Obtem base operacional configurada para o servico."""

    ambiente_normalizado = _normalizar_ambiente(
        ambiente
    )

    servico_normalizado = str(
        servico or ""
    ).strip().upper()

    variaveis = _VARIAVEIS_BASE[
        ambiente_normalizado
    ]

    nome_variavel = variaveis.get(
        servico_normalizado
    )

    if nome_variavel is None:
        raise ConfiguracaoEndpointSefinInvalida(
            f"Servico SEFIN desconhecido: "
            f"{servico_normalizado or '<VAZIO>'}."
        )

    base_url = str(
        os.getenv(nome_variavel, "") or ""
    ).strip().rstrip("/")

    if not base_url:
        raise ConfiguracaoEndpointSefinInvalida(
            f"Variavel {nome_variavel} nao configurada."
        )

    if not base_url.lower().startswith("https://"):
        raise ConfiguracaoEndpointSefinInvalida(
            f"Variavel {nome_variavel} deve usar HTTPS."
        )

    return base_url


def compor_url(
    *,
    ambiente,
    servico: str,
    rota: str,
    **parametros,
) -> str:
    """Compoe URL sem realizar requisicao externa."""

    base_url = obter_base_url(
        ambiente=ambiente,
        servico=servico,
    )

    rota_normalizada = str(
        rota or ""
    ).strip()

    if not rota_normalizada.startswith("/"):
        raise ConfiguracaoEndpointSefinInvalida(
            "Rota SEFIN deve iniciar com '/'."
        )

    try:
        rota_resolvida = rota_normalizada.format(
            **parametros
        )
    except KeyError as exc:
        raise ConfiguracaoEndpointSefinInvalida(
            "Parametro obrigatorio ausente na rota SEFIN: "
            f"{exc.args[0]}."
        ) from exc

    if "{" in rota_resolvida or "}" in rota_resolvida:
        raise ConfiguracaoEndpointSefinInvalida(
            "Rota SEFIN possui parametros nao resolvidos."
        )

    return base_url + rota_resolvida
