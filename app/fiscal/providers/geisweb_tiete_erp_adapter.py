"""Adapter ERP JSP -> estrutura canonica GeisWeb Tiete.

Responsabilidades:
- extrair dados ja conhecidos pelo ERP;
- montar o contrato consumido por geisweb_tiete_xml;
- validar dados obrigatorios antes da serializacao.

Nao:
- assina XML;
- acessa certificado;
- transmite;
- inventa classificacao tributaria da Reforma.
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from app.fiscal.dps_erp_adapter import (
    montar_servico_da_os,
    montar_tomador_da_os,
    montar_valores_da_os,
)
from app.fiscal.providers.geisweb_tiete_config import (
    MUNICIPIO_IBGE,
)


class AdaptacaoGeisWebErpInvalida(ValueError):
    """Dados ERP insuficientes para montar lote GeisWeb."""


def _texto(valor) -> str:
    if valor is None:
        return ""

    return str(valor).strip()


def _obrigatorio(valor, *, campo: str) -> str:
    valor = _texto(valor)

    if not valor:
        raise AdaptacaoGeisWebErpInvalida(
            f"Campo obrigatorio ausente: {campo}."
        )

    return valor


def _decimal(valor, *, campo: str) -> str:
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise AdaptacaoGeisWebErpInvalida(
            f"{campo} deve possuir valor decimal valido."
        ) from exc

    return f"{numero:.2f}"


def _data_emissao(valor) -> str:
    if isinstance(valor, datetime):
        return valor.replace(
            microsecond=0
        ).isoformat()

    if isinstance(valor, date):
        return datetime.combine(
            valor,
            datetime.min.time(),
        ).isoformat()

    valor = _obrigatorio(
        valor,
        campo="data_emissao",
    )

    return valor


def _documento_federal(valor, *, campo: str) -> str:
    texto = _obrigatorio(
        valor,
        campo=campo,
    )

    digitos = "".join(
        caractere
        for caractere in texto
        if caractere.isdigit()
    )

    if len(digitos) not in {11, 14}:
        raise AdaptacaoGeisWebErpInvalida(
            f"{campo} deve possuir CPF ou CNPJ valido em formato numerico."
        )

    return digitos


def _validar_vinculo_configuracao(
    configuracao,
    configuracao_fiscal,
):
    if configuracao is None:
        raise AdaptacaoGeisWebErpInvalida(
            "Configuracao geral nao informada."
        )

    if configuracao_fiscal is None:
        raise AdaptacaoGeisWebErpInvalida(
            "Configuracao fiscal nao informada."
        )

    configuracao_id = getattr(
        configuracao,
        "id",
        None,
    )

    configuracao_fiscal_id = getattr(
        configuracao_fiscal,
        "configuracao_id",
        None,
    )

    if configuracao_id is None:
        raise AdaptacaoGeisWebErpInvalida(
            "Configuracao geral sem id."
        )

    if configuracao_fiscal_id is None:
        raise AdaptacaoGeisWebErpInvalida(
            "Configuracao fiscal sem configuracao_id."
        )

    if configuracao_id != configuracao_fiscal_id:
        raise AdaptacaoGeisWebErpInvalida(
            "Configuracao fiscal nao pertence a configuracao geral informada."
        )


def _normalizar_ibs_cbs(ibs_cbs):
    if not isinstance(ibs_cbs, dict):
        raise AdaptacaoGeisWebErpInvalida(
            "ibs_cbs deve ser informado explicitamente como dict."
        )

    return {
        "c_class_trib": _obrigatorio(
            ibs_cbs.get("c_class_trib"),
            campo="ibs_cbs.c_class_trib",
        ),
        "ibs": _decimal(
            ibs_cbs.get("ibs"),
            campo="ibs_cbs.ibs",
        ),
        "cbs": _decimal(
            ibs_cbs.get("cbs"),
            campo="ibs_cbs.cbs",
        ),
        "c_class_trib_reg": _obrigatorio(
            ibs_cbs.get("c_class_trib_reg"),
            campo="ibs_cbs.c_class_trib_reg",
        ),
    }


def _normalizar_outros_impostos(outros_impostos):
    if not isinstance(outros_impostos, dict):
        raise AdaptacaoGeisWebErpInvalida(
            "outros_impostos deve ser informado explicitamente como dict."
        )

    resultado = {}

    for campo in (
        "pis",
        "cofins",
        "csll",
        "irrf",
        "inss",
    ):
        if campo not in outros_impostos:
            raise AdaptacaoGeisWebErpInvalida(
                f"Campo obrigatorio ausente: outros_impostos.{campo}."
            )

        resultado[campo] = _decimal(
            outros_impostos[campo],
            campo=f"outros_impostos.{campo}",
        )

    return resultado


def _normalizar_tomador(tomador):
    if not isinstance(tomador, dict):
        raise AdaptacaoGeisWebErpInvalida(
            "Tomador deve ser dict."
        )

    endereco = tomador.get("endereco")

    if not isinstance(endereco, dict):
        raise AdaptacaoGeisWebErpInvalida(
            "Endereco do tomador deve ser dict."
        )

    return {
        "cnpj_cpf": _documento_federal(
            tomador.get("documento"),
            campo="tomador.documento",
        ),
        "nif": "",
        "nao_nif": "",
        "razao_social": _obrigatorio(
            tomador.get("nome"),
            campo="tomador.nome",
        ),
        "endereco": {
            "rua": _obrigatorio(
                endereco.get("logradouro"),
                campo="tomador.endereco.logradouro",
            ),
            "numero": _obrigatorio(
                endereco.get("numero"),
                campo="tomador.endereco.numero",
            ),
            "bairro": _obrigatorio(
                endereco.get("bairro"),
                campo="tomador.endereco.bairro",
            ),
            "cidade": _obrigatorio(
                endereco.get("cidade"),
                campo="tomador.endereco.cidade",
            ),
            "estado": _obrigatorio(
                endereco.get("uf"),
                campo="tomador.endereco.uf",
            ),
            "cep": _obrigatorio(
                endereco.get("cep"),
                campo="tomador.endereco.cep",
            ),
            "pais": _obrigatorio(
                endereco.get("pais"),
                campo="tomador.endereco.pais",
            ),
            "prov_reg": "",
            "email": _texto(
                tomador.get("email")
            ),
        },
    }


def montar_lote_geisweb_da_os(
    *,
    documento,
    ordem_servico,
    configuracao,
    configuracao_fiscal,
    numero_lote,
    data_emissao,
    tipo_lancamento,
    regime_geisweb,
    codigo_nacional,
    base_calculo,
    ibs_cbs,
    outros_impostos,
    ncm="",
    tomador=None,
    servico=None,
    valores=None,
):
    """Monta dados canonicos do EnviaLoteRps GeisWeb."""

    _validar_vinculo_configuracao(
        configuracao,
        configuracao_fiscal,
    )

    numero_rps = getattr(
        documento,
        "numero_rps",
        None,
    )

    numero_rps = _obrigatorio(
        numero_rps,
        campo="documento.numero_rps",
    )

    numero_lote = _obrigatorio(
        numero_lote,
        campo="numero_lote",
    )

    cnpj_prestador = _documento_federal(
        getattr(
            configuracao,
            "cnpj",
            None,
        ),
        campo="configuracao.cnpj",
    )

    inscricao_municipal = _obrigatorio(
        getattr(
            configuracao_fiscal,
            "inscricao_municipal",
            None,
        ),
        campo="configuracao_fiscal.inscricao_municipal",
    )

    municipio_prestador = _obrigatorio(
        getattr(
            configuracao_fiscal,
            "municipio_ibge",
            None,
        ),
        campo="configuracao_fiscal.municipio_ibge",
    )

    if municipio_prestador != MUNICIPIO_IBGE:
        raise AdaptacaoGeisWebErpInvalida(
            "GEISWEB_TIETE exige municipio IBGE "
            f"{MUNICIPIO_IBGE}."
        )

    if tomador is None:
        tomador = montar_tomador_da_os(
            ordem_servico
        )

    if servico is None:
        servico = montar_servico_da_os(
            ordem_servico,
            configuracao_fiscal,
            municipio_incidencia_ibge=(
                municipio_prestador
            ),
            municipio_prestacao_ibge=(
                municipio_prestador
            ),
        )

    if valores is None:
        valores = montar_valores_da_os(
            ordem_servico
        )

    if not isinstance(servico, dict):
        raise AdaptacaoGeisWebErpInvalida(
            "Servico ERP deve ser dict."
        )

    if not isinstance(valores, dict):
        raise AdaptacaoGeisWebErpInvalida(
            "Valores ERP devem ser dict."
        )

    codigo_servico = _obrigatorio(
        servico.get(
            "codigo_tributacao_municipal"
        ),
        campo=(
            "servico.codigo_tributacao_municipal"
        ),
    )

    descricao = _obrigatorio(
        servico.get("descricao"),
        campo="servico.descricao",
    )

    municipio_prestacao = _obrigatorio(
        servico.get(
            "municipio_prestacao_ibge"
        ),
        campo="servico.municipio_prestacao_ibge",
    )

    valor_servicos = _decimal(
        valores.get("valor_servicos"),
        campo="valores.valor_servicos",
    )

    aliquota = _decimal(
        getattr(
            configuracao_fiscal,
            "aliquota_iss_padrao",
            None,
        ),
        campo=(
            "configuracao_fiscal.aliquota_iss_padrao"
        ),
    )

    nbs = _texto(
        servico.get("nbs")
    )

    lote = {
        "cnpj_cpf": cnpj_prestador,
        "numero_lote": numero_lote,
        "rps": [
            {
                "numero_rps": numero_rps,
                "data_emissao": _data_emissao(
                    data_emissao
                ),
                "servico": {
                    "valores": {
                        "valor_servicos": (
                            valor_servicos
                        ),
                        "base_calculo": _decimal(
                            base_calculo,
                            campo="base_calculo",
                        ),
                        "aliquota": aliquota,
                    },
                    "codigo_servico": (
                        codigo_servico
                    ),
                    "tipo_lancamento": (
                        _obrigatorio(
                            tipo_lancamento,
                            campo="tipo_lancamento",
                        )
                    ),
                    "discriminacao": descricao,
                    "municipio_prestacao_servico": (
                        municipio_prestacao
                    ),
                },
                "prestador": {
                    "cnpj_cpf": cnpj_prestador,
                    "inscricao_municipal": (
                        inscricao_municipal
                    ),
                    "regime": _obrigatorio(
                        regime_geisweb,
                        campo="regime_geisweb",
                    ),
                },
                "tomador": _normalizar_tomador(
                    tomador
                ),
                "orgao_gerador": {
                    "codigo_municipio": (
                        MUNICIPIO_IBGE
                    ),
                    "uf": "SP",
                },
                "outros_impostos": (
                    _normalizar_outros_impostos(
                        outros_impostos
                    )
                ),
                "ncm": _texto(ncm),
                "nbs": nbs,
                "codigo_nacional": (
                    _obrigatorio(
                        codigo_nacional,
                        campo="codigo_nacional",
                    )
                ),
                "ibs_cbs": _normalizar_ibs_cbs(
                    ibs_cbs
                ),
            }
        ],
    }

    return lote
