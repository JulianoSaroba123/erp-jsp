"""D24F02-B5.4D - tributacao municipal ISSQN da DPS."""

import importlib.util
from pathlib import Path

import pytest
from lxml import etree

from app.fiscal.providers.sefin_nacional_dps import (
    DpsCanonicaInvalida,
    montar_dps_canonica,
    montar_totais_tributos_canonico,
)
from app.fiscal.xml.dps_serializer import (
    SerializacaoDpsInvalida,
    montar_xml_dps,
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


def _dados_base():
    arquivo = Path(__file__).with_name(
        "sefin_nacional_dps_b54c_test.py"
    )

    spec = importlib.util.spec_from_file_location(
        "_b54c_para_b54d",
        arquivo,
    )

    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    return modulo._dados_base()


def _dados_provider_base():
    arquivo = Path(__file__).with_name(
        "sefin_nacional_dps_b54a_test.py"
    )

    spec = importlib.util.spec_from_file_location(
        "_b54a_provider_para_b54d",
        arquivo,
    )

    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    return modulo._dados_provider_base()


def _valores(dados):
    raiz = montar_xml_dps(dados)
    inf_dps = raiz[0]

    return _filho(
        inf_dps,
        "valores",
    )


def _com_tributacao(dados=None):
    dados = dados or _dados_base()

    dados["iss"] = {
        "tributacao_issqn": "1",
        "tipo_retencao": "1",
        "aliquota": "3.50",
    }

    dados["totais_tributos"] = {
        "indicador": "0",
    }

    return dados


def test_b54d_001_marcos_anteriores_continuam_sem_trib():
    valores = _valores(
        _dados_base()
    )

    assert "trib" not in [
        _localname(elemento)
        for elemento in valores
    ]


def test_b54d_002_serializa_trib_mun_e_tot_trib():
    valores = _valores(
        _com_tributacao()
    )

    trib = _filho(
        valores,
        "trib",
    )

    assert [
        _localname(elemento)
        for elemento in trib
    ] == [
        "tribMun",
        "totTrib",
    ]


def test_b54d_003_serializa_issqn_retencao_e_aliquota():
    valores = _valores(
        _com_tributacao()
    )

    trib = _filho(
        valores,
        "trib",
    )

    trib_mun = _filho(
        trib,
        "tribMun",
    )

    assert [
        _localname(elemento)
        for elemento in trib_mun
    ] == [
        "tribISSQN",
        "tpRetISSQN",
        "pAliq",
    ]

    assert _filho(
        trib_mun,
        "tribISSQN",
    ).text == "1"

    assert _filho(
        trib_mun,
        "tpRetISSQN",
    ).text == "1"

    assert _filho(
        trib_mun,
        "pAliq",
    ).text == "3.50"


def test_b54d_004_aliquota_opcional_nao_e_fabricada():
    dados = _com_tributacao()

    dados["iss"]["aliquota"] = None

    valores = _valores(dados)

    trib_mun = _filho(
        _filho(
            valores,
            "trib",
        ),
        "tribMun",
    )

    assert [
        _localname(elemento)
        for elemento in trib_mun
    ] == [
        "tribISSQN",
        "tpRetISSQN",
    ]


def test_b54d_005_serializa_ind_tot_trib_zero():
    valores = _valores(
        _com_tributacao()
    )

    tot_trib = _filho(
        _filho(
            valores,
            "trib",
        ),
        "totTrib",
    )

    assert [
        _localname(elemento)
        for elemento in tot_trib
    ] == [
        "indTotTrib",
    ]

    assert tot_trib[0].text == "0"


def test_b54d_006_rejeita_iss_sem_totais_tributos():
    dados = _dados_base()

    dados["iss"] = {
        "tributacao_issqn": "1",
        "tipo_retencao": "1",
        "aliquota": "3.50",
    }

    with pytest.raises(
        SerializacaoDpsInvalida,
        match="totais_tributos",
    ):
        montar_xml_dps(dados)


def test_b54d_007_rejeita_totais_sem_iss():
    dados = _dados_base()

    dados["totais_tributos"] = {
        "indicador": "0",
    }

    with pytest.raises(
        SerializacaoDpsInvalida,
        match="ISS canonico",
    ):
        montar_xml_dps(dados)


def test_b54d_008_contrato_canonico_total_tributos():
    assert montar_totais_tributos_canonico(
        {
            "indicador": "0",
        }
    ) == {
        "indicador": "0",
    }


def test_b54d_009_rejeita_indicador_canonico_nao_suportado():
    with pytest.raises(
        DpsCanonicaInvalida,
        match="deve ser 0",
    ):
        montar_totais_tributos_canonico(
            {
                "indicador": "1",
            }
        )


def test_b54d_010_provider_integra_total_e_xml():
    dados = _dados_provider_base()

    # O XML TCServ exige o municipio onde o servico foi
    # efetivamente prestado. Nao usar municipio de incidencia
    # como fallback porque os conceitos fiscais sao distintos.
    dados["servico"]["municipio_prestacao_ibge"] = "3550308"

    dados["iss"] = {
        "tributacao_issqn": "1",
        "tipo_retencao": "1",
        "aliquota": "3.50",
    }

    dados["totais_tributos"] = {
        "indicador": "0",
    }

    dps = montar_dps_canonica(
        **dados
    )

    assert dps["totais_tributos"] == {
        "indicador": "0",
    }

    valores = _valores(dps)

    trib = _filho(
        valores,
        "trib",
    )

    trib_mun = _filho(
        trib,
        "tribMun",
    )

    tot_trib = _filho(
        trib,
        "totTrib",
    )

    assert _filho(
        trib_mun,
        "pAliq",
    ).text == "3.50"

    assert _filho(
        tot_trib,
        "indTotTrib",
    ).text == "0"


def test_b54d_011_provider_nao_fabrica_totais_tributos():
    dados = _dados_provider_base()

    dps = montar_dps_canonica(
        **dados
    )

    assert "totais_tributos" not in dps
