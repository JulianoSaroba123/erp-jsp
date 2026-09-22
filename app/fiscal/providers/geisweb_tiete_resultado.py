from __future__ import annotations

from dataclasses import dataclass
from xml.etree import ElementTree as ET


class GeisWebResultadoError(RuntimeError):
    """Erro ao interpretar o XML funcional retornado pelo GeisWeb."""


@dataclass(frozen=True)
class GeisWebMensagem:
    erro: int | None
    status: str


@dataclass(frozen=True)
class GeisWebNfse:
    numero_rps: str | None
    numero_nfse: str | None
    codigo_verificacao: str | None
    chave_nacional: str | None


@dataclass(frozen=True)
class GeisWebResultadoEnvio:
    status: str
    mensagem: str
    numero_lote: str | None
    numero_nfse: str | None
    codigo_verificacao: str | None
    chave_nacional: str | None
    nfse: tuple[GeisWebNfse, ...]
    mensagens: tuple[GeisWebMensagem, ...]


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]

    if ":" in tag:
        return tag.rsplit(":", 1)[1]

    return tag


def _filhos(elemento: ET.Element, nome: str):
    for filho in list(elemento):
        if _local_name(filho.tag) == nome:
            yield filho


def _primeiro(elemento: ET.Element, nome: str):
    for item in elemento.iter():
        if _local_name(item.tag) == nome:
            return item

    return None


def _texto(elemento: ET.Element | None) -> str | None:
    if elemento is None:
        return None

    valor = "".join(elemento.itertext()).strip()

    return valor or None


def _inteiro_ou_none(valor: str | None) -> int | None:
    if valor is None:
        return None

    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _ler_nfse(elemento: ET.Element) -> GeisWebNfse:
    identificacao = _primeiro(
        elemento,
        "IdentificacaoNfse",
    )

    if identificacao is None:
        return GeisWebNfse(
            numero_rps=None,
            numero_nfse=None,
            codigo_verificacao=None,
            chave_nacional=None,
        )

    return GeisWebNfse(
        numero_rps=_texto(
            _primeiro(
                identificacao,
                "NumeroRps",
            )
        ),
        numero_nfse=_texto(
            _primeiro(
                identificacao,
                "NumeroNfse",
            )
        ),
        codigo_verificacao=_texto(
            _primeiro(
                identificacao,
                "CodigoVerificacao",
            )
        ),
        chave_nacional=_texto(
            _primeiro(
                identificacao,
                "ChaveNotaNacional",
            )
        ),
    )


def _ler_mensagem(elemento: ET.Element) -> GeisWebMensagem:
    return GeisWebMensagem(
        erro=_inteiro_ou_none(
            _texto(
                _primeiro(
                    elemento,
                    "Erro",
                )
            )
        ),
        status=(
            _texto(
                _primeiro(
                    elemento,
                    "Status",
                )
            )
            or ""
        ),
    )


def interpretar_resultado_envio_geisweb(
    xml: str | bytes,
) -> GeisWebResultadoEnvio:
    """
    Interpreta o XML interno do EnviaSignLoteRps.

    Regras:
    - NFS-e com NumeroNfse => ACEITA;
    - Msg sem NFS-e => REJEITADA;
    - estrutura reconhecida sem conclusão => ERRO;
    - XML inválido => exceção técnica.
    """

    if isinstance(xml, bytes):
        try:
            xml_texto = xml.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise GeisWebResultadoError(
                "Retorno funcional GeisWeb possui codificacao invalida."
            ) from exc

    elif isinstance(xml, str):
        xml_texto = xml.lstrip("\ufeff")

    else:
        raise GeisWebResultadoError(
            "Retorno funcional GeisWeb deve ser str ou bytes."
        )

    if not xml_texto.strip():
        raise GeisWebResultadoError(
            "Retorno funcional GeisWeb esta vazio."
        )

    try:
        raiz = ET.fromstring(xml_texto)

    except ET.ParseError as exc:
        raise GeisWebResultadoError(
            "Retorno funcional GeisWeb possui XML invalido."
        ) from exc

    if _local_name(raiz.tag) != "EnviaLoteRpsResposta":
        raise GeisWebResultadoError(
            "Raiz funcional GeisWeb inesperada."
        )

    numero_lote = _texto(
        _primeiro(
            raiz,
            "NumeroLote",
        )
    )

    notas = tuple(
        _ler_nfse(elemento)
        for elemento in _filhos(
            raiz,
            "Nfse",
        )
    )

    mensagens = tuple(
        _ler_mensagem(elemento)
        for elemento in _filhos(
            raiz,
            "Msg",
        )
    )

    notas_validas = tuple(
        nota
        for nota in notas
        if nota.numero_nfse
    )

    if notas_validas:
        primeira = notas_validas[0]

        texto_mensagens = "; ".join(
            msg.status
            for msg in mensagens
            if msg.status
        )

        mensagem = (
            texto_mensagens
            or "NFS-e emitida pelo GeisWeb Tiete."
        )

        return GeisWebResultadoEnvio(
            status="ACEITA",
            mensagem=mensagem,
            numero_lote=numero_lote,
            numero_nfse=primeira.numero_nfse,
            codigo_verificacao=primeira.codigo_verificacao,
            chave_nacional=primeira.chave_nacional,
            nfse=notas,
            mensagens=mensagens,
        )

    if mensagens:
        mensagem = "; ".join(
            msg.status
            for msg in mensagens
            if msg.status
        )

        if not mensagem:
            mensagem = (
                "GeisWeb rejeitou o lote sem mensagem descritiva."
            )

        return GeisWebResultadoEnvio(
            status="REJEITADA",
            mensagem=mensagem,
            numero_lote=numero_lote,
            numero_nfse=None,
            codigo_verificacao=None,
            chave_nacional=None,
            nfse=notas,
            mensagens=mensagens,
        )

    return GeisWebResultadoEnvio(
        status="ERRO",
        mensagem=(
            "Retorno GeisWeb reconhecido, mas sem NFS-e "
            "emitida ou mensagem de rejeicao."
        ),
        numero_lote=numero_lote,
        numero_nfse=None,
        codigo_verificacao=None,
        chave_nacional=None,
        nfse=notas,
        mensagens=mensagens,
    )
