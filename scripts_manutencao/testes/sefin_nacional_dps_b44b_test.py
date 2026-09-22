"""Testes D24F02-B4.4B - contrato canonico do ISSQN."""

from types import SimpleNamespace

import pytest

from app.fiscal.providers.sefin_nacional_dps import (
    DpsCanonicaInvalida,
    montar_iss_canonico,
)


def test_b44b_001_iss_ausente_retorna_bloco_vazio():
    assert montar_iss_canonico() == {}


def test_b44b_002_monta_iss_canonico_completo():
    iss = montar_iss_canonico(
        {
            "tributacao_issqn": "1",
            "tipo_retencao": "1",
            "aliquota": "5",
        }
    )

    assert iss == {
        "tributacao_issqn": "1",
        "tipo_retencao": "1",
        "aliquota": "5.00",
    }


def test_b44b_003_normaliza_aliquota_com_virgula():
    iss = montar_iss_canonico(
        {
            "tributacao_issqn": "1",
            "tipo_retencao": "1",
            "aliquota": "4,25",
        }
    )

    assert iss["aliquota"] == "4.25"


def test_b44b_004_usa_aliquota_padrao_da_configuracao_fiscal():
    configuracao_fiscal = SimpleNamespace(
        aliquota_iss_padrao="3.50",
    )

    iss = montar_iss_canonico(
        {
            "tributacao_issqn": "1",
            "tipo_retencao": "1",
        },
        configuracao_fiscal=configuracao_fiscal,
    )

    assert iss["aliquota"] == "3.50"


def test_b44b_005_nao_fabrica_aliquota_sem_configuracao():
    iss = montar_iss_canonico(
        {
            "tributacao_issqn": "1",
            "tipo_retencao": "1",
        }
    )

    assert iss["aliquota"] is None


def test_b44b_006_tributacao_issqn_obrigatoria():
    with pytest.raises(
        DpsCanonicaInvalida,
        match="iss.tributacao_issqn",
    ):
        montar_iss_canonico(
            {
                "tipo_retencao": "1",
            }
        )


def test_b44b_007_rejeita_tributacao_issqn_invalida():
    with pytest.raises(
        DpsCanonicaInvalida,
        match="codigo entre 1 e 4",
    ):
        montar_iss_canonico(
            {
                "tributacao_issqn": "9",
                "tipo_retencao": "1",
            }
        )


def test_b44b_008_tipo_retencao_obrigatorio():
    with pytest.raises(
        DpsCanonicaInvalida,
        match="iss.tipo_retencao",
    ):
        montar_iss_canonico(
            {
                "tributacao_issqn": "1",
            }
        )


def test_b44b_009_rejeita_tipo_retencao_invalido():
    with pytest.raises(
        DpsCanonicaInvalida,
        match="codigo entre 1 e 3",
    ):
        montar_iss_canonico(
            {
                "tributacao_issqn": "1",
                "tipo_retencao": "7",
            }
        )


def test_b44b_010_rejeita_aliquota_nao_numerica():
    with pytest.raises(
        DpsCanonicaInvalida,
        match="Aliquota do ISSQN invalida",
    ):
        montar_iss_canonico(
            {
                "tributacao_issqn": "1",
                "tipo_retencao": "1",
                "aliquota": "abc",
            }
        )


def test_b44b_011_rejeita_aliquota_fora_da_faixa():
    with pytest.raises(
        DpsCanonicaInvalida,
        match="entre 0 e 100",
    ):
        montar_iss_canonico(
            {
                "tributacao_issqn": "1",
                "tipo_retencao": "1",
                "aliquota": "101",
            }
        )

def _dados_dps_base():
    import importlib.util
    from pathlib import Path

    arquivo_b42 = Path(__file__).with_name(
        "sefin_nacional_dps_b42_test.py"
    )

    spec = importlib.util.spec_from_file_location(
        "_sefin_nacional_dps_b42_para_b44b",
        arquivo_b42,
    )

    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    return modulo._dados_base()


def test_b44b_012_dps_integra_iss_canonico():
    from app.fiscal.providers.sefin_nacional_dps import (
        montar_dps_canonica,
    )

    dados = _dados_dps_base()
    dados["iss"] = {
        "tributacao_issqn": "1",
        "tipo_retencao": "1",
        "aliquota": "5",
    }

    dps = montar_dps_canonica(**dados)

    assert dps["iss"] == {
        "tributacao_issqn": "1",
        "tipo_retencao": "1",
        "aliquota": "5.00",
    }


def test_b44b_013_dps_preserva_iss_vazio():
    from app.fiscal.providers.sefin_nacional_dps import (
        montar_dps_canonica,
    )

    dados = _dados_dps_base()

    dps = montar_dps_canonica(**dados)

    assert dps["iss"] == {}


def test_b44b_014_dps_usa_aliquota_fiscal_padrao(monkeypatch):
    from types import SimpleNamespace

    from app.fiscal.providers import sefin_nacional_dps as dps_mod

    dados = _dados_dps_base()
    prestador_base = dados["prestador"]

    dados["iss"] = {
        "tributacao_issqn": "1",
        "tipo_retencao": "1",
    }

    dados["configuracao"] = object()
    dados["configuracao_fiscal"] = SimpleNamespace(
        aliquota_iss_padrao="3.75",
    )

    monkeypatch.setattr(
        dps_mod,
        "montar_prestador_canonico",
        lambda configuracao, configuracao_fiscal: prestador_base,
    )

    dps = dps_mod.montar_dps_canonica(**dados)

    assert dps["iss"]["aliquota"] == "3.75"
