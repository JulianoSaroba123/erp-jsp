from datetime import datetime, timedelta, timezone

import pytest

from app.fiscal.providers.sefin_nacional_dps import (
    DpsCanonicaInvalida,
    montar_dps_canonica,
)


def _dados_base():
    return {
        "ambiente": "HOMOLOGACAO",
        "versao_layout": "1.01",
        "data_emissao": datetime(
            2026,
            9,
            16,
            15,
            0,
            0,
            tzinfo=timezone(
                timedelta(hours=-3)
            ),
        ),
        "versao_aplicativo": "ERP_JSP",
        "serie": "1",
        "numero_dps": "1",
        "competencia": "2026-09-16",
        "tipo_emitente": "1",
        "municipio_emissao_ibge": "3554508",
        "prestador": {
            "tipo_documento": "CNPJ",
            "documento": "12345678000199",
            "municipio_ibge": "3554508",
            "regime_tributario": {
                "op_simp_nac": "3",
                "reg_esp_trib": "0",
            },
        },
        "servico": {
            "codigo_lista_nacional": "010101",
            "codigo_tributacao_municipal": "123",
            "nbs": "123456789",
            "descricao": "Teste D24F02-B4.2",
            "municipio_incidencia_ibge": "3554508",
        },
        "valores": {
            "valor_servicos": "100.00",
        },
    }


def test_b42_001_ctribnac_valido():
    dados = _dados_base()

    dps = montar_dps_canonica(**dados)

    assert (
        dps["servico"]["codigo_lista_nacional"]
        == "010101"
    )


def test_b42_002_ctribnac_obrigatorio():
    dados = _dados_base()
    dados["servico"].pop("codigo_lista_nacional")

    with pytest.raises(
        DpsCanonicaInvalida,
        match="Campo obrigatorio ausente",
    ):
        montar_dps_canonica(**dados)


def test_b42_003_ctribnac_formato_invalido():
    dados = _dados_base()
    dados["servico"]["codigo_lista_nacional"] = "10101"

    with pytest.raises(
        DpsCanonicaInvalida,
        match="6 digitos",
    ):
        montar_dps_canonica(**dados)


def test_b42_004_ctribnac_preserva_zero():
    dados = _dados_base()
    dados["servico"]["codigo_lista_nacional"] = "010201"

    dps = montar_dps_canonica(**dados)

    assert (
        dps["servico"]["codigo_lista_nacional"]
        == "010201"
    )


def test_b42_005_ctribmun_opcional():
    dados = _dados_base()
    dados["servico"].pop(
        "codigo_tributacao_municipal"
    )

    dps = montar_dps_canonica(**dados)

    assert (
        dps["servico"]["codigo_tributacao_municipal"]
        is None
    )


def test_b42_006_ctribmun_valido():
    dados = _dados_base()
    dados["servico"][
        "codigo_tributacao_municipal"
    ] = "321"

    dps = montar_dps_canonica(**dados)

    assert (
        dps["servico"][
            "codigo_tributacao_municipal"
        ]
        == "321"
    )


def test_b42_007_ctribmun_tamanho_invalido():
    dados = _dados_base()
    dados["servico"][
        "codigo_tributacao_municipal"
    ] = "1234"

    with pytest.raises(
        DpsCanonicaInvalida,
        match="3 digitos",
    ):
        montar_dps_canonica(**dados)


def test_b42_008_ctribmun_nao_numerico():
    dados = _dados_base()
    dados["servico"][
        "codigo_tributacao_municipal"
    ] = "12A"

    with pytest.raises(
        DpsCanonicaInvalida,
        match="3 digitos",
    ):
        montar_dps_canonica(**dados)


def test_b42_009_nbs_e_ibscbs():
    dados = _dados_base()

    dps = montar_dps_canonica(**dados)

    assert dps["servico"]["nbs"] == "123456789"

    dados = _dados_base()
    dados["servico"].pop("nbs")

    dps = montar_dps_canonica(**dados)

    assert dps["servico"]["nbs"] is None

    dados = _dados_base()
    dados["servico"]["nbs"] = "12345678"

    with pytest.raises(
        DpsCanonicaInvalida,
        match="9 digitos",
    ):
        montar_dps_canonica(**dados)

    dados = _dados_base()
    dados["servico"].pop("nbs")
    dados["ibs_cbs"] = {
        "grupo_informado": True,
    }

    with pytest.raises(
        DpsCanonicaInvalida,
        match="IBS/CBS",
    ):
        montar_dps_canonica(**dados)
