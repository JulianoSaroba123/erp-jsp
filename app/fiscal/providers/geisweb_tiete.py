"""Provider municipal GeisWeb para Tiete/SP.

Estagio atual:
- registrado na arquitetura NFS-e;
- validacao local da configuracao;
- homologacao tecnica conhecida;
- PRODUCAO bloqueada;
- adapter ERP -> GeisWeb ainda nao integrado;
- transmissao externa ainda nao implementada.

Nao realiza rede neste estagio.
"""

from app.fiscal.providers.base import (
    ErroProviderNfse,
    NfseProvider,
    TransmissaoProviderNaoImplementada,
)
from app.fiscal.providers.geisweb_tiete_config import (
    CODIGO_PROVIDER,
    MUNICIPIO_IBGE,
    ConfiguracaoGeisWebTieteInvalida,
    obter_configuracao_geisweb_tiete,
)
from app.fiscal.providers.registry import (
    normalizar_codigo_provider,
    registrar_provider,
)


class PreparacaoGeisWebPendente(ErroProviderNfse):
    """Adapter ERP -> GeisWeb ainda nao foi integrado."""


@registrar_provider
class GeisWebTieteProvider(NfseProvider):
    """Provider da NFS-e municipal GeisWeb de Tiete/SP."""

    codigo = CODIGO_PROVIDER

    def validar_configuracao(self, configuracao) -> None:
        if configuracao is None:
            raise ConfiguracaoGeisWebTieteInvalida(
                "Configuracao fiscal nao informada."
            )

        provider = normalizar_codigo_provider(
            getattr(
                configuracao,
                "provider",
                None,
            )
        )

        if provider != self.codigo:
            raise ConfiguracaoGeisWebTieteInvalida(
                "Configuracao fiscal nao utiliza o provider "
                "GEISWEB_TIETE."
            )

        ambiente = getattr(
            configuracao,
            "ambiente",
            None,
        )

        # Tambem garante que PRODUCAO continue bloqueada
        # enquanto o endpoint real de Tiete nao for homologado.
        obter_configuracao_geisweb_tiete(
            ambiente
        )

        municipio_ibge = str(
            getattr(
                configuracao,
                "municipio_ibge",
                "",
            )
            or ""
        ).strip()

        if municipio_ibge != MUNICIPIO_IBGE:
            raise ConfiguracaoGeisWebTieteInvalida(
                "GEISWEB_TIETE somente pode ser utilizado "
                f"para o municipio IBGE {MUNICIPIO_IBGE}."
            )

    def preparar_payload(
        self,
        documento,
        ordem_servico,
        configuracao,
    ):
        """Bloqueia preparacao ate o adapter ERP -> GeisWeb existir."""

        self.validar_configuracao(
            configuracao
        )

        raise PreparacaoGeisWebPendente(
            "Provider GEISWEB_TIETE registrado, mas o adapter "
            "ERP -> GeisWeb ainda nao foi integrado."
        )

    def transmitir(
        self,
        payload,
        configuracao,
    ):
        """Transmissao externa permanece desabilitada."""

        self.validar_configuracao(
            configuracao
        )

        raise TransmissaoProviderNaoImplementada(
            "Transmissao externa do provider GEISWEB_TIETE "
            "ainda nao esta habilitada."
        )
