"""Contrato das operacoes SOAP GeisWeb Tiete.

Fonte operacional:
WSDL vivo de homologacao mapeado pelo ERP JSP.

Este modulo nao transmite e nao escolhe automaticamente
entre envio assinado e nao assinado.
"""

from dataclasses import dataclass

from app.fiscal.providers.geisweb_tiete_config import (
    ENDPOINT_HOMOLOGACAO,
    SOAP_NAMESPACE_HOMOLOGACAO,
)


OPERACAO_ENVIA_LOTE_RPS = "EnviaLoteRps"
OPERACAO_ENVIA_SIGN_LOTE_RPS = "EnviaSignLoteRps"


class OperacaoGeisWebInvalida(ValueError):
    """Operacao SOAP GeisWeb invalida."""


class ModoAssinaturaGeisWebNaoDefinido(ValueError):
    """O modo de assinatura ainda nao foi homologado para o prestador."""


@dataclass(frozen=True)
class OperacaoGeisWeb:
    nome: str
    soap_action: str
    assinatura_xml: bool
    endpoint: str


OPERACOES = {
    OPERACAO_ENVIA_LOTE_RPS: OperacaoGeisWeb(
        nome=OPERACAO_ENVIA_LOTE_RPS,
        soap_action=(
            SOAP_NAMESPACE_HOMOLOGACAO
            + "#EnviaLoteRps"
        ),
        assinatura_xml=False,
        endpoint=ENDPOINT_HOMOLOGACAO,
    ),
    OPERACAO_ENVIA_SIGN_LOTE_RPS: OperacaoGeisWeb(
        nome=OPERACAO_ENVIA_SIGN_LOTE_RPS,
        soap_action=(
            SOAP_NAMESPACE_HOMOLOGACAO
            + "#EnviaSignLoteRps"
        ),
        assinatura_xml=True,
        endpoint=ENDPOINT_HOMOLOGACAO,
    ),
}


def obter_operacao_geisweb(nome) -> OperacaoGeisWeb:
    nome = str(nome or "").strip()

    operacao = OPERACOES.get(nome)

    if operacao is None:
        raise OperacaoGeisWebInvalida(
            f"Operacao GeisWeb invalida: {nome!r}."
        )

    return operacao


def resolver_operacao_envio_geisweb(
    *,
    assinatura_xml,
) -> OperacaoGeisWeb:
    """Resolve somente quando a politica foi definida explicitamente."""

    if assinatura_xml is None:
        raise ModoAssinaturaGeisWebNaoDefinido(
            "Modo de assinatura do GEISWEB_TIETE ainda nao "
            "foi homologado para o prestador."
        )

    if not isinstance(assinatura_xml, bool):
        raise ModoAssinaturaGeisWebNaoDefinido(
            "assinatura_xml deve ser True ou False."
        )

    if assinatura_xml:
        return obter_operacao_geisweb(
            OPERACAO_ENVIA_SIGN_LOTE_RPS
        )

    return obter_operacao_geisweb(
        OPERACAO_ENVIA_LOTE_RPS
    )
