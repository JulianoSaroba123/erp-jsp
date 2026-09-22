from types import SimpleNamespace

import pytest

from app.fiscal import nfse_service as service


def _documento(**alteracoes):
    dados = {
        "id": 10,
        "status": "RASCUNHO",
        "mensagem_status": None,
        "serie_rps": None,
        "numero_rps": None,
        "pode_ser_editada": True,
    }
    dados.update(alteracoes)
    return SimpleNamespace(**dados)


def _ordem():
    return SimpleNamespace(id=20)


def _configuracao():
    return SimpleNamespace(
        id=1,
        serie_rps="1",
        proximo_rps=321,
    )


def _institucional():
    return SimpleNamespace(id=99)


def _argumentos(documento):
    return {
        "documento": documento,
        "ordem_servico": _ordem(),
        "configuracao_fiscal": _configuracao(),
        "configuracao_institucional": _institucional(),
        "versao_layout": "1.01",
        "tipo_emitente": "1",
        "municipio_incidencia_ibge": "3554508",
        "iss": {
            "tributacao_issqn": "1",
            "tipo_retencao": "1",
        },
        "totais_tributos": {
            "indicador": "0",
        },
    }


def test_b7a5_001_reserva_prepara_e_commita(
    monkeypatch,
):
    documento = _documento()
    eventos = []

    def fake_reservar_rps_nfse(**kwargs):
        eventos.append("reserva")
        documento.serie_rps = "1"
        documento.numero_rps = 321
        return documento, True

    def fake_preparar_payload_nfse_com_dps(**kwargs):
        eventos.append("payload")
        assert kwargs["documento"] is documento

        return {
            "provider": "SEFIN_NACIONAL",
            "conteudo": b"<DPS>VALIDA</DPS>",
        }

    monkeypatch.setattr(
        service,
        "reservar_rps_nfse",
        fake_reservar_rps_nfse,
    )
    monkeypatch.setattr(
        service,
        "preparar_payload_nfse_com_dps",
        fake_preparar_payload_nfse_com_dps,
    )
    monkeypatch.setattr(
        service,
        "_commit_preparacao_local_nfse",
        lambda: eventos.append("commit"),
    )
    monkeypatch.setattr(
        service,
        "_rollback_preparacao_local_nfse",
        lambda: eventos.append("rollback"),
    )

    def transmitir_proibido(*args, **kwargs):
        raise AssertionError(
            "B7-A5 nao pode transmitir NFS-e."
        )

    monkeypatch.setattr(
        service,
        "transmitir_payload_nfse",
        transmitir_proibido,
    )

    resultado_documento, payload = (
        service.preparar_documento_nfse_com_dps(
            **_argumentos(documento)
        )
    )

    assert resultado_documento is documento
    assert payload["conteudo"] == b"<DPS>VALIDA</DPS>"

    assert documento.status == "PREPARADA"
    assert "validada contra o XSD" in documento.mensagem_status

    assert eventos == [
        "reserva",
        "payload",
        "commit",
    ]


def test_b7a5_002_falha_no_pipeline_executa_rollback(
    monkeypatch,
):
    documento = _documento()
    eventos = []

    monkeypatch.setattr(
        service,
        "reservar_rps_nfse",
        lambda **kwargs: (
            eventos.append("reserva")
            or (documento, True)
        ),
    )

    def falhar_payload(**kwargs):
        eventos.append("payload")
        raise service.PreparacaoNfseInvalida(
            "falha-controlada-no-pipeline"
        )

    monkeypatch.setattr(
        service,
        "preparar_payload_nfse_com_dps",
        falhar_payload,
    )
    monkeypatch.setattr(
        service,
        "_commit_preparacao_local_nfse",
        lambda: eventos.append("commit"),
    )
    monkeypatch.setattr(
        service,
        "_rollback_preparacao_local_nfse",
        lambda: eventos.append("rollback"),
    )

    with pytest.raises(
        service.PreparacaoNfseInvalida,
        match="falha-controlada",
    ):
        service.preparar_documento_nfse_com_dps(
            **_argumentos(documento)
        )

    assert eventos == [
        "reserva",
        "payload",
        "rollback",
    ]

    assert documento.status == "RASCUNHO"


def test_b7a5_003_falha_na_reserva_executa_rollback(
    monkeypatch,
):
    documento = _documento()
    eventos = []

    def falhar_reserva(**kwargs):
        eventos.append("reserva")
        raise service.PreparacaoNfseInvalida(
            "falha-controlada-na-reserva"
        )

    monkeypatch.setattr(
        service,
        "reservar_rps_nfse",
        falhar_reserva,
    )

    def payload_proibido(**kwargs):
        raise AssertionError(
            "Pipeline DPS nao pode iniciar sem reserva RPS."
        )

    monkeypatch.setattr(
        service,
        "preparar_payload_nfse_com_dps",
        payload_proibido,
    )
    monkeypatch.setattr(
        service,
        "_commit_preparacao_local_nfse",
        lambda: eventos.append("commit"),
    )
    monkeypatch.setattr(
        service,
        "_rollback_preparacao_local_nfse",
        lambda: eventos.append("rollback"),
    )

    with pytest.raises(
        service.PreparacaoNfseInvalida,
        match="falha-controlada-na-reserva",
    ):
        service.preparar_documento_nfse_com_dps(
            **_argumentos(documento)
        )

    assert eventos == [
        "reserva",
        "rollback",
    ]


def test_b7a5_004_falha_no_commit_executa_rollback(
    monkeypatch,
):
    documento = _documento()
    eventos = []

    monkeypatch.setattr(
        service,
        "reservar_rps_nfse",
        lambda **kwargs: (
            eventos.append("reserva")
            or (documento, True)
        ),
    )
    monkeypatch.setattr(
        service,
        "preparar_payload_nfse_com_dps",
        lambda **kwargs: (
            eventos.append("payload")
            or {
                "provider": "SEFIN_NACIONAL",
                "conteudo": b"<DPS/>",
            }
        ),
    )

    def falhar_commit():
        eventos.append("commit")
        raise RuntimeError(
            "falha-controlada-no-commit"
        )

    monkeypatch.setattr(
        service,
        "_commit_preparacao_local_nfse",
        falhar_commit,
    )
    monkeypatch.setattr(
        service,
        "_rollback_preparacao_local_nfse",
        lambda: eventos.append("rollback"),
    )

    with pytest.raises(
        RuntimeError,
        match="falha-controlada-no-commit",
    ):
        service.preparar_documento_nfse_com_dps(
            **_argumentos(documento)
        )

    assert eventos == [
        "reserva",
        "payload",
        "commit",
        "rollback",
    ]


def test_b7a5_005_encaminha_parametros_fiscais(
    monkeypatch,
):
    documento = _documento()
    capturado = {}

    monkeypatch.setattr(
        service,
        "reservar_rps_nfse",
        lambda **kwargs: (documento, False),
    )

    def capturar_payload(**kwargs):
        capturado.update(kwargs)
        return {
            "conteudo": b"<DPS/>",
        }

    monkeypatch.setattr(
        service,
        "preparar_payload_nfse_com_dps",
        capturar_payload,
    )
    monkeypatch.setattr(
        service,
        "_commit_preparacao_local_nfse",
        lambda: None,
    )
    monkeypatch.setattr(
        service,
        "_rollback_preparacao_local_nfse",
        lambda: None,
    )

    argumentos = _argumentos(documento)

    service.preparar_documento_nfse_com_dps(
        **argumentos
    )

    assert capturado["documento"] is documento
    assert (
        capturado["ordem_servico"]
        is argumentos["ordem_servico"]
    )
    assert (
        capturado["configuracao_fiscal"]
        is argumentos["configuracao_fiscal"]
    )
    assert (
        capturado["configuracao_institucional"]
        is argumentos["configuracao_institucional"]
    )
    assert capturado["versao_layout"] == "1.01"
    assert capturado["tipo_emitente"] == "1"
    assert (
        capturado["municipio_incidencia_ibge"]
        == "3554508"
    )
