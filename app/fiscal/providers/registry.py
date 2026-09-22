"""Registry dos providers NFS-e.

O registry apenas resolve implementacoes locais.
Nenhuma funcao deste modulo realiza comunicacao externa.
"""

from app.fiscal.providers.base import (
    ErroProviderNfse,
    NfseProvider,
)


class ProviderNaoConfigurado(ErroProviderNfse):
    """Nenhum codigo de provider foi informado."""


class ProviderNaoRegistrado(ErroProviderNfse):
    """O provider configurado ainda nao possui implementacao."""


class ConflitoRegistroProvider(ErroProviderNfse):
    """Tentativa de registrar outro provider com o mesmo codigo."""


_PROVIDERS: dict[str, type[NfseProvider]] = {}


def normalizar_codigo_provider(codigo) -> str | None:
    """Normaliza o identificador utilizado pelo registry."""

    if codigo is None:
        return None

    valor = str(codigo).strip().upper()

    return valor or None


def registrar_provider(
    provider_class: type[NfseProvider],
) -> type[NfseProvider]:
    """Registra uma implementacao de provider pelo seu codigo."""

    if not isinstance(provider_class, type):
        raise TypeError("provider_class deve ser uma classe")

    if not issubclass(provider_class, NfseProvider):
        raise TypeError(
            "provider_class deve herdar de NfseProvider"
        )

    codigo = normalizar_codigo_provider(
        getattr(provider_class, "codigo", None)
    )

    if codigo is None:
        raise ValueError(
            "Provider deve declarar um codigo valido."
        )

    existente = _PROVIDERS.get(codigo)

    if (
        existente is not None
        and existente is not provider_class
    ):
        raise ConflitoRegistroProvider(
            f"Provider {codigo} ja esta registrado."
        )

    _PROVIDERS[codigo] = provider_class

    return provider_class


def obter_provider(codigo) -> NfseProvider:
    """Retorna uma instancia do provider registrado."""

    codigo_normalizado = normalizar_codigo_provider(codigo)

    if codigo_normalizado is None:
        raise ProviderNaoConfigurado(
            "Provider NFS-e nao configurado."
        )

    provider_class = _PROVIDERS.get(
        codigo_normalizado
    )

    if provider_class is None:
        raise ProviderNaoRegistrado(
            "Provider NFS-e "
            f"{codigo_normalizado} ainda nao esta implementado."
        )

    return provider_class()


def providers_registrados() -> tuple[str, ...]:
    """Lista codigos atualmente registrados."""

    return tuple(sorted(_PROVIDERS))
