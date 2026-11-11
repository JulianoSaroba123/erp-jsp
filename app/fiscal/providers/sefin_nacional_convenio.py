"""Gate local para interpretar disponibilidade de convênio municipal NFS-e.

H4-F17:
- não realiza HTTP;
- não acessa banco;
- não carrega certificado;
- interpreta respostas já obtidas da API de parametrização;
- diferencia município ativo de bloqueio ambiental por convênio inativo.
"""

from __future__ import annotations

from dataclasses import dataclass
import json


@dataclass(frozen=True)
class ResultadoConvenioMunicipal:
    ambiente: str
    codigo_municipio: str
    status_code: int
    ativo: bool
    mensagem: str | None
    bloqueio_ambiental: bool


class RespostaConvenioInvalida(ValueError):
    """Resposta da API de convênio não pôde ser interpretada."""


def _mensagem_json(
    dados: dict,
) -> str | None:
    for chave in (
        "mensagem",
        "Mensagem",
        "message",
        "Message",
        "descricao",
        "Descricao",
    ):
        if chave in dados:
            valor = str(
                dados.get(
                    chave
                )
                or ""
            ).strip()

            if valor:
                return valor

    return None


def interpretar_resposta_convenio(
    *,
    ambiente,
    codigo_municipio,
    status_code,
    conteudo,
) -> ResultadoConvenioMunicipal:
    ambiente_normalizado = str(
        ambiente or ""
    ).strip().upper()

    codigo = str(
        codigo_municipio or ""
    ).strip()

    try:
        status = int(
            status_code
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise RespostaConvenioInvalida(
            "Status HTTP do convênio é inválido."
        ) from exc

    corpo = bytes(
        conteudo or b""
    )

    dados = {}

    if corpo:
        try:
            valor = json.loads(
                corpo.decode(
                    "utf-8"
                )
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise RespostaConvenioInvalida(
                "Resposta do convênio não é JSON válido."
            ) from exc

        if not isinstance(
            valor,
            dict,
        ):
            raise RespostaConvenioInvalida(
                "Resposta JSON do convênio deve ser objeto."
            )

        dados = valor

    mensagem = _mensagem_json(
        dados
    )

    if 200 <= status <= 299:
        return ResultadoConvenioMunicipal(
            ambiente=ambiente_normalizado,
            codigo_municipio=codigo,
            status_code=status,
            ativo=True,
            mensagem=mensagem,
            bloqueio_ambiental=False,
        )

    texto = (
        mensagem or ""
    ).lower()

    inativo = (
        status == 404
        and "conv" in texto
        and "não est" in texto
        and "ativo" in texto
    )

    return ResultadoConvenioMunicipal(
        ambiente=ambiente_normalizado,
        codigo_municipio=codigo,
        status_code=status,
        ativo=False,
        mensagem=mensagem,
        bloqueio_ambiental=inativo,
    )


def validar_convenio_ativo(
    resultado: ResultadoConvenioMunicipal,
) -> None:
    if not isinstance(
        resultado,
        ResultadoConvenioMunicipal,
    ):
        raise TypeError(
            "Resultado de convênio inválido."
        )

    if resultado.ativo:
        return

    if resultado.bloqueio_ambiental:
        raise RespostaConvenioInvalida(
            "Município sem convênio ativo no ambiente "
            + resultado.ambiente
            + ". Emissão deve ser bloqueada antes do POST /nfse."
        )

    raise RespostaConvenioInvalida(
        "Convênio municipal não confirmado para emissão."
    )
