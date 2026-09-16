"""Testes D24F02-B4.3C - integracao do prestador canonico com a DPS."""

import importlib.util
from pathlib import Path

import pytest

from app.fiscal.providers import sefin_nacional_dps as dps_mod


def _carregar_dados_base():
    """Reutiliza a fixture consolidada do B4.2 sem duplicar contrato da DPS."""
    arquivo_b42 = Path(__file__).with_name(
        "sefin_nacional_dps_b42_test.py"
    )

    spec = importlib.util.spec_from_file_location(
        "_sefin_nacional_dps_b42_base",
        arquivo_b42,
    )

    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    return modulo._dados_base()


def _prestador_canonico_teste():
    return {
        "tipo_documento": "CNPJ",
        "documento": "12345678000195",
        "inscricao_municipal": "987654",
        "municipio_ibge": "3554508",
        "nome": "EMPRESA CANONICA LTDA",
        "regime_tributario": {
            "op_simp_nac": "1",
            "reg_ap_trib_sn": "0",
            "reg_esp_trib": "0",
        },
    }


def test_b43c_001_dps_chama_adaptador_canonico(monkeypatch):
    dados = _carregar_dados_base()

    configuracao = object()
    configuracao_fiscal = object()

    chamadas = []

    def fake_montar_prestador_canonico(
        configuracao,
        configuracao_fiscal,
    ):
        chamadas.append(
            (
                configuracao,
                configuracao_fiscal,
            )
        )
        return _prestador_canonico_teste()

    monkeypatch.setattr(
        dps_mod,
        "montar_prestador_canonico",
        fake_montar_prestador_canonico,
    )

    dados["configuracao"] = configuracao
    dados["configuracao_fiscal"] = configuracao_fiscal

    dps_mod.montar_dps_canonica(**dados)

    assert chamadas == [
        (
            configuracao,
            configuracao_fiscal,
        )
    ]


def test_b43c_002_prestador_canonico_tem_prioridade_sobre_legado(
    monkeypatch,
):
    dados = _carregar_dados_base()

    configuracao = object()
    configuracao_fiscal = object()

    dados["prestador"] = {
        "tipo_documento": "CNPJ",
        "documento": "19131243000197",
        "inscricao_municipal": "LEGADO",
        "municipio_ibge": "9999999",
        "nome": "PRESTADOR LEGADO",
        "regime_tributario": {
            "op_simp_nac": "3",
            "reg_ap_trib_sn": "9",
            "reg_esp_trib": "99",
        },
    }

    monkeypatch.setattr(
        dps_mod,
        "montar_prestador_canonico",
        lambda configuracao, configuracao_fiscal:
            _prestador_canonico_teste(),
    )

    dados["configuracao"] = configuracao
    dados["configuracao_fiscal"] = configuracao_fiscal

    dps = dps_mod.montar_dps_canonica(**dados)

    assert dps["prestador"]["tipo_documento"] == "CNPJ"
    assert dps["prestador"]["documento"] == "12345678000195"
    assert dps["prestador"]["inscricao_municipal"] == "987654"
    assert dps["prestador"]["municipio_ibge"] == "3554508"
    assert dps["prestador"]["nome"] == "EMPRESA CANONICA LTDA"

    assert dps["prestador"]["regime_tributario"] == {
        "op_simp_nac": "1",
        "reg_ap_trib_sn": "0",
        "reg_esp_trib": "0",
    }


def test_b43c_003_sem_fontes_preserva_compatibilidade_b42():
    dados = _carregar_dados_base()

    dps = dps_mod.montar_dps_canonica(**dados)

    assert dps["prestador"] is not None
    assert dps["prestador"]["documento"]


def test_b43c_004_sem_prestador_e_sem_fontes_bloqueia():
    dados = _carregar_dados_base()

    dados.pop("prestador", None)

    with pytest.raises(
        dps_mod.DpsCanonicaInvalida,
        match="Prestador canonico ou configuracao fiscal",
    ):
        dps_mod.montar_dps_canonica(**dados)


def test_b43c_005_fonte_fiscal_parcial_nao_cai_no_legado():
    dados = _carregar_dados_base()

    dados["configuracao"] = object()
    dados["configuracao_fiscal"] = None

    with pytest.raises(
        dps_mod.DpsCanonicaInvalida,
        match="Configuracao fiscal do prestador nao informada",
    ):
        dps_mod.montar_dps_canonica(**dados)
