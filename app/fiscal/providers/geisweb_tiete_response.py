from __future__ import annotations

from dataclasses import dataclass
from xml.etree import ElementTree as ET


class GeisWebResponseError(RuntimeError):
    """
    Erro técnico ao interpretar a resposta SOAP do GeisWeb.

    Informações retornadas pelo servidor podem ser preservadas em atributos,
    mas não são incluídas automaticamente na mensagem da exceção.
    """

    def __init__(
        self,
        message: str,
        *,
        fault_code: str | None = None,
        fault_string: str | None = None,
        raw_response: str | None = None,
    ) -> None:
        super().__init__(message)

        self.fault_code = fault_code
        self.fault_string = fault_string
        self.raw_response = raw_response


@dataclass(frozen=True)
class GeisWebNormalizedResponse:
    operation_response: str
    response_parameter: str
    payload: str
    payload_is_xml: bool


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]

    if ":" in tag:
        return tag.rsplit(":", 1)[1]

    return tag


def _find_first_by_local_name(
    parent: ET.Element,
    local_name: str,
) -> ET.Element | None:
    for element in parent.iter():
        if _local_name(element.tag) == local_name:
            return element

    return None


def _texto_elemento(element: ET.Element | None) -> str | None:
    if element is None:
        return None

    texto = "".join(element.itertext()).strip()
    return texto or None


def _payload_parece_xml(payload: str) -> bool:
    valor = payload.lstrip()

    if not valor.startswith("<"):
        return False

    try:
        ET.fromstring(valor)
    except ET.ParseError:
        return False

    return True


def normalizar_resposta_geisweb(
    response: str | bytes,
    *,
    operation: str = "EnviaSignLoteRps",
    response_parameter: str = "EnviaSignLoteRpsResposta",
) -> GeisWebNormalizedResponse:
    """
    Extrai o xsd:string devolvido pelo SOAP rpc/encoded do GeisWeb.

    A função:
    - não realiza HTTP;
    - não interpreta regras de negócio do XML interno;
    - detecta SOAP Fault;
    - tolera namespaces diferentes;
    - aceita resposta como str ou bytes.
    """

    if isinstance(response, bytes):
        try:
            response_text = response.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise GeisWebResponseError(
                "Resposta SOAP GeisWeb possui codificação inválida."
            ) from exc

    elif isinstance(response, str):
        response_text = response.lstrip("\ufeff")

    else:
        raise GeisWebResponseError(
            "Resposta SOAP GeisWeb deve ser str ou bytes."
        )

    if not response_text.strip():
        raise GeisWebResponseError(
            "Resposta SOAP GeisWeb está vazia."
        )

    try:
        root = ET.fromstring(response_text)

    except ET.ParseError as exc:
        raise GeisWebResponseError(
            "Resposta SOAP GeisWeb possui XML inválido.",
            raw_response=response_text,
        ) from exc

    if _local_name(root.tag) != "Envelope":
        raise GeisWebResponseError(
            "Resposta GeisWeb não contém SOAP Envelope válido.",
            raw_response=response_text,
        )

    body = _find_first_by_local_name(root, "Body")

    if body is None:
        raise GeisWebResponseError(
            "Resposta SOAP GeisWeb não contém Body.",
            raw_response=response_text,
        )

    fault = _find_first_by_local_name(body, "Fault")

    if fault is not None:
        fault_code = _texto_elemento(
            _find_first_by_local_name(
                fault,
                "faultcode",
            )
        )

        fault_string = _texto_elemento(
            _find_first_by_local_name(
                fault,
                "faultstring",
            )
        )

        raise GeisWebResponseError(
            "GeisWeb retornou SOAP Fault.",
            fault_code=fault_code,
            fault_string=fault_string,
            raw_response=response_text,
        )

    parametro = _find_first_by_local_name(
        body,
        response_parameter,
    )

    if parametro is None:
        raise GeisWebResponseError(
            (
                "Resposta SOAP GeisWeb não contém o parâmetro "
                f"{response_parameter}."
            ),
            raw_response=response_text,
        )

    payload = _texto_elemento(parametro)

    if payload is None:
        raise GeisWebResponseError(
            (
                "Parâmetro de resposta SOAP GeisWeb "
                f"{response_parameter} está vazio."
            ),
            raw_response=response_text,
        )

    operation_response = f"{operation}Response"

    ancestral_operacao = None

    for elemento in body.iter():
        if _local_name(elemento.tag) == operation_response:
            ancestral_operacao = elemento
            break

    if ancestral_operacao is None:
        operation_response = _local_name(body.tag)

    return GeisWebNormalizedResponse(
        operation_response=operation_response,
        response_parameter=response_parameter,
        payload=payload,
        payload_is_xml=_payload_parece_xml(payload),
    )