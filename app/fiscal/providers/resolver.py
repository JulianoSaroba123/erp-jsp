"""Resolucao local do provider NFS-e configurado.

D24F01-C10C:
- resolve somente implementacoes locais registradas;
- valida a configuracao exigida pelo provider;
- nao realiza comunicacao externa;
- nao transmite NFS-e;
- nao consome RPS;
- nao altera financeiro.
"""

from app.fiscal.providers.base import NfseProvider
from app.fiscal.providers.registry import obter_provider


def resolver_provider_nfse(configuracao) -> NfseProvider:
    """Resolve e valida localmente o provider da configuracao fiscal."""

    if configuracao is None:
        raise ValueError(
            "Configuracao fiscal nao informada."
        )

    provider = obter_provider(
        getattr(configuracao, "provider", None)
    )

    provider.validar_configuracao(configuracao)

    return provider
