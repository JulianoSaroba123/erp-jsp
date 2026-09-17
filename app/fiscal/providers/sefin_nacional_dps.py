"""Modelo interno canonico da DPS da NFS-e Nacional.

D24F02-B4.1:
- alinha obrigatoriedades ao XSD v1.01;
- adiciona identificacao formal da DPS;
- gera Id canonico da DPS;
- nao gera XML;
- nao assina documento;
- nao realiza HTTP;
- preserva CNPJ alfanumerico.
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re


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


def _datetime_emissao(valor) -> str:
    if not isinstance(valor, datetime):
        raise DpsCanonicaInvalida(
            "dhEmi deve ser datetime."
        )

    if valor.tzinfo is None or valor.utcoffset() is None:
        raise DpsCanonicaInvalida(
            "dhEmi deve possuir timezone."
        )

    texto = valor.replace(
        microsecond=0
    ).isoformat()

    # O schema atual aceita offsets de hora cheia.
    if not re.fullmatch(
        r"20\d{2}-\d{2}-\d{2}T"
        r"\d{2}:\d{2}:\d{2}"
        r"[+-]\d{2}:00",
        texto,
    ):
        raise DpsCanonicaInvalida(
            "dhEmi fora do formato aceito pelo XSD."
        )

    return texto


def _documento_federal(
    documento,
    *,
    tipo_documento: str,
) -> str:
    valor = _texto(
        documento,
        campo="documento",
        obrigatorio=True,
    ).upper()

    tipo = tipo_documento.upper()

    if tipo == "CPF":
        somente_digitos = "".join(
            c for c in valor if c.isdigit()
        )

        if len(somente_digitos) != 11:
            raise DpsCanonicaInvalida(
                "CPF deve possuir 11 digitos."
            )

        return somente_digitos

    if tipo == "CNPJ":
        normalizado = "".join(
            c
            for c in valor
            if c.isalnum()
        ).upper()

        if not re.fullmatch(
            r"[0-9A-Z]{14}",
            normalizado,
        ):
            raise DpsCanonicaInvalida(
                "CNPJ deve possuir 14 caracteres alfanumericos."
            )

        return normalizado

    raise DpsCanonicaInvalida(
        "Tipo de documento deve ser CPF ou CNPJ."
    )


def gerar_id_dps(
    *,
    municipio_ibge,
    tipo_documento,
    documento,
    serie,
    numero_dps,
) -> str:
    """Gera Id de 45 caracteres conforme TSIdDPS."""

    municipio = _texto(
        municipio_ibge,
        campo="municipio_ibge",
        obrigatorio=True,
    )

    if not re.fullmatch(r"[0-9]{7}", municipio):
        raise DpsCanonicaInvalida(
            "Municipio IBGE deve possuir 7 digitos."
        )

    tipo = str(tipo_documento or "").strip().upper()

    documento_normalizado = _documento_federal(
        documento,
        tipo_documento=tipo,
    )

    if tipo == "CPF":
        tipo_inscricao = "1"
        inscricao_id = documento_normalizado.zfill(14)
    else:
        tipo_inscricao = "2"
        inscricao_id = documento_normalizado

    serie_texto = _texto(
        serie,
        campo="serie",
        obrigatorio=True,
    )

    if not re.fullmatch(
        r"[0-9]{1,4}|[0-8][0-9]{4}",
        serie_texto,
    ):
        raise DpsCanonicaInvalida(
            "Serie DPS invalida."
        )

    numero_texto = _texto(
        numero_dps,
        campo="numero_dps",
        obrigatorio=True,
    )

    if not re.fullmatch(
        r"[1-9][0-9]{0,14}",
        numero_texto,
    ):
        raise DpsCanonicaInvalida(
            "Numero DPS invalido."
        )

    identificador = (
        "DPS"
        + municipio
        + tipo_inscricao
        + inscricao_id
        + serie_texto.zfill(5)
        + numero_texto.zfill(15)
    )

    if len(identificador) != 45:
        raise DpsCanonicaInvalida(
            "Id DPS nao possui 45 caracteres."
        )

    return identificador


def montar_dps_canonica(
    *,
    ambiente,
    versao_layout,
    data_emissao,
    versao_aplicativo,
    serie,
    numero_dps,
    competencia,
    tipo_emitente,
    municipio_emissao_ibge,
    servico: dict,
    valores: dict,
    prestador: dict | None = None,
    configuracao=None,
    configuracao_fiscal=None,
    tomador: dict | None = None,
    iss: dict | None = None,
    totais_tributos: dict | None = None,
    ibs_cbs: dict | None = None,
) -> dict:
    """Monta representacao interna validada da DPS."""

    ambiente_normalizado = _texto(
        ambiente,
        campo="ambiente",
        obrigatorio=True,
    ).upper()

    mapa_ambiente = {
        "PRODUCAO": "1",
        "HOMOLOGACAO": "2",
    }

    tp_amb = mapa_ambiente.get(
        ambiente_normalizado
    )

    if tp_amb is None:
        raise DpsCanonicaInvalida(
            "Ambiente da DPS invalido."
        )

    versao = _texto(
        versao_layout,
        campo="versao_layout",
        obrigatorio=True,
    )

    ver_aplic = _texto(
        versao_aplicativo,
        campo="versao_aplicativo",
        obrigatorio=True,
    )

    if len(ver_aplic) > 20:
        raise DpsCanonicaInvalida(
            "Versao do aplicativo excede 20 caracteres."
        )

    tipo_emitente = str(
        tipo_emitente or ""
    ).strip()

    if tipo_emitente not in {
        "1",
        "2",
        "3",
    }:
        raise DpsCanonicaInvalida(
            "Tipo emitente da DPS invalido."
        )

    municipio_emissao = _texto(
        municipio_emissao_ibge,
        campo="municipio_emissao_ibge",
        obrigatorio=True,
    )

    if not re.fullmatch(
        r"[0-9]{7}",
        municipio_emissao,
    ):
        raise DpsCanonicaInvalida(
            "Municipio de emissao deve possuir 7 digitos."
        )

    # --------------------------------------------------------
    # PRESTADOR CANONICO
    # --------------------------------------------------------
    # Quando as fontes institucionais/fiscais sao fornecidas,
    # elas sao a fonte de verdade do prestador da DPS.
    #
    # O parametro prestador permanece temporariamente como
    # compatibilidade dos testes canonicos anteriores (B4.2).
    # --------------------------------------------------------
    if configuracao is not None or configuracao_fiscal is not None:
        prestador = montar_prestador_canonico(
            configuracao=configuracao,
            configuracao_fiscal=configuracao_fiscal,
        )
    elif prestador is None:
        raise DpsCanonicaInvalida(
            "Prestador canonico ou configuracao fiscal deve ser informado."
        )

    tipo_documento_prestador = _texto(
        prestador.get(
            "tipo_documento",
            "CNPJ",
        ),
        campo="prestador.tipo_documento",
        obrigatorio=True,
    ).upper()

    documento_prestador = _documento_federal(
        prestador.get("documento"),
        tipo_documento=tipo_documento_prestador,
    )

    id_dps = gerar_id_dps(
        municipio_ibge=municipio_emissao,
        tipo_documento=tipo_documento_prestador,
        documento=documento_prestador,
        serie=serie,
        numero_dps=numero_dps,
    )

    municipio_prestador = _texto(
        prestador.get("municipio_ibge"),
        campo="prestador.municipio_ibge",
        obrigatorio=True,
    )

    if not re.fullmatch(
        r"[0-9]{7}",
        municipio_prestador,
    ):
        raise DpsCanonicaInvalida(
            "Municipio IBGE do prestador invalido."
        )

    reg_trib = dict(
        prestador.get("regime_tributario")
        or {}
    )

    if not reg_trib:
        raise DpsCanonicaInvalida(
            "Regime tributario do prestador nao informado."
        )

    op_simp_nac = _texto(
        reg_trib.get("op_simp_nac"),
        campo="prestador.regime_tributario.op_simp_nac",
        obrigatorio=True,
    )

    reg_esp_trib = _texto(
        reg_trib.get("reg_esp_trib"),
        campo="prestador.regime_tributario.reg_esp_trib",
        obrigatorio=True,
    )

    codigo_lista_nacional = _texto(
        servico.get("codigo_lista_nacional"),
        campo="servico.codigo_lista_nacional",
        obrigatorio=True,
    )

    # cTribNac - TSCodTribNac
    # XSD v1.01: exatamente 6 digitos.
    if not re.fullmatch(
        r"[0-9]{6}",
        codigo_lista_nacional,
    ):
        raise DpsCanonicaInvalida(
            "Codigo de tributacao nacional deve possuir 6 digitos."
        )

    codigo_tributacao_municipal = _texto(
        servico.get("codigo_tributacao_municipal"),
        campo="servico.codigo_tributacao_municipal",
    )

    # cTribMun - TCCodTribMun
    # Opcional; quando informado, exatamente 3 digitos.
    if codigo_tributacao_municipal is not None:
        if not re.fullmatch(
            r"[0-9]{3}",
            codigo_tributacao_municipal,
        ):
            raise DpsCanonicaInvalida(
                "Codigo de tributacao municipal deve possuir 3 digitos."
            )

    nbs = _texto(
        servico.get("nbs"),
        campo="servico.nbs",
    )

    # cNBS - TSCodNBS
    # Opcional; quando informado, exatamente 9 digitos.
    if nbs is not None and not re.fullmatch(
        r"[0-9]{9}",
        nbs,
    ):
        raise DpsCanonicaInvalida(
            "Codigo NBS deve possuir 9 digitos."
        )

    # O grupo IBS/CBS permanece opcional nesta etapa.
    # Contudo, se ele for efetivamente informado,
    # a classificacao NBS precisa estar presente.
    if ibs_cbs and nbs is None:
        raise DpsCanonicaInvalida(
            "Codigo NBS deve ser informado quando IBS/CBS for informado."
        )

    descricao_servico = _texto(
        servico.get("descricao"),
        campo="servico.descricao",
        obrigatorio=True,
    )

    municipio_incidencia = _texto(
        servico.get("municipio_incidencia_ibge"),
        campo="servico.municipio_incidencia_ibge",
        obrigatorio=True,
    )

    if not re.fullmatch(
        r"[0-9]{7}",
        municipio_incidencia,
    ):
        raise DpsCanonicaInvalida(
            "Municipio de incidencia invalido."
        )

    municipio_prestacao = _texto(
        servico.get("municipio_prestacao_ibge"),
        campo="servico.municipio_prestacao_ibge",
    )

    if (
        municipio_prestacao is not None
        and not re.fullmatch(
            r"[0-9]{7}",
            municipio_prestacao,
        )
    ):
        raise DpsCanonicaInvalida(
            "Municipio de prestacao invalido."
        )

    tomador_canonico = None

    if tomador:
        tipo_tomador = _texto(
            tomador.get("tipo_documento"),
            campo="tomador.tipo_documento",
            obrigatorio=True,
        ).upper()

        documento_tomador = _documento_federal(
            tomador.get("documento"),
            tipo_documento=tipo_tomador,
        )

        nome_tomador = _texto(
            tomador.get("nome"),
            campo="tomador.nome",
            obrigatorio=True,
        )

        endereco = tomador.get("endereco") or {}

        tomador_canonico = {
            "tipo_documento": tipo_tomador,
            "documento": documento_tomador,
            "nome": nome_tomador,
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
        }

    return {
        "identificacao": {
            "id": id_dps,
            "ambiente": ambiente_normalizado,
            "tp_amb": tp_amb,
            "dh_emi": _datetime_emissao(
                data_emissao
            ),
            "versao_layout": versao,
            "versao_aplicativo": ver_aplic,
            "serie": str(serie),
            "numero_dps": str(numero_dps),
            "competencia": _data_iso(
                competencia,
                campo="competencia",
            ),
            "tipo_emitente": tipo_emitente,
            "municipio_emissao_ibge": municipio_emissao,
        },
        "prestador": {
            "tipo_documento": tipo_documento_prestador,
            "documento": documento_prestador,
            "inscricao_municipal": _texto(
                prestador.get("inscricao_municipal"),
                campo="prestador.inscricao_municipal",
            ),
            "municipio_ibge": municipio_prestador,
            "nome": _texto(
                prestador.get("nome"),
                campo="prestador.nome",
            ),
            "regime_tributario": {
                "op_simp_nac": op_simp_nac,
                "reg_ap_trib_sn": _texto(
                    reg_trib.get("reg_ap_trib_sn"),
                    campo=(
                        "prestador.regime_tributario."
                        "reg_ap_trib_sn"
                    ),
                ),
                "reg_esp_trib": reg_esp_trib,
            },
        },
        "tomador": tomador_canonico,
        "servico": {
            "codigo_lista_nacional": codigo_lista_nacional,
            "codigo_tributacao_municipal": codigo_tributacao_municipal,
            "nbs": nbs,
            "descricao": descricao_servico,
            "municipio_incidencia_ibge": municipio_incidencia,
            **(
                {
                    "municipio_prestacao_ibge": (
                        municipio_prestacao
                    )
                }
                if municipio_prestacao is not None
                else {}
            ),
        },
        "valores": {
            "valor_servicos": _valor_decimal(
                valores.get("valor_servicos"),
                campo="valor_servicos",
            ),
            "valor_recebido": (
                _valor_decimal(
                    valores.get("valor_recebido"),
                    campo="valor_recebido",
                )
                if valores.get("valor_recebido") is not None
                else None
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
        "iss": montar_iss_canonico(
            iss=iss,
            configuracao_fiscal=configuracao_fiscal,
        ),
        **(
            {
                "totais_tributos": montar_totais_tributos_canonico(
                    totais_tributos
                )
            }
            if totais_tributos
            else {}
        ),
        "ibs_cbs": montar_ibs_cbs_canonico(
            ibs_cbs=ibs_cbs,
        ),
    }


def montar_prestador_canonico(configuracao, configuracao_fiscal):
    """Monta o prestador canonico da DPS a partir dos cadastros oficiais."""

    if configuracao is None:
        raise DpsCanonicaInvalida(
            "Configuracao institucional do prestador nao informada."
        )

    if configuracao_fiscal is None:
        raise DpsCanonicaInvalida(
            "Configuracao fiscal do prestador nao informada."
        )

    configuracao_id = getattr(configuracao, "id", None)
    configuracao_fiscal_id = getattr(
        configuracao_fiscal,
        "configuracao_id",
        None,
    )

    if configuracao_id is None:
        raise DpsCanonicaInvalida(
            "Identificador da configuracao institucional nao informado."
        )

    if configuracao_fiscal_id is None:
        raise DpsCanonicaInvalida(
            "Vinculo da configuracao fiscal com a configuracao institucional "
            "nao informado."
        )

    if configuracao_id != configuracao_fiscal_id:
        raise DpsCanonicaInvalida(
            "Configuracao fiscal nao pertence a configuracao institucional "
            "informada."
        )

    cnpj_original = getattr(configuracao, "cnpj", None)
    cnpj = "".join(
        caractere
        for caractere in str(cnpj_original or "")
        if caractere.isdigit()
    )

    if len(cnpj) != 14:
        raise DpsCanonicaInvalida(
            "CNPJ do prestador deve possuir 14 digitos."
        )

    razao_social = str(
        getattr(configuracao, "razao_social", None) or ""
    ).strip()

    if not razao_social:
        raise DpsCanonicaInvalida(
            "Razao social do prestador nao informada."
        )

    inscricao_municipal = str(
        getattr(configuracao_fiscal, "inscricao_municipal", None) or ""
    ).strip()

    if not inscricao_municipal:
        raise DpsCanonicaInvalida(
            "Inscricao municipal do prestador nao informada."
        )

    municipio_ibge = str(
        getattr(configuracao_fiscal, "municipio_ibge", None) or ""
    ).strip()

    if not municipio_ibge.isdigit() or len(municipio_ibge) != 7:
        raise DpsCanonicaInvalida(
            "Municipio IBGE do prestador deve possuir 7 digitos."
        )

    return {
        "tipo_documento": "CNPJ",
        "documento": cnpj,
        "inscricao_municipal": inscricao_municipal,
        "municipio_ibge": municipio_ibge,
        "nome": razao_social,
        "regime_tributario": {
            "op_simp_nac": getattr(
                configuracao_fiscal,
                "op_simp_nac",
                None,
            ),
            "reg_ap_trib_sn": getattr(
                configuracao_fiscal,
                "reg_ap_trib_sn",
                None,
            ),
            "reg_esp_trib": getattr(
                configuracao_fiscal,
                "reg_esp_trib",
                None,
            ),
        },
    }

def montar_iss_canonico(iss=None, configuracao_fiscal=None):
    """Monta o bloco canonico de tributacao municipal do ISSQN."""

    from decimal import Decimal, InvalidOperation

    dados = dict(iss or {})

    # ISS ainda e opcional na montagem canonica durante o B4.4B.
    # Quando informado, seu contrato passa a ser estrito.
    if not dados:
        return {}

    tributacao_issqn = _texto(
        dados.get("tributacao_issqn"),
        campo="iss.tributacao_issqn",
        obrigatorio=True,
    )

    if tributacao_issqn not in {"1", "2", "3", "4"}:
        raise DpsCanonicaInvalida(
            "Tributacao do ISSQN deve possuir codigo entre 1 e 4."
        )

    tipo_retencao = _texto(
        dados.get("tipo_retencao"),
        campo="iss.tipo_retencao",
        obrigatorio=True,
    )

    if tipo_retencao not in {"1", "2", "3"}:
        raise DpsCanonicaInvalida(
            "Tipo de retencao do ISSQN deve possuir codigo entre 1 e 3."
        )

    aliquota = dados.get("aliquota")

    if (
        aliquota in (None, "")
        and configuracao_fiscal is not None
    ):
        aliquota = getattr(
            configuracao_fiscal,
            "aliquota_iss_padrao",
            None,
        )

    aliquota_canonica = None

    if aliquota not in (None, ""):
        try:
            aliquota_decimal = Decimal(
                str(aliquota).strip().replace(",", ".")
            )
        except (InvalidOperation, ValueError):
            raise DpsCanonicaInvalida(
                "Aliquota do ISSQN invalida."
            )

        if not Decimal("0") <= aliquota_decimal <= Decimal("100"):
            raise DpsCanonicaInvalida(
                "Aliquota do ISSQN deve estar entre 0 e 100."
            )

        aliquota_canonica = format(
            aliquota_decimal.quantize(Decimal("0.01")),
            "f",
        )

    return {
        "tributacao_issqn": tributacao_issqn,
        "tipo_retencao": tipo_retencao,
        "aliquota": aliquota_canonica,
    }

def montar_totais_tributos_canonico(
    totais_tributos=None,
):
    """Monta a declaracao canonica de totais tributarios da DPS."""

    dados = dict(
        totais_tributos or {}
    )

    if not dados:
        return {}

    indicador = _texto(
        dados.get("indicador"),
        campo="totais_tributos.indicador",
        obrigatorio=True,
    )

    # B5.4D suporta somente a declaracao explicita
    # correspondente ao indTotTrib=0 do layout DPS 1.01.
    if indicador != "0":
        raise DpsCanonicaInvalida(
            "Indicador de totais tributarios deve ser 0 neste contrato."
        )

    return {
        "indicador": indicador,
    }


def montar_ibs_cbs_canonico(ibs_cbs=None):
    """Monta o bloco canonico declaratorio de IBS/CBS da DPS."""

    dados = dict(ibs_cbs or {})

    if not dados:
        return {}

    c_ind_op = _texto(
        dados.get("c_ind_op"),
        campo="ibs_cbs.c_ind_op",
        obrigatorio=True,
    )

    if not re.fullmatch(r"[0-9]{6}", c_ind_op):
        raise DpsCanonicaInvalida(
            "Indicador da operacao IBS/CBS deve possuir 6 digitos."
        )

    cst = _texto(
        dados.get("cst"),
        campo="ibs_cbs.cst",
        obrigatorio=True,
    )

    if not re.fullmatch(r"[0-9]{3}", cst):
        raise DpsCanonicaInvalida(
            "CST do IBS/CBS deve possuir 3 digitos."
        )

    c_class_trib = _texto(
        dados.get("c_class_trib"),
        campo="ibs_cbs.c_class_trib",
        obrigatorio=True,
    )

    if not re.fullmatch(r"[0-9]{6}", c_class_trib):
        raise DpsCanonicaInvalida(
            "Classificacao tributaria IBS/CBS deve possuir 6 digitos."
        )

    modo_xml = any(
        chave in dados
        for chave in (
            "fin_nfse",
            "ind_final",
            "ind_dest",
        )
    )

    if not modo_xml:
        return {
            "c_ind_op": c_ind_op,
            "cst": cst,
            "c_class_trib": c_class_trib,
        }

    fin_nfse = _texto(
        dados.get("fin_nfse"),
        campo="ibs_cbs.fin_nfse",
        obrigatorio=True,
    )

    if fin_nfse != "0":
        raise DpsCanonicaInvalida(
            "Finalidade da NFS-e IBS/CBS deve ser 0."
        )

    ind_dest = _texto(
        dados.get("ind_dest"),
        campo="ibs_cbs.ind_dest",
        obrigatorio=True,
    )

    if ind_dest not in {"0", "1"}:
        raise DpsCanonicaInvalida(
            "Indicador do destinatario IBS/CBS deve ser 0 ou 1."
        )

    ind_final = _texto(
        dados.get("ind_final"),
        campo="ibs_cbs.ind_final",
    )

    if (
        ind_final is not None
        and ind_final not in {"0", "1"}
    ):
        raise DpsCanonicaInvalida(
            "Indicador de consumidor final IBS/CBS deve ser 0 ou 1."
        )

    return {
        "fin_nfse": fin_nfse,
        "ind_final": ind_final,
        "c_ind_op": c_ind_op,
        "ind_dest": ind_dest,
        "cst": cst,
        "c_class_trib": c_class_trib,
    }
