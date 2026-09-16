"""Contrato base dos providers NFS-e.

D24F01:
- define somente a fronteira tecnica dos providers;
- nao transmite NFS-e;
- nao consome RPS;
- nao realiza chamadas HTTP;
- nao altera financeiro.
"""

from abc import ABC, abstractmethod
from typing import Any


class ErroProviderNfse(RuntimeError):
    """Erro base da camada de providers NFS-e."""


class IntegracaoFiscalDesativada(ErroProviderNfse):
    """Operacao externa bloqueada pelo disjuntor fiscal."""


class TransmissaoProviderNaoImplementada(ErroProviderNfse):
    """O provider ainda nao possui transporte externo implementado."""


class NfseProvider(ABC):
    """Contrato minimo para providers NFS-e."""

    codigo: str

    @abstractmethod
    def validar_configuracao(self, configuracao) -> None:
        """Valida dados necessarios ao provider sem acessar rede."""

    @abstractmethod
    def preparar_payload(
        self,
        *,
        documento,
        ordem_servico,
        configuracao,
    ) -> dict[str, Any]:
        """Prepara dados locais para futura integracao.

        Esta operacao nao pode transmitir documentos.
        """

    def transmitir(
        self,
        *,
        payload: dict,
        configuracao,
    ) -> dict:
        """Contrato da fronteira externa de transmissao NFS-e.

        A implementacao base nunca realiza comunicacao externa.
        Providers municipais futuros deverao sobrescrever este metodo.
        """

        self.validar_integracao_externa(configuracao)

        raise TransmissaoProviderNaoImplementada(
            "Transmissao NFS-e ainda nao implementada "
            f"para o provider {self.codigo}."
        )

    def validar_integracao_externa(self, configuracao) -> None:
        """Bloqueia operacao externa se a integracao estiver desativada."""

        if not bool(
            getattr(configuracao, "integracao_ativa", False)
        ):
            raise IntegracaoFiscalDesativada(
                "Integracao fiscal externa esta desativada."
            )
