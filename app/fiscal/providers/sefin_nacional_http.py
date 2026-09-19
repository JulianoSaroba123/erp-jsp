"""Transporte HTTP isolado do provider SEFIN Nacional.

D24F03-B8-A3.1:
- nao conhece regras de negocio da OS;
- nao assina XML;
- nao carrega certificado;
- nao decide ambiente fiscal;
- exige HTTPS;
- aplica timeout explicito;
- classifica falhas HTTP e de comunicacao;
- nao segue redirecionamentos.
"""

from dataclasses import dataclass
from typing import Mapping

import requests

from app.fiscal.providers.base import (
    ErroAutenticacaoNfse,
    ErroComunicacaoNfse,
    ErroTransmissaoNfse,
    IndisponibilidadeNfse,
)


METODOS_HTTP_PERMITIDOS = frozenset({
    "GET",
    "POST",
    "HEAD",
})

TIMEOUT_CONEXAO_PADRAO = 10
TIMEOUT_LEITURA_PADRAO = 30


@dataclass(frozen=True)
class RespostaHttpSefin:
    metodo: str
    url: str
    status_code: int
    headers: dict
    conteudo: bytes


class ClienteHttpSefin:
    """Cliente HTTP tecnico e injetavel para testes."""

    def __init__(
        self,
        *,
        session=None,
        timeout_conexao=TIMEOUT_CONEXAO_PADRAO,
        timeout_leitura=TIMEOUT_LEITURA_PADRAO,
    ):
        self._session = (
            session
            if session is not None
            else requests.Session()
        )

        self._timeout = self._validar_timeout(
            timeout_conexao,
            timeout_leitura,
        )

    @staticmethod
    def _validar_timeout(
        timeout_conexao,
        timeout_leitura,
    ) -> tuple[float, float]:
        try:
            conexao = float(timeout_conexao)
            leitura = float(timeout_leitura)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Timeout HTTP SEFIN deve ser numerico."
            ) from exc

        if conexao <= 0 or leitura <= 0:
            raise ValueError(
                "Timeout HTTP SEFIN deve ser maior que zero."
            )

        return (
            conexao,
            leitura,
        )

    @staticmethod
    def _normalizar_metodo(metodo) -> str:
        valor = str(
            metodo or ""
        ).strip().upper()

        if valor not in METODOS_HTTP_PERMITIDOS:
            raise ValueError(
                f"Metodo HTTP SEFIN invalido: "
                f"{valor or '<VAZIO>'}."
            )

        return valor

    @staticmethod
    def _validar_url(url) -> str:
        valor = str(
            url or ""
        ).strip()

        if not valor:
            raise ValueError(
                "URL HTTP SEFIN nao informada."
            )

        if not valor.lower().startswith(
            "https://"
        ):
            raise ValueError(
                "URL HTTP SEFIN deve utilizar HTTPS."
            )

        return valor

    @staticmethod
    def _classificar_status(
        *,
        status_code: int,
        metodo: str,
        url: str,
    ) -> None:
        if 200 <= status_code <= 299:
            return

        mensagem = (
            f"SEFIN retornou HTTP {status_code} "
            f"em {metodo} {url}."
        )

        if status_code in {
            401,
            403,
        }:
            raise ErroAutenticacaoNfse(
                mensagem
            )

        if (
            status_code in {
                408,
                425,
                429,
            }
            or 500 <= status_code <= 599
        ):
            raise IndisponibilidadeNfse(
                mensagem
            )

        if 400 <= status_code <= 499:
            raise ErroTransmissaoNfse(
                mensagem
            )

        if 300 <= status_code <= 399:
            raise ErroComunicacaoNfse(
                "Redirecionamento HTTP inesperado. "
                + mensagem
            )

        raise ErroComunicacaoNfse(
            "Status HTTP inesperado. "
            + mensagem
        )

    def requisitar(
        self,
        *,
        metodo,
        url,
        headers: Mapping | None = None,
        conteudo: bytes | bytearray | None = None,
    ) -> RespostaHttpSefin:
        metodo_normalizado = (
            self._normalizar_metodo(
                metodo
            )
        )

        url_normalizada = (
            self._validar_url(
                url
            )
        )

        if conteudo is not None and not isinstance(
            conteudo,
            (bytes, bytearray),
        ):
            raise ValueError(
                "Conteudo HTTP SEFIN deve ser bytes."
            )

        headers_normalizados = dict(
            headers or {}
        )

        try:
            resposta = self._session.request(
                method=metodo_normalizado,
                url=url_normalizada,
                headers=headers_normalizados,
                data=(
                    None
                    if conteudo is None
                    else bytes(conteudo)
                ),
                timeout=self._timeout,
                verify=True,
                allow_redirects=False,
            )
        except requests.Timeout as exc:
            raise ErroComunicacaoNfse(
                "Timeout na comunicacao com a SEFIN Nacional."
            ) from exc
        except requests.ConnectionError as exc:
            raise ErroComunicacaoNfse(
                "Falha de conexao com a SEFIN Nacional."
            ) from exc
        except requests.RequestException as exc:
            raise ErroComunicacaoNfse(
                "Falha HTTP na comunicacao com a SEFIN Nacional."
            ) from exc

        try:
            status_code = int(
                resposta.status_code
            )
        except (TypeError, ValueError) as exc:
            raise ErroComunicacaoNfse(
                "Resposta SEFIN possui status HTTP invalido."
            ) from exc

        self._classificar_status(
            status_code=status_code,
            metodo=metodo_normalizado,
            url=url_normalizada,
        )

        return RespostaHttpSefin(
            metodo=metodo_normalizado,
            url=url_normalizada,
            status_code=status_code,
            headers=dict(
                getattr(
                    resposta,
                    "headers",
                    {},
                )
                or {}
            ),
            conteudo=bytes(
                getattr(
                    resposta,
                    "content",
                    b"",
                )
                or b""
            ),
        )
