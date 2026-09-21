from types import SimpleNamespace

import pytest

from app.fiscal import nfse_service as service


def test_h1_001_preparacao_geisweb_encadeia_xml(
    monkeypatch,
):
    documento = SimpleNamespace()
    ordem = SimpleNamespace()
    config_fiscal = SimpleNamespace()
    config_institucional = SimpleNamespace()

    payload_base = {
        "provider": "GEISWEB_TIETE",
        "conteudo": None,
    }

    payload_xml = {
        **payload_base,
        "conteudo": b"<EnviaLoteRps/>",
    }

    monkeypatch.setattr(
        service,
        "preparar_payload_nfse",
        lambda **kwargs: payload_base,
    )

    capturado = {}

    def preparar_xml(**kwargs):
        capturado.update(kwargs)
        return payload_xml

    monkeypatch.setattr(
        service,
        "preparar_payload_geisweb_com_xml",
        preparar_xml,
    )

    resultado = service.preparar_payload_nfse_com_geisweb(
        documento=documento,
        ordem_servico=ordem,
        configuracao_fiscal=config_fiscal,
        configuracao_institucional=config_institucional,
        numero_lote="10",
        data_emissao="2026-09-21",
        tipo_lancamento="1",
        regime_geisweb="1",
        codigo_nacional="TESTE",
        base_calculo="100.00",
        ibs_cbs={},
        outros_impostos={},
    )

    assert resultado is payload_xml
    assert capturado["payload"] is payload_base
    assert capturado["documento"] is documento
    assert capturado["ordem_servico"] is ordem
    assert (
        capturado["configuracao_institucional"]
        is config_institucional
    )
    assert capturado["configuracao_fiscal"] is config_fiscal


def test_h1_002_preparacao_rejeita_outro_provider(
    monkeypatch,
):
    monkeypatch.setattr(
        service,
        "preparar_payload_nfse",
        lambda **kwargs: {
            "provider": "SEFIN_NACIONAL",
            "conteudo": None,
        },
    )

    with pytest.raises(
        service.PreparacaoNfseInvalida,
        match="outro provider",
    ):
        service.preparar_payload_nfse_com_geisweb(
            documento=SimpleNamespace(),
            ordem_servico=SimpleNamespace(),
            configuracao_fiscal=SimpleNamespace(),
            configuracao_institucional=SimpleNamespace(),
            numero_lote="1",
            data_emissao="2026-09-21",
            tipo_lancamento="1",
            regime_geisweb="1",
            codigo_nacional="TESTE",
            base_calculo="100.00",
            ibs_cbs={},
            outros_impostos={},
        )


def _documento():
    return SimpleNamespace(
        status="PREPARADA",
        mensagem_status=None,
    )


def test_h1_003_gate_aceita_xml_geisweb_valido(
    monkeypatch,
):
    monkeypatch.setattr(
        service,
        "validar_xml_envio_lote_rps",
        lambda xml: SimpleNamespace(
            valido=True,
            erros=(),
        ),
    )

    documento = _documento()

    resultado = service.preparar_nfse_para_envio(
        documento=documento,
        payload={
            "provider": "GEISWEB_TIETE",
            "conteudo": b"<EnviaLoteRps/>",
        },
    )

    assert resultado is documento
    assert documento.status == "PENDENTE_ENVIO"


def test_h1_004_gate_bloqueia_xml_geisweb_invalido(
    monkeypatch,
):
    monkeypatch.setattr(
        service,
        "validar_xml_envio_lote_rps",
        lambda xml: SimpleNamespace(
            valido=False,
            erros=("erro-xsd",),
        ),
    )

    documento = _documento()

    with pytest.raises(
        service.TransicaoStatusNfseInvalida,
        match="XML invalido perante o XSD",
    ):
        service.preparar_nfse_para_envio(
            documento=documento,
            payload={
                "provider": "GEISWEB_TIETE",
                "conteudo": b"<invalido/>",
            },
        )

    assert documento.status == "PREPARADA"
