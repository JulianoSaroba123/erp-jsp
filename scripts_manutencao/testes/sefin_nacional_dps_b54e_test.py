from pathlib import Path
import runpy

import pytest
from lxml import etree

from app.fiscal.providers.sefin_nacional_dps import (
    DpsCanonicaInvalida,
    montar_dps_canonica,
    montar_ibs_cbs_canonico,
)
from app.fiscal.xml.dps_serializer import (
    SerializacaoDpsInvalida,
    montar_xml_dps,
)


def _helper(nome_arquivo, nome_funcao):
    caminho = Path(__file__).with_name(nome_arquivo)
    namespace = runpy.run_path(str(caminho))
    return namespace[nome_funcao]()


def _dados_base():
    return _helper(
        "sefin_nacional_dps_b54d_test.py",
        "_dados_base",
    )


def _dados_provider_base():
    return _helper(
        "sefin_nacional_dps_b54a_test.py",
        "_dados_provider_base",
    )


def _localname(elemento):
    return etree.QName(elemento).localname


def _filho(pai, nome):
    for elemento in pai:
        if _localname(elemento) == nome:
            return elemento

    raise AssertionError(
        f"Elemento XML nao encontrado: {nome}"
    )


def _ibs():
    return {
        "fin_nfse": "0",
        "ind_final": None,
        "c_ind_op": "010101",
        "ind_dest": "0",
        "cst": "000",
        "c_class_trib": "000001",
    }


def _inf_dps(dados):
    return montar_xml_dps(dados)[0]


def test_b54e_001_ausencia_nao_cria_ibscbs():
    inf_dps = _inf_dps(_dados_base())

    assert "IBSCBS" not in [
        _localname(x)
        for x in inf_dps
    ]


def test_b54e_002_ordem_minima_ibscbs():
    dados = _dados_base()
    dados["ibs_cbs"] = _ibs()

    ibs = _filho(
        _inf_dps(dados),
        "IBSCBS",
    )

    assert [
        _localname(x)
        for x in ibs
    ] == [
        "finNFSe",
        "cIndOp",
        "indDest",
        "valores",
    ]


def test_b54e_003_estrutura_tributaria():
    dados = _dados_base()
    dados["ibs_cbs"] = _ibs()

    ibs = _filho(
        _inf_dps(dados),
        "IBSCBS",
    )

    valores = _filho(
        ibs,
        "valores",
    )

    trib = _filho(
        valores,
        "trib",
    )

    g_ibs = _filho(
        trib,
        "gIBSCBS",
    )

    assert [
        _localname(x)
        for x in g_ibs
    ] == [
        "CST",
        "cClassTrib",
    ]


def test_b54e_004_valores_cst_classificacao():
    dados = _dados_base()
    dados["ibs_cbs"] = _ibs()

    ibs = _filho(
        _inf_dps(dados),
        "IBSCBS",
    )

    g_ibs = _filho(
        _filho(
            _filho(
                ibs,
                "valores",
            ),
            "trib",
        ),
        "gIBSCBS",
    )

    assert _filho(
        g_ibs,
        "CST",
    ).text == "000"

    assert _filho(
        g_ibs,
        "cClassTrib",
    ).text == "000001"


def test_b54e_005_ind_final_respeita_ordem_xsd():
    dados = _dados_base()
    dados["ibs_cbs"] = _ibs()
    dados["ibs_cbs"]["ind_final"] = "1"

    ibs = _filho(
        _inf_dps(dados),
        "IBSCBS",
    )

    assert [
        _localname(x)
        for x in ibs
    ] == [
        "finNFSe",
        "indFinal",
        "cIndOp",
        "indDest",
        "valores",
    ]


@pytest.mark.parametrize(
    "campo",
    [
        "fin_nfse",
        "ind_dest",
    ],
)
def test_b54e_006_serializer_exige_campos_obrigatorios(campo):
    dados = _dados_base()
    dados["ibs_cbs"] = _ibs()
    dados["ibs_cbs"].pop(campo)

    with pytest.raises(
        SerializacaoDpsInvalida,
        match=campo,
    ):
        montar_xml_dps(dados)


def test_b54e_007_provider_contrato_completo():
    resultado = montar_ibs_cbs_canonico(
        {
            "fin_nfse": "0",
            "ind_final": "1",
            "c_ind_op": "010101",
            "ind_dest": "0",
            "cst": "000",
            "c_class_trib": "000001",
        }
    )

    assert resultado == {
        "fin_nfse": "0",
        "ind_final": "1",
        "c_ind_op": "010101",
        "ind_dest": "0",
        "cst": "000",
        "c_class_trib": "000001",
    }


@pytest.mark.parametrize(
    "alteracao,mensagem",
    [
        (
            {"fin_nfse": "1"},
            "deve ser 0",
        ),
        (
            {"ind_dest": "9"},
            "deve ser 0 ou 1",
        ),
        (
            {"ind_final": "9"},
            "consumidor final",
        ),
    ],
)
def test_b54e_008_provider_rejeita_indicadores_invalidos(
    alteracao,
    mensagem,
):
    dados = _ibs()
    dados.update(alteracao)

    with pytest.raises(
        DpsCanonicaInvalida,
        match=mensagem,
    ):
        montar_ibs_cbs_canonico(dados)


def test_b54e_009_preserva_contrato_legado_b44c():
    resultado = montar_ibs_cbs_canonico(
        {
            "c_ind_op": "010101",
            "cst": "000",
            "c_class_trib": "000001",
        }
    )

    assert resultado == {
        "c_ind_op": "010101",
        "cst": "000",
        "c_class_trib": "000001",
    }


def test_b54e_010_provider_ate_xml():
    dados = _dados_provider_base()

    dados["servico"][
        "municipio_prestacao_ibge"
    ] = "3550308"

    dados["iss"] = {
        "tributacao_issqn": "1",
        "tipo_retencao": "1",
        "aliquota": "3.50",
    }

    dados["totais_tributos"] = {
        "indicador": "0",
    }

    dados["ibs_cbs"] = {
        "fin_nfse": "0",
        "c_ind_op": "010101",
        "ind_dest": "0",
        "cst": "000",
        "c_class_trib": "000001",
    }

    dps = montar_dps_canonica(
        **dados
    )

    inf_dps = _inf_dps(dps)

    assert [
        _localname(x)
        for x in inf_dps
    ][-2:] == [
        "valores",
        "IBSCBS",
    ]

    ibs = _filho(
        inf_dps,
        "IBSCBS",
    )

    assert _filho(
        ibs,
        "finNFSe",
    ).text == "0"

    assert _filho(
        ibs,
        "cIndOp",
    ).text == "010101"

    assert _filho(
        ibs,
        "indDest",
    ).text == "0"
