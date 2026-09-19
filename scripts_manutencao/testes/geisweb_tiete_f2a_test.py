import pytest

from app.fiscal.providers.geisweb_tiete_operacoes import (
    ModoAssinaturaGeisWebNaoDefinido,
    OPERACAO_ENVIA_LOTE_RPS,
    OPERACAO_ENVIA_SIGN_LOTE_RPS,
    obter_operacao_geisweb,
    resolver_operacao_envio_geisweb,
)


def test_operacao_envio_sem_assinatura():
    operacao = resolver_operacao_envio_geisweb(
        assinatura_xml=False
    )

    assert operacao.nome == OPERACAO_ENVIA_LOTE_RPS
    assert operacao.assinatura_xml is False
    assert operacao.soap_action.endswith(
        "#EnviaLoteRps"
    )


def test_operacao_envio_assinado():
    operacao = resolver_operacao_envio_geisweb(
        assinatura_xml=True
    )

    assert (
        operacao.nome
        == OPERACAO_ENVIA_SIGN_LOTE_RPS
    )

    assert operacao.assinatura_xml is True

    assert operacao.soap_action.endswith(
        "#EnviaSignLoteRps"
    )


def test_nao_escolhe_modo_automaticamente():
    with pytest.raises(
        ModoAssinaturaGeisWebNaoDefinido
    ):
        resolver_operacao_envio_geisweb(
            assinatura_xml=None
        )


def test_operacoes_usam_mesmo_endpoint_homologacao():
    normal = obter_operacao_geisweb(
        OPERACAO_ENVIA_LOTE_RPS
    )

    assinada = obter_operacao_geisweb(
        OPERACAO_ENVIA_SIGN_LOTE_RPS
    )

    assert normal.endpoint == assinada.endpoint

    assert (
        "/homologacao/reforma/modelo/"
        in normal.endpoint
    )
