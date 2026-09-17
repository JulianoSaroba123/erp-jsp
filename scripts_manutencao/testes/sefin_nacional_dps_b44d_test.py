"""D24F02-B4.4D - homologacao integrada da DPS canonica completa."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

from app.fiscal.providers.sefin_nacional_dps import montar_dps_canonica


def _dados_base():
    arquivo_b42 = Path(__file__).with_name(
        "sefin_nacional_dps_b42_test.py"
    )

    spec = importlib.util.spec_from_file_location(
        "_sefin_nacional_dps_b42_para_b44d",
        arquivo_b42,
    )

    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    return modulo._dados_base()


def test_b44d_001_monta_dps_canonica_completa():
    dados = _dados_base()

    configuracao = SimpleNamespace(
        id=77,
        cnpj="12.345.678/0001-95",
        razao_social="JSP ELETRICA INDUSTRIAL E SOLAR LTDA",
    )

    configuracao_fiscal = SimpleNamespace(
        configuracao_id=77,
        inscricao_municipal="123456",
        municipio_ibge="3554508",
        op_simp_nac="1",
        reg_ap_trib_sn="0",
        reg_esp_trib="0",
        aliquota_iss_padrao="3.50",
    )

    # Prestador legado propositalmente conflitante.
    # A fonte canonica deve prevalecer.
    dados["prestador"] = {
        "tipo_documento": "CNPJ",
        "documento": "99999999000199",
        "inscricao_municipal": "LEGADO",
        "municipio_ibge": "9999999",
        "nome": "PRESTADOR LEGADO",
        "regime_tributario": {
            "op_simp_nac": "9",
            "reg_ap_trib_sn": "9",
            "reg_esp_trib": "9",
        },
    }

    dados["configuracao"] = configuracao
    dados["configuracao_fiscal"] = configuracao_fiscal

    dados["servico"]["nbs"] = "123456789"

    dados["iss"] = {
        "tributacao_issqn": "1",
        "tipo_retencao": "1",
        # Sem aliquota propositalmente:
        # deve vir da ConfiguracaoFiscal.
    }

    dados["ibs_cbs"] = {
        "c_ind_op": "010101",
        "cst": "000",
        "c_class_trib": "000001",
        "campo_estranho": "nao deve escapar",
    }

    dps = montar_dps_canonica(**dados)

    # --------------------------------------------------------
    # PRESTADOR
    # --------------------------------------------------------
    assert dps["prestador"]["tipo_documento"] == "CNPJ"
    assert dps["prestador"]["documento"] == "12345678000195"
    assert dps["prestador"]["inscricao_municipal"] == "123456"
    assert dps["prestador"]["municipio_ibge"] == "3554508"
    assert dps["prestador"]["nome"] == (
        "JSP ELETRICA INDUSTRIAL E SOLAR LTDA"
    )

    assert dps["prestador"]["regime_tributario"] == {
        "op_simp_nac": "1",
        "reg_ap_trib_sn": "0",
        "reg_esp_trib": "0",
    }

    # --------------------------------------------------------
    # SERVICO
    # --------------------------------------------------------
    assert dps["servico"]["nbs"] == "123456789"
    assert dps["servico"]["codigo_lista_nacional"]
    assert dps["servico"]["descricao"]
    assert dps["servico"]["municipio_incidencia_ibge"]

    # --------------------------------------------------------
    # VALORES
    # --------------------------------------------------------
    assert dps["valores"]["valor_servicos"] is not None

    # --------------------------------------------------------
    # ISS
    # --------------------------------------------------------
    assert dps["iss"] == {
        "tributacao_issqn": "1",
        "tipo_retencao": "1",
        "aliquota": "3.50",
    }

    # --------------------------------------------------------
    # IBS/CBS
    # --------------------------------------------------------
    assert dps["ibs_cbs"] == {
        "c_ind_op": "010101",
        "cst": "000",
        "c_class_trib": "000001",
    }

    # --------------------------------------------------------
    # TOMADOR
    # --------------------------------------------------------
    # O contrato B4.2 ja define se ele esta presente ou ausente.
    # Aqui apenas comprovamos que o bloco integra a DPS.
    assert "tomador" in dps
