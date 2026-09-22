from types import SimpleNamespace

import pytest

from app.fiscal.providers.base import IntegracaoFiscalDesativada

from app.fiscal.providers import (
    obter_provider,
    providers_registrados,
)
from app.fiscal.providers.base import (
    TransmissaoProviderNaoImplementada,
)
from app.fiscal.providers.geisweb_tiete import (
    GeisWebTieteProvider,
    PreparacaoGeisWebPendente,
)
from app.fiscal.providers.geisweb_tiete_config import (
    ConfiguracaoGeisWebTieteInvalida,
)
from app.fiscal.providers.resolver import (
    resolver_provider_nfse,
)
from app.fiscal.providers.sefin_nacional import (
    SefinNacionalProvider,
)


def _configuracao(
    *,
    provider="GEISWEB_TIETE",
    ambiente="HOMOLOGACAO",
    municipio_ibge="3554508",
):
    return SimpleNamespace(
        provider=provider,
        ambiente=ambiente,
        municipio_ibge=municipio_ibge,
        integracao_ativa=False,
    )


def test_geisweb_tiete_esta_registrado():
    registrados = providers_registrados()

    assert "GEISWEB_TIETE" in registrados


def test_sefin_nacional_continua_registrado():
    registrados = providers_registrados()

    assert "SEFIN_NACIONAL" in registrados

    provider = obter_provider(
        "SEFIN_NACIONAL"
    )

    assert isinstance(
        provider,
        SefinNacionalProvider,
    )


def test_obter_provider_geisweb_tiete():
    provider = obter_provider(
        "GEISWEB_TIETE"
    )

    assert isinstance(
        provider,
        GeisWebTieteProvider,
    )

    assert provider.codigo == "GEISWEB_TIETE"


def test_resolver_provider_geisweb_homologacao():
    provider = resolver_provider_nfse(
        _configuracao()
    )

    assert isinstance(
        provider,
        GeisWebTieteProvider,
    )


def test_geisweb_rejeita_municipio_diferente():
    with pytest.raises(
        ConfiguracaoGeisWebTieteInvalida
    ):
        resolver_provider_nfse(
            _configuracao(
                municipio_ibge="3550308"
            )
        )


def test_geisweb_producao_permanece_bloqueada():
    with pytest.raises(
        ConfiguracaoGeisWebTieteInvalida
    ):
        resolver_provider_nfse(
            _configuracao(
                ambiente="PRODUCAO"
            )
        )


def test_preparacao_local_retorna_payload_tecnico():
    provider = obter_provider(
        "GEISWEB_TIETE"
    )

    payload = provider.preparar_payload(
        documento=SimpleNamespace(
            id=10,
            serie_rps="A",
            numero_rps=7,
        ),
        ordem_servico=SimpleNamespace(
            id=20
        ),
        configuracao=_configuracao(),
    )

    assert payload["provider"] == "GEISWEB_TIETE"
    assert payload["ambiente"] == "HOMOLOGACAO"
    assert payload["tipo_documento"] == "RPS_LOTE"

    assert payload["documento_id"] == 10
    assert payload["ordem_servico_id"] == 20

    assert payload["rps"]["serie"] == "A"
    assert payload["rps"]["numero"] == 7

    assert payload["layout"]["versao"] == "1.01"

    assert (
        payload["municipio_prestador"]["codigo_ibge"]
        == "3554508"
    )

    assert (
        payload["webservice"]["soap_version"]
        == "1.1"
    )

    assert payload["conteudo"] is None


def test_transmissao_geisweb_bloqueia_quando_integracao_desativada():
    provider = obter_provider(
        "GEISWEB_TIETE"
    )

    with pytest.raises(
        IntegracaoFiscalDesativada
    ):
        provider.transmitir(
            payload={},
            configuracao=_configuracao(),
        )
