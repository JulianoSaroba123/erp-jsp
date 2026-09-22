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
        serie_rps="1",
        numero_rps=1,
    )


def _ordem():
    return SimpleNamespace(id=620)


def _config(
    *,
    ambiente="HOMOLOGACAO",
    integracao_ativa=False,
):
    return SimpleNamespace(
        id=1,
        provider="GEISWEB_TIETE",
        ambiente=ambiente,
        integracao_ativa=integracao_ativa,
    )


def test_exige_token_transmitir():
    with pytest.raises(
        service.TransmissaoNfseInvalida,
        match="TRANSMITIR",
    ):
        service.transmitir_nfse_geisweb_homologacao_one_shot(
            documento=_documento(),
            ordem_servico=_ordem(),
            configuracao=_config(),
            confirmacao="SIM",
        )


def test_producao_permanece_bloqueada():
    with pytest.raises(
        service.TransmissaoNfseInvalida,
        match="somente em HOMOLOGACAO",
    ):
        service.transmitir_nfse_geisweb_homologacao_one_shot(
            documento=_documento(),
            ordem_servico=_ordem(),
            configuracao=_config(
                ambiente="PRODUCAO",
            ),
            confirmacao="TRANSMITIR",
        )


def test_one_shot_liga_e_desliga_gate(
    monkeypatch,
):
    documento = _documento()
    config = _config()

    monkeypatch.setattr(
        service,
        "precheck_transmissao_geisweb",
        lambda **kwargs: {"ok": True},
    )

    chamadas = []

    def fake(**kwargs):
        assert kwargs[
            "configuracao"
        ].integracao_ativa is True

        assert kwargs[
            "autorizar_transmissao"
        ] is True

        chamadas.append(True)

        return documento, {
            "status": "ACEITA",
        }

    monkeypatch.setattr(
        service,
        "transmitir_documento_nfse_geisweb_controlado",
        fake,
    )

    service.transmitir_nfse_geisweb_homologacao_one_shot(
        documento=documento,
        ordem_servico=_ordem(),
        configuracao=config,
        confirmacao="TRANSMITIR",
    )

    assert chamadas == [True]
    assert config.integracao_ativa is False


def test_falha_tambem_desliga_gate(
    monkeypatch,
):
    config = _config()

    monkeypatch.setattr(
        service,
        "precheck_transmissao_geisweb",
        lambda **kwargs: {"ok": True},
    )

    def fake(**kwargs):
        assert kwargs[
            "configuracao"
        ].integracao_ativa is True

        raise RuntimeError("falha simulada")

    monkeypatch.setattr(
        service,
        "transmitir_documento_nfse_geisweb_controlado",
        fake,
    )

    with pytest.raises(
        RuntimeError,
        match="falha simulada",
    ):
        service.transmitir_nfse_geisweb_homologacao_one_shot(
            documento=_documento(),
            ordem_servico=_ordem(),
            configuracao=config,
            confirmacao="TRANSMITIR",
        )

    assert config.integracao_ativa is False


def test_helper_nao_commita():
    fonte = inspect.getsource(
        service.transmitir_nfse_geisweb_homologacao_one_shot
    )

    assert "precheck_transmissao_geisweb(" in fonte
    assert "autorizar_transmissao=True" in fonte
    assert "db.session" not in fonte
    assert ".commit(" not in fonte


def test_rota_registrada():
    app = create_app("testing")

    rotas = {
        regra.endpoint: regra.rule
        for regra in app.url_map.iter_rules()
    }

    endpoint = (
        "ordem_servico."
        "transmitir_nfse_parcela_homologacao"
    )

    assert endpoint in rotas


def test_interface_exige_confirmacao():
    fonte = Path(
        "app/ordem_servico/templates/os/"
        "_painel_fiscal_parcelas.html"
    ).read_text(
        encoding="utf-8"
    )

    assert "Transmitir em HOMOLOGA" in fonte
    assert 'name="confirmacao"' in fonte
    assert 'pattern="TRANSMITIR"' in fonte
    assert "CHAMADA EXTERNA REAL" in fonte
