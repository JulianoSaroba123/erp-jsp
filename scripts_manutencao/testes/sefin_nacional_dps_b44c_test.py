"""Testes D24F02-B4.4C - contrato canonico minimo IBS/CBS."""

import pytest

from app.fiscal.providers.sefin_nacional_dps import (
    DpsCanonicaInvalida,
    montar_ibs_cbs_canonico,
)


def test_b44c_001_grupo_ausente_retorna_vazio():
    assert montar_ibs_cbs_canonico() == {}


def test_b44c_002_monta_grupo_canonico():
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


def test_b44c_003_c_ind_op_obrigatorio():
    with pytest.raises(
        DpsCanonicaInvalida,
        match="ibs_cbs.c_ind_op",
    ):
        montar_ibs_cbs_canonico(
            {
                "cst": "000",
                "c_class_trib": "000001",
            }
        )


def test_b44c_004_rejeita_c_ind_op_invalido():
    with pytest.raises(
        DpsCanonicaInvalida,
        match="6 digitos",
    ):
        montar_ibs_cbs_canonico(
            {
                "c_ind_op": "101",
                "cst": "000",
                "c_class_trib": "000001",
            }
        )


def test_b44c_005_cst_obrigatorio():
    with pytest.raises(
        DpsCanonicaInvalida,
        match="ibs_cbs.cst",
    ):
        montar_ibs_cbs_canonico(
            {
                "c_ind_op": "010101",
                "c_class_trib": "000001",
            }
        )


def test_b44c_006_rejeita_cst_invalido():
    with pytest.raises(
        DpsCanonicaInvalida,
        match="3 digitos",
    ):
        montar_ibs_cbs_canonico(
            {
                "c_ind_op": "010101",
                "cst": "00",
                "c_class_trib": "000001",
            }
        )


def test_b44c_007_c_class_trib_obrigatorio():
    with pytest.raises(
        DpsCanonicaInvalida,
        match="ibs_cbs.c_class_trib",
    ):
        montar_ibs_cbs_canonico(
            {
                "c_ind_op": "010101",
                "cst": "000",
            }
        )


def test_b44c_008_rejeita_c_class_trib_invalido():
    with pytest.raises(
        DpsCanonicaInvalida,
        match="6 digitos",
    ):
        montar_ibs_cbs_canonico(
            {
                "c_ind_op": "010101",
                "cst": "000",
                "c_class_trib": "123",
            }
        )


def test_b44c_009_nao_preserva_campos_estranhos():
    resultado = montar_ibs_cbs_canonico(
        {
            "c_ind_op": "010101",
            "cst": "000",
            "c_class_trib": "000001",
            "grupo_informado": True,
            "qualquer_coisa": "nao deve escapar",
        }
    )

    assert resultado == {
        "c_ind_op": "010101",
        "cst": "000",
        "c_class_trib": "000001",
    }

def _dados_dps_base_b44c():
    import importlib.util
    from pathlib import Path

    arquivo_b42 = Path(__file__).with_name(
        "sefin_nacional_dps_b42_test.py"
    )

    spec = importlib.util.spec_from_file_location(
        "_sefin_nacional_dps_b42_para_b44c",
        arquivo_b42,
    )

    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    return modulo._dados_base()


def test_b44c_010_dps_integra_ibs_cbs_canonico():
    from app.fiscal.providers.sefin_nacional_dps import (
        montar_dps_canonica,
    )

    dados = _dados_dps_base_b44c()

    dados["servico"]["nbs"] = "123456789"

    dados["ibs_cbs"] = {
        "c_ind_op": "010101",
        "cst": "000",
        "c_class_trib": "000001",
        "campo_estranho": "nao deve escapar",
    }

    dps = montar_dps_canonica(**dados)

    assert dps["ibs_cbs"] == {
        "c_ind_op": "010101",
        "cst": "000",
        "c_class_trib": "000001",
    }


def test_b44c_011_dps_preserva_ibs_cbs_vazio():
    from app.fiscal.providers.sefin_nacional_dps import (
        montar_dps_canonica,
    )

    dados = _dados_dps_base_b44c()
    dados["ibs_cbs"] = None

    dps = montar_dps_canonica(**dados)

    assert dps["ibs_cbs"] == {}


def test_b44c_012_dps_rejeita_ibs_cbs_invalido():
    from app.fiscal.providers.sefin_nacional_dps import (
        montar_dps_canonica,
    )

    dados = _dados_dps_base_b44c()

    dados["servico"]["nbs"] = "123456789"

    dados["ibs_cbs"] = {
        "c_ind_op": "101",
        "cst": "000",
        "c_class_trib": "000001",
    }

    with pytest.raises(
        DpsCanonicaInvalida,
        match="6 digitos",
    ):
        montar_dps_canonica(**dados)
