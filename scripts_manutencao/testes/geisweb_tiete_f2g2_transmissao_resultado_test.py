from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from app.fiscal.providers import (
    geisweb_tiete_transmissao as tx,
)


class FakeSession:
    def close(self):
        pass


def _instalar_pipeline(monkeypatch, resultado_funcional):
    monkeypatch.setenv(
        tx.ENV_PFX_PASSWORD,
        "SENHA-TESTE",
    )

    material = SimpleNamespace(
        caminho=Path("teste.pfx"),
    )

    monkeypatch.setattr(
        tx,
        "carregar_certificado_a1_do_ambiente",
        lambda: material,
    )

    monkeypatch.setattr(
        tx,
        "montar_envelope_soap_geisweb",
        lambda **kwargs: b"<soap/>",
    )

    monkeypatch.setattr(
        tx,
        "montar_headers_soap_geisweb",
        lambda **kwargs: {
            "SOAPAction": '"urn:teste"',
        },
    )

    monkeypatch.setattr(
        tx,
        "criar_session_a1",
        lambda *args, **kwargs: FakeSession(),
    )

    monkeypatch.setattr(
        tx,
        "enviar_soap_geisweb",
        lambda *args, **kwargs: SimpleNamespace(
            status_code=200,
            text="<soap-response/>",
        ),
    )

    monkeypatch.setattr(
        tx,
        "normalizar_resposta_geisweb",
        lambda *args, **kwargs: SimpleNamespace(
            payload="<EnviaLoteRpsResposta/>",
            payload_is_xml=True,
        ),
    )

    monkeypatch.setattr(
        tx,
        "interpretar_resultado_envio_geisweb",
        lambda payload: resultado_funcional,
    )


def _payload():
    return {
        "conteudo": b"<EnviaLoteRps/>",
        "webservice": {
            "endpoint": "https://geisweb.invalid/soap",
        },
    }


def _config():
    return SimpleNamespace(
        ambiente="HOMOLOGACAO",
    )


def test_f2g2_mapeia_nfse_emitida(monkeypatch):
    nota = SimpleNamespace(
        numero_rps="10",
        numero_nfse="200",
        codigo_verificacao="ABC",
        chave_nacional="CHAVE",
    )

    resultado_funcional = SimpleNamespace(
        status="ACEITA",
        mensagem="NFS-e emitida.",
        numero_lote="99",
        numero_nfse="200",
        codigo_verificacao="ABC",
        chave_nacional="CHAVE",
        mensagens=(),
        nfse=(nota,),
    )

    _instalar_pipeline(
        monkeypatch,
        resultado_funcional,
    )

    resultado = tx.transmitir_payload_geisweb(
        payload=_payload(),
        configuracao=_config(),
    )

    assert resultado["status"] == "ACEITA"
    assert resultado["numero_nfse"] == "200"
    assert resultado["protocolo"] is None

    dados = resultado["dados_provider"]

    assert dados["numero_lote"] == "99"
    assert dados["codigo_verificacao"] == "ABC"
    assert dados["chave_nacional"] == "CHAVE"

    assert dados["nfse"][0]["numero_rps"] == "10"
    assert dados["nfse"][0]["numero_nfse"] == "200"


def test_f2g2_mapeia_rejeicao(monkeypatch):
    mensagem = SimpleNamespace(
        erro=100,
        status="Inscricao municipal invalida.",
    )

    resultado_funcional = SimpleNamespace(
        status="REJEITADA",
        mensagem="Inscricao municipal invalida.",
        numero_lote=None,
        numero_nfse=None,
        codigo_verificacao=None,
        chave_nacional=None,
        mensagens=(mensagem,),
        nfse=(),
    )

    _instalar_pipeline(
        monkeypatch,
        resultado_funcional,
    )

    resultado = tx.transmitir_payload_geisweb(
        payload=_payload(),
        configuracao=_config(),
    )

    assert resultado["status"] == "REJEITADA"
    assert resultado["numero_nfse"] is None

    assert resultado["dados_provider"]["mensagens"] == [
        {
            "erro": 100,
            "status": "Inscricao municipal invalida.",
        }
    ]


def test_f2g2_mapeia_retorno_inconclusivo_como_erro(
    monkeypatch,
):
    resultado_funcional = SimpleNamespace(
        status="ERRO",
        mensagem="Retorno inconclusivo.",
        numero_lote="55",
        numero_nfse=None,
        codigo_verificacao=None,
        chave_nacional=None,
        mensagens=(),
        nfse=(),
    )

    _instalar_pipeline(
        monkeypatch,
        resultado_funcional,
    )

    resultado = tx.transmitir_payload_geisweb(
        payload=_payload(),
        configuracao=_config(),
    )

    assert resultado["status"] == "ERRO"
    assert resultado["mensagem"] == "Retorno inconclusivo."
    assert resultado["dados_provider"]["numero_lote"] == "55"
