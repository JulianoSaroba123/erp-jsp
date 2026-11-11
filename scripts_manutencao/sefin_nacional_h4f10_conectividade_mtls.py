"""H4-F10 - conectividade real mTLS com a SEFIN Produção Restrita.

Executa UMA consulta HEAD /dps/{id} com ID sintético.
Não envia DPS, não usa POST, não emite NFS-e e não acessa banco.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import requests
from cryptography.hazmat.primitives import hashes


SCRIPT_H4F9 = (
    Path(__file__).resolve().parent
    / "sefin_nacional_h4f9_preflight_real.py"
)

ID_DPS_SINTETICO = (
    "DPS"
    "3554508"
    "2"
    "00000000000000"
    "00001"
    "999999999999999"
)

TIMEOUT = (
    10,
    30,
)


def _carregar_h4f9():
    spec = importlib.util.spec_from_file_location(
        "h4f9_preflight_real",
        SCRIPT_H4F9,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            "Nao foi possivel carregar o preflight H4-F9."
        )

    modulo = importlib.util.module_from_spec(
        spec
    )
    spec.loader.exec_module(
        modulo
    )
    return modulo


preflight = _carregar_h4f9()


class ConectividadeSefinInvalida(RuntimeError):
    """Falha na conectividade real segura com a SEFIN."""


class ResultadoConectividade:
    def __init__(
        self,
        *,
        sucesso,
        http_status,
        classificacao,
        metodo,
        servidor_alcancado,
        certificado_cliente_enviado,
        autenticacao_rejeitada,
        rede_utilizada,
        transmissao_executada,
    ):
        self.sucesso = bool(sucesso)
        self.http_status = int(http_status)
        self.classificacao = str(classificacao)
        self.metodo = str(metodo)
        self.servidor_alcancado = bool(
            servidor_alcancado
        )
        self.certificado_cliente_enviado = bool(
            certificado_cliente_enviado
        )
        self.autenticacao_rejeitada = bool(
            autenticacao_rejeitada
        )
        self.rede_utilizada = bool(
            rede_utilizada
        )
        self.transmissao_executada = bool(
            transmissao_executada
        )


def _validar_id_sintetico() -> None:
    if (
        len(ID_DPS_SINTETICO) != 45
        or not ID_DPS_SINTETICO.startswith("DPS")
        or not ID_DPS_SINTETICO[3:].isdigit()
    ):
        raise ConectividadeSefinInvalida(
            "ID DPS sintetico do H4-F10 e invalido."
        )


def _classificar_http(
    status_code: int,
) -> tuple[bool, str, bool]:
    if status_code in {
        200,
        204,
    }:
        return (
            True,
            "HEAD_PROCESSADO_DPS_EXISTENTE",
            False,
        )

    if status_code == 404:
        return (
            True,
            "HEAD_PROCESSADO_DPS_NAO_ENCONTRADA",
            False,
        )

    if status_code == 400:
        return (
            True,
            "HEAD_PROCESSADO_REJEICAO_DE_CONSULTA",
            False,
        )

    if status_code in {
        401,
        403,
    }:
        return (
            False,
            "AUTENTICACAO_REJEITADA",
            True,
        )

    if 300 <= status_code <= 399:
        return (
            False,
            "REDIRECIONAMENTO_INESPERADO",
            False,
        )

    if status_code == 405:
        return (
            False,
            "METODO_HEAD_NAO_ACEITO",
            False,
        )

    if status_code == 429 or 500 <= status_code <= 599:
        return (
            False,
            "SERVICO_INDISPONIVEL",
            False,
        )

    return (
        False,
        "STATUS_HTTP_INESPERADO",
        False,
    )


def executar_conectividade(
    *,
    session=None,
) -> ResultadoConectividade:
    """Realiza somente HEAD /dps/{id} com mTLS real."""

    _validar_id_sintetico()

    preflight._validar_variaveis_minimas()
    preflight._validar_xsd()

    endpoint_emissao = preflight._validar_endpoint()

    base = endpoint_emissao.removesuffix(
        "/nfse"
    )

    url = (
        base
        + "/dps/"
        + ID_DPS_SINTETICO
    )

    (
        chave_privada,
        certificado,
        cadeia,
        _,
    ) = preflight._carregar_material_a1()

    cliente = (
        session
        if session is not None
        else requests.Session()
    )

    with preflight._materializar_mtls(
        chave_privada,
        certificado,
        cadeia,
    ) as caminhos:
        try:
            resposta = cliente.request(
                method="HEAD",
                url=url,
                headers={
                    "Accept": "application/json",
                },
                timeout=TIMEOUT,
                verify=True,
                allow_redirects=False,
                cert=caminhos,
            )
        except requests.exceptions.SSLError as exc:
            raise ConectividadeSefinInvalida(
                "Falha TLS/mTLS ao conectar com a SEFIN."
            ) from exc
        except requests.Timeout as exc:
            raise ConectividadeSefinInvalida(
                "Timeout ao conectar com a SEFIN."
            ) from exc
        except requests.ConnectionError as exc:
            raise ConectividadeSefinInvalida(
                "Falha de conexao com a SEFIN."
            ) from exc
        except requests.RequestException as exc:
            raise ConectividadeSefinInvalida(
                "Falha HTTP ao conectar com a SEFIN."
            ) from exc

    try:
        status_code = int(
            resposta.status_code
        )
    except (TypeError, ValueError) as exc:
        raise ConectividadeSefinInvalida(
            "Resposta da SEFIN possui status HTTP invalido."
        ) from exc

    (
        sucesso,
        classificacao,
        autenticacao_rejeitada,
    ) = _classificar_http(
        status_code
    )

    return ResultadoConectividade(
        sucesso=sucesso,
        http_status=status_code,
        classificacao=classificacao,
        metodo="HEAD",
        servidor_alcancado=True,
        certificado_cliente_enviado=True,
        autenticacao_rejeitada=autenticacao_rejeitada,
        rede_utilizada=True,
        transmissao_executada=False,
    )


def executar() -> int:
    resultado = executar_conectividade()

    print(
        "=== H4-F10 | CONECTIVIDADE REAL MTLS SEFIN ==="
    )
    print(
        "STATUS: "
        + (
            "OK"
            if resultado.sucesso
            else "FALHA"
        )
    )
    print(
        "OPERACAO: HEAD /dps/{id_sintetico}"
    )
    print(
        "HTTP STATUS: "
        + str(
            resultado.http_status
        )
    )
    print(
        "CLASSIFICACAO: "
        + resultado.classificacao
    )
    print(
        "SERVIDOR SEFIN ALCANCADO: "
        + str(
            resultado.servidor_alcancado
        )
    )
    print(
        "CERTIFICADO CLIENTE ENVIADO: "
        + str(
            resultado.certificado_cliente_enviado
        )
    )
    print(
        "AUTENTICACAO REJEITADA: "
        + str(
            resultado.autenticacao_rejeitada
        )
    )
    print(
        "REDE UTILIZADA: "
        + str(
            resultado.rede_utilizada
        )
    )
    print(
        "POST /nfse: NAO EXECUTADO"
    )
    print(
        "TRANSMISSAO: NAO EXECUTADA"
    )

    return (
        0
        if resultado.sucesso
        else 2
    )


def main() -> int:
    try:
        return executar()
    except (
        ConectividadeSefinInvalida,
        preflight.PreflightStandaloneInvalido,
    ) as exc:
        print(
            "=== H4-F10 | CONECTIVIDADE REAL MTLS SEFIN ==="
        )
        print(
            "STATUS: FALHA"
        )
        print(
            "MOTIVO: "
            + str(
                exc
            )
        )
        print(
            "POST /nfse: NAO EXECUTADO"
        )
        print(
            "TRANSMISSAO: NAO EXECUTADA"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
