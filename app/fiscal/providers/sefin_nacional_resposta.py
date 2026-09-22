"""Normalizacao tecnica da resposta de emissao SEFIN Nacional.

D24F03-B8-A3.4:
- interpreta o JSON oficial do POST /nfse;
- trata sucesso 201;
- trata corpos de erro 400/403/500;
- descompacta nfseXmlGZipB64;
- nao altera banco;
- nao decide transicao de status do documento;
- nao realiza HTTP.
"""

import base64
import binascii
from dataclasses import dataclass
import gzip
import json


class RespostaEmissaoSefinInvalida(ValueError):
    """Resposta da SEFIN fora do contrato esperado."""


@dataclass(frozen=True)
class MensagemProcessamentoSefin:
    mensagem: str | None = None
    codigo: str | None = None
    descricao: str | None = None
    complemento: str | None = None


@dataclass(frozen=True)
class RespostaEmissaoSefin:
    status_code: int
    sucesso: bool
    tipo_ambiente: int
    versao_aplicativo: str
    data_hora_processamento: str
    id_dps: str | None = None
    chave_acesso: str | None = None
    nfse_xml: bytes | None = None
    alertas: tuple[MensagemProcessamentoSefin, ...] = ()
    erros: tuple[MensagemProcessamentoSefin, ...] = ()


_STATUS_PERMITIDOS = frozenset(
    {
        201,
        400,
        403,
        500,
    }
)


def _texto_obrigatorio(
    dados: dict,
    campo: str,
) -> str:
    valor = dados.get(campo)

    if not isinstance(valor, str) or not valor.strip():
        raise RespostaEmissaoSefinInvalida(
            f"Campo obrigatorio invalido na resposta SEFIN: {campo}."
        )

    return valor.strip()


def _texto_opcional(
    valor,
    *,
    campo: str,
) -> str | None:
    if valor is None:
        return None

    if not isinstance(valor, str):
        raise RespostaEmissaoSefinInvalida(
            f"Campo invalido na resposta SEFIN: {campo}."
        )

    valor = valor.strip()

    return valor or None


def _tipo_ambiente(
    dados: dict,
) -> int:
    valor = dados.get(
        "tipoAmbiente"
    )

    if not isinstance(valor, int) or isinstance(valor, bool):
        raise RespostaEmissaoSefinInvalida(
            "tipoAmbiente invalido na resposta SEFIN."
        )

    if valor not in (1, 2):
        raise RespostaEmissaoSefinInvalida(
            "tipoAmbiente fora do dominio esperado."
        )

    return valor


def _mensagem(
    valor,
) -> MensagemProcessamentoSefin:
    if not isinstance(valor, dict):
        raise RespostaEmissaoSefinInvalida(
            "Mensagem de processamento SEFIN invalida."
        )

    return MensagemProcessamentoSefin(
        mensagem=_texto_opcional(
            valor.get("mensagem"),
            campo="mensagem",
        ),
        codigo=_texto_opcional(
            valor.get("codigo"),
            campo="codigo",
        ),
        descricao=_texto_opcional(
            valor.get("descricao"),
            campo="descricao",
        ),
        complemento=_texto_opcional(
            valor.get("complemento"),
            campo="complemento",
        ),
    )


def _mensagens(
    dados: dict,
    campo: str,
    *,
    obrigatorio: bool,
) -> tuple[MensagemProcessamentoSefin, ...]:
    if campo not in dados:
        if obrigatorio:
            raise RespostaEmissaoSefinInvalida(
                f"Campo obrigatorio ausente na resposta SEFIN: {campo}."
            )

        return ()

    valores = dados[campo]

    if not isinstance(valores, list):
        raise RespostaEmissaoSefinInvalida(
            f"Campo {campo} deve ser uma lista."
        )

    return tuple(
        _mensagem(item)
        for item in valores
    )


def _carregar_json(
    conteudo,
) -> dict:
    if not isinstance(
        conteudo,
        (bytes, bytearray),
    ):
        raise RespostaEmissaoSefinInvalida(
            "Conteudo da resposta SEFIN deve ser bytes."
        )

    if not conteudo:
        raise RespostaEmissaoSefinInvalida(
            "Resposta SEFIN vazia."
        )

    try:
        texto = bytes(
            conteudo
        ).decode(
            "utf-8"
        )
    except UnicodeDecodeError as exc:
        raise RespostaEmissaoSefinInvalida(
            "Resposta SEFIN nao esta em UTF-8 valido."
        ) from exc

    try:
        dados = json.loads(
            texto
        )
    except json.JSONDecodeError as exc:
        raise RespostaEmissaoSefinInvalida(
            "Resposta SEFIN nao contem JSON valido."
        ) from exc

    if not isinstance(
        dados,
        dict,
    ):
        raise RespostaEmissaoSefinInvalida(
            "Resposta JSON da SEFIN deve ser um objeto."
        )

    return dados


def _descompactar_nfse(
    valor,
) -> bytes:
    if not isinstance(valor, str) or not valor.strip():
        raise RespostaEmissaoSefinInvalida(
            "nfseXmlGZipB64 ausente ou invalido."
        )

    try:
        comprimido = base64.b64decode(
            valor,
            validate=True,
        )
    except (
        binascii.Error,
        ValueError,
    ) as exc:
        raise RespostaEmissaoSefinInvalida(
            "nfseXmlGZipB64 possui Base64 invalido."
        ) from exc

    try:
        xml = gzip.decompress(
            comprimido
        )
    except (
        OSError,
        EOFError,
    ) as exc:
        raise RespostaEmissaoSefinInvalida(
            "nfseXmlGZipB64 possui GZip invalido."
        ) from exc

    if not xml:
        raise RespostaEmissaoSefinInvalida(
            "XML da NFS-e retornado pela SEFIN esta vazio."
        )

    return xml


def normalizar_resposta_emissao_sefin(
    *,
    status_code: int,
    conteudo,
) -> RespostaEmissaoSefin:
    """Normaliza o contrato HTTP/JSON oficial da emissao."""

    if status_code not in _STATUS_PERMITIDOS:
        raise RespostaEmissaoSefinInvalida(
            "Status HTTP inesperado para emissao SEFIN: "
            f"{status_code}."
        )

    dados = _carregar_json(
        conteudo
    )

    tipo_ambiente = _tipo_ambiente(
        dados
    )

    versao_aplicativo = _texto_obrigatorio(
        dados,
        "versaoAplicativo",
    )

    data_hora_processamento = _texto_obrigatorio(
        dados,
        "dataHoraProcessamento",
    )

    if status_code == 201:
        id_dps = _texto_obrigatorio(
            dados,
            "idDps",
        )

        chave_acesso = _texto_obrigatorio(
            dados,
            "chaveAcesso",
        )

        nfse_xml = _descompactar_nfse(
            dados.get(
                "nfseXmlGZipB64"
            )
        )

        alertas = _mensagens(
            dados,
            "alertas",
            obrigatorio=False,
        )

        return RespostaEmissaoSefin(
            status_code=status_code,
            sucesso=True,
            tipo_ambiente=tipo_ambiente,
            versao_aplicativo=versao_aplicativo,
            data_hora_processamento=data_hora_processamento,
            id_dps=id_dps,
            chave_acesso=chave_acesso,
            nfse_xml=nfse_xml,
            alertas=alertas,
        )

    erros = _mensagens(
        dados,
        "erros",
        obrigatorio=True,
    )

    id_dps = _texto_opcional(
        dados.get(
            "idDPS"
        ),
        campo="idDPS",
    )

    return RespostaEmissaoSefin(
        status_code=status_code,
        sucesso=False,
        tipo_ambiente=tipo_ambiente,
        versao_aplicativo=versao_aplicativo,
        data_hora_processamento=data_hora_processamento,
        id_dps=id_dps,
        erros=erros,
    )
