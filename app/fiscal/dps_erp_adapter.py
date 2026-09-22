"""Adaptador dos modelos do ERP JSP para a DPS canonica.

Esta camada somente transforma dados ja existentes no ERP.
Nao reserva RPS, nao incrementa numeracao, nao persiste,
nao transmite e nao realiza chamadas externas.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.fiscal.providers.sefin_nacional_dps import (
    montar_dps_canonica,
)


class AdaptacaoDpsErpInvalida(ValueError):
    """Dados do ERP insuficientes ou ambiguos para montar a DPS."""


def _texto(valor):
    if valor is None:
        return None

    texto = str(valor).strip()
    return texto or None


def _decimal(valor, *, campo):
    try:
        return Decimal(str(valor or 0))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise AdaptacaoDpsErpInvalida(
            f"{campo} invalido."
        ) from exc


def _municipio_ibge(valor, *, campo):
    texto = _texto(valor)

    if texto is None or not texto.isdigit() or len(texto) != 7:
        raise AdaptacaoDpsErpInvalida(
            f"{campo} deve possuir 7 digitos."
        )

    return texto


def _tipo_documento_cliente(cliente):
    tipo = str(
        getattr(cliente, "tipo", "") or ""
    ).strip().upper()

    if tipo == "PF":
        return "CPF"

    if tipo == "PJ":
        return "CNPJ"

    raise AdaptacaoDpsErpInvalida(
        "Tipo do cliente deve ser PF ou PJ."
    )


def _nome_cliente(cliente):
    tipo = str(
        getattr(cliente, "tipo", "") or ""
    ).strip().upper()

    if tipo == "PJ":
        nome = (
            _texto(getattr(cliente, "razao_social", None))
            or _texto(getattr(cliente, "nome_fantasia", None))
            or _texto(getattr(cliente, "nome", None))
        )
    else:
        nome = _texto(getattr(cliente, "nome", None))

    if nome is None:
        raise AdaptacaoDpsErpInvalida(
            "Nome do tomador nao informado."
        )

    return nome


def _pais_cliente(cliente):
    pais = _texto(
        getattr(cliente, "pais", None)
    )

    if pais is None:
        return "BR"

    normalizado = pais.upper()

    if normalizado in {
        "BR",
        "BRA",
        "BRASIL",
    }:
        return "BR"

    return pais


def montar_tomador_da_os(ordem_servico):
    """Monta o tomador canonico a partir do cliente da OS."""

    cliente = getattr(
        ordem_servico,
        "cliente",
        None,
    )

    if cliente is None:
        raise AdaptacaoDpsErpInvalida(
            "Cliente da ordem de servico nao informado."
        )

    documento = _texto(
        getattr(cliente, "cpf_cnpj", None)
    )

    if documento is None:
        raise AdaptacaoDpsErpInvalida(
            "CPF/CNPJ do tomador nao informado."
        )

    return {
        "tipo_documento": _tipo_documento_cliente(
            cliente
        ),
        "documento": documento,
        "nome": _nome_cliente(cliente),
        "email": (
            _texto(getattr(cliente, "email", None))
            or _texto(
                getattr(
                    cliente,
                    "email_financeiro",
                    None,
                )
            )
        ),
        "endereco": {
            "cep": _texto(
                getattr(cliente, "cep", None)
            ),
            "logradouro": _texto(
                getattr(cliente, "endereco", None)
            ),
            "numero": _texto(
                getattr(cliente, "numero", None)
            ),
            "complemento": _texto(
                getattr(cliente, "complemento", None)
            ),
            "bairro": _texto(
                getattr(cliente, "bairro", None)
            ),
            "cidade": _texto(
                getattr(cliente, "cidade", None)
            ),
            "uf": _texto(
                getattr(cliente, "estado", None)
            ),
            "pais": _pais_cliente(cliente),
        },
    }


def montar_servico_da_os(
    ordem_servico,
    configuracao_fiscal,
    *,
    municipio_incidencia_ibge,
    municipio_prestacao_ibge=None,
):
    """Monta os dados de servico sem fabricar incidencia fiscal."""

    descricao = (
        _texto(getattr(ordem_servico, "descricao", None))
        or _texto(getattr(ordem_servico, "titulo", None))
    )

    if descricao is None:
        raise AdaptacaoDpsErpInvalida(
            "Descricao do servico nao informada."
        )

    codigo_lista = _texto(
        getattr(
            configuracao_fiscal,
            "codigo_lc116",
            None,
        )
    )

    if codigo_lista is None:
        raise AdaptacaoDpsErpInvalida(
            "Codigo LC116 nao informado na configuracao fiscal."
        )

    codigo_municipal = _texto(
        getattr(
            configuracao_fiscal,
            "codigo_servico_municipal",
            None,
        )
    )

    if codigo_municipal is None:
        raise AdaptacaoDpsErpInvalida(
            "Codigo de servico municipal nao informado."
        )

    servico = {
        "codigo_lista_nacional": codigo_lista,
        "codigo_tributacao_municipal": codigo_municipal,
        "nbs": None,
        "descricao": descricao,
        "municipio_incidencia_ibge": _municipio_ibge(
            municipio_incidencia_ibge,
            campo="Municipio de incidencia",
        ),
    }

    if municipio_prestacao_ibge is not None:
        servico["municipio_prestacao_ibge"] = (
            _municipio_ibge(
                municipio_prestacao_ibge,
                campo="Municipio de prestacao",
            )
        )

    return servico


def montar_valores_da_os(ordem_servico):
    """Usa somente os servicos da OS na base da NFS-e."""

    valor_servicos = _decimal(
        getattr(
            ordem_servico,
            "valor_total_servicos",
            0,
        ),
        campo="Valor total dos servicos",
    )

    if valor_servicos <= 0:
        raise AdaptacaoDpsErpInvalida(
            "Valor total dos servicos deve ser maior que zero."
        )

    desconto_global = _decimal(
        getattr(
            ordem_servico,
            "valor_desconto",
            0,
        ),
        campo="Desconto da OS",
    )

    if desconto_global != 0:
        raise AdaptacaoDpsErpInvalida(
            "A OS possui desconto global. "
            "A alocacao fiscal do desconto entre servicos e produtos "
            "deve ser definida antes da DPS."
        )

    return {
        "valor_servicos": valor_servicos,
        "valor_recebido": None,
        "desconto_incondicionado": Decimal("0"),
        "desconto_condicionado": Decimal("0"),
        "deducoes": Decimal("0"),
    }


def montar_dps_canonica_da_os(
    *,
    documento,
    ordem_servico,
    configuracao,
    configuracao_fiscal,
    versao_layout,
    tipo_emitente,
    municipio_incidencia_ibge,
    iss,
    totais_tributos,
    municipio_prestacao_ibge=None,
    ibs_cbs=None,
    data_emissao=None,
    versao_aplicativo="ERP-JSP",
):
    """Transforma uma OS existente em DPS canonica validada.

    Nenhuma numeracao e criada ou consumida aqui.
    """

    if documento is None:
        raise AdaptacaoDpsErpInvalida(
            "Documento NFS-e nao informado."
        )

    if ordem_servico is None:
        raise AdaptacaoDpsErpInvalida(
            "Ordem de servico nao informada."
        )

    if configuracao is None:
        raise AdaptacaoDpsErpInvalida(
            "Configuracao institucional nao informada."
        )

    if configuracao_fiscal is None:
        raise AdaptacaoDpsErpInvalida(
            "Configuracao fiscal nao informada."
        )

    numero_dps = getattr(
        documento,
        "numero_rps",
        None,
    )

    if numero_dps is None:
        raise AdaptacaoDpsErpInvalida(
            "Documento NFS-e ainda nao possui numero RPS/DPS reservado."
        )

    serie = (
        _texto(getattr(documento, "serie_rps", None))
        or _texto(
            getattr(
                configuracao_fiscal,
                "serie_rps",
                None,
            )
        )
    )

    if serie is None:
        raise AdaptacaoDpsErpInvalida(
            "Serie RPS/DPS nao informada."
        )

    emissao = data_emissao

    if emissao is None:
        emissao = (
            getattr(documento, "criado_em", None)
            or getattr(
                documento,
                "data_criacao",
                None,
            )
        )

    if emissao is None:
        raise AdaptacaoDpsErpInvalida(
            "Data de emissao da DPS nao disponivel."
        )

    competencia = getattr(
        ordem_servico,
        "data_conclusao",
        None,
    )

    if competencia is None:
        raise AdaptacaoDpsErpInvalida(
            "OS concluida sem data de conclusao."
        )

    if isinstance(competencia, datetime):
        competencia = competencia.date()

    municipio_emissao = _municipio_ibge(
        getattr(
            configuracao_fiscal,
            "municipio_ibge",
            None,
        ),
        campo="Municipio de emissao",
    )

    if not isinstance(iss, dict) or not iss:
        raise AdaptacaoDpsErpInvalida(
            "Decisao fiscal de ISS nao informada."
        )

    if (
        not isinstance(totais_tributos, dict)
        or not totais_tributos
    ):
        raise AdaptacaoDpsErpInvalida(
            "Totais tributarios da DPS nao informados."
        )

    return montar_dps_canonica(
        ambiente=getattr(
            documento,
            "ambiente",
            None,
        ),
        versao_layout=versao_layout,
        data_emissao=emissao,
        versao_aplicativo=versao_aplicativo,
        serie=serie,
        numero_dps=numero_dps,
        competencia=competencia,
        tipo_emitente=tipo_emitente,
        municipio_emissao_ibge=municipio_emissao,
        configuracao=configuracao,
        configuracao_fiscal=configuracao_fiscal,
        tomador=montar_tomador_da_os(
            ordem_servico
        ),
        servico=montar_servico_da_os(
            ordem_servico,
            configuracao_fiscal,
            municipio_incidencia_ibge=(
                municipio_incidencia_ibge
            ),
            municipio_prestacao_ibge=(
                municipio_prestacao_ibge
            ),
        ),
        valores=montar_valores_da_os(
            ordem_servico
        ),
        iss=iss,
        totais_tributos=totais_tributos,
        ibs_cbs=ibs_cbs,
    )