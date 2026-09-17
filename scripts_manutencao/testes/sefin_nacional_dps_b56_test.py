from copy import deepcopy
from pathlib import Path
import runpy

import pytest
from lxml import etree

import app.fiscal.xml.dps_serializer as serializer

from app.fiscal.xml.dps_serializer import (
    EstruturaXmlDpsInvalida,
    NAMESPACE_NFSE,
    VERSAO_DPS,
    montar_xml_dps,
    serializar_xml,
    validar_estrutura_xml_dps,
)


def _dados_completos():
    caminho = Path(__file__).with_name(
        "sefin_nacional_dps_b55_test.py"
    )

    namespace = runpy.run_path(
        str(caminho)
    )

    return namespace["_dados_completos"]()


def _localname(elemento):
    return etree.QName(elemento).localname


def _filho_direto(pai, nome):
    for filho in pai:
        if _localname(filho) == nome:
            return filho

    raise AssertionError(
        f"Filho {nome} nao encontrado."
    )


def test_b56_001_estrutura_atual_valida_sem_mutacao():
    raiz = montar_xml_dps(
        _dados_completos()
    )

    antes = serializar_xml(
        raiz
    )

    validar_estrutura_xml_dps(
        raiz
    )

    depois = serializar_xml(
        raiz
    )

    assert depois == antes


def test_b56_002_raiz_ausente_bloqueada():
    with pytest.raises(
        EstruturaXmlDpsInvalida,
        match="Elemento XML ausente",
    ):
        validar_estrutura_xml_dps(
            None
        )


def test_b56_003_nome_da_raiz_invalido_bloqueado():
    raiz = montar_xml_dps(
        _dados_completos()
    )

    raiz.tag = etree.QName(
        NAMESPACE_NFSE,
        "NFSe",
    )

    with pytest.raises(
        EstruturaXmlDpsInvalida,
        match="raiz da DPS deve ser DPS",
    ):
        validar_estrutura_xml_dps(
            raiz
        )


def test_b56_004_namespace_da_raiz_invalido_bloqueado():
    raiz = montar_xml_dps(
        _dados_completos()
    )

    raiz.tag = etree.QName(
        "urn:jsp:teste",
        "DPS",
    )

    with pytest.raises(
        EstruturaXmlDpsInvalida,
        match="Namespace da raiz DPS invalido",
    ):
        validar_estrutura_xml_dps(
            raiz
        )


def test_b56_005_versao_invalida_bloqueada():
    raiz = montar_xml_dps(
        _dados_completos()
    )

    raiz.set(
        "versao",
        "9.99",
    )

    with pytest.raises(
        EstruturaXmlDpsInvalida,
        match="Versao estrutural da DPS invalida",
    ):
        validar_estrutura_xml_dps(
            raiz
        )


def test_b56_006_inf_dps_ausente_bloqueado():
    raiz = montar_xml_dps(
        _dados_completos()
    )

    raiz.remove(
        raiz[0]
    )

    with pytest.raises(
        EstruturaXmlDpsInvalida,
        match="exatamente um infDPS",
    ):
        validar_estrutura_xml_dps(
            raiz
        )


def test_b56_007_inf_dps_duplicado_bloqueado():
    raiz = montar_xml_dps(
        _dados_completos()
    )

    raiz.append(
        deepcopy(raiz[0])
    )

    with pytest.raises(
        EstruturaXmlDpsInvalida,
        match="exatamente um infDPS",
    ):
        validar_estrutura_xml_dps(
            raiz
        )


def test_b56_008_id_inf_dps_ausente_bloqueado():
    raiz = montar_xml_dps(
        _dados_completos()
    )

    raiz[0].set(
        "Id",
        " ",
    )

    with pytest.raises(
        EstruturaXmlDpsInvalida,
        match="Id de infDPS obrigatorio",
    ):
        validar_estrutura_xml_dps(
            raiz
        )


def test_b56_009_ordem_identificacao_invalida_bloqueada():
    raiz = montar_xml_dps(
        _dados_completos()
    )

    inf_dps = raiz[0]

    primeiro = inf_dps[0]

    inf_dps.remove(
        primeiro
    )

    inf_dps.insert(
        1,
        primeiro,
    )

    with pytest.raises(
        EstruturaXmlDpsInvalida,
        match="Ordem estrutural da identificacao",
    ):
        validar_estrutura_xml_dps(
            raiz
        )


def test_b56_010_grupo_prest_obrigatorio():
    raiz = montar_xml_dps(
        _dados_completos()
    )

    inf_dps = raiz[0]

    prest = _filho_direto(
        inf_dps,
        "prest",
    )

    inf_dps.remove(
        prest
    )

    with pytest.raises(
        EstruturaXmlDpsInvalida,
        match="Grupo prest deve ocorrer exatamente uma vez",
    ):
        validar_estrutura_xml_dps(
            raiz
        )


def test_b56_011_grupo_prest_duplicado_bloqueado():
    raiz = montar_xml_dps(
        _dados_completos()
    )

    inf_dps = raiz[0]

    prest = _filho_direto(
        inf_dps,
        "prest",
    )

    inf_dps.append(
        deepcopy(prest)
    )

    with pytest.raises(
        EstruturaXmlDpsInvalida,
        match="Grupo prest deve ocorrer exatamente uma vez",
    ):
        validar_estrutura_xml_dps(
            raiz
        )


def test_b56_012_ordem_grupos_principais_invalida():
    raiz = montar_xml_dps(
        _dados_completos()
    )

    inf_dps = raiz[0]

    prest = _filho_direto(
        inf_dps,
        "prest",
    )

    inf_dps.remove(
        prest
    )

    serv = _filho_direto(
        inf_dps,
        "serv",
    )

    indice_serv = list(
        inf_dps
    ).index(serv)

    inf_dps.insert(
        indice_serv + 1,
        prest,
    )

    with pytest.raises(
        EstruturaXmlDpsInvalida,
        match="Ordem dos grupos principais",
    ):
        validar_estrutura_xml_dps(
            raiz
        )


def test_b56_013_serializer_executa_validacao_estrutural(
    monkeypatch,
):
    chamadas = []

    original = (
        serializer.validar_estrutura_xml_dps
    )

    def espiao(raiz):
        chamadas.append(
            raiz
        )

        return original(
            raiz
        )

    monkeypatch.setattr(
        serializer,
        "validar_estrutura_xml_dps",
        espiao,
    )

    xml = serializer.montar_xml_dps_serializado(
        _dados_completos()
    )

    assert isinstance(
        xml,
        bytes,
    )

    assert len(chamadas) == 1

    raiz_validada = chamadas[0]

    assert (
        etree.QName(
            raiz_validada
        ).localname
        == "DPS"
    )

    assert (
        raiz_validada.get("versao")
        == VERSAO_DPS
    )
