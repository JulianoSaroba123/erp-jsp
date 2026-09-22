from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import inspect

import pytest

from app import create_app
from app.fiscal import nfse_service as service


def _documento():
    return SimpleNamespace(
        id=1,
        status="PENDENTE_ENVIO",
        provider="GEISWEB_TIETE",
        ambiente="HOMOLOGACAO",
        serie_rps="1",
        numero_rps=1,
    )


def _ordem():
    return SimpleNamespace(
        id=620,
    )


def _config():
    return SimpleNamespace(
        id=1,
        provider="GEISWEB_TIETE",
        ambiente="HOMOLOGACAO",
        integracao_ativa=False,
    )


def test_precheck_valida_certificado_e_mtls_sem_transmitir(
    monkeypatch,
):
    documento = _documento()
    ordem = _ordem()
    configuracao = _config()

    payload = {
        "provider": "GEISWEB_TIETE",
        "ambiente": "HOMOLOGACAO",
        "conteudo": b"<xml/>",
        "webservice": {
            "endpoint": service.ENDPOINT_HOMOLOGACAO,
        },
    }

    monkeypatch.setattr(
        service,
        "reconstruir_payload_geisweb_para_envio",
        lambda **kwargs: payload,
    )

    monkeypatch.setenv(
        service.ENV_PFX_PASSWORD,
        "senha-teste",
    )

    certificado = SimpleNamespace(
        not_valid_before_utc=datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ),
        not_valid_after_utc=datetime(
            2027,
            1,
            1,
            tzinfo=timezone.utc,
        ),
    )

    material = SimpleNamespace(
        caminho=Path("certificado-teste.pfx"),
        certificado=certificado,
    )

    monkeypatch.setattr(
        service,
        "carregar_certificado_a1_do_ambiente",
        lambda: material,
    )

    fechado = []

    class FakeSession:
        def close(self):
            fechado.append(True)

    monkeypatch.setattr(
        service,
        "criar_session_a1",
        lambda caminho, senha: FakeSession(),
    )

    status_antes = documento.status

    resultado = service.precheck_transmissao_geisweb(
        documento=documento,
        ordem_servico=ordem,
        configuracao=configuracao,
    )

    assert resultado["ok"] is True
    assert resultado["mtls_pronto"] is True
    assert resultado["integracao_ativa"] is False
    assert resultado["numero_rps"] == 1
    assert resultado["serie_rps"] == "1"

    assert documento.status == status_antes
    assert configuracao.integracao_ativa is False

    assert fechado == [True]


def test_precheck_bloqueia_sem_senha(
    monkeypatch,
):
    documento = _documento()

    monkeypatch.setattr(
        service,
        "reconstruir_payload_geisweb_para_envio",
        lambda **kwargs: {
            "provider": "GEISWEB_TIETE",
            "ambiente": "HOMOLOGACAO",
            "conteudo": b"<xml/>",
            "webservice": {
                "endpoint": service.ENDPOINT_HOMOLOGACAO,
            },
        },
    )

    monkeypatch.delenv(
        service.ENV_PFX_PASSWORD,
        raising=False,
    )

    with pytest.raises(
        service.TransmissaoNfseInvalida,
        match="Senha do certificado A1",
    ):
        service.precheck_transmissao_geisweb(
            documento=documento,
            ordem_servico=_ordem(),
            configuracao=_config(),
        )


def test_precheck_nao_possui_fronteira_de_rede():
    fonte = inspect.getsource(
        service.precheck_transmissao_geisweb
    )

    assert (
        "reconstruir_payload_geisweb_para_envio("
        in fonte
    )

    assert (
        "carregar_certificado_a1_do_ambiente("
        in fonte
    )

    assert "criar_session_a1(" in fonte

    proibidos = (
        "enviar_soap_geisweb(",
        "transmitir_payload_nfse(",
        "transmitir_e_aplicar_nfse(",
        "transmitir_documento_nfse_geisweb_controlado(",
        ".post(",
        ".get(",
        "requests.",
        "db.session",
    )

    for termo in proibidos:
        assert termo not in fonte


def test_rota_precheck_registrada():
    app = create_app("testing")

    rotas = {
        regra.endpoint: regra.rule
        for regra in app.url_map.iter_rules()
    }

    endpoint = (
        "ordem_servico."
        "precheck_nfse_parcela_transmissao"
    )

    assert endpoint in rotas

    assert rotas[endpoint] == (
        "/ordem_servico/<int:id>/fiscal/parcela/"
        "<int:parcela_id>/precheck-transmissao"
    )


def test_interface_expoe_precheck():
    fonte = Path(
        "app/ordem_servico/templates/os/"
        "_painel_fiscal_parcelas.html"
    ).read_text(
        encoding="utf-8"
    )

    assert "Pr&eacute;-check transmiss&atilde;o" in fonte

    assert (
        "precheck_nfse_parcela_transmissao"
        in fonte
    )
