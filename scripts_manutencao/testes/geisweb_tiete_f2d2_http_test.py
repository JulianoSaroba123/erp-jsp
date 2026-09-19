from __future__ import annotations

import requests
import pytest

from app.fiscal.providers.geisweb_tiete_http import (
    GeisWebHttpError,
    GeisWebHttpResponse,
    enviar_soap_geisweb,
)


ENDPOINT_FAKE = "https://geisweb.invalid/soap"
SOAP_ACTION = "urn:EnviaSignLoteRps"
SOAP_XML = "<soapenv:Envelope>teste</soapenv:Envelope>"


class FakeResponse:
    def __init__(
        self,
        *,
        status_code=200,
        text="<retorno>ok</retorno>",
        content=None,
        headers=None,
    ):
        self.status_code = status_code
        self.text = text
        self.content = (
            content
            if content is not None
            else text.encode("utf-8")
        )
        self.headers = headers or {
            "Content-Type": "text/xml; charset=utf-8"
        }


class FakeSession:
    def __init__(self, response=None, error=None):
        self.response = response or FakeResponse()
        self.error = error
        self.calls = []

    def post(
        self,
        endpoint,
        *,
        data,
        headers,
        timeout,
    ):
        self.calls.append(
            {
                "endpoint": endpoint,
                "data": data,
                "headers": dict(headers),
                "timeout": timeout,
            }
        )

        if self.error is not None:
            raise self.error

        return self.response


def test_f2d2_executa_post_na_session_injetada_com_soap11():
    session = FakeSession()

    resposta = enviar_soap_geisweb(
        session,
        endpoint=ENDPOINT_FAKE,
        soap_action=SOAP_ACTION,
        envelope=SOAP_XML,
    )

    assert isinstance(resposta, GeisWebHttpResponse)
    assert len(session.calls) == 1

    chamada = session.calls[0]

    assert chamada["endpoint"] == ENDPOINT_FAKE
    assert chamada["data"] == SOAP_XML.encode("utf-8")
    assert chamada["timeout"] == (10.0, 60.0)

    assert chamada["headers"] == {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": '"urn:EnviaSignLoteRps"',
    }


def test_f2d2_respeita_timeout_explicito():
    session = FakeSession()

    enviar_soap_geisweb(
        session,
        endpoint=ENDPOINT_FAKE,
        soap_action='"urn:EnviaSignLoteRps"',
        envelope=SOAP_XML,
        timeout=(3.0, 15.0),
    )

    assert session.calls[0]["timeout"] == (3.0, 15.0)

    assert session.calls[0]["headers"]["SOAPAction"] == (
        '"urn:EnviaSignLoteRps"'
    )


def test_f2d2_preserva_resposta_http_200():
    session = FakeSession(
        response=FakeResponse(
            status_code=200,
            text="<resultado>SUCESSO</resultado>",
            headers={
                "Content-Type": "text/xml",
                "X-Teste": "ok",
            },
        )
    )

    resposta = enviar_soap_geisweb(
        session,
        endpoint=ENDPOINT_FAKE,
        soap_action=SOAP_ACTION,
        envelope=SOAP_XML,
    )

    assert resposta.status_code == 200
    assert resposta.text == "<resultado>SUCESSO</resultado>"
    assert resposta.content == (
        b"<resultado>SUCESSO</resultado>"
    )
    assert resposta.headers["X-Teste"] == "ok"


def test_f2d2_preserva_erro_http_sem_vazar_corpo_na_mensagem():
    corpo_sensivel = (
        "<fault>"
        "CONTEUDO-QUE-NAO-DEVE-IR-NA-MENSAGEM"
        "</fault>"
    )

    session = FakeSession(
        response=FakeResponse(
            status_code=500,
            text=corpo_sensivel,
        )
    )

    with pytest.raises(GeisWebHttpError) as exc_info:
        enviar_soap_geisweb(
            session,
            endpoint=ENDPOINT_FAKE,
            soap_action=SOAP_ACTION,
            envelope=SOAP_XML,
        )

    erro = exc_info.value

    assert erro.status_code == 500
    assert erro.response_text == corpo_sensivel

    assert (
        "CONTEUDO-QUE-NAO-DEVE-IR-NA-MENSAGEM"
        not in str(erro)
    )

    assert str(erro) == "GeisWeb Tietê respondeu HTTP 500."


def test_f2d2_trata_timeout_sem_expor_dados_da_requisicao():
    session = FakeSession(
        error=requests.Timeout(
            "SEGREDO-TRANSPORTE-NAO-DEVE-VAZAR"
        )
    )

    with pytest.raises(GeisWebHttpError) as exc_info:
        enviar_soap_geisweb(
            session,
            endpoint=ENDPOINT_FAKE,
            soap_action=SOAP_ACTION,
            envelope=SOAP_XML,
        )

    erro = exc_info.value

    assert (
        str(erro)
        == "Falha de transporte HTTP ao comunicar com o GeisWeb Tietê."
    )

    assert "SEGREDO-TRANSPORTE" not in str(erro)
    assert isinstance(erro.original_error, requests.Timeout)


def test_f2d2_bloqueia_endpoint_sem_https_antes_do_post():
    session = FakeSession()

    with pytest.raises(
        GeisWebHttpError,
        match="deve utilizar HTTPS",
    ):
        enviar_soap_geisweb(
            session,
            endpoint="http://geisweb.invalid/soap",
            soap_action=SOAP_ACTION,
            envelope=SOAP_XML,
        )

    assert session.calls == []