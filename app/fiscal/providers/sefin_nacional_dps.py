"""Modelo interno canonico da DPS da NFS-e Nacional.

D24F02-B4:
- representa dados fiscais antes da serializacao XML;
- nao depende de SQLAlchemy;
- nao gera XML;
- nao assina documento;
- nao realiza HTTP;
- preserva suporte a CNPJ alfanumerico.
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation


class DpsCanonicaInvalida(ValueError):
    """Dados insuficientes ou invalidos para montar a DPS canonica."""


def _texto(valor, *, campo: str, obrigatorio: bool = False):
    if valor is None:
        texto = ""
    else:
        texto = str(valor).strip()

    if obrigatorio and not texto:
        raise DpsCanonicaInvalida(
            f"Campo obrigatorio ausente: {campo}."
        )

    return texto or None


def _valor_decimal(valor, *, campo: str) -> str:
    try:
        numero = Decimal(str(valor or "0"))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise DpsCanonicaInvalida(
            f"Valor invalido para {campo}."
        ) from exc

    if numero < 0:
        raise DpsCanonicaInvalida(
            f"Valor de {campo} nao pode ser negativo."
        )

    return f"{numero.quantize(Decimal('0.01')):.2f}"


def _data_iso(valor, *, campo: str) -> str:
    if isinstance(valor, datetime):
        valor = valor.date()

    if isinstance(valor, date):
        return valor.isoformat()

    texto = _texto(
        valor,
        campo=campo,
        obrigatorio=True,
    )

    try:
        return date.fromisoformat(texto).isoformat()
    except ValueError as exc:
        raise DpsCanonicaInvalida(
            f"Data invalida para {campo}."
        ) from exc


def montar_dps_canonica(
    *,
    ambiente,
    versao_layout,
    competencia,
    prestador: dict,
    tomador: dict,
    servico: dict,
    valores: dict,
    iss: dict | None = None,
    ibs_cbs: dict | None = None,
) -> dict:
    """Monta representacao interna validada da DPS."""

    ambiente_normalizado = _texto(
        ambiente,
        campo="ambiente",
        obrigatorio=True,
    ).upper()

    if ambiente_normalizado not in {
        "HOMOLOGACAO",
        "PRODUCAO",
    }:
        raise DpsCanonicaInvalida(
            "Ambiente da DPS invalido."
        )

    versao = _texto(
        versao_layout,
        campo="versao_layout",
        obrigatorio=True,
    )

    prestador_documento = _texto(
        prestador.get("documento"),
        campo="prestador.documento",
        obrigatorio=True,
    )

    prestador_im = _texto(
        prestador.get("inscricao_municipal"),
        campo="prestador.inscricao_municipal",
        obrigatorio=True,
    )

    prestador_municipio = _texto(
        prestador.get("municipio_ibge"),
        campo="prestador.municipio_ibge",
        obrigatorio=True,
    )

    if len(prestador_municipio) != 7:
        raise DpsCanonicaInvalida(
            "Municipio IBGE do prestador deve possuir 7 caracteres."
        )

    tipo_tomador = _texto(
        tomador.get("tipo_documento"),
        campo="tomador.tipo_documento",
        obrigatorio=True,
    ).upper()

    if tipo_tomador not in {
        "CPF",
        "CNPJ",
    }:
        raise DpsCanonicaInvalida(
            "Tipo de documento do tomador deve ser CPF ou CNPJ."
        )

    tomador_documento = _texto(
        tomador.get("documento"),
        campo="tomador.documento",
        obrigatorio=True,
    )

    tomador_nome = _texto(
        tomador.get("nome"),
        campo="tomador.nome",
        obrigatorio=True,
    )

    descricao_servico = _texto(
        servico.get("descricao"),
        campo="servico.descricao",
        obrigatorio=True,
    )

    codigo_municipal = _texto(
        servico.get("codigo_tributacao_municipal"),
        campo="servico.codigo_tributacao_municipal",
        obrigatorio=True,
    )

    municipio_incidencia = _texto(
        servico.get("municipio_incidencia_ibge"),
        campo="servico.municipio_incidencia_ibge",
        obrigatorio=True,
    )

    if len(municipio_incidencia) != 7:
        raise DpsCanonicaInvalida(
            "Municipio de incidencia deve possuir 7 caracteres."
        )

    endereco = tomador.get("endereco") or {}

    return {
        "identificacao": {
            "ambiente": ambiente_normalizado,
            "versao_layout": versao,
            "competencia": _data_iso(
                competencia,
                campo="competencia",
            ),
        },
        "prestador": {
            "documento": prestador_documento,
            "inscricao_municipal": prestador_im,
            "municipio_ibge": prestador_municipio,
            "regime_tributario": _texto(
                prestador.get("regime_tributario"),
                campo="prestador.regime_tributario",
            ),
            "optante_simples_nacional": bool(
                prestador.get(
                    "optante_simples_nacional",
                    False,
                )
            ),
        },
        "tomador": {
            "tipo_documento": tipo_tomador,
            "documento": tomador_documento,
            "nome": tomador_nome,
            "email": _texto(
                tomador.get("email"),
                campo="tomador.email",
            ),
            "endereco": {
                "cep": _texto(
                    endereco.get("cep"),
                    campo="tomador.endereco.cep",
                ),
                "logradouro": _texto(
                    endereco.get("logradouro"),
                    campo="tomador.endereco.logradouro",
                ),
                "numero": _texto(
                    endereco.get("numero"),
                    campo="tomador.endereco.numero",
                ),
                "complemento": _texto(
                    endereco.get("complemento"),
                    campo="tomador.endereco.complemento",
                ),
                "bairro": _texto(
                    endereco.get("bairro"),
                    campo="tomador.endereco.bairro",
                ),
                "cidade": _texto(
                    endereco.get("cidade"),
                    campo="tomador.endereco.cidade",
                ),
                "uf": _texto(
                    endereco.get("uf"),
                    campo="tomador.endereco.uf",
                ),
                "pais": _texto(
                    endereco.get("pais") or "BR",
                    campo="tomador.endereco.pais",
                ),
            },
        },
        "servico": {
            "codigo_lista_nacional": _texto(
                servico.get("codigo_lista_nacional"),
                campo="servico.codigo_lista_nacional",
            ),
            "codigo_tributacao_municipal": codigo_municipal,
            "nbs": _texto(
                servico.get("nbs"),
                campo="servico.nbs",
            ),
            "descricao": descricao_servico,
            "municipio_incidencia_ibge": municipio_incidencia,
        },
        "valores": {
            "valor_servicos": _valor_decimal(
                valores.get("valor_servicos"),
                campo="valor_servicos",
            ),
            "desconto_incondicionado": _valor_decimal(
                valores.get(
                    "desconto_incondicionado",
                    0,
                ),
                campo="desconto_incondicionado",
            ),
            "desconto_condicionado": _valor_decimal(
                valores.get(
                    "desconto_condicionado",
                    0,
                ),
                campo="desconto_condicionado",
            ),
            "deducoes": _valor_decimal(
                valores.get("deducoes", 0),
                campo="deducoes",
            ),
        },
        "iss": dict(iss or {}),
        "ibs_cbs": dict(ibs_cbs or {}),
    }
