"""Fundacao de serializacao XML da DPS Nacional."""

from lxml import etree


NAMESPACE_NFSE = "http://www.sped.fazenda.gov.br/nfse"
VERSAO_DPS = "1.01"


def _qname(nome: str) -> etree.QName:
    """Retorna QName no namespace oficial da NFS-e."""

    nome_normalizado = str(nome or "").strip()

    if not nome_normalizado:
        raise ValueError("Nome do elemento XML nao pode ser vazio.")

    return etree.QName(
        NAMESPACE_NFSE,
        nome_normalizado,
    )


def criar_elemento_nfse(
    nome: str,
    *,
    raiz: bool = False,
    **atributos,
):
    """Cria elemento XML pertencente ao namespace oficial da NFS-e."""

    nsmap = {None: NAMESPACE_NFSE} if raiz else None

    elemento = etree.Element(
        _qname(nome),
        nsmap=nsmap,
    )

    for chave, valor in atributos.items():
        if valor is not None:
            elemento.set(
                str(chave),
                str(valor),
            )

    return elemento


def serializar_xml(elemento) -> bytes:
    """Serializa arvore XML em UTF-8 de forma deterministica."""

    if elemento is None:
        raise ValueError("Elemento XML nao informado.")

    return etree.tostring(
        elemento,
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=False,
    )

class SerializacaoDpsInvalida(ValueError):
    """Erro de contrato entre a DPS canonica e o XML."""


def _valor_obrigatorio(dados, chave, *, grupo="identificacao"):
    """Obtem campo obrigatorio da representacao canonica."""

    if not isinstance(dados, dict):
        raise SerializacaoDpsInvalida(
            f"Grupo {grupo} da DPS canonica invalido."
        )

    valor = dados.get(chave)

    if valor is None or str(valor).strip() == "":
        raise SerializacaoDpsInvalida(
            f"Campo obrigatorio ausente: {grupo}.{chave}."
        )

    return str(valor).strip()


def adicionar_elemento_nfse(pai, nome: str, valor):
    """Adiciona elemento textual no namespace oficial da NFS-e."""

    if pai is None:
        raise SerializacaoDpsInvalida(
            "Elemento pai XML nao informado."
        )

    elemento = etree.SubElement(
        pai,
        _qname(nome),
    )

    elemento.text = str(valor)

    return elemento



def _valor_opcional(dados, chave):
    """Obtem valor textual opcional sem fabricar conteudo."""

    if not isinstance(dados, dict):
        return None

    valor = dados.get(chave)

    if valor is None:
        return None

    valor = str(valor).strip()

    return valor or None


def _adicionar_identificador_federal(
    pai,
    pessoa,
    *,
    grupo,
):
    """Serializa a escolha CPF/CNPJ do contrato nacional."""

    tipo_documento = _valor_obrigatorio(
        pessoa,
        "tipo_documento",
        grupo=grupo,
    ).upper()

    if tipo_documento not in {"CPF", "CNPJ"}:
        raise SerializacaoDpsInvalida(
            f"Tipo de documento nao suportado em {grupo}: "
            f"{tipo_documento}."
        )

    documento = _valor_obrigatorio(
        pessoa,
        "documento",
        grupo=grupo,
    )

    adicionar_elemento_nfse(
        pai,
        tipo_documento,
        documento,
    )


def _adicionar_regime_tributario(prestador_xml, regime):
    """Serializa TCRegTrib conforme layout DPS 1.01."""

    if not isinstance(regime, dict):
        raise SerializacaoDpsInvalida(
            "Grupo prestador.regime_tributario nao informado."
        )

    reg_trib = etree.SubElement(
        prestador_xml,
        _qname("regTrib"),
    )

    adicionar_elemento_nfse(
        reg_trib,
        "opSimpNac",
        _valor_obrigatorio(
            regime,
            "op_simp_nac",
            grupo="prestador.regime_tributario",
        ),
    )

    reg_ap_trib_sn = _valor_opcional(
        regime,
        "reg_ap_trib_sn",
    )

    if reg_ap_trib_sn is not None:
        adicionar_elemento_nfse(
            reg_trib,
            "regApTribSN",
            reg_ap_trib_sn,
        )

    adicionar_elemento_nfse(
        reg_trib,
        "regEspTrib",
        _valor_obrigatorio(
            regime,
            "reg_esp_trib",
            grupo="prestador.regime_tributario",
        ),
    )

    return reg_trib


def _adicionar_prestador(inf_dps, prestador):
    """Serializa TCInfoPrestador."""

    if not isinstance(prestador, dict):
        raise SerializacaoDpsInvalida(
            "Grupo prestador da DPS canonica nao informado."
        )

    prestador_xml = etree.SubElement(
        inf_dps,
        _qname("prest"),
    )

    _adicionar_identificador_federal(
        prestador_xml,
        prestador,
        grupo="prestador",
    )

    inscricao_municipal = _valor_opcional(
        prestador,
        "inscricao_municipal",
    )

    if inscricao_municipal is not None:
        adicionar_elemento_nfse(
            prestador_xml,
            "IM",
            inscricao_municipal,
        )

    nome = _valor_opcional(
        prestador,
        "nome",
    )

    if nome is not None:
        adicionar_elemento_nfse(
            prestador_xml,
            "xNome",
            nome,
        )

    # municipio_ibge nao possui tag direta em TCInfoPrestador.
    # Endereco do prestador nao integra o contrato canonico atual.

    _adicionar_regime_tributario(
        prestador_xml,
        prestador.get("regime_tributario"),
    )

    return prestador_xml


def _adicionar_tomador(inf_dps, tomador):
    """Serializa TCInfoPessoa quando houver tomador."""

    if tomador is None:
        return None

    if not isinstance(tomador, dict):
        raise SerializacaoDpsInvalida(
            "Grupo tomador da DPS canonica invalido."
        )

    tomador_xml = etree.SubElement(
        inf_dps,
        _qname("toma"),
    )

    _adicionar_identificador_federal(
        tomador_xml,
        tomador,
        grupo="tomador",
    )

    adicionar_elemento_nfse(
        tomador_xml,
        "xNome",
        _valor_obrigatorio(
            tomador,
            "nome",
            grupo="tomador",
        ),
    )

    # O endereco canonico atual nao possui municipio IBGE.
    # TCEnderNac exige cMun, portanto <end> nao e emitido neste marco.

    email = _valor_opcional(
        tomador,
        "email",
    )

    if email is not None:
        adicionar_elemento_nfse(
            tomador_xml,
            "email",
            email,
        )

    return tomador_xml



def _adicionar_servico(inf_dps, servico):
    """Serializa TCServ conforme DPS 1.01."""

    if not isinstance(servico, dict):
        raise SerializacaoDpsInvalida(
            "Grupo servico da DPS canonica nao informado."
        )

    serv_xml = etree.SubElement(
        inf_dps,
        _qname("serv"),
    )

    loc_prest = etree.SubElement(
        serv_xml,
        _qname("locPrest"),
    )

    adicionar_elemento_nfse(
        loc_prest,
        "cLocPrestacao",
        _valor_obrigatorio(
            servico,
            "municipio_prestacao_ibge",
            grupo="servico",
        ),
    )

    c_serv = etree.SubElement(
        serv_xml,
        _qname("cServ"),
    )

    adicionar_elemento_nfse(
        c_serv,
        "cTribNac",
        _valor_obrigatorio(
            servico,
            "codigo_lista_nacional",
            grupo="servico",
        ),
    )

    codigo_municipal = _valor_opcional(
        servico,
        "codigo_tributacao_municipal",
    )

    if codigo_municipal is not None:
        adicionar_elemento_nfse(
            c_serv,
            "cTribMun",
            codigo_municipal,
        )

    adicionar_elemento_nfse(
        c_serv,
        "xDescServ",
        _valor_obrigatorio(
            servico,
            "descricao",
            grupo="servico",
        ),
    )

    nbs = _valor_opcional(
        servico,
        "nbs",
    )

    if nbs is not None:
        adicionar_elemento_nfse(
            c_serv,
            "cNBS",
            nbs,
        )

    return serv_xml




def _valor_monetario_nao_zero(
    dados,
    chave,
    *,
    grupo="valores",
):
    """Retorna valor monetario somente quando diferente de zero."""

    from decimal import Decimal, InvalidOperation

    valor = _valor_opcional(
        dados,
        chave,
    )

    if valor is None:
        return None

    try:
        decimal = Decimal(valor)
    except InvalidOperation as exc:
        raise SerializacaoDpsInvalida(
            f"Valor monetario invalido: {grupo}.{chave}."
        ) from exc

    if decimal == 0:
        return None

    return valor


def _adicionar_valores_basicos(inf_dps, valores):
    """Serializa o bloco inicial TCInfoValores da DPS 1.01."""

    if not isinstance(valores, dict):
        raise SerializacaoDpsInvalida(
            "Grupo valores da DPS canonica nao informado."
        )

    valores_xml = etree.SubElement(
        inf_dps,
        _qname("valores"),
    )

    v_serv_prest = etree.SubElement(
        valores_xml,
        _qname("vServPrest"),
    )

    # vReceb nao e emitido neste marco.
    # No XSD ele representa valor recebido pelo intermediario,
    # enquanto o campo canonico valor_recebido ainda e generico.

    adicionar_elemento_nfse(
        v_serv_prest,
        "vServ",
        _valor_obrigatorio(
            valores,
            "valor_servicos",
            grupo="valores",
        ),
    )

    desconto_incondicionado = _valor_monetario_nao_zero(
        valores,
        "desconto_incondicionado",
    )

    desconto_condicionado = _valor_monetario_nao_zero(
        valores,
        "desconto_condicionado",
    )

    if (
        desconto_incondicionado is not None
        or desconto_condicionado is not None
    ):
        descontos_xml = etree.SubElement(
            valores_xml,
            _qname("vDescCondIncond"),
        )

        if desconto_incondicionado is not None:
            adicionar_elemento_nfse(
                descontos_xml,
                "vDescIncond",
                desconto_incondicionado,
            )

        if desconto_condicionado is not None:
            adicionar_elemento_nfse(
                descontos_xml,
                "vDescCond",
                desconto_condicionado,
            )

    deducoes = _valor_monetario_nao_zero(
        valores,
        "deducoes",
    )

    if deducoes is not None:
        deducoes_xml = etree.SubElement(
            valores_xml,
            _qname("vDedRed"),
        )

        adicionar_elemento_nfse(
            deducoes_xml,
            "vDR",
            deducoes,
        )

    return valores_xml



def _adicionar_tributacao_municipal(
    valores_xml,
    iss,
    totais_tributos,
):
    """Serializa trib/tribMun/totTrib da DPS 1.01."""

    iss_informado = isinstance(iss, dict) and bool(iss)
    totais_informados = (
        isinstance(totais_tributos, dict)
        and bool(totais_tributos)
    )

    # Compatibilidade dos marcos anteriores enquanto o XML
    # ainda esta sendo construido incrementalmente.
    if not iss_informado and not totais_informados:
        return None

    if not iss_informado:
        raise SerializacaoDpsInvalida(
            "Grupo ISS canonico obrigatorio quando totais tributarios "
            "sao informados."
        )

    if not totais_informados:
        raise SerializacaoDpsInvalida(
            "Grupo totais_tributos canonico obrigatorio quando ISS "
            "e informado."
        )

    trib_xml = etree.SubElement(
        valores_xml,
        _qname("trib"),
    )

    trib_mun = etree.SubElement(
        trib_xml,
        _qname("tribMun"),
    )

    adicionar_elemento_nfse(
        trib_mun,
        "tribISSQN",
        _valor_obrigatorio(
            iss,
            "tributacao_issqn",
            grupo="iss",
        ),
    )

    adicionar_elemento_nfse(
        trib_mun,
        "tpRetISSQN",
        _valor_obrigatorio(
            iss,
            "tipo_retencao",
            grupo="iss",
        ),
    )

    aliquota = _valor_opcional(
        iss,
        "aliquota",
    )

    if aliquota is not None:
        adicionar_elemento_nfse(
            trib_mun,
            "pAliq",
            aliquota,
        )

    indicador = _valor_obrigatorio(
        totais_tributos,
        "indicador",
        grupo="totais_tributos",
    )

    if indicador != "0":
        raise SerializacaoDpsInvalida(
            "Indicador de totais tributarios incompativel "
            "com o contrato XML atual."
        )

    tot_trib = etree.SubElement(
        trib_xml,
        _qname("totTrib"),
    )

    adicionar_elemento_nfse(
        tot_trib,
        "indTotTrib",
        indicador,
    )

    return trib_xml


def _adicionar_ibs_cbs(
    inf_dps,
    ibs_cbs,
):
    """Serializa o grupo declaratorio IBS/CBS da DPS 1.01."""

    if ibs_cbs is None or ibs_cbs == {}:
        return None

    if not isinstance(ibs_cbs, dict):
        raise SerializacaoDpsInvalida(
            "Grupo ibs_cbs da DPS canonica invalido."
        )

    ibs_xml = etree.SubElement(
        inf_dps,
        _qname("IBSCBS"),
    )

    adicionar_elemento_nfse(
        ibs_xml,
        "finNFSe",
        _valor_obrigatorio(
            ibs_cbs,
            "fin_nfse",
            grupo="ibs_cbs",
        ),
    )

    ind_final = _valor_opcional(
        ibs_cbs,
        "ind_final",
    )

    if ind_final is not None:
        adicionar_elemento_nfse(
            ibs_xml,
            "indFinal",
            ind_final,
        )

    adicionar_elemento_nfse(
        ibs_xml,
        "cIndOp",
        _valor_obrigatorio(
            ibs_cbs,
            "c_ind_op",
            grupo="ibs_cbs",
        ),
    )

    adicionar_elemento_nfse(
        ibs_xml,
        "indDest",
        _valor_obrigatorio(
            ibs_cbs,
            "ind_dest",
            grupo="ibs_cbs",
        ),
    )

    valores_xml = etree.SubElement(
        ibs_xml,
        _qname("valores"),
    )

    trib_xml = etree.SubElement(
        valores_xml,
        _qname("trib"),
    )

    g_ibs_cbs = etree.SubElement(
        trib_xml,
        _qname("gIBSCBS"),
    )

    adicionar_elemento_nfse(
        g_ibs_cbs,
        "CST",
        _valor_obrigatorio(
            ibs_cbs,
            "cst",
            grupo="ibs_cbs",
        ),
    )

    adicionar_elemento_nfse(
        g_ibs_cbs,
        "cClassTrib",
        _valor_obrigatorio(
            ibs_cbs,
            "c_class_trib",
            grupo="ibs_cbs",
        ),
    )

    return ibs_xml


def montar_xml_dps(dps_canonica: dict):
    """Monta a estrutura XML inicial DPS/infDPS conforme layout 1.01."""

    if not isinstance(dps_canonica, dict):
        raise SerializacaoDpsInvalida(
            "DPS canonica deve ser um dicionario."
        )

    identificacao = dps_canonica.get("identificacao")

    if not isinstance(identificacao, dict):
        raise SerializacaoDpsInvalida(
            "Grupo identificacao da DPS canonica nao informado."
        )

    versao_layout = _valor_obrigatorio(
        identificacao,
        "versao_layout",
    )

    if versao_layout != VERSAO_DPS:
        raise SerializacaoDpsInvalida(
            "Versao da DPS canonica incompativel com o serializador."
        )

    raiz = criar_elemento_nfse(
        "DPS",
        raiz=True,
        versao=VERSAO_DPS,
    )

    inf_dps = etree.SubElement(
        raiz,
        _qname("infDPS"),
    )

    inf_dps.set(
        "Id",
        _valor_obrigatorio(
            identificacao,
            "id",
        ),
    )

    # Ordem obrigatoria definida pelo TCInfDPS do XSD v1.01.
    campos = (
        ("tpAmb", "tp_amb"),
        ("dhEmi", "dh_emi"),
        ("verAplic", "versao_aplicativo"),
        ("serie", "serie"),
        ("nDPS", "numero_dps"),
        ("dCompet", "competencia"),
        ("tpEmit", "tipo_emitente"),
        ("cLocEmi", "municipio_emissao_ibge"),
    )

    for tag_xml, chave_canonica in campos:
        adicionar_elemento_nfse(
            inf_dps,
            tag_xml,
            _valor_obrigatorio(
                identificacao,
                chave_canonica,
            ),
        )

    _adicionar_prestador(
        inf_dps,
        dps_canonica.get("prestador"),
    )

    _adicionar_tomador(
        inf_dps,
        dps_canonica.get("tomador"),
    )

    _adicionar_servico(
        inf_dps,
        dps_canonica.get("servico"),
    )

    valores_xml = _adicionar_valores_basicos(
        inf_dps,
        dps_canonica.get("valores"),
    )

    _adicionar_tributacao_municipal(
        valores_xml,
        dps_canonica.get("iss"),
        dps_canonica.get("totais_tributos"),
    )

    _adicionar_ibs_cbs(
        inf_dps,
        dps_canonica.get("ibs_cbs"),
    )

    return raiz
