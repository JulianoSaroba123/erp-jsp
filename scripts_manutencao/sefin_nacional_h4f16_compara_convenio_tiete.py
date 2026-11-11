"""H4-F16 - compara convênio municipal de Tietê entre ambientes.

Somente leitura:
- GET Produção Restrita
- GET Produção
- sem POST
- sem emissão
- sem Flask
- sem banco

Objetivo: diagnosticar E0037 do H4-F15.
"""

from __future__ import annotations

import json

import requests


CODIGO_MUNICIPIO = "3554508"

URL_PRODREST = (
    "https://adn.producaorestrita.nfse.gov.br"
    "/parametrizacao/"
    + CODIGO_MUNICIPIO
    + "/convenio"
)

URL_PRODUCAO = (
    "https://adn.nfse.gov.br"
    "/parametrizacao/"
    + CODIGO_MUNICIPIO
    + "/convenio"
)

TIMEOUT = (
    10,
    30,
)


class ComparacaoConvenioInvalida(RuntimeError):
    """Falha controlada na comparação dos convênios."""


def _resumo_resposta(
    *,
    ambiente: str,
    resposta,
) -> dict:
    try:
        status_code = int(
            resposta.status_code
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ComparacaoConvenioInvalida(
            f"{ambiente}: status HTTP inválido."
        ) from exc

    conteudo = bytes(
        getattr(
            resposta,
            "content",
            b"",
        )
        or b""
    )

    dados = None
    mensagem = None

    if conteudo:
        try:
            valor = json.loads(
                conteudo.decode(
                    "utf-8"
                )
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ):
            mensagem = (
                conteudo[:500]
                .decode(
                    "utf-8",
                    errors="replace",
                )
                .strip()
                or None
            )
        else:
            if isinstance(
                valor,
                dict,
            ):
                dados = valor

                for chave in (
                    "mensagem",
                    "Mensagem",
                    "message",
                    "Message",
                    "descricao",
                    "Descricao",
                ):
                    if chave in valor:
                        texto = str(
                            valor.get(
                                chave
                            )
                            or ""
                        ).strip()

                        if texto:
                            mensagem = texto
                            break

    return {
        "ambiente": ambiente,
        "status_code": status_code,
        "ok_http": 200 <= status_code <= 299,
        "mensagem": mensagem,
        "json": dados,
        "bytes": len(
            conteudo
        ),
    }


def _consultar(
    *,
    url: str,
    ambiente: str,
    session=None,
) -> dict:
    cliente = (
        session
        if session is not None
        else requests.Session()
    )

    try:
        resposta = cliente.request(
            method="GET",
            url=url,
            headers={
                "Accept": "application/json",
            },
            timeout=TIMEOUT,
            verify=True,
            allow_redirects=False,
        )
    except requests.exceptions.Timeout as exc:
        raise ComparacaoConvenioInvalida(
            f"{ambiente}: timeout na consulta."
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise ComparacaoConvenioInvalida(
            f"{ambiente}: falha HTTP/TLS na consulta."
        ) from exc

    return _resumo_resposta(
        ambiente=ambiente,
        resposta=resposta,
    )


def executar_comparacao(
    *,
    session_prodrest=None,
    session_producao=None,
) -> dict:
    prodrest = _consultar(
        url=URL_PRODREST,
        ambiente="PRODUCAO_RESTRITA",
        session=session_prodrest,
    )

    producao = _consultar(
        url=URL_PRODUCAO,
        ambiente="PRODUCAO",
        session=session_producao,
    )

    if (
        not prodrest[
            "ok_http"
        ]
        and producao[
            "ok_http"
        ]
    ):
        diagnostico = (
            "DIVERGENCIA_AMBIENTAL_PROVAVEL"
        )
    elif (
        prodrest[
            "ok_http"
        ]
        and producao[
            "ok_http"
        ]
    ):
        diagnostico = (
            "CONVENIO_RESPONDE_NOS_DOIS_AMBIENTES"
        )
    elif (
        not prodrest[
            "ok_http"
        ]
        and not producao[
            "ok_http"
        ]
    ):
        diagnostico = (
            "CONVENIO_NAO_CONFIRMADO_EM_AMBOS"
        )
    else:
        diagnostico = (
            "PRODREST_RESPONDE_E_PRODUCAO_NAO"
        )

    return {
        "codigo_municipio": CODIGO_MUNICIPIO,
        "prodrest": prodrest,
        "producao": producao,
        "diagnostico": diagnostico,
        "metodos": (
            "GET",
            "GET",
        ),
        "post_executado": False,
        "emissao_executada": False,
        "banco_acessado": False,
        "flask_inicializado": False,
    }


def _imprimir_ambiente(
    dados: dict,
) -> None:
    print(
        dados[
            "ambiente"
        ]
        + " HTTP: "
        + str(
            dados[
                "status_code"
            ]
        )
    )
    print(
        dados[
            "ambiente"
        ]
        + " OK HTTP: "
        + str(
            dados[
                "ok_http"
            ]
        )
    )
    print(
        dados[
            "ambiente"
        ]
        + " MENSAGEM: "
        + (
            dados[
                "mensagem"
            ]
            or "<sem mensagem textual>"
        )
    )

    if isinstance(
        dados[
            "json"
        ],
        dict,
    ):
        print(
            dados[
                "ambiente"
            ]
            + " CHAVES JSON: "
            + ", ".join(
                sorted(
                    str(
                        item
                    )
                    for item in dados[
                        "json"
                    ].keys()
                )
            )
        )


def executar() -> int:
    resultado = executar_comparacao()

    print(
        "=== H4-F16 | COMPARA CONVENIO TIETE ==="
    )
    print(
        "STATUS: OK"
    )
    print(
        "CODIGO MUNICIPIO: "
        + resultado[
            "codigo_municipio"
        ]
    )

    _imprimir_ambiente(
        resultado[
            "prodrest"
        ]
    )
    _imprimir_ambiente(
        resultado[
            "producao"
        ]
    )

    print(
        "DIAGNOSTICO: "
        + resultado[
            "diagnostico"
        ]
    )
    print(
        "METODOS: GET + GET"
    )
    print(
        "POST: NAO EXECUTADO"
    )
    print(
        "EMISSAO: NAO EXECUTADA"
    )
    print(
        "FLASK INICIALIZADO: False"
    )
    print(
        "BANCO ACESSADO: False"
    )

    return 0


def main() -> int:
    try:
        return executar()
    except ComparacaoConvenioInvalida as exc:
        print(
            "=== H4-F16 | COMPARA CONVENIO TIETE ==="
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
            "POST: NAO EXECUTADO"
        )
        print(
            "EMISSAO: NAO EXECUTADA"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
