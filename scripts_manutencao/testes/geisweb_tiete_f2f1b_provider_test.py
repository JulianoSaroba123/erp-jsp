from __future__ import annotations

from types import SimpleNamespace

import pytest

import app.fiscal.providers.geisweb_tiete  # noqa: F401
from app.fiscal.providers import geisweb_tiete_transmissao as tx
from app.fiscal.providers.registry import obter_provider


def test_f2f1b_provider_valida_disjuntor_e_delega_transmissao(
    monkeypatch,
):
    provider = obter_provider("GEISWEB_TIETE")

    payload = {
        "conteudo": b"<xml/>",
    }

    configuracao = SimpleNamespace(
        ambiente="HOMOLOGACAO",
    )

    chamadas = []

    monkeypatch.setattr(
        provider,
        "validar_configuracao",
        lambda cfg: chamadas.append("configuracao"),
    )

    monkeypatch.setattr(
        provider,
        "validar_integracao_externa",
        lambda cfg: chamadas.append("disjuntor"),
    )

    esperado = {
        "status": "PROCESSANDO",
        "mensagem": "ok",
        "protocolo": None,
        "numero_nfse": None,
        "dados_provider": {
            "provider": "GEISWEB_TIETE",
        },
    }

    def transmitir_fake(*, payload, configuracao):
        chamadas.append("transmissao")

        assert payload is not None
        assert configuracao is not None

        return esperado

    monkeypatch.setattr(
        tx,
        "transmitir_payload_geisweb",
        transmitir_fake,
    )

    resultado = provider.transmitir(
        payload=payload,
        configuracao=configuracao,
    )

    assert chamadas == [
        "configuracao",
        "disjuntor",
        "transmissao",
    ]

    assert resultado == esperado


def test_f2f1b_disjuntor_bloqueia_antes_da_transmissao(
    monkeypatch,
):
    provider = obter_provider("GEISWEB_TIETE")

    chamadas = []

    monkeypatch.setattr(
        provider,
        "validar_configuracao",
        lambda cfg: chamadas.append("configuracao"),
    )

    def bloquear(cfg):
        chamadas.append("disjuntor")
        raise RuntimeError("integracao bloqueada")

    monkeypatch.setattr(
        provider,
        "validar_integracao_externa",
        bloquear,
    )

    def transmissao_proibida(**kwargs):
        chamadas.append("transmissao")
        raise AssertionError(
            "Transmissao nao poderia ser chamada."
        )

    monkeypatch.setattr(
        tx,
        "transmitir_payload_geisweb",
        transmissao_proibida,
    )

    with pytest.raises(
        RuntimeError,
        match="integracao bloqueada",
    ):
        provider.transmitir(
            payload={"conteudo": b"<xml/>"},
            configuracao=SimpleNamespace(),
        )

    assert chamadas == [
        "configuracao",
        "disjuntor",
    ]


def test_f2f1b_configuracao_invalida_bloqueia_antes_do_disjuntor(
    monkeypatch,
):
    provider = obter_provider("GEISWEB_TIETE")

    chamadas = []

    def configuracao_invalida(cfg):
        chamadas.append("configuracao")
        raise ValueError("configuracao invalida")

    monkeypatch.setattr(
        provider,
        "validar_configuracao",
        configuracao_invalida,
    )

    monkeypatch.setattr(
        provider,
        "validar_integracao_externa",
        lambda cfg: chamadas.append("disjuntor"),
    )

    monkeypatch.setattr(
        tx,
        "transmitir_payload_geisweb",
        lambda **kwargs: chamadas.append("transmissao"),
    )

    with pytest.raises(
        ValueError,
        match="configuracao invalida",
    ):
        provider.transmitir(
            payload={"conteudo": b"<xml/>"},
            configuracao=SimpleNamespace(),
        )

    assert chamadas == [
        "configuracao",
    ]
