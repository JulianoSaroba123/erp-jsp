"""D24F02-B6-A5 - validacao XSD local da DPS."""

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path

import pytest

from app.fiscal.xsd import obter_caminho_xsd_dps
from app.fiscal.xml.dps_serializer import (
    montar_xml_dps_serializado,
)
from app.fiscal.xml.dps_xsd_validator import (
    STATUS_INVALIDO,
    STATUS_VALIDO_COMPATIBILIDADE_SERIE,
    ValidacaoXsdDpsInvalida,
    validar_xml_dps_xsd,
)


ROOT = Path(__file__).resolve().parents[2]

XSD_DPS = obter_caminho_xsd_dps()

XSD_TIPOS_SIMPLES = (
    XSD_DPS.parent
    / "tiposSimples_v1.01.xsd"
)


def _dados_b55():
    arquivo = Path(__file__).with_name(
        "sefin_nacional_dps_b55_test.py"
    )

    spec = importlib.util.spec_from_file_location(
        "_b55_para_b6",
        arquivo,
    )

    modulo = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        modulo
    )

    return deepcopy(
        modulo._dados_completos()
    )


def _dados_completos_xsd():
    dados = _dados_b55()

    dados["identificacao"]["serie"] = "1"

    dados["iss"] = {
        "tributacao_issqn": "1",
        "tipo_retencao": "1",
        "aliquota": "3.50",
    }

    dados["totais_tributos"] = {
        "indicador": "0",
    }

    return dados


def test_b6a5_001_xsd_original_rejeita_pattern_serie():
    xml = montar_xml_dps_serializado(
        _dados_completos_xsd()
    )

    resultado = validar_xml_dps_xsd(
        xml,
        XSD_DPS,
        permitir_compatibilidade_serie=False,
    )

    assert resultado.valido is False
    assert resultado.status == STATUS_INVALIDO
    assert resultado.compatibilidade_aplicada is False

    assert any(
        "serie" in erro
        and "SCHEMAV_CVC_PATTERN_VALID" in erro
        for erro in resultado.erros
    )


def test_b6a5_002_compatibilidade_valida_dps_completa():
    xml = montar_xml_dps_serializado(
        _dados_completos_xsd()
    )

    resultado = validar_xml_dps_xsd(
        xml,
        XSD_DPS,
    )

    assert resultado.valido is True

    assert (
        resultado.status
        == STATUS_VALIDO_COMPATIBILIDADE_SERIE
    )

    assert resultado.compatibilidade_aplicada is True
    assert resultado.erros == ()


def test_b6a5_003_nao_mascara_erro_fiscal_real():
    dados = _dados_b55()

    dados["identificacao"]["serie"] = "1"

    xml = montar_xml_dps_serializado(
        dados
    )

    resultado = validar_xml_dps_xsd(
        xml,
        XSD_DPS,
    )

    assert resultado.valido is False
    assert resultado.status == STATUS_INVALIDO

    assert (
        resultado.compatibilidade_aplicada
        is False
    )

    assert any(
        (
            "Missing child element" in erro
            or "}valores" in erro
        )
        for erro in resultado.erros
    )


def test_b6a5_004_nao_altera_xsd_original():
    antes = hashlib.sha256(
        XSD_TIPOS_SIMPLES.read_bytes()
    ).hexdigest()

    xml = montar_xml_dps_serializado(
        _dados_completos_xsd()
    )

    resultado = validar_xml_dps_xsd(
        xml,
        XSD_DPS,
    )

    depois = hashlib.sha256(
        XSD_TIPOS_SIMPLES.read_bytes()
    ).hexdigest()

    assert resultado.valido is True
    assert antes == depois


def test_b6a5_005_rejeita_caminho_xsd_inexistente():
    xml = montar_xml_dps_serializado(
        _dados_completos_xsd()
    )

    with pytest.raises(
        ValidacaoXsdDpsInvalida,
        match="XSD DPS nao encontrado",
    ):
        validar_xml_dps_xsd(
            xml,
            ROOT / "nao_existe.xsd",
        )
