"""Configuracao tecnica local do provider SEFIN Nacional.

D24F02-B2:
- define metadados por ambiente;
- nao realiza HTTP;
- nao contem certificado;
- nao contem segredo;
- nao consulta servico externo.
"""

CODIGO_IBGE_TIETE = "3554508"

VERSAO_LAYOUT_DPS = "1.01"

AMBIENTES_SEFIN_NACIONAL = {
    "HOMOLOGACAO": {
        "ambiente_externo": "PRODUCAO_RESTRITA",
        "perfil_xsd": "PRODREST-v1.01-20260727",
        "servico_emissao": "SEFIN_NACIONAL",
        "servico_parametrizacao": "ADN_PARAMETRIZACAO",
    },
    "PRODUCAO": {
        "ambiente_externo": "PRODUCAO",
        "perfil_xsd": "v1.01-20260209",
        "servico_emissao": "SEFIN_NACIONAL",
        "servico_parametrizacao": "ADN_PARAMETRIZACAO",
    },
}

ROTAS_SEFIN_NACIONAL = {
    "emitir_nfse": {
        "metodo": "POST",
        "rota": "/nfse",
    },
    "consultar_nfse": {
        "metodo": "GET",
        "rota": "/nfse/{chave_acesso}",
    },
    "consultar_dps": {
        "metodo": "GET",
        "rota": "/dps/{id_dps}",
    },
    "verificar_dps": {
        "metodo": "HEAD",
        "rota": "/dps/{id_dps}",
    },
    "parametros_convenio": {
        "metodo": "GET",
        "rota": (
            "/parametros_municipais/"
            "{codigo_municipio}/convenio"
        ),
    },
}


def obter_configuracao_sefin(ambiente: str) -> dict:
    """Retorna copia da configuracao tecnica do ambiente."""

    ambiente_normalizado = str(
        ambiente or ""
    ).strip().upper()

    configuracao = AMBIENTES_SEFIN_NACIONAL.get(
        ambiente_normalizado
    )

    if configuracao is None:
        raise ValueError(
            "Ambiente SEFIN Nacional invalido."
        )

    return {
        **configuracao,
        "layout_dps": VERSAO_LAYOUT_DPS,
        "codigo_municipio": CODIGO_IBGE_TIETE,
        "rotas": {
            nome: dict(valor)
            for nome, valor in ROTAS_SEFIN_NACIONAL.items()
        },
    }
