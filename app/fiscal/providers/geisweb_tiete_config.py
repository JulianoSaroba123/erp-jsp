"""Configuracao tecnica local do provider GeisWeb de Tiete/SP.

Este modulo nao contem senha, certificado ou segredo.

A homologacao foi comprovada tecnicamente em 19/09/2026 por WSDL
obtido diretamente do GeisWeb com mTLS A1.

A URL de producao permanece deliberadamente bloqueada ate a
validacao/credenciamento especifico de Tiete.
"""

CODIGO_PROVIDER = "GEISWEB_TIETE"

MUNICIPIO_IBGE = "3554508"
VERSAO_LAYOUT = "1.01"

NAMESPACE_ENVIO_LOTE_RPS = (
    "http://www.gerenciadecidades.com.br/"
    "xsd/envio_lote_rps_reforma.xsd"
)

ENDPOINT_HOMOLOGACAO = (
    "https://www.gerenciadecidades.com.br/"
    "homologacao/reforma/modelo/webservice/"
    "GeisWebServiceImpl.php"
)

WSDL_HOMOLOGACAO = ENDPOINT_HOMOLOGACAO + "?wsdl"

SOAP_NAMESPACE_HOMOLOGACAO = (
    "urn:"
    + ENDPOINT_HOMOLOGACAO
)

SOAP_ACTION_ENVIA_LOTE_RPS = (
    SOAP_NAMESPACE_HOMOLOGACAO
    + "#EnviaLoteRps"
)


class ConfiguracaoGeisWebTieteInvalida(ValueError):
    """Configuracao tecnica GeisWeb invalida ou ainda nao homologada."""


def normalizar_ambiente_geisweb(ambiente) -> str:
    valor = str(ambiente or "").strip().upper()

    if valor not in {"HOMOLOGACAO", "PRODUCAO"}:
        raise ConfiguracaoGeisWebTieteInvalida(
            "Ambiente GeisWeb deve ser HOMOLOGACAO ou PRODUCAO."
        )

    return valor


def obter_configuracao_geisweb_tiete(ambiente) -> dict:
    ambiente = normalizar_ambiente_geisweb(ambiente)

    if ambiente == "PRODUCAO":
        raise ConfiguracaoGeisWebTieteInvalida(
            "Endpoint de PRODUCAO do GEISWEB_TIETE ainda nao foi "
            "homologado. Transmissao bloqueada por seguranca."
        )

    return {
        "provider": CODIGO_PROVIDER,
        "ambiente": ambiente,
        "municipio_ibge": MUNICIPIO_IBGE,
        "versao_layout": VERSAO_LAYOUT,
        "endpoint": ENDPOINT_HOMOLOGACAO,
        "wsdl": WSDL_HOMOLOGACAO,
        "namespace_xml": NAMESPACE_ENVIO_LOTE_RPS,
        "soap_namespace": SOAP_NAMESPACE_HOMOLOGACAO,
        "soap_action_envia_lote_rps": SOAP_ACTION_ENVIA_LOTE_RPS,
        "soap_version": "1.1",
        "soap_style": "rpc",
        "soap_use": "encoded",
    }
