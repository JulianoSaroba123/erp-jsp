"""Camada de providers da fundacao NFS-e."""

from app.fiscal.providers.base import (
    ErroProviderNfse,
    IntegracaoFiscalDesativada,
    NfseProvider,
)
from app.fiscal.providers.registry import (
    ConflitoRegistroProvider,
    ProviderNaoConfigurado,
    ProviderNaoRegistrado,
    normalizar_codigo_provider,
    obter_provider,
    providers_registrados,
    registrar_provider,
)

from app.fiscal.providers.resolver import resolver_provider_nfse


__all__ = [
    "ConflitoRegistroProvider",
    "ErroProviderNfse",
    "IntegracaoFiscalDesativada",
    "NfseProvider",
    "ProviderNaoConfigurado",
    "ProviderNaoRegistrado",
    "normalizar_codigo_provider",
    "obter_provider",
    "providers_registrados",
    "registrar_provider",
    "resolver_provider_nfse",
]

from app.fiscal.providers.sefin_nacional import SefinNacionalProvider
