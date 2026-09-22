from datetime import datetime
from types import SimpleNamespace

import pytest

from app.fiscal.providers import obter_provider
from app.fiscal.providers.geisweb_tiete_preparacao import (
    PreparacaoLocalGeisWebInvalida,
    preparar_payload_geisweb_com_xml,
)
from app.fiscal.providers.geisweb_tiete_xsd import (
    validar_xml_envio_lote_rps,
)


def _documento():
    return SimpleNamespace(
        id=10,
        serie_rps="A",
        numero_rps=7,
    )


def _ordem():
    return SimpleNamespace(id=20)


def _institucional():
    return SimpleNamespace(
        id=30,
        cnpj="11.111.111/0001-91",
        razao_social="EMPRESA TESTE",
    )


def _fiscal():
    return SimpleNamespace(
        configuracao_id=30,
        provider="GEISWEB_TIETE",
        ambiente="HOMOLOGACAO",
        municipio_ibge="3554508",
        integracao_ativa=False,
        inscricao_municipal="14180",
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


def _payload():
    provider = obter_provider(
        "GEISWEB_TIETE"
    )

    return provider.preparar_payload(
        documento=_documento(),
        ordem_servico=_ordem(),
        configuracao=_fiscal(),
    )


def _preparar(payload=None):
    return preparar_payload_geisweb_com_xml(
        payload=payload or _payload(),
        documento=_documento(),
        ordem_servico=_ordem(),
        configuracao_institucional=_institucional(),
        configuracao_fiscal=_fiscal(),
        numero_lote="7",
        data_emissao=datetime(
            2026,
            9,
            19,
            12,
            0,
            0,
        ),
        tipo_lancamento="1",
        regime_geisweb="1",
        codigo_nacional="140601",
        base_calculo="100.00",
        ibs_cbs={
            "c_class_trib": "TESTE",
            "ibs": "0.00",
            "cbs": "0.00",
            "c_class_trib_reg": "TESTE",
        },
        outros_impostos={
            "pis": "0.00",
            "cofins": "0.00",
            "csll": "0.00",
            "irrf": "0.00",
            "inss": "0.00",
        },
        tomador=_tomador(),
        servico=_servico(),
        valores=_valores(),
    )


def test_publica_xml_no_payload():
    resultado = _preparar()

    assert isinstance(
        resultado["conteudo"],
        bytes,
    )

    assert b"EnviaLoteRps" in resultado["conteudo"]

    assert (
        resultado["validacao_xsd"]["valido"]
        is True
    )


def test_xml_publicado_valida_no_xsd():
    resultado = _preparar()

    validacao = validar_xml_envio_lote_rps(
        resultado["conteudo"]
    )

    assert validacao.valido, validacao.erros


def test_payload_original_nao_e_mutado():
    payload = _payload()

    resultado = _preparar(
        payload=payload
    )

    assert payload["conteudo"] is None
    assert resultado["conteudo"] is not None


def test_rejeita_payload_com_conteudo_preexistente():
    payload = _payload()
    payload["conteudo"] = b"<teste/>"

    with pytest.raises(
        PreparacaoLocalGeisWebInvalida,
        match="ja possui conteudo",
    ):
        _preparar(
            payload=payload
        )


def test_rejeita_provider_incorreto():
    payload = _payload()
    payload["provider"] = "SEFIN_NACIONAL"

    with pytest.raises(
        PreparacaoLocalGeisWebInvalida,
        match="GEISWEB_TIETE",
    ):
        _preparar(
            payload=payload
        )
