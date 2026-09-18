from types import SimpleNamespace

import pytest

from app.fiscal import nfse_service as service


def _objetos_base():
    documento = SimpleNamespace(
        numero_rps=77,
        serie_rps="1",
    )

    ordem_servico = SimpleNamespace(
        id=10,
    )

    configuracao_fiscal = SimpleNamespace(
        id=1,
        proximo_rps=321,
    )

    configuracao_institucional = SimpleNamespace(
        id=99,
    )

    return (
        documento,
        ordem_servico,
        configuracao_fiscal,
        configuracao_institucional,
    )


def _executar(
    monkeypatch,
    *,
    valido=True,
    erros=(),
):
    (
        documento,
        ordem_servico,
        configuracao_fiscal,
        configuracao_institucional,
    ) = _objetos_base()

    payload = {
        "provider": "SEFIN_NACIONAL",
        "conteudo": None,
    }

    eventos = []

    monkeypatch.setattr(
        service,
        "preparar_payload_nfse",
        lambda **kwargs: (
            eventos.append("payload") or payload
        ),
    )

    monkeypatch.setattr(
        service,
        "montar_dps_canonica_da_os",
        lambda **kwargs: (
            eventos.append("dps") or {"dps": "canonica"}
        ),
    )

    monkeypatch.setattr(
        service,
        "montar_xml_dps_serializado",
        lambda dps: (
            eventos.append("xml")
            or b"<DPS>TESTE</DPS>"
        ),
    )

    monkeypatch.setattr(
        service,
        "obter_caminho_xsd_dps",
        lambda versao: (
            eventos.append("xsd")
            or "DPS_v1.01.xsd"
        ),
    )

    monkeypatch.setattr(
        service,
        "validar_xml_dps_xsd",
        lambda xml, caminho: (
            eventos.append("validacao")
            or SimpleNamespace(
                valido=valido,
                erros=erros,
            )
        ),
    )

    resultado = service.preparar_payload_nfse_com_dps(
        documento=documento,
        ordem_servico=ordem_servico,
        configuracao_fiscal=configuracao_fiscal,
        configuracao_institucional=configuracao_institucional,
        versao_layout="1.01",
        tipo_emitente="1",
        municipio_incidencia_ibge="3554508",
        iss={
            "tributacao_issqn": "1",
            "tipo_retencao": "1",
        },
        totais_tributos={
            "indicador": "0",
        },
    )

    return (
        resultado,
        payload,
        eventos,
        documento,
        configuracao_fiscal,
    )


def test_b7a3_001_publica_xml_somente_apos_xsd_valido(
    monkeypatch,
):
    resultado, payload, eventos, _, _ = _executar(
        monkeypatch
    )

    assert resultado is payload
    assert payload["conteudo"] == b"<DPS>TESTE</DPS>"

    assert eventos == [
        "payload",
        "dps",
        "xml",
        "xsd",
        "validacao",
    ]


def test_b7a3_002_xsd_invalido_nao_publica_conteudo(
    monkeypatch,
):
    payload = {
        "provider": "SEFIN_NACIONAL",
        "conteudo": None,
    }

    monkeypatch.setattr(
        service,
        "preparar_payload_nfse",
        lambda **kwargs: payload,
    )

    monkeypatch.setattr(
        service,
        "montar_dps_canonica_da_os",
        lambda **kwargs: {"dps": "canonica"},
    )

    monkeypatch.setattr(
        service,
        "montar_xml_dps_serializado",
        lambda dps: b"<DPS>INVALIDA</DPS>",
    )

    monkeypatch.setattr(
        service,
        "obter_caminho_xsd_dps",
        lambda versao: "DPS_v1.01.xsd",
    )

    monkeypatch.setattr(
        service,
        "validar_xml_dps_xsd",
        lambda xml, caminho: SimpleNamespace(
            valido=False,
            erros=("falha-xsd-controlada",),
        ),
    )

    (
        documento,
        ordem_servico,
        configuracao_fiscal,
        configuracao_institucional,
    ) = _objetos_base()

    with pytest.raises(
        service.PreparacaoNfseInvalida,
        match="invalido perante o XSD",
    ):
        service.preparar_payload_nfse_com_dps(
            documento=documento,
            ordem_servico=ordem_servico,
            configuracao_fiscal=configuracao_fiscal,
            configuracao_institucional=configuracao_institucional,
            versao_layout="1.01",
            tipo_emitente="1",
            municipio_incidencia_ibge="3554508",
            iss={
                "tributacao_issqn": "1",
                "tipo_retencao": "1",
            },
            totais_tributos={
                "indicador": "0",
            },
        )

    assert payload["conteudo"] is None


def test_b7a3_003_nao_consume_rps(
    monkeypatch,
):
    (
        resultado,
        _,
        _,
        documento,
        configuracao_fiscal,
    ) = _executar(monkeypatch)

    assert resultado["conteudo"] is not None
    assert documento.numero_rps == 77
    assert configuracao_fiscal.proximo_rps == 321
