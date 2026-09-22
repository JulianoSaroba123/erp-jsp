from __future__ import annotations

import pytest

from app.fiscal.providers.geisweb_tiete_response import (
    GeisWebNormalizedResponse,
    GeisWebResponseError,
    normalizar_resposta_geisweb,
)


SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"


def test_f2e1_extrai_xml_escapado_do_xsd_string():
    soap = f"""
    <soapenv:Envelope
        xmlns:soapenv="{SOAP_NS}"
        xmlns:ns1="urn:GeisWebService">
      <soapenv:Body>
        <ns1:EnviaSignLoteRpsResponse>
          <EnviaSignLoteRpsResposta>
            &lt;Retorno&gt;&lt;Sucesso&gt;true&lt;/Sucesso&gt;&lt;/Retorno&gt;
          </EnviaSignLoteRpsResposta>
        </ns1:EnviaSignLoteRpsResponse>
      </soapenv:Body>
    </soapenv:Envelope>
    """

    resposta = normalizar_resposta_geisweb(soap)

    assert isinstance(
        resposta,
        GeisWebNormalizedResponse,
    )

    assert (
        resposta.operation_response
        == "EnviaSignLoteRpsResponse"
    )

    assert (
        resposta.response_parameter
        == "EnviaSignLoteRpsResposta"
    )

    assert resposta.payload == (
        "<Retorno><Sucesso>true</Sucesso></Retorno>"
    )

    assert resposta.payload_is_xml is True


def test_f2e1_aceita_payload_em_cdata():
    soap = f"""
    <soap:Envelope xmlns:soap="{SOAP_NS}">
      <soap:Body>
        <EnviaSignLoteRpsResponse>
          <EnviaSignLoteRpsResposta><![CDATA[
            <Retorno><Protocolo>ABC123</Protocolo></Retorno>
          ]]></EnviaSignLoteRpsResposta>
        </EnviaSignLoteRpsResponse>
      </soap:Body>
    </soap:Envelope>
    """

    resposta = normalizar_resposta_geisweb(soap)

    assert "<Protocolo>ABC123</Protocolo>" in resposta.payload
    assert resposta.payload_is_xml is True


def test_f2e1_tolera_namespace_no_parametro_de_resposta():
    soap = f"""
    <s:Envelope
        xmlns:s="{SOAP_NS}"
        xmlns:g="urn:teste">
      <s:Body>
        <g:EnviaSignLoteRpsResponse>
          <g:EnviaSignLoteRpsResposta>OK</g:EnviaSignLoteRpsResposta>
        </g:EnviaSignLoteRpsResponse>
      </s:Body>
    </s:Envelope>
    """

    resposta = normalizar_resposta_geisweb(
        soap.encode("utf-8")
    )

    assert resposta.payload == "OK"
    assert resposta.payload_is_xml is False


def test_f2e1_detecta_soap_fault_sem_vazar_faultstring_na_mensagem():
    soap = f"""
    <soap:Envelope xmlns:soap="{SOAP_NS}">
      <soap:Body>
        <soap:Fault>
          <faultcode>soap:Server</faultcode>
          <faultstring>
            SEGREDO-RETORNADO-PELO-SERVIDOR
          </faultstring>
        </soap:Fault>
      </soap:Body>
    </soap:Envelope>
    """

    with pytest.raises(GeisWebResponseError) as exc_info:
        normalizar_resposta_geisweb(soap)

    erro = exc_info.value

    assert erro.fault_code == "soap:Server"

    assert (
        erro.fault_string
        == "SEGREDO-RETORNADO-PELO-SERVIDOR"
    )

    assert str(erro) == "GeisWeb retornou SOAP Fault."

    assert (
        "SEGREDO-RETORNADO-PELO-SERVIDOR"
        not in str(erro)
    )


def test_f2e1_rejeita_xml_soap_malformado():
    soap = """
    <soap:Envelope>
      <soap:Body>
    """

    with pytest.raises(
        GeisWebResponseError,
        match="XML inválido",
    ):
        normalizar_resposta_geisweb(soap)


def test_f2e1_rejeita_resposta_sem_parametro_esperado():
    soap = f"""
    <soap:Envelope xmlns:soap="{SOAP_NS}">
      <soap:Body>
        <EnviaSignLoteRpsResponse>
          <OutroParametro>OK</OutroParametro>
        </EnviaSignLoteRpsResponse>
      </soap:Body>
    </soap:Envelope>
    """

    with pytest.raises(
        GeisWebResponseError,
        match="EnviaSignLoteRpsResposta",
    ):
        normalizar_resposta_geisweb(soap)