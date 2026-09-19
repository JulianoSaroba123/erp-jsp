"""Builder XML do EnviaLoteRps GeisWeb 1.01.

Nao transmite.
Nao assina.
Nao acessa certificado.
Nao acessa banco.

A responsabilidade deste modulo e exclusivamente construir o XML
municipal conforme o schema GeisWeb Reforma 1.01.
"""

from lxml import etree

from app.fiscal.providers.geisweb_tiete_config import (
    NAMESPACE_ENVIO_LOTE_RPS,
)


class EstruturaGeisWebInvalida(ValueError):
    """Dados insuficientes ou invalidos para gerar XML GeisWeb."""


NS = NAMESPACE_ENVIO_LOTE_RPS


def _qname(nome: str):
    return etree.QName(NS, nome)


def _texto(valor):
    if valor is None:
        return ""
    return str(valor).strip()


def _obrigatorio(dados, chave, *, contexto):
    if not isinstance(dados, dict):
        raise EstruturaGeisWebInvalida(
            f"{contexto} deve ser dict."
        )

    if chave not in dados:
        raise EstruturaGeisWebInvalida(
            f"Campo obrigatorio ausente: {contexto}.{chave}"
        )

    return dados[chave]


def _grupo(dados, chave, *, contexto):
    valor = _obrigatorio(
        dados,
        chave,
        contexto=contexto,
    )

    if not isinstance(valor, dict):
        raise EstruturaGeisWebInvalida(
            f"{contexto}.{chave} deve ser dict."
        )

    return valor


def _elemento(pai, nome, valor=None):
    filho = etree.SubElement(
        pai,
        _qname(nome),
    )

    if valor is not None:
        filho.text = _texto(valor)

    return filho


def _montar_servico(rps_xml, dados):
    servico = _grupo(
        dados,
        "servico",
        contexto="rps",
    )

    xml = _elemento(
        rps_xml,
        "Servico",
    )

    valores = _grupo(
        servico,
        "valores",
        contexto="rps.servico",
    )

    valores_xml = _elemento(
        xml,
        "Valores",
    )

    _elemento(
        valores_xml,
        "ValorServicos",
        _obrigatorio(
            valores,
            "valor_servicos",
            contexto="rps.servico.valores",
        ),
    )

    _elemento(
        valores_xml,
        "BaseCalculo",
        _obrigatorio(
            valores,
            "base_calculo",
            contexto="rps.servico.valores",
        ),
    )

    _elemento(
        valores_xml,
        "Aliquota",
        _obrigatorio(
            valores,
            "aliquota",
            contexto="rps.servico.valores",
        ),
    )

    for chave, nome in (
        ("codigo_servico", "CodigoServico"),
        ("tipo_lancamento", "TipoLancamento"),
        ("discriminacao", "Discriminacao"),
        (
            "municipio_prestacao_servico",
            "MunicipioPrestacaoServico",
        ),
    ):
        _elemento(
            xml,
            nome,
            _obrigatorio(
                servico,
                chave,
                contexto="rps.servico",
            ),
        )


def _montar_prestador(rps_xml, dados):
    prestador = _grupo(
        dados,
        "prestador",
        contexto="rps",
    )

    xml = _elemento(
        rps_xml,
        "PrestadorServico",
    )

    identificacao = _elemento(
        xml,
        "IdentificacaoPrestador",
    )

    for chave, nome in (
        ("cnpj_cpf", "CnpjCpf"),
        ("inscricao_municipal", "InscricaoMunicipal"),
        ("regime", "Regime"),
    ):
        _elemento(
            identificacao,
            nome,
            _obrigatorio(
                prestador,
                chave,
                contexto="rps.prestador",
            ),
        )


def _montar_tomador(rps_xml, dados):
    tomador = _grupo(
        dados,
        "tomador",
        contexto="rps",
    )

    xml = _elemento(
        rps_xml,
        "TomadorServico",
    )

    ident = _elemento(
        xml,
        "IdentificacaoTomador",
    )

    for chave, nome in (
        ("cnpj_cpf", "CnpjCpf"),
        ("nif", "NIF"),
        ("nao_nif", "NaoNIF"),
    ):
        _elemento(
            ident,
            nome,
            _obrigatorio(
                tomador,
                chave,
                contexto="rps.tomador",
            ),
        )

    _elemento(
        xml,
        "RazaoSocial",
        _obrigatorio(
            tomador,
            "razao_social",
            contexto="rps.tomador",
        ),
    )

    endereco = _grupo(
        tomador,
        "endereco",
        contexto="rps.tomador",
    )

    endereco_xml = _elemento(
        xml,
        "Endereco",
    )

    campos = (
        ("rua", "Rua"),
        ("numero", "Numero"),
        ("bairro", "Bairro"),
        ("cidade", "Cidade"),
        ("estado", "Estado"),
        ("cep", "Cep"),
        ("pais", "Pais"),
        ("prov_reg", "ProvReg"),
    )

    for chave, nome in campos:
        _elemento(
            endereco_xml,
            nome,
            _obrigatorio(
                endereco,
                chave,
                contexto="rps.tomador.endereco",
            ),
        )

    if "telefone" in endereco:
        _elemento(
            endereco_xml,
            "Telefone",
            endereco.get("telefone"),
        )

    if "email" in endereco:
        _elemento(
            endereco_xml,
            "Email",
            endereco.get("email"),
        )


def _montar_orgao_gerador(rps_xml, dados):
    orgao = _grupo(
        dados,
        "orgao_gerador",
        contexto="rps",
    )

    xml = _elemento(
        rps_xml,
        "OrgaoGerador",
    )

    _elemento(
        xml,
        "CodigoMunicipio",
        _obrigatorio(
            orgao,
            "codigo_municipio",
            contexto="rps.orgao_gerador",
        ),
    )

    _elemento(
        xml,
        "Uf",
        _obrigatorio(
            orgao,
            "uf",
            contexto="rps.orgao_gerador",
        ),
    )


def _montar_outros_impostos(rps_xml, dados):
    impostos = _grupo(
        dados,
        "outros_impostos",
        contexto="rps",
    )

    xml = _elemento(
        rps_xml,
        "OutrosImpostos",
    )

    for chave, nome in (
        ("pis", "Pis"),
        ("cofins", "Cofins"),
        ("csll", "Csll"),
        ("irrf", "Irrf"),
        ("inss", "Inss"),
    ):
        _elemento(
            xml,
            nome,
            _obrigatorio(
                impostos,
                chave,
                contexto="rps.outros_impostos",
            ),
        )


def _montar_ibs_cbs(rps_xml, dados):
    ibs_cbs = _grupo(
        dados,
        "ibs_cbs",
        contexto="rps",
    )

    xml = _elemento(
        rps_xml,
        "IBSCBS",
    )

    valores = _elemento(
        xml,
        "valores",
    )

    trib = _elemento(
        valores,
        "trib",
    )

    grupo = _elemento(
        trib,
        "gIBSCBS",
    )

    _elemento(
        grupo,
        "cClassTrib",
        _obrigatorio(
            ibs_cbs,
            "c_class_trib",
            contexto="rps.ibs_cbs",
        ),
    )

    _elemento(
        grupo,
        "Ibs",
        _obrigatorio(
            ibs_cbs,
            "ibs",
            contexto="rps.ibs_cbs",
        ),
    )

    _elemento(
        grupo,
        "Cbs",
        _obrigatorio(
            ibs_cbs,
            "cbs",
            contexto="rps.ibs_cbs",
        ),
    )

    regular = _elemento(
        grupo,
        "gTribRegular",
    )

    _elemento(
        regular,
        "cClassTribReg",
        _obrigatorio(
            ibs_cbs,
            "c_class_trib_reg",
            contexto="rps.ibs_cbs",
        ),
    )


def _montar_rps(raiz, dados):
    xml = _elemento(
        raiz,
        "Rps",
    )

    identificacao = _elemento(
        xml,
        "IdentificacaoRps",
    )

    _elemento(
        identificacao,
        "NumeroRps",
        _obrigatorio(
            dados,
            "numero_rps",
            contexto="rps",
        ),
    )

    _elemento(
        xml,
        "DataEmissao",
        _obrigatorio(
            dados,
            "data_emissao",
            contexto="rps",
        ),
    )

    _montar_servico(xml, dados)
    _montar_prestador(xml, dados)
    _montar_tomador(xml, dados)
    _montar_orgao_gerador(xml, dados)
    _montar_outros_impostos(xml, dados)

    _elemento(
        xml,
        "NCM",
        _obrigatorio(
            dados,
            "ncm",
            contexto="rps",
        ),
    )

    _elemento(
        xml,
        "NBS",
        _obrigatorio(
            dados,
            "nbs",
            contexto="rps",
        ),
    )

    _elemento(
        xml,
        "CodigoNacional",
        _obrigatorio(
            dados,
            "codigo_nacional",
            contexto="rps",
        ),
    )

    _montar_ibs_cbs(
        xml,
        dados,
    )


def montar_xml_envio_lote_rps(dados: dict):
    if not isinstance(dados, dict):
        raise EstruturaGeisWebInvalida(
            "Dados do lote GeisWeb devem ser dict."
        )

    rps_lista = _obrigatorio(
        dados,
        "rps",
        contexto="lote",
    )

    if (
        not isinstance(rps_lista, list)
        or not rps_lista
    ):
        raise EstruturaGeisWebInvalida(
            "lote.rps deve possuir ao menos um RPS."
        )

    raiz = etree.Element(
        _qname("EnviaLoteRps"),
        nsmap={None: NS},
    )

    _elemento(
        raiz,
        "CnpjCpf",
        _obrigatorio(
            dados,
            "cnpj_cpf",
            contexto="lote",
        ),
    )

    _elemento(
        raiz,
        "NumeroLote",
        _obrigatorio(
            dados,
            "numero_lote",
            contexto="lote",
        ),
    )

    for rps in rps_lista:
        if not isinstance(rps, dict):
            raise EstruturaGeisWebInvalida(
                "Cada RPS deve ser dict."
            )

        _montar_rps(
            raiz,
            rps,
        )

    return raiz


def serializar_xml_geisweb(elemento) -> bytes:
    return etree.tostring(
        elemento,
        encoding="ISO-8859-1",
        xml_declaration=True,
        pretty_print=False,
    )


def montar_xml_envio_lote_rps_serializado(
    dados: dict,
) -> bytes:
    return serializar_xml_geisweb(
        montar_xml_envio_lote_rps(
            dados
        )
    )
