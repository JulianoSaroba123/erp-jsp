"""Provider da NFS-e Nacional / SEFIN.

D24F02-B1:
- registra o provider SEFIN_NACIONAL;
- valida somente configuracao local;
- prepara somente um envelope tecnico local;
- nao gera XML DPS;
- nao assina documento;
- nao realiza HTTP;
- nao acessa ambiente externo.
"""

from app.fiscal.providers.base import NfseProvider
from app.fiscal.providers.sefin_nacional_config import (
    obter_configuracao_sefin,
)
from app.fiscal.providers.registry import (
    normalizar_codigo_provider,
    registrar_provider,
)


@registrar_provider
class SefinNacionalProvider(NfseProvider):
    """Fundacao local do provider da NFS-e Nacional."""

    codigo = "SEFIN_NACIONAL"

    def validar_configuracao(self, configuracao) -> None:
        """Valida somente os dados locais necessarios ao provider."""

        if configuracao is None:
            raise ValueError(
                "Configuracao fiscal nao informada."
            )

        provider = normalizar_codigo_provider(
            getattr(configuracao, "provider", None)
        )

        if provider != self.codigo:
            raise ValueError(
                "Configuracao fiscal nao utiliza o provider "
                "SEFIN_NACIONAL."
            )

        ambiente = str(
            getattr(configuracao, "ambiente", "") or ""
        ).strip().upper()

        if ambiente not in {
            "HOMOLOGACAO",
            "PRODUCAO",
        }:
            raise ValueError(
                "Ambiente fiscal invalido para SEFIN_NACIONAL."
            )

    def preparar_payload(
        self,
        *,
        documento,
        ordem_servico,
        configuracao,
    ) -> dict:
        """Prepara envelope local para futura construcao da DPS.

        Este retorno ainda NAO representa o XML oficial da DPS.
        """

        self.validar_configuracao(configuracao)

        if documento is None:
            raise ValueError(
                "Documento NFS-e nao informado."
            )

        if ordem_servico is None:
            raise ValueError(
                "Ordem de servico nao informada."
            )

        ambiente = str(
            configuracao.ambiente
        ).strip().upper()

        metadados = obter_configuracao_sefin(
            ambiente
        )

        return {
            "provider": self.codigo,
            "ambiente": ambiente,
            "tipo_documento": "DPS",
            "documento_id": getattr(
                documento,
                "id",
                None,
            ),
            "ordem_servico_id": getattr(
                ordem_servico,
                "id",
                None,
            ),
            "layout": {
                "versao": metadados["layout_dps"],
                "perfil_xsd": metadados["perfil_xsd"],
            },
            "municipio_prestador": {
                "codigo_ibge": metadados[
                    "codigo_municipio"
                ],
            },
            "rotas": metadados["rotas"],
            "conteudo": None,
        }
