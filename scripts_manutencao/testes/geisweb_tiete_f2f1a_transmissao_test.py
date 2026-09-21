from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from app.fiscal.providers import geisweb_tiete_transmissao as tx


class FakeSession:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def _payload():
    return {
        "conteudo": b"<EnviaLoteRps/>",
        "webservice": {
            "endpoint": "https://geisweb.invalid/soap",
        },
    }


def _configuracao():
    return SimpleNamespace(
        ambiente="HOMOLOGACAO",
    )


def _preparar_fluxo_feliz(monkeypatch):
    chamadas = {}
    session = FakeSession()

    material = SimpleNamespace(
        caminho=Path("certificado-teste.pfx"),
    )

    monkeypatch.setenv(
        tx.ENV_PFX_PASSWORD,
        "SENHA-APENAS-TESTE",
    )

    monkeypatch.setattr(
        tx,
        "carregar_certificado_a1_do_ambiente",
        lambda: material,
    )

    def assinar(xml, material_recebido):
        chamadas["xml_normal"] = xml
        chamadas["material"] = material_recebido
        return b"<EnviaSignLoteRps/>"

    monkeypatch.setattr(
        tx,
        "assinar_xml_geisweb",
        assinar,
    )

    def montar_envelope(*, xml_fiscal, nome_operacao):
        chamadas["xml_assinado"] = xml_fiscal
        chamadas["operacao_soap"] = nome_operacao
        return b"<SOAP/>"

    monkeypatch.setattr(
        tx,
        "montar_envelope_soap_geisweb",
        montar_envelope,
    )

    monkeypatch.setattr(
        tx,
        "montar_headers_soap_geisweb",
        lambda *, nome_operacao: {
            "SOAPAction": (
                '"urn:teste#EnviaSignLoteRps"'
            )
        },
    )

    def criar_session(caminho, senha):
        chamadas["caminho"] = caminho
        chamadas["senha"] = senha
        return session

    monkeypatch.setattr(
        tx,
        "criar_session_a1",
        criar_session,
    )

    def enviar_http(
        session_recebida,
        *,
        endpoint,
        soap_action,
        envelope,
    ):
        chamadas["session"] = session_recebida
        chamadas["endpoint"] = endpoint
        chamadas["soap_action"] = soap_action
        chamadas["envelope"] = envelope

        return SimpleNamespace(
            status_code=200,
            text="<SOAP-RESPONSE/>",
        )

    monkeypatch.setattr(
        tx,
        "enviar_soap_geisweb",
        enviar_http,
    )

    def normalizar(
        response,
        *,
        operation,
        response_parameter,
    ):
        chamadas["response"] = response
        chamadas["operation_response"] = operation
        chamadas["response_parameter"] = response_parameter

        return SimpleNamespace(
            payload="<Retorno>OK</Retorno>",
            payload_is_xml=True,
        )

    monkeypatch.setattr(
        tx,
        "normalizar_resposta_geisweb",
        normalizar,
    )

    def interpretar(payload):
        chamadas["payload_funcional"] = payload

        return SimpleNamespace(
            status="ACEITA",
            mensagem="NFS-e emitida.",
            numero_lote="123",
            numero_nfse="456",
            codigo_verificacao="ABC123",
            chave_nacional=None,
            mensagens=(),
            nfse=(),
        )

    monkeypatch.setattr(
        tx,
        "interpretar_resultado_envio_geisweb",
        interpretar,
    )

    return chamadas, session, material


def test_f2f1a_orquestra_fluxo_completo_mockado(monkeypatch):
    chamadas, session, material = _preparar_fluxo_feliz(
        monkeypatch
    )

    resultado = tx.transmitir_payload_geisweb(
        payload=_payload(),
        configuracao=_configuracao(),
    )

    assert chamadas["xml_normal"] == b"<EnviaLoteRps/>"
    assert chamadas["material"] is material

    assert chamadas["xml_assinado"] == (
        b"<EnviaSignLoteRps/>"
    )

    assert chamadas["operacao_soap"] == (
        "EnviaSignLoteRps"
    )

    assert chamadas["endpoint"] == (
        "https://geisweb.invalid/soap"
    )

    assert chamadas["soap_action"] == (
        '"urn:teste#EnviaSignLoteRps"'
    )

    assert chamadas["envelope"] == b"<SOAP/>"
    assert chamadas["session"] is session

    assert chamadas["operation_response"] == (
        "EnviaSignLoteRps"
    )

    assert chamadas["response_parameter"] == (
        "EnviaSignLoteRpsResposta"
    )

    assert session.closed is True

    assert resultado["status"] == "ACEITA"
    assert resultado["protocolo"] is None
    assert resultado["numero_nfse"] == "456"

    dados = resultado["dados_provider"]

    assert dados["provider"] == "GEISWEB_TIETE"
    assert dados["ambiente"] == "HOMOLOGACAO"
    assert dados["http_status"] == 200
    assert dados["resposta"] == "<Retorno>OK</Retorno>"
    assert dados["resposta_is_xml"] is True


def test_f2f1a_usa_certificado_do_ambiente_sem_vazar_senha(
    monkeypatch,
):
    chamadas, _, _ = _preparar_fluxo_feliz(
        monkeypatch
    )

    resultado = tx.transmitir_payload_geisweb(
        payload=_payload(),
        configuracao=_configuracao(),
    )

    assert chamadas["caminho"] == Path(
        "certificado-teste.pfx"
    )

    assert chamadas["senha"] == (
        "SENHA-APENAS-TESTE"
    )

    assert (
        "SENHA-APENAS-TESTE"
        not in str(resultado)
    )


def test_f2f1a_rejeita_payload_sem_xml_antes_de_certificado(
    monkeypatch,
):
    chamadas = []

    monkeypatch.setattr(
        tx,
        "carregar_certificado_a1_do_ambiente",
        lambda: chamadas.append("certificado"),
    )

    payload = _payload()
    payload["conteudo"] = None

    with pytest.raises(
        tx.GeisWebTransmissaoError,
        match="nao possui XML",
    ):
        tx.transmitir_payload_geisweb(
            payload=payload,
            configuracao=_configuracao(),
        )

    assert chamadas == []


def test_f2f1a_rejeita_payload_sem_endpoint_antes_de_certificado(
    monkeypatch,
):
    chamadas = []

    monkeypatch.setattr(
        tx,
        "carregar_certificado_a1_do_ambiente",
        lambda: chamadas.append("certificado"),
    )

    payload = _payload()
    payload["webservice"]["endpoint"] = None

    with pytest.raises(
        tx.GeisWebTransmissaoError,
        match="nao possui endpoint",
    ):
        tx.transmitir_payload_geisweb(
            payload=payload,
            configuracao=_configuracao(),
        )

    assert chamadas == []


def test_f2f1a_fecha_session_quando_http_falha(monkeypatch):
    _, session, _ = _preparar_fluxo_feliz(
        monkeypatch
    )

    def falhar_http(*args, **kwargs):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(
        tx,
        "enviar_soap_geisweb",
        falhar_http,
    )

    with pytest.raises(
        RuntimeError,
        match="falha simulada",
    ):
        tx.transmitir_payload_geisweb(
            payload=_payload(),
            configuracao=_configuracao(),
        )

    assert session.closed is True


def test_f2f1a_rejeita_ausencia_da_senha_do_a1(monkeypatch):
    material = SimpleNamespace(
        caminho=Path("certificado-teste.pfx"),
    )

    monkeypatch.setattr(
        tx,
        "carregar_certificado_a1_do_ambiente",
        lambda: material,
    )

    monkeypatch.delenv(
        tx.ENV_PFX_PASSWORD,
        raising=False,
    )

    with pytest.raises(
        tx.GeisWebTransmissaoError,
        match="Senha do certificado A1",
    ):
        tx.transmitir_payload_geisweb(
            payload=_payload(),
            configuracao=_configuracao(),
        )