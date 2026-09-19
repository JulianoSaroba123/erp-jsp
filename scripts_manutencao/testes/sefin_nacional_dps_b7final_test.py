from types import SimpleNamespace

import pytest

from app.fiscal import nfse_service as service


def _documento(status="PREPARADA"):
    return SimpleNamespace(
        id=10,
        status=status,
        mensagem_status=None,
    )


def _payload(conteudo=b"<DPS>VALIDA</DPS>"):
    return {
        "provider": "SEFIN_NACIONAL",
        "conteudo": conteudo,
    }


def test_b7final_001_preparada_vira_pendente_envio():
    documento = _documento()

    resultado = service.preparar_nfse_para_envio(
        documento=documento,
        payload=_payload(),
    )

    assert resultado is documento
    assert documento.status == "PENDENTE_ENVIO"
    assert "Nenhuma NFS-e foi transmitida" in (
        documento.mensagem_status
    )


def test_b7final_002_bloqueia_estado_invalido():
    documento = _documento(
        status="RASCUNHO"
    )

    with pytest.raises(
        service.TransicaoStatusNfseInvalida,
        match="nao pode ser marcado",
    ):
        service.preparar_nfse_para_envio(
            documento=documento,
            payload=_payload(),
        )

    assert documento.status == "RASCUNHO"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"conteudo": None},
        {"conteudo": b""},
        {"conteudo": "<DPS/>"},
    ],
)
def test_b7final_003_exige_xml_serializado(
    payload,
):
    documento = _documento()

    with pytest.raises(
        service.TransicaoStatusNfseInvalida,
        match="nao possui XML",
    ):
        service.preparar_nfse_para_envio(
            documento=documento,
            payload=payload,
        )

    assert documento.status == "PREPARADA"


def test_b7final_004_nao_transmite(
    monkeypatch,
):
    documento = _documento()

    def transmitir_proibido(*args, **kwargs):
        raise AssertionError(
            "Transicao local nao pode transmitir NFS-e."
        )

    monkeypatch.setattr(
        service,
        "transmitir_payload_nfse",
        transmitir_proibido,
    )

    service.preparar_nfse_para_envio(
        documento=documento,
        payload=_payload(),
    )

    assert documento.status == "PENDENTE_ENVIO"


def test_b7final_005_habilita_contrato_da_transmissao(
    monkeypatch,
):
    documento = _documento()
    payload = _payload()
    eventos = []

    service.preparar_nfse_para_envio(
        documento=documento,
        payload=payload,
    )

    assert documento.status == "PENDENTE_ENVIO"

    monkeypatch.setattr(
        service,
        "transmitir_payload_nfse",
        lambda **kwargs: (
            eventos.append("transmitir")
            or {
                "status": "ERRO",
                "mensagem": "simulacao local",
                "protocolo": None,
                "numero_nfse": None,
                "dados_provider": {},
            }
        ),
    )

    resultado_documento, resultado = (
        service.transmitir_e_aplicar_nfse(
            documento=documento,
            payload=payload,
            configuracao=SimpleNamespace(id=1),
        )
    )

    assert resultado_documento is documento
    assert resultado["status"] == "ERRO"
    assert eventos == ["transmitir"]
    assert documento.status == "PENDENTE_ENVIO"
