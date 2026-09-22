from datetime import datetime
from types import SimpleNamespace

import pytest

from app.fiscal.providers.geisweb_tiete_erp_adapter import (
    AdaptacaoGeisWebErpInvalida,
    montar_lote_geisweb_da_os,
)
from app.fiscal.providers.geisweb_tiete_xml import (
    montar_xml_envio_lote_rps_serializado,
)
from app.fiscal.providers.geisweb_tiete_xsd import (
    validar_xml_envio_lote_rps,
)


def _documento():
    return SimpleNamespace(
        numero_rps=7,
        serie_rps="A",
    )


def _configuracao():
    return SimpleNamespace(
        id=10,
        cnpj="11.111.111/0001-91",
        razao_social="EMPRESA TESTE",
    )


def _configuracao_fiscal():
    return SimpleNamespace(
        configuracao_id=10,
        inscricao_municipal="14180",
        municipio_ibge="3554508",
        aliquota_iss_padrao="2.00",
        codigo_servico_municipal="140601",
        codigo_lc116="1406",
    )


def _tomador():
    return {
        "tipo_documento": "CNPJ",
        "documento": "22.222.222/0001-91",
        "nome": "CLIENTE TESTE",
        "email": "cliente@example.com",
        "endereco": {
            "cep": "18530000",
            "logradouro": "RUA TESTE",
            "numero": "100",
            "complemento": "",
            "bairro": "CENTRO",
            "cidade": "TIETE",
            "uf": "SP",
            "pais": "BR",
        },
    }


def _servico():
    return {
        "codigo_lista_nacional": "1406",
        "codigo_tributacao_municipal": "140601",
        "nbs": "",
        "descricao": "SERVICO TESTE",
        "municipio_incidencia_ibge": "3554508",
        "municipio_prestacao_ibge": "3554508",
    }


def _valores():
    return {
        "valor_servicos": "100.00",
        "valor_recebido": None,
        "desconto_incondicionado": "0.00",
        "desconto_condicionado": "0.00",
        "deducoes": "0.00",
    }


def _ibs_cbs():
    return {
        "c_class_trib": "TESTE",
        "ibs": "0.00",
        "cbs": "0.00",
        "c_class_trib_reg": "TESTE",
    }


def _outros_impostos():
    return {
        "pis": "0.00",
        "cofins": "0.00",
        "csll": "0.00",
        "irrf": "0.00",
        "inss": "0.00",
    }


def _montar(**alteracoes):
    dados = {
        "documento": _documento(),
        "ordem_servico": SimpleNamespace(id=1),
        "configuracao": _configuracao(),
        "configuracao_fiscal": (
            _configuracao_fiscal()
        ),
        "numero_lote": "7",
        "data_emissao": datetime(
            2026,
            9,
            19,
            10,
            0,
            0,
        ),
        "tipo_lancamento": "1",
        "regime_geisweb": "1",
        "codigo_nacional": "140601",
        "base_calculo": "100.00",
        "ibs_cbs": _ibs_cbs(),
        "outros_impostos": (
            _outros_impostos()
        ),
        "tomador": _tomador(),
        "servico": _servico(),
        "valores": _valores(),
    }

    dados.update(alteracoes)

    return montar_lote_geisweb_da_os(
        **dados
    )


def test_adapter_monta_lote_geisweb():
    lote = _montar()

    assert lote["cnpj_cpf"] == (
        "11111111000191"
    )

    assert lote["numero_lote"] == "7"

    rps = lote["rps"][0]

    assert rps["numero_rps"] == "7"
    assert (
        rps["servico"]["codigo_servico"]
        == "140601"
    )
    assert (
        rps["servico"][
            "municipio_prestacao_servico"
        ]
        == "3554508"
    )
    assert (
        rps["prestador"][
            "inscricao_municipal"
        ]
        == "14180"
    )
    assert (
        rps["codigo_nacional"]
        == "140601"
    )


def test_adapter_gera_xml_valido_no_xsd():
    lote = _montar()

    xml = (
        montar_xml_envio_lote_rps_serializado(
            lote
        )
    )

    resultado = validar_xml_envio_lote_rps(
        xml
    )

    assert resultado.valido, resultado.erros


def test_adapter_nao_inventa_codigo_nacional():
    with pytest.raises(
        AdaptacaoGeisWebErpInvalida,
        match="codigo_nacional",
    ):
        _montar(
            codigo_nacional=None
        )


def test_adapter_nao_inventa_ibs_cbs():
    with pytest.raises(
        AdaptacaoGeisWebErpInvalida,
        match="ibs_cbs",
    ):
        _montar(
            ibs_cbs=None
        )


def test_adapter_valida_vinculo_configuracao():
    fiscal = _configuracao_fiscal()

    fiscal.configuracao_id = 99

    with pytest.raises(
        AdaptacaoGeisWebErpInvalida,
        match="nao pertence",
    ):
        _montar(
            configuracao_fiscal=fiscal
        )


def test_adapter_rejeita_municipio_fora_tiete():
    fiscal = _configuracao_fiscal()

    fiscal.municipio_ibge = "3550308"

    with pytest.raises(
        AdaptacaoGeisWebErpInvalida,
        match="3554508",
    ):
        _montar(
            configuracao_fiscal=fiscal
        )
