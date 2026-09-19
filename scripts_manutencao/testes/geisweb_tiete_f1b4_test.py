from types import SimpleNamespace

from app.fiscal.providers import (
    obter_provider,
)


def _configuracao():
    return SimpleNamespace(
        provider="GEISWEB_TIETE",
        ambiente="HOMOLOGACAO",
        municipio_ibge="3554508",
        integracao_ativa=False,
    )


def test_payload_geisweb_tem_contrato_tecnico():
    provider = obter_provider(
        "GEISWEB_TIETE"
    )

    payload = provider.preparar_payload(
        documento=SimpleNamespace(
            id=1,
            serie_rps="A",
            numero_rps=10,
        ),
        ordem_servico=SimpleNamespace(
            id=2,
        ),
        configuracao=_configuracao(),
    )

    assert payload == {
        "provider": "GEISWEB_TIETE",
        "ambiente": "HOMOLOGACAO",
        "tipo_documento": "RPS_LOTE",
        "documento_id": 1,
        "ordem_servico_id": 2,
        "rps": {
            "serie": "A",
            "numero": 10,
        },
        "layout": {
            "versao": "1.01",
            "namespace": (
                "http://www.gerenciadecidades.com.br/"
                "xsd/envio_lote_rps_reforma.xsd"
            ),
        },
        "municipio_prestador": {
            "codigo_ibge": "3554508",
        },
        "webservice": {
            "endpoint": (
                "https://www.gerenciadecidades.com.br/"
                "homologacao/reforma/modelo/webservice/"
                "GeisWebServiceImpl.php"
            ),
            "wsdl": (
                "https://www.gerenciadecidades.com.br/"
                "homologacao/reforma/modelo/webservice/"
                "GeisWebServiceImpl.php?wsdl"
            ),
            "soap_version": "1.1",
            "soap_style": "rpc",
            "soap_use": "encoded",
            "soap_action": (
                "urn:https://www.gerenciadecidades.com.br/"
                "homologacao/reforma/modelo/webservice/"
                "GeisWebServiceImpl.php#EnviaLoteRps"
            ),
        },
        "conteudo": None,
    }


def test_payload_geisweb_nao_monta_xml_neste_estagio():
    provider = obter_provider(
        "GEISWEB_TIETE"
    )

    payload = provider.preparar_payload(
        documento=SimpleNamespace(
            id=1,
            serie_rps="A",
            numero_rps=10,
        ),
        ordem_servico=SimpleNamespace(
            id=2,
        ),
        configuracao=_configuracao(),
    )

    assert payload["conteudo"] is None

    assert "xml" not in payload
    assert "assinatura" not in payload
    assert "certificado" not in payload


def test_payload_geisweb_preserva_dados_rps():
    provider = obter_provider(
        "GEISWEB_TIETE"
    )

    payload = provider.preparar_payload(
        documento=SimpleNamespace(
            id=999,
            serie_rps="JSP",
            numero_rps=123,
        ),
        ordem_servico=SimpleNamespace(
            id=456,
        ),
        configuracao=_configuracao(),
    )

    assert payload["documento_id"] == 999
    assert payload["ordem_servico_id"] == 456
    assert payload["rps"] == {
        "serie": "JSP",
        "numero": 123,
    }
