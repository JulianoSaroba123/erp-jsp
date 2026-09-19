from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import requests


class GeisWebHttpError(RuntimeError):
    """
    Erro técnico do transporte HTTP GeisWeb.

    O conteúdo da resposta pode ser preservado nos atributos,
    mas não é incluído automaticamente na mensagem da exceção.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_text: str | None = None,
        response_content: bytes | None = None,
        response_headers: Mapping[str, str] | None = None,
        original_error: Exception | None = None,
    ) -> None:
        super().__init__(message)

        self.status_code = status_code
        self.response_text = response_text
        self.response_content = response_content
        self.response_headers = dict(response_headers or {})
        self.original_error = original_error


@dataclass(frozen=True)
class GeisWebHttpResponse:
    status_code: int
    text: str
    content: bytes
    headers: dict[str, str]


def _normalizar_soap_action(soap_action: str) -> str:
    if not isinstance(soap_action, str):
        raise GeisWebHttpError(
            "SOAPAction do GeisWeb é inválido."
        )

    action = soap_action.strip()

    if not action:
        raise GeisWebHttpError(
            "SOAPAction do GeisWeb não foi informado."
        )

    if action.startswith('"') and action.endswith('"'):
        action = action[1:-1].strip()

    if not action:
        raise GeisWebHttpError(
            "SOAPAction do GeisWeb não foi informado."
        )

    return f'"{action}"'


def _validar_endpoint_https(endpoint: str) -> str:
    if not isinstance(endpoint, str):
        raise GeisWebHttpError(
            "Endpoint GeisWeb é inválido."
        )

    endpoint_normalizado = endpoint.strip()

    if not endpoint_normalizado:
        raise GeisWebHttpError(
            "Endpoint GeisWeb não foi informado."
        )

    if not endpoint_normalizado.lower().startswith("https://"):
        raise GeisWebHttpError(
            "Endpoint GeisWeb deve utilizar HTTPS."
        )

    return endpoint_normalizado


def enviar_soap_geisweb(
    session,
    *,
    endpoint: str,
    soap_action: str,
    envelope: str | bytes,
    timeout: float | tuple[float, float] = (10.0, 60.0),
) -> GeisWebHttpResponse:
    """
    Executa somente o transporte HTTP SOAP 1.1 do GeisWeb.

    Não cria SSLContext.
    Não abre certificado A1.
    Não monta XML fiscal.
    Não assina XML.
    Não monta SOAP.
    Não interpreta funcionalmente a resposta.
    """

    endpoint_normalizado = _validar_endpoint_https(endpoint)

    post = getattr(session, "post", None)

    if not callable(post):
        raise GeisWebHttpError(
            "Session HTTP GeisWeb não possui operação POST válida."
        )

    if isinstance(envelope, str):
        payload = envelope.encode("utf-8")
    elif isinstance(envelope, bytes):
        payload = envelope
    else:
        raise GeisWebHttpError(
            "Envelope SOAP GeisWeb deve ser str ou bytes."
        )

    if not payload:
        raise GeisWebHttpError(
            "Envelope SOAP GeisWeb está vazio."
        )

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": _normalizar_soap_action(soap_action),
    }

    try:
        response = post(
            endpoint_normalizado,
            data=payload,
            headers=headers,
            timeout=timeout,
        )

    except requests.RequestException as exc:
        raise GeisWebHttpError(
            "Falha de transporte HTTP ao comunicar com o GeisWeb Tietê.",
            original_error=exc,
        ) from exc

    status_code = int(response.status_code)
    response_text = response.text
    response_content = response.content
    response_headers = dict(response.headers)

    if not 200 <= status_code < 300:
        raise GeisWebHttpError(
            f"GeisWeb Tietê respondeu HTTP {status_code}.",
            status_code=status_code,
            response_text=response_text,
            response_content=response_content,
            response_headers=response_headers,
        )

    return GeisWebHttpResponse(
        status_code=status_code,
        text=response_text,
        content=response_content,
        headers=response_headers,
    )