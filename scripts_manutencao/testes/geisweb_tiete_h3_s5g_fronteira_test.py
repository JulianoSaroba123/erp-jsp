from types import SimpleNamespace

from app.fiscal.providers.geisweb_tiete import GeisWebTieteProvider
from app.fiscal.providers import geisweb_tiete_transmissao as tx


def test_h3_s5g_integracao_ativa_abre_disjuntor_e_delega_sem_rede(
    monkeypatch,
):
    provider = GeisWebTieteProvider()

    configuracao = SimpleNamespace(
        provider="GEISWEB_TIETE",
        ambiente="HOMOLOGACAO",
        municipio_ibge="3554508",
        integracao_ativa=True,
    )

    payload = {
        "provider": "GEISWEB_TIETE",
        "conteudo": b"<xml/>",
    }

    esperado = {
        "status": "PROCESSANDO",
        "mensagem": "fronteira mockada",
        "protocolo": None,
        "numero_nfse": None,
        "dados_provider": {
            "provider": "GEISWEB_TIETE",
            "ambiente": "HOMOLOGACAO",
        },
    }

    chamadas = []

    def transmitir_fake(*, payload, configuracao):
        chamadas.append(
            {
                "payload": payload,
                "configuracao": configuracao,
            }
        )

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

    assert resultado is esperado
    assert len(chamadas) == 1

    assert chamadas[0]["payload"] is payload
    assert chamadas[0]["configuracao"] is configuracao

    assert configuracao.integracao_ativa is True
