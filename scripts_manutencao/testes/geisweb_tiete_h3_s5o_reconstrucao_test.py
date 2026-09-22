import hashlib
from types import SimpleNamespace

import pytest

from app.fiscal import nfse_service as service


class FakeProvider:
    def __init__(self):
        self.chamadas = []

    def preparar_payload(
        self,
        *,
        documento,
        ordem_servico,
        configuracao,
    ):
        self.chamadas.append(
            (
                documento,
                ordem_servico,
                configuracao,
            )
        )

        return {
            "provider": "GEISWEB_TIETE",
            "ambiente": "HOMOLOGACAO",
            "webservice": {
                "endpoint": "https://mock.invalid",
                "soap_action": "mock",
            },
            "conteudo": None,
        }


def montar_cenario():
    xml = b"<xml-fiscal-geisweb>imutavel</xml-fiscal-geisweb>"

    documento = SimpleNamespace(
        id=12,
        ordem_servico_id=1,
        status="PREPARADA",
        provider="GEISWEB_TIETE",
        ambiente="HOMOLOGACAO",
        serie_rps="1",
        numero_rps=1,
        xml_envio=xml,
        xml_envio_sha256=hashlib.sha256(xml).hexdigest(),
    )

    ordem = SimpleNamespace(
        id=1,
    )

    configuracao = SimpleNamespace(
        provider="GEISWEB_TIETE",
        ambiente="HOMOLOGACAO",
    )

    return (
        xml,
        documento,
        ordem,
        configuracao,
    )


def test_s5o_reconstroi_sem_alterar_xml(
    monkeypatch,
):
    (
        xml,
        documento,
        ordem,
        configuracao,
    ) = montar_cenario()

    fake_provider = FakeProvider()

    monkeypatch.setattr(
        service,
        "resolver_provider_nfse",
        lambda configuracao: fake_provider,
    )

    monkeypatch.setattr(
        service,
        "validar_xml_envio_lote_rps",
        lambda xml_recebido: SimpleNamespace(
            valido=True,
            erros=(),
        ),
    )

    payload = service.reconstruir_payload_geisweb_para_envio(
        documento=documento,
        ordem_servico=ordem,
        configuracao=configuracao,
    )

    assert payload["conteudo"] == xml
    assert payload["conteudo"] is documento.xml_envio

    assert fake_provider.chamadas == [
        (
            documento,
            ordem,
            configuracao,
        )
    ]

    assert documento.numero_rps == 1
    assert documento.status == "PREPARADA"


def test_s5o_bloqueia_hash_divergente(
    monkeypatch,
):
    (
        _,
        documento,
        ordem,
        configuracao,
    ) = montar_cenario()

    documento.xml_envio_sha256 = "0" * 64

    monkeypatch.setattr(
        service,
        "resolver_provider_nfse",
        lambda configuracao: pytest.fail(
            "Provider nao pode ser acionado com hash invalido."
        ),
    )

    with pytest.raises(
        service.TransmissaoNfseInvalida,
        match="Integridade",
    ):
        service.reconstruir_payload_geisweb_para_envio(
            documento=documento,
            ordem_servico=ordem,
            configuracao=configuracao,
        )


def test_s5o_bloqueia_xsd_invalido(
    monkeypatch,
):
    (
        _,
        documento,
        ordem,
        configuracao,
    ) = montar_cenario()

    monkeypatch.setattr(
        service,
        "validar_xml_envio_lote_rps",
        lambda xml_recebido: SimpleNamespace(
            valido=False,
            erros=("falha-xsd",),
        ),
    )

    monkeypatch.setattr(
        service,
        "resolver_provider_nfse",
        lambda configuracao: pytest.fail(
            "Provider nao pode ser acionado com XSD invalido."
        ),
    )

    with pytest.raises(
        service.TransmissaoNfseInvalida,
        match="XSD GeisWeb",
    ):
        service.reconstruir_payload_geisweb_para_envio(
            documento=documento,
            ordem_servico=ordem,
            configuracao=configuracao,
        )


def test_s5o_bloqueia_ambiente_divergente(
    monkeypatch,
):
    (
        _,
        documento,
        ordem,
        configuracao,
    ) = montar_cenario()

    configuracao.ambiente = "PRODUCAO"

    monkeypatch.setattr(
        service,
        "resolver_provider_nfse",
        lambda configuracao: pytest.fail(
            "Provider nao pode ser acionado em ambiente divergente."
        ),
    )

    with pytest.raises(
        service.TransmissaoNfseInvalida,
        match="Ambiente fiscal",
    ):
        service.reconstruir_payload_geisweb_para_envio(
            documento=documento,
            ordem_servico=ordem,
            configuracao=configuracao,
        )
