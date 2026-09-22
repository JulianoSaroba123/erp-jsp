from types import SimpleNamespace

import pytest

from app.fiscal.providers.sefin_nacional_dps import (
    DpsCanonicaInvalida,
    montar_prestador_canonico,
)


def _configuracao(**alteracoes):
    dados = {
        "id": 1,
        "cnpj": "12.345.678/0001-90",
        "razao_social": "JSP ELETRICA INDUSTRIAL LTDA",
    }
    dados.update(alteracoes)
    return SimpleNamespace(**dados)


def _configuracao_fiscal(**alteracoes):
    dados = {
        "configuracao_id": 1,
        "inscricao_municipal": "123456",
        "municipio_ibge": "3554508",
        "op_simp_nac": "1",
        "reg_ap_trib_sn": "1",
        "reg_esp_trib": "0",
    }
    dados.update(alteracoes)
    return SimpleNamespace(**dados)


def test_b43b_001_monta_prestador_canonico():
    prestador = montar_prestador_canonico(
        _configuracao(),
        _configuracao_fiscal(),
    )

    assert prestador == {
        "tipo_documento": "CNPJ",
        "documento": "12345678000190",
        "inscricao_municipal": "123456",
        "municipio_ibge": "3554508",
        "nome": "JSP ELETRICA INDUSTRIAL LTDA",
        "regime_tributario": {
            "op_simp_nac": "1",
            "reg_ap_trib_sn": "1",
            "reg_esp_trib": "0",
        },
    }


def test_b43b_002_exige_configuracao_institucional():
    with pytest.raises(
        DpsCanonicaInvalida,
        match="Configuracao institucional",
    ):
        montar_prestador_canonico(
            None,
            _configuracao_fiscal(),
        )


def test_b43b_003_exige_configuracao_fiscal():
    with pytest.raises(
        DpsCanonicaInvalida,
        match="Configuracao fiscal",
    ):
        montar_prestador_canonico(
            _configuracao(),
            None,
        )


def test_b43b_004_exige_id_institucional():
    with pytest.raises(
        DpsCanonicaInvalida,
        match="Identificador da configuracao institucional",
    ):
        montar_prestador_canonico(
            _configuracao(id=None),
            _configuracao_fiscal(),
        )


def test_b43b_005_exige_vinculo_fiscal():
    with pytest.raises(
        DpsCanonicaInvalida,
        match="Vinculo da configuracao fiscal",
    ):
        montar_prestador_canonico(
            _configuracao(),
            _configuracao_fiscal(configuracao_id=None),
        )


def test_b43b_006_bloqueia_configuracao_fiscal_de_outra_empresa():
    with pytest.raises(
        DpsCanonicaInvalida,
        match="nao pertence",
    ):
        montar_prestador_canonico(
            _configuracao(id=1),
            _configuracao_fiscal(configuracao_id=2),
        )


@pytest.mark.parametrize(
    "cnpj",
    [
        None,
        "",
        "123",
        "12.345.678/0001",
    ],
)
def test_b43b_007_exige_cnpj_com_14_digitos(cnpj):
    with pytest.raises(
        DpsCanonicaInvalida,
        match="14 digitos",
    ):
        montar_prestador_canonico(
            _configuracao(cnpj=cnpj),
            _configuracao_fiscal(),
        )


@pytest.mark.parametrize(
    "razao_social",
    [
        None,
        "",
        "   ",
    ],
)
def test_b43b_008_exige_razao_social(razao_social):
    with pytest.raises(
        DpsCanonicaInvalida,
        match="Razao social",
    ):
        montar_prestador_canonico(
            _configuracao(razao_social=razao_social),
            _configuracao_fiscal(),
        )


@pytest.mark.parametrize(
    "inscricao_municipal",
    [
        None,
        "",
        "   ",
    ],
)
def test_b43b_009_exige_inscricao_municipal(
    inscricao_municipal,
):
    with pytest.raises(
        DpsCanonicaInvalida,
        match="Inscricao municipal",
    ):
        montar_prestador_canonico(
            _configuracao(),
            _configuracao_fiscal(
                inscricao_municipal=inscricao_municipal,
            ),
        )


@pytest.mark.parametrize(
    "municipio_ibge",
    [
        None,
        "",
        "355450",
        "35545080",
        "35545A8",
    ],
)
def test_b43b_010_exige_municipio_ibge_valido(
    municipio_ibge,
):
    with pytest.raises(
        DpsCanonicaInvalida,
        match="7 digitos",
    ):
        montar_prestador_canonico(
            _configuracao(),
            _configuracao_fiscal(
                municipio_ibge=municipio_ibge,
            ),
        )


def test_b43b_011_preserva_regime_nacional_sem_fabricar_valores():
    prestador = montar_prestador_canonico(
        _configuracao(),
        _configuracao_fiscal(
            op_simp_nac=None,
            reg_ap_trib_sn=None,
            reg_esp_trib=None,
        ),
    )

    assert prestador["regime_tributario"] == {
        "op_simp_nac": None,
        "reg_ap_trib_sn": None,
        "reg_esp_trib": None,
    }


def test_b43b_012_ignora_regime_tributario_legado():
    fiscal = _configuracao_fiscal()
    fiscal.regime_tributario = "SIMPLES_NACIONAL"

    prestador = montar_prestador_canonico(
        _configuracao(),
        fiscal,
    )

    assert prestador["regime_tributario"] == {
        "op_simp_nac": "1",
        "reg_ap_trib_sn": "1",
        "reg_esp_trib": "0",
    }
